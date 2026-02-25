import os
import time
import hashlib
import json
import asyncio
import urllib.request
import urllib.error
import urllib.parse
import re
from flask import current_app
from app.utils.file_handler import ensure_directory_exists

GOD_CHARACTER_NAMES = frozenset({'dumnezeu', 'god', 'domnul', 'lord', 'yahweh', 'elohim'})

CHARACTER_NAME_PREFIXES = (
    'apoi', 'și', 'si', 'iar', 'dar', 'atunci', 'acolo', 'aici', 'însă', 'insa',
    'deci', 'totuși', 'totusi', 'prin', 'după', 'dupa',
)


def normalize_character_name_for_voice(name):
    """Map 'Apoi Dumnezeu' -> 'Dumnezeu' so voice selection dedupes and lookup matches."""
    if not name or not (name := (name or '').strip().rstrip('*†').strip()):
        return None
    low = name.lower()
    if low in GOD_CHARACTER_NAMES:
        return name
    for prefix in CHARACTER_NAME_PREFIXES:
        if low.startswith(prefix):
            rest = name[len(prefix):].strip()
            if rest:
                return normalize_character_name_for_voice(rest)
            break
    if ' ' in name:
        for part in name.split():
            if part.lower() in GOD_CHARACTER_NAMES:
                return part
    return name

def remove_verse_number_from_text(text, chunk_type=None):
    """Remove verse numbers from the beginning of text for TTS.
    
    Removes patterns like:
    - "1. Text..." -> "Text..."
    - "1 Text..." -> "Text..."
    - "1) Text..." -> "Text..."
    - "1 - Text..." -> "Text..."
    
    Only applies to verse chunks, not titles or other chunk types.
    """
    if not text or not isinstance(text, str):
        return text
    
    if chunk_type and chunk_type != 'verse':
        return text
    
    text = text.strip()
    
    patterns = [
        r'^\d+\.\s+',           # "1. " or "12. "
        r'^\d+\s+',              # "1 " or "12 "
        r'^\d+\)\s+',            # "1) " or "12) "
        r'^\d+\s*-\s+',          # "1 - " or "12 - "
        r'^\d+\s*:\s+',          # "1: " or "12: "
        r'^\[?\d+\]?\s+',        # "[1] " or "1] " or "[1 "
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, count=1)
    
    return text.strip()


TITLE_CHUNK_TYPES = frozenset({'book_title', 'chapter_number', 'chapter_name', 'section_title'})

_RO_LETTERS = r'A-Za-z\u00C0-\u024f'
_REF_PATTERN = re.compile(
    r'[\s*_**†;.]*(?:\d*[' + _RO_LETTERS + r']{2,4}\.?\s*\d+:\d+(?:\s*,\s*\d+)*(?:\s*[;\s.])*)+',
    re.IGNORECASE
)

