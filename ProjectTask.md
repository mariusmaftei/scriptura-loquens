# Project Task List: Scriptura Loquens

## Project Overview

An AI-powered application that processes Bible PDFs, extracts and categorizes text by narrator and character speech, then generates multi-voice audio narration with distinct voices for narrator and different characters.

## Suggested App Name

**Scriptura Loquens** (Latin: "Speaking Scripture") - Already matches your workspace name!

## Technologies Stack

### Frontend

- **React** - UI framework
- **React Router** - Navigation
- **Axios/Fetch** - API communication
- **react-dropzone** - PDF file upload with drag-and-drop
- **react-audio-player** or **react-h5-audio-player** - Audio playback controls
- **Context API** - State management (simpler for MVP)
- **Zustand** (optional) - If state becomes complex
- **react-query** or **SWR** - API data fetching and caching

### Backend

- **Python** - Core processing logic
- **Flask** - REST API framework
- **SQLite** (MVP) → **PostgreSQL** (Production) - Relational database
  - **Why SQL?** Structured data with clear relationships (PDF → Text → Chunks → Audio)
  - **Why SQLite for MVP?** Zero setup, file-based, perfect for development
  - **Why PostgreSQL later?** Better for production, concurrent users, advanced features
- **SQLAlchemy** - Database ORM (works with both SQLite and PostgreSQL)
- **Flask-Migrate** - Database migrations (Alembic wrapper)
- **Flask-CORS** - CORS handling
- **pdfplumber** (RECOMMENDED) - Better than PyPDF2 for text extraction, handles tables better
- **PyPDF2** (alternative) - Simpler but less accurate
- **OCR Libraries** (if needed): **Tesseract OCR** + **pytesseract** or **Google Cloud Vision API** - For scanned PDFs/image-based PDFs
- **python-docx** or **pypandoc** - Text cleaning/formatting
- **Google Gemini API** - Text analysis and chunk extraction
- **Language Detection**: **langdetect** or **polyglot** - Detect PDF language (English, Romanian, German, etc.)
- **Google Text-to-Speech (TTS)** or **ElevenLabs API** - Multi-voice audio generation (language-aware)
- **Speech-to-Text API** (optional): **Google Cloud Speech-to-Text** or **Whisper API** - For audio transcription
- **Flask-CORS** - CORS middleware
- **hashlib** - Generate PDF hash for duplicate detection
- **python-dotenv** - Environment variable management
- **requests** - HTTP client for API calls
- **python-multipart** - File upload handling

### AI Models & Services

- **Google Gemini** (Gemini Pro or Gemini Ultra)
  - Text extraction and chunking
  - Character/narrator identification
  - Speech classification
- **Google Cloud Text-to-Speech API** or **ElevenLabs API**
  - Multiple voice synthesis
  - Voice assignment per character/narrator
- **OCR/Transcription Services** (if needed)
  - **Tesseract OCR** (open-source, local) - For scanned PDFs
  - **Google Cloud Vision API** (cloud-based, better accuracy) - For image-based PDFs
  - **Google Cloud Speech-to-Text** or **OpenAI Whisper** - For audio transcription (if needed)

### Additional Tools

- **PDF.js** (optional) - Client-side PDF preview
- **Node.js** (optional) - Build tooling if needed
- **Docker** (optional) - Containerization

## MVP Project Tasks

### Phase 1: Project Setup & Database Schema

- [ ] Initialize React project (Vite recommended for faster setup)
- [ ] Set up Python backend project structure
- [ ] Create Flask application skeleton
- [ ] Set up SQLite database
- [ ] Design database schema (PDFs, extracted_text, chunks, audio_files)
- [ ] Create database models/tables
- [ ] Set up database migrations (if using ORM)
- [ ] Configure CORS for frontend-backend communication
- [ ] Set up environment variables (.env files)
- [ ] Create requirements.txt for Python dependencies

### Phase 2: PDF Processing & Database Storage

- [ ] Implement PDF upload endpoint
- [ ] Create PDF hash generation (SHA256) for duplicate detection
- [ ] Build database check: query if PDF already exists by hash
- [ ] Detect PDF type (text-based vs image-based/scanned)
- [ ] Create PDF text extraction module
  - [ ] Handle text-based PDFs (PyPDF2/pdfplumber)
  - [ ] **If OCR needed**: Add OCR module for scanned PDFs (Tesseract or Google Vision API)
