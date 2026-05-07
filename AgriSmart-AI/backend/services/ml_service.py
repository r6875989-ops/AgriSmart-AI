"""
backend/services/ml_service.py
───────────────────────────────
ML inference using NVIDIA API (LLaMA vision + text models).
Output structure matches the original local-ML version exactly,
so the existing fertilizer.py blueprint and frontend work unchanged.
"""

import os
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY", "")
)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


# ══════════════════════════════════════════════════════════════════════════════
# DISEASE DETECTION  (LLaMA 3.2 Vision via NVIDIA API)
# ══════════════════════════════════════════════════════════════════════════════

def load_disease_model():
    """Stub — no local model needed for API-based inference."""
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


def predict_disease_ml(image_base64: str) -> dict:
    """
    Predict crop disease from a base64 image string using NVIDIA LLaMA Vision API.
    Returns same structure as original local-ML version.
    """
    try:
        prompt = """Analyze this crop leaf image carefully and return ONLY valid JSON, no extra text or markdown.

Return exactly this structure:
{
    "disease_name": "Early_blight",
    "confidence": 92.5,
    "affected_crop": "Tomato",
    "symptoms": ["symptom 1", "symptom 2", "symptom 3"],
    "treatment": ["treatment step 1", "treatment step 2", "treatment step 3", "treatment step 4"],
    "prevention": ["prevention 1", "prevention 2", "prevention 3"],
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
        "disease_name": "अर्ली ब्लाइट (अगेती अंगमारी)",
        "crop": "टमाटर",
        "severity": "गंभीर",
        "urgency": "24-48 घंटे में उपचार करें",
        "status": "⚠️ रोग पाया गया",
        "estimated_yield_loss": "30-40% नुकसान",
        "best_season": "अक्टूबर से फरवरी",
        "symptoms": ["लक्षण 1", "लक्षण 2"],
        "treatment": ["उपचार 1", "उपचार 2"],
        "prevention": ["बचाव 1", "बचाव 2"],
        "market_advice": "उपचार के बाद बाजार ले जाएं",
        "government_helpline": "किसान कॉल सेंटर: 1800-180-1551",
        "nearest_help": "नजदीकी कृषि विभाग से संपर्क करें"
    }
}

Rules:
- severity must be one of: "High", "Medium", "Low", "None"
- is_healthy must be true only if plant is completely healthy
- confidence must be 0-100 number
- Analyze the ACTUAL image provided
- Return ONLY the JSON object, nothing else"""

        response = client.chat.completions.create(
            model="meta/llama-3.2-90b-vision-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
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

        # Strip markdown fences if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        # Extract JSON object if surrounded by extra text
        if not result_text.startswith('{'):
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result_text = result_text[start:end + 1]

        return json.loads(result_text)

    except Exception as e:
        print(f"[ml_service] predict_disease_ml error: {e}")
        return _error_result(
            "Prediction Error",
            [f"Analysis failed: {str(e)}"],
            ["Please try again with a clearer, well-lit photo of the leaf."]
        )


# ══════════════════════════════════════════════════════════════════════════════
# FERTILIZER RECOMMENDATION  (LLaMA 3.3 70B via NVIDIA API)
# Output structure matches original local Random-Forest version exactly.
# ══════════════════════════════════════════════════════════════════════════════

def load_fertilizer_model():
    """Stub — no local model needed for API-based inference."""
    return None, None


def predict_fertilizer_ml(
    crop, soil_type,
    stage='', region='', problem='',
    temperature=30, humidity=60, moisture=40,
    nitrogen=20, phosphorous=15, potassium=5,
    **kwargs
):
    """
    Predict best fertilizer using NVIDIA LLaMA API.
    Returns EXACTLY the same dict structure as the original Random Forest version
    so fertilizer.py blueprint and frontend work without any changes.
    """
    try:
        prompt = f"""You are an expert Indian agricultural scientist with deep knowledge of fertilizers, soil science, and crop nutrition.

Analyze these field conditions and give a precise fertilizer recommendation:
- Crop: {crop}
- Soil Type: {soil_type}
- Growth Stage: {stage}
- Region/Climate: {region}
- Current Problem: {problem if problem else 'None reported'}
- Soil N-P-K (estimated): N={nitrogen}, P={phosphorous}, K={potassium}
- Temperature: {temperature}°C, Humidity: {humidity}%, Moisture: {moisture}%

Return ONLY a valid JSON object with EXACTLY this structure, no extra text, no markdown:
{{
    "primary_fertilizer": {{
        "name": "DAP",
        "commercial_name": "DAP — Di-Ammonium Phosphate (डीएपी)",
        "npk_ratio": "18-46-0",
        "quantity_per_acre": "50-75 kg/acre",
        "cost_inr": "₹1,350–1,500/bag (50 kg)",
        "confidence": 88.5
    }},
    "secondary_nutrients": [
        {{"name": "Zinc Sulphate", "quantity": "10 kg/acre", "purpose": "Improves phosphorus uptake"}}
    ],
    "organic_alternative": "Bone meal (200 kg/acre) + Rock phosphate",
    "application_method": "Apply as basal dose — place 5-7 cm deep near root zone.",
    "timing": "At or just before sowing as basal application",
    "dos": [
        "Apply as basal dose at sowing",
        "Combine with organic manure",
        "Mix into moist soil"
    ],
    "donts": [
        "Do not top-dress",
        "Do not apply to waterlogged soil",
        "Never mix with urea for storage"
    ],
    "expected_improvement": "Stronger root development and 15-25% better flowering within 15-20 days.",
    "alternatives": [
        {{"name": "17-17-17", "confidence": 11.5}}
    ],
    "model_confidence": 88.5,
    "hindi": {{
        "fertilizer_name": "डीएपी (डाई-अमोनियम फॉस्फेट)",
        "commercial_name": "DAP — Di-Ammonium Phosphate (डीएपी)",
        "crop": "{_get_hindi_crop(crop)}",
        "soil_type": "{_get_hindi_soil(soil_type)}",
        "method": "बेसल खुराक के रूप में लगाएं — जड़ क्षेत्र के पास 5-7 सेमी गहराई में रखें।",
        "timing": "बुवाई के समय या ठीक पहले बेसल खुराक के रूप में",
        "dos": [
            "बुवाई के समय बेसल खुराक के रूप में लगाएं",
            "जैविक खाद के साथ मिलाएं",
            "नम मिट्टी में मिलाएं"
        ],
        "donts": [
            "कभी टॉप-ड्रेस न करें",
            "जलभरी मिट्टी पर न लगाएं",
            "यूरिया के साथ स्टोर में न मिलाएं"
        ],
        "improvement": "15-20 दिनों में मजबूत जड़ विकास और 15-25% बेहतर फूल आना।",
        "summary": "डीएपी (डाई-अमोनियम फॉस्फेट) — {_get_hindi_crop(crop)} के लिए {_get_hindi_soil(soil_type)} मिट्टी में उपयोग करें"
    }}
}}

Important rules:
- name must be a real fertilizer: Urea, DAP, 17-17-17, 14-35-14, 10-26-26, MOP, SSP, etc.
- npk_ratio must be accurate (e.g., Urea=46-0-0, DAP=18-46-0, MOP=0-0-60)
- cost_inr must be realistic Indian market price
- confidence and model_confidence must be same number between 70-98
- All Hindi text must be accurate Devanagari
- Return ONLY the JSON object"""

        response = client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.1
        )

        result_text = response.choices[0].message.content.strip()

        if not result_text:
            raise ValueError("Empty response from API")

        # Strip markdown fences
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        # Extract JSON object if surrounded by extra text
        if not result_text.startswith('{'):
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result_text = result_text[start:end + 1]

        result = json.loads(result_text)

        # ── Safety net: ensure all required top-level keys exist ──────────────
        result.setdefault('secondary_nutrients', [])
        result.setdefault('organic_alternative', 'Consult local agronomist for organic alternatives')
        result.setdefault('application_method', 'Broadcast and incorporate into soil before sowing')
        result.setdefault('timing', 'At sowing or as recommended by agronomist')
        result.setdefault('dos', ['Follow recommended dosage', 'Apply with irrigation'])
        result.setdefault('donts', ['Do not exceed recommended dose'])
        result.setdefault('expected_improvement', 'Expected improvement in crop health and yield.')
        result.setdefault('alternatives', [])
        result.setdefault('model_confidence', 80.0)

        primary = result.get('primary_fertilizer', {})
        primary.setdefault('commercial_name', f"{primary.get('name', 'Unknown')} Fertilizer")
        primary.setdefault('npk_ratio', 'Variable')
        primary.setdefault('quantity_per_acre', '50-100 kg/acre')
        primary.setdefault('cost_inr', '₹800–1,500/bag')
        primary.setdefault('confidence', result.get('model_confidence', 80.0))

        return result

    except Exception as e:
        print(f"[ml_service] predict_fertilizer_ml error: {e}")
        # ── Fallback with correct structure ───────────────────────────────────
        return {
            'primary_fertilizer': {
                'name': 'DAP',
                'commercial_name': 'DAP — Di-Ammonium Phosphate (डीएपी)',
                'npk_ratio': '18-46-0',
                'quantity_per_acre': '50-75 kg/acre',
                'cost_inr': '₹1,350–1,500/bag (50 kg)',
                'confidence': 75.0,
            },
            'secondary_nutrients': [
                {'name': 'Zinc Sulphate', 'quantity': '10 kg/acre', 'purpose': 'Micronutrient support'}
            ],
            'organic_alternative': 'Bone meal (200 kg/acre) + Rock phosphate',
            'application_method': 'Apply as basal dose — place 5-7 cm deep near root zone.',
            'timing': 'At sowing or just before as basal application',
            'dos': ['Apply as basal dose at sowing', 'Combine with organic manure', 'Mix into moist soil'],
            'donts': ['Do not top-dress', 'Do not apply to waterlogged soil'],
            'expected_improvement': 'Stronger root development and 15-25% better yield.',
            'alternatives': [],
            'model_confidence': 75.0,
            'hindi': {
                'fertilizer_name': 'डीएपी (डाई-अमोनियम फॉस्फेट)',
                'commercial_name': 'DAP — Di-Ammonium Phosphate (डीएपी)',
                'crop': _get_hindi_crop(crop),
                'soil_type': _get_hindi_soil(soil_type),
                'method': 'बेसल खुराक के रूप में लगाएं — जड़ क्षेत्र के पास 5-7 सेमी गहराई में रखें।',
                'timing': 'बुवाई के समय या ठीक पहले बेसल खुराक के रूप में',
                'dos': ['बुवाई के समय बेसल खुराक के रूप में लगाएं', 'जैविक खाद के साथ मिलाएं'],
                'donts': ['कभी टॉप-ड्रेस न करें', 'जलभरी मिट्टी पर न लगाएं'],
                'improvement': '15-20 दिनों में मजबूत जड़ विकास और बेहतर फूल आना।',
                'summary': f"डीएपी (डाई-अमोनियम फॉस्फेट) — {_get_hindi_crop(crop)} के लिए {_get_hindi_soil(soil_type)} मिट्टी में उपयोग करें",
            },
            'error_note': str(e),
        }


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _get_hindi_crop(crop: str) -> str:
    return {
        'Wheat': 'गेहूं', 'Rice': 'चावल/धान', 'Maize': 'मक्का', 'Sugarcane': 'गन्ना',
        'Cotton': 'कपास', 'Tomato': 'टमाटर', 'Potato': 'आलू', 'Soybean': 'सोयाबीन',
        'Onion': 'प्याज', 'Mustard': 'सरसों', 'Barley': 'जौ', 'Groundnut': 'मूंगफली',
        'Corn': 'मक्का', 'Pepper': 'मिर्च', 'Chickpea': 'चना', 'Lentil': 'मसूर',
    }.get(crop, crop)


def _get_hindi_soil(soil_type: str) -> str:
    return {
        'Sandy': 'रेतीली', 'Loamy': 'दोमट', 'Clay': 'चिकनी मिट्टी',
        'Clayey': 'चिकनी मिट्टी', 'Silty': 'गाद वाली', 'Peaty': 'पीट',
        'Chalky': 'चूना युक्त', 'Black': 'काली मिट्टी', 'Red': 'लाल मिट्टी',
    }.get(soil_type, soil_type)
