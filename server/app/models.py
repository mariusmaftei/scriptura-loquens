import json
from app.database import db
from datetime import datetime


class AmbientTrack(db.Model):
    __tablename__ = 'ambient_tracks'

    __table_args__ = (db.Index('ix_ambient_tracks_pdf_id', 'pdf_id'),)

    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.Integer, db.ForeignKey('pdfs.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'pdf_id': self.pdf_id,
            'name': self.name,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PDF(db.Model):
    __tablename__ = 'pdfs'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_hash = db.Column(db.String(64), unique=True, nullable=False)
    language = db.Column(db.String(10))
    language_name = db.Column(db.String(50))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    selected_ambient_track_id = db.Column(db.Integer, nullable=True)
    custom_narrator_name = db.Column(db.String(255), nullable=True)
    custom_voice_actor_name = db.Column(db.String(255), nullable=True)
    use_ai = db.Column(db.Boolean, default=False, nullable=False)
    pipeline = db.Column(db.String(20), default='bible', nullable=False)
    book_key = db.Column(db.String(120), nullable=True)
    book_display_name = db.Column(db.String(255), nullable=True)
    book_author = db.Column(db.String(255), nullable=True)
    book_genre = db.Column(db.String(80), nullable=True)
    book_cover_path = db.Column(db.String(500), nullable=True)

    extracted_texts = db.relationship('ExtractedText', backref='pdf', cascade='all, delete-orphan')
    chunks = db.relationship('Chunk', backref='pdf', cascade='all, delete-orphan')
    voice_settings = db.relationship('VoiceSetting', backref='pdf', cascade='all, delete-orphan')
    ambient_tracks = db.relationship('AmbientTrack', backref='pdf', cascade='all, delete-orphan', foreign_keys='AmbientTrack.pdf_id')
    selected_ambient_track = db.relationship('AmbientTrack', primaryjoin='PDF.selected_ambient_track_id == AmbientTrack.id', foreign_keys='AmbientTrack.id', viewonly=True)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_hash': self.file_hash,
            'language': self.language,
            'language_name': self.language_name,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'status': self.status,
            'error_message': self.error_message,
            'file_path': self.file_path,
            'selected_ambient_track_id': self.selected_ambient_track_id,
            'custom_narrator_name': self.custom_narrator_name,
            'custom_voice_actor_name': self.custom_voice_actor_name,
            'use_ai': self.use_ai,
            'pipeline': getattr(self, 'pipeline', 'bible') or 'bible',
            'book_key': getattr(self, 'book_key', None),
            'book_display_name': getattr(self, 'book_display_name', None),
            'book_author': getattr(self, 'book_author', None),
            'book_genre': getattr(self, 'book_genre', None),
            'book_cover_path': getattr(self, 'book_cover_path', None),
        }

class ExtractedText(db.Model):
    __tablename__ = 'extracted_text'

    __table_args__ = (db.Index('ix_extracted_text_pdf_id', 'pdf_id'),)

    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.Integer, db.ForeignKey('pdfs.id'), nullable=False)
    raw_text = db.Column(db.Text)
    cleaned_text = db.Column(db.Text, nullable=False)
    extraction_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'pdf_id': self.pdf_id,
            'raw_text': self.raw_text,
            'cleaned_text': self.cleaned_text,
            'extraction_date': self.extraction_date.isoformat() if self.extraction_date else None
        }

class Chunk(db.Model):
    __tablename__ = 'chunks'

    __table_args__ = (db.Index('ix_chunks_pdf_position', 'pdf_id', 'position'),)

    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.Integer, db.ForeignKey('pdfs.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    character_name = db.Column(db.String(100))
    chunk_type = db.Column(db.String(30), default='verse')  # 'book_title', 'chapter_number', 'chapter_name', 'verse', 'section_title'
    references = db.Column(db.Text)  # JSON string array of verse references: ["Ioan 1:1", "Evr. 1:10", "Ps. 8:3"]
    verse_num = db.Column(db.String(20))  # e.g. "3" for verse 3; segments of same verse share this
    position = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    audio_files = db.relationship('AudioFile', backref='chunk', cascade='all, delete-orphan')
    
    def to_dict(self):
        refs = []
        if self.references:
            try:
                refs = json.loads(self.references)
            except:
                pass
        return {
            'id': self.id,
            'pdf_id': self.pdf_id,
            'text': self.text,
            'role': self.role,
            'character_name': self.character_name,
            'chunk_type': self.chunk_type,
            'references': refs,
            'verse_num': self.verse_num,
            'position': self.position,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VoiceSetting(db.Model):
    __tablename__ = 'voice_settings'

    __table_args__ = (
        db.UniqueConstraint('pdf_id', 'role', 'character_name', name='unique_voice_setting'),
        db.Index('ix_voice_settings_pdf_role_char', 'pdf_id', 'role', 'character_name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    pdf_id = db.Column(db.Integer, db.ForeignKey('pdfs.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    character_name = db.Column(db.String(100))
    language_code = db.Column(db.String(10), nullable=False)
    voice_id = db.Column(db.String(100), nullable=False)
    voice_name = db.Column(db.String(200))
    speed = db.Column(db.Float, default=1.0)
    pitch = db.Column(db.Float, default=0.0)
    volume = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'pdf_id': self.pdf_id,
            'role': self.role,
            'character_name': self.character_name,
            'language_code': self.language_code,
            'voice_id': self.voice_id,
            'voice_name': self.voice_name,
            'speed': self.speed,
            'pitch': self.pitch,
            'volume': self.volume,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AudioFile(db.Model):
    __tablename__ = 'audio_files'

    __table_args__ = (
        db.Index('ix_audio_files_chunk_voice', 'chunk_id', 'voice_id'),
        db.Index('ix_audio_files_chunk_hash', 'chunk_id', 'voice_settings_hash'),
    )

    id = db.Column(db.Integer, primary_key=True)
    chunk_id = db.Column(db.Integer, db.ForeignKey('chunks.id'), nullable=False)
    audio_path = db.Column(db.String(500), nullable=False)
    voice_id = db.Column(db.String(100), nullable=False)
    voice_settings_hash = db.Column(db.String(64))
    duration = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'chunk_id': self.chunk_id,
            'audio_path': self.audio_path,
            'voice_id': self.voice_id,
            'voice_settings_hash': self.voice_settings_hash,
            'duration': self.duration,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
