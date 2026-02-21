# Scriptura Loquens - Backend Server

Flask backend server for the Scriptura Loquens application.

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Copy `.env.example` to `.env` and fill in your API keys:

   ```bash
   cp .env.example .env
   ```

   Required environment variables:

   - `GOOGLE_GEMINI_API_KEY` - Your Google Gemini API key
   - `GOOGLE_TTS_API_KEY` - Path to your Google Cloud credentials JSON file
   - `SECRET_KEY` - Flask secret key (change in production)
   - `DATABASE_URL` - Database URL (default: SQLite)

3. **Initialize the database:**
   The database will be created automatically on first run.

4. **Run the server:**

   ```bash
   python run.py
   ```

   Or:

   ```bash
   python -m app.main
   ```

   Server will run on `http://localhost:5000`

## Project Structure

```
server/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── main.py              # App entry point
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── routes/              # API routes
│   │   ├── pdf_routes.py
│   │   ├── chunk_routes.py
│   │   └── audio_routes.py
│   ├── services/            # Business logic
│   │   ├── pdf_service.py
│   │   ├── gemini_service.py
│   │   └── tts_service.py
│   └── utils/               # Utility functions
│       ├── file_handler.py
│       └── text_cleaner.py
├── uploads/                 # PDF uploads (created automatically)
├── audio/                   # Generated audio files (created automatically)
├── requirements.txt
├── .env.example
└── run.py
```

## API Endpoints

### PDF Routes

- `POST /api/upload-pdf` - Upload a PDF file
- `GET /api/pdf/<id>` - Get PDF metadata
- `GET /api/pdf/<id>/text` - Get extracted text
- `POST /api/pdf/<id>/process` - Process PDF (extract text, detect language, analyze chunks)
- `GET /api/pdfs` - List all PDFs

### Chunk Routes

- `GET /api/pdf/<id>/chunks` - Get all chunks for a PDF
- `GET /api/pdf/<id>/characters` - Get detected characters
- `POST /api/pdf/<id>/analyze` - Analyze text chunks (if not already done)

### Audio Routes

- `GET /api/pdf/<id>/voices` - Get available voices for PDF language
- `GET /api/pdf/<id>/voice-settings` - Get voice settings
- `PUT /api/pdf/<id>/voice-settings` - Update voice settings
- `POST /api/pdf/<id>/regenerate-audio` - Generate/regenerate audio files
- `GET /api/pdf/<id>/audio` - Get audio file metadata
- `GET /api/audio/<id>/file` - Download audio file
- `GET /api/audio/chunk/<chunk_id>` - Get audio for specific chunk

## Database Models

- **PDF** - PDF metadata and status
- **ExtractedText** - Raw and cleaned text
- **Chunk** - Text chunks with role and character
- **VoiceSetting** - Voice settings per character
- **AudioFile** - Generated audio files

## Notes

- PDFs are stored in `uploads/` directory
- Audio files are stored in `audio/` directory
- Database caching prevents reprocessing same PDFs
- Language is automatically detected from text
- TTS voices match detected language
