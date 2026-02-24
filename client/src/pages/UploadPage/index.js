import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import PDFUpload from "../../components/PDFUpload/PDFUpload";
import ErrorMessage from "../../components/ErrorMessage/ErrorMessage";
import Container from "../../components/Container/Container";
import styles from "./UploadPage.module.css";
import pdfImage from "../../assets/images/pdf.png";
import aiImage from "../../assets/images/ai-image.png";
import notesImage from "../../assets/images/notes.png";

const UploadPage = () => {
  const navigate = useNavigate();
  const { uploadPDF, loading, error, clearError } = useApp();
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (file) => {
    try {
      setUploading(true);
      clearError();
      const result = await uploadPDF(file);
      if (result?.id) {
        navigate(`/documents/${result.id}`, { replace: true });
      }
    } catch (err) {
      console.error("Upload error:", err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Container>
      <div className={styles.uploadPage}>
        <section className={styles.header}>
          <h1 className={styles.title}>Import</h1>
          <p className={styles.subtitle}>
            Încarcă un document PDF biblic. Sistemul extrage textul, detectează limba și analizează conținutul cu pipeline-ul pe reguli (layout), fără AI.
          </p>
        </section>

        <div className={styles.processFlow}>
          <div className={styles.processStep}>
            <img
              src={pdfImage}
              alt="Import PDF"
              className={styles.processImage}
            />
            <p className={styles.processLabel}>Import PDF</p>
          </div>
          <div className={styles.processArrow}>→</div>
          <div className={styles.processStep}>
            <img
              src={aiImage}
              alt="Procesare AI"
              className={styles.processImage}
            />
            <p className={styles.processLabel}>Analiză AI</p>
          </div>
          <div className={styles.processArrow}>→</div>
          <div className={styles.processStep}>
            <img
              src={notesImage}
              alt="Transcriere"
              className={styles.processImage}
            />
            <p className={styles.processLabel}>Transcriere</p>
          </div>
        </div>

        <section className={styles.uploadSection}>
          <PDFUpload
            onUpload={handleUpload}
            onFileSelect={() => clearError()}
            uploading={loading || uploading}
            error={error}
          />
        </section>
        {error && <ErrorMessage message={error} onDismiss={clearError} />}
      </div>
    </Container>
  );
};

export default UploadPage;
