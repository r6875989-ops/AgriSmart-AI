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
import base64
import numpy as np
import joblib
from PIL import Image
import io

# ─── Lazy globals (loaded once on first call) ──────────────────────────────────
_tf_model           = None
_disease_classes    = None
_fertilizer_model   = None
_fertilizer_encoders = None

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


# ══════════════════════════════════════════════════════════════════════════════
# DISEASE DETECTION  (MobileNetV2 CNN)
# ══════════════════════════════════════════════════════════════════════════════

def load_disease_model():
    """Load CNN model and class mapping — lazy, called once."""
    global _tf_model, _disease_classes

    if _tf_model is None:
        model_path   = os.path.join(MODELS_DIR, 'disease_model.h5')
        classes_path = os.path.join(MODELS_DIR, 'disease_classes.pkl')

        if not os.path.exists(model_path):
            print(f"⚠️  Disease model not found: {model_path}")
            return None, None
        if not os.path.exists(classes_path):
            print(f"⚠️  Disease classes not found: {classes_path}")
            return None, None

        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        import tensorflow as tf

        _tf_model        = tf.keras.models.load_model(model_path)
        _disease_classes = joblib.load(classes_path)
        print(f"✅ Disease model loaded — {_disease_classes['num_classes']} classes, "
              f"accuracy={_disease_classes['accuracy']:.2%}")

    return _tf_model, _disease_classes


def predict_disease_ml(image_base64: str) -> dict:
    """
    Predict crop disease from a CLEAN base64 string (no data URL prefix).
    The caller (disease.py route) is responsible for stripping the prefix.

    Returns a dict with: disease_name, confidence, affected_crop,
                         symptoms, treatment, prevention, severity,
                         is_healthy, top_predictions
    """
    model, classes_data = load_disease_model()

    # ── Model not available ────────────────────────────────────────────────────
    if model is None or classes_data is None:
        return _error_result(
            "Model Not Loaded",
            ["Disease detection model not trained yet."],
            ["Run: python training/train_disease.py  to train the model first."]
        )

    try:
        # ── Decode image ───────────────────────────────────────────────────────
        img_bytes = base64.b64decode(image_base64)
        img       = Image.open(io.BytesIO(img_bytes)).convert('RGB')

        img_size  = classes_data.get('img_size', 224)
        img       = img.resize((img_size, img_size), Image.LANCZOS)

        # ── Normalise to [0, 1] ────────────────────────────────────────────────
        img_array = np.array(img, dtype=np.float32) / 255.0
        img_array = np.expand_dims(img_array, axis=0)   # shape: (1, 224, 224, 3)

        # ── Run inference ──────────────────────────────────────────────────────
        predictions  = model.predict(img_array, verbose=0)
        predicted_idx = int(np.argmax(predictions[0]))
        confidence    = float(np.max(predictions[0]) * 100)

        # ── FIX 1: disease_info key may be int OR str depending on joblib/json ─
        disease_info = classes_data.get('disease_info', {})
        info = _safe_get(disease_info, predicted_idx)

        class_name = info.get('class_name', 'Unknown')
        crop       = info.get('crop',       'Unknown')
        disease    = info.get('disease',    'Unknown')
        is_healthy = info.get('is_healthy', False)

        # ── Top-3 predictions ──────────────────────────────────────────────────
        top3_indices = np.argsort(predictions[0])[::-1][:3]
        top3 = []
        for idx in top3_indices:
            idx = int(idx)
            d = _safe_get(disease_info, idx)   # FIX: same key-type fix
            top3.append({
                'class':      d.get('disease', 'Unknown'),
                'crop':       d.get('crop',    'Unknown'),
                'confidence': round(float(predictions[0][idx] * 100), 1),
            })

        # ── Remedies ───────────────────────────────────────────────────────────
        treatments, symptoms, prevention, hindi_remedies = get_disease_remedies(class_name, disease, crop)

        # ── Severity ───────────────────────────────────────────────────────────
        if is_healthy:
            severity = "None"
        elif confidence >= 85:
            severity = "High"
        elif confidence >= 60:
            severity = "Medium"
        else:
            severity = "Low"

        # ── Hindi translations ─────────────────────────────────────────────────
        hindi = _get_disease_hindi(disease if not is_healthy else 'Healthy', crop, severity, is_healthy, hindi_remedies)

        return {
            'disease_name':    disease if not is_healthy else 'Healthy',
            'confidence':      round(confidence, 1),
            'affected_crop':   crop,
            'symptoms':        symptoms,
            'treatment':       treatments,
            'prevention':      prevention,
            'severity':        severity,
            'is_healthy':      is_healthy,
            'top_predictions': top3,
            'hindi':           hindi,
        }

    except Exception as e:
        print(f"[ml_service] predict_disease_ml error: {e}")
        return _error_result(
            "Prediction Error",
            [f"Internal error: {str(e)}"],
            ["Please try again with a clearer, well-lit photo of the leaf."]
        )


def _safe_get(disease_info: dict, idx: int) -> dict:
    """
    FIX for Bug 3: disease_info keys may be int or str depending on
    how joblib serialised the dict. Try both to be safe.
    """
    result = disease_info.get(idx)           # try int key first
    if result is None:
        result = disease_info.get(str(idx))  # fallback to str key
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
        'top_predictions': [],
        'hindi':           {'disease_name': 'अज्ञात', 'crop': 'अज्ञात', 'severity': 'अज्ञात', 'symptoms': [], 'treatment': [], 'prevention': []},
    }