- [ ] **Language Detection**: Detect document language (English, Romanian, German, etc.)
  - [ ] Use langdetect or polyglot library
  - [ ] Detect language from extracted text sample
  - [ ] Store language code and name in PDFs table
- [ ] Build text cleaning pipeline (remove headers, footers, page numbers)
- [ ] Implement text normalization (whitespace, formatting)
- [ ] Store extracted text in database with PDF metadata (including language)
- [ ] Add error handling for corrupted/invalid PDFs
- [ ] Create endpoint to return cleaned text (from DB if exists)

### Phase 3: AI Text Analysis & Chunking (with DB caching)

- [ ] Set up Google Gemini API integration
- [ ] Create prompt engineering for narrator/character identification
  - Detect Narrator speech
  - Detect Character speech and extract character names (e.g., "Moise", "Solomon", "David")
  - Identify when characters are speaking vs narrator
- [ ] Check database: if chunks already exist for this PDF, skip Gemini call
- [ ] Implement text chunking logic based on speech type
- [ ] Build classification system:
  - Role: 'narrator' or 'character'
  - Character name: NULL for narrator, actual name for characters (e.g., "Moise", "Solomon")
- [ ] Store chunks in database with metadata (role, text, position, character_name)
- [ ] Add endpoint to return structured chunks (from DB)
- [ ] Implement error handling and retry logic for API calls

### Phase 4: Text-to-Speech Integration (with DB caching)

- [ ] Research and select TTS service (Google TTS or ElevenLabs)
  - **Google TTS**: Multiple languages, SSML support, good quality
    - Supports: English (en), Romanian (ro), German (de), French (fr), Spanish (es), etc.
  - **ElevenLabs**: More natural voices, multilingual support
- [ ] Set up TTS API credentials
- [ ] Create language-aware voice mapping system:
  - Get detected language from PDF
  - Map language to available TTS voices for that language
  - Default voice mapping per language:
    - Narrator → Language-specific narrator voice
    - Each character → Language-specific character voice
- [ ] Implement voice selection logic:
  - Query available voices for detected language
  - Assign default voices based on language
  - Store language_code with voice settings
- [ ] Implement voice customization storage (user can change voices per character, but within same language)
- [ ] Check database: if audio already exists for chunks with same voice settings, skip TTS generation
- [ ] Implement TTS generation for each chunk using language-appropriate voice
- [ ] Store audio file paths/URLs in database with voice settings used
- [ ] Build audio file storage (local filesystem or cloud storage)
- [ ] Create endpoint to generate audio with custom voice settings (validate language matches)
- [ ] Add endpoint to retrieve existing audio from DB
- [ ] Add endpoint to update voice settings and regenerate audio if needed

### Phase 5: Frontend UI (MVP)

- [ ] Design and create main dashboard layout
- [ ] Build PDF upload component with drag-and-drop
- [ ] Create file upload progress indicator
- [ ] Build chunk visualization component:
  - Show narrator chunks vs character chunks
  - Display character names (e.g., "Moise", "Solomon")
  - Color-code or label by character
- [ ] Create voice customization interface:
  - List all detected characters (Narrator + Character names)
  - Voice selector dropdown for each character
  - Voice preview button
  - Save voice settings
- [ ] Create audio player component with basic controls (play/pause)
- [ ] Add loading states and error handling UI
- [ ] Create simple list view of processed PDFs

### Phase 6: Frontend-Backend Integration (MVP)

- [ ] Connect PDF upload to backend endpoint
- [ ] Handle duplicate PDF detection (show message if already processed)
- [ ] Connect chunk display with backend data (from DB)
- [ ] Connect TTS generation and audio playback
- [ ] Implement basic error handling and user feedback
- [ ] Add "Process PDF" button that checks DB first

### Phase 7: MVP Testing & Polish

- [ ] Test complete flow: upload → extract → analyze → TTS
- [ ] Test database caching (upload same PDF twice, verify no duplicate processing)
- [ ] Test AI chunking accuracy with sample Bible PDF
- [ ] Test TTS quality and voice consistency
- [ ] Basic error handling testing
- [ ] Create README with setup instructions

## Technical Considerations

### Database Recommendation: SQL (Relational Database)

**Recommended: SQLite (MVP) → PostgreSQL (Production)**

#### Why SQL/Relational Database?

✅ **Perfect fit for your data structure:**

