import os
from app.services.bible_pipeline.extract import extract_layout_lines
from app.services.bible_pipeline.normalize import normalize_reading_order
from app.services.bible_pipeline.run import lines_to_format_lines

_LANG_NAMES = {"ro": "Romanian", "en": "English", "fr": "French", "de": "German", "es": "Spanish", "it": "Italian"}


def detect_pdf_language(pdf_path: str) -> dict:
    out = process_pdf_file_with_format(pdf_path)
    text = (out.get("cleaned_text") or "")[:5000]
    if not text.strip():
        return {"language_code": "ro", "language_name": "Romanian"}
    try:
        from langdetect import detect
        code = detect(text)
        return {
            "language_code": code,
            "language_name": _LANG_NAMES.get(code, code),
        }
    except Exception:
        return {"language_code": "ro", "language_name": "Romanian"}


def process_pdf_file_with_format(pdf_path: str) -> dict:
    if not os.path.exists(pdf_path):
        return {"raw_text": "", "cleaned_text": "", "format_lines": [], "language_code": "ro", "language_name": "Romanian"}
    raw_lines = extract_layout_lines(pdf_path)
    lines = normalize_reading_order(raw_lines)
    format_lines = lines_to_format_lines(lines)
    raw_text = "\n".join((ln.get("text") or "").strip() for ln in lines)
    cleaned_text = raw_text.strip()
    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "format_lines": format_lines,
        "language_code": "ro",
        "language_name": "Romanian",
    }


def process_pdf_file(pdf_path: str) -> dict:
    out = process_pdf_file_with_format(pdf_path)
    return {
        "raw_text": out["raw_text"],
        "cleaned_text": out["cleaned_text"],
        "language_code": out["language_code"],
        "language_name": out["language_name"],
    }
