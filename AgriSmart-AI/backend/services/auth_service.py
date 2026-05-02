import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g
from config import Config
from models.database import get_db, execute_query

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_token(user_id, email, name):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'name': name,
        'exp': datetime.now(timezone.utc) + timedelta(days=Config.JWT_EXPIRY_DAYS),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')

def decode_token(token):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator - requires valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token missing. Please login.'}), 401
        
        payload = decode_token(token)
        if payload is None:
            return jsonify({'error': 'Token invalid or expired. Please login again.'}), 401
        
        g.user_id = payload['user_id']
        g.user_email = payload['email']
        g.user_name = payload['name']
        
        return f(*args, **kwargs)
    return decorated

def check_rate_limit(user_id, endpoint):
    """Check if user has exceeded rate limit"""
    conn, dialect = get_db()
    
    
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    cursor, _ = execute_query(conn, dialect, 
        "SELECT COUNT(*) as count FROM rate_limits WHERE user_id = ? AND endpoint = ? AND timestamp > ?", (user_id, endpoint, one_hour_ago.isoformat())
    )
    result = cursor.fetchone()
    count = result['count'] if result else 0
    conn.close()
    
    return count >= Config.RATE_LIMIT_PER_HOUR

def record_api_call(user_id, endpoint):
    """Record an API call for rate limiting"""
    conn, dialect = get_db()
    
    execute_query(
        conn, dialect,
        "INSERT INTO rate_limits (user_id, endpoint) VALUES (?, ?)",
        (user_id, endpoint)
    )
    conn.commit()
    conn.close()
