import React from "react";
import styles from "./ProgressPage.module.css";

const STEPS = [
  { id: "upload", label: "PDF uploaded", done: true },
  { id: "extract", label: "Extracting text…" },
  { id: "analyze", label: "Analyzing with AI…" },
  { id: "ready", label: "Ready" },
];

const ProgressPage = ({ filename, currentStep = "extract", error = null }) => {
  const stepIndex = STEPS.findIndex((s) => s.id === currentStep);
  const doneCount =
    currentStep === "ready" ? STEPS.length : Math.max(1, stepIndex + 1);

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <div className={styles.iconWrap}>
          <div className={styles.icon} aria-hidden>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
            </svg>
          </div>
        </div>
        <h1 className={styles.title}>Processing your document</h1>
        {filename && <p className={styles.filename}>{filename}</p>}
        {error ? (
          <div className={styles.errorBox}>
            <p className={styles.errorText}>{error}</p>
          </div>
        ) : (
          <>
            <ul className={styles.steps} aria-label="Progress">
              {STEPS.map((step, i) => {
                const isDone = i < doneCount;
                const isCurrent = step.id === currentStep;
                return (
                  <li
                    key={step.id}
                    className={`${styles.step} ${isDone ? styles.done : ""} ${
                      isCurrent ? styles.current : ""
                    }`}
                  >
                    <span className={styles.stepMarker}>
                      {isDone ? (
                        <svg
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M20 6L9 17l-5-5" />
                        </svg>
                      ) : (
                        <span className={styles.stepNum}>{i + 1}</span>
                      )}
                    </span>
                    <span className={styles.stepLabel}>{step.label}</span>
                  </li>
                );
              })}
            </ul>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${(doneCount / STEPS.length) * 100}%` }}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ProgressPage;
