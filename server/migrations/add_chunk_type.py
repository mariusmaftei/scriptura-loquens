"""
Migration script to add chunk_type column to chunks table.
Run this script to update existing databases.
"""
import sqlite3
import os
from pathlib import Path

def migrate_database(db_path):
    """Add chunk_type column to chunks table if it doesn't exist."""
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(chunks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'chunk_type' not in columns:
            print("Adding chunk_type column to chunks table...")
            cursor.execute("ALTER TABLE chunks ADD COLUMN chunk_type VARCHAR(30) DEFAULT 'verse'")
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("chunk_type column already exists. No migration needed.")
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "instance" / "scriptura_loquens.db"
    
    if not db_path.exists():
        db_path = script_dir.parent / "scriptura_loquens.db"
    
    if db_path.exists():
        migrate_database(str(db_path))
    else:
        print(f"Database not found. Please specify the database path.")
        print("Usage: python add_chunk_type.py <path_to_database>")
