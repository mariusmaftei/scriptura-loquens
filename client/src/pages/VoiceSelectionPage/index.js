import React, { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import VoiceCustomizer from "../../components/VoiceCustomizer/VoiceCustomizer";
import VoiceCloner from "../../components/VoiceCloner/VoiceCloner";
import Button from "../../components/Button/Button";
import ErrorMessage from "../../components/ErrorMessage/ErrorMessage";
import styles from "./VoiceSelectionPage.module.css";
import { pdfAPI, API_BASE_URL } from "../../services/api";

const PREVIEW_TEXT_EN =
  "In the beginning, God created the heavens and the earth. The earth was without form and void, and darkness was over the face of the deep. And the Spirit of God was hovering over the face of the waters.";
const PREVIEW_TEXT_RO =
  "La început, Dumnezeu a făcut cerurile și pământul. Pământul era pustiu și gol; peste fața adâncului de ape era întuneric, și Duhul lui Dumnezeu Se mișca pe deasupra apelor.";

const VoiceSelectionPage = ({ pdfId, onComplete }) => {
  const {
    currentPDF,
    characters,
    voiceSettings,
    availableVoices,
    error,
    updateVoiceSettings,
    regenerateAudio,
    clearError,
    loadAvailableVoices,
  } = useApp();

  const [localSettings, setLocalSettings] = useState(voiceSettings);
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [previewingVoice, setPreviewingVoice] = useState(null);
  const [showVoiceCloner, setShowVoiceCloner] = useState(false);
  const audioRef = useRef(null);

  const handleVoiceChange = (characterKey, voiceId) => {
    const newSettings = {
      ...localSettings,
      [characterKey]: {
        ...localSettings[characterKey],
        voice_id: voiceId,
      },
    };
    setLocalSettings(newSettings);
    setHasChanges(true);
  };

  const handleSpeedChange = (characterKey, speed) => {
    const newSettings = {
      ...localSettings,
      [characterKey]: {
        ...localSettings[characterKey],
        speed: parseFloat(speed),
      },
    };
    setLocalSettings(newSettings);
    setHasChanges(true);
  };

  const handlePreview = async (characterKey, settings) => {
    if (!settings.voice_id) return;

    const language = currentPDF?.language || "en";
    const previewText = language === "ro" ? PREVIEW_TEXT_RO : PREVIEW_TEXT_EN;
    const selectedVoice = availableVoices.find(
      (v) => v.voice_id === settings.voice_id
    );
    const languageCode = selectedVoice?.language_code || language;

    setPreviewingVoice(characterKey);

    try {
      const response = await fetch(`${API_BASE_URL}/voice/preview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          voice_id: settings.voice_id,
          language_code: languageCode,
          text: previewText,
          speed: settings.speed || 1.0,
          pitch: settings.pitch || 0.0,
        }),
      });

      if (!response.ok) {
        throw new Error("Preview generation failed");
      }

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = audioUrl;
        audioRef.current.play().catch((e) => {
          console.error("Playback error:", e);
        });
      }
    } catch (err) {
      console.error("Preview error:", err);
    } finally {
      setPreviewingVoice(null);
    }
  };

  const handleVoiceCloned = async (result) => {
    setShowVoiceCloner(false);
    if (pdfId) {
      try {
        await loadAvailableVoices(pdfId);
      } catch (err) {
        console.error("Failed to refresh voices:", err);
      }
    }
  };

  const handleSave = async () => {
    if (!pdfId) return;
    setIsSaving(true);
    try {
      await updateVoiceSettings(pdfId, localSettings);
      await regenerateAudio(pdfId);
      setHasChanges(false);
      if (onComplete) {
        onComplete();
      }
    } catch (err) {
      console.error("Voice save error:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const allVoicesSelected = characters.every((char) => {
    const key = char.character_name
      ? `${char.role}_${char.character_name}`
      : char.role;
    return localSettings[key]?.voice_id;
  });

  if (!currentPDF || currentPDF.id !== parseInt(pdfId, 10)) {
    return null;
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.headerTop}>
            <Link to="/" className={styles.backLink}>
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              <span>New document</span>
            </Link>
            <div className={styles.docInfo}>
              <h1 className={styles.docTitle}>{currentPDF.filename}</h1>
              <p className={styles.subtitle}>
                Select voices for each character before viewing the
                transcription
              </p>
            </div>
          </div>
        </header>

        <div className={styles.settingsSection}>
          <div className={styles.settingsHeader}>
            <div>
              <h2 className={styles.settingsTitle}>
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                </svg>
                Voice Selection
              </h2>
              <p className={styles.settingsDescription}>
                Choose a voice for each character. Click Preview to hear a
                sample before selecting.
              </p>
            </div>
            {!showVoiceCloner && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowVoiceCloner(true)}
                className={styles.cloneButton}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Create Custom Voice
              </Button>
            )}
          </div>

          <div className={styles.settingsContent}>
            {showVoiceCloner && (
              <div className={styles.voiceClonerWrapper}>
                <VoiceCloner
                  onVoiceCloned={handleVoiceCloned}
                  onCancel={() => setShowVoiceCloner(false)}
                />
              </div>
            )}

            {!showVoiceCloner && (
              <VoiceCustomizer
                characters={characters}
                voiceSettings={localSettings}
                availableVoices={availableVoices}
                language={currentPDF.language || "en"}
                onVoiceChange={handleVoiceChange}
                onSpeedChange={handleSpeedChange}
                onPreview={handlePreview}
                previewingVoice={previewingVoice}
              />
            )}

            <audio ref={audioRef} style={{ display: "none" }} />

            {!showVoiceCloner && (
              <div className={styles.actions}>
                <Button
                  variant="primary"
                  size="lg"
                  onClick={handleSave}
                  disabled={!allVoicesSelected || isSaving || !hasChanges}
                  className={styles.saveButton}
                >
                  {isSaving
                    ? "Generating audio..."
                    : "Continue to Transcription"}
                </Button>
                {!allVoicesSelected && (
                  <p className={styles.hint}>
                    Please select a voice for all characters to continue
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {error && <ErrorMessage message={error} onDismiss={clearError} />}
    </div>
  );
};

export default VoiceSelectionPage;
