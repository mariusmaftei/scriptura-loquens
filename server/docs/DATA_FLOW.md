# Scriptura Loquens – Data flow and technologies

This document describes how data moves through the app and which technologies process each step.

---

## Pipeline in one sentence

**PDF → extract text → clean text (plain string) → send to AI → AI returns JSON (chunks) → we store chunks in DB → TTS reads chunks from DB and generates audio.**

We do **not** turn the PDF or its text into JSON before sending to AI. We send **cleaned plain text**; the AI returns **JSON** (narrator/character segments), which we store. TTS then uses those stored chunks.

---

## High-level flow

```
[User] → Upload PDF → [Backend] → Store file + DB record (pending)
                ↓
[User] → Process (or auto) → [Backend] → Extract text → Clean text → Detect language
                ↓
                → Send CLEANED TEXT (not JSON) to AI → AI returns JSON (chunks)
                ↓
                → Store chunks in DB (ready for TTS) → status = completed
                ↓
[User] → Result page → [Frontend] → Load PDF + chunks + voices
                ↓
[User] → Assign voices + Save → [Backend] → TTS reads chunks from DB → Generate audio → Store files
                ↓
[User] → Play segment → [Frontend] → Request audio URL → [Backend] → Stream file
```

---

## 1. Upload PDF

| Step                    | What happens                           | Technology                                           |
| ----------------------- | -------------------------------------- | ---------------------------------------------------- |
| User selects file       | Browser sends `multipart/form-data`    | **React** (Dropzone), **Axios**                      |
| `POST /api/upload-pdf`  | Server receives file                   | **Flask**                                            |
| Save to disk            | File written under `UPLOAD_FOLDER`     | **Werkzeug** `secure_filename`, app **file_handler** |
| Hash file               | SHA-256 of file content                | **Python** `hashlib`, app **file_handler**           |
| Duplicate check         | Look up `file_hash` in DB              | **SQLAlchemy**, **PostgreSQL / SQLite**              |
| Create or update record | Insert `PDF` or update existing row    | **SQLAlchemy**                                       |
| Response                | Return `{ id, filename, status, ... }` | **Flask** `jsonify`                                  |

**Data stored:** `pdfs` table (id, filename, file_hash, file_path, status=`pending`), file on disk.

---

## 2. Process PDF (extract + analyze)

Triggered by the frontend when the user lands on `/pdf/:id` and status is `pending`, or by "Try again" after an error.

| Step                        | What happens                                                 | Technology                        |
| --------------------------- | ------------------------------------------------------------ | --------------------------------- |
| `POST /api/pdf/:id/process` | Server loads PDF record, sets status `processing`            | **Flask**, **SQLAlchemy**         |
| Resolve file path           | Ensure absolute path to PDF on disk                          | **Python** `os.path`              |
| **Extract text**            | Read PDF pages, get text per page                            | **pdfplumber**                    |
| Limit pages                 | Only first N pages (default 5)                               | **Config** `MAX_PDF_PAGES`        |
| Clean text                  | Normalize whitespace, basic cleanup                          | App **text_cleaner**              |
| **Detect language**         | Infer language from text sample                              | **langdetect**                    |
| Store extracted text        | Save `raw_text`, `cleaned_text`, link to PDF                 | **SQLAlchemy** → `extracted_text` |
| **Chunk analysis**          | Send cleaned text to AI, get narrator/character segments     | **Google Gemini API** (see below) |
| Store chunks                | Insert rows with text, role, character_name, position        | **SQLAlchemy** → `chunks`         |
| Mark completed              | Set PDF `status=completed`, set `language` / `language_name` | **SQLAlchemy**                    |

**Gemini (chunk analysis):**

- **SDK:** `google-genai` (new) or `google-generativeai` (legacy fallback).
- **Input:** Prompt + full cleaned text (or batched if > 30k chars).
- **Output:** JSON with `chunks[]`: `text`, `role` (narrator/character), `character_name`, `position`.
- **Config:** `GOOGLE_GEMINI_API_KEY` (AI Studio) or Vertex AI; optional `GEMINI_MODEL_ID`, `GEMINI_THINKING_LEVEL`.

**Data stored:** `extracted_text` (raw_text, cleaned_text), `pdfs` (language, language_name, status=`completed`), `chunks` (text, role, character_name, position).

---

## 3. Result page (transcription + voices)

| Step                              | What happens                                            | Technology                                            |
| --------------------------------- | ------------------------------------------------------- | ----------------------------------------------------- |
| User opens `/pdf/:id`             | Frontend loads PDF and related data                     | **React**, **React Router**                           |
| `GET /api/pdf/:id`                | PDF metadata                                            | **Flask**, **SQLAlchemy**                             |
| `GET /api/pdf/:id/chunks`         | List of text segments                                   | **Flask**, **SQLAlchemy**                             |
| `GET /api/pdf/:id/characters`     | Unique roles/characters for voice assignment            | **Flask**, **SQLAlchemy** (derived from chunks)       |
| `GET /api/pdf/:id/voices`         | Available TTS voices for document language              | **Flask**, app **tts_service** (Edge or Google list)  |
| `GET /api/pdf/:id/voice-settings` | Saved voice per role/character                          | **Flask**, **SQLAlchemy** → `voice_settings`          |
| `GET /api/pdf/:id/audio`          | List of generated audio files (chunk_id, path, hash)    | **Flask**, **SQLAlchemy** → `audio_files`             |
| UI                                | Show transcription (chunks), voice customizer, playback | **React** (ChunkViewer, VoiceCustomizer, AudioPlayer) |

