# Pipeline: Reliable Verse Number Handling

## Current Flow (Why results.json hasn't changed)

1. **Client** → `POST /api/analyze-pdf-json` with PDF
2. **pdf_service** → `process_pdf_file_with_format()` → extracts `format_lines` (text per PDF line)
3. **gemini_service** → `analyze_text_in_batches(format_lines)` → `analyze_text_chunks(format_lines=...)`
4. **Response** → frontend saves to `results.json`

**To see changes:** Re-upload the PDF via the UI (or re-call the API) and save the new response to `results.json`. The server reloads on file changes; the client must trigger a new analyze.

---

## Suggested Pipeline Architecture

### Principle: Extract verse number at the source, pass it through unchanged

```
PDF → [Extract] → format_lines (each line: text, verse_num?) 
    → [Chunk] → blocks (each verse block keeps verse_num from source)
    → [Build JSON] → chunks (verse_num from block text "N. " first, else block.verse_num)
```

### Step 1: PDF Extraction (pdf_service)

- **Output:** `format_lines = [{text, font_size, is_non_black, verse_num?}]`
- **Logic:** When a line starts with `"N. "`, set `verse_num = N` for that line and all following lines until the next `"N. "`
- **Why:** Verse numbers are determined at extraction; later steps only propagate them.

### Step 2: Line preprocessing (gemini_service _split_from_format_lines)

- **Keep:** `verse_num` on each line when merging footnote lines
- **Fix:** `_merge_footnote_line_with_next` must not drop verse numbers. If the first line of a merge has `"N. "`, prepend it to the merged text: `merged = f"{vn}. {merged}"` when the first line had a verse number.

### Step 3: Block building (_split_by_verse_numbers)

- **Keep:** Block text in the form `"N. content"` when the first content line has it
- **Already done:** `_block_text()` uses the verse number from the first line when present

### Step 4: JSON chunk construction (analyze_text_chunks)

- **Primary:** Read verse number from block text: `m = re.match(r'^(\d+)\.\s+', block_text)`
- **Fallback:** Use `b.get('verse_num')` when the block text has no `"N. "` prefix (e.g. merged continuations)

---

## Concrete Fixes to Apply

### A. Preserve verse number in footnote merge

In `_merge_footnote_line_with_next`, when merging two lines:

- If `kept[i]` has text starting with `"N. "`, extract `N` and prefix the merged text with `"N. "`.
- Preserve `verse_num` from `kept[i]` (the line that had the verse number).

### B. Add verse_num at PDF extraction (optional, for robustness)

In `extract_text_with_formatting` or `_extract_lines_with_format`, after building each line:

- If `line['text']` matches `^(\d+)\.\s+`, set `line['verse_num'] = m.group(1)`.
- This gives the pipeline a second source of verse numbers.

### C. Simpler flow: line-by-line chunking (alternative)

Instead of join → split, process `format_lines` sequentially:

1. For each line, detect type: `verse` (starts with `"N. "`), `section`, `preamble`
2. For verses: extract `verse_num = N` and create a chunk with that number
3. Merge continuation lines (e.g. `"pe"` + `"deasupra"`) but keep the verse number from the line that started the verse

---

## Verification

1. **Re-upload the PDF** via the UI (or POST to `/api/analyze-pdf-json`) – the server returns fresh results
2. **Save the response** to `results.json` – the client/frontend must overwrite the file with the new API output
3. **Check** that each verse chunk has the correct `verse_num` matching the PDF

## Fixes Applied

1. **PDF extraction (pdf_service):** `_add_verse_nums_to_lines()` adds `verse_num` to each format_line when it starts with `"N. "`; subsequent lines inherit until the next verse
2. **Footnote merge:** `_merge_footnote_line_with_next` preserves `"N. "` from either merged line and uses the correct verse_num
3. **Format lines:** `_split_from_format_lines` uses `line.get('verse_num')` from PDF extraction when available
4. **Chunk construction:** Verse number is taken from block text `"N. "` first, then from `b.verse_num`