def _strip_references_from_tts(text):
    """Remove cross-references so they are never spoken."""
    if not text or not isinstance(text, str):
        return text
    t = _REF_PATTERN.sub(' ', text)
    t = re.sub(r'\*\*', ' ', t)
    t = re.sub(r'\*', ' ', t)
    t = re.sub(r'†', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def prepare_text_for_tts(text, chunk_type=None):
    """Prepare chunk text for TTS: strip verse numbers, references, footnote markers; add emphasis for titles."""
    t = remove_verse_number_from_text(text, chunk_type)
    if not t or not isinstance(t, str):
        return t or ''
    t = _strip_references_from_tts(t.strip())
    if chunk_type and chunk_type in TITLE_CHUNK_TYPES and t and not t.rstrip().endswith('!'):
        t = t.rstrip() + '!'
    return t


LANGUAGE_VOICES_GOOGLE = {
    'en': [
        {'voice_id': 'en-US-Wavenet-C', 'voice_name': 'Narrator (clear)', 'role_tag': 'narrator'},
        {'voice_id': 'en-US-Wavenet-B', 'voice_name': 'Deep — God / authority', 'role_tag': 'god'},
        {'voice_id': 'en-US-Wavenet-D', 'voice_name': 'Male (neutral)', 'role_tag': 'male'},
        {'voice_id': 'en-US-Wavenet-E', 'voice_name': 'Male (warm)', 'role_tag': 'male'},
        {'voice_id': 'en-US-Wavenet-F', 'voice_name': 'Female (neutral)', 'role_tag': 'female'},
        {'voice_id': 'en-US-Wavenet-A', 'voice_name': 'Female (calm)', 'role_tag': 'female'},
    ],
    'ro': [
        {'voice_id': 'ro-RO-Standard-B', 'voice_name': 'Narrator (bărbat)', 'role_tag': 'narrator'},
        {'voice_id': 'ro-RO-Standard-B', 'voice_name': 'Deep — Dumnezeu / autoritate', 'role_tag': 'god'},
        {'voice_id': 'ro-RO-Standard-B', 'voice_name': 'Bărbat (matur)', 'role_tag': 'male'},
        {'voice_id': 'ro-RO-Standard-A', 'voice_name': 'Femeie', 'role_tag': 'female'},
    ],
    'de': [
        {'voice_id': 'de-DE-Standard-A', 'voice_name': 'Narrator (female)', 'role_tag': 'narrator'},
        {'voice_id': 'de-DE-Wavenet-B', 'voice_name': 'Deep — God / authority', 'role_tag': 'god'},
        {'voice_id': 'de-DE-Standard-B', 'voice_name': 'Male', 'role_tag': 'male'},
        {'voice_id': 'de-DE-Standard-A', 'voice_name': 'Female', 'role_tag': 'female'},
        {'voice_id': 'de-DE-Standard-C', 'voice_name': 'Female (alt)', 'role_tag': 'female'},
    ],
    'fr': [
        {'voice_id': 'fr-FR-Standard-A', 'voice_name': 'Narrator (female)', 'role_tag': 'narrator'},
        {'voice_id': 'fr-FR-Wavenet-B', 'voice_name': 'Deep — God / authority', 'role_tag': 'god'},
        {'voice_id': 'fr-FR-Standard-B', 'voice_name': 'Male', 'role_tag': 'male'},
        {'voice_id': 'fr-FR-Standard-A', 'voice_name': 'Female', 'role_tag': 'female'},
        {'voice_id': 'fr-FR-Standard-C', 'voice_name': 'Female (alt)', 'role_tag': 'female'},
    ],
}

CHIRP_HD_ACTORS = (
    ('Achernar', 'Female'), ('Aoede', 'Female'), ('Autonoe', 'Female'), ('Callirrhoe', 'Female'),
    ('Despina', 'Female'), ('Erinome', 'Female'), ('Gacrux', 'Female'), ('Kore', 'Female'),
    ('Laomedeia', 'Female'), ('Leda', 'Female'), ('Pulcherrima', 'Female'), ('Sulafat', 'Female'),
    ('Vindemiatrix', 'Female'), ('Zephyr', 'Female'),
    ('Achird', 'Male'), ('Algenib', 'Male'), ('Algieba', 'Male'), ('Alnilam', 'Male'),
    ('Charon', 'Male'), ('Enceladus', 'Male'), ('Fenrir', 'Male'), ('Iapetus', 'Male'),
    ('Orus', 'Male'), ('Puck', 'Male'), ('Rasalgethi', 'Male'), ('Sadachbia', 'Male'),
    ('Sadaltager', 'Male'), ('Schedar', 'Male'), ('Umbriel', 'Male'), ('Zubenelgenubi', 'Male'),
)

LANGUAGE_VOICES_CHIRP_HD = {
    'en': [
        {'voice_id': 'en-US-Chirp3-HD-Leda', 'voice_name': 'Narrator (Leda)', 'role_tag': 'narrator'},
        {'voice_id': 'en-US-Chirp3-HD-Charon', 'voice_name': 'Deep — God / authority (Charon)', 'role_tag': 'god'},
        {'voice_id': 'en-US-Chirp3-HD-Charon', 'voice_name': 'Charon', 'role_tag': 'male'},
        {'voice_id': 'en-US-Chirp3-HD-Schedar', 'voice_name': 'Schedar', 'role_tag': 'male'},
        {'voice_id': 'en-US-Chirp3-HD-Rasalgethi', 'voice_name': 'Rasalgethi', 'role_tag': 'male'},
        {'voice_id': 'en-US-Chirp3-HD-Achird', 'voice_name': 'Achird', 'role_tag': 'male'},
        {'voice_id': 'en-US-Chirp3-HD-Fenrir', 'voice_name': 'Fenrir', 'role_tag': 'male'},
        {'voice_id': 'en-US-Chirp3-HD-Leda', 'voice_name': 'Leda', 'role_tag': 'female'},
        {'voice_id': 'en-US-Chirp3-HD-Kore', 'voice_name': 'Kore', 'role_tag': 'female'},
        {'voice_id': 'en-US-Chirp3-HD-Achernar', 'voice_name': 'Achernar', 'role_tag': 'female'},
        {'voice_id': 'en-US-Chirp3-HD-Despina', 'voice_name': 'Despina', 'role_tag': 'female'},
    ],
    'ro': [
        {'voice_id': 'ro-RO-Chirp3-HD-Enceladus', 'voice_name': 'Narrator (Enceladus)', 'role_tag': 'narrator'},
        {'voice_id': 'ro-RO-Chirp3-HD-Fenrir', 'voice_name': 'Deep — Dumnezeu (Fenrir)', 'role_tag': 'god'},
        {'voice_id': 'ro-RO-Chirp3-HD-Charon', 'voice_name': 'Charon', 'role_tag': 'male'},
        {'voice_id': 'ro-RO-Chirp3-HD-Schedar', 'voice_name': 'Schedar', 'role_tag': 'male'},
        {'voice_id': 'ro-RO-Chirp3-HD-Rasalgethi', 'voice_name': 'Rasalgethi', 'role_tag': 'male'},
        {'voice_id': 'ro-RO-Chirp3-HD-Achird', 'voice_name': 'Achird', 'role_tag': 'male'},
        {'voice_id': 'ro-RO-Chirp3-HD-Fenrir', 'voice_name': 'Fenrir', 'role_tag': 'male'},
        {'voice_id': 'ro-RO-Chirp3-HD-Alnilam', 'voice_name': 'Alnilam', 'role_tag': 'male'},
        {'voice_id': 'ro-RO-Chirp3-HD-Enceladus', 'voice_name': 'Enceladus', 'role_tag': 'male'},
        {'voice_id': 'ro-RO-Chirp3-HD-Leda', 'voice_name': 'Leda', 'role_tag': 'female'},
        {'voice_id': 'ro-RO-Chirp3-HD-Kore', 'voice_name': 'Kore', 'role_tag': 'female'},
        {'voice_id': 'ro-RO-Chirp3-HD-Achernar', 'voice_name': 'Achernar', 'role_tag': 'female'},
        {'voice_id': 'ro-RO-Chirp3-HD-Despina', 'voice_name': 'Despina', 'role_tag': 'female'},
    ],
}

EDGE_VOICES = {
    'en': [
        {'voice_id': 'en-US-AriaNeural', 'voice_name': 'Narrator (clear, confident)', 'role_tag': 'narrator'},
        {'voice_id': 'en-US-ChristopherNeural', 'voice_name': 'Deep — God / authority', 'role_tag': 'god'},
        {'voice_id': 'en-US-EricNeural', 'voice_name': 'Male (rational)', 'role_tag': 'male'},
        {'voice_id': 'en-US-GuyNeural', 'voice_name': 'Male (warm)', 'role_tag': 'male'},
        {'voice_id': 'en-US-RogerNeural', 'voice_name': 'Male (lively)', 'role_tag': 'male'},
        {'voice_id': 'en-US-SteffanNeural', 'voice_name': 'Male (calm)', 'role_tag': 'male'},
        {'voice_id': 'en-US-JennyNeural', 'voice_name': 'Female (friendly)', 'role_tag': 'female'},
        {'voice_id': 'en-US-MichelleNeural', 'voice_name': 'Female (pleasant)', 'role_tag': 'female'},
    ],
    'ro': [
        {'voice_id': 'ro-RO-EmilNeural', 'voice_name': 'Narrator (bărbat)', 'role_tag': 'narrator'},
        {'voice_id': 'ro-RO-EmilNeural', 'voice_name': 'Deep — Dumnezeu / autoritate', 'role_tag': 'god'},
        {'voice_id': 'ro-RO-EmilNeural', 'voice_name': 'Bărbat (matur)', 'role_tag': 'male'},
        {'voice_id': 'ro-RO-AlinaNeural', 'voice_name': 'Femeie', 'role_tag': 'female'},
    ],
    'de': [
        {'voice_id': 'de-DE-KatjaNeural', 'voice_name': 'Narrator (female)', 'role_tag': 'narrator'},
        {'voice_id': 'de-DE-ConradNeural', 'voice_name': 'Deep — God / authority', 'role_tag': 'god'},
        {'voice_id': 'de-DE-KillianNeural', 'voice_name': 'Male (alt)', 'role_tag': 'male'},
        {'voice_id': 'de-DE-KatjaNeural', 'voice_name': 'Female', 'role_tag': 'female'},
        {'voice_id': 'de-DE-AmalaNeural', 'voice_name': 'Female (alt)', 'role_tag': 'female'},
    ],
    'fr': [
        {'voice_id': 'fr-FR-DeniseNeural', 'voice_name': 'Narrator (female)', 'role_tag': 'narrator'},
        {'voice_id': 'fr-FR-HenriNeural', 'voice_name': 'Deep — God / authority', 'role_tag': 'god'},
        {'voice_id': 'fr-FR-DeniseNeural', 'voice_name': 'Female', 'role_tag': 'female'},
        {'voice_id': 'fr-FR-EloiseNeural', 'voice_name': 'Female (alt)', 'role_tag': 'female'},
    ],
}

def _use_edge_tts():
    return (current_app.config.get('TTS_PROVIDER') or 'google').lower() == 'edge'

def _use_elevenlabs():
    return (current_app.config.get('TTS_PROVIDER') or 'google').lower() == 'elevenlabs'

def _use_chirp_hd():
    if _use_edge_tts() or _use_elevenlabs():
        return False
    return current_app.config.get('TTS_USE_CHIRP_HD', False) in (True, '1', 'true', 'yes')

def initialize_tts_client():
    if _use_edge_tts():
        return None
    creds_path = (
        current_app.config.get('GOOGLE_TTS_CREDENTIALS_JSON')
        or current_app.config.get('GOOGLE_TTS_API_KEY')
    )
    if not creds_path or not os.path.isfile(creds_path):
        raise ValueError(
            "TTS credentials not configured. Set GOOGLE_TTS_CREDENTIALS_JSON (or use TTS_PROVIDER=edge for free Edge TTS)."
        )
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
    from google.cloud import texttospeech
    return texttospeech.TextToSpeechClient()

def _voice_list_for_lang(language_code):
    if _use_edge_tts():
        return EDGE_VOICES.get(language_code, EDGE_VOICES['en'])
    if _use_elevenlabs():
        return _fetch_elevenlabs_voices(language_code) or EDGE_VOICES.get(language_code, EDGE_VOICES['en'])
    if _use_chirp_hd():
        return LANGUAGE_VOICES_CHIRP_HD.get(language_code, LANGUAGE_VOICES_CHIRP_HD['en'])
    return LANGUAGE_VOICES_GOOGLE.get(language_code, LANGUAGE_VOICES_GOOGLE['en'])

def _first_voice_by_tag(voice_list, role_tag):
    for v in voice_list:
        if v.get('role_tag') == role_tag:
            return v['voice_id']
    return voice_list[0]['voice_id'] if voice_list else None

def get_voice_for_language(language_code, role='narrator', gender='male', character_name=None):
    lst = _voice_list_for_lang(language_code)
    if character_name and (character_name or '').strip().lower() in GOD_CHARACTER_NAMES:
        return _first_voice_by_tag(lst, 'god')
    if role == 'narrator':
        return _first_voice_by_tag(lst, 'narrator')
    if (gender or 'male').lower() == 'male':
        return _first_voice_by_tag(lst, 'male')
    return _first_voice_by_tag(lst, 'female')

def generate_voice_settings_hash(settings):
    settings_str = json.dumps(settings, sort_keys=True)
    return hashlib.md5(settings_str.encode()).hexdigest()

def _synthesize_edge_speech(text, voice_id, speed=1.0):
    import edge_tts
    rate = f"{'+' if speed >= 1 else ''}{(speed - 1) * 100:.0f}%"
    
    async def _generate():
        communicate = edge_tts.Communicate(text, voice_id, rate=rate)
        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_generate())
    finally:
        loop.close()

