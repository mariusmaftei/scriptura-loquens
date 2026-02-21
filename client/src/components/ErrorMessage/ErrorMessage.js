import React from "react";
import styles from "./ErrorMessage.module.css";

const ErrorMessage = ({ message, onRetry, onDismiss }) => {
  if (!message) return null;

  return (
    <div className={styles.errorMessage} role="alert">
      <div className={styles.content}>
        <svg
          className={styles.icon}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className={styles.text}>{message}</p>
      </div>
      <div className={styles.actions}>
        {onRetry && (
          <button
            type="button"
            className={styles.retryButton}
            onClick={onRetry}
          >
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            className={styles.dismissButton}
            onClick={onDismiss}
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorMessage;
