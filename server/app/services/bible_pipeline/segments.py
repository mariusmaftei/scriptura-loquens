import re
from typing import Optional

RO_OPEN = "\u201e"
RO_CLOSE = "\u201d"
SPEAKER_RE = re.compile(r"^(.+?)\s+a\s+zis\s*:\s*$", re.IGNORECASE)


def segment_verse_text(text: str, default_speaker: Optional[str] = None) -> list[dict]:
    if not text or not text.strip():
        return [{"role": "narrator", "character_name": None, "text": text or ""}]
    parts = []
    current = []
    i = 0
    while i < len(text):
        if text[i] == RO_OPEN:
            if current:
                parts.append(("narrator", "".join(current).strip()))
                current = []
            i += 1
            end = text.find(RO_CLOSE, i)
            if end == -1:
                end = len(text)
            parts.append(("character", text[i:end].strip()))
            i = end + 1 if end < len(text) else len(text)
            continue
        current.append(text[i])
        i += 1
    if current:
        parts.append(("narrator", "".join(current).strip()))
    speaker = default_speaker
    out = []
    for role, part in parts:
        if not part:
            continue
        if role == "character" and not speaker:
            for r, p in parts:
                if r == "narrator":
                    m = SPEAKER_RE.match(p)
                    if m:
                        speaker = m.group(1).strip()
                        break
        out.append({
            "role": role,
            "character_name": speaker if role == "character" else None,
            "text": part,
        })
    return out if out else [{"role": "narrator", "character_name": None, "text": text}]
