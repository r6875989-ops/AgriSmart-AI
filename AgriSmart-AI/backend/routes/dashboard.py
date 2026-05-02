import json
from flask import Blueprint, request, jsonify, g
from services.auth_service import token_required
from models.database import get_db, execute_query

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_stats():
    """Get user activity stats for dashboard"""
    conn, dialect = get_db()
    
    
    # Total disease scans
    cursor, _ = execute_query(conn, dialect, "SELECT COUNT(*) as count FROM crop_analysis WHERE user_id = ?", (g.user_id,))
    total_scans = cursor.fetchone()['count']
    
    # Diseases found (non-healthy)
    cursor, _ = execute_query(conn, dialect, "SELECT COUNT(*) as count FROM crop_analysis WHERE user_id = ? AND is_healthy = 0", (g.user_id,))
    diseases_found = cursor.fetchone()['count']
    
    # Fertilizer reports
    cursor, _ = execute_query(conn, dialect, "SELECT COUNT(*) as count FROM fertilizer_logs WHERE user_id = ?", (g.user_id,))
    fertilizer_reports = cursor.fetchone()['count']
    
    # Price checks
    cursor, _ = execute_query(conn, dialect, "SELECT COUNT(*) as count FROM price_predictions WHERE user_id = ?", (g.user_id,))
    price_checks = cursor.fetchone()['count']
    
    # Voice sessions
    cursor, _ = execute_query(conn, dialect, "SELECT COUNT(*) as count FROM voice_logs WHERE user_id = ?", (g.user_id,))
    voice_sessions = cursor.fetchone()['count']
    
    # This week's scans
    from datetime import datetime, timedelta, timezone
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    cursor, _ = execute_query(conn, dialect, """
        SELECT COUNT(*) as count FROM crop_analysis 
        WHERE user_id = ? AND timestamp >= ?
    """, (g.user_id, seven_days_ago))
    scans_this_week = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total_scans': total_scans,
        'diseases_found': diseases_found,
        'fertilizer_reports': fertilizer_reports,
        'price_checks': price_checks,
        'voice_sessions': voice_sessions,
        'scans_this_week': scans_this_week
    }), 200

