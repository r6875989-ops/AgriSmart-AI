from flask import Blueprint, request, jsonify
from models.database import get_db, execute_query
from services.auth_service import hash_password, check_password, generate_token, token_required
from flask import g
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    errors = []
    if not name or len(name) < 2:
        errors.append('Name must be at least 2 characters')
    if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append('Please enter a valid email address')
    if not password or len(password) < 8:
        errors.append('Password must be at least 8 characters')
    if password != confirm_password:
        errors.append('Passwords do not match')
    if errors:
        return jsonify({'error': errors[0], 'errors': errors}), 400

    conn, dialect = get_db()
    try:
        # Check existing email
        cursor, _ = execute_query(
            conn, dialect,
            "SELECT user_id FROM users WHERE email = ?",
            (email,)
        )
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Email already registered. Please login.'}), 409

        # Insert new user
        hashed = hash_password(password)
        cursor, user_id = execute_query(
            conn, dialect,
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed),
            fetch_id=True
        )
        conn.commit()

        # ✅ Verify user_id mila ya nahi
        if not user_id:
            # Fallback — email se user_id lo
            cursor, _ = execute_query(
                conn, dialect,
                "SELECT user_id FROM users WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()
            user_id = row['user_id'] if row else None

        if not user_id:
            conn.close()
            return jsonify({'error': 'Registration failed: could not get user ID'}), 500

        token = generate_token(user_id, email, name)
        conn.close()

        return jsonify({
            'message': 'Registration successful!',
            'token': token,
            'user': {
                'user_id': user_id,
                'name': name,
                'email': email
            }
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        conn.close()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    conn, dialect = get_db()
    try:
        cursor, _ = execute_query(
            conn, dialect,
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'No account found with this email'}), 401

        # ✅ Dict ya Row dono handle karo
        if hasattr(user, 'keys'):
            user = dict(user)

        if not check_password(password, user['password']):
            return jsonify({'error': 'Incorrect password'}), 401

        token = generate_token(user['user_id'], user['email'], user['name'])

        return jsonify({
            'message': 'Login successful!',
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email']
            }
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        conn.close()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@auth_bp.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    conn, dialect = get_db()
    try:
        cursor, _ = execute_query(
            conn, dialect,
            "SELECT user_id, name, email, created_at FROM users WHERE user_id = ?",
            (g.user_id,)
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        if hasattr(user, 'keys'):
            user = dict(user)

        return jsonify({
            'user': {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email'],
                'created_at': str(user['created_at'])
            }
        }), 200

    except Exception as e:
        conn.close()
        return jsonify({'error': f'Failed: {str(e)}'}), 500
