"""
backend/routes/disease.py
─────────────────────────
Route: POST /api/disease/predict
Receives image from frontend, validates it, runs ML inference, saves result to DB.

FIXES applied vs original:
  1. Strip base64 prefix ONLY here  (frontend now sends full data URL)
  2. Actually check _ML_MODEL_EXISTS before calling model
  3. Return 503 with clear message when model file is missing
  4. Improved error messages for debugging
"""

import os
import base64
import json
from flask import Blueprint, request, jsonify, g
from services.auth_service import token_required, check_rate_limit, record_api_call
from services.ml_service import predict_disease_ml
from models.database import get_db, execute_query
from config import Config

disease_bp = Blueprint('disease', __name__)

# ─── Check if ML model file exists on startup ─────────────────────────────────
_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
_ML_MODEL_PATH = os.path.join(_MODELS_DIR, 'disease_model.h5')
_ML_CLASSES_PATH = os.path.join(_MODELS_DIR, 'disease_classes.pkl')
_ML_MODEL_EXISTS = os.path.exists(_ML_MODEL_PATH) and os.path.exists(_ML_CLASSES_PATH)

if not _ML_MODEL_EXISTS:
    print("⚠️  WARNING: disease_model.h5 or disease_classes.pkl not found.")
    print("   Run: python training/train_disease.py  to train the model first.")
else:
    print(f"✅ Disease model files found at: {_MODELS_DIR}")


