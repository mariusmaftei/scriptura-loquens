import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { pdfAPI } from "../../services/api";
import Container from "../../components/Container/Container";
import styles from "./ProcessedDocumentsPage.module.css";

const ProcessedDocumentsPage = () => {
  const [processedPDFs, setProcessedPDFs] = useState([]);
  const [loadingPDFs, setLoadingPDFs] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadPDFs = async () => {
      try {
        setLoadingPDFs(true);
        setError(null);
        const pdfs = await pdfAPI.listPDFs();
        const completed = pdfs.filter((pdf) => pdf.status === "completed");
        setProcessedPDFs(completed);
      } catch (err) {
        console.error("Failed to load PDFs:", err);
        setError("Eroare la încărcarea documentelor");
      } finally {
        setLoadingPDFs(false);
      }
    };
    loadPDFs();
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return "Data necunoscută";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("ro-RO", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return "Data necunoscută";
    }
  };

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
          <div className={styles.pdfGrid}>
            {processedPDFs.map((pdf) => (
              <Link
                key={pdf.id}
                to={`/documents/${pdf.id}`}
                className={styles.pdfCard}
              >
                <div className={styles.cardAccent} aria-hidden />
                <div className={styles.cardInner}>
                  <div className={styles.cardIcon}>
                    <svg
                      width="28"
                      height="28"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
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
                  <div className={styles.cardHeader}>
                    <h3 className={styles.pdfTitle}>{pdf.filename}</h3>
                  </div>
                  <div className={styles.cardBody}>
                    <div className={styles.metaList}>
                      <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Limbă</span>
                        <span className={styles.metaValue}>
                          {pdf.language_name || pdf.language || "Necunoscut"}
                        </span>
                      </div>
                      <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Procesat</span>
                        <span className={styles.metaValue}>
                          {formatDate(pdf.upload_date)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className={styles.cardFooter}>
                    <span className={styles.viewLink}>
                      Deschide documentul
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M5 12h14M12 5l7 7-7 7" />
                      </svg>
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </Container>
  );
};

export default ProcessedDocumentsPage;