@dashboard_bp.route('/api/dashboard/history/<module>', methods=['GET'])
@token_required
def get_history(module):
    """Get user history for a specific module"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    offset = (page - 1) * per_page
    
    conn, dialect = get_db()
    
    
    if module == 'disease':
        cursor, _ = execute_query(conn, dialect, """
            SELECT id, image_path, disease, confidence, affected_crop, severity, 
                   symptoms, treatment, prevention, is_healthy, timestamp
            FROM crop_analysis WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ? OFFSET ?
        """, (g.user_id, per_page, offset))
        rows = cursor.fetchall()
        
        # Get total count
        cursor, _ = execute_query(conn, dialect, "SELECT COUNT(*) as count FROM crop_analysis WHERE user_id = ?", (g.user_id,))
        total = cursor.fetchone()['count']
        
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'image_path': row['image_path'],
                'disease': row['disease'],
                'confidence': row['confidence'],
                'affected_crop': row['affected_crop'],
                'severity': row['severity'],
                'symptoms': json.loads(row['symptoms']) if row['symptoms'] else [],
                'treatment': json.loads(row['treatment']) if row['treatment'] else [],
                'prevention': json.loads(row['prevention']) if row['prevention'] else [],
                'is_healthy': bool(row['is_healthy']),
                'timestamp': row['timestamp']
            })
    
    elif module == 'fertilizer':
        cursor, _ = execute_query(conn, dialect, """
            SELECT id, crop, soil_type, stage, region, problem, fertilizer, 
                   quantity, advice, full_response, timestamp
            FROM fertilizer_logs WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ? OFFSET ?
        """, (g.user_id, per_page, offset))
        rows = cursor.fetchall()
        
        cursor, _ = execute_query(conn, dialect, "SELECT COUNT(*) as count FROM fertilizer_logs WHERE user_id = ?", (g.user_id,))
        total = cursor.fetchone()['count']
        
        history = []
        for row in rows:
            item = {
                'id': row['id'],
                'crop': row['crop'],
                'soil_type': row['soil_type'],
                'stage': row['stage'],
                'region': row['region'],
                'problem': row['problem'],
                'fertilizer': row['fertilizer'],
                'quantity': row['quantity'],
                'advice': row['advice'],
                'timestamp': row['timestamp']
            }
            # Parse full response if available
            if row['full_response']:
                try:
                    item['full_details'] = json.loads(row['full_response'])
                except json.JSONDecodeError:
                    pass
            history.append(item)
    
    elif module == 'price':
        cursor, _ = execute_query(conn, dialect, """
            SELECT id, crop, state, current_price, predicted_price, trend, 
                   advice, full_response, timestamp
            FROM price_predictions WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ? OFFSET ?
        """, (g.user_id, per_page, offset))
        rows = cursor.fetchall()
        
        cursor, _ = execute_query(conn, dialect, "SELECT COUNT(*) as count FROM price_predictions WHERE user_id = ?", (g.user_id,))
        total = cursor.fetchone()['count']
        
        history = []
        for row in rows:
            item = {
                'id': row['id'],
                'crop': row['crop'],
                'state': row['state'],
                'current_price': row['current_price'],
                'predicted_price': row['predicted_price'],
                'trend': row['trend'],
                'advice': row['advice'],
                'timestamp': row['timestamp']
            }
            if row['full_response']:
                try:
                    item['full_details'] = json.loads(row['full_response'])
                except json.JSONDecodeError:
                    pass
            history.append(item)
    
    elif module == 'voice':
        cursor, _ = execute_query(conn, dialect, """
            SELECT id, transcript, language, intent, response_text, 
                   module_triggered, timestamp
            FROM voice_logs WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ? OFFSET ?
        """, (g.user_id, per_page, offset))
        rows = cursor.fetchall()
        
        cursor, _ = execute_query(conn, dialect, "SELECT COUNT(*) as count FROM voice_logs WHERE user_id = ?", (g.user_id,))
        total = cursor.fetchone()['count']
        
        history = [{
            'id': row['id'],
            'transcript': row['transcript'],
            'language': row['language'],
            'intent': row['intent'],
            'response_text': row['response_text'],
            'module_triggered': row['module_triggered'],
            'timestamp': row['timestamp']
        } for row in rows]
    
    else:
        conn.close()
        return jsonify({'error': f'Invalid module: {module}'}), 400
    
    conn.close()
    
    return jsonify({
        'module': module,
        'history': history,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }), 200

@dashboard_bp.route('/api/dashboard/recent-activity', methods=['GET'])
@token_required
def get_recent_activity():
    """Get recent activity across all modules"""
    conn, dialect = get_db()
    
    
    activities = []
    
    # Recent disease scans
    cursor, _ = execute_query(conn, dialect, """
        SELECT 'disease' as type, disease as title, affected_crop as subtitle, 
               confidence, timestamp 
        FROM crop_analysis WHERE user_id = ? 
        ORDER BY timestamp DESC LIMIT 3
    """, (g.user_id,))
    for row in cursor.fetchall():
        activities.append({
            'type': 'disease',
            'title': f"Disease scan",
            'subtitle': f"{row['subtitle']} · {row['title']}",
            'detail': row['title'],
            'confidence': row['confidence'],
            'timestamp': row['timestamp']
        })
    
    # Recent fertilizer logs
    cursor, _ = execute_query(conn, dialect, """
        SELECT 'fertilizer' as type, crop, soil_type, fertilizer, timestamp
        FROM fertilizer_logs WHERE user_id = ?
        ORDER BY timestamp DESC LIMIT 3
    """, (g.user_id,))
    for row in cursor.fetchall():
        activities.append({
            'type': 'fertilizer',
            'title': 'Fertilizer advice',
            'subtitle': f"{row['crop']} · {row['soil_type']} soil",
            'detail': row['fertilizer'],
            'timestamp': row['timestamp']
        })
    
    # Recent price predictions
    cursor, _ = execute_query(conn, dialect, """
        SELECT 'price' as type, crop, predicted_price, trend, timestamp
        FROM price_predictions WHERE user_id = ?
        ORDER BY timestamp DESC LIMIT 3
    """, (g.user_id,))
    for row in cursor.fetchall():
        activities.append({
            'type': 'price',
            'title': 'Price prediction',
            'subtitle': f"{row['crop']} · {row['predicted_price']} forecast",
            'detail': row['trend'],
            'timestamp': row['timestamp']
        })
    
    # Recent voice sessions
    cursor, _ = execute_query(conn, dialect, """
        SELECT 'voice' as type, transcript, language, module_triggered, timestamp
        FROM voice_logs WHERE user_id = ?
        ORDER BY timestamp DESC LIMIT 3
    """, (g.user_id,))
    for row in cursor.fetchall():
        activities.append({
            'type': 'voice',
            'title': 'Voice session',
            'subtitle': f'"{row["transcript"][:40]}..." · {row["language"].upper()}',
            'detail': row['module_triggered'],
            'timestamp': row['timestamp']
        })
    
    # Sort all by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    conn.close()
    
    return jsonify({'activities': activities[:10]}), 200
