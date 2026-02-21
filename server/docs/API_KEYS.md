# Scriptura Loquens – Models and API Setup

This project uses **2 Google services**. Below: what they are, what I recommend, and exact links to set them up.

---

## 1. What This Project Uses

| #   | Service                         | What it does                                                                                            | What you need                                  |
| --- | ------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| 1   | **Gemini**                      | Reads the Bible text and splits it into “narrator” vs “character” and gets names (e.g. Moise, Solomon). | One **API key**                                |
| 2   | **Google Cloud Text-to-Speech** | Turns each text chunk into spoken audio (different voices per character).                               | **Service account JSON file** (path in `.env`) |

---

## 2. Recommendation

- **Gemini:** Use **Google AI Studio** (one API key, no Google Cloud project needed to start).  
  If you prefer to use your **Vertex AI** key from Google Cloud, that works too (see Option B below).
- **TTS:** Use **Google Cloud Text-to-Speech** with a **service account JSON** (same as now). No other realistic alternative for multi-voice, multi-language in this stack.

---

## 3. Setup 1 – Gemini (text analysis)

**Recommendation: Google AI Studio (easiest)**

- **Create API key (Google AI Studio):**  
  **https://aistudio.google.com/app/apikey**

  1. Open the link and sign in with your Google account.
  2. Click **“Create API key”** (you can create one under a new or existing Google Cloud project).
  3. Copy the key and put it in your `.env` (see “What to put in `.env`” at the end).

- **In your `.env` file:**
  ```env
  GOOGLE_GEMINI_API_KEY=your-api-key-from-aistudio-google-com
  ```
  Do **not** set `GOOGLE_API_KEY` or `GOOGLE_GENAI_USE_VERTEXAI` if you use this.

**Option B – Use your Vertex AI key (Google Cloud)**

- **Create / manage API key (Vertex AI):**  
  **https://console.cloud.google.com/vertex-ai/studio/settings/api-keys**
  1. Select your project (e.g. `softindex-labs`).
  2. Create or copy an API key (Vertex keys often start with `AQ.`, e.g. `AQ.Ab8RN...` — that format is correct).
  3. In `.env` use:
  ```env
  GOOGLE_API_KEY=AQ.Ab8RN...your-full-vertex-key
  GOOGLE_GENAI_USE_VERTEXAI=True
  ```
  Do **not** set `GOOGLE_GEMINI_API_KEY` when using this.

**Model catalog and changelog**

