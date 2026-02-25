from flask import Blueprint, request, jsonify
from app.database import db
from app.models import PDF, Chunk, ExtractedText, VoiceSetting
from app.services.gemini_service import analyze_text_in_batches
from app.services.tts_service import normalize_character_name_for_voice
import json

bp = Blueprint('chunks', __name__)

@bp.route('/pdf/<int:pdf_id>/chunks', methods=['GET'])
def get_chunks(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    chunks = Chunk.query.filter_by(pdf_id=pdf_id).order_by(Chunk.position).all()
    return jsonify([chunk.to_dict() for chunk in chunks])

@bp.route('/pdf/<int:pdf_id>/characters', methods=['GET'])
def get_characters(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    chunks = Chunk.query.filter_by(pdf_id=pdf_id).all()
    characters = []
    seen = set()
    for chunk in chunks:
        if chunk.role == 'narrator':
            key = 'narrator'
            display_name = None
        else:
            display_name = normalize_character_name_for_voice(chunk.character_name) or chunk.character_name
            key = f"{chunk.role}_{display_name or 'unknown'}"
        if key not in seen:
            seen.add(key)
            characters.append({
                'role': chunk.role,
                'character_name': display_name if chunk.role != 'narrator' else chunk.character_name
            })
    return jsonify(characters)

@bp.route('/pdf/<int:pdf_id>/analyze', methods=['POST'])
def analyze_pdf(pdf_id):
    pdf = PDF.query.get_or_404(pdf_id)
    
    existing_chunks = Chunk.query.filter_by(pdf_id=pdf_id).first()
    if existing_chunks:
        chunks = Chunk.query.filter_by(pdf_id=pdf_id).order_by(Chunk.position).all()
        return jsonify([chunk.to_dict() for chunk in chunks]), 200
    
    extracted_text = ExtractedText.query.filter_by(pdf_id=pdf_id).first()
    if not extracted_text:
        return jsonify({'error': 'Text not extracted. Process PDF first'}), 400
    
    try:
        chunks_data = analyze_text_in_batches(extracted_text.cleaned_text)
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
        chunks_to_add = [Chunk(
            pdf_id=pdf_id,
            text=cf['text'],
            role=cf['role'],
            character_name=cf.get('character_name'),
            chunk_type=cf.get('chunk_type', 'verse'),
            references=json.dumps(cf['references']) if cf.get('references') else None,
            verse_num=cf.get('verse_num'),
            position=cf['position']
        ) for cf in flat_for_db]
        db.session.add_all(chunks_to_add)
        
        db.session.commit()
        
        chunks = Chunk.query.filter_by(pdf_id=pdf_id).order_by(Chunk.position).all()
        return jsonify([chunk.to_dict() for chunk in chunks]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