- Clear relationships: PDF → Extracted Text → Chunks → Audio Files
- Foreign keys ensure data integrity
- Easy joins: "Get all chunks for PDF X"
- ACID transactions (important for data consistency)

✅ **Your use cases:**

- Check if PDF exists by hash → Simple `SELECT` query
- Get all chunks for a PDF → `JOIN` query
- Store structured metadata → Perfect for SQL tables
- No complex nested structures needed

✅ **SQLite for MVP:**

- Zero configuration (just a file)
- No server needed
- Fast for single-user development
- Easy to backup (just copy the file)
- Can migrate to PostgreSQL later with same schema

✅ **PostgreSQL for Production:**

- Better concurrency (multiple users)
- More robust for production workloads
- Advanced features (full-text search, JSON support)
- Better performance at scale

#### Why NOT NoSQL (MongoDB, etc.)?

❌ Your data is highly structured and relational
❌ No benefit from document flexibility
❌ More complex to handle relationships
❌ Overkill for this use case

#### Why NOT Vector Database (Pinecone, Chroma, etc.)?

❌ Not needed for MVP
❌ Only useful if you want semantic search ("find similar chunks")
❌ Can add later as a secondary database if needed
❌ Adds complexity without immediate benefit

**Future Enhancement:** If you later want semantic search (e.g., "find chunks similar to this text"), you can add a vector DB alongside SQL for that specific feature.

### Database Schema (SQLite for MVP)

```sql
-- PDFs table
CREATE TABLE pdfs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,  -- SHA256 hash for duplicate detection
    language TEXT,  -- Detected language code (e.g., 'en', 'ro', 'de', 'fr')
    language_name TEXT,  -- Human-readable language name (e.g., 'English', 'Romanian', 'German')
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',  -- pending, processing, completed, error
    file_path TEXT
);

-- Extracted text table
CREATE TABLE extracted_text (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_id INTEGER NOT NULL,
    raw_text TEXT,
    cleaned_text TEXT NOT NULL,
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
);

-- Chunks table (AI analysis results)
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'narrator' or 'character'
    character_name TEXT,  -- NULL for narrator, actual name for characters (e.g., 'Moise', 'Solomon')
    position INTEGER NOT NULL,  -- Order in the document
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
);

-- Voice settings table (user customization per character)
CREATE TABLE voice_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'narrator' or 'character'
    character_name TEXT,  -- NULL for narrator, character name for characters
    language_code TEXT NOT NULL,  -- Language code (e.g., 'en', 'ro', 'de') - matches PDF language
    voice_id TEXT NOT NULL,  -- TTS voice identifier (e.g., 'en-US-Wavenet-D', 'ro-RO-Standard-A')
    voice_name TEXT,  -- Human-readable voice name
    speed REAL DEFAULT 1.0,  -- Speech speed multiplier
    pitch REAL DEFAULT 0.0,  -- Pitch adjustment
    volume REAL DEFAULT 1.0,  -- Volume level
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE,
    UNIQUE(pdf_id, role, character_name)  -- One voice setting per character per PDF
);

-- Audio files table
CREATE TABLE audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER NOT NULL,
    audio_path TEXT NOT NULL,
    voice_id TEXT NOT NULL,  -- Which voice was used (matches voice_settings.voice_id)
    voice_settings_hash TEXT,  -- Hash of voice settings to detect if regeneration needed
    duration REAL,  -- Duration in seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);
```

### API Endpoints (MVP)

```
POST /api/upload-pdf                    # Upload PDF, check hash, return existing or new PDF ID
GET  /api/pdf/{pdf_id}                  # Get PDF metadata
GET  /api/pdf/{pdf_id}/text             # Get extracted text (from DB)
POST /api/pdf/{pdf_id}/process          # Process PDF: extract → analyze → TTS (skip if exists)
GET  /api/pdf/{pdf_id}/chunks           # Get chunks (from DB) - includes character names
GET  /api/pdf/{pdf_id}/characters       # Get list of detected characters (narrator + character names)
GET  /api/pdf/{pdf_id}/voices           # Get available TTS voices for PDF's language
GET  /api/pdf/{pdf_id}/voice-settings   # Get voice settings for all characters
PUT  /api/pdf/{pdf_id}/voice-settings   # Update voice settings for a character (must match PDF language)
POST /api/pdf/{pdf_id}/regenerate-audio # Regenerate audio with new voice settings
GET  /api/pdf/{pdf_id}/audio            # Get audio files (from DB)
GET  /api/pdfs                          # List all processed PDFs
```

