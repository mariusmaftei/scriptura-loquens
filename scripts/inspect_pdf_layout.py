"""
Extract layout from a PDF and write it to JSON so the structure can be inspected.
Usage: python scripts/inspect_pdf_layout.py <path_to.pdf> [output.json]
Default output: pdf_layout_inspect.json in project root.
"""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "server"))

from app.services.bible_pipeline.extract import extract_layout_lines
from app.services.bible_pipeline.normalize import normalize_reading_order


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect_pdf_layout.py <path_to.pdf> [output.json]", file=sys.stderr)
        sys.exit(1)
    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "pdf_layout_inspect.json"
    raw_lines = extract_layout_lines(str(pdf_path))
    lines = normalize_reading_order(raw_lines)
    out = {
        "pdf_path": str(pdf_path),
        "total_raw_lines": len(raw_lines),
        "total_lines_after_normalize": len(lines),
        "lines": [
            {
                "text": ln.get("text"),
                "font_size": ln.get("font_size"),
                "page_no": ln.get("page_no"),
                "bbox": list(ln["bbox"]) if ln.get("bbox") else None,
            }
            for ln in lines
        ],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(lines)} lines to {out_path}")

if __name__ == "__main__":
    main()
