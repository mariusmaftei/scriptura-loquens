# Chunk Analysis Pipeline & Troubleshooting

## API Responsibilities

| API | Responsibility |
|-----|----------------|
| **Google Gemini** | Analyzes text, splits it into chunks, detects narrator vs character speech |
| **ElevenLabs** | Converts text into audio (TTS) — you pay for this |
| **Microsoft Edge TTS** | Alternative free TTS option |
| **Google Cloud TTS** | Alternative TTS option |

Gemini does **not** generate audio — it only structures the text (chunks, roles, character names). TTS providers (ElevenLabs, Edge, Google) turn that text into speech.

---

## What Went Wrong: `No module named 'google.generativeai'`

### The Error

```
Failed to analyze chunks: Gemini API error: No module named 'google.generativeai'
```

### Root Cause

Google has two Gemini SDKs:

| Package | Import | Status |
|---------|--------|--------|
| `google-genai` | `from google import genai` | New, recommended (used by this app) |
| `google-generativeai` | `import google.generativeai` | Legacy, deprecated |

This app uses **only** `google-genai`. The error occurs when:

1. **Deployment (Docker)**: `requirements.txt` was missing `google-generativeai`. Something in the environment (or a transitive import) tried to load the legacy package and failed because it was not installed.
2. **Namespace conflict**: Both packages live under the `google.*` namespace. In some setups, loading `google` can trigger expectations for the old module elsewhere.

### Fix Applied

`google-generativeai` was added back to `requirements.txt` so it is available even though the app does not import it directly. Both packages coexist without conflict.

**For Docker deployments:** Rebuild the image without cache so dependencies refresh:
- EasyPanel: rebuild app with “No cache”
- Local: `docker build --no-cache -t scriptura-server ./server`

---

## The Pipeline: From PDF Upload to Audio

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Upload PDF │ ──► │  Extract     │ ──► │  Chunk          │ ──► │  Store chunks    │ ──► │  Text → Audio   │
│  (save file)│     │  Text        │     │  Analysis       │     │  in DB           │     │  (TTS)          │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────────┘     └─────────────────┘
       │                      │                      │                                          │
       │                      │                      └── Gemini (chunks, narrator, characters)   └── ElevenLabs
       │                      └── pdfplumber, langdetect                                      or Edge or Google TTS
       └── file_handler
```

### Step 1: Upload PDF

**Route:** `POST /api/upload-pdf`  
**Handler:** `pdf_routes.upload_pdf()`

- Receives the file, saves it to `UPLOAD_FOLDER`
- Computes hash for deduplication
- Creates a `PDF` record with `status='pending'`
- Returns the PDF id

### Step 2: Process PDF (Triggered by Client)

**Route:** `POST /api/pdf/<id>/process`  
**Handler:** `pdf_routes.process_pdf()`

This is where chunk analysis runs.

#### 2a. Extract Text

- Calls `process_pdf_file()` from `pdf_service`
- Uses **pdfplumber** to extract raw text from pages (up to `MAX_PDF_PAGES`)
- **text_cleaner** normalizes whitespace and cleans the text
- **langdetect** detects language (for TTS)
- Result stored in `ExtractedText` (raw_text, cleaned_text)

#### 2b. Chunk Analysis (Gemini)

- Calls `analyze_text_in_batches()` from `gemini_service` with cleaned text
- **Verse boundaries are deterministic**: split by verse numbers (`1.`, `22.`, etc.) so each verse = exactly one chunk
- For each batch:
  1. `_split_by_verse_numbers()` — splits text by `^\d+\.\s+` pattern
  2. `_clean_verse_text()` — removes footnote markers (* **), extracts references
  3. Gemini classifies each block (role, character_name, chunk_type) but does NOT decide boundaries

#### 2c. Store Chunks

- Each chunk → `Chunk` record (text, role, character_name, position, etc.)
- `db.session.add_all(chunks_to_add)`
- PDF status set to `completed`

### Data Flow Summary

| Stage | Input | Output | Service / Tool |
|-------|-------|--------|----------------|
| Upload | PDF file | PDF record | file_handler |
| Extract | PDF path | raw_text, cleaned_text | pdf_service (pdfplumber) |
| Chunk | cleaned_text | list of chunks (JSON) | gemini_service (Gemini API) |
| Store | chunks | Chunk rows in DB | pdf_routes |

### Alternative Entry: Analyze Endpoint

**Route:** `POST /api/pdf/<id>/analyze` (chunk_routes)

- Same `analyze_text_in_batches()` call
- Used when text was already extracted but chunks are missing

---

## Key Files

| File | Role |
|------|------|
| `app/routes/pdf_routes.py` | Upload, process, orchestrates the pipeline |
| `app/services/pdf_service.py` | Text extraction (pdfplumber, langdetect) |
| `app/services/gemini_service.py` | Chunk analysis — splits text, detects narrator & characters |
| `app/services/tts_service.py` | Text → audio (ElevenLabs, Edge, Google TTS) |
| `app/utils/text_cleaner.py` | Text normalization |
| `app/models.py` | PDF, ExtractedText, Chunk models |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GOOGLE_GEMINI_API_KEY` or `GEMINI_API_KEY` | AI Studio API key for Gemini (chunk analysis) |
| `GEMINI_MODEL_ID` | Model (e.g. `gemini-2.5-flash`, `gemini-3-flash-preview`) |
| `MAX_PDF_PAGES` | Max pages to extract (default 5) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Use Vertex AI instead of AI Studio |
| `TTS_PROVIDER` | `edge` (free), `elevenlabs`, or `google` |
| `ELEVENLABS_API_KEY` | Required when `TTS_PROVIDER=elevenlabs` (paid). When set, custom cloned voices also appear with Edge TTS. |

**Voices:** Edge TTS has 2 Romanian voices (Emil, Alina). ElevenLabs has 50+ plus custom cloning. With `ELEVENLABS_API_KEY` set, ElevenLabs voices (including custom) are merged into the list even when `TTS_PROVIDER=edge`.
