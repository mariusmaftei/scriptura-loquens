# How the AI (Gemini) Sees the Cleaned Text

This document shows exactly what text flows through the pipeline and what Gemini receives.

---

## 1. Raw PDF Lines (from pdfplumber)

Each line from the PDF as extracted:

```
GENEZA
Capitolul 1
Vremurile străvechi de la facerea lumii până la Avraam*
*Gen. 1 - Gen. 11:9
Facerea lumii
1. La început*, Dumnezeu a făcut** cerurile şi pământul.
*Ioan 1:1, 2; Evr. 1:10. **Ps. 8:3; Ps. 33:6; ...
Lumina
2. Pământul era pustiu şi gol; ...
*Ps. 33:6; Isa. 40:13, 14
3. Dumnezeu* a zis: „Să fie** lumină!” Şi a fost lumină.
...
```

---

## 2. Filtered: Reference Lines Removed

Lines matching `_is_reference_line()` are **dropped** (never sent to Gemini, never in audio):

| Filtered out | Reason |
|--------------|--------|
| `*Gen. 1 - Gen. 11:9` | Chapter reference |
| `*Ioan 1:1, 2; Evr. 1:10. **Ps. 8:3; ...` | Verse reference |
| `*Ps. 33:6; Isa. 40:13, 14` | Verse reference |
| `1. Evr. 1: Ioan 1:1, 2` | Verse number + ref content |

---

## 3. Joined Text (After Filtering)

```
GENEZA
Capitolul 1
Vremurile străvechi de la facerea lumii până la Avraam*
Facerea lumii
1. La început*, Dumnezeu a făcut** cerurile şi pământul.
Lumina
2. Pământul era pustiu şi gol; ...
3. Dumnezeu* a zis: „Să fie** lumină!” Şi a fost lumină.
...
```

---

## 4. Blocks (Split by Verse Numbers)

The text is split into blocks. A new block starts at each `N.` (verse number).

| Block | Type | Text |
|-------|------|------|
| 1 | preamble | `GENEZA` |
| 2 | preamble | `Capitolul 1` |
| 3 | preamble | `Vremurile străvechi de la facerea lumii până la Avraam*` |
| 4 | preamble | `Facerea lumii` |
| 5 | verse | `1. La început*, Dumnezeu a făcut** cerurile şi pământul.` |
| 6 | preamble | `Lumina` |
| 7 | verse | `2. Pământul era pustiu şi gol; ...` |
| 8 | verse | `3. Dumnezeu* a zis: „Să fie** lumină!” Şi a fost lumină.` |
| ... | ... | ... |

---

## 5. What Gemini Receives (Prompt Format)

Blocks are sent truncated to 500 chars each:

```
[1] GENEZA
[2] Capitolul 1
[3] Vremurile străvechi de la facerea lumii până la Avraam*
[4] Facerea lumii
[5] 1. La început*, Dumnezeu a făcut** cerurile şi pământul.
[6] Lumina
[7] 2. Pământul era pustiu şi gol; peste faţa adâncului de ape era întuneric, şi* Duhul lui Dumnezeu Se mişca pe deasupra apelor.
[8] 3. Dumnezeu* a zis: „Să fie** lumină!" Şi a fost lumină.
...
```

**Gemini's job:** Assign `role`, `character_name`, `chunk_type`, `references` for each block. It does NOT change, split, or merge block text.

---

## 6. When Format Lines Are Used (No Gemini Call)

When `format_lines` are available (font size, color), the pipeline uses rule-based classification and skips Gemini:

- **Preamble** chunk_type: `_infer_preamble_type()` or `_looks_like_title_format()` (font > 12.5pt or non-black)
- **Verse** segments: `_split_verse_by_character_speech()` splits quoted speech into narrator/character chunks

---

## 7. Stored Chunk Text (After _clean_verse_text)

For verse blocks, before storage:

- `*`, `**`, `†` removed
- Reference spans (Ioan 1:1, Ps. 8:3, etc.) removed
- Inline `,1` refs removed

**Example:** `1. La început*, Dumnezeu a făcut** cerurile...` → stored as `La început, Dumnezeu a făcut cerurile şi pământul.`

---

## 8. TTS Output (What You Hear)

- Verse number (`1.`) stripped by `remove_verse_number_from_text()`
- Any remaining refs stripped by `_strip_references_from_tts()`
- Titles get `!` appended for emphasis

**Final spoken:** `"La început, Dumnezeu a făcut cerurile şi pământul."`
