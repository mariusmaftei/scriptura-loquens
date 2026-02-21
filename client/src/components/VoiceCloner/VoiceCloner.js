import React, { useState } from "react";
import { pdfAPI } from "../../services/api";
import Button from "../Button/Button";
import styles from "./VoiceCloner.module.css";

const VoiceCloner = ({ onVoiceCloned, onCancel }) => {
  const [audioFile, setAudioFile] = useState(null);
  const [voiceName, setVoiceName] = useState("");
  const [description, setDescription] = useState("");
  const [removeBackgroundNoise, setRemoveBackgroundNoise] = useState(false);
  const [isCloning, setIsCloning] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const allowedTypes = [
        "audio/mpeg",
        "audio/wav",
        "audio/mp3",
        "audio/m4a",
        "audio/ogg",
        "audio/flac",
      ];
      const allowedExtensions = [".mp3", ".wav", ".m4a", ".ogg", ".flac"];
      const fileExt = "." + file.name.split(".").pop().toLowerCase();

      if (
        !allowedTypes.includes(file.type) &&
        !allowedExtensions.includes(fileExt)
      ) {
        setError(
          "Invalid file type. Please upload MP3, WAV, M4A, OGG, or FLAC."
        );
        setAudioFile(null);
        return;
      }

      if (file.size > 50 * 1024 * 1024) {
        setError("File size must be less than 50MB.");
        setAudioFile(null);
        return;
      }

      setAudioFile(file);
      setError(null);
      if (!voiceName) {
        const nameFromFile = file.name
          .replace(/\.[^/.]+$/, "")
          .replace(/[-_]/g, " ");
        setVoiceName(nameFromFile);
      }
    }
  };

  const handleClone = async () => {
    if (!audioFile || !voiceName.trim()) {
      setError("Please select an audio file and enter a voice name.");
      return;
    }

    setIsCloning(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await pdfAPI.cloneVoice(
        audioFile,
        voiceName.trim(),
        description.trim() || null,
        removeBackgroundNoise
      );

      setSuccess(result.message || "Voice cloned successfully!");

      setTimeout(() => {
        if (onVoiceCloned) {
          onVoiceCloned(result);
        }
      }, 1500);
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.message ||
          "Failed to clone voice. Please try again."
      );
    } finally {
      setIsCloning(false);
    }
  };

  return (
    <div className={styles.voiceCloner}>
      <div className={styles.header}>
        <h3 className={styles.title}>
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
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
          </svg>
          Clone Voice from Audio Sample
        </h3>
        {onCancel && (
          <button
            className={styles.closeButton}
            onClick={onCancel}
            type="button"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </div>

      <div className={styles.content}>
        <div className={styles.infoBox}>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <p>
            Upload at least 1 minute of clear audio for best results. The cloned
            voice will be available for use immediately.
          </p>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="audio-file" className={styles.label}>
            Audio File (MP3, WAV, M4A, OGG, FLAC)
          </label>
          <div className={styles.fileInputWrapper}>
            <input
              type="file"
              id="audio-file"
              accept="audio/*"
              onChange={handleFileChange}
              className={styles.fileInput}
              disabled={isCloning}
            />
            <label htmlFor="audio-file" className={styles.fileInputLabel}>
              {audioFile ? audioFile.name : "Choose file..."}
            </label>
          </div>
          {audioFile && (
            <p className={styles.fileInfo}>
              {(audioFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          )}
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="voice-name" className={styles.label}>
            Voice Name <span className={styles.required}>*</span>
          </label>
          <input
            type="text"
            id="voice-name"
            value={voiceName}
            onChange={(e) => setVoiceName(e.target.value)}
            placeholder="e.g., Narrator Voice, Deep Male Voice"
            className={styles.textInput}
            disabled={isCloning}
            maxLength={100}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="description" className={styles.label}>
            Description (Optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Warm, mature male voice for Bible narration"
            className={styles.textarea}
            disabled={isCloning}
            rows={3}
            maxLength={500}
          />
        </div>

        <div className={styles.formGroup}>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={removeBackgroundNoise}
              onChange={(e) => setRemoveBackgroundNoise(e.target.checked)}
              disabled={isCloning}
              className={styles.checkbox}
            />
            <span>Remove background noise</span>
          </label>
        </div>

        {error && (
          <div className={styles.errorMessage}>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
        )}

        {success && (
          <div className={styles.successMessage}>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            {success}
          </div>
        )}

        <div className={styles.actions}>
          {onCancel && (
            <Button variant="secondary" onClick={onCancel} disabled={isCloning}>
              Cancel
            </Button>
          )}
          <Button
            variant="primary"
            onClick={handleClone}
            disabled={isCloning || !audioFile || !voiceName.trim()}
          >
            {isCloning ? "Cloning Voice..." : "Clone Voice"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default VoiceCloner;
