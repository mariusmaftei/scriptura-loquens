from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from flask import current_app

db = SQLAlchemy()

def init_db():
    db.create_all()
    _migrate_chunk_type_column()
    _migrate_pdf_use_ai()
    _migrate_chunk_verse_num()
    _migrate_pdf_ambient_column()
    _migrate_pdf_custom_voice_names()
    _migrate_add_indexes()

def _migrate_chunk_type_column():
    """Add chunk_type and references columns to chunks table if they don't exist."""
    try:
        inspector = inspect(db.engine)
        if inspector.has_table('chunks'):
            columns = [col['name'] for col in inspector.get_columns('chunks')]
            
            if 'chunk_type' not in columns:
                current_app.logger.info("Adding chunk_type column to chunks table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE chunks ADD COLUMN chunk_type VARCHAR(30) DEFAULT 'verse'"))
                    conn.commit()
                current_app.logger.info("Migration completed: chunk_type column added")
            
            if 'references' not in columns:
                current_app.logger.info("Adding references column to chunks table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE chunks ADD COLUMN references TEXT"))
                    conn.commit()
                current_app.logger.info("Migration completed: references column added")
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Could not migrate chunks table: {e}. This is OK if the columns already exist.")
        else:
            print(f"Warning: Could not migrate chunks table: {e}")


def _migrate_chunk_verse_num():
    """Add verse_num column to chunks table if it doesn't exist."""
    try:
        inspector = inspect(db.engine)
        if inspector.has_table('chunks'):
            columns = [col['name'] for col in inspector.get_columns('chunks')]
            if 'verse_num' not in columns:
                current_app.logger.info("Adding verse_num column to chunks table...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE chunks ADD COLUMN verse_num VARCHAR(20)"))
                    conn.commit()
                current_app.logger.info("Migration completed: verse_num column added")
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Could not migrate chunks table: {e}. This is OK if the columns already exist.")
        else:
            print(f"Warning: Could not migrate chunks table: {e}")


def _migrate_pdf_ambient_column():
    """Add selected_ambient_track_id to pdfs table if it doesn't exist."""
    try:
        inspector = inspect(db.engine)
        if inspector.has_table('pdfs'):
            columns = [col['name'] for col in inspector.get_columns('pdfs')]
            if 'selected_ambient_track_id' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE pdfs ADD COLUMN selected_ambient_track_id INTEGER"))
                    conn.commit()
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Could not migrate pdfs ambient column: {e}")
        else:
            print(f"Warning: Could not migrate pdfs ambient column: {e}")


def _migrate_pdf_custom_voice_names():
    """Add custom_narrator_name and custom_voice_actor_name to pdfs if missing."""
    try:
        inspector = inspect(db.engine)
        if inspector.has_table('pdfs'):
            columns = [col['name'] for col in inspector.get_columns('pdfs')]
            with db.engine.connect() as conn:
                if 'custom_narrator_name' not in columns:
                    conn.execute(text("ALTER TABLE pdfs ADD COLUMN custom_narrator_name VARCHAR(255)"))
                    conn.commit()
                if 'custom_voice_actor_name' not in columns:
                    conn.execute(text("ALTER TABLE pdfs ADD COLUMN custom_voice_actor_name VARCHAR(255)"))
                    conn.commit()
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Could not migrate pdfs custom voice names: {e}")
        else:
            print(f"Warning: Could not migrate pdfs custom voice names: {e}")


def _migrate_pdf_use_ai():
    """Add use_ai to pdfs table if it doesn't exist."""
    try:
        inspector = inspect(db.engine)
        if inspector.has_table('pdfs'):
            columns = [col['name'] for col in inspector.get_columns('pdfs')]
            if 'use_ai' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE pdfs ADD COLUMN use_ai BOOLEAN DEFAULT 0"))
                    conn.commit()
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Could not migrate pdfs use_ai: {e}")
        else:
            print(f"Warning: Could not migrate pdfs use_ai: {e}")


def _migrate_add_indexes():
    indexes = [
        ('extracted_text', 'ix_extracted_text_pdf_id', ['pdf_id']),
        ('chunks', 'ix_chunks_pdf_position', ['pdf_id', 'position']),
        ('ambient_tracks', 'ix_ambient_tracks_pdf_id', ['pdf_id']),
        ('voice_settings', 'ix_voice_settings_pdf_role_char', ['pdf_id', 'role', 'character_name']),
        ('audio_files', 'ix_audio_files_chunk_voice', ['chunk_id', 'voice_id']),
        ('audio_files', 'ix_audio_files_chunk_hash', ['chunk_id', 'voice_settings_hash']),
    ]
    try:
        inspector = inspect(db.engine)
        for table, idx_name, cols in indexes:
            if not inspector.has_table(table):
                continue
            existing = [i['name'] for i in inspector.get_indexes(table)]
            if idx_name in existing:
                continue
            col_str = ', '.join(cols)
            with db.engine.connect() as conn:
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({col_str})"))
                conn.commit()
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Could not add indexes: {e}")
        else:
            print(f"Warning: Could not add indexes: {e}")
