# Audio folder structure (implemented)

When a user uploads a PDF (e.g. `biblia.pdf`), a folder is created from the PDF name (without extension).

**Root:** `audio/transcriptions/<pdf_ref>/`

- `<pdf_ref>` = PDF filename without `.pdf`, slugified (e.g. `biblia.pdf` → `biblia`).

**Inside the PDF folder:** one folder per **detected character** (narrator or character name).

- `narrator/` – all narrator segments
- `<character_slug>/` – one folder per character (e.g. `dumnezeu`, from the text)

**Inside each character folder:** one folder per **chosen voice/actor**.

- `<actor_slug>/` – from the voice name or voice ID (e.g. user picks voice "Bob" → `bob/`; "en-US-Standard-A" → `en-us-standard-a/`)
- `custom/` – when the user records or uploads custom audio for that character

**Example:**

```
audio/transcriptions/
  biblia/
    narrator/
      bob/              ← narrator with voice "Bob"
        seg0001_narrator_abc123.mp3
        seg0005_narrator_abc123.mp3
      john/             ← user switched narrator to John
        seg0001_narrator_def456.mp3
    dumnezeu/
      alice/
        seg0003_dumnezeu_xxx.mp3
      custom/           ← user recorded custom audio for this character
        seg0003_custom_abc.webm
```

- **TTS:** `regenerate_audio` saves under `pdf_ref/character_slug/actor_slug/` using the voice name (or voice ID slug) from voice settings.
- **Custom upload/record:** files are saved under `pdf_ref/character_slug/custom/`.
- **Resolve:** `_resolve_audio_path` supports both the flat layout (legacy) and the new nested layout; it can search under `pdf_ref` for the filename if the stored path is missing.
