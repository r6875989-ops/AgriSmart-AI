import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('JWT_SECRET', 'agrismart-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'agrismart.db')
    
    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET', 'agrismart-secret-key-change-in-production')
    JWT_EXPIRY_DAYS = 7
    
    # NVIDIA API
    NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY', '')
    NVIDIA_BASE_URL = 'https://integrate.api.nvidia.com/v1'
    NVIDIA_VISION_MODEL = 'meta/llama-3.2-90b-vision-instruct'
    NVIDIA_TEXT_MODEL = 'meta/llama-3.3-70b-instruct'
    
    # File Upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Rate Limiting
    RATE_LIMIT_PER_HOUR = 20
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