### Processing Flow with Database Caching

1. **Upload PDF** → Generate hash → Check DB

   - If exists: Return existing PDF ID
   - If new: Store PDF, return new PDF ID

2. **Process PDF** → Check each step in DB
   - **Extract text**: Check `extracted_text` table
     - If not exists: Extract text from PDF
   - **Detect language**: Check `pdfs.language` field
     - If not exists: Detect language from extracted text (langdetect/polyglot)
     - Store language code and name in PDFs table
   - **Analyze chunks**: Check `chunks` table
     - If not exists: Call Gemini API to identify narrator/characters
   - **Generate audio**: Check `audio_files` table
     - If not exists: Generate TTS using language-specific voices
     - Only call external APIs if data doesn't exist

### AI Character Detection (Gemini Prompt Engineering)

**Key Requirements:**

- Identify Narrator speech vs Character speech
- Extract actual character names from text (e.g., "Moise", "Solomon", "David", "Jesus")
- Handle variations in character name formatting
- Return structured JSON with:
  ```json
  {
    "chunks": [
      {
        "text": "...",
        "role": "narrator",
        "character_name": null,
        "position": 1
      },
      {
        "text": "And Moise said...",
        "role": "character",
        "character_name": "Moise",
        "position": 2
      }
    ]
  }
  ```

**Example Prompt Structure:**

- "Analyze this Bible text and identify narrator speech vs character speech"
- "Extract character names when they are speaking (e.g., Moise, Solomon, David)"
- "Return JSON with role ('narrator' or 'character') and character_name"

### Data Models

- **PDF**: id, filename, file_hash, language, language_name, upload_date, status, file_path
- **Extracted Text**: id, pdf_id, raw_text, cleaned_text, extraction_date
- **Chunks**: id, pdf_id, text, role ('narrator' or 'character'), character_name (e.g., 'Moise', 'Solomon'), position, created_at
- **Voice Settings**: id, pdf_id, role, character_name, language_code, voice_id, voice_name, speed, pitch, volume, created_at, updated_at
- **Audio Files**: id, chunk_id, audio_path, voice_id, voice_settings_hash, duration, created_at

### Environment Variables Needed

