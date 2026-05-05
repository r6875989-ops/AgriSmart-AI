import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('JWT_SECRET', 'agrismart-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'agrismart.db')

    JWT_SECRET = os.getenv('JWT_SECRET', 'agrismart-secret-key-change-in-production')
    JWT_EXPIRY_DAYS = 7

    NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY', '')
    NVIDIA_BASE_URL = 'https://integrate.api.nvidia.com/v1'
    NVIDIA_VISION_MODEL = 'meta/llama-3.2-90b-vision-instruct'
    NVIDIA_TEXT_MODEL = 'meta/llama-3.3-70b-instruct'

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    RATE_LIMIT_PER_HOUR = 20

    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,http://localhost:3000,https://agri-smart-ai-six.vercel.app'
    ).split(',')
