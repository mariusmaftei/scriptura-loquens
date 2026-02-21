# Scriptura Loquens – environment variables

Use this as a reference. Put the real values in `server/.env` (never commit that file).

---

## App

```
FRONTEND_URL=http://localhost:3000
SECRET_KEY=your-secret-key-change-in-production
```

---

## Database (PostgreSQL)

Create a database (e.g. `scriptura_loquens`) and a user with access, then:

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE_NAME
```

**Examples:**

- Local:
  ```
  DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/scriptura_loquens
  ```
- With host and port:
  ```
  DATABASE_URL=postgresql://myuser:mypass@db.example.com:5432/scriptura_loquens
  ```

---

## Folders & PDF limit (optional; defaults shown)

```
UPLOAD_FOLDER=uploads
AUDIO_FOLDER=audio
# Only process first N pages (saves Gemini/token usage; default 5)
MAX_PDF_PAGES=5
```

---

## Gemini (choose one)

**Option A – Google AI Studio (recommended)**  
Get key: https://aistudio.google.com/app/apikey

```
GOOGLE_GEMINI_API_KEY=your-api-key
```

**Option B – Vertex AI**  
Get key: https://console.cloud.google.com/vertex-ai/studio/settings/api-keys

```
GOOGLE_API_KEY=your-vertex-ai-api-key
GOOGLE_GENAI_USE_VERTEXAI=True
```

---

## Text-to-speech (choose one)

**Option A – Edge TTS (free, no key)**

```
TTS_PROVIDER=edge
```

**Option B – Google Cloud TTS**  
Needs service account JSON path.

```
TTS_PROVIDER=google
GOOGLE_TTS_CREDENTIALS_JSON=C:/path/to/your-service-account.json
```

---

## Optional

```
GOOGLE_VISION_API_KEY=key
```

---

## Example full `.env` (PostgreSQL + Edge TTS + Google AI Studio)

```
FRONTEND_URL=http://localhost:3000
SECRET_KEY=your-secret-key-change-in-production

DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/scriptura_loquens
UPLOAD_FOLDER=uploads
AUDIO_FOLDER=audio

GOOGLE_GEMINI_API_KEY=your-gemini-api-key
TTS_PROVIDER=edge
```
