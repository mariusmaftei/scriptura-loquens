"""Test pipeline_v2 with format_lines from results.json."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "server"))
from app.services.pipeline_v2 import run

def main():
    base = Path(__file__).resolve().parent.parent
    path = base / "results.json"
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    fl = data.get("format_lines") or []
    if not fl:
        print("No format_lines in file")
        return
    chunks = run(fl)
    out = {"chunks": chunks, "filename": data.get("filename"), "format_lines": fl[:5]}
    out_path = base / "results_v2.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(chunks)} chunks to {out_path}")

if __name__ == "__main__":
    main()
