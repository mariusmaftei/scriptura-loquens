import re
from typing import Any


PAGE_NUM_RE = re.compile(r"^\s*\d+\s*$")


def normalize_reading_order(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for ln in lines:
        text = (ln.get("text") or "").strip()
        if not text:
            continue
        if PAGE_NUM_RE.match(text) and len(text) < 5:
            continue
        out.append({
            "text": text,
            "font_size": ln.get("font_size", 0),
            "bbox": ln.get("bbox"),
            "page_width": ln.get("page_width"),
            "page_no": ln.get("page_no"),
        })
    return out
