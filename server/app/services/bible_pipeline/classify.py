import re
from typing import Any

CHAPTER_NUM_RE = re.compile(r"^Capitolul\s+(\d+)\s*$", re.IGNORECASE)
BIBLE_REF_RE = re.compile(
    r"(?:[1-3]?\s*[A-Za-zăâîșțĂÂÎȘȚ]+\.?\s*\d+(?:\s*[-:]\s*\d+(?::\d+)?)?(?:\s*,\s*\d+(?::\d+)?)*)",
    re.IGNORECASE
)


def _is_uppercase_title(s: str) -> bool:
    if len(s) > 80:
        return False
    letters = [c for c in s if c.isalpha()]
    return len(letters) > 0 and all(c.isupper() or not c.isalpha() for c in s)


def _is_small_font(font_size: float, verse_font: float) -> bool:
    return verse_font > 0 and font_size < verse_font * 0.95


def _looks_like_ref_line(text: str, font_size: float, verse_font: float) -> bool:
    if not _is_small_font(font_size, verse_font):
        return False
    return bool(BIBLE_REF_RE.search(text))


def infer_verse_font_size(lines: list[dict[str, Any]]) -> float:
    sizes = [ln["font_size"] for ln in lines if ln.get("font_size", 0) > 0]
    if not sizes:
        return 12.0
    sizes.sort()
    mid = len(sizes) // 2
    return sizes[mid]


def classify_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not lines:
        return []
    verse_font = infer_verse_font_size(lines)
    result = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        text = (ln.get("text") or "").strip()
        fs = ln.get("font_size") or 0
        if not text:
            i += 1
            continue
        if _is_uppercase_title(text) and fs > verse_font * 1.2:
            result.append({**ln, "line_type": "book_title"})
            i += 1
            continue
        m = CHAPTER_NUM_RE.match(text)
        if m:
            result.append({**ln, "line_type": "chapter_number"})
            i += 1
            if i < len(lines):
                next_ln = lines[i]
                next_text = (next_ln.get("text") or "").strip()
                next_fs = next_ln.get("font_size") or 0
                if next_text and not CHAPTER_NUM_RE.match(next_text) and not _is_uppercase_title(next_text):
                    if _looks_like_ref_line(next_text, next_fs, verse_font):
                        result.append({**next_ln, "line_type": "chapter_reference"})
                    else:
                        result.append({**next_ln, "line_type": "chapter_name"})
                        i += 1
                        if i < len(lines) and _looks_like_ref_line(
                            (lines[i].get("text") or "").strip(),
                            lines[i].get("font_size") or 0,
                            verse_font
                        ):
                            result.append({**lines[i], "line_type": "chapter_reference"})
                            i += 1
                    i += 1
            continue
        if result and result[-1].get("line_type") == "chapter_name" and _looks_like_ref_line(text, fs, verse_font):
            result.append({**ln, "line_type": "chapter_reference"})
            i += 1
            continue
        if (
            (fs >= verse_font * 1.05 or (fs >= verse_font * 0.98 and len(text) <= 30))
            and len(text) < 80
            and not text.endswith(".")
            and not text.endswith(";")
            and not _is_uppercase_title(text)
            and not re.match(r"^\s*\d", text)
            and not BIBLE_REF_RE.fullmatch(text.strip())
        ):
            result.append({**ln, "line_type": "section_title"})
            i += 1
            continue
        if _looks_like_ref_line(text, fs, verse_font) and result and result[-1].get("line_type") in ("verse_text", "verse_reference"):
            result.append({**ln, "line_type": "verse_reference"})
            i += 1
            continue
        result.append({**ln, "line_type": "verse_text"})
        i += 1
    return result
