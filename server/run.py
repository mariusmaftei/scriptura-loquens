def _gemini_model():
    try:
        from google import genai  # noqa: F401
        return 'gemini-3-flash-preview'
    except ImportError:
        return 'gemini-1.5-flash'

if __name__ == '__main__':
    from app.config import Config
    host = '0.0.0.0'
    port = Config.PORT
    from app.main import app

    with app.app_context():
        uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        db_type = 'PostgreSQL' if 'postgresql' in uri else 'SQLite'
        db_name = uri.split('/')[-1].split('?')[0] if 'postgresql' in uri else uri.split('/')[-1] or 'scriptura_loquens'

        tts = (app.config.get('TTS_PROVIDER') or 'google').lower()
        tts_labels = {'edge': 'Microsoft Edge', 'google': 'Google Cloud TTS', 'elevenlabs': 'ElevenLabs'}

        default_model = _gemini_model()
        gemini_model = app.config.get('GEMINI_MODEL_ID') or default_model
        gemini_ok = bool(app.config.get('GOOGLE_GEMINI_API_KEY') or app.config.get('GOOGLE_API_KEY'))

    print()
    print("  +----------------------------------------------------------+")
    print("  |  Scriptura Loquens  -  Backend                           |")
    print("  +----------------------------------------------------------+")
    print(f"  |  Port      http://127.0.0.1:{port}")
    print(f"  |  Network   http://{host}:{port}")
    print("  +----------------------------------------------------------+")
    print(f"  |  Database  {db_type} ({db_name})")
    print("  +----------------------------------------------------------+")
    gemini_status = "OK" if gemini_ok else "no key"
    print(f"  |  AI        Gemini ({gemini_model}) [{gemini_status}]")
    print(f"  |  TTS       {tts_labels.get(tts, tts)}")
    print("  +----------------------------------------------------------+")
    print()

    app.run(debug=True, host=host, port=port)
