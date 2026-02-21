import re

VERSE_REF = re.compile(
    r"(?:[A-Za-z\u0100-\u024f]{2,4}\.?\s*\d+:\d+(?:\s*,\s*\d+)*\s*[;,]?\s*)+",
    re.IGNORECASE
)
REF_BLOCK = re.compile(
    r"[\s*_**†]*(?:[A-Za-z\u0100-\u024f]{2,4}\.?\s*\d+(?:\s*:\s*\d+(?:\s*,\s*\d+)*)?(?:\s*[-–]\s*[A-Za-z\u0100-\u024f]{2,4}\.?\s*\d+(?:\s*:\s*\d+)?)?(?:\s*[;,.]\s*(?:[A-Za-z\u0100-\u024f]{2,4}\.?\s*\d+(?:\s*:\s*\d+(?:\s*,\s*\d+)*)?)*)*)\s*[*_**†\s]*",
    re.IGNORECASE
)

def _remove_verse_reference_lines(text):
    """Remove lines that are Bible verse references (e.g. Ioan 1:1, 2; Ps. 8:3; Evr. 1:10)."""
    if not text:
        return ""
    lines = text.split("\n")
    out = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            out.append(line)
            continue
        if re.match(r"^[\s\-*\\_†]+$", stripped):
            continue
        if VERSE_REF.search(stripped):
            ref_part = "".join(VERSE_REF.findall(stripped))
            if len(ref_part) >= len(stripped) * 0.4:
                continue
        stripped = REF_BLOCK.sub(" ", stripped)
        stripped = re.sub(r"\s*[*_**†]+\s*", " ", stripped)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        if stripped:
            out.append(stripped)
    return "\n".join(out)


def _strip_footnote_markers(text):
    """Remove footnote/reference markers (\\*, \\**, †, _) so they are not read aloud."""
    if not text:
        return ""
    t = text
    t = re.sub(r"\\\*\\\*", " ", t)
    t = re.sub(r"\\\*", " ", t)
    t = re.sub(r"\*\*(?=\s|$)", " ", t)
    t = re.sub(r"\*(?=\s|$)", " ", t)
    t = re.sub(r"†(?=\s|$)", " ", t)
    t = re.sub(r"_(?=\s|$)", " ", t)
    return t


def clean_text(text):
    if not text:
        return ""

    cleaned = text
    cleaned = _remove_verse_reference_lines(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"^\s+|\s+$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"Page \d+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\d{1,2}/\d{1,2}/\d{4}", "", cleaned)
    cleaned = re.sub(r"^\d+$", "", cleaned, flags=re.MULTILINE)
    cleaned = _strip_footnote_markers(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()
    return cleaned


def normalize_whitespace(text):
    if not text:
        return ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()
