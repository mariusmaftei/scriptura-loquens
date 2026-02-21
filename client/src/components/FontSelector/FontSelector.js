import React, { useState, useEffect, useCallback } from "react";
import styles from "./FontSelector.module.css";

const FONT_OPTIONS = [
  {
    id: "system",
    name: "System Default",
    family:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  {
    id: "gentium-plus",
    name: "Gentium Plus (Bible Classic)",
    family: "'Gentium Plus', 'Gentium Book Plus', serif",
    googleFont: "Gentium+Plus",
  },
  {
    id: "eb-garamond",
    name: "EB Garamond (Elegant)",
    family: "'EB Garamond', serif",
    googleFont: "EB+Garamond",
  },
  {
    id: "literata",
    name: "Literata (Reading)",
    family: "'Literata', serif",
    googleFont: "Literata",
  },
  {
    id: "crimson-pro",
    name: "Crimson Pro (Traditional)",
    family: "'Crimson Pro', serif",
    googleFont: "Crimson+Pro",
  },
  {
    id: "charis-sil",
    name: "Charis SIL (Bible Standard)",
    family: "'Charis SIL', 'Charis SIL Compact', serif",
    googleFont: "Charis+SIL",
  },
  {
    id: "source-serif-pro",
    name: "Source Serif Pro",
    family: "'Source Serif Pro', serif",
    googleFont: "Source+Serif+Pro",
  },
  {
    id: "lora",
    name: "Lora",
    family: "'Lora', serif",
    googleFont: "Lora",
  },
];

const STORAGE_KEY = "scriptura_loquens_font_family";

const FontSelector = ({ onFontChange }) => {
  const [selectedFont, setSelectedFont] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) || "gentium-plus";
  });

  const applyFont = useCallback(
    (fontId) => {
      const fontOption = FONT_OPTIONS.find((f) => f.id === fontId);
      if (!fontOption) return;

      if (fontOption.googleFont) {
        const linkId = `font-link-${fontOption.id}`;
        let link = document.getElementById(linkId);
        if (!link) {
          link = document.createElement("link");
          link.id = linkId;
          link.rel = "stylesheet";
          link.href = `https://fonts.googleapis.com/css2?family=${fontOption.googleFont}:wght@400;600;700&display=swap`;
          document.head.appendChild(link);
        }
      }

      document.documentElement.style.setProperty(
        "--transcription-font-family",
        fontOption.family
      );

      if (onFontChange) {
        onFontChange(fontOption);
      }
    },
    [onFontChange]
  );

  useEffect(() => {
    const savedFont = localStorage.getItem(STORAGE_KEY) || "gentium-plus";
    setSelectedFont(savedFont);
    applyFont(savedFont);
  }, [applyFont]);

  const handleFontChange = (e) => {
    const fontId = e.target.value;
    setSelectedFont(fontId);
    localStorage.setItem(STORAGE_KEY, fontId);
    applyFont(fontId);
  };

  return (
    <div className={styles.fontSelector}>
      <label htmlFor="font-select" className={styles.label}>
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
        Font Family
      </label>
      <select
        id="font-select"
        value={selectedFont}
        onChange={handleFontChange}
        className={styles.select}
      >
        {FONT_OPTIONS.map((font) => (
          <option key={font.id} value={font.id}>
            {font.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default FontSelector;
