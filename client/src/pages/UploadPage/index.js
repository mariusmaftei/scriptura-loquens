import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { pdfAPI } from "../../services/api";
import PDFUpload from "../../components/PDFUpload/PDFUpload";
import ErrorMessage from "../../components/ErrorMessage/ErrorMessage";
import Container from "../../components/Container/Container";
import { getBookKeyForPDF, getBookMetaForPDF, slugFromName } from "../../utils/bookMeta";
import styles from "./UploadPage.module.css";
import pdfImage from "../../assets/images/pdf.png";
import aiImage from "../../assets/images/ai-image.png";
import notesImage from "../../assets/images/notes.png";

const BOOK_MODE_NEW = "new";
const BOOK_MODE_EXISTING = "existing";

const GENRE_OPTIONS = [
  { value: "carte", label: "Carte" },
  { value: "epistolar", label: "Epistolar" },
  { value: "evanghelie", label: "Evanghelie" },
  { value: "istoric", label: "Istoric" },
  { value: "lege", label: "Lege / Torá" },
  { value: "poezie", label: "Poezie / Psalmi" },
  { value: "profetic", label: "Profetic" },
  { value: "sapiențial", label: "Sapiențial" },
  { value: "apocaliptic", label: "Apocaliptic" },
];

const UploadPage = () => {
  const navigate = useNavigate();
  const { uploadPDF, loading, error, clearError } = useApp();
  const [uploading, setUploading] = useState(false);
  const [bookMode, setBookMode] = useState(BOOK_MODE_NEW);
  const [bookName, setBookName] = useState("");
  const [bookAuthor, setBookAuthor] = useState("");
  const [bookGenre, setBookGenre] = useState("carte");
  const [selectedBookKey, setSelectedBookKey] = useState("");
  const [existingBooks, setExistingBooks] = useState([]);
  const [loadingBooks, setLoadingBooks] = useState(false);
  const [bookCoverFile, setBookCoverFile] = useState(null);

  const bookOptions = useMemo(() => {
    const base = bookMode === BOOK_MODE_NEW
      ? {
          bookKey: slugFromName(bookName) || undefined,
          bookDisplayName: bookName.trim() || undefined,
          bookAuthor: bookAuthor.trim() || undefined,
          bookGenre: bookGenre.trim() || undefined,
        }
      : selectedBookKey
        ? (() => {
            const book = existingBooks.find((b) => b.key === selectedBookKey);
            return {
              bookKey: selectedBookKey,
              bookDisplayName: book?.meta?.displayName,
              bookAuthor: book?.meta?.byValue,
              bookGenre: book?.meta?.genre,
            };
          })()
        : {};
    if (bookCoverFile) base.cover = bookCoverFile;
    return base;
  }, [bookMode, bookName, bookAuthor, bookGenre, selectedBookKey, existingBooks, bookCoverFile]);

  useEffect(() => {
    if (bookMode !== BOOK_MODE_EXISTING) return;
    let cancelled = false;
    const load = async () => {
      setLoadingBooks(true);
      try {
        const pdfs = await pdfAPI.listPDFs();
        const completed = pdfs.filter((p) => p.status === "completed");
        const byKey = new Map();
        completed.forEach((pdf) => {
          const key = getBookKeyForPDF(pdf);
          if (!byKey.has(key)) {
            byKey.set(key, { key, pdfs: [], meta: getBookMetaForPDF(pdf) });
          }
          byKey.get(key).pdfs.push(pdf);
        });
        const books = Array.from(byKey.values()).sort((a, b) =>
          (a.meta?.displayName || "").localeCompare(b.meta?.displayName || "")
        );
        if (!cancelled) {
          setExistingBooks(books);
          if (books.length > 0 && !books.some((b) => b.key === selectedBookKey)) {
            setSelectedBookKey(books[0].key);
          }
        }
      } catch (err) {
        if (!cancelled) setExistingBooks([]);
      } finally {
        if (!cancelled) setLoadingBooks(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [bookMode]);

  const handleUpload = async (file) => {
    try {
      setUploading(true);
      clearError();
      const result = await uploadPDF(file, bookOptions);
      if (result?.id) {
        const key = result.book_key || bookOptions.bookKey;
        if (key) {
          navigate(`/biblioteca/book/${encodeURIComponent(key)}`, { replace: true });
        } else {
          navigate(`/documents/${result.id}`, { replace: true });
        }
      }
    } catch (err) {
      console.error("Upload error:", err);
    } finally {
      setUploading(false);
    }
  };

  const canProceed = bookMode === BOOK_MODE_EXISTING
    ? !!selectedBookKey
    : !!bookName.trim();

  return (
    <Container>
      <div className={styles.uploadPage}>
        <section className={styles.header}>
          <h1 className={styles.title}>Import</h1>
          <p className={styles.subtitle}>
            Alege sau creează o carte, apoi încarcă PDF-ul. Documentul va fi asociat cărții și va apărea în bibliotecă.
          </p>
        </section>

        <section className={styles.bookStep}>
          <h2 className={styles.stepTitle}>Carte</h2>
          <div className={styles.bookModeRow}>
            <label className={styles.radioWrap}>
              <input
                type="radio"
                name="bookMode"
                checked={bookMode === BOOK_MODE_NEW}
                onChange={() => setBookMode(BOOK_MODE_NEW)}
                className={styles.radio}
              />
              <span>Carte nouă</span>
            </label>
            <label className={styles.radioWrap}>
              <input
                type="radio"
                name="bookMode"
                checked={bookMode === BOOK_MODE_EXISTING}
                onChange={() => setBookMode(BOOK_MODE_EXISTING)}
                className={styles.radio}
              />
              <span>Adaugă la carte existentă</span>
            </label>
          </div>

          {bookMode === BOOK_MODE_NEW && (
            <div className={styles.bookForm}>
              <label className={styles.fieldLabel}>
                Nume carte <span className={styles.required}>*</span>
              </label>
              <input
                type="text"
                value={bookName}
                onChange={(e) => setBookName(e.target.value)}
                placeholder="ex. Sfânta Scriptură"
                className={styles.input}
                aria-required="true"
              />
              <label className={styles.fieldLabel}>Autor / Traducător</label>
              <input
                type="text"
                value={bookAuthor}
                onChange={(e) => setBookAuthor(e.target.value)}
                placeholder="ex. Dumitru Cornilescu"
                className={styles.input}
              />
              <label className={styles.fieldLabel}>Gen</label>
              <select
                value={bookGenre}
                onChange={(e) => setBookGenre(e.target.value)}
                className={styles.select}
                aria-label="Gen carte"
              >
                {GENRE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <label className={styles.fieldLabel}>Copertă (imagine)</label>
              <div className={styles.coverRow}>
                <input
                  type="file"
                  id="book-cover"
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  onChange={(e) => setBookCoverFile(e.target.files?.[0] || null)}
                  className={styles.fileInput}
                  aria-label="Încarcă copertă carte"
                />
                {bookCoverFile && (
                  <span className={styles.coverName}>{bookCoverFile.name}</span>
                )}
              </div>
            </div>
          )}

          {bookMode === BOOK_MODE_EXISTING && (
            <div className={styles.bookForm}>
              {loadingBooks ? (
                <p className={styles.hint}>Se încarcă cărțile...</p>
              ) : existingBooks.length === 0 ? (
                <p className={styles.hint}>Nu există cărți procesate. Alege „Carte nouă” pentru a crea una.</p>
              ) : (
                <>
                  <label htmlFor="select-book" className={styles.fieldLabel}>
                    Selectează cartea
                  </label>
                  <select
                    id="select-book"
                    value={selectedBookKey}
                    onChange={(e) => setSelectedBookKey(e.target.value)}
                    className={styles.select}
                  >
                    {existingBooks.map((b) => (
                      <option key={b.key} value={b.key}>
                        {b.meta?.displayName || b.key} {b.meta?.byValue ? ` – ${b.meta.byValue}` : ""}
                      </option>
                    ))}
                  </select>
                </>
              )}
            </div>
          )}
        </section>

        <div className={styles.processFlow}>
          <div className={styles.processStep}>
            <img src={pdfImage} alt="Procesează PDF" className={styles.processImage} />
            <p className={styles.processLabel}>Procesează PDF</p>
          </div>
          <div className={styles.processArrow}>→</div>
          <div className={styles.processStep}>
            <img src={aiImage} alt="Procesare AI" className={styles.processImage} />
            <p className={styles.processLabel}>Analiză AI</p>
          </div>
          <div className={styles.processArrow}>→</div>
          <div className={styles.processStep}>
            <img src={notesImage} alt="Transcriere" className={styles.processImage} />
            <p className={styles.processLabel}>Transcriere</p>
          </div>
        </div>

        <section className={`${styles.uploadSection} ${!canProceed ? styles.uploadSectionLocked : ""}`}>
          {!canProceed ? (
            <p className={styles.hint}>
              {bookMode === BOOK_MODE_NEW
                ? "Completează numele cărții pentru a debloca încărcarea."
                : "Selectează o carte pentru a debloca încărcarea."}
            </p>
          ) : (
            <PDFUpload
              onUpload={handleUpload}
              onFileSelect={() => clearError()}
              uploading={loading || uploading}
              error={error}
            />
          )}
        </section>
        {error && <ErrorMessage message={error} onDismiss={clearError} />}
      </div>
    </Container>
  );
};

export default UploadPage;
