import os
import hashlib
from werkzeug.utils import secure_filename
from flask import current_app

def generate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_uploaded_file(file, folder):
    folder = os.path.abspath(folder)
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = secure_filename(file.filename) or "upload.pdf"
    file_path = os.path.join(folder, filename)
    file.save(file_path)
    return file_path

def get_file_hash_from_content(content):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
