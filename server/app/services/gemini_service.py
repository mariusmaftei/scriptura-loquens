"""Chunk analysis uses the layout-based Bible pipeline only (no AI)."""
from app.services.bible_pipeline.run import run_from_format_lines


def analyze_text_in_batches(text=None, format_lines=None):
    if format_lines:
        return run_from_format_lines(format_lines)
    if text:
        lines = [{"text": line.strip(), "font_size": 12.0} for line in (text or "").split("\n") if line.strip()]
        return run_from_format_lines(lines)
    return []
