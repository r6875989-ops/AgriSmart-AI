import json
from openai import OpenAI
from config import Config

# Initialize NVIDIA-compatible OpenAI client
client = None

def get_client():
    """Get or create NVIDIA API client"""
    global client
    if client is None:
        client = OpenAI(
            base_url=Config.NVIDIA_BASE_URL,
            api_key=Config.NVIDIA_API_KEY
        )
    return client

def analyze_disease(image_base64):
    """Analyze crop disease from image using NVIDIA Vision model"""
    try:
        ai = get_client()
        
        response = ai.chat.completions.create(
            model=Config.NVIDIA_VISION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert agricultural plant pathologist. Always respond with valid JSON only, no extra text."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this crop/leaf image carefully.
Return ONLY a JSON object with these exact fields:
{
    "disease_name": "name of the disease or 'Healthy'",
    "confidence": 85,
    "affected_crop": "crop name",
    "symptoms": ["symptom 1", "symptom 2", "symptom 3"],
    "treatment": ["treatment step 1", "treatment step 2", "treatment step 3"],
    "prevention": ["prevention tip 1", "prevention tip 2", "prevention tip 3"],
    "severity": "Low or Medium or High",
    "is_healthy": false
}
Return ONLY the JSON, no markdown, no explanation."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1024,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        # Clean up potential markdown wrapping
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "disease_name": "Analysis Error",
            "confidence": 0,
            "affected_crop": "Unknown",
            "symptoms": ["Could not parse AI response"],
            "treatment": ["Please try again with a clearer image"],
            "prevention": [],
            "severity": "Unknown",
            "is_healthy": False,
            "raw_response": content if 'content' in dir() else "No response"
        }
    except Exception as e:
        return {
            "error": str(e),
            "disease_name": "Service Error",
            "confidence": 0,
            "affected_crop": "Unknown",
            "symptoms": [f"Error: {str(e)}"],
            "treatment": ["Please check your API key and try again"],
            "prevention": [],
            "severity": "Unknown",
            "is_healthy": False
        }

def recommend_fertilizer(crop, soil_type, stage, problem, region):
    """Get fertilizer recommendation using NVIDIA text model"""
    try:
        ai = get_client()
        
        response = ai.chat.completions.create(
            model=Config.NVIDIA_TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Indian agronomist. Always respond with valid JSON only, no extra text."
                },
                {
                    "role": "user",
                    "content": f"""A farmer in India needs fertilizer recommendation:
- Crop: {crop}
- Soil Type: {soil_type}
- Growth Stage: {stage}
- Problem: {problem or 'None reported'}
- Region/Climate: {region}

Provide detailed fertilizer recommendations as JSON:
{{
    "primary_fertilizer": {{
        "name": "fertilizer name",
        "npk_ratio": "N-P-K ratio",
        "quantity_per_acre": "amount in kg/acre",
        "cost_inr": "estimated cost in ₹"
    }},
    "secondary_nutrients": [
        {{"name": "nutrient name", "quantity": "amount", "purpose": "why needed"}}
    ],
    "organic_alternative": "organic option description",
    "application_method": "how to apply",
    "timing": "when to apply",
    "dos": ["do this", "do that"],
    "donts": ["don't do this", "don't do that"],
    "expected_improvement": "expected result description"
}}
Return ONLY the JSON, no markdown, no explanation."""
                }
            ],
            max_tokens=1024,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "Could not parse AI response", "raw": content if 'content' in dir() else ""}
    except Exception as e:
        return {"error": str(e)}

def predict_price(crop, state, month, quantity=None):
    """Predict market price using NVIDIA text model"""
    try:
        ai = get_client()
        
        response = ai.chat.completions.create(
            model=Config.NVIDIA_TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an agricultural market analyst specializing in Indian crop markets and mandi prices. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": f"""Provide market price prediction for Indian crop market:
- Crop: {crop}
- State: {state}
- Month: {month}
- Quantity: {quantity or 'Not specified'} quintals

Return ONLY JSON:
{{
    "current_price_min": 2000,
    "current_price_max": 2400,
    "predicted_30_days": 2600,
    "predicted_60_days": 2800,
    "trend": "rising or falling or stable",
    "advice": "detailed market advice for the farmer",
    "best_sell_window": "recommended time period to sell",
    "factors": ["factor 1 affecting price", "factor 2", "factor 3"],
    "msp": 2015,
    "price_history": [
        {{"month": "Jan", "price": 2000}},
        {{"month": "Feb", "price": 2100}},
        {{"month": "Mar", "price": 2200}},
        {{"month": "Apr", "price": 2300}},
        {{"month": "May", "price": 2400}},
        {{"month": "Jun", "price": 2500}}
    ]
}}
Return ONLY the JSON, no markdown."""
                }
            ],
            max_tokens=1024,
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "Could not parse AI response", "raw": content if 'content' in dir() else ""}
    except Exception as e:
        return {"error": str(e)}

def process_voice(transcript, language='hi'):
    """Process voice transcript - detect intent and generate response"""
    try:
        ai = get_client()
        
        lang_instruction = "Respond in Hindi (Devanagari script)" if language == 'hi' else "Respond in English"
        
        response = ai.chat.completions.create(
            model=Config.NVIDIA_TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful Indian farming assistant. {lang_instruction}. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": f"""User said (in {'Hindi/Hinglish' if language == 'hi' else 'English'}): "{transcript}"

Identify the intent and provide a helpful farming response.
Return ONLY JSON:
{{
    "intent": "disease_detection or fertilizer_recommendation or price_query or general_farming_query",
    "crop": "detected crop name or null",
    "location": "detected location or null",
    "query_summary": "brief summary of the query in English",
    "response_text": "detailed helpful response in English",
    "response_hindi": "detailed helpful response in Hindi (Devanagari script)",
    "module_triggered": "disease or fertilizer or price or general"
}}
Return ONLY the JSON, no markdown."""
                }
            ],
            max_tokens=1024,
            temperature=0.5
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "Could not parse AI response", "raw": content if 'content' in dir() else ""}
    except Exception as e:
        return {"error": str(e)}
