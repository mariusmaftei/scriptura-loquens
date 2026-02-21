import os
from dotenv import load_dotenv

load_dotenv()

SERVER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///scriptura_loquens.db'
    
    _upload = os.environ.get('UPLOAD_FOLDER') or os.path.join(SERVER_ROOT, 'uploads')
    _audio = os.environ.get('AUDIO_FOLDER') or os.path.join(SERVER_ROOT, 'audio')
    UPLOAD_FOLDER = os.path.abspath(_upload) if not os.path.isabs(_upload) else _upload
    AUDIO_FOLDER = os.path.abspath(_audio) if not os.path.isabs(_audio) else _audio
    
    _max_mb = int(os.environ.get('MAX_CONTENT_LENGTH_MB', '100'))
    MAX_CONTENT_LENGTH = _max_mb * 1024 * 1024
    MAX_PDF_PAGES = int(os.environ.get('MAX_PDF_PAGES', '5'))
    
    GOOGLE_GEMINI_API_KEY = os.environ.get('GOOGLE_GEMINI_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    GEMINI_MODEL_ID = os.environ.get('GEMINI_MODEL_ID')
    GEMINI_THINKING_LEVEL = (os.environ.get('GEMINI_THINKING_LEVEL') or '').strip().lower() or None
    GOOGLE_GENAI_USE_VERTEXAI = os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', '').lower() in ('1', 'true', 'yes')
    TTS_PROVIDER = (os.environ.get('TTS_PROVIDER') or 'google').lower()
    TTS_USE_CHIRP_HD = os.environ.get('TTS_USE_CHIRP_HD', '').lower() in ('1', 'true', 'yes')
    ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
    GOOGLE_TTS_CREDENTIALS_JSON = os.environ.get('GOOGLE_TTS_CREDENTIALS_JSON') or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    GOOGLE_TTS_API_KEY = os.environ.get('GOOGLE_TTS_API_KEY')
    GOOGLE_VISION_API_KEY = os.environ.get('GOOGLE_VISION_API_KEY')
    
    FRONTEND_URL = os.environ.get('FRONTEND_URL') or 'http://localhost:3000'
    FRONTEND_BUILD = os.environ.get('FRONTEND_BUILD')

    PORT = int(os.environ.get('PORT', '5000'))

    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@test.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin1'
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