**Data read:** All from **PostgreSQL / SQLite** via **SQLAlchemy**; voice list from app config / TTS provider.

---

## 4. Voice assignment and audio generation

| Step                                 | What happens                                                     | Technology                                             |
| ------------------------------------ | ---------------------------------------------------------------- | ------------------------------------------------------ |
| User changes voice / speed / pitch   | Frontend keeps local state                                       | **React** (VoiceCustomizer)                            |
| User clicks Save                     | `PUT /api/pdf/:id/voice-settings` with per-role settings         | **Axios**, **Flask**                                   |
| Store voice settings                 | Upsert rows in `voice_settings`                                  | **SQLAlchemy**                                         |
| `POST /api/pdf/:id/regenerate-audio` | For each chunk: get voice for role, synthesize if needed         | **Flask**, **TTS service**                             |
| **TTS**                              | Turn chunk text into speech                                      | **Edge TTS** (free) or **Google Cloud Text-to-Speech** |
| Cache check                          | Skip if chunk already has audio with same voice/speed/pitch hash | App **tts_service** (hash), **SQLAlchemy**             |
| Save audio                           | Write MP3 to `AUDIO_FOLDER`, link to chunk                       | App **tts_service**, **SQLAlchemy** → `audio_files`    |
| Response                             | Return list of audio file metadata                               | **Flask** `jsonify`                                    |

**TTS technologies:**

- **Edge TTS:** `edge-tts` (Python), no API key; voices per language (e.g. `en-US-AriaNeural`).
- **Google Cloud TTS:** `google-cloud-texttospeech`; uses `GOOGLE_TTS_CREDENTIALS_JSON` (service account).

**Data stored:** `voice_settings` (voice_id, speed, pitch, volume per role/character), `audio_files` (chunk_id, audio_path, voice_settings_hash), MP3 files on disk.

---

## 5. Audio playback

| Step                 | What happens                                                       | Technology                                      |
| -------------------- | ------------------------------------------------------------------ | ----------------------------------------------- |
| User selects a chunk | Frontend finds `AudioFile` for that chunk                          | **React**                                       |
| Build URL            | `GET /api/audio/:audioId/file`                                     | **Axios** (URL from `getAudioFileUrl(audioId)`) |
| Stream file          | Server reads file from disk, sends with `Content-Type: audio/mpeg` | **Flask** `send_file`                           |
| Playback             | Browser plays stream                                               | **HTML5 `<audio>`** in AudioPlayer              |

**Data read:** File system (`AUDIO_FOLDER`), **SQLAlchemy** for `audio_files` row.

---

## Summary table: who processes what

| Stage              | Backend tech                    | External / libs                                            |
| ------------------ | ------------------------------- | ---------------------------------------------------------- |
| Upload & store     | Flask, SQLAlchemy, file_handler | PostgreSQL / SQLite, hashlib                               |
| PDF → text         | pdf_service                     | **pdfplumber**, **langdetect**, text_cleaner               |
| Text → chunks      | gemini_service                  | **Google Gemini API** (google-genai / google-generativeai) |
| Chunks → audio     | tts_service                     | **Edge TTS** or **Google Cloud TTS**                       |
| Serve data & files | Flask, SQLAlchemy               | -                                                          |
| UI & playback      | React, React Router, Axios      | Browser (HTML5 audio)                                      |

---

## Database entities (for data flow)

- **pdfs** – One per upload; `status`: pending → processing → completed | error.
- **extracted_text** – One per PDF; raw and cleaned text from pdfplumber.
- **chunks** – Many per PDF; narrator/character segments from Gemini.
- **voice_settings** – Per PDF, per role/character; voice_id, speed, pitch, volume.
- **audio_files** – One per chunk (per voice config); path to MP3 and settings hash.

All relationships are via `pdf_id` (and `chunk_id` for audio_files). Deletes cascade from PDF.

---

## Recommendations

**Current design is correct.** Summary:

| Step        | What we do                                                         | Recommendation                                                                                                                                   |
| ----------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Before AI   | Clean PDF text (whitespace, etc.) → **plain string**               | **Keep.** Do not convert to JSON first. The AI needs the raw narrative to decide narrator vs character; a pre-JSON structure would be redundant. |
| Input to AI | Send **cleaned text** in a prompt; ask for JSON output             | **Keep.** Prompt + cleaned text is the right input.                                                                                              |
| AI output   | AI returns **JSON** (chunks with text, role, character_name)       | **Keep.** We parse and store as rows.                                                                                                            |
| Storage     | Store chunks in DB (text, role, character_name, position)          | **Keep.** DB is the single source of truth for “prepared” segments.                                                                              |
| TTS         | Read chunks from DB; generate audio per chunk; cache by voice hash | **Keep.** TTS only runs on stored chunks; no need to re-call AI.                                                                                 |

**Optional improvements (later):**

- **Stricter cleaning before AI:** e.g. remove verse numbers, headers, footers if they confuse the model (still send plain text, not JSON).
- **Validate AI JSON:** check for duplicates, overlapping text, or missing fields before saving.
- **Store “last error” on PDF:** implemented. `PDF.error_message` stores the last processing error; the UI shows it when status is `error`. If upgrading an existing DB, add the column: `ALTER TABLE pdfs ADD COLUMN error_message TEXT;` (PostgreSQL) or same for SQLite.