def _get_disease_hindi(disease, crop, severity, is_healthy, hindi_remedies):
    """Build Hindi translation sub-object for disease result."""
    crop_hindi = {
        'Tomato': 'टमाटर', 'Potato': 'आलू', 'Corn': 'मक्का', 'Pepper': 'मिर्च',
        'Apple': 'सेब', 'Grape': 'अंगूर', 'Strawberry': 'स्ट्रॉबेरी',
        'Cherry': 'चेरी', 'Peach': 'आड़ू', 'Squash': 'कद्दू',
    }.get(crop, crop)

    severity_hindi = {
        'High': 'गंभीर', 'Medium': 'मध्यम', 'Low': 'कम', 'None': 'कोई नहीं', 'Unknown': 'अज्ञात'
    }.get(severity, severity)

    disease_hindi_map = {
        'Healthy': 'स्वस्थ',
        'Bacterial_spot': 'बैक्टीरियल स्पॉट (जीवाणु धब्बा)',
        'Early_blight': 'अर्ली ब्लाइट (अगेती अंगमारी)',
        'Late_blight': 'लेट ब्लाइट (पछेती अंगमारी)',
        'Leaf_Mold': 'लीफ मोल्ड (पत्ती फफूंद)',
        'Septoria_leaf_spot': 'सेप्टोरिया लीफ स्पॉट (पत्ती धब्बा)',
        'Spider_mites': 'स्पाइडर माइट्स (मकड़ी कीट)',
        'Target_Spot': 'टार्गेट स्पॉट (निशाना धब्बा)',
        'YellowLeaf_Curl_Virus': 'पीली पत्ती मरोड़ वायरस',
        'mosaic_virus': 'मोज़ेक वायरस',
    }
    disease_name_hi = disease_hindi_map.get(disease, disease)

    status = 'पौधा स्वस्थ है ✅' if is_healthy else f'रोग पाया गया: {disease_name_hi}'

    return {
        'disease_name': disease_name_hi,
        'crop': crop_hindi,
        'severity': severity_hindi,
        'status': status,
        'symptoms': hindi_remedies.get('symptoms_hi', []),
        'treatment': hindi_remedies.get('treatment_hi', []),
        'prevention': hindi_remedies.get('prevention_hi', []),
    }


