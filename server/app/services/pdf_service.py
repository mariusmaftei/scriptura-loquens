import os
import re
import pdfplumber
from langdetect import detect, LangDetectException

VERSE_START = re.compile(r'^(\d+)\.\s+')
from app.utils.text_cleaner import clean_text, normalize_whitespace
from app.utils.file_handler import generate_file_hash
from flask import current_app

def _is_black_color(c):
    if c is None:
        return True
    if isinstance(c, (int, float)):
        return c == 0
    if isinstance(c, (list, tuple)):
        if len(c) >= 3:
            return all(float(x) < 0.01 for x in c[:3])
        return True
    return True

def _extract_lines_with_format(file_path, max_pages):
    lines = []
    with pdfplumber.open(file_path) as pdf:
        for p in pdf.pages[:max_pages]:
            words = []
            try:
                words = p.extract_words() or []
            except Exception:
                pass
            if not words:
                chars = getattr(p, 'chars', None) or []
                if not chars:
                    text = p.extract_text()
                    if text:
                        for ln in text.split('\n'):
                            if ln.strip():
                                lines.append({'text': ln.strip(), 'font_size': 12.0, 'is_non_black': False})
                    continue
                by_top = {}
                line_tolerance = 2.0
                for c in chars:
                    top = float(c.get('top', c.get('y0', 0)))
                    x0 = c.get('x0', 0)
                    band = round(top / line_tolerance) * line_tolerance
                    by_top.setdefault(band, []).append((x0, c))
                for top in sorted(by_top.keys()):
                    segs = sorted(by_top[top], key=lambda x: x[0])
                    line_text = ''.join(s[1].get('text', '') for s in segs)
                    if not line_text.strip():
                        continue
                    sizes = [float(s[1].get('size', 12)) for s in segs]
                    dom_size = max(set(sizes), key=sizes.count) if sizes else 12.0
                    any_non_black = any(not _is_black_color(s[1].get('non_stroking_color')) for s in segs)
                    lines.append({'text': line_text, 'font_size': dom_size, 'is_non_black': any_non_black})
                continue
            by_top = {}
            line_tolerance = 3.0
            for w in words:
                t = w.get('text', '').strip()
                if not t:
                    continue
                top = float(w.get('top', w.get('y0', 0)))
                x0 = w.get('x0', 0)
                band = round(top / line_tolerance) * line_tolerance
                by_top.setdefault(band, []).append((x0, w))
            for top in sorted(by_top.keys()):
                segs = sorted(by_top[top], key=lambda x: x[0])
                line_text = ' '.join(s[1].get('text', '') for s in segs)
                if not line_text.strip():
                    continue
                heights = [float(s[1].get('bottom', 0)) - float(s[1].get('top', 0)) for s in segs]
                dom_size = max(set(heights), key=heights.count) if heights else 12.0
                lines.append({'text': line_text.strip(), 'font_size': dom_size, 'is_non_black': False})
    return lines

LANGUAGE_NAMES = {
    'en': 'English',
    'ro': 'Romanian',
    'de': 'German',
    'fr': 'French',
    'es': 'Spanish',
    'it': 'Italian',
    'pt': 'Portuguese'
}

def detect_pdf_language(text):
    if not text or len(text) < 100:
        return 'en', 'English'
    
    text_sample = text[:2000] if len(text) > 2000 else text
    
    try:
        lang_code = detect(text_sample)
        lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
        return lang_code, lang_name
    except LangDetectException:
        return 'en', 'English'

def extract_text_from_pdf(file_path):
    try:
        max_pages = 5
        if current_app:
            max_pages = int(current_app.config.get('MAX_PDF_PAGES', 5))
        max_pages = max(1, min(max_pages, 999))
        raw_text = ""
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_process = min(max_pages, total_pages)
            for i in range(pages_to_process):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    raw_text += page_text + "\n"
        cleaned_text = clean_text(raw_text)
        cleaned_text = normalize_whitespace(cleaned_text)
        if total_pages > max_pages:
            raw_text += f"\n[Truncated: first {pages_to_process} of {total_pages} pages only (MAX_PDF_PAGES={max_pages}).]"
        return raw_text, cleaned_text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def _add_verse_nums_to_lines(lines):
    current_verse_num = None
    for line in lines:
        t = (line.get('text') or '').strip()
        m = VERSE_START.match(t)
        if m:
            current_verse_num = m.group(1)
        line['verse_num'] = current_verse_num

def extract_text_with_formatting(file_path):
    try:
        max_pages = 5
        if current_app:
            max_pages = int(current_app.config.get('MAX_PDF_PAGES', 5))
        max_pages = max(1, min(max_pages, 999))
        lines = _extract_lines_with_format(file_path, max_pages)
        _add_verse_nums_to_lines(lines)
        raw_text = '\n'.join(l['text'] for l in lines)
        cleaned = clean_text(raw_text)
        cleaned = normalize_whitespace(cleaned)
        return {'raw_text': raw_text, 'cleaned_text': cleaned, 'format_lines': lines}
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def process_pdf_file(file_path):
    file_hash = generate_file_hash(file_path)
    raw_text, cleaned_text = extract_text_from_pdf(file_path)
    language_code, language_name = detect_pdf_language(cleaned_text)
    return {
        'file_hash': file_hash,
        'raw_text': raw_text,
        'cleaned_text': cleaned_text,
        'language_code': language_code,
        'language_name': language_name
    }

def process_pdf_file_with_format(file_path):
    file_hash = generate_file_hash(file_path)
    data = extract_text_with_formatting(file_path)
    raw_text = data['raw_text']
    cleaned_text = data['cleaned_text']
    format_lines = data.get('format_lines') or []
    language_code, language_name = detect_pdf_language(cleaned_text)
    return {
        'file_hash': file_hash,
        'raw_text': raw_text,
        'cleaned_text': cleaned_text,
        'format_lines': format_lines,
        'language_code': language_code,
        'language_name': language_name
    }