```
GOOGLE_GEMINI_API_KEY=
GOOGLE_TTS_API_KEY= (or ELEVENLABS_API_KEY=)
GOOGLE_VISION_API_KEY= (optional, if using OCR)
DATABASE_URL=sqlite:///./scriptura_loquens.db
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

## MVP Focus: Core Features Only

**What's IN the MVP:**

- PDF upload with duplicate detection
- **Automatic language detection** (English, Romanian, German, etc.)
- Text extraction and storage
- AI chunking with character name detection (Narrator + Character names like "Moise", "Solomon")
- **Language-aware TTS voices** (voices match PDF language automatically)
- Voice customization per character (user can select different voices within same language)
- Multi-voice TTS generation with caching
- Basic UI to upload, view chunks, customize voices, and play audio
- Database to avoid reprocessing same PDFs

**What's OUT of MVP (Future Enhancements):**

- OCR/Transcription for scanned PDFs (add if users upload image-based PDFs)
- Audio transcription (Speech-to-Text) - only if users need to upload audio files
- Advanced voice customization
- Text editing capabilities
- Multiple audio export formats
- User accounts/authentication
- Project save/load
- Advanced UI features

## Transcription Considerations

### Types of Transcription

**1. OCR (Optical Character Recognition) - RECOMMENDED for MVP if needed**

- **When needed**: If Bible PDFs are scanned images (not text-based PDFs)
- **Use case**: Extract text from image-based PDFs
- **Options**:
  - **Tesseract OCR** (free, local) - Good for MVP, no API costs
  - **Google Cloud Vision API** (paid, cloud) - Better accuracy, costs per page
- **Recommendation**: ✅ **Add to MVP** if your Bible PDFs are scanned images
- **Implementation**: Check PDF type → if image-based, use OCR → then proceed with text extraction

**2. Speech-to-Text (Audio Transcription) - NOT needed for MVP**

- **When needed**: If users upload audio recordings of Bible readings
- **Use case**: Convert audio files to text
- **Options**:
  - **Google Cloud Speech-to-Text**
  - **OpenAI Whisper API**
- **Recommendation**: ❌ **Skip for MVP** - You're generating audio, not receiving it
- **Future**: Could add if users want to upload their own audio recordings

**3. Audio Verification Transcription - OPTIONAL**

- **When needed**: Transcribe generated TTS audio back to text to verify quality
- **Use case**: Quality assurance, debugging
- **Recommendation**: ❌ **Skip for MVP** - Not essential, adds complexity

### Recommendation

**For MVP:**

- ✅ **Add OCR** if Bible PDFs are often scanned/image-based documents
- ❌ **Skip Speech-to-Text** - Not needed since you're generating audio, not receiving it
- ❌ **Skip Audio Verification** - Can add later if needed

**Decision Point:**

- Are your Bible PDFs text-based (selectable text) or scanned images?
  - **Text-based**: No OCR needed, current PDF extraction is sufficient
  - **Scanned images**: Add OCR to MVP (recommend Tesseract for free option)

## Implementation Recommendations & Best Practices

### 1. Project Structure Recommendations

**Backend Structure:**

```
backend/
├── app/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # DB connection & setup
│   ├── routes/
│   │   ├── pdf_routes.py
│   │   ├── chunk_routes.py
│   │   └── audio_routes.py
│   ├── services/
│   │   ├── pdf_service.py      # PDF processing logic
│   │   ├── gemini_service.py   # Gemini API integration
│   │   ├── tts_service.py      # TTS generation
│   │   └── ocr_service.py      # OCR (if needed)
│   ├── utils/
│   │   ├── text_cleaner.py     # Text cleaning utilities
│   │   └── file_handler.py     # File operations
│   └── config.py          # Configuration
├── uploads/               # PDF storage
├── audio/                 # Generated audio files
├── requirements.txt
├── .env.example
└── run.py                 # Flask app entry point
```

**Frontend Structure:**

```
frontend/
├── src/
│   ├── components/
│   │   ├── PDFUpload/
│   │   ├── ChunkViewer/
│   │   ├── VoiceCustomizer/
│   │   └── AudioPlayer/
│   ├── services/
│   │   └── api.js         # API calls
│   ├── context/
│   │   └── AppContext.js  # State management
│   ├── utils/
│   └── App.jsx
├── package.json
└── vite.config.js
```

### 2. Critical Implementation Details

#### PDF Processing Improvements

- **File Size Limits**: Add max file size validation (e.g., 50MB)
- **File Type Validation**: Verify PDF MIME type, not just extension
- **Progress Tracking**: Use background jobs (Celery or Flask background tasks) for long operations
- **Chunking Strategy**: For large PDFs, process in batches to avoid Gemini token limits
- **Text Cleaning**: Handle Bible-specific formatting (verse numbers, chapter markers)

#### Gemini API Optimization

- **Token Management**:
  - Split large texts into chunks (max 30K tokens per request)
  - Use streaming responses if available
  - Implement exponential backoff for rate limits
- **Prompt Engineering**:

  ```python
  prompt = f"""
  Analyze this Bible text and identify:
  1. Narrator speech (descriptive text, not dialogue)
  2. Character speech (direct quotes from characters)

  For character speech, extract the character name (e.g., Moise, Solomon, David, Jesus).

  Return JSON format:
  {{
    "chunks": [
      {{
        "text": "exact text from source",
        "role": "narrator" or "character",
        "character_name": null or "character name",
        "position": 1
      }}
    ]
  }}

  Text to analyze:
  {text}
  """
  ```

- **Error Handling**: Retry logic with exponential backoff, handle API errors gracefully

#### Language Detection Implementation

- **Language Detection Library**: Use `langdetect` (simple) or `polyglot` (more accurate)

  ```python
  from langdetect import detect, LangDetectException

  def detect_language(text_sample):
      try:
          lang_code = detect(text_sample)
          lang_names = {
              'en': 'English',
              'ro': 'Romanian',
              'de': 'German',
              'fr': 'French',
              'es': 'Spanish',
              'it': 'Italian',
              'pt': 'Portuguese'
          }
          return lang_code, lang_names.get(lang_code, lang_code.upper())
      except LangDetectException:
          return 'en', 'English'  # Default fallback
  ```

- **Detection Strategy**:
  - Use first 1000-2000 characters of extracted text
  - Store language code (ISO 639-1) and human-readable name
  - Fallback to English if detection fails

#### TTS Implementation (Language-Aware)

- **Voice Selection**: Language-specific voice mappings:

  ```python
  LANGUAGE_VOICES = {
    'en': {  # English
      'narrator': 'en-US-Wavenet-D',  # Deep, authoritative
      'male_character': 'en-US-Wavenet-E',
      'female_character': 'en-US-Wavenet-F',
    },
    'ro': {  # Romanian
      'narrator': 'ro-RO-Standard-A',  # Female narrator
      'male_character': 'ro-RO-Standard-B',  # Male character
      'female_character': 'ro-RO-Standard-A',
    },
    'de': {  # German
      'narrator': 'de-DE-Standard-A',  # Female narrator
      'male_character': 'de-DE-Standard-B',  # Male character
      'female_character': 'de-DE-Standard-C',
    },
    'fr': {  # French
      'narrator': 'fr-FR-Standard-A',
      'male_character': 'fr-FR-Standard-B',
      'female_character': 'fr-FR-Standard-C',
    }
  }

  def get_voice_for_language(language_code, role='narrator', gender='male'):
      voices = LANGUAGE_VOICES.get(language_code, LANGUAGE_VOICES['en'])
      if role == 'narrator':
          return voices['narrator']
      elif gender == 'male':
          return voices.get('male_character', voices['narrator'])
      else:
          return voices.get('female_character', voices['narrator'])
  ```

- **Voice Validation**: Ensure selected voice matches PDF language
- **Fallback**: If language not supported, use English voices
- **Audio Format**: Use MP3 for smaller files, WAV for quality
- **Audio Concatenation**: Merge chunks into single file or keep separate for flexibility
- **Storage**: Consider cloud storage (S3, Google Cloud Storage) for production

#### Database Optimizations

- **Indexes**: Add indexes on frequently queried columns:
  ```sql
  CREATE INDEX idx_pdfs_hash ON pdfs(file_hash);
  CREATE INDEX idx_chunks_pdf_id ON chunks(pdf_id);
  CREATE INDEX idx_audio_chunk_id ON audio_files(chunk_id);
  ```
- **Connection Pooling**: Use SQLAlchemy connection pooling
- **Backup Strategy**: Regular SQLite backups (copy file) or use PostgreSQL for production

### 3. Security Considerations

- **File Upload Security**:
  - Validate file types (check magic bytes, not just extension)
  - Scan for malware (optional, use ClamAV)
  - Limit file sizes
  - Sanitize filenames
- **API Security**:
  - Rate limiting (Flask-Limiter)
  - API key validation for sensitive endpoints
  - CORS configuration (only allow frontend domain)
- **Environment Variables**:
  - Never commit `.env` files
  - Use different API keys for dev/prod
  - Rotate keys regularly

### 4. Performance Optimizations

- **Caching Strategy**:
  - Database caching (already planned) ✅
  - Add Redis for session/API response caching (future)
  - Cache voice settings per PDF
- **Async Processing**:
  - Use Flask background tasks or Celery for long operations
  - Return job ID immediately, poll for status
- **Frontend Optimizations**:
  - Lazy load audio files
  - Virtual scrolling for large chunk lists
  - Debounce voice preview requests

### 5. Error Handling & User Experience

- **Error Types to Handle**:
  - PDF extraction failures
  - Gemini API errors (rate limits, invalid responses)
  - TTS generation failures
  - Database connection errors
  - File system errors
- **User Feedback**:
  - Progress indicators for each step
  - Clear error messages
  - Retry mechanisms
  - Status updates (processing, completed, error)

### 6. Testing Strategy

**Unit Tests:**

- PDF text extraction
- Text cleaning functions
- Database operations
- API response parsing

**Integration Tests:**

- End-to-end flow: upload → extract → analyze → TTS
- Database caching verification
- API error handling

**Manual Testing:**

- Test with various Bible PDF formats
- Test character detection accuracy
- Test voice customization
- Test duplicate PDF handling

### 7. Missing Features to Consider

- **Audio Playback Controls**:
  - Play/pause/stop
  - Seek to specific chunk
  - Playback speed control
  - Volume control
- **Export Options**:
  - Download single audio file (concatenated)
  - Download separate files per character
  - Export chunks as JSON/CSV
- **Character Management**:
  - Merge similar character names (e.g., "Moise" and "Moses")
  - Manual character name correction
  - Character grouping

### 8. Deployment Considerations

**Backend:**

- Use Gunicorn or uWSGI for Flask in production
- Set up reverse proxy (Nginx)
- Use environment-specific configs
- Set up logging (structured logging)

**Frontend:**

- Build optimization (minification, code splitting)
- CDN for static assets
- Environment variables for API URLs

**Database:**

- Migrate to PostgreSQL for production
- Set up automated backups
- Connection pooling configuration

### 9. Monitoring & Logging

- **Logging**:
  - Log all API calls (Gemini, TTS)
  - Log errors with stack traces
  - Log processing times for optimization
- **Metrics**:
  - Track PDF processing time
  - Track API costs (Gemini, TTS)
  - Track user actions

### 10. Cost Optimization

- **Gemini API**:
  - Cache results aggressively (already planned) ✅
  - Use appropriate model tier (Pro vs Ultra)
  - Batch requests when possible
- **TTS API**:
  - Cache audio files (already planned) ✅
  - Use appropriate quality settings
  - Consider self-hosted TTS for cost savings (future)

### 11. Quick Reference: Key Code Patterns

**PDF Hash Generation:**

```python
import hashlib