def get_disease_remedies(class_name: str, disease: str, crop: str):
    """
    Match a disease class name to treatment/symptom/prevention lists.

    FIX for Bug 4: normalize strings before matching — collapses double
    underscores (e.g. 'Tomato__Tomato_YellowLeaf__Curl_Virus') so the
    key 'YellowLeaf_Curl_Virus' matches correctly.
    """

    remedies = {
        'Bacterial_spot': {
            'symptoms': [
                'Small, dark, water-soaked spots on leaves',
                'Spots may have yellow halos around them',
                'Leaves may curl and drop prematurely',
            ],
            'treatment': [
                'Apply copper-based bactericide (Kocide 3000) immediately',
                'Remove and destroy all infected plant parts',
                'Spray Streptomycin sulfate (0.5 g/L) weekly',
                'Use disease-free certified seeds for next season',
            ],
            'prevention': [
                'Use disease-resistant varieties',
                'Avoid overhead irrigation — use drip instead',
                'Practice 3-year crop rotation',
                'Maintain proper plant spacing for air circulation',
            ],
            'symptoms_hi': [
                'पत्तियों पर छोटे, गहरे, पानी से भीगे धब्बे',
                'धब्बों के चारों ओर पीले घेरे हो सकते हैं',
                'पत्तियाँ मुड़ सकती हैं और समय से पहले गिर सकती हैं',
            ],
            'treatment_hi': [
                'तुरंत कॉपर-आधारित बैक्टेरीसाइड (कोसाइड 3000) लगाएं',
                'सभी संक्रमित पौधों के भागों को हटाकर नष्ट करें',
                'हर हफ्ते स्ट्रेप्टोमाइसिन सल्फेट (0.5 ग्राम/लीटर) का छिड़काव करें',
                'अगले सीज़न के लिए रोग-मुक्त प्रमाणित बीज का उपयोग करें',
            ],
            'prevention_hi': [
                'रोग-प्रतिरोधी किस्मों का उपयोग करें',
                'ऊपर से सिंचाई से बचें — ड्रिप सिंचाई का उपयोग करें',
                '3 साल का फसल चक्र अपनाएं',
                'हवा के आने-जाने के लिए पौधों के बीच उचित दूरी बनाए रखें',
            ],
        },
        'Early_blight': {
            'symptoms': [
                'Dark brown concentric rings on lower leaves (target-like pattern)',
                'Yellowing around the lesions',
                'Premature leaf drop starting from bottom of plant',
            ],
            'treatment': [
                'Apply Mancozeb (2.5 g/L) or Chlorothalonil fungicide',
                'Remove infected lower leaves immediately',
                'Apply Trichoderma viride as bio-control agent',
                'Spray Neem oil solution (5 ml/L) every 7 days',
            ],
            'prevention': [
                'Mulch around plants to prevent soil splash onto leaves',
                'Water at plant base — never on foliage',
                'Rotate crops every 2–3 years',
                'Use certified disease-free seeds',
            ],
            'symptoms_hi': [
                'निचली पत्तियों पर गहरे भूरे रंग के गोल छल्ले (निशाने जैसा)',
                'घावों के आसपास पीलापन',
                'पौधे के नीचे से पत्तियाँ समय से पहले गिरना',
            ],
            'treatment_hi': [
                'मैंकोज़ेब (2.5 ग्राम/लीटर) या क्लोरोथालोनिल फफूंदनाशक लगाएं',
                'संक्रमित निचली पत्तियों को तुरंत हटा दें',
                'जैविक नियंत्रण के लिए ट्राइकोडर्मा विरिडी लगाएं',
                'हर 7 दिन में नीम तेल (5 मिली/लीटर) का छिड़काव करें',
            ],
            'prevention_hi': [
                'पत्तियों पर मिट्टी के छींटे रोकने के लिए मल्चिंग करें',
                'पौधे के तने पर पानी दें — पत्तियों पर कभी नहीं',
                'हर 2-3 साल में फसल चक्र बदलें',
                'प्रमाणित रोग-मुक्त बीजों का उपयोग करें',
            ],
        },
        'Late_blight': {
            'symptoms': [
                'Large, irregular water-soaked patches on leaves',
                'White fuzzy mold visible on leaf undersides',
                'Rapid browning and wilting of entire plant',
            ],
            'treatment': [
                'Apply Metalaxyl + Mancozeb (Ridomil Gold) immediately',
                'Remove and burn all infected plants — do not compost',
                'Apply Cymoxanil fungicide as preventive spray',
                'Spray Bordeaux mixture (1%) every 5–7 days',
            ],
            'prevention': [
                'Plant resistant varieties (e.g. Kufri Jyoti for potato)',
                'Avoid excessive irrigation',
                'Monitor weather — high humidity greatly increases risk',
                'Destroy all crop debris after harvest',
            ],
            'symptoms_hi': [
                'पत्तियों पर बड़े, अनियमित पानी से भरे धब्बे',
                'पत्तियों के नीचे सफेद रुई जैसी फफूंद दिखाई देना',
                'पूरे पौधे का तेजी से भूरा होना और मुरझाना',
            ],
            'treatment_hi': [
                'तुरंत मेटालैक्सिल + मैंकोज़ेब (रिडोमिल गोल्ड) लगाएं',
                'सभी संक्रमित पौधों को हटाकर जला दें — खाद न बनाएं',
                'रोकथाम के लिए सायमोक्सनिल फफूंदनाशक का छिड़काव करें',
                'हर 5-7 दिन में बोर्डो मिश्रण (1%) का छिड़काव करें',
            ],
            'prevention_hi': [
                'प्रतिरोधी किस्में लगाएं (जैसे आलू के लिए कुफरी ज्योति)',
                'अत्यधिक सिंचाई से बचें',
                'मौसम पर नज़र रखें — उच्च आर्द्रता से खतरा बहुत बढ़ जाता है',
                'फसल कटाई के बाद सभी अवशेष नष्ट कर दें',
            ],
        },
        'Leaf_Mold': {
            'symptoms': [
                'Yellow spots on upper leaf surface',
                'Olive-green to brown velvety growth on lower surface',
                'Leaves may curl and wither in severe cases',
            ],
            'treatment': [
                'Apply Chlorothalonil (Daconil) fungicide',
                'Improve greenhouse or field ventilation immediately',
                'Prune lower leaves to increase air circulation',
                'Apply sulfur-based fungicide every 7–10 days',
            ],
            'prevention': [
                'Maintain relative humidity below 85%',
                'Ensure good air circulation between plants',
                'Avoid leaf wetness by watering at base',
                'Use drip irrigation instead of overhead sprinklers',
            ],
            'symptoms_hi': [
                'पत्तियों की ऊपरी सतह पर पीले धब्बे',
                'निचली सतह पर जैतूनी-हरे से भूरे रंग की मखमली वृद्धि',
                'गंभीर मामलों में पत्तियाँ मुड़ सकती हैं और सूख सकती हैं',
            ],
            'treatment_hi': [
                'क्लोरोथालोनिल (डाकोनिल) फफूंदनाशक लगाएं',
                'ग्रीनहाउस या खेत में हवा का प्रवाह तुरंत बढ़ाएं',
                'हवा के आने-जाने के लिए निचली पत्तियों की छँटाई करें',
                'हर 7-10 दिन में सल्फर-आधारित फफूंदनाशक लगाएं',
            ],
            'prevention_hi': [
                'आर्द्रता 85% से नीचे बनाए रखें',
                'पौधों के बीच अच्छे हवा प्रवाह को सुनिश्चित करें',
                'तने पर पानी देकर पत्ती की नमी से बचें',
                'ऊपरी स्प्रिंकलर के बजाय ड्रिप सिंचाई का उपयोग करें',
            ],
        },
        'Septoria_leaf_spot': {
            'symptoms': [
                'Small circular spots with dark borders and tan/grey centres',
                'Tiny black dots (pycnidia) visible in the centre of spots',
                'Lower leaves affected first, disease progresses upward',
            ],
            'treatment': [
                'Apply Chlorothalonil or Mancozeb fungicide weekly',
                'Remove heavily infected leaves and destroy them',
                'Apply copper fungicide as backup spray',
                'Use Azoxystrobin (Amistar) for severe cases',
            ],
            'prevention': [
                'Mulch soil to prevent rain splash carrying spores',
                'Rotate crops for minimum 2 years',
                'Stake plants to improve air flow',
                'Water at plant base in morning only',
            ],
            'symptoms_hi': [
                'गहरे किनारों और भूरे/धूसर केंद्र वाले छोटे गोल धब्बे',
                'धब्बों के बीच में छोटे काले बिंदु (पिक्निडिया) दिखाई देना',
                'पहले निचली पत्तियाँ प्रभावित होती हैं, रोग ऊपर की ओर बढ़ता है',
            ],
            'treatment_hi': [
                'हर सप्ताह क्लोरोथालोनिल या मैंकोज़ेब फफूंदनाशक लगाएं',
                'अत्यधिक संक्रमित पत्तियों को हटाकर नष्ट कर दें',
                'बैकअप स्प्रे के रूप में कॉपर फफूंदनाशक लगाएं',
                'गंभीर मामलों में एज़ोक्सीस्ट्रोबिन (अमिस्टार) का उपयोग करें',
            ],
            'prevention_hi': [
                'बीजाणुओं को फैलने से रोकने के लिए मिट्टी पर मल्चिंग करें',
                'कम से कम 2 साल का फसल चक्र अपनाएं',
                'हवा के प्रवाह के लिए पौधों को सहारा/खूंटी दें',
                'केवल सुबह में पौधे के तने पर पानी दें',
            ],
        },
        'Spider_mites': {
            'symptoms': [
                'Fine stippling (tiny yellow dots) across leaves',
                'Fine webbing visible on leaf undersides',
                'Leaves become bronze or yellow and eventually dry out',
            ],
            'treatment': [
                'Spray Abamectin (Vertimec) miticide at label rate',
                'Apply Neem oil spray (3–5 ml/L) every 5–7 days',
                'Release predatory mites (Phytoseiulus persimilis)',
                'Knock mites off with a strong jet of water first',
            ],
            'prevention': [
                'Maintain adequate soil moisture — mites thrive in drought',
                'Avoid excessive nitrogen fertilisation',
                'Introduce beneficial insects (ladybirds, lacewings)',
                'Inspect leaf undersides weekly during hot dry weather',
            ],
            'symptoms_hi': [
                'पत्तियों पर बारीक छोटे पीले बिंदु (स्टिपलिंग)',
                'पत्तियों के नीचे बारीक जाले दिखाई देना',
                'पत्तियाँ कांस्य या पीली हो जाती हैं और अंत में सूख जाती हैं',
            ],
            'treatment_hi': [
                'एबामेक्टिन (वर्टिमेक) माइटीसाइड का निर्धारित दर पर छिड़काव करें',
                'हर 5-7 दिन में नीम तेल (3-5 मिली/लीटर) का छिड़काव करें',
                'शिकारी माइट्स (फाइटोसीयुलस पर्सिमिलिस) छोड़ें',
                'पहले पानी की तेज धार से कीटों को हटाएं',
            ],
            'prevention_hi': [
                'मिट्टी में पर्याप्त नमी बनाए रखें — सूखे में कीट बढ़ते हैं',
                'अत्यधिक नाइट्रोजन उर्वरक से बचें',
                'लाभकारी कीट (लेडीबर्ड, लेसविंग) छोड़ें',
                'गर्म शुष्क मौसम में हर हफ्ते पत्तियों के नीचे जांच करें',
            ],
        },
        'Target_Spot': {
            'symptoms': [
                'Brown spots with concentric rings forming a target pattern',
                'Spots appear on leaves, stems, and fruit',
                'Severe defoliation in advanced stages',
            ],
            'treatment': [
                'Apply Azoxystrobin + Difenoconazole (e.g. Amistar Top)',
                'Remove and dispose of infected plant debris',
                'Spray Mancozeb (2.5 g/L) every 7–10 days',
                'Apply bio-fungicide Bacillus subtilis as supplement',
            ],
            'prevention': [
                'Use certified pathogen-free transplants',
                'Avoid working in wet fields to prevent spread',
                'Maintain proper plant spacing',
                'Practice 2–3 year crop rotation',
            ],
            'symptoms_hi': [
                'भूरे धब्बे जिनमें गोल छल्ले निशाने जैसा पैटर्न बनाते हैं',
                'पत्तियों, तनों और फलों पर धब्बे दिखाई देना',
                'गंभीर अवस्था में पत्तियों का अत्यधिक झड़ना',
            ],
            'treatment_hi': [
                'एज़ोक्सीस्ट्रोबिन + डाइफेनोकोनाज़ोल (जैसे अमिस्टार टॉप) लगाएं',
                'संक्रमित पौधों के अवशेषों को हटाकर निपटान करें',
                'हर 7-10 दिन में मैंकोज़ेब (2.5 ग्राम/लीटर) का छिड़काव करें',
                'पूरक के रूप में जैव-फफूंदनाशक बैसिलस सबटिलिस लगाएं',
            ],
            'prevention_hi': [
                'प्रमाणित रोगाणु-मुक्त पौध का उपयोग करें',
                'फैलाव रोकने के लिए गीले खेतों में काम करने से बचें',
                'पौधों के बीच उचित दूरी बनाए रखें',
                '2-3 साल का फसल चक्र अपनाएं',
            ],
        },
        'YellowLeaf_Curl_Virus': {
            'symptoms': [
                'Upward curling of leaf margins (cupping)',
                'Yellowing and stunting of all new growth',
                'Drastically reduced fruit set and very small fruits',
            ],
            'treatment': [
                'Remove and destroy all infected plants immediately — no cure',
                'Control whitefly vectors with Imidacloprid spray',
                'Place yellow sticky traps around the field perimeter',
                'Focus on prevention — no chemical cures this virus',
            ],
            'prevention': [
                'Use certified virus-resistant varieties (e.g. Arka Rakshak)',
                'Cover nursery beds with 40-mesh insect-proof nylon net',
                'Eliminate whitefly populations before and during season',
                'Never plant near fields already showing infection',
            ],
            'symptoms_hi': [
                'पत्तियों के किनारे ऊपर की ओर मुड़ना (कपिंग)',
                'सभी नई वृद्धि का पीला पड़ना और बौनापन',
                'फलों की संख्या में भारी कमी और बहुत छोटे फल',
            ],
            'treatment_hi': [
                'सभी संक्रमित पौधों को तुरंत हटाकर नष्ट करें — कोई इलाज नहीं',
                'इमिडाक्लोप्रिड छिड़काव से सफेद मक्खी को नियंत्रित करें',
                'खेत के चारों ओर पीले चिपचिपे जाल लगाएं',
                'रोकथाम पर ध्यान दें — कोई रासायनिक दवा इस वायरस का इलाज नहीं करती',
            ],
            'prevention_hi': [
                'प्रमाणित वायरस-प्रतिरोधी किस्मों का उपयोग करें (जैसे अर्का रक्षक)',
                'नर्सरी बेड को 40-मेश कीट-रोधी नायलॉन जाल से ढकें',
                'सीज़न से पहले और दौरान सफेद मक्खी की आबादी को खत्म करें',
                'पहले से संक्रमित खेतों के पास कभी न लगाएं',
            ],
        },
        'mosaic_virus': {
            'symptoms': [
                'Light and dark green mosaic pattern across leaves',
                'Leaf distortion, curling, and puckering',
                'Stunted plant growth and significantly reduced yield',
            ],
            'treatment': [
                'Remove and destroy all infected plants immediately',
                'Control aphid vectors with appropriate insecticide',
                'Disinfect all tools with 10% bleach solution between plants',
                'No chemical cure — prevention is the only strategy',
            ],
            'prevention': [
                'Use only virus-free certified seeds or transplants',
                'Control aphid populations with sticky traps + insecticides',
                'Wash hands thoroughly before handling plants',
                'Keep tobacco users away from tomato crops (TMV risk)',
            ],
            'symptoms_hi': [
                'पत्तियों पर हल्के और गहरे हरे रंग का मोज़ेक पैटर्न',
                'पत्तियों का विकृत होना, मुड़ना और सिकुड़ना',
                'पौधे की वृद्धि रुकना और उपज में भारी कमी',
            ],
            'treatment_hi': [
                'सभी संक्रमित पौधों को तुरंत हटाकर नष्ट करें',
                'उचित कीटनाशक से एफिड (चेपा) कीट को नियंत्रित करें',
                'पौधों के बीच सभी औज़ारों को 10% ब्लीच से कीटाणुरहित करें',
                'कोई रासायनिक इलाज नहीं — रोकथाम ही एकमात्र उपाय है',
            ],
            'prevention_hi': [
                'केवल वायरस-मुक्त प्रमाणित बीज या पौध का उपयोग करें',
                'चिपचिपे जाल + कीटनाशकों से एफिड आबादी नियंत्रित करें',
                'पौधों को छूने से पहले हाथ अच्छी तरह धोएं',
                'तंबाकू उपयोगकर्ताओं को टमाटर की फसल से दूर रखें (TMV जोखिम)',
            ],
        },
        'healthy': {
            'symptoms': [
                'Plant appears healthy with normal green coloring',
                'No visible spots, lesions, or discoloration',
                'Normal leaf shape and vigorous growth pattern',
            ],
            'treatment': [
                'No treatment needed — your plant is healthy!',
                'Continue your current care practices',
                'Monitor weekly for any early signs of disease',
            ],
            'prevention': [
                'Maintain balanced NPK fertilisation schedule',
                'Water consistently at plant base — not on foliage',
                'Remove weeds and crop debris regularly',
                'Scout fields weekly to catch problems early',
            ],
            'symptoms_hi': [
                'पौधा स्वस्थ है, सामान्य हरा रंग दिख रहा है',
                'कोई दृश्य धब्बे, घाव या रंग बदलाव नहीं',
                'पत्ती का सामान्य आकार और जोरदार वृद्धि',
            ],
            'treatment_hi': [
                'कोई उपचार की आवश्यकता नहीं — आपका पौधा स्वस्थ है!',
                'अपनी वर्तमान देखभाल प्रक्रियाएं जारी रखें',
                'रोग के शुरुआती लक्षणों के लिए हर सप्ताह निगरानी करें',
            ],
            'prevention_hi': [
                'संतुलित NPK उर्वरक अनुसूची बनाए रखें',
                'पौधे के तने पर लगातार पानी दें — पत्तियों पर नहीं',
                'खरपतवार और फसल अवशेषों को नियमित रूप से हटाएं',
                'समस्याओं को जल्दी पकड़ने के लिए हर सप्ताह खेत का निरीक्षण करें',
            ],
        },
    }

    # ── FIX 4: Normalise strings before matching ───────────────────────────────
    # Collapse multiple underscores, strip leading/trailing, lowercase
    def normalise(s: str) -> str:
        import re
        return re.sub(r'_+', '_', s).strip('_').lower()

    norm_class   = normalise(class_name)
    norm_disease = normalise(disease)

    for key, remedy in remedies.items():
        key_norm = normalise(key)
        if key_norm in norm_class or key_norm in norm_disease:
            hindi = {
                'symptoms_hi': remedy.get('symptoms_hi', []),
                'treatment_hi': remedy.get('treatment_hi', []),
                'prevention_hi': remedy.get('prevention_hi', []),
            }
            return remedy['treatment'], remedy['symptoms'], remedy['prevention'], hindi

    # ── Default fallback ───────────────────────────────────────────────────────
    return (
        [
            'Consult your local agricultural extension officer',
            'Apply a broad-spectrum fungicide as a precaution',
            'Remove and destroy all visibly infected plant parts',
        ],
        [
            'Visible spots or unusual discoloration on leaves',
            'Abnormal growth patterns or leaf shape',
            'Possible wilting, curling, or premature leaf drop',
        ],
        [
            'Practice 2–3 year crop rotation',
            'Use disease-resistant certified varieties',
            'Maintain proper spacing and ventilation between plants',
        ],
        {
            'symptoms_hi': [
                'पत्तियों पर दिखाई देने वाले धब्बे या असामान्य रंग बदलाव',
                'असामान्य वृद्धि पैटर्न या पत्ती का आकार',
                'संभावित मुरझाना, मुड़ना या समय से पहले पत्ती गिरना',
            ],
            'treatment_hi': [
                'अपने स्थानीय कृषि विस्तार अधिकारी से परामर्श करें',
                'सावधानी के तौर पर एक व्यापक-स्पेक्ट्रम फफूंदनाशक लगाएं',
                'सभी दृश्य रूप से संक्रमित पौध भागों को हटाकर नष्ट करें',
            ],
            'prevention_hi': [
                '2-3 साल का फसल चक्र अपनाएं',
                'रोग-प्रतिरोधी प्रमाणित किस्मों का उपयोग करें',
                'पौधों के बीच उचित दूरी और हवादार वातावरण बनाए रखें',
            ],
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# FERTILIZER RECOMMENDATION  (Random Forest)
# ══════════════════════════════════════════════════════════════════════════════

def load_fertilizer_model():
    """Load Random Forest fertilizer model — lazy, called once."""
    global _fertilizer_model, _fertilizer_encoders

    if _fertilizer_model is None:
        model_path    = os.path.join(MODELS_DIR, 'fertilizer_model.pkl')
        encoders_path = os.path.join(MODELS_DIR, 'fertilizer_encoders.pkl')

        if not os.path.exists(model_path):
            print(f"⚠️  Fertilizer model not found: {model_path}")
            return None, None

        _fertilizer_model    = joblib.load(model_path)
        _fertilizer_encoders = joblib.load(encoders_path)
        acc = _fertilizer_encoders.get('accuracy', 0)
        print(f"✅ Fertilizer model loaded — accuracy: {acc:.2%}")

    return _fertilizer_model, _fertilizer_encoders


def predict_fertilizer_ml(
    crop, soil_type,
    temperature=30, humidity=60, moisture=40,
    nitrogen=20, phosphorous=15, potassium=5
):
    """Predict best fertilizer using trained Random Forest model."""
    model, encoders = load_fertilizer_model()

    if model is None:
        return {
            'error': 'Model not found. Run: python training/train_fertilizer.py',
            'primary_fertilizer': {
                'name': 'Model Not Loaded',
                'npk_ratio': 'N/A',
                'quantity_per_acre': 'N/A',
                'cost_inr': 'N/A',
            },
        }

    try:
        soil_enc   = encoders['soil_encoder']
        crop_enc   = encoders['crop_encoder']
        target_enc = encoders['target_encoder']

        soil_classes = list(soil_enc.classes_)
        crop_classes = list(crop_enc.classes_)

        soil_val = soil_type if soil_type in soil_classes else soil_classes[0]
        crop_val = crop      if crop in crop_classes      else crop_classes[0]

        soil_encoded = soil_enc.transform([soil_val])[0]
        crop_encoded = crop_enc.transform([crop_val])[0]

        # Feature engineering (must match training script exactly)
        npk_total             = nitrogen + potassium + phosphorous
        n_ratio               = nitrogen    / (npk_total + 1)
        p_ratio               = phosphorous / (npk_total + 1)
        k_ratio               = potassium   / (npk_total + 1)
        temp_humidity_ratio   = temperature / (humidity + 1)
        moisture_humidity_ratio = moisture  / (humidity + 1)

        features = np.array([[
            temperature, humidity, moisture,
            soil_encoded, crop_encoded,
            nitrogen, potassium, phosphorous,
            npk_total, n_ratio, p_ratio, k_ratio,
            temp_humidity_ratio, moisture_humidity_ratio,
        ]])

        prediction    = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        fertilizer    = target_enc.inverse_transform([prediction])[0]
        confidence    = float(np.max(probabilities) * 100)

        top3_indices = np.argsort(probabilities)[::-1][:3]
        alternatives = []
        for idx in top3_indices[1:]:
            alt_name = target_enc.inverse_transform([idx])[0]
            alt_conf = float(probabilities[idx] * 100)
            if alt_conf > 5:
                alternatives.append({'name': alt_name, 'confidence': round(alt_conf, 1)})

        details = get_fertilizer_details(fertilizer, crop, soil_type)

        # Commercial name mapping
        commercial_name = _get_commercial_name(fertilizer)

        # Hindi translations
        crop_hindi_map = {
            'Wheat': 'गेहूं', 'Rice': 'चावल/धान', 'Maize': 'मक्का', 'Sugarcane': 'गन्ना',
            'Cotton': 'कपास', 'Tomato': 'टमाटर', 'Potato': 'आलू', 'Soybean': 'सोयाबीन',
            'Onion': 'प्याज', 'Mustard': 'सरसों', 'Barley': 'जौ', 'Groundnut': 'मूंगफली',
        }
        soil_hindi_map = {
            'Sandy': 'रेतीली', 'Loamy': 'दोमट', 'Clay': 'चिकनी मिट्टी', 'Silty': 'गाद वाली',
            'Peaty': 'पीट', 'Chalky': 'चूना युक्त', 'Black': 'काली मिट्टी', 'Red': 'लाल मिट्टी',
        }

        hindi = {
            'fertilizer_name': _get_hindi_fertilizer_name(fertilizer),
            'commercial_name': commercial_name,
            'crop': crop_hindi_map.get(crop, crop),
            'soil_type': soil_hindi_map.get(soil_type, soil_type),
            'method': details.get('method_hi', details.get('method', '')),
            'timing': details.get('timing_hi', details.get('timing', '')),
            'dos': details.get('dos_hi', []),
            'donts': details.get('donts_hi', []),
            'improvement': details.get('improvement_hi', ''),
            'summary': f"{_get_hindi_fertilizer_name(fertilizer)} ({commercial_name}) — {crop_hindi_map.get(crop, crop)} के लिए {soil_hindi_map.get(soil_type, soil_type)} मिट्टी में उपयोग करें",
        }

        return {
            'primary_fertilizer': {
                'name':              fertilizer,
                'commercial_name':   commercial_name,
                'npk_ratio':         details['npk_ratio'],
                'quantity_per_acre': details['quantity'],
                'cost_inr':          details['cost'],
                'confidence':        round(confidence, 1),
            },
            'secondary_nutrients':    details.get('secondary', []),
            'organic_alternative':    details.get('organic', ''),
            'application_method':     details.get('method', ''),
            'timing':                 details.get('timing', ''),
            'dos':                    details.get('dos', []),
            'donts':                  details.get('donts', []),
            'expected_improvement':   details.get('improvement', ''),
            'alternatives':           alternatives,
            'model_confidence':       round(confidence, 1),
            'hindi':                  hindi,
        }

    except Exception as e:
        print(f"[ml_service] predict_fertilizer_ml error: {e}")
        return {
            'error': str(e),
            'primary_fertilizer': {
                'name': 'Prediction Error',
                'npk_ratio': 'N/A',
                'quantity_per_acre': 'N/A',
                'cost_inr': 'N/A',
            },
        }


def get_fertilizer_details(fertilizer_name: str, crop: str, soil_type: str) -> dict:
    """Return detailed fertilizer info including quantity, cost, dos/donts."""
    details = {
        'Urea': {
            'npk_ratio': '46-0-0',
            'quantity':  '100–130 kg/acre',
            'cost':      '₹270–320/bag (45 kg)',
            'secondary': [{'name': 'Zinc Sulphate', 'quantity': '10 kg/acre', 'purpose': 'Improves nitrogen uptake'}],
            'organic':   'Vermicompost (2 t/acre) + Azotobacter bio-fertilizer',
            'method':    'Split application — broadcast and incorporate before irrigation.',
            'timing':    '1st dose at sowing, 2nd at tillering, 3rd at flowering',
            'dos':   ['Apply before irrigation', 'Split into 2–3 doses', 'Apply in cool hours (morning/evening)'],
            'donts': ['Never apply on dry soil', 'Avoid just before heavy rain', 'Do not mix with SSP or lime'],
            'improvement': 'Expected 20–30% increase in vegetative growth within 7–10 days.',
            'method_hi':  'विभाजित प्रयोग — सिंचाई से पहले छिड़ककर मिट्टी में मिलाएं।',
            'timing_hi':  'पहली खुराक बुवाई पर, दूसरी कल्ले फूटने पर, तीसरी फूल आने पर',
            'dos_hi':     ['सिंचाई से पहले लगाएं', '2-3 खुराकों में बांटें', 'सुबह/शाम ठंडे समय में लगाएं'],
            'donts_hi':   ['सूखी मिट्टी पर कभी न लगाएं', 'भारी बारिश से ठीक पहले न दें', 'SSP या चूने के साथ न मिलाएं'],
            'improvement_hi': '7-10 दिनों में वनस्पति वृद्धि में 20-30% वृद्धि की उम्मीद।',
        },
        'DAP': {
            'npk_ratio': '18-46-0',
            'quantity':  '50–75 kg/acre',
            'cost':      '₹1,350–1,500/bag (50 kg)',
            'secondary': [{'name': 'Sulphur', 'quantity': '8 kg/acre', 'purpose': 'Enhances phosphorus efficiency'}],
            'organic':   'Bone meal (200 kg/acre) + Rock phosphate',
            'method':    'Apply as basal dose — place 5–7 cm deep near root zone.',
            'timing':    'At or just before sowing as basal application',
            'dos':   ['Apply as basal dose at sowing', 'Combine with organic manure', 'Mix into moist soil'],
            'donts': ['Do not top-dress', 'Do not apply to waterlogged soil', 'Never mix with urea for storage'],
            'improvement': 'Stronger root development and 15–25% better flowering within 15–20 days.',
            'method_hi':  'बेसल खुराक के रूप में लगाएं — जड़ क्षेत्र के पास 5-7 सेमी गहराई में रखें।',
            'timing_hi':  'बुवाई के समय या ठीक पहले बेसल खुराक के रूप में',
            'dos_hi':     ['बुवाई के समय बेसल खुराक के रूप में लगाएं', 'जैविक खाद के साथ मिलाएं', 'नम मिट्टी में मिलाएं'],
            'donts_hi':   ['कभी टॉप-ड्रेस न करें', 'जलभरी मिट्टी पर न लगाएं', 'यूरिया के साथ स्टोर में न मिलाएं'],
            'improvement_hi': '15-20 दिनों में मजबूत जड़ विकास और 15-25% बेहतर फूल आना।',
        },
        '14-35-14': {
            'npk_ratio': '14-35-14',
            'quantity':  '80–100 kg/acre',
            'cost':      '₹1,200–1,400/bag (50 kg)',
            'secondary': [{'name': 'Boron', 'quantity': '2 kg/acre', 'purpose': 'Improves fruit setting'}],
            'organic':   'Cow dung compost + Bone meal + Wood ash combination',
            'method':    'Basal dose in furrows. Side-dress during growth if needed.',
            'timing':    'At sowing or transplanting as basal',
            'dos':   ['Apply in furrows at sowing', 'Ensure adequate soil moisture'],
            'donts': ['Avoid heavy application near seeds', 'Do not apply to very acidic soils without liming'],
            'improvement': 'Balanced nutrition — 20–25% better overall crop growth and quality.',
            'method_hi':  'बुवाई के समय नालियों में बेसल खुराक। जरूरत पड़ने पर वृद्धि के दौरान साइड-ड्रेस करें।',
            'timing_hi':  'बुवाई या रोपाई के समय बेसल खुराक के रूप में',
            'dos_hi':     ['बुवाई के समय नालियों में लगाएं', 'पर्याप्त मिट्टी नमी सुनिश्चित करें'],
            'donts_hi':   ['बीजों के पास अधिक मात्रा में न दें', 'बिना चूना मिलाए अम्लीय मिट्टी पर न लगाएं'],
            'improvement_hi': 'संतुलित पोषण — फसल वृद्धि और गुणवत्ता में 20-25% सुधार।',
        },
        '17-17-17': {
            'npk_ratio': '17-17-17',
            'quantity':  '80–100 kg/acre',
            'cost':      '₹1,400–1,600/bag (50 kg)',
            'secondary': [{'name': 'Magnesium Sulphate', 'quantity': '5 kg/acre', 'purpose': 'Chlorophyll synthesis'}],
            'organic':   'Balanced compost + Neem cake + Wood ash',
            'method':    'Broadcast evenly and incorporate into soil before sowing.',
            'timing':    'At sowing/planting — can split for long-duration crops',
            'dos':   ['Use for crops needing balanced nutrition', 'Combine with organic manure'],
            'donts': ['Do not over-apply near seeds', 'Avoid on heavily potash-rich soils'],
            'improvement': 'Complete balanced nutrition — 20–30% improvement in overall crop development.',
            'method_hi':  'बुवाई से पहले समान रूप से छिड़ककर मिट्टी में मिलाएं।',
            'timing_hi':  'बुवाई/रोपाई के समय — लंबी अवधि वाली फसलों के लिए विभाजित कर सकते हैं',
            'dos_hi':     ['संतुलित पोषण वाली फसलों के लिए उपयोग करें', 'जैविक खाद के साथ मिलाएं'],
            'donts_hi':   ['बीजों के पास अत्यधिक न दें', 'अत्यधिक पोटाश वाली मिट्टी पर न लगाएं'],
            'improvement_hi': 'पूर्ण संतुलित पोषण — समग्र फसल विकास में 20-30% सुधार।',
        },
    }

    info = details.get(fertilizer_name, {
        'npk_ratio': 'Variable',
        'quantity':  '50–100 kg/acre',
        'cost':      '₹800–1,500/bag',
        'secondary': [],
        'organic':   'Consult local agronomist for organic alternatives',
        'method':    'Broadcast and incorporate into soil before sowing',
        'timing':    'At sowing or as recommended by agronomist',
        'dos':   ['Follow recommended dosage', 'Apply with irrigation'],
        'donts': ['Do not exceed recommended dose'],
        'improvement': 'Expected improvement in crop health and yield.',
        'method_hi':  'बुवाई से पहले मिट्टी में मिलाकर छिड़काव करें',
        'timing_hi':  'बुवाई के समय या कृषि विशेषज्ञ की सलाह अनुसार',
        'dos_hi':     ['निर्धारित मात्रा का पालन करें', 'सिंचाई के साथ लगाएं'],
        'donts_hi':   ['निर्धारित मात्रा से अधिक न दें'],
        'improvement_hi': 'फसल स्वास्थ्य और उपज में सुधार की उम्मीद।',
    })
    return info


def _get_commercial_name(fertilizer_code: str) -> str:
    """Map ML model output (often NPK codes) to commercial fertilizer names."""
    name_map = {
        'Urea': 'Urea (यूरिया)',
        'DAP': 'DAP — Di-Ammonium Phosphate (डीएपी)',
        '14-35-14': 'NPK Complex 14-35-14',
        '17-17-17': 'NPK Complex 17-17-17 (Suphala)',
        '10-26-26': 'NPK Complex 10-26-26',
        '20-20': 'Ammonium Phosphate 20-20 (अमोनियम फॉस्फेट)',
        '28-28': 'NPK Complex 28-28-0',
        '10-10-10': 'NPK Complex 10-10-10',
        '20-20-0': 'Ammonium Phosphate Sulphate (20-20-0)',
        '20-20-0-13': 'Ammonium Phosphate Sulphate (20-20-0-13S)',
        'SSP': 'Single Super Phosphate (SSP)',
        'MOP': 'Muriate of Potash (MOP — पोटाश)',
        'TSP': 'Triple Super Phosphate (TSP)',
        'CAN': 'Calcium Ammonium Nitrate (CAN)',
        'AS': 'Ammonium Sulphate (AS)',
    }
    return name_map.get(fertilizer_code, f'{fertilizer_code} Fertilizer')


def _get_hindi_fertilizer_name(fertilizer_code: str) -> str:
    """Return Hindi name for common fertilizers."""
    hindi_map = {
        'Urea': 'यूरिया',
        'DAP': 'डीएपी (डाई-अमोनियम फॉस्फेट)',
        '14-35-14': 'एनपीके कॉम्प्लेक्स 14-35-14',
        '17-17-17': 'एनपीके कॉम्प्लेक्स 17-17-17 (सुफला)',
        '10-26-26': 'एनपीके कॉम्प्लेक्स 10-26-26',
        '20-20': 'अमोनियम फॉस्फेट 20-20',
        '28-28': 'एनपीके कॉम्प्लेक्स 28-28-0',
        'SSP': 'सिंगल सुपर फॉस्फेट (एसएसपी)',
        'MOP': 'म्यूरेट ऑफ पोटाश (एमओपी)',
    }
    return hindi_map.get(fertilizer_code, fertilizer_code)