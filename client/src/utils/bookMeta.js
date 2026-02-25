const getBookKeyFromFilename = (filename) => {
  if (!filename) return "fara-titlu";
  let base = filename.replace(/\.pdf$/i, "").trim();
  base = base.replace(/\s*[-–—]?\s*(?:page\s*[-–—]?\s*)?\d+\s*$/i, "").trim();
  const slug = base
    .replace(/\s+/g, "-")
    .replace(/[^\w\u0080-\u024F\-]/gi, "")
    .replace(/-+/g, "-")
    .trim()
    .toLowerCase();
  return slug || "fara-titlu";
};

const getBookTitleFromFilename = (filename) => {
  if (!filename) return "Fără titlu";
  let base = filename.replace(/\.pdf$/i, "").trim();
  base = base.replace(/\s*[-–—]?\s*(?:page\s*[-–—]?\s*)?\d+\s*$/i, "").trim();
  return base || "Fără titlu";
};

const toTitleCase = (str) => {
  if (!str || typeof str !== "string") return str;
  const small = /\b(și|în|de|la|cu|pe|din|pentru|sau|dar|ca|fiind)\b/gi;
  return str
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(small, (m) => m.toLowerCase());
};

const KNOWN_BOOKS = {
  "biblia-in-limba-romana-dumitru-cornilescu": {
    displayName: "Sfânta Scriptură",
    byLabel: "Traducator",
    byValue: "Dumitru Cornilescu",
    genre: "epistolar",
  },
};

const getBookMeta = (key, rawTitle) => {
  const known = KNOWN_BOOKS[key];
  if (known) return known;
  if (key.includes("biblia") && key.includes("cornilescu")) {
    return {
      displayName: "Sfânta Scriptură",
      byLabel: "Traducator",
      byValue: "Dumitru Cornilescu",
      genre: "epistolar",
    };
  }
  const displayName = toTitleCase(rawTitle);
  const parts = rawTitle.split(/\s+[-–—]\s+|\s+,\s+/);
  const byValue = parts.length > 1 ? parts.pop().trim() : null;
  return {
    displayName: parts.length > 0 ? toTitleCase(parts[0]) : displayName,
    byLabel: byValue ? "Autor" : null,
    byValue: byValue || null,
    genre: "carte",
  };
};

const slugFromName = (name) => {
  if (!name || typeof name !== "string") return "";
  return name
    .trim()
    .replace(/\s+/g, "-")
    .replace(/[^\w\u0080-\u024F\-]/gi, "")
    .replace(/-+/g, "-")
    .toLowerCase() || "fara-titlu";
};

const getBookKeyForPDF = (pdf) => {
  if (pdf?.book_key) return pdf.book_key;
  return getBookKeyFromFilename(pdf?.filename);
};

const getBookMetaForPDF = (pdf) => {
  if (pdf?.book_display_name) {
    return {
      displayName: pdf.book_display_name,
      byLabel: pdf.book_author ? "Autor" : null,
      byValue: pdf.book_author || null,
      genre: (pdf.book_genre || "carte").toLowerCase(),
    };
  }
  const key = getBookKeyForPDF(pdf);
  const rawTitle = getBookTitleFromFilename(pdf?.filename);
  return getBookMeta(key, rawTitle);
};

export { getBookKeyFromFilename, getBookTitleFromFilename, getBookMeta, toTitleCase, slugFromName, getBookKeyForPDF, getBookMetaForPDF };
