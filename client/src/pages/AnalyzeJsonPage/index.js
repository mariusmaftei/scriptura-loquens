import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { pdfAPI } from "../../services/api";
import Container from "../../components/Container/Container";
import Button from "../../components/Button/Button";
import Loading from "../../components/Loading/Loading";
import ErrorMessage from "../../components/ErrorMessage/ErrorMessage";
import styles from "./AnalyzeJsonPage.module.css";

const AnalyzeJsonPage = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [jsonResult, setJsonResult] = useState(null);
  const [copied, setCopied] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0 && acceptedFiles[0].type === "application/pdf") {
      setFile(acceptedFiles[0]);
      setError(null);
      setJsonResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    disabled: loading,
  });

  const handleAnalyze = async () => {
    if (!file) return;
    try {
      setLoading(true);
      setError(null);
      const data = await pdfAPI.analyzePDFJson(file);
      setJsonResult(data);
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Eroare la analiză");
      setJsonResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!jsonResult) return;
    navigator.clipboard.writeText(JSON.stringify(jsonResult, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClear = () => {
    setFile(null);
    setJsonResult(null);
    setError(null);
  };

  return (
    <Container>
      <div className={styles.page}>
        <section className={styles.header}>
          <h1 className={styles.title}>Analiză JSON</h1>
          <p className={styles.subtitle}>
            Încarcă un PDF biblic și obține rezultatul în format JSON. Ideal pentru
            analiză, debugging sau trimitere către AI.
          </p>
        </section>

        <section className={styles.uploadSection}>
          {!file ? (
            <div
              {...getRootProps()}
              className={`${styles.dropzone} ${isDragActive ? styles.active : ""}`}
            >
              <input {...getInputProps()} />
              <div className={styles.dropzoneContent}>
                <svg className={styles.icon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className={styles.text}>
                  {isDragActive ? "Plasează PDF aici" : "Trage PDF aici sau apasă pentru a selecta"}
                </p>
                <p className={styles.hint}>Doar fișiere PDF</p>
              </div>
            </div>
          ) : (
            <div className={styles.filePreview}>
              <div className={styles.fileInfo}>
                <svg className={styles.fileIcon} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <span className={styles.fileName}>{file.name}</span>
              </div>
              <div className={styles.actions}>
                <Button variant="outline" size="sm" onClick={handleClear} disabled={loading}>
                  Șterge
                </Button>
                <Button variant="primary" size="sm" onClick={handleAnalyze} loading={loading} disabled={loading}>
                  {loading ? "Se analizează..." : "Analizează"}
                </Button>
              </div>
            </div>
          )}
        </section>

        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {jsonResult && (
          <section className={styles.resultSection}>
            <div className={styles.resultHeader}>
              <h2 className={styles.resultTitle}>Rezultat JSON</h2>
              <Button variant="outline" size="sm" onClick={handleCopy}>
                {copied ? "Copiat!" : "Copiază"}
              </Button>
            </div>
            <pre className={styles.jsonBlock}>
              <code>{JSON.stringify(jsonResult, null, 2)}</code>
            </pre>
          </section>
        )}
      </div>
    </Container>
  );
};

export default AnalyzeJsonPage;
