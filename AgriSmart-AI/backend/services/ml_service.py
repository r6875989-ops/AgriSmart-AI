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
    try:
        prompt = """You are Dr. Rajesh Kumar, a senior Indian agricultural scientist with 20 years of field experience across all Indian states.

Carefully analyze this crop leaf image and provide a highly detailed disease diagnosis.

Return ONLY the following JSON — no extra text, no markdown, no explanation:

{
    "disease_name": "Early_blight",
    "confidence": 92.5,
    "affected_crop": "Tomato",
    "symptoms": ["symptom 1", "symptom 2"],
    "treatment": ["treatment 1", "treatment 2"],
    "prevention": ["prevention 1", "prevention 2"],
    "severity": "High",
    "is_healthy": false,
    "estimated_yield_loss": "30-40% if untreated",
    "urgency": "Treat within 24-48 hours",
    "best_season_to_grow": "October to February",
    "top_predictions": [
        {"class": "Early_blight", "crop": "Tomato", "confidence": 92.5},
        {"class": "Septoria_leaf_spot", "crop": "Tomato", "confidence": 4.8},
        {"class": "Healthy", "crop": "Tomato", "confidence": 2.7}
    ],
    "hindi": {
        "disease_name": "अर्ली ब्लाइट",
        "crop": "टमाटर",
        "severity": "गंभीर",
        "urgency": "24-48 घंटे में उपचार करें",
        "status": "⚠️ रोग पाया गया",
        "estimated_yield_loss": "30-40% नुकसान",
        "best_season": "अक्टूबर से फरवरी",
        "symptoms": ["लक्षण 1"],
        "treatment": ["उपचार 1"],
        "prevention": ["बचाव 1"],
        "market_advice": "उपचार के बाद बाजार ले जाएं",
        "government_helpline": "किसान कॉल सेंटर: 1800-180-1551",
        "nearest_help": "नजदीकी कृषि विभाग से संपर्क करें"
    }
}"""

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

        if not result_text:
            return _error_result(
                "Empty Response",
                ["NVIDIA API returned empty response"],
                ["Please try again with a clearer photo"]
            )

        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        if not result_text.startswith('{'):
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result_text = result_text[start:end+1]

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


def predict_fertilizer_ml(crop, soil_type, stage, region, problem, temperature=None, **kwargs):
    """Fertilizer recommendation using NVIDIA API"""
    try:
        prompt = f"""You are an expert Indian agricultural scientist.
        
Recommend fertilizer for:
- Crop: {crop}
- Soil Type: {soil_type}
- Growth Stage: {stage}
- Region: {region}
- Problem: {problem}

Return ONLY this JSON:
{{
    "fertilizer": "DAP + Urea",
    "quantity": "50kg DAP + 25kg Urea per acre",
    "advice": "Apply in two splits",
    "hindi": {{
        "fertilizer": "डीएपी + यूरिया",
        "quantity": "प्रति एकड़ 50 किग्रा डीएपी + 25 किग्रा यूरिया",
        "advice": "दो बार में डालें"
    }}
}}"""

        response = client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )

        result_text = response.choices[0].message.content.strip()

# Empty response check
if not result_text:
    return _error_result(
        "Empty Response",
        ["NVIDIA API returned empty response"],
        ["Please try again with a clearer photo"]
    )

# Clean JSON
if "```json" in result_text:
    result_text = result_text.split("```json")[1].split("```")[0].strip()
elif "```" in result_text:
    result_text = result_text.split("```")[1].split("```")[0].strip()

# Find JSON object
if not result_text.startswith('{'):
    start = result_text.find('{')
    end = result_text.rfind('}')
    if start != -1 and end != -1:
        result_text = result_text[start:end+1]

result = json.loads(result_text)
return result

    except Exception as e:
        return {
            "fertilizer": "Analysis Failed",
            "quantity": "Unknown",
            "advice": str(e),
            "hindi": {
                "fertilizer": "विश्लेषण विफल",
                "quantity": "अज्ञात",
                "advice": "पुनः प्रयास करें"
            }
        }
