import React, { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import ProgressPage from "../ProgressPage";
import VoiceSelectionPage from "../VoiceSelectionPage";
import ResultPage from "../ResultPage";
import Button from "../../components/Button/Button";
import Loading from "../../components/Loading/Loading";
import styles from "./ScripturePage.module.css";

const POLL_INTERVAL_MS = 2500;

const ScripturePage = () => {
  const { pdfId } = useParams();
  const navigate = useNavigate();
  const {
    currentPDF,
    loadPDFData,
    processPDF,
    error,
    clearError,
    voiceSettings,
    characters,
  } = useApp();

  const [view, setView] = useState("loading");
  const [progressStep, setProgressStep] = useState("extract");
  const [voicesConfigured, setVoicesConfigured] = useState(false);
  const processStarted = useRef(false);
  const pollTimer = useRef(null);

  useEffect(() => {
    if (!pdfId) return;
    let cancelled = false;
    setView("loading");

    const load = async () => {
      try {
        await loadPDFData(pdfId);
        if (cancelled) return;
      } catch (e) {
        if (!cancelled) setView("error");
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [pdfId, loadPDFData]);

  useEffect(() => {
    if (!currentPDF || currentPDF.id !== parseInt(pdfId, 10)) return;

    const status = currentPDF.status;
    if (status === "completed") {
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
        pollTimer.current = null;
      }
      const hasVoiceSettings = Object.keys(voiceSettings || {}).length > 0;
      const hasCharacters = (characters || []).length > 0;
      if (hasVoiceSettings && hasCharacters) {
        setView("result");
      } else if (hasCharacters) {
        setView("voiceSelection");
      } else {
        setView("result");
      }
      return;
    }
    if (status === "error") {
      setView("error");
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
        pollTimer.current = null;
      }
      return;
    }

    setView("progress");
    if (status === "processing") {
      setProgressStep("analyze");
      if (!pollTimer.current) {
        pollTimer.current = setInterval(() => {
          loadPDFData(pdfId);
        }, POLL_INTERVAL_MS);
      }
      return;
    }

    if (status === "pending" && !processStarted.current) {
      processStarted.current = true;
      setProgressStep("extract");
      const analyzeTimer = setTimeout(() => setProgressStep("analyze"), 2500);
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
        pollTimer.current = null;
      }
      processPDF(pdfId)
        .then(() => {
          if (pollTimer.current) clearInterval(pollTimer.current);
          return loadPDFData(pdfId);
        })
        .then(() => {
          clearTimeout(analyzeTimer);
          setProgressStep("ready");
          setView("result");
        })
        .catch(() => {
          clearTimeout(analyzeTimer);
          setView("error");
        })
        .finally(() => {
          processStarted.current = false;
        });
    }
  }, [currentPDF, pdfId, loadPDFData, processPDF]);

  useEffect(() => {
    return () => {
      if (pollTimer.current) {
        clearInterval(pollTimer.current);
      }
    };
  }, []);

  const handleRetry = async () => {
    clearError();
    processStarted.current = false;
    setView("progress");
    setProgressStep("extract");
    try {
      await processPDF(pdfId);
      await loadPDFData(pdfId);
      setView("result");
    } catch {
      setView("error");
    }
  };

  if (view === "loading") {
    return (
      <div className={styles.loadWrap}>
        <Loading message="Loading…" fullScreen />
      </div>
    );
  }

  if (view === "progress") {
    return (
      <ProgressPage
        filename={currentPDF?.filename}
        currentStep={progressStep}
        error={null}
      />
    );
  }

  if (view === "error") {
    return (
      <div className={styles.errorWrap}>
        <div className={styles.errorCard}>
          <h2 className={styles.errorTitle}>Processing failed</h2>
          <div className={styles.errorDetail} role="alert">
            <p className={styles.errorLabel}>What went wrong</p>
            <p className={styles.errorMessage}>
              {currentPDF?.error_message ||
                error ||
                "This document failed to process earlier (e.g. API or extraction error). Click Try again to re-run; if it fails again, the exact error will appear here and in the server terminal."}
            </p>
          </div>
          <div className={styles.actions}>
            <Button
              variant="primary"
              onClick={handleRetry}
              className={styles.retryBtn}
            >
              Try again
            </Button>
            <Button
              variant="secondary"
              onClick={() => navigate("/")}
              className={styles.backBtn}
            >
              Back to upload
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (view === "voiceSelection") {
    return (
      <VoiceSelectionPage
        pdfId={pdfId}
        onComplete={() => {
          setVoicesConfigured(true);
          setView("result");
        }}
      />
    );
  }

  if (view === "result") {
    return <ResultPage pdfId={pdfId} />;
  }

  return null;
};

export default ScripturePage;
