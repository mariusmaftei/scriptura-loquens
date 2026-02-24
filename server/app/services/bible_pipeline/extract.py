import fitz
from typing import TypedDict


class LayoutLine(TypedDict):
    text: str
    font_size: float
    bbox: tuple[float, float, float, float]
    page_width: float
    page_no: int


def extract_layout_lines(pdf_path: str) -> list[LayoutLine]:
    lines: list[LayoutLine] = []
    doc = fitz.open(pdf_path)
    for page_no in range(len(doc)):
        page = doc[page_no]
        page_width = page.rect.width
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                parts = []
                font_size = 0.0
                bbox = line.get("bbox", (0, 0, 0, 0))
                for s in spans:
                    parts.append(s.get("text", ""))
                    fs = s.get("size", 0)
                    if fs > font_size:
                        font_size = fs
                text = "".join(parts).strip()
                if not text:
                    continue
                lines.append({
                    "text": text,
                    "font_size": round(font_size, 1),
                    "bbox": tuple(bbox),
                    "page_width": page_width,
                    "page_no": page_no + 1,
                })
    doc.close()
    return lines
