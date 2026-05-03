"""
backend/services/ml_service.py
───────────────────────────────
Local ML inference using trained .h5 and .pkl model files.

FIXES applied vs original:
  1. disease_info key type mismatch  → try int key first, then str key
  2. top-3 loop same fix             → int/str key fallback
  3. get_disease_remedies matching   → normalize underscores before matching
  4. Lazy TF import kept             → avoids slow startup
  5. Added explicit error logging    → easier debugging
"""

import os
import json
from openai import OpenAI

# ── NVIDIA Client ──────────────────────────────────────────────────────────────
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY", "")
)

_fertilizer_model    = None
_fertilizer_encoders = None

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


# ══════════════════════════════════════════════════════════════════════════════
# DISEASE DETECTION — NVIDIA Vision API
# ══════════════════════════════════════════════════════════════════════════════

def load_disease_model():
    """No local model needed — NVIDIA API handles everything"""
    return None, None


def predict_disease_ml(image_base64: str) -> dict:
    """
    Predict crop disease using NVIDIA Llama Vision API.
    Returns EXACT same dict format as original TensorFlow model.
    """
    try:
        prompt = """You are Dr. Rajesh Kumar, a senior Indian agricultural scientist with 20 years of field experience across all Indian states.

Carefully analyze this crop leaf image and provide a highly detailed disease diagnosis.

Return ONLY the following JSON — no extra text, no markdown, no explanation:

{
    "disease_name": "Early_blight",
    "confidence": 92.5,
    "affected_crop": "Tomato",
    "symptoms": [
        "Dark brown concentric rings forming a target-like pattern on lower leaves",
        "Yellow chlorotic halo of 2-3mm surrounding each lesion",
        "Premature defoliation starting from bottom of plant upward",
        "Dark sunken lesions with water-soaked margins on stems",
        "Fruit shows dark leathery spots near stem end"
    ],
    "treatment": [
        "IMMEDIATE ACTION: Apply Mancozeb 75WP (Dithane M-45) at 2.5g per litre of water — spray every 7 days",
        "Alternate with Chlorothalonil (Kavach) 2g/L to prevent fungicide resistance",
        "Remove and BURN all infected leaves — never compost diseased material",
        "Apply Trichoderma viride (5g/L) as biological control agent at root zone",
        "For severe infection: Azoxystrobin (Amistar Top) 1ml/L — max 2 sprays per season",
        "After rain: reapply fungicide within 24 hours as rain washes away protection"
    ],
    "prevention": [
        "Always use certified disease-resistant seeds: Pusa Ruby, Arka Vikas, or Naveen varieties",
        "Maintain minimum 60cm plant spacing to allow air circulation and reduce humidity",
        "Practice strict 3-year crop rotation — avoid tomato, potato, brinjal in same field",
        "Apply thick mulch layer (5-8cm) around base to prevent soil splash onto lower leaves",
        "Water only at plant base using drip irrigation — never overhead sprinklers",
        "Apply balanced NPK fertilizer — excess nitrogen increases disease susceptibility",
        "Scout fields every 3-4 days during monsoon for early detection"
    ],
    "severity": "High",
    "is_healthy": false,
    "estimated_yield_loss": "30-40% if left untreated for 2 weeks",
    "urgency": "Treat within 24-48 hours to prevent spread",
    "best_season_to_grow": "October to February in North India, June to September in South India",
    "top_predictions": [
        {"class": "Early_blight", "crop": "Tomato", "confidence": 92.5},
        {"class": "Septoria_leaf_spot", "crop": "Tomato", "confidence": 4.8},
        {"class": "Healthy", "crop": "Tomato", "confidence": 2.7}
    ],
    "hindi": {
        "disease_name": "अर्ली ब्लाइट (अगेती झुलसा रोग)",
        "crop": "टमाटर",
        "severity": "गंभीर",
        "urgency": "24-48 घंटे के अंदर उपचार अनिवार्य है",
        "status": "⚠️ रोग पाया गया: अगेती झुलसा",
        "estimated_yield_loss": "2 सप्ताह में उपचार न करने पर 30-40% फसल नुकसान",
        "best_season": "उत्तर भारत में अक्टूबर से फरवरी, दक्षिण भारत में जून से सितंबर",
        "symptoms": [
            "निचली पत्तियों पर गहरे भूरे रंग के गोल छल्ले — निशाने जैसा दिखता है",
            "प्रत्येक घाव के चारों ओर 2-3 मिमी का पीला घेरा",
            "पौधे के नीचे से ऊपर की ओर पत्तियाँ समय से पहले गिरना",
            "तने पर पानी से भरे किनारों वाले गहरे धंसे हुए घाव",
            "फल पर तने के पास गहरे चमड़े जैसे धब्बे"
        ],
        "treatment": [
            "तत्काल कार्रवाई: मैंकोज़ेब 75WP (डाइथेन M-45) 2.5 ग्राम प्रति लीटर पानी में — हर 7 दिन छिड़काव करें",
            "फफूंदनाशक प्रतिरोध से बचने के लिए क्लोरोथालोनिल (कवच) 2 ग्राम/लीटर से बदल-बदलकर छिड़काव करें",
            "सभी संक्रमित पत्तियों को हटाकर जला दें — बीमार पौधों की खाद कभी न बनाएं",
            "जड़ क्षेत्र में जैविक नियंत्रण: ट्राइकोडर्मा विरिडी 5 ग्राम/लीटर",
            "गंभीर संक्रमण के लिए: एज़ोक्सीस्ट्रोबिन (अमिस्टार टॉप) 1 मिली/लीटर — प्रति सीज़न अधिकतम 2 बार",
            "बारिश के बाद: 24 घंटे के अंदर फफूंदनाशक दोबारा लगाएं"
        ],
        "prevention": [
            "हमेशा प्रमाणित रोग-प्रतिरोधी बीज उपयोग करें: पूसा रूबी, अर्का विकास, या नवीन किस्में",
            "हवा के आने-जाने के लिए पौधों के बीच न्यूनतम 60 सेमी की दूरी रखें",
            "कड़ा 3 साल का फसल चक्र अपनाएं — एक ही खेत में टमाटर, आलू, बैंगन न लगाएं",
            "निचली पत्तियों पर मिट्टी के छींटे रोकने के लिए 5-8 सेमी मोटी मल्च परत लगाएं",
            "केवल ड्रिप सिंचाई से पौधे के तने पर पानी दें — ऊपरी स्प्रिंकलर कभी नहीं",
            "संतुलित NPK उर्वरक लगाएं — अधिक नाइट्रोजन से रोग की संभावना बढ़ती है",
            "मानसून के दौरान हर 3-4 दिन में खेत की जाँच करें"
        ],
        "market_advice": "बाज़ार में ले जाने से पहले सभी उपचार पूरे करें और फल साफ करें",
        "government_helpline": "किसान कॉल सेंटर: 1800-180-1551 (निःशुल्क, 24x7)",
        "nearest_help": "नजदीकी कृषि विभाग कार्यालय या KVK से संपर्क करें"
    }
}

STRICT RULES:
1. Analyze the ACTUAL image provided — do not use example values
2. All hindi section values MUST be in Devanagari Hindi script
3. Confidence scores must be realistic based on actual image
4. top_predictions must have 3 items always
5. If crop is HEALTHY:
   - is_healthy = true
   - disease_name = "Healthy"
   - severity = "None"
   - estimated_yield_loss = "0% - Crop is healthy"
   - urgency = "No immediate action needed"
   - hindi.status = "✅ पौधा स्वस्थ है"
   - hindi.disease_name = "स्वस्थ"
   - hindi.severity = "कोई नहीं"
   - hindi.urgency = "कोई तत्कालता नहीं"
6. Return ONLY valid JSON — absolutely no extra text before or after"""

        response = client.chat.completions.create(
            model="meta/llama-3.2-90b-vision-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )

        result_text = response.choices[0].message.content.strip()

        # ── Clean JSON if wrapped in markdown ─────────────────────────────────
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)
        return result

    except Exception as e:
        print(f"[ml_service] predict_disease_ml error: {e}")
        return _error_result(
            "Prediction Error",
            [f"Analysis failed: {str(e)}"],
            ["Please try again with a clearer, well-lit photo of the leaf"]
        )


