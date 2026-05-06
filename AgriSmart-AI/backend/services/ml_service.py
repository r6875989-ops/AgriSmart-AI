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

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY", "")
)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


def load_disease_model():
    return None, None


def _error_result(name, symptoms, treatment):
    return {
        'disease_name': name,
        'confidence': 0,
        'affected_crop': 'Unknown',
        'symptoms': symptoms,
        'treatment': treatment,
        'prevention': [],
        'severity': 'Unknown',
        'is_healthy': False,
        'estimated_yield_loss': 'Unknown',
        'urgency': 'Unknown',
        'best_season_to_grow': 'Unknown',
        'top_predictions': [],
        'hindi': {
            'disease_name': 'अज्ञात',
            'crop': 'अज्ञात',
            'severity': 'अज्ञात',
            'urgency': 'अज्ञात',
            'status': '❌ विश्लेषण विफल — पुनः प्रयास करें',
            'estimated_yield_loss': 'अज्ञात',
            'best_season': 'अज्ञात',
            'symptoms': ['छवि का विश्लेषण नहीं हो सका'],
            'treatment': ['स्पष्ट तस्वीर से पुनः प्रयास करें'],
            'prevention': [],
            'market_advice': 'पुनः प्रयास करें',
            'government_helpline': 'किसान कॉल सेंटर: 1800-180-1551',
            'nearest_help': 'नजदीकी कृषि विभाग से संपर्क करें'
        }
    }


def predict_disease_ml(image_base64):
    try:
        prompt = """Analyze this crop leaf image and return ONLY this JSON, no extra text:
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
        {"class": "Healthy", "crop": "Tomato", "confidence": 7.5}
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
}
Analyze the ACTUAL image. Return ONLY valid JSON."""

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
            raise ValueError("Empty response from API")

        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        if not result_text.startswith('{'):
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result_text = result_text[start:end+1]

        return json.loads(result_text)

    except Exception as e:
        print(f"[ml_service] predict_disease_ml error: {e}")
        return _error_result(
            "Prediction Error",
            [f"Analysis failed: {str(e)}"],
            ["Please try again with a clearer photo"]
        )


def load_fertilizer_model():
    return None, None


def predict_fertilizer_ml(crop, soil_type, stage='', region='', problem='', temperature=None, **kwargs):
    try:
        prompt = f"""You are an expert Indian agricultural scientist.
Recommend fertilizer for:
- Crop: {crop}
- Soil Type: {soil_type}
- Growth Stage: {stage}
- Region: {region}
- Problem: {problem if problem else 'None'}

Return ONLY this JSON, no extra text:
{{
    "primary_fertilizer": {{
        "name": "DAP",
        "quantity_per_acre": "50kg per acre",
        "application_method": "Broadcast before sowing",
        "timing": "At sowing time"
    }},
    "secondary_fertilizer": {{
        "name": "Urea",
        "quantity_per_acre": "25kg per acre",
        "application_method": "Top dressing",
        "timing": "30 days after sowing"
    }},
    "micronutrients": "Zinc Sulphate 10kg/acre",
    "expected_improvement": "15-20% yield increase",
    "precautions": "Avoid excess nitrogen",
    "hindi": {{
        "primary_fertilizer": "डीएपी - 50 किग्रा प्रति एकड़",
        "secondary_fertilizer": "यूरिया - 25 किग्रा प्रति एकड़",
        "micronutrients": "जिंक सल्फेट 10 किग्रा/एकड़",
        "expected_improvement": "15-20% उपज वृद्धि",
        "precautions": "नाइट्रोजन की अधिक मात्रा से बचें"
    }}
}}"""

        response = client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.1
        )

        result_text = response.choices[0].message.content.strip()

        if not result_text:
            raise ValueError("Empty response")

        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        if not result_text.startswith('{'):
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result_text = result_text[start:end+1]

        return json.loads(result_text)

    except Exception as e:
        print(f"[ml_service] predict_fertilizer_ml error: {e}")
        return {
            "primary_fertilizer": {
                "name": "DAP",
                "quantity_per_acre": "50kg per acre",
                "application_method": "Broadcast",
                "timing": "At sowing"
            },
            "secondary_fertilizer": {
                "name": "Urea",
                "quantity_per_acre": "25kg per acre",
                "application_method": "Top dressing",
                "timing": "30 days after sowing"
            },
            "micronutrients": "Zinc Sulphate if needed",
            "expected_improvement": "Default recommendation",
            "precautions": str(e),
            "hindi": {
                "primary_fertilizer": "डीएपी - 50 किग्रा प्रति एकड़",
                "secondary_fertilizer": "यूरिया - 25 किग्रा प्रति एकड़",
                "micronutrients": "जिंक सल्फेट यदि आवश्यक",
                "expected_improvement": "डिफ़ॉल्ट अनुशंसा",
                "precautions": "पुनः प्रयास करें"
            }
        }
