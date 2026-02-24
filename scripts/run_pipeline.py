"""Run PDF -> original-text.json pipeline. Usage: python scripts/run_pipeline.py <pdf_path> [output.json]"""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "server"))

from app.services.bible_pipeline import run, run_to_json

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_pipeline.py <pdf_path> [output.json]", file=sys.stderr)
        sys.exit(1)
    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else pdf_path.with_suffix(".json")
    run_to_json(str(pdf_path), str(out_path))
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
