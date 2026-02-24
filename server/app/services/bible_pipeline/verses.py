import re
from typing import Any

VERSE_NUM_ONLY_RE = re.compile(r"^\s*(\d+)\s*\.?\s*$")
VERSE_NUM_PREFIX_RE = re.compile(r"^\s*(\d+)\s*\.\s*(.*)$", re.DOTALL)
FOOTNOTE_RE = re.compile(r"^[\*\†\s]+")


def _strip_footnote(s: str) -> str:
    return FOOTNOTE_RE.sub("", s).strip()


def collect_verse_blocks(classified: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks = []
    i = 0
    while i < len(classified):
        ln = classified[i]
        line_type = ln.get("line_type", "verse_text")
        text = (ln.get("text") or "").strip()

        if line_type in ("book_title", "chapter_number", "section_title"):
            blocks.append({"block_type": line_type, "lines": [ln], "references": None})
            i += 1
            continue
        if line_type == "chapter_name":
            blocks.append({"block_type": "chapter_name", "lines": [ln], "references": None})
            i += 1
            if i < len(classified) and classified[i].get("line_type") == "chapter_reference":
                blocks[-1]["references"] = (classified[i].get("text") or "").strip()
                i += 1
            continue
        if line_type == "chapter_reference":
            if blocks and blocks[-1].get("block_type") == "chapter_name":
                blocks[-1]["references"] = text
            i += 1
            continue
        if line_type == "verse_reference":
            if blocks and blocks[-1].get("block_type") == "verse":
                prev_ref = blocks[-1].get("references") or ""
                blocks[-1]["references"] = (prev_ref + " " + text).strip() if prev_ref else text
            i += 1
            continue

        if line_type != "verse_text":
            i += 1
            continue

        verse_lines = []
        verse_num = None
        ref_after = None
        while i < len(classified):
            cur = classified[i]
            lt = cur.get("line_type", "verse_text")
            if lt in ("book_title", "chapter_number", "chapter_name", "chapter_reference", "section_title"):
                if verse_lines or verse_num is not None:
                    blocks.append({
                        "block_type": "verse",
                        "lines": verse_lines,
                        "verse_num": verse_num,
                        "references": ref_after,
                    })
                break
            if lt == "verse_reference":
                ref_after = (cur.get("text") or "").strip()
                if verse_lines or verse_num is not None:
                    blocks.append({
                        "block_type": "verse",
                        "lines": verse_lines,
                        "verse_num": verse_num,
                        "references": ref_after,
                    })
                i += 1
                break
            t = (cur.get("text") or "").strip()
            only_num = VERSE_NUM_ONLY_RE.match(t)
            if only_num:
                num = only_num.group(1)
                if verse_lines or verse_num is not None:
                    blocks.append({
                        "block_type": "verse",
                        "lines": verse_lines,
                        "verse_num": verse_num,
                        "references": ref_after,
                    })
                    ref_after = None
                verse_num = num
                verse_lines = []
                i += 1
                if i < len(classified) and classified[i].get("line_type") == "verse_text":
                    verse_lines.append(classified[i])
                    i += 1
                continue
            prefix = VERSE_NUM_PREFIX_RE.match(t)
            if prefix:
                num, rest = prefix.group(1), prefix.group(2).strip()
                if verse_lines or verse_num is not None:
                    blocks.append({
                        "block_type": "verse",
                        "lines": verse_lines,
                        "verse_num": verse_num,
                        "references": ref_after,
                    })
                    ref_after = None
                verse_num = num
                verse_lines = [{**cur, "text": rest}] if rest else []
                i += 1
                continue
            verse_lines.append(cur)
            i += 1
        else:
            if verse_lines or verse_num is not None:
                blocks.append({
                    "block_type": "verse",
                    "lines": verse_lines,
                    "verse_num": verse_num,
                    "references": ref_after,
                })
    return blocks


def blocks_to_chunks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks = []
    pos = 0
    for b in blocks:
        bt = b.get("block_type")
        if bt in ("book_title", "chapter_number", "chapter_name", "section_title"):
            pos += 1
            text = " ".join((x.get("text") or "").strip() for x in b.get("lines", [])).strip()
            chunks.append({
                "chunk_type": bt,
                "position": pos,
                "references": b.get("references"),
                "verse_num": None,
                "text": text,
            })
            continue
        if bt == "verse":
            pos += 1
            text = " ".join(
                _strip_footnote((x.get("text") or "").strip())
                for x in b.get("lines", [])
            ).strip()
            verse_num = b.get("verse_num")
            if not verse_num and chunks:
                prev = chunks[-1]
                if prev.get("chunk_type") == "verse" and prev.get("verse_num"):
                    try:
                        n = int(prev["verse_num"])
                        verse_num = str(n + 1)
                    except (TypeError, ValueError):
                        verse_num = str(pos)
            if not verse_num:
                verse_num = str(pos)
            chunks.append({
                "chunk_type": "verse",
                "position": pos,
                "references": b.get("references"),
                "verse_num": verse_num,
                "text": text,
            })
    return chunks
