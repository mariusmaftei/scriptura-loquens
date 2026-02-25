import React, { useState, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { pdfAPI } from "../../services/api";
import Container from "../../components/Container/Container";
import ConfirmationModal from "../../components/ConfirmationModal/ConfirmationModal";
import { getBookKeyForPDF, getBookMetaForPDF, getBookMeta } from "../../utils/bookMeta";
import styles from "./BookDetailPage.module.css";

const BookDetailPage = () => {
  const { bookSlug } = useParams();
  const [allPdfs, setAllPdfs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [confirmModal, setConfirmModal] = useState({ open: false, pdf: null });
  const [filterQuery, setFilterQuery] = useState("");

  const bookPdfs = React.useMemo(() => {
    const list = allPdfs.filter((p) => getBookKeyForPDF(p) === bookSlug);
    return list.sort((a, b) => new Date(a.upload_date || 0) - new Date(b.upload_date || 0));
  }, [allPdfs, bookSlug]);

  const bookMeta = bookPdfs.length > 0 ? getBookMetaForPDF(bookPdfs[0]) : getBookMeta(bookSlug, bookSlug);
  const bookTitle = bookMeta.displayName;

  const filteredPdfs = React.useMemo(() => {
    let list = bookPdfs;
    if (filterQuery.trim()) {
      const q = filterQuery.trim().toLowerCase();
      list = bookPdfs.filter((pdf) => {
        const filename = (pdf.filename || "").toLowerCase();
        const lang = (pdf.language_name || pdf.language || "").toLowerCase();
        const dateStr = pdf.upload_date ? new Date(pdf.upload_date).toLocaleDateString("ro-RO") : "";
        return filename.includes(q) || lang.includes(q) || dateStr.includes(q);
      });
    }
    return list;
  }, [bookPdfs, filterQuery]);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const pdfs = await pdfAPI.listPDFs();
        setAllPdfs(pdfs);
      } catch (err) {
        setError("Eroare la încărcarea documentelor");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return "Data necunoscută";
    try {
      return new Date(dateString).toLocaleDateString("ro-RO", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return "Data necunoscută";
    }
  };

  const handleDelete = (e, pdf) => {
    e.preventDefault();
    e.stopPropagation();
    setConfirmModal({ open: true, pdf });
  };

  const handleConfirmDelete = async () => {
    if (!confirmModal.pdf) return;
    try {
      setDeletingId(confirmModal.pdf.id);
      setError(null);
      await pdfAPI.deletePDF(confirmModal.pdf.id);
      setAllPdfs((prev) => prev.filter((p) => p.id !== confirmModal.pdf.id));
      setConfirmModal({ open: false, pdf: null });
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.message || "Eroare la ștergere");
      setConfirmModal({ open: false, pdf: null });
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <Container>
        <div className={styles.page}>
          <p className={styles.loading}>Se încarcă...</p>
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <div className={styles.page}>
          <p className={styles.error}>{error}</p>
          <Link to="/biblioteca" className={styles.backLink}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            Înapoi la Bibliotecă
          </Link>
        </div>
      </Container>
    );
  }

  return (
    <Container>
      <div className={styles.page}>
        <Link to="/biblioteca" className={styles.backLink}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          Înapoi la Bibliotecă
        </Link>

        <div className={styles.hero}>
          <h1 className={styles.bookTitle}>{bookTitle}</h1>
          <p className={styles.bookSubtitle}>
            {bookPdfs.length} {bookPdfs.length === 1 ? "document" : "documente"}
            {(() => {
              const completed = bookPdfs.filter((p) => p.status === "completed").length;
              return completed < bookPdfs.length && completed > 0
                ? ` (${completed} procesate)`
                : completed === 0 && bookPdfs.length > 0
                  ? " — deschide un document pentru a-l procesa"
                  : "";
            })()}
          </p>
        </div>

        {bookPdfs.length === 0 ? (
          <div className={styles.empty}>
            <p>Nu există documente pentru această carte.</p>
          </div>
        ) : (
          <>
            <div className={styles.filterBar}>
              <label htmlFor="doc-filter" className={styles.filterLabel}>
                Filtrează documente
              </label>
              <div className={styles.filterInputWrap}>
                <input
                  id="doc-filter"
                  type="text"
                  className={styles.filterInput}
                  placeholder="Nume fișier, limbă sau dată..."
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  aria-label="Filtrează documentele după nume, limbă sau dată"
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
                  {filteredPdfs.length} {filteredPdfs.length === 1 ? "document" : "documente"}
                </p>
              )}
            </div>
          <div className={styles.pdfGrid}>
            {filteredPdfs.map((pdf) => (
              <Link
                key={pdf.id}
                to={`/documents/${pdf.id}`}
                className={styles.pdfCard}
              >
                <div className={styles.cardAccent} aria-hidden />
                <button
                  type="button"
                  className={styles.deleteBtn}
                  onClick={(e) => handleDelete(e, pdf)}
                  disabled={deletingId === pdf.id}
                  title="Șterge documentul și audio"
                  aria-label="Șterge documentul și audio"
                >
                  {deletingId === pdf.id ? (
                    <span className={styles.deleteBtnText}>...</span>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                      <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z" />
                      <line x1="10" y1="11" x2="10" y2="17" />
                      <line x1="14" y1="11" x2="14" y2="17" />
                    </svg>
                  )}
                </button>
                <div className={styles.cardInner}>
                  <div className={styles.cardIcon}>
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                      <polyline points="10 9 9 9 8 9" />
                    </svg>
                  </div>
                  <h3 className={styles.pdfTitle}>{pdf.filename}</h3>
                  {pdf.status !== "completed" && (
                    <span className={styles.statusBadge}>În așteptare</span>
                  )}
                  <div className={styles.cardBody}>
                    <div className={styles.metaList}>
                      <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Limbă</span>
                        <span className={styles.metaValue}>{pdf.language_name || pdf.language || "—"}</span>
                      </div>
                      <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Încărcat</span>
                        <span className={styles.metaValue}>{formatDate(pdf.upload_date)}</span>
                      </div>
                    </div>
                  </div>
                  <div className={styles.cardFooter}>
                    <span className={styles.viewLink}>
                      {pdf.status === "completed" ? "Deschide documentul" : "Procesează documentul"}
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M5 12h14M12 5l7 7-7 7" />
                      </svg>
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
          {filteredPdfs.length === 0 && filterQuery.trim() && (
            <p className={styles.filterEmpty}>Niciun document găsit pentru „{filterQuery.trim()}”.</p>
          )}
          </>
        )}
      </div>

      <ConfirmationModal
        open={confirmModal.open}
        onClose={() => setConfirmModal({ open: false, pdf: null })}
        onConfirm={handleConfirmDelete}
        title="Șterge documentul"
        message="Sigur ștergi acest document și tot conținutul asociat (inclusiv audio)? Acțiunea nu poate fi anulată."
        confirmLabel="Șterge"
        cancelLabel="Anulează"
        variant="danger"
        loading={deletingId !== null}
      />
    </Container>
  );
};

export default BookDetailPage;