def generate_pdf_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
```

**Database Check Before Processing:**

```python
def check_pdf_exists(file_hash):
    pdf = PDF.query.filter_by(file_hash=file_hash).first()
    if pdf:
        # Check if fully processed
        if pdf.status == 'completed':
            return pdf.id, True  # Already processed
        return pdf.id, False  # Exists but not processed
    return None, False  # New PDF
```

**Gemini API Call with Retry:**

```python
import time
from google import generativeai

def call_gemini_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            model = generativeai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

**Voice Settings Hash (for caching):**

```python
import hashlib
import json

def generate_voice_settings_hash(voice_settings):
    settings_str = json.dumps(voice_settings, sort_keys=True)
    return hashlib.md5(settings_str.encode()).hexdigest()
```

**Language Detection:**

```python
from langdetect import detect, LangDetectException

def detect_pdf_language(cleaned_text):
    # Use sample of text for faster detection
    text_sample = cleaned_text[:2000] if len(cleaned_text) > 2000 else cleaned_text

    try:
        lang_code = detect(text_sample)
        lang_names = {
            'en': 'English',
            'ro': 'Romanian',
            'de': 'German',
            'fr': 'French',
            'es': 'Spanish',
            'it': 'Italian',
            'pt': 'Portuguese'
        }
        return lang_code, lang_names.get(lang_code, lang_code.upper())
    except LangDetectException:
        return 'en', 'English'  # Default fallback
```

