import json
from flask import Blueprint, request, jsonify, g
from services.auth_service import token_required, check_rate_limit, record_api_call
from services.ml_service import predict_fertilizer_ml
from models.database import get_db, execute_query

fertilizer_bp = Blueprint('fertilizer', __name__)

@fertilizer_bp.route('/api/fertilizer/recommend', methods=['POST'])
@token_required
def get_recommendation():
    """Get fertilizer recommendation based on crop and soil data"""
    
    if check_rate_limit(g.user_id, 'fertilizer'):
        return jsonify({'error': 'Rate limit exceeded. Max 20 requests per hour.'}), 429
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    crop = data.get('crop', '').strip()
    soil_type = data.get('soil_type', '').strip()
    stage = data.get('stage', '').strip()
    problem = data.get('problem', '').strip()
    region = data.get('region', '').strip()
    
    # Validation
    if not crop:
        return jsonify({'error': 'Crop name is required'}), 400
    if not soil_type:
        return jsonify({'error': 'Soil type is required'}), 400
    if not stage:
        return jsonify({'error': 'Growth stage is required'}), 400
    if not region:
        return jsonify({'error': 'Region/Climate is required'}), 400
    
    # Estimate NPK values based on soil type and region for ML model
    soil_npk_defaults = {
        'Sandy': {'n': 15, 'p': 10, 'k': 5, 'temp': 32, 'humidity': 55, 'moisture': 35},
        'Loamy': {'n': 20, 'p': 15, 'k': 10, 'temp': 30, 'humidity': 60, 'moisture': 50},
        'Clay': {'n': 25, 'p': 20, 'k': 8, 'temp': 28, 'humidity': 65, 'moisture': 55},
        'Clayey': {'n': 25, 'p': 20, 'k': 8, 'temp': 28, 'humidity': 65, 'moisture': 55},
        'Silty': {'n': 22, 'p': 18, 'k': 7, 'temp': 29, 'humidity': 58, 'moisture': 48},
        'Peaty': {'n': 30, 'p': 12, 'k': 6, 'temp': 26, 'humidity': 70, 'moisture': 60},
        'Chalky': {'n': 12, 'p': 15, 'k': 12, 'temp': 31, 'humidity': 52, 'moisture': 30},
        'Black': {'n': 18, 'p': 12, 'k': 9, 'temp': 33, 'humidity': 62, 'moisture': 40},
        'Red': {'n': 14, 'p': 18, 'k': 6, 'temp': 34, 'humidity': 56, 'moisture': 38},
    }
    defaults = soil_npk_defaults.get(soil_type, {'n': 20, 'p': 15, 'k': 5, 'temp': 30, 'humidity': 60, 'moisture': 40})
    
    # Use ML model for prediction
    result = predict_fertilizer_ml(
    crop=crop,
    soil_type=soil_type,
    stage=stage,
    region=region,
    problem=problem,
    temperature=defaults['temp'],
    humidity=defaults['humidity'],
    moisture=defaults['moisture'],
    nitrogen=defaults['n'],
    phosphorous=defaults['p'],
    potassium=defaults['k']
)
    
    record_api_call(g.user_id, 'fertilizer')
    
    # Save to database
    conn, dialect = get_db()
    
    primary = result.get('primary_fertilizer', {})
    cursor, record_id = execute_query(
        conn, dialect,
        '''
        INSERT INTO fertilizer_logs (user_id, crop, soil_type, stage, region, problem, fertilizer, quantity, advice, full_response)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            g.user_id,
            crop,
            soil_type,
            stage,
            region,
            problem,
            primary.get('name', 'Unknown'),
            primary.get('quantity_per_acre', 'Unknown'),
            result.get('expected_improvement', ''),
            json.dumps(result)
        ),
        fetch_id=True
    )
    conn.commit()
    conn.close()
    
    result['id'] = record_id
    return jsonify(result), 200
