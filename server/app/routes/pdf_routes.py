from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.database import db
from app.models import PDF, ExtractedText, Chunk, AmbientTrack
from app.services.pdf_service import process_pdf_file, process_pdf_file_with_format
from app.services.gemini_service import analyze_text_in_batches
from app.utils.file_handler import save_uploaded_file, generate_file_hash
from app.config import Config
import json
import os
import tempfile
import traceback
import uuid

bp = Blueprint('pdf', __name__)

@bp.route('/analyze-pdf-json', methods=['POST'])
def analyze_pdf_json():
    """Upload PDF, extract + analyze, return full JSON for inspection (no DB persist)."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    tmp_path = None
    try:
        upload_root = os.path.abspath(Config.UPLOAD_FOLDER)
        os.makedirs(upload_root, exist_ok=True)
        safe_name = secure_filename(file.filename) or 'upload.pdf'
        tmp_path = os.path.join(upload_root, f"analyze_{uuid.uuid4().hex}_{safe_name}")
        file.save(tmp_path)
        result = process_pdf_file_with_format(tmp_path)
        format_lines = result.get('format_lines') or []
        chunks_data = analyze_text_in_batches(format_lines=format_lines) if format_lines else analyze_text_in_batches(result.get('cleaned_text', ''))
        out = {
            'filename': file.filename,
            'language': result.get('language_code'),
            'language_name': result.get('language_name'),
            'chunks': chunks_data,
        }
        return jsonify(out), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'message': str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

@bp.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400
    
    try:
        upload_folder = os.path.abspath(Config.UPLOAD_FOLDER)
        file_path = save_uploaded_file(file, upload_folder)
        file_hash = generate_file_hash(file_path)
        existing_pdf = PDF.query.filter_by(file_hash=file_hash).first()
        if existing_pdf:
            existing_pdf.file_path = file_path
            existing_pdf.filename = file.filename
            db.session.commit()
            return jsonify(existing_pdf.to_dict()), 200
        pdf = PDF(
            filename=file.filename,
            file_hash=file_hash,
            file_path=file_path,
            status='pending'
        )
        db.session.add(pdf)
        db.session.commit()
        return jsonify(pdf.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e), 'message': str(e)}), 500

@bp.route('/pdf/<int:pdf_id>', methods=['GET'])
def get_pdf(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    return jsonify(pdf.to_dict())


@bp.route('/pdf/<int:pdf_id>/custom-voice-names', methods=['PUT'])
def update_custom_voice_names(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    data = request.get_json() or {}
    if 'custom_narrator_name' in data:
        pdf.custom_narrator_name = (data['custom_narrator_name'] or '').strip() or None
    if 'custom_voice_actor_name' in data:
        pdf.custom_voice_actor_name = (data['custom_voice_actor_name'] or '').strip() or None
    db.session.commit()
    return jsonify(pdf.to_dict())


@bp.route('/pdf/<int:pdf_id>/text', methods=['GET'])
def get_pdf_text(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    extracted_text = ExtractedText.query.filter_by(pdf_id=pdf_id).first()
    
    if not extracted_text:
        return jsonify({'error': 'Text not extracted yet'}), 404
    
    return jsonify(extracted_text.to_dict())

@bp.route('/pdf/<int:pdf_id>/process', methods=['POST'])
def process_pdf(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    
    if pdf.status == 'completed':
        return jsonify({'message': 'PDF already processed', 'pdf': pdf.to_dict()}), 200
    
    try:
        pdf.status = 'processing'
        pdf.error_message = None
        db.session.commit()

        upload_root = os.path.abspath(Config.UPLOAD_FOLDER)
        file_path = (pdf.file_path or "").strip()
        if not file_path:
            pdf.status = 'error'
            pdf.error_message = 'PDF file not found. Upload the file again.'
            db.session.commit()
            return jsonify({'error': pdf.error_message}), 404
        if not os.path.isabs(file_path):
            file_path = os.path.join(upload_root, os.path.basename(file_path))
        if not os.path.exists(file_path):
            alt = os.path.join(upload_root, pdf.filename)
            if os.path.exists(alt):
                file_path = alt
            else:
                safe_name = secure_filename(pdf.filename)
                alt = os.path.join(upload_root, safe_name) if safe_name else None
                if alt and os.path.exists(alt):
                    file_path = alt
                else:
                    pdf.status = 'error'
                    pdf.error_message = 'PDF file not found. The file may have been moved. Upload the PDF again to process it.'
                    db.session.commit()
                    return jsonify({'error': pdf.error_message}), 404
            pdf.file_path = file_path
            db.session.commit()

        existing_text = ExtractedText.query.filter_by(pdf_id=pdf_id).first()
        format_lines_to_use = None
        if existing_text:
            cleaned_text_to_use = existing_text.cleaned_text
            if existing_text.raw_text:
                format_lines_to_use = [{'text': ln, 'font_size': 12.0, 'is_non_black': False}
                                       for ln in existing_text.raw_text.split('\n') if ln.strip()]
        else:
            result = process_pdf_file_with_format(file_path)
            cleaned_text_to_use = result['cleaned_text']
            format_lines_to_use = result.get('format_lines')
            db.session.add(ExtractedText(
                pdf_id=pdf_id,
                raw_text=result['raw_text'],
                cleaned_text=result['cleaned_text']
            ))
            pdf.language = result['language_code']
            pdf.language_name = result['language_name']

        existing_chunks = Chunk.query.filter_by(pdf_id=pdf_id).first()
        if not existing_chunks:
            if not (cleaned_text_to_use or "").strip():
                msg = 'No text could be extracted from the PDF. The file may be scanned (image-only) or empty.'
                pdf.status = 'error'
                pdf.error_message = msg
                db.session.commit()
                return jsonify({'error': msg, 'message': 'No text extracted'}), 400
            try:
                if format_lines_to_use:
                    chunks_data = analyze_text_in_batches(format_lines=format_lines_to_use)
                else:
                    chunks_data = analyze_text_in_batches(cleaned_text_to_use)
                flat_for_db = []
                pos = 0
                for c in chunks_data:
                    if c.get('segments'):
                        for seg in c['segments']:
                            pos += 1
                            flat_for_db.append({
                                'text': seg['text'],
                                'role': seg['role'],
                                'character_name': seg.get('character_name'),
                                'chunk_type': c.get('chunk_type', 'verse'),
                                'references': c.get('references'),
                                'verse_num': c.get('verse_num') if c.get('chunk_type') == 'verse' else None,
                                'position': pos
                            })
                    else:
                        pos += 1
                        flat_for_db.append({
                            'text': c.get('text') or '',
                            'role': c.get('role', 'narrator'),
                            'character_name': c.get('character_name'),
                            'chunk_type': c.get('chunk_type', 'verse'),
                            'references': c.get('references'),
                            'verse_num': None,
                            'position': pos
                        })
                chunks_to_add = [
                    Chunk(
                        pdf_id=pdf_id,
                        text=cf['text'],
                        role=cf['role'],
                        character_name=cf.get('character_name'),
                        chunk_type=cf.get('chunk_type', 'verse'),
                        references=json.dumps(cf['references']) if cf.get('references') else None,
                        verse_num=cf.get('verse_num'),
                        position=cf['position']
                    )
                    for cf in flat_for_db
                ]
                db.session.add_all(chunks_to_add)
            except Exception as e:
                msg = f'Failed to analyze chunks: {str(e)}'
                pdf.status = 'error'
                pdf.error_message = msg
                db.session.commit()
                traceback.print_exc()
                return jsonify({'error': msg, 'message': str(e)}), 500

        pdf.status = 'completed'
        pdf.error_message = None
        db.session.commit()
        return jsonify({
            'message': 'PDF processed successfully',
            'pdf': pdf.to_dict()
        }), 200
    except Exception as e:
        try:
            pdf.status = 'error'
            pdf.error_message = str(e)
            db.session.commit()
        except Exception:
            db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e), 'message': str(e)}), 500

@bp.route('/pdfs', methods=['GET'])
def list_pdfs():
    pdfs = PDF.query.order_by(PDF.upload_date.desc()).all()
    return jsonify([pdf.to_dict() for pdf in pdfs])


@bp.route('/pdf/<int:pdf_id>/ambient', methods=['GET'])
def list_ambient(pdf_id):
    PDF.query.get_or_404(pdf_id)
    tracks = AmbientTrack.query.filter_by(pdf_id=pdf_id).order_by(AmbientTrack.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tracks])


@bp.route('/pdf/<int:pdf_id>/ambient', methods=['POST'])
def upload_ambient(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    allowed = {'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/m4a', 'audio/x-m4a', 'audio/ogg'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.mp3', '.wav', '.m4a', '.ogg'):
        return jsonify({'error': 'Invalid file type. Use MP3, WAV, M4A or OGG'}), 400
    try:
        ambient_root = os.path.join(os.path.abspath(Config.AUDIO_FOLDER), 'ambient')
        pdf_folder = os.path.join(ambient_root, str(pdf_id))
        os.makedirs(pdf_folder, exist_ok=True)
        name = secure_filename(file.filename) or 'ambient'
        base, _ = os.path.splitext(name)
        path = os.path.join(pdf_folder, name)
        file.save(path)
        track = AmbientTrack(pdf_id=pdf_id, name=base, file_path=path)
        db.session.add(track)
        db.session.commit()
        return jsonify(track.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/pdf/<int:pdf_id>/ambient/selected', methods=['PUT'])
def set_selected_ambient(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    data = request.get_json() or {}
    track_id = data.get('ambient_track_id')
    if track_id is None:
        pdf.selected_ambient_track_id = None
        db.session.commit()
        return jsonify({'selected_ambient_track_id': None})
    track = AmbientTrack.query.filter_by(id=track_id, pdf_id=pdf_id).first()
    if not track:
        return jsonify({'error': 'Ambient track not found for this document'}), 404
    pdf.selected_ambient_track_id = track_id
    db.session.commit()
    return jsonify({'selected_ambient_track_id': track_id})