### 12. Recommended Library Versions

**Backend (requirements.txt):**

```
Flask==3.0.0
SQLAlchemy==2.0.23
Flask-CORS==4.0.0
Flask-Migrate==4.0.5
pdfplumber==0.10.3
google-generativeai==0.3.2
google-cloud-texttospeech==2.16.3
langdetect==1.0.9  # Language detection
python-dotenv==1.0.0
requests==2.31.0
python-multipart==0.0.6
```

**Frontend (package.json):**

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "react-dropzone": "^14.2.3",
    "react-h5-audio-player": "^3.9.1"
  }
}
```

### 13. Critical Decisions Summary

✅ **Use pdfplumber** over PyPDF2 (better text extraction)
✅ **Use SQLite for MVP**, PostgreSQL for production
✅ **Use Flask-CORS** for CORS handling
✅ **Use Context API** for state management (simpler than Zustand for MVP)
✅ **Use react-h5-audio-player** for audio playback (feature-rich)
✅ **Implement database caching** at every step (saves API costs)
✅ **Add indexes** on frequently queried columns
✅ **Use background jobs** for long operations (better UX)
✅ **Validate file types** properly (security)
✅ **Add comprehensive error handling** (better UX)
✅ **Automatic language detection** - Detect PDF language and use matching TTS voices
✅ **Language-aware TTS** - Voices automatically match document language (en, ro, de, etc.)

## Next Steps

1. **Start with Phase 1**: Set up React + Python backend + SQLite database
2. **Design database schema** and create tables with indexes
3. **Implement PDF hash checking** to prevent duplicate processing
4. **Build PDF extraction** with database storage and error handling
5. **Test Gemini integration** with sample text, store results in DB
6. **Test TTS generation**, store audio paths in DB
7. **Build simple frontend** to test complete flow
8. **Verify caching works**: Upload same PDF twice, confirm no duplicate API calls
9. **Add error handling** and user feedback throughout
10. **Set up logging** and monitoring