def _safe_get(disease_info: dict, idx: int) -> dict:
    result = disease_info.get(idx)
    if result is None:
        result = disease_info.get(str(idx))
    return result or {}


def _error_result(name: str, symptoms: list, treatment: list) -> dict:
    return {
        'disease_name':    name,
        'confidence':      0,
        'affected_crop':   'Unknown',
        'symptoms':        symptoms,
        'treatment':       treatment,
        'prevention':      [],
        'severity':        'Unknown',
        'is_healthy':      False,
        'estimated_yield_loss': 'Unknown',
        'urgency':         'Unknown',
        'best_season_to_grow': 'Unknown',
        'top_predictions': [],
        'hindi': {
            'disease_name':       'अज्ञात',
            'crop':               'अज्ञात',
            'severity':           'अज्ञात',
            'urgency':            'अज्ञात',
            'status':             '❌ विश्लेषण विफल — पुनः प्रयास करें',
            'estimated_yield_loss': 'अज्ञात',
            'best_season':        'अज्ञात',
            'symptoms':           ['छवि का विश्लेषण नहीं हो सका'],
            'treatment':          ['स्पष्ट और अच्छी रोशनी वाली तस्वीर से पुनः प्रयास करें'],
            'prevention':         [],
            'market_advice':      'पुनः प्रयास करें',
            'government_helpline': 'किसान कॉल सेंटर: 1800-180-1551',
            'nearest_help':       'नजदीकी कृषि विभाग से संपर्क करें'
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# FERTILIZER MODEL (unchanged — local ML model)
# ══════════════════════════════════════════════════════════════════════════════

def load_fertilizer_model():
    """Load fertilizer recommendation ML model — lazy load"""
    global _fertilizer_model, _fertilizer_encoders
    if _fertilizer_model is None:
        import joblib
        model_path    = os.path.join(MODELS_DIR, 'fertilizer_model.pkl')
        encoders_path = os.path.join(MODELS_DIR, 'fertilizer_encoders.pkl')
        if not os.path.exists(model_path):
            print(f"⚠️  Fertilizer model not found: {model_path}")
            return None, None
        if not os.path.exists(encoders_path):
            print(f"⚠️  Fertilizer encoders not found: {encoders_path}")
            return None, None
        _fertilizer_model    = joblib.load(model_path)
        _fertilizer_encoders = joblib.load(encoders_path)
        print("✅ Fertilizer model loaded successfully")
    return _fertilizer_model, _fertilizer_encoders