# ─── Predict endpoint ──────────────────────────────────────────────────────────
@disease_bp.route('/api/disease/predict', methods=['POST'])
@token_required
def predict_disease():
    """
    Accepts JSON: { image_base64: "<full data URL or raw base64>", filename: "leaf.jpg" }
    Returns JSON with disease name, confidence, symptoms, treatment, prevention.
    """

    # ── Rate limiting ──────────────────────────────────────────────────────────
    if check_rate_limit(g.user_id, 'disease'):
        return jsonify({'error': 'Rate limit exceeded. Max 20 requests per hour.'}), 429

    # ── Parse request body ─────────────────────────────────────────────────────
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    image_base64 = data.get('image_base64', '').strip()
    filename     = data.get('filename', 'upload.jpg').strip()

    if not image_base64:
        return jsonify({'error': 'image_base64 field is required'}), 400

    # ── FIX 1: Strip data URL prefix ONLY HERE ─────────────────────────────────
    # Frontend sends full data URL: "data:image/jpeg;base64,/9j/4AAQ..."
    # We strip the prefix once here. Never strip twice.
    if ',' in image_base64:
        image_base64 = image_base64.split(',', 1)[1]   # split on FIRST comma only

    # ── Validate file extension ────────────────────────────────────────────────
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    allowed = getattr(Config, 'ALLOWED_EXTENSIONS', {'jpg', 'jpeg', 'png', 'webp'})
    if ext not in allowed:
        return jsonify({'error': f'File type ".{ext}" not allowed. Use JPG, PNG, or WebP.'}), 400

    # ── Validate decoded image size ────────────────────────────────────────────
    try:
        decoded_bytes = base64.b64decode(image_base64)
    except Exception:
        return jsonify({'error': 'Invalid base64 image data. Ensure image is not corrupted.'}), 400

    max_bytes = getattr(Config, 'MAX_CONTENT_LENGTH', 5 * 1024 * 1024)
    if len(decoded_bytes) > max_bytes:
        return jsonify({'error': f'Image too large. Maximum size is {max_bytes // (1024*1024)}MB.'}), 400

    # ── FIX 2: Guard — return clear error if model is not trained ──────────────
    if not _ML_MODEL_EXISTS:
        return jsonify({
            'error': 'ML model not found. Run: python training/train_disease.py',
            'hint': f'Expected model at: {_ML_MODEL_PATH}'
        }), 503

    # ── Save uploaded image to disk ────────────────────────────────────────────
    upload_folder = getattr(Config, 'UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    safe_filename = f"{g.user_id}_{filename}"
    image_path = os.path.join(upload_folder, safe_filename)
    try:
        with open(image_path, 'wb') as f:
            f.write(decoded_bytes)
    except Exception as e:
        print(f"[disease.py] Upload save failed (non-fatal): {e}")
        image_path = 'upload_failed'

    # ── Run ML prediction ──────────────────────────────────────────────────────
    # Pass the CLEAN base64 string (no prefix) to ml_service
    result = predict_disease_ml(image_base64)

    # ── Record API usage ───────────────────────────────────────────────────────
    try:
      record_api_call(g.user_id, 'disease')
    except Exception:
      pass
   

    # ── Save result to database ────────────────────────────────────────────────
    record_id = None
    try:
        conn, dialect = get_db()
        cursor, record_id = execute_query(
            conn, dialect,
            '''
            INSERT INTO crop_analysis
              (user_id, image_path, disease, confidence, affected_crop,
               severity, symptoms, treatment, prevention, is_healthy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                g.user_id,
                image_path,
                result.get('disease_name', 'Unknown'),
                result.get('confidence', 0),
                result.get('affected_crop', 'Unknown'),
                result.get('severity', 'Unknown'),
                json.dumps(result.get('symptoms', [])),
                json.dumps(result.get('treatment', [])),
                json.dumps(result.get('prevention', [])),
                1 if result.get('is_healthy', False) else 0,
            ),
            fetch_id=True
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[disease.py] DB save failed (non-fatal): {e}")

    # ── Return result ──────────────────────────────────────────────────────────
    return jsonify({
        'id':              record_id,
        'disease_name':    result.get('disease_name', 'Unknown'),
        'confidence':      result.get('confidence', 0),
        'affected_crop':   result.get('affected_crop', 'Unknown'),
        'symptoms':        result.get('symptoms', []),
        'treatment':       result.get('treatment', []),
        'prevention':      result.get('prevention', []),
        'severity':        result.get('severity', 'Unknown'),
        'is_healthy':      result.get('is_healthy', False),
        'top_predictions': result.get('top_predictions', []),
    }), 200


# ─── History endpoint ─────────────────────────────────────────────────────────
@disease_bp.route('/api/disease/history', methods=['GET'])
@token_required
def get_history():
    """Return paginated scan history for the logged-in user."""
    page  = max(1, int(request.args.get('page', 1)))
    limit = min(50, int(request.args.get('limit', 10)))
    offset = (page - 1) * limit

    try:
        conn, dialect = get_db()
        cursor, _ = execute_query(
            conn, dialect,
            '''
            SELECT id, image_path, disease, confidence, affected_crop,
                   severity, is_healthy, timestamp
            FROM crop_analysis
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            ''',
            (g.user_id, limit, offset)
        )
        rows = cursor.fetchall()
        conn.close()

        records = [
            {
                'id':           row[0],
                'image_path':   row[1],
                'disease':      row[2],
                'confidence':   row[3],
                'affected_crop':row[4],
                'severity':     row[5],
                'is_healthy':   bool(row[6]),
                'timestamp':   str(row[7]),
            }
            for row in rows
        ]
        return jsonify({'page': page, 'limit': limit, 'records': records}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Single record endpoint ───────────────────────────────────────────────────
@disease_bp.route('/api/disease/<int:record_id>', methods=['GET'])
@token_required
def get_record(record_id):
    """Return a single scan record by ID (only if owned by requesting user)."""
    try:
        conn, dialect = get_db()
        cursor, _ = execute_query(
            conn, dialect,
            '''
            SELECT id, disease, confidence, affected_crop, severity,
                   symptoms, treatment, prevention, is_healthy, timestamp
            FROM crop_analysis
            WHERE id = ? AND user_id = ?
            ''',
            (record_id, g.user_id)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Record not found'}), 404

        return jsonify({
            'id':            row[0],
            'disease_name':  row[1],
            'confidence':    row[2],
            'affected_crop': row[3],
            'severity':      row[4],
            'symptoms':      json.loads(row[5] or '[]'),
            'treatment':     json.loads(row[6] or '[]'),
            'prevention':    json.loads(row[7] or '[]'),
            'is_healthy':    bool(row[8]),
            'timestamp':    str(row[9]),
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