- This app defaults to **`gemini-3-flash-preview`**. Override with `GEMINI_MODEL_ID` in `.env` if needed.
- For current model IDs, deprecation dates, and new features, see the official docs:
  - **Release notes (changelog):** [Gemini API Release notes](https://ai.google.dev/gemini-api/docs/changelog)
  - **Models:** [Gemini models](https://ai.google.dev/gemini-api/docs/models) (list, pricing, lifecycle).
- Optional: `GEMINI_THINKING_LEVEL=low|high|minimal` (Gemini 3; `low` = faster/cheaper).
- **Vertex AI users:** full Gemini API reference (generateContent, generationConfig, thinkingConfig, etc.) is in the project file **`vertex-doc.md`** (from Vertex AI docs).

---

## 4. Setup 2 – Text-to-Speech (voice generation)

TTS does **not** use the Gemini/Vertex API key. It uses a **service account JSON file**.

**Step 1 – Open Google Cloud Console**

- **Console home:**  
  **https://console.cloud.google.com/**

**Step 2 – Create or select a project**

- Use the project dropdown at the top (e.g. `softindex-labs` or create a new one).

**Step 3 – Enable the Text-to-Speech API**

- **Direct link to enable TTS API:**  
  **https://console.cloud.google.com/apis/library/texttospeech.googleapis.com**
- Open it, select your project if asked, then click **“Enable”**.

**Step 4 – Create a service account and download JSON**

- **Go to Credentials:**  
  **https://console.cloud.google.com/apis/credentials**
  1. Click **“Create credentials”** → **“Service account”**.
  2. Give it a name (e.g. `scriptura-tts`) → **Create and continue**.
  3. Role: e.g. **“Cloud Text-to-Speech API User”** (or a broader role like “Editor” for the project) → **Done**.
  4. Click the new service account → **“Keys”** tab → **“Add key”** → **“Create new key”** → **JSON** → **Create**.  
     The JSON file will download.

**Step 5 – Use the JSON in the app**

- Save the file somewhere safe (e.g. `server/keys/tts-credentials.json`).
- In `.env` set the **path** to that file:
  ```env
  GOOGLE_TTS_CREDENTIALS_JSON=C:/path/to/tts-credentials.json
  ```
  Use the real path on your machine (Windows example above).

**Chirp 3 HD (realistic voices, e.g. Romanian)**

- The same voices you hear in **Vertex AI Studio** (Generate speech → Text-to-speech) are **Chirp 3: HD**. They work with the same Cloud TTS API and service account.
- To use them in this app, set:
  ```env
  TTS_PROVIDER=google
  TTS_USE_CHIRP_HD=true
  GOOGLE_TTS_CREDENTIALS_JSON=C:/path/to/tts-credentials.json
  ```
- You get multiple male/female Chirp voices per language (e.g. Charon, Schedar, Fenrir for Romanian narrator/God).

**ElevenLabs (realistic voices, recommended for Romanian)**

- **ElevenLabs** gives very natural, human-like voices and supports Romanian and 30+ other languages. Best option if you want **realistic** narration and more than 2 Romanian voices.
- Get an API key: **https://elevenlabs.io/app/settings/api-keys**
- In `.env` set:
  ```env
  TTS_PROVIDER=elevenlabs
  ELEVENLABS_API_KEY=your-elevenlabs-api-key
  ```
- The app will list all your ElevenLabs voices (default + custom) and use `eleven_multilingual_v2` for synthesis. No Google Cloud setup required.

---

## 5. What to put in `.env` – Summary

**If you use Google AI Studio for Gemini (recommended):**

```env
# Gemini – from https://aistudio.google.com/app/apikey
GOOGLE_GEMINI_API_KEY=your-api-key-here

# TTS – path to JSON from https://console.cloud.google.com/apis/credentials
GOOGLE_TTS_CREDENTIALS_JSON=C:/full/path/to/your-tts-credentials.json
```

**If you use Vertex AI for Gemini:**

```env
# Gemini – from https://console.cloud.google.com/vertex-ai/studio/settings/api-keys
GOOGLE_API_KEY=your-vertex-ai-api-key
GOOGLE_GENAI_USE_VERTEXAI=True

# TTS – same as above
GOOGLE_TTS_CREDENTIALS_JSON=C:/full/path/to/your-tts-credentials.json
```

---

## 6. Quick link list

| What                                            | Link                                                                      |
| ----------------------------------------------- | ------------------------------------------------------------------------- |
| **Gemini API key (recommended)**                | https://aistudio.google.com/app/apikey                                    |
| **Gemini API key (Vertex AI)**                  | https://console.cloud.google.com/vertex-ai/studio/settings/api-keys       |
| **Google Cloud Console**                        | https://console.cloud.google.com/                                         |
| **Enable Text-to-Speech API**                   | https://console.cloud.google.com/apis/library/texttospeech.googleapis.com |
| **Create credentials (service account / JSON)** | https://console.cloud.google.com/apis/credentials                         |
| **ElevenLabs API key (TTS)**                    | https://elevenlabs.io/app/settings/api-keys                               |
| **Gemini API – Release notes (changelog)**      | https://ai.google.dev/gemini-api/docs/changelog                           |
| **Gemini API – Models (catalog)**               | https://ai.google.dev/gemini-api/docs/models                              |

Once you have the Gemini key and the TTS JSON path (or ElevenLabs key) in `.env`, the app can use both services as described in the project.

---

## 7. Cheapest text-to-speech options

Rough comparison (prices and free tiers can change; check the official links).

| Option               | Cost                                                                                                         | Notes                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| **Edge TTS (free)**  | **Free**                                                                                                     | No API key. Uses Microsoft’s online voices. Only 2 Romanian voices (Emil, Alina). Best if you want **zero cost**. |
| **ElevenLabs**       | **Free tier:** ~10k chars/month. **Paid:** per character.                                                    | One API key. Very realistic voices, Romanian + 30+ languages. [Pricing](https://elevenlabs.io/pricing)            |
| **Google Cloud TTS** | **Free tier:** ~4M characters/month (Standard/WaveNet). **After:** ~$4 per 1M characters (Standard/WaveNet). | Needs service account JSON. [Pricing](https://cloud.google.com/text-to-speech/pricing)                            |
| **Amazon Polly**     | **Free tier:** 5M characters/month (Standard, first 12 months). **After:** ~$4 per 1M (Standard).            | Needs AWS account. [Pricing](https://aws.amazon.com/polly/pricing/)                                               |
| **Azure Speech**     | **Free tier:** ~0.5M characters/month. Then paid.                                                            | [Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/)                  |

**Recommendation:**

1. **Free:** Use **Edge TTS** – no key, no billing. Only 2 Romanian voices; quality is decent but not the most realistic.
2. **Realistic Romanian (recommended):** Use **ElevenLabs** – one API key, many natural voices. Free tier available; paid per character.
3. **Paid, Google stack:** **Google Cloud TTS** with Chirp 3 HD or WaveNet; use the free tier first.

**Using Edge TTS (free) in this project**

- In `.env` set:
  ```env
  TTS_PROVIDER=edge
  ```
- Do **not** set `GOOGLE_TTS_CREDENTIALS_JSON` when using Edge TTS (no key or JSON needed).
- Install: `pip install edge-tts` (already in `requirements.txt`).
- Run the server as usual. Narrator and character voices are mapped to Microsoft Edge voices (e.g. `en-US-AriaNeural`, `ro-RO-AlinaNeural`) per language.

**Using ElevenLabs (realistic voices) in this project**

- In `.env` set:
  ```env
  TTS_PROVIDER=elevenlabs
  ELEVENLABS_API_KEY=your-api-key-from-elevenlabs-io
  ```
- Get your API key from https://elevenlabs.io/app/settings/api-keys
- Run the server as usual. The app will list all your ElevenLabs voices (default + custom) and use them for narrator and characters. Romanian and 30+ other languages are supported with the same natural voices.