def _parse_elevenlabs_voice_list(voices, language_code):
    first_male_id = first_male_name = None
    out = []
    for v in voices:
        vid = v.get('voice_id') or v.get('id')
        if not vid:
            continue
        name = v.get('name') or vid
        labels = v.get('labels') or {}
        gender = (labels.get('gender') or 'neutral').lower()
        role_tag = 'female' if gender == 'female' else 'male'
        if role_tag == 'male' and first_male_id is None:
            first_male_id, first_male_name = vid, name
        out.append({
            'voice_id': vid,
            'voice_name': name,
            'language_code': language_code or 'en',
            'role_tag': role_tag,
        })
    if first_male_id:
        out.insert(0, {'voice_id': first_male_id, 'voice_name': first_male_name or first_male_id, 'language_code': language_code or 'en', 'role_tag': 'god'})
        out.insert(0, {'voice_id': first_male_id, 'voice_name': first_male_name or first_male_id, 'language_code': language_code or 'en', 'role_tag': 'narrator'})
    return out if out else None

_VOICE_CACHE = {}
_VOICE_CACHE_TTL = 3600

def _get_cached_voices(cache_key):
    entry = _VOICE_CACHE.get(cache_key)
    if entry and (time.time() - entry[0]) < _VOICE_CACHE_TTL:
        return entry[1]
    return None

