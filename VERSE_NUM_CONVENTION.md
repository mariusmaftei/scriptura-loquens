# Verse Number Convention & Best Approach for Text-to-Audio

## Your Project Context

- **Input:** Bible PDF (Romanian, Dumitru Cornilescu)
- **Output:** Chunked text → TTS → audio files
- **Purpose:** verse_num for display, navigation, and possibly announcing before each verse

## Core Principle

**For TTS/audio, playback order is what matters.** The chunks are played in position order (1, 2, 3…). `verse_num` is metadata for the UI and labeling, not for ordering.

## Recommended Approach

### 1. **Treat verse_num as optional / best-effort**

- Use **position** for playback order (chunk 5 plays before chunk 7).
- Use **verse_num** for display only (e.g. “Verse 3”).
- If verse_num is wrong, audio order is still correct. Worst case: the label is off, but playback is fine.

### 2. **Avoid complex post-processing heuristics**

The current approach tries to:
- Fix duplicates (1,1 → 1,2)
- Fill gaps (14,16,18 → 14,15,16,17,18)
- Enforce monotonic sequence

This can create new problems (e.g. overwriting a correct `verse_num` with a wrong one). Heuristics are brittle when the source is inconsistent.

### 3. **Fix at the source**

Verse numbers should be set where the PDF is parsed, not later:

- Each PDF line already has or implies a verse number (e.g. `"2. Pământul era..."`).
- Preserve that number when building lines.
- Keep verse number and content together when merging footnote lines.
- Avoid joining all text and then re-splitting, which tends to lose verse markers.

### 4. **Simpler alternative: line-by-line processing**

Instead of:
```
join lines → split by regex → merge → post-fix verse_num
```

Use:
```
for each line:
  if line starts with "N. " → verse N starts
  group lines until next "N. " → one chunk per verse
  assign verse_num = N from the line that started it
```

That keeps verse numbers tied to the original text, with fewer chances to mislabel.

### 5. **Convention summary**

| Aspect | Recommendation |
|--------|----------------|
| **Playback order** | Use `position` only |
| **verse_num** | Best-effort metadata; do not rely on it for ordering |
| **Fixes** | Prefer fixes during extraction/parsing over post-processing |
| **Heuristics** | Avoid extra logic (monotonic, gap-fill, etc.) |
| **Testing** | Re-upload PDF and compare against printed Bible numbering |

## Practical Next Steps

1. **Option A – Minimal change:** Remove the monotonic/gap-fill post-processing. Keep whatever verse_num comes from the PDF/text, and rely on position for order.

2. **Option B – Stronger fix:** Refactor to a line-by-line flow where each line is classified once (verse/section/preamble) and verse_num is taken directly from lines that start with `"N. "`.

3. **Option C – Decouple:** If verse numbers stay unreliable, omit or de-emphasize them in the UI and focus on correct ordering and audio quality.
