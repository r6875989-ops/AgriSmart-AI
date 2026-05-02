import json
from flask import Blueprint, request, jsonify, g
from services.auth_service import token_required, check_rate_limit, record_api_call
from services.nvidia_service import process_voice
from models.database import get_db, execute_query

voice_bp = Blueprint('voice', __name__)

@voice_bp.route('/api/voice/process', methods=['POST'])
@token_required
def process_voice_query():
    """Process voice transcript and return AI response"""
    
    if check_rate_limit(g.user_id, 'voice'):
        return jsonify({'error': 'Rate limit exceeded. Max 20 requests per hour.'}), 429
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    transcript = data.get('transcript', '').strip()
    language = data.get('language', 'hi')
    
    if not transcript:
        return jsonify({'error': 'No transcript provided'}), 400
    
    # Call NVIDIA AI
    result = process_voice(transcript, language)
    
    record_api_call(g.user_id, 'voice')
    
    # Save to database
    conn, dialect = get_db()
    
    response_text = result.get('response_hindi' if language == 'hi' else 'response_text', '')
    
    cursor, record_id = execute_query(
        conn, dialect,
        '''
        INSERT INTO voice_logs (user_id, transcript, language, intent, response_text, module_triggered)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (
            g.user_id,
            transcript,
            language,
            result.get('intent', 'general'),
            response_text,
            result.get('module_triggered', 'general')
        ),
        fetch_id=True
    )
    conn.commit()
    conn.close()
    
    result['id'] = record_id
    return jsonify(result), 200
