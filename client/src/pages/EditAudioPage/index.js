import React, { useState, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { pdfAPI } from "../../services/api";
import Container from "../../components/Container/Container";
import styles from "./EditAudioPage.module.css";

const EditAudioPage = () => {
  const { pdfId: paramPdfId } = useParams();
  const [processedPDFs, setProcessedPDFs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPdfId, setSelectedPdfId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const pdfs = await pdfAPI.listPDFs();
        const completed = pdfs.filter((p) => p.status === "completed");
        setProcessedPDFs(completed);
        if (paramPdfId && completed.some((p) => String(p.id) === paramPdfId)) {
          setSelectedPdfId(parseInt(paramPdfId, 10));
        } else if (completed.length > 0 && !selectedPdfId) {
          setSelectedPdfId(completed[0].id);
        }
      } catch (err) {
        setError("Eroare la încărcarea documentelor");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [paramPdfId]);

  const selectedPdf = processedPDFs.find((p) => p.id === selectedPdfId);

  return (
    <Container>
      <div className={styles.page}>
        <section className={styles.header}>
          <h1 className={styles.title}>Post-producție</h1>
          <p className={styles.subtitle}>
            Alege un document, apoi adaugă voci TTS noi sau încarcă propriul
            audio înregistrat pentru fiecare segment.
          </p>
        </section>

        {loading ? (
          <div className={styles.loading}>Se încarcă documentele...</div>
        ) : error ? (
          <div className={styles.error}>{error}</div>
        ) : processedPDFs.length === 0 ? (
          <div className={styles.empty}>
            <p>Niciun document procesat încă.</p>
            <Link to="/import" className={styles.link}>
              Importă un PDF mai întâi
            </Link>
          </div>
        ) : (
          <>
            <div className={styles.pdfSection}>
              <div className={styles.pdfSectionCard}>
                <label className={styles.label}>Document selectat</label>
                <div className={styles.pdfSectionRow}>
                  <select
                    className={styles.select}
                    value={selectedPdfId ?? ""}
                    onChange={(e) =>
                      setSelectedPdfId(
                        e.target.value ? parseInt(e.target.value, 10) : null
                      )
                    }
                  >
                    <option value="">Selectează un document</option>
                    {processedPDFs.map((pdf) => (
                      <option key={pdf.id} value={pdf.id}>
                        {(pdf.filename || "").replace(/\.pdf$/i, "")}
                      </option>
                    ))}
                  </select>
                  {selectedPdf && (
                    <Link
                      to={`/documents/${selectedPdf.id}`}
                      className={styles.openDocBtn}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                      </svg>
                      Deschide documentul
                    </Link>
                  )}
                </div>
              </div>
            </div>

            {selectedPdfId && (
              <div className={styles.cards}>
                <section className={styles.card}>
                  <div className={styles.cardIcon}>
                    <svg
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
                    </svg>
                  </div>
                  <h2 className={styles.cardTitle}>Editare standard</h2>
                  <p className={styles.cardDesc}>
                    Atribuie sau schimbă vocile TTS pentru narator și
                    personaje. Clonează o voce personalizată sau alege din
                    bibliotecă.
                  </p>
                  <Link
                    to={`/documents/${selectedPdfId}`}
                    className={styles.cardAction}
                  >
                    Editează voci în document
                  </Link>
                </section>

                <section className={styles.card}>
                  <div className={styles.cardIcon}>
                    <svg
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M3 18v-6a9 9 0 0 1 18 0v6" />
                      <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3z" />
                      <path d="M3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z" />
                    </svg>
                  </div>
                  <h2 className={styles.cardTitle}>Editare custom</h2>
                  <p className={styles.cardDesc}>
                    Înregistrează sau încarcă propriul tău audio pentru fiecare
                    segment în studio. Înlocuiește TTS cu vocea ta.
                  </p>
                  <Link
                    to={`/post-productie/studio/${selectedPdfId}`}
                    className={styles.cardAction}
                  >
                    Deschide studio
                  </Link>
                </section>
              </div>
            )}
          </>
        )}
      </div>
    </Container>
  );
};

export default EditAudioPage;
