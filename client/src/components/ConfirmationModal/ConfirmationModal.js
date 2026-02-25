import React, { useEffect } from "react";
import Button from "../Button/Button";
import styles from "./ConfirmationModal.module.css";

const ConfirmationModal = ({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = "Confirmă",
  cancelLabel = "Anulează",
  variant = "primary",
  loading = false,
  confirmDisabled = false,
}) => {
  useEffect(() => {
    if (!open) return;
    const handleEscape = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleEscape);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div
      className={styles.backdrop}
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmation-modal-title"
      aria-describedby={message ? "confirmation-modal-message" : undefined}
    >
      <div className={styles.modal}>
        <div className={styles.accent} aria-hidden />
        <div className={styles.content}>
          <h2 id="confirmation-modal-title" className={styles.title}>
            {title}
          </h2>
          {message && (
            <p id="confirmation-modal-message" className={styles.message}>
              {message}
            </p>
          )}
          <div className={styles.actions}>
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={loading}
            >
              {cancelLabel}
            </Button>
            <Button
              type="button"
              variant={variant === "danger" ? "danger" : "primary"}
              onClick={onConfirm}
              disabled={confirmDisabled || loading}
              loading={loading}
            >
              {confirmLabel}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;
