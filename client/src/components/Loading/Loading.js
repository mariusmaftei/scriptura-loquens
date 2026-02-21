import React from "react";
import styles from "./Loading.module.css";

const Loading = ({
  size = "md",
  fullScreen = false,
  message = "Loading...",
}) => {
  const containerClass = fullScreen ? styles.fullScreen : styles.container;

  return (
    <div className={containerClass}>
      <div className={styles.spinnerContainer}>
        <div
          className={`${styles.spinner} ${styles[size]}`}
          aria-label="Loading"
        />
        {message && <p className={styles.message}>{message}</p>}
      </div>
    </div>
  );
};

export default Loading;
