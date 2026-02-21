# PDF to Audio Pipeline (pipeline-pdf-chunks-audio-md)

## Structure → Audio mapping (one chunk = one audio file)

| Element | Example | Detection | Audio |
|---------|---------|-----------|-------|
| **Book title** | GENEZA | Font size, centered | 1 file |
| **Chapter number** | Capitolul 1 | `Capitolul` + number pattern | 1 file |
| **Chapter name** | Vremurile străvechi... | Not numbered, font/color | 1 file |
| **Section titles** | Facerea lumii, Lumina | Not numbered, short | 1 file each |
| **Verse** | 1. La început, Dumnezeu... | Numbered `N.` | 1–3 files (narrator/character) |
| **Reference lines** | *Ioan 1:1; Gen. 3:12; ... | Never included | Not spoken |

## Verse boundaries

- **Starts:** `1.`, `18.`, etc. (number + period + space)
- **Ends:** Next verse number OR reference line (`*Gen. 3:12; 1Cor. 11:9...`)
- **References excluded:** Filtered during block building + safety pass in TTS

## Multi-character verses (e.g. verse 3)

`Dumnezeu a zis: „Să fie lumină!" Şi a fost lumină.` → **3 audio files:**

1. Narrator: "Dumnezeu a zis:"
2. Character (God): "„Să fie lumină!""
3. Narrator: "Şi a fost lumină."

## TTS output (clean audio)

- No verse numbers (`1.`, `18.`)
- No footnote markers (`*`, `**`, `†`)
- No reference lines
- Example: "La început, Dumnezeu a făcut cerurile şi pământul."
