import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import styles from "./PDFUpload.module.css";
import Button from "../Button/Button";
import Loading from "../Loading/Loading";
import ErrorMessage from "../ErrorMessage/ErrorMessage";

const PDFUpload = ({
  onUpload,
  onFileSelect,
  uploading = false,
  error = null,
}) => {
  const [selectedFile, setSelectedFile] = useState(null);

  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        if (file.type === "application/pdf") {
          setSelectedFile(file);
          onFileSelect?.(file);
        }
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } =
    useDropzone({
      onDrop,
      accept: {
        "application/pdf": [".pdf"],
      },
      maxFiles: 1,
      disabled: uploading,
    });

  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  const handleRemove = () => {
    setSelectedFile(null);
    onFileSelect?.(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  return (
    <div className={styles.pdfUpload}>
      {error && <ErrorMessage message={error} onDismiss={handleRemove} />}

      {fileRejections.length > 0 && (
        <ErrorMessage
          message="Te rugăm să încarci un fișier PDF valid"
          onDismiss={handleRemove}
        />
      )}

      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={`${styles.dropzone} ${isDragActive ? styles.active : ""}`}
        >
          <input {...getInputProps()} />
          <div className={styles.dropzoneContent}>
            <svg
              className={styles.icon}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className={styles.text}>
              {isDragActive
                ? "Plasează fișierul PDF aici"
                : "Trage și plasează un fișier PDF aici sau apasă pentru a selecta"}
            </p>
            <p className={styles.hint}>Doar fișiere PDF sunt acceptate</p>
          </div>
        </div>
      ) : (
        <div className={styles.filePreview}>
          <div className={styles.fileInfo}>
            <svg
              className={styles.fileIcon}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
            <div className={styles.fileDetails}>
              <p className={styles.fileName}>{selectedFile.name}</p>
              <p className={styles.fileSize}>
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
          <div className={styles.fileActions}>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRemove}
              disabled={uploading}
            >
              Elimină
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleUpload}
              loading={uploading}
              disabled={uploading}
            >
              {uploading ? "Se încarcă..." : "Import PDF"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PDFUpload;
