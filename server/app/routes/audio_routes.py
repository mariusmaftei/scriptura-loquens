from flask import Blueprint, request, jsonify, send_file
from app.database import db
from app.models import PDF, Chunk, VoiceSetting, AudioFile, AmbientTrack
from app.services.tts_service import (
    synthesize_speech, save_audio_file, get_voice_for_language,
    generate_voice_settings_hash, get_available_voices_for_language,
    language_code_from_voice_id, clone_elevenlabs_voice,
    prepare_text_for_tts, _voice_slug, _actor_slug, _pdf_ref_from_filename,
)
from app.config import Config
from app.utils.file_handler import ensure_directory_exists
from werkzeug.utils import secure_filename
import os
import hashlib
import re

bp = Blueprint('audio', __name__)


CUSTOM_VOICE_ID = 'custom'


def _get_current_audio_files_for_pdf(pdf_id):
    """Return one AudioFile per chunk: prefer custom upload, else TTS matching voice settings."""
    chunks = Chunk.query.filter_by(pdf_id=pdf_id).order_by(Chunk.position).all()
    if not chunks:
        return []
    chunk_ids = [c.id for c in chunks]
    all_audio = AudioFile.query.filter(AudioFile.chunk_id.in_(chunk_ids)).all()
    audio_by_chunk = {}
    for a in all_audio:
        audio_by_chunk.setdefault(a.chunk_id, []).append(a)
    voice_settings = VoiceSetting.query.filter_by(pdf_id=pdf_id).all()
    vs_lookup = {(vs.role, vs.character_name): vs for vs in voice_settings}
    result = []
    for chunk in chunks:
        chunk_audios = audio_by_chunk.get(chunk.id) or []
        custom = next((a for a in chunk_audios if a.voice_id == CUSTOM_VOICE_ID), None)
        if custom:
            result.append(custom)
            continue
        vs = vs_lookup.get((chunk.role, chunk.character_name))
        if not vs:
            continue
        settings_hash = generate_voice_settings_hash({
            'voice_id': vs.voice_id,
            'speed': vs.speed,
            'pitch': vs.pitch
        })
        audio = next((a for a in chunk_audios if a.voice_settings_hash == settings_hash), None)
        if audio:
            result.append(audio)
    return result


def _get_pdf_reference_name(pdf):
    """Generate a clean reference name for PDF folder organization."""
    if not pdf:
        return None
    name = pdf.filename or f"pdf_{pdf.id}"
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    name = name.strip('-').lower()[:50]
    return name or f"pdf_{pdf.id}"

def _resolve_audio_path(audio_file):
    """Resolve audio file path, handling both old and new folder structures."""
    path = (audio_file.audio_path or "").strip()
    if not path:
        return None

    if os.path.isabs(path) and os.path.exists(path):
        return path

    audio_root = os.path.abspath(Config.AUDIO_FOLDER)

    if os.path.exists(path):
        return path

    basename = os.path.basename(path)

    chunk = Chunk.query.get(audio_file.chunk_id)
    if chunk and chunk.pdf_id:
        pdf = PDF.query.get(chunk.pdf_id)
        pdf_ref = _pdf_ref_from_filename(pdf.filename, chunk.pdf_id) if pdf else str(chunk.pdf_id)
        flat_path = os.path.join(audio_root, 'transcriptions', pdf_ref, basename)
        if os.path.exists(flat_path):
            return flat_path
        legacy_ref = _get_pdf_reference_name(pdf) if pdf else str(chunk.pdf_id)
        if legacy_ref != pdf_ref:
            flat_legacy = os.path.join(audio_root, 'transcriptions', legacy_ref, basename)
            if os.path.exists(flat_legacy):
                return flat_legacy
        transcription_path_legacy = os.path.join(audio_root, 'transcriptions', str(chunk.pdf_id), basename)
        if os.path.exists(transcription_path_legacy):
            return transcription_path_legacy
        pdf_base = os.path.join(audio_root, 'transcriptions', pdf_ref)
        if os.path.isdir(pdf_base):
            for root, _dirs, files in os.walk(pdf_base):
                if basename in files:
                    return os.path.join(root, basename)

    fallback = os.path.join(audio_root, basename)
    if os.path.exists(fallback):
        return fallback

    return path