def _set_cached_voices(cache_key, data):
    _VOICE_CACHE[cache_key] = (time.time(), data)

def _fetch_elevenlabs_voices(language_code):
    api_key = (current_app.config.get('ELEVENLABS_API_KEY') or '').strip()
    if not api_key:
        return None
    lang = language_code or 'en'
    cached = _get_cached_voices(f"elevenlab_{lang}")
    if cached is not None:
        return cached

    def fetch_v1():
        req = urllib.request.Request(
            'https://api.elevenlabs.io/v1/voices',
            headers={'xi-api-key': api_key, 'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if isinstance(data, list):
            return data
        return data.get('voices') or []

    def fetch_v2():
        all_voices = []
        next_token = None
        for _ in range(20):
            url = 'https://api.elevenlabs.io/v2/voices?page_size=100'
            if next_token:
                url += '&next_page_token=' + urllib.parse.quote(next_token)
            req = urllib.request.Request(
                url,
                headers={'xi-api-key': api_key, 'Accept': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            page = data.get('voices') or []
            all_voices.extend(page)
            if not data.get('has_more'):
                break
            next_token = data.get('next_page_token')
            if not next_token:
                break
        return all_voices

    try:
        raw = fetch_v1()
        if raw:
            result = _parse_elevenlabs_voice_list(raw, lang)
            if result:
                _set_cached_voices(f"elevenlab_{lang}", result)
            return result
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError, KeyError):
        pass
    try:
        raw = fetch_v2()
        if raw:
            result = _parse_elevenlabs_voice_list(raw, lang)
            if result:
                _set_cached_voices(f"elevenlab_{lang}", result)
            return result
    except Exception:
        pass
    return None

def clone_elevenlabs_voice(audio_file_path, voice_name, description=None, remove_background_noise=False):
    """Clone a voice from an audio sample using ElevenLabs Instant Voice Cloning API."""
    try:
        import requests
    except ImportError:
        raise ImportError("requests library is required for voice cloning. Install it with: pip install requests")
    
    api_key = current_app.config.get('ELEVENLABS_API_KEY')
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not set")
    
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
    
    url = 'https://api.elevenlabs.io/v1/voices/add'
    
    with open(audio_file_path, 'rb') as audio_file:
        files = {
            'files': (os.path.basename(audio_file_path), audio_file, 'audio/mpeg')
        }
        
        data = {
            'name': voice_name,
            'remove_background_noise': str(remove_background_noise).lower()
        }
        
        if description:
            data['description'] = description
        
        headers = {
            'xi-api-key': api_key
        }
        
        try:
            response = requests.post(url, files=files, data=data, headers=headers, timeout=120)
            response.raise_for_status()
            response_data = response.json()
            for k in list(_VOICE_CACHE.keys()):
                if k.startswith('elevenlab_'):
                    del _VOICE_CACHE[k]
            return {
                'voice_id': response_data.get('voice_id'),
                'requires_verification': response_data.get('requires_verification', False),
                'name': voice_name
            }
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            if e.response is not None:
                try:
                    error_body = e.response.json()
                    detail = error_body.get('detail', {})
                    if isinstance(detail, dict):
                        error_msg = detail.get('message', str(e))
                    elif isinstance(detail, str):
                        error_msg = detail
                    else:
                        error_msg = error_body.get('message', str(e))
                except:
                    error_msg = e.response.text or str(e)
            
            error_lower = error_msg.lower()
            if 'permission' in error_lower or 'create_instant_voice_clone' in error_lower:
                raise Exception(
                    "Your ElevenLabs API key doesn't have permission to create voice clones. "
                    "Please go to https://elevenlabs.io/app/settings/api-keys and ensure your API key has "
                    "the 'create_instant_voice_clone' permission enabled."
                )
            if 'subscription' in error_lower or 'no access' in error_lower or 'upgrade' in error_lower:
                raise Exception(
                    "Instant Voice Cloning requires a paid ElevenLabs subscription. "
                    "The free tier does not include this feature. "
                    "Please upgrade your plan at https://elevenlabs.io/pricing or use the default voices available in your plan."
                )
            raise Exception(f"ElevenLabs API error: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"ElevenLabs API error: {str(e)}")

def _synthesize_elevenlabs_speech(text, voice_id, language_code='en', speed=1.0, pitch=0.0):
    api_key = current_app.config.get('ELEVENLABS_API_KEY')
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not set")
    lang = (language_code or 'en').split('-')[0].lower()
    body = {
        'text': text,
        'model_id': 'eleven_multilingual_v2',
        'language_code': lang,
    }
    if speed != 1.0:
        body['voice_settings'] = {'stability': 0.5, 'similarity_boost': 0.75, 'speed': max(0.5, min(2.0, float(speed)))}
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{urllib.parse.quote(str(voice_id), safe="")}?output_format=mp3_44100_128'
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            'xi-api-key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'audio/mpeg',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()

def synthesize_speech(text, voice_id, language_code='en', speed=1.0, pitch=0.0):
    if _use_elevenlabs() or (not _is_locale_voice_id(voice_id) and current_app.config.get('ELEVENLABS_API_KEY')):
        return _synthesize_elevenlabs_speech(text, voice_id, language_code=language_code, speed=speed, pitch=pitch)
    if _use_edge_tts():
        return _synthesize_edge_speech(text, voice_id, speed=speed)
    
    from google.cloud import texttospeech
    client = initialize_tts_client()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_id,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speed,
        pitch=pitch,
    )
    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config
    )
    return response.audio_content

def _voice_slug(role, character_name):
    if role == 'narrator' or not (character_name or '').strip():
        return 'narrator'
    slug = re.sub(r'[^\w\s-]', '', (character_name or '').strip())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-').lower()[:30] or 'character'
    return slug or 'character'


def _pdf_ref_from_filename(pdf_filename, pdf_id):
    """PDF folder name without extension (e.g. biblia.pdf -> biblia)."""
    if not pdf_filename:
        return f"pdf_{pdf_id}"
    name = re.sub(r'\.pdf$', '', pdf_filename, flags=re.I)
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name).strip('-').lower()[:50]
    return name or f"pdf_{pdf_id}"


def get_voice_name_for_id(voice_id, language_code):
    """Resolve display name for a voice_id from available voices (for readable folder names)."""
    if not voice_id:
        return None
    try:
        voices = get_available_voices_for_language(language_code or 'en')
        for v in voices:
            if v.get('voice_id') == voice_id:
                return v.get('voice_name') or voice_id
    except Exception:
        pass
    if '-' in voice_id and len(voice_id) > 10:
        part = voice_id.split('-')[-1]
        if part and part.isalpha():
            return part
    return None


def _actor_slug(voice_id, voice_name=None):
    """Folder name for the voice actor: readable name, or fallback from voice_id, or voice-<short_id>."""
    if (voice_name or '').strip():
        slug = re.sub(r'[^\w\s-]', '', (voice_name or '').strip())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-').lower()[:40]
        if slug:
            return slug
    if (voice_id or '').strip():
        vid = (voice_id or '').strip()
        if '-' in vid and len(vid) > 10:
            part = vid.split('-')[-1]
            if part and len(part) >= 2 and part.isalpha():
                return part.lower()[:40]
        if vid.isalnum() and len(vid) >= 12:
            return f"voice-{vid[:8]}"
        slug = re.sub(r'[^\w\s-]', '', vid)
        slug = re.sub(r'[-\s]+', '-', slug).strip('-').lower()[:40]
        if slug:
            return slug
    return 'voice'


def save_audio_file(audio_content, chunk_id, audio_folder, pdf_id=None, pdf_filename=None, voice_id=None, chunk=None, voice_settings_hash=None, voice_name=None, character_slug=None, actor_slug=None):
    """Save audio with structure: transcriptions/<pdf_ref>/<character>/<actor>/seg....mp3
    pdf_ref = sanitized PDF name (e.g. biblia-in-limba-romana-dumitru-cornilescu-page-5).
    character = narrator | character slug (e.g. dumnezeu).
    actor = voice actor name for readability (e.g. fenrir, enceladus); fallback voice-<id> when name unknown.
    """
    hash_suffix = (voice_settings_hash or "")[:8] if voice_settings_hash else ""
    if chunk is not None:
        pos = getattr(chunk, 'position', 0)
        seg_slug = _voice_slug(getattr(chunk, 'role', 'narrator'), getattr(chunk, 'character_name', None))
        base_name = f"seg{pos:04d}_{seg_slug}"
        filename = f"{base_name}_{hash_suffix}.mp3" if hash_suffix else f"{base_name}.mp3"
    else:
        filename = f"chunk_{chunk_id}.mp3"

    if pdf_id and pdf_filename:
        pdf_ref = _pdf_ref_from_filename(pdf_filename, pdf_id)
        base = os.path.join(os.path.abspath(audio_folder), 'transcriptions', pdf_ref)
        if character_slug and actor_slug:
            transcription_folder = os.path.join(base, character_slug, actor_slug)
        else:
            transcription_folder = base
        ensure_directory_exists(transcription_folder)
        file_path = os.path.join(transcription_folder, filename)
    elif pdf_id:
        transcription_folder = os.path.join(os.path.abspath(audio_folder), 'transcriptions', str(pdf_id))
        ensure_directory_exists(transcription_folder)
        file_path = os.path.join(transcription_folder, filename)
    else:
        ensure_directory_exists(audio_folder)
        file_path = os.path.join(os.path.abspath(audio_folder), filename)
    with open(file_path, 'wb') as out:
        out.write(audio_content)
    return file_path

def language_code_from_voice_id(voice_id):
    parts = (voice_id or "").split("-")
    if len(parts) >= 2 and len(parts[0]) == 2 and len(parts[1]) == 2:
        return f"{parts[0]}-{parts[1]}"
    return None

def _normalize_google_language_code(language_code):
    if not language_code or "-" in language_code:
        return language_code
    _locale_map = {'ro': 'ro-RO', 'en': 'en-US', 'de': 'de-DE', 'fr': 'fr-FR', 'es': 'es-ES', 'it': 'it-IT'}
    return _locale_map.get(language_code.lower(), language_code)

def _voice_matches_language(voice_language_codes, requested_code):
    if not voice_language_codes:
        return False
    if requested_code in voice_language_codes:
        return True
    prefix = requested_code.split("-")[0].lower()
    for code in voice_language_codes:
        if code and code.split("-")[0].lower() == prefix:
            return True
    return False

def _fetch_google_voices_for_language(language_code):
    lang = _normalize_google_language_code(language_code) or language_code
    cached = _get_cached_voices(f"google_{lang}")
    if cached is not None:
        return cached
    try:
        client = initialize_tts_client()
        from google.cloud.texttospeech import ListVoicesRequest
        request = ListVoicesRequest(language_code=lang)
        response = client.list_voices(request=request)
        out = []
        for v in response.voices:
            if not _voice_matches_language(list(v.language_codes or []), language_code):
                continue
            name = v.name or ""
            gender = "Male" if v.ssml_gender == 1 else "Female" if v.ssml_gender == 2 else ""
            label = name
            if "Wavenet" in name or "Neural2" in name or "Chirp" in name:
                short = name.split("-")[-1] if "-" in name else name
                label = f"{short} ({gender})" if gender else short
            else:
                label = f"{name} ({gender})" if gender else name
            actual_lang = (v.language_codes or [language_code])[0]
            out.append({
                'voice_id': name,
                'voice_name': label,
                'language_code': actual_lang,
            })
        if out:
            _set_cached_voices(f"google_{lang}", out)
            return out
    except Exception:
        pass
    return None

def _is_locale_voice_id(voice_id):
    """Edge/Google use xx-XX-Name (e.g. ro-RO-EmilNeural). ElevenLabs uses alphanumeric IDs."""
    if not voice_id or not isinstance(voice_id, str):
        return False
    parts = voice_id.split('-')
    return len(parts) >= 3 and len(parts[0]) == 2 and len(parts[1]) == 2

def get_available_voices_for_language(language_code):
    if _use_elevenlabs():
        lst = _fetch_elevenlabs_voices(language_code)
        if lst:
            seen = set()
            out = []
            for v in lst:
                vid = v['voice_id']
                if vid not in seen:
                    seen.add(vid)
                    out.append({
                        'voice_id': vid,
                        'voice_name': v.get('voice_name') or vid,
                        'language_code': v.get('language_code') or language_code,
                    })
            return out
        return []
    if _use_edge_tts():
        lst = EDGE_VOICES.get(language_code, EDGE_VOICES['en'])
        seen = set()
        out = []
        for v in lst:
            vid = v['voice_id']
            if vid not in seen:
                seen.add(vid)
                out.append({
                    'voice_id': vid,
                    'voice_name': v.get('voice_name') or vid,
                    'language_code': language_code,
                })
        elevenlabs = _fetch_elevenlabs_voices(language_code)
        if elevenlabs:
            for v in elevenlabs:
                vid = v['voice_id']
                if vid not in seen:
                    seen.add(vid)
                    out.append({
                        'voice_id': vid,
                        'voice_name': v.get('voice_name') or vid,
                        'language_code': v.get('language_code') or language_code,
                    })
        return out

    if _use_chirp_hd():
        locale = _normalize_google_language_code(language_code) or language_code
        if "-" not in locale and len(locale) == 2:
            locale = f"{locale}-{locale.upper()}"
        out = []
        for name, gender in CHIRP_HD_ACTORS:
            voice_id = f"{locale}-Chirp3-HD-{name}"
            out.append({
                'voice_id': voice_id,
                'voice_name': f"{name} ({gender})",
                'language_code': locale,
            })
        return out

    api_voices = _fetch_google_voices_for_language(language_code)
    if api_voices:
        return api_voices

    lst = LANGUAGE_VOICES_GOOGLE.get(language_code, LANGUAGE_VOICES_GOOGLE['en'])
    seen = set()
    out = []
    for v in lst:
        vid = v['voice_id']
        if vid not in seen:
            seen.add(vid)
            out.append({
                'voice_id': vid,
                'voice_name': v.get('voice_name') or vid,
                'language_code': language_code,
            })
    return out
