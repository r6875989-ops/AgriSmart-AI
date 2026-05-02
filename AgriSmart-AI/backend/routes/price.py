import json
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from services.auth_service import token_required, check_rate_limit, record_api_call
from services.nvidia_service import predict_price
from models.database import get_db, execute_query

price_bp = Blueprint('price', __name__)

@price_bp.route('/api/price/predict', methods=['POST'])
@token_required
def get_price_prediction():
    """Get market price prediction for a crop"""
    
    if check_rate_limit(g.user_id, 'price'):
        return jsonify({'error': 'Rate limit exceeded. Max 20 requests per hour.'}), 429
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    crop = data.get('crop', '').strip()
    state = data.get('state', '').strip()
    month = data.get('month', datetime.now().strftime('%B'))
    quantity = data.get('quantity', None)
    
    if not crop:
        return jsonify({'error': 'Crop name is required'}), 400
    if not state:
        return jsonify({'error': 'State is required'}), 400
    
    # Call NVIDIA AI
    result = predict_price(crop, state, month, quantity)
    
    record_api_call(g.user_id, 'price')
    
    # Save to database
    conn, dialect = get_db()
    
    current_price = f"₹{result.get('current_price_min', 0)}-₹{result.get('current_price_max', 0)}"
    predicted = f"₹{result.get('predicted_30_days', 0)}"
    
    cursor, record_id = execute_query(
        conn, dialect,
        '''
        INSERT INTO price_predictions (user_id, crop, state, current_price, predicted_price, trend, advice, full_response)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            g.user_id,
            crop,
            state,
            current_price,
            predicted,
            result.get('trend', 'stable'),
            result.get('advice', ''),
            json.dumps(result)
        ),
        fetch_id=True
    )
    conn.commit()
    conn.close()
    
    result['id'] = record_id

    # ── Hindi translations ─────────────────────────────────────────────────
    crop_hindi = {
        'Wheat': 'गेहूं', 'Rice': 'चावल/धान', 'Maize': 'मक्का', 'Sugarcane': 'गन्ना',
        'Cotton': 'कपास', 'Tomato': 'टमाटर', 'Potato': 'आलू', 'Soybean': 'सोयाबीन',
        'Onion': 'प्याज', 'Mustard': 'सरसों', 'Groundnut': 'मूंगफली', 'Chana': 'चना',
    }.get(crop, crop)

    state_hindi = {
        'Andhra Pradesh': 'आंध्र प्रदेश', 'Bihar': 'बिहार', 'Chhattisgarh': 'छत्तीसगढ़',
        'Gujarat': 'गुजरात', 'Haryana': 'हरियाणा', 'Himachal Pradesh': 'हिमाचल प्रदेश',
        'Jharkhand': 'झारखंड', 'Karnataka': 'कर्नाटक', 'Kerala': 'केरल',
        'Madhya Pradesh': 'मध्य प्रदेश', 'Maharashtra': 'महाराष्ट्र', 'Odisha': 'ओडिशा',
        'Punjab': 'पंजाब', 'Rajasthan': 'राजस्थान', 'Tamil Nadu': 'तमिल नाडु',
        'Telangana': 'तेलंगाना', 'Uttar Pradesh': 'उत्तर प्रदेश', 'Uttarakhand': 'उत्तराखंड',
        'West Bengal': 'पश्चिम बंगाल',
    }.get(state, state)

    trend = result.get('trend', 'stable')
    trend_hindi = {'rising': 'बढ़ रहा है ↑', 'falling': 'गिर रहा है ↓', 'stable': 'स्थिर →'}.get(trend, trend)

    min_p = result.get('current_price_min', 0)
    max_p = result.get('current_price_max', 0)
    p30 = result.get('predicted_30_days', 0)
    p60 = result.get('predicted_60_days', 0)
    msp_val = result.get('msp', '')

    result['hindi'] = {
        'crop': crop_hindi,
        'state': state_hindi,
        'trend': trend_hindi,
        'current_price': f'वर्तमान मूल्य: ₹{min_p}-₹{max_p} प्रति क्विंटल',
        'predicted_30': f'30-दिन अनुमान: ₹{p30} प्रति क्विंटल',
        'predicted_60': f'60-दिन अनुमान: ₹{p60} प्रति क्विंटल',
        'msp': f'न्यूनतम समर्थन मूल्य (MSP): ₹{msp_val}' if msp_val else '',
        'advice': f'{crop_hindi} ({state_hindi}) — बाज़ार का रुझान: {trend_hindi}',
        'summary': f'{crop_hindi} का {state_hindi} में बाज़ार भाव — वर्तमान ₹{min_p}-₹{max_p}, 30 दिन बाद ₹{p30}, रुझान: {trend_hindi}',
    }

    return jsonify(result), 200