@bp.route('/pdf/<int:pdf_id>/voices', methods=['GET'])
def get_available_voices(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    language_code = pdf.language or 'en'
    voices = get_available_voices_for_language(language_code)
    return jsonify(voices)

@bp.route('/pdf/<int:pdf_id>/voice-settings', methods=['GET'])
def get_voice_settings(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    settings = VoiceSetting.query.filter_by(pdf_id=pdf_id).all()
    
    result = {}
    for setting in settings:
        key = setting.character_name if setting.character_name else setting.role
        result[key] = setting.to_dict()
    
    return jsonify(result)

@bp.route('/pdf/<int:pdf_id>/voice-settings', methods=['PUT'])
def update_voice_settings(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    data = request.get_json()
    
    try:
        existing_settings = {(
            s.role, s.character_name
        ): s for s in VoiceSetting.query.filter_by(pdf_id=pdf_id).all()}
        for key, settings_data in data.items():
            parts = key.split('_', 1)
            role = parts[0]
            character_name = parts[1] if len(parts) > 1 else None
            if character_name == 'narrator':
                character_name = None
            existing = existing_settings.get((role, character_name))
            
            if existing:
                existing.voice_id = settings_data.get('voice_id', existing.voice_id)
                existing.voice_name = settings_data.get('voice_name', existing.voice_name)
                existing.speed = settings_data.get('speed', existing.speed)
                existing.pitch = settings_data.get('pitch', existing.pitch)
                existing.volume = settings_data.get('volume', existing.volume)
            else:
                new_setting = VoiceSetting(
                    pdf_id=pdf_id,
                    role=role,
                    character_name=character_name,
                    language_code=pdf.language or 'en',
                    voice_id=settings_data.get('voice_id'),
                    voice_name=settings_data.get('voice_name'),
                    speed=settings_data.get('speed', 1.0),
                    pitch=settings_data.get('pitch', 0.0),
                    volume=settings_data.get('volume', 1.0)
                )
                db.session.add(new_setting)
                existing_settings[(role, character_name)] = new_setting
        
        db.session.commit()
        
        settings = list(existing_settings.values())
        result = {}
        for setting in settings:
            key = setting.character_name if setting.character_name else setting.role
            result[key] = setting.to_dict()
        
        return jsonify(result), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/pdf/<int:pdf_id>/regenerate-audio', methods=['POST'])
def regenerate_audio(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    chunks = Chunk.query.filter_by(pdf_id=pdf_id).order_by(Chunk.position).all()
    
    if not chunks:
        return jsonify({'error': 'No chunks found. Analyze PDF first'}), 400
    
    try:
        audio_folder = Config.AUDIO_FOLDER
        language_code = pdf.language or 'en'
        chunk_ids = [c.id for c in chunks]
        vs_list = VoiceSetting.query.filter_by(pdf_id=pdf_id).all()
        vs_lookup = {(vs.role, vs.character_name): vs for vs in vs_list}
        existing_audio_all = AudioFile.query.filter(
            AudioFile.chunk_id.in_(chunk_ids)
        ).all()
        existing_by_chunk_hash = {
            (a.chunk_id, a.voice_settings_hash): a
            for a in existing_audio_all
            if a.voice_settings_hash
        }

        for chunk in chunks:
            voice_setting = vs_lookup.get((chunk.role, chunk.character_name))
            if not voice_setting:
                voice_id = get_voice_for_language(
                    language_code, chunk.role, character_name=chunk.character_name
                )
                voice_setting = VoiceSetting(
                    pdf_id=pdf_id,
                    role=chunk.role,
                    character_name=chunk.character_name,
                    language_code=language_code,
                    voice_id=voice_id,
                    speed=1.0,
                    pitch=0.0,
                    volume=1.0
                )
                db.session.add(voice_setting)
                db.session.flush()
                vs_lookup[(chunk.role, chunk.character_name)] = voice_setting

            settings_hash = generate_voice_settings_hash({
                'voice_id': voice_setting.voice_id,
                'speed': voice_setting.speed,
                'pitch': voice_setting.pitch
            })
            if existing_by_chunk_hash.get((chunk.id, settings_hash)):
                continue

            synth_lang = language_code_from_voice_id(voice_setting.voice_id) or language_code
            text_for_tts = prepare_text_for_tts(chunk.text, chunk.chunk_type)
            audio_content = synthesize_speech(
                text_for_tts,
                voice_setting.voice_id,
                synth_lang,
                voice_setting.speed,
                voice_setting.pitch
            )

            character_slug = _voice_slug(chunk.role, chunk.character_name)
            actor_slug = _actor_slug(voice_setting.voice_id, voice_setting.voice_name)
            audio_path = save_audio_file(
                audio_content,
                chunk.id,
                audio_folder,
                pdf_id=pdf_id,
                pdf_filename=pdf.filename,
                voice_id=voice_setting.voice_id,
                chunk=chunk,
                voice_settings_hash=settings_hash,
                character_slug=character_slug,
                actor_slug=actor_slug,
            )

            audio_file = AudioFile(
                chunk_id=chunk.id,
                audio_path=audio_path,
                voice_id=voice_setting.voice_id,
                voice_settings_hash=settings_hash
            )
            db.session.add(audio_file)
        
        db.session.commit()

        audio_files = _get_current_audio_files_for_pdf(pdf_id)
        return jsonify([a.to_dict() for a in audio_files]), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/voices/clone', methods=['POST'])
def clone_voice():
    """Clone a voice from an audio sample using ElevenLabs."""
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio_file']
    voice_name = request.form.get('voice_name', '').strip()
    description = request.form.get('description', '').strip() or None
    remove_background_noise = request.form.get('remove_background_noise', 'false').lower() == 'true'
    
    if not voice_name:
        return jsonify({'error': 'Voice name is required'}), 400
    
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    allowed_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}
    file_ext = os.path.splitext(audio_file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400
    
    try:
        voice_clones_folder = os.path.join(Config.AUDIO_FOLDER, 'voice-clones')
        ensure_directory_exists(voice_clones_folder)
        
        filename = secure_filename(audio_file.filename)
        timestamp = str(int(os.path.getmtime(__file__) if os.path.exists(__file__) else 0))
        unique_filename = f"{voice_name.replace(' ', '-')}_{timestamp}{file_ext}"
        file_path = os.path.join(voice_clones_folder, unique_filename)
        
        audio_file.save(file_path)
        
        result = clone_elevenlabs_voice(
            file_path,
            voice_name,
            description=description,
            remove_background_noise=remove_background_noise
        )
        
        return jsonify({
            'success': True,
            'voice_id': result['voice_id'],
            'voice_name': result['name'],
            'requires_verification': result.get('requires_verification', False),
            'message': 'Voice cloned successfully. It will appear in the voice list shortly.'
        }), 200
        
    except Exception as e:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return jsonify({'error': str(e)}), 500

@bp.route('/pdf/<int:pdf_id>/audio', methods=['GET'])
def get_audio(pdf_id):
    PDF.query.get_or_404(pdf_id)
    audio_files = _get_current_audio_files_for_pdf(pdf_id)
    return jsonify([a.to_dict() for a in audio_files])

def _mimetype_for_audio_path(path):
    ext = (os.path.splitext(path or '')[1] or '').lower()
    return {'': 'audio/mpeg', '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg', '.webm': 'audio/webm'}.get(ext, 'audio/mpeg')


@bp.route('/audio/<int:audio_id>/file', methods=['GET'])
def get_audio_file(audio_id):
    audio_file = AudioFile.query.get_or_404(audio_id)
    path = _resolve_audio_path(audio_file)
    if not path or not os.path.exists(path):
        return jsonify({'error': 'Audio file not found'}), 404
    mimetype = _mimetype_for_audio_path(path)
    response = send_file(path, mimetype=mimetype, as_attachment=False)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@bp.route('/ambient/<int:ambient_id>/file', methods=['GET'])
def get_ambient_file(ambient_id):
    track = AmbientTrack.query.get_or_404(ambient_id)
    path = (track.file_path or "").strip()
    if not path:
        return jsonify({'error': 'Ambient file not found'}), 404
    if not os.path.isabs(path):
        path = os.path.join(os.path.abspath(Config.AUDIO_FOLDER), path)
    if not os.path.exists(path):
        return jsonify({'error': 'Ambient file not found'}), 404
    ext = os.path.splitext(path)[1].lower()
    mimetype = 'audio/mpeg' if ext == '.mp3' else 'audio/wav' if ext == '.wav' else 'audio/mp4' if ext == '.m4a' else 'audio/ogg'
    return send_file(path, mimetype=mimetype, as_attachment=False)


@bp.route('/audio/chunk/<int:chunk_id>', methods=['GET'])
def get_audio_by_chunk(chunk_id):
    chunk = Chunk.query.get_or_404(chunk_id)
    voice_setting = VoiceSetting.query.filter_by(
        pdf_id=chunk.pdf_id,
        role=chunk.role,
        character_name=chunk.character_name
    ).first()
    if not voice_setting:
        return jsonify({'error': 'No voice setting for this chunk'}), 404
    settings_hash = generate_voice_settings_hash({
        'voice_id': voice_setting.voice_id,
        'speed': voice_setting.speed,
        'pitch': voice_setting.pitch
    })
    audio_file = AudioFile.query.filter_by(
        chunk_id=chunk_id,
        voice_settings_hash=settings_hash
    ).first()
    if not audio_file:
        return jsonify({'error': 'Audio not found for this chunk'}), 404
    path = _resolve_audio_path(audio_file)
    if not path or not os.path.exists(path):
        return jsonify({'error': 'Audio file not found'}), 404
    return send_file(path, mimetype='audio/mpeg', as_attachment=False)


@bp.route('/pdf/<int:pdf_id>/chunks/<int:chunk_id>/custom-audio', methods=['POST'])
def upload_custom_chunk_audio(pdf_id, chunk_id):
    PDF.query.get_or_404(pdf_id)
    chunk = Chunk.query.filter_by(id=chunk_id, pdf_id=pdf_id).first_or_404()
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    ext = (os.path.splitext(secure_filename(file.filename) or '')[1] or '.mp3').lower()
    if ext not in ('.mp3', '.wav', '.m4a', '.ogg', '.webm'):
        return jsonify({'error': 'Invalid format. Use mp3, wav, m4a, ogg or webm'}), 400
    pdf = PDF.query.get(pdf_id)
    pdf_ref = _pdf_ref_from_filename(pdf.filename, pdf_id) if pdf else str(pdf_id)
    character_slug = _voice_slug(chunk.role, chunk.character_name)
    actor_slug = 'custom'
    audio_root = os.path.abspath(Config.AUDIO_FOLDER)
    transcription_folder = os.path.join(audio_root, 'transcriptions', pdf_ref, character_slug, actor_slug)
    ensure_directory_exists(transcription_folder)
    base_name = f"seg{chunk.position:04d}_custom"
    filename = f"{base_name}_{hashlib.md5(os.urandom(8)).hexdigest()[:8]}{ext}"
    file_path = os.path.join(transcription_folder, filename)
    file.save(file_path)
    existing = AudioFile.query.filter_by(chunk_id=chunk_id, voice_id=CUSTOM_VOICE_ID).first()
    if existing:
        old_path = _resolve_audio_path(existing)
        if old_path and os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass
        existing.audio_path = file_path
        db.session.commit()
        return jsonify(existing.to_dict()), 200
    audio_file = AudioFile(
        chunk_id=chunk_id,
        audio_path=file_path,
        voice_id=CUSTOM_VOICE_ID,
        voice_settings_hash=None
    )
    db.session.add(audio_file)
    db.session.commit()
    return jsonify(audio_file.to_dict()), 201


def _sanitize_filename(name):
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')[:50]

def _get_preview_cache_key(voice_id, language_code, text, speed, pitch):
    preview_text = text[:200] if len(text) > 200 else text
    key_data = f"{voice_id}|{language_code}|{preview_text}|{speed}|{pitch}"
    return hashlib.md5(key_data.encode()).hexdigest()

def _get_voice_name_for_cache(voice_id, language_code):
    try:
        voices = get_available_voices_for_language(language_code)
        for v in voices:
            if v.get('voice_id') == voice_id:
                name = v.get('voice_name') or voice_id
                return _sanitize_filename(name)
    except Exception:
        pass
    return _sanitize_filename(voice_id.split('-')[-1] if '-' in voice_id else voice_id[:20])

@bp.route('/voice/preview', methods=['POST'])
def preview_voice():
    data = request.get_json()
    voice_id = data.get('voice_id')
    language_code = data.get('language_code', 'en')
    text = data.get('text', 'Hello, this is a voice preview.')
    speed = data.get('speed', 1.0)
    pitch = data.get('pitch', 0.0)
    
    if not voice_id:
        return jsonify({'error': 'voice_id is required'}), 400
    
    try:
        preview_text = text[:200] if len(text) > 200 else text
        cache_key = _get_preview_cache_key(voice_id, language_code, preview_text, speed, pitch)
        voice_name = _get_voice_name_for_cache(voice_id, language_code)
        previews_dir = os.path.join(os.path.abspath(Config.AUDIO_FOLDER), 'previews')
        ensure_directory_exists(previews_dir)
        cache_path = os.path.join(previews_dir, f"{voice_name}_{cache_key}.mp3")
        
        if os.path.exists(cache_path):
            return send_file(
                cache_path,
                mimetype='audio/mpeg',
                as_attachment=False,
                download_name='preview.mp3'
            )
        
        text_for_tts = prepare_text_for_tts(preview_text)
        audio_content = synthesize_speech(
            text_for_tts,
            voice_id,
            language_code,
            speed,
            pitch
        )
        
        with open(cache_path, 'wb') as f:
            f.write(audio_content)
        
        from io import BytesIO
        audio_buffer = BytesIO(audio_content)
        audio_buffer.seek(0)
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='preview.mp3'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
