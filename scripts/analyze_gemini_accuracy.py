"""Analyze Gemini output (results.json) and compute accuracy metrics."""

import json
import re
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

def load_results(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze(data):
    chunks = data.get("chunks", [])
    format_lines = data.get("format_lines", [])
    issues = []
    scores = {"total": 0, "passed": 0}

    verse_chunks = [c for c in chunks if c.get("chunk_type") == "verse"]
    verse_nums_in_format = set()
    for line in format_lines:
        m = re.match(r"^(\d+)\.\s*$", (line.get("text") or "").strip())
        if m:
            verse_nums_in_format.add(m.group(1))

    verse_num_missing = sum(1 for c in verse_chunks if not c.get("verse_num"))
    verse_num_ok = len(verse_chunks) - verse_num_missing

    segment_order_errors = 0
    footnote_as_section = 0
    wrong_narrator_char_order = 0

    for i, c in enumerate(chunks):
        ctype = c.get("chunk_type", "")
        segs = c.get("segments", [])

        if ctype == "section_title" and segs:
            txt = (segs[0].get("text") or "").strip()
            if re.match(r"^[\wăâîşț]+\*.*\*", txt) or "*" in txt[:30]:
                footnote_as_section += 1
                issues.append(f"Pos {c.get('position')}: Footnote key '{txt[:50]}...' misclassified as section_title")

        if ctype == "verse" and len(segs) > 1:
            roles = [s.get("role") for s in segs]
            if "character" in roles:
                first_char_idx = next((j for j, r in enumerate(roles) if r == "character"), -1)
                if first_char_idx == 0:
                    wrong_narrator_char_order += 1
                    issues.append(f"Pos {c.get('position')}: Character first - narrator intro should come before quote")
                elif first_char_idx > 0:
                    before = roles[:first_char_idx]
                    if "narrator" not in before:
                        wrong_narrator_char_order += 1
                        issues.append(f"Pos {c.get('position')}: Character segment before narrator intro - order wrong")
                narrator_after = [r for j, r in enumerate(roles) if j > first_char_idx and r == "narrator"]
                char_after = [r for j, r in enumerate(roles) if j > first_char_idx and r == "character"]
                if char_after and narrator_after and roles.index("character", first_char_idx + 1) < max(
                    j for j, r in enumerate(roles) if r == "narrator" and j > first_char_idx
                ):
                    pass

    total_checks = (
        len(verse_chunks) + 1 +
        sum(1 for c in chunks if c.get("chunk_type") == "section_title") +
        sum(1 for c in verse_chunks if len(c.get("segments", [])) > 1)
    )
    passed = (
        verse_num_ok +
        (1 if footnote_as_section == 0 else 0) +
        (len([c for c in verse_chunks if len(c.get("segments", [])) > 1]) - wrong_narrator_char_order)
    )

    report = {
        "summary": {
            "total_chunks": len(chunks),
            "verse_chunks": len(verse_chunks),
            "verse_num_missing": verse_num_missing,
            "verse_num_ok": verse_num_ok,
            "footnote_misclassified": footnote_as_section,
            "segment_order_errors": wrong_narrator_char_order,
        },
        "scores": {
            "verse_num_accuracy": round(100 * verse_num_ok / len(verse_chunks), 1) if verse_chunks else 100,
            "chunk_type_accuracy": round(100 * (len(chunks) - footnote_as_section) / len(chunks), 1) if chunks else 100,
            "overall_estimate": None,
        },
        "issues": issues[:30],
    }

    verse_score = 100 * verse_num_ok / len(verse_chunks) if verse_chunks else 100
    chunk_score = 100 * (len(chunks) - footnote_as_section) / len(chunks) if chunks else 100
    seg_count = sum(1 for c in verse_chunks if len(c.get("segments", [])) > 1)
    seg_score = 100 * (seg_count - wrong_narrator_char_order) / seg_count if seg_count else 100
    report["scores"]["segment_order_accuracy"] = round(seg_score, 1)
    report["scores"]["overall_estimate"] = round(
        (verse_score * 0.3 + chunk_score * 0.4 + seg_score * 0.3), 1
    )

    return report

def main():
    base = Path(__file__).resolve().parent.parent
    path = base / "results.json"
    out_path = None
    args = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "-o" and i + 1 < len(sys.argv):
            out_path = Path(sys.argv[i + 1])
            i += 2
        elif not sys.argv[i].startswith("-"):
            args.append(sys.argv[i])
            i += 1
        else:
            i += 1
    if args:
        path = Path(args[0])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    data = load_results(path)
    report = analyze(data)

    print("=" * 60)
    print("GEMINI OUTPUT ACCURACY ANALYSIS")
    print("=" * 60)
    print(f"\nFile: {path.name}")
    print(f"\n--- SUMMARY ---")
    for k, v in report["summary"].items():
        print(f"  {k}: {v}")
    print(f"\n--- SCORES ---")
    for k, v in report["scores"].items():
        if v is not None:
            print(f"  {k}: {v}%")
    print(f"\n--- ISSUES (first 30) ---")
    for msg in report["issues"]:
        print(f"  - {msg}")
    if not report["issues"]:
        print("  None")
    print("\n--- INTERPRETATION ---")
    print("  verse_num_accuracy: Verse numbers (1, 2, 3...) detected for verse chunks")
    print("  chunk_type_accuracy: book_title, chapter_number, verse, section_title correct")
    print("  segment_order_accuracy: Narrator intro before character quote in segmented verses")
    print("\n" + "=" * 60)

    if report["scores"].get("overall_estimate"):
        print(f"\n  OVERALL ACCURACY SCORE: {report['scores']['overall_estimate']}%")
        print("  (Weighted: verse_num 30%, chunk_type 40%, segment_order 30%)")

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to: {out_path}")

if __name__ == "__main__":
    main()
