import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { pdfAPI, getBookCoverUrl } from "../../services/api";
import Container from "../../components/Container/Container";
import { getBookKeyForPDF, getBookMetaForPDF, getBookMeta } from "../../utils/bookMeta";
import scriptureImage from "../../assets/images/scripture-facebook.png";
import styles from "./ProcessedDocumentsPage.module.css";

const ProcessedDocumentsPage = () => {
  const [processedPDFs, setProcessedPDFs] = useState([]);
  const [loadingPDFs, setLoadingPDFs] = useState(true);
  const [error, setError] = useState(null);
  const [filterQuery, setFilterQuery] = useState("");

  useEffect(() => {
    const loadPDFs = async () => {
      try {
        setLoadingPDFs(true);
        setError(null);
        const pdfs = await pdfAPI.listPDFs();
        setProcessedPDFs(pdfs);
      } catch (err) {
        console.error("Failed to load PDFs:", err);
        setError("Eroare la încărcarea documentelor");
      } finally {
        setLoadingPDFs(false);
      }
    };
    loadPDFs();
  }, []);

  const books = React.useMemo(() => {
    const byKey = new Map();
    processedPDFs.forEach((pdf) => {
      const key = getBookKeyForPDF(pdf);
      if (!byKey.has(key)) {
        const meta = getBookMetaForPDF(pdf);
        byKey.set(key, { key, title: meta.displayName, pdfs: [], meta });
      }
      byKey.get(key).pdfs.push(pdf);
    });
    return Array.from(byKey.values()).map((b) => ({
      key: b.key,
      title: b.title,
      pdfs: b.pdfs,
      meta: b.meta,
    }));
  }, [processedPDFs]);

  const filteredBooks = React.useMemo(() => {
    if (!filterQuery.trim()) return books;
    const q = filterQuery.trim().toLowerCase();
    return books.filter((book) => {
      const meta = book.meta || getBookMeta(book.key, book.title);
      const matchTitle = (meta.displayName || "").toLowerCase().includes(q);
      const matchBy = (meta.byValue || "").toLowerCase().includes(q);
      const matchGenre = (meta.genre || "").toLowerCase().includes(q);
      return matchTitle || matchBy || matchGenre;
    });
  }, [books, filterQuery]);

  return (
    <Container>
      <div className={styles.processedPage}>
        <div className={styles.header}>
          <h1 className={styles.title}>Bibliotecă</h1>
          <p className={styles.subtitle}>
            Vizualizează și accesează documentele biblice procesate anterior
          </p>
        </div>

        {loadingPDFs ? (
          <div className={styles.loading}>
            <p>Se încarcă documentele...</p>
          </div>
        ) : error ? (
          <div className={styles.error}>
            <p>{error}</p>
          </div>
        ) : processedPDFs.length === 0 ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon} aria-hidden>
              <svg
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.25"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <p className={styles.emptyTitle}>Niciun document procesat încă</p>
            <p className={styles.emptyText}>
              Importă un PDF biblic din pagina Import pentru a vedea
              documentele aici.
            </p>
          </div>
        ) : (
          <>
            <div className={styles.filterBar}>
              <label htmlFor="book-filter" className={styles.filterLabel}>
                Filtrează cărți
              </label>
              <div className={styles.filterInputWrap}>
                <input
                  id="book-filter"
                  type="text"
                  className={styles.filterInput}
                  placeholder="Titlu, traducător, autor sau gen..."
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  aria-label="Filtrează cărțile după titlu, traducător, autor sau gen"
                />
                {filterQuery && (
                  <button
                    type="button"
                    className={styles.filterClear}
                    onClick={() => setFilterQuery("")}
                    aria-label="Șterge filtrul"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                )}
              </div>
              {filterQuery && (
                <p className={styles.filterCount}>
                  {filteredBooks.length} {filteredBooks.length === 1 ? "carte" : "cărți"}
                </p>
              )}
            </div>
          <div className={styles.bookGrid}>
            {filteredBooks.map((book) => {
              const meta = book.meta || getBookMeta(book.key, book.title);
              const coverUrl = getBookCoverUrl(book.pdfs[0]) || scriptureImage;
              return (
              <Link
                key={book.key}
                to={`/biblioteca/book/${encodeURIComponent(book.key)}`}
                className={styles.bookCard}
              >
                <div className={styles.cardAccent} aria-hidden />
                <div className={styles.bookCoverWrap}>
                  <img
                    src={coverUrl}
                    alt=""
                    className={styles.bookCover}
                  />
                </div>
                <div className={styles.cardInner}>
                  <h3 className={styles.bookTitle}>{meta.displayName}</h3>
                  {meta.byLabel && meta.byValue && (
                    <p className={styles.bookBy}>
                      {meta.byLabel}: {meta.byValue}
                    </p>
                  )}
                  <p className={styles.bookGenre}>{meta.genre}</p>
                  <p className={styles.bookCount}>
                    {book.pdfs.length} {book.pdfs.length === 1 ? "document" : "documente"}
                  </p>
                </div>
              </Link>
              );
            })}
          </div>
          {filteredBooks.length === 0 && filterQuery.trim() && (
            <p className={styles.filterEmpty}>Nicio carte găsită pentru „{filterQuery.trim()}”.</p>
          )}
          </>
        )}
      </div>
    </Container>
  );
};

export default ProcessedDocumentsPage;
