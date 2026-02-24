import json
from typing import Any, Optional

from .schema import Chunk, PipelineOutput, Segment
from .extract import extract_layout_lines
from .normalize import normalize_reading_order
from .classify import classify_lines
from .verses import collect_verse_blocks, blocks_to_chunks
from .segments import segment_verse_text


def _format_line(ln: dict) -> dict:
    return {
        "text": ln.get("text", ""),
        "font_size": ln.get("font_size", 0),
        "alignment": "left",
        "is_non_black": False,
    }


def lines_to_format_lines(lines: list[dict]) -> list[dict]:
    return [_format_line(ln) for ln in lines]


def _norm_ref(s: Optional[str]) -> Optional[str]:
    if not s or not s.strip():
        return None
    s = s.strip()
    while s and s[0] in "*† ":
        s = s[1:].strip()
    return s if s else None


def _norm_character_name(s: Optional[str]) -> Optional[str]:
    if not s or not s.strip():
        return None
    return s.strip().rstrip("*†").strip() or None


def run_from_format_lines(format_lines: list[dict]) -> list[dict]:
    lines = [
        {"text": ln.get("text", ""), "font_size": ln.get("font_size", 0)}
        for ln in format_lines
    ]
    classified = classify_lines(lines)
    blocks = collect_verse_blocks(classified)
    raw_chunks = blocks_to_chunks(blocks)
    chunks_out = []
    for i, c in enumerate(raw_chunks):
        pos = i + 1
        refs = _norm_ref(c.get("references"))
        if c["chunk_type"] == "verse":
            segs = segment_verse_text(c["text"])
            chunks_out.append({
                "chunk_type": "verse",
                "position": pos,
                "references": refs,
                "verse_num": c.get("verse_num"),
                "segments": [
                    {"role": s["role"], "character_name": _norm_character_name(s.get("character_name")), "text": s["text"]}
                    for s in segs
                ],
            })
        else:
            text = c.get("text", "").strip()
            chunks_out.append({
                "chunk_type": c["chunk_type"],
                "position": pos,
                "references": refs,
                "verse_num": None,
                "segments": [{"role": "narrator", "character_name": None, "text": text or ""}],
            })
    for i, c in enumerate(chunks_out):
        c["position"] = i + 1
    return chunks_out


def run(pdf_path: str, reference: Optional[str] = None) -> dict:
    raw_lines = extract_layout_lines(pdf_path)
    lines = normalize_reading_order(raw_lines)
    format_lines = lines_to_format_lines(lines)
    chunks = run_from_format_lines(format_lines)
    out = {"chunks": chunks}
    if reference is not None:
        out["reference"] = reference
    validated = PipelineOutput.model_validate(out)
    return validated.model_dump(mode="json", by_alias=True)


def run_to_json(pdf_path: str, output_path: str, reference: Optional[str] = None) -> None:
    data = run(pdf_path, reference=reference)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
