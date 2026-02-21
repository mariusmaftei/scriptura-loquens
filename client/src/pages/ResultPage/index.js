import React, { useState, useCallback, useRef, useMemo } from "react";
import { Link } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { getAmbientFileUrl } from "../../services/api";
import ChunkViewer from "../../components/ChunkViewer/ChunkViewer";
import VoiceCustomizer from "../../components/VoiceCustomizer/VoiceCustomizer";
import SequentialAudioPlayer from "../../components/SequentialAudioPlayer/SequentialAudioPlayer";
import ErrorMessage from "../../components/ErrorMessage/ErrorMessage";
import Button from "../../components/Button/Button";
import FontSelector from "../../components/FontSelector/FontSelector";
import VoiceCloner from "../../components/VoiceCloner/VoiceCloner";
import styles from "./ResultPage.module.css";

const getCharacterLabel = (role, characterName) =>
  role === "narrator" ? "Narrator" : characterName || "Character";

const getVoiceSettingsKey = (role, characterName) => characterName || role;

const ResultPage = ({ pdfId }) => {
  const {
    currentPDF,
    chunks,
    characters,
    voiceSettings,
    availableVoices,
    audioFiles,
    ambientTracks,
    error,
    updateVoiceSettings,
    regenerateAudio,
    clearError,
    loadAvailableVoices,
    uploadAmbient,
    setSelectedAmbient,
  } = useApp();

  const ambientFileInputRef = useRef(null);
  const [ambientUploading, setAmbientUploading] = useState(false);

  const voiceActorList = useMemo(() => {
    const byId = new Map(
      (availableVoices || []).map((v) => [
        v.voice_id,
        v.voice_name || v.voice_id,
      ])
    );
    return (characters || []).map((char) => {
      const key = getVoiceSettingsKey(char.role, char.character_name);
      const setting = voiceSettings?.[key];
      const voiceName =
        setting?.voice_name ||
        (setting?.voice_id
          ? byId.get(setting.voice_id) || setting.voice_id
          : null);
      return {
        label: getCharacterLabel(char.role, char.character_name),
        voiceName: voiceName || null,
      };
    });
  }, [characters, voiceSettings, availableVoices]);

  const docTitle = useMemo(
    () => (currentPDF?.filename || "").replace(/\.pdf$/i, ""),
    [currentPDF?.filename]
  );

  const [selectedChunkId, setSelectedChunkId] = useState(null);
  const [playingChunkId, setPlayingChunkId] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSingleSegment, setPlaySingleSegment] = useState(false);
  const [playerSettingsPanel, setPlayerSettingsPanel] = useState(null);
  const [showVoiceCloner, setShowVoiceCloner] = useState(false);
  const transcriptionScrollRef = useRef(null);

  const handleVoiceSave = async (settings) => {
    if (!pdfId) return;
    try {
      await updateVoiceSettings(pdfId, settings);
      await regenerateAudio(pdfId);
    } catch (err) {
      console.error("Voice save error:", err);
    }
  };

  const handleAmbientUpload = async (e) => {
    const file = e?.target?.files?.[0];
    if (!file || !pdfId) return;
    e.target.value = "";
    try {
      setAmbientUploading(true);
      await uploadAmbient(pdfId, file);
    } catch (err) {
      console.error("Ambient upload error:", err);
    } finally {
      setAmbientUploading(false);
    }
  };

  const handleSelectAmbient = (value) => {
    if (!pdfId) return;
    const id = value === "" ? null : parseInt(value, 10);
    setSelectedAmbient(pdfId, id);
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

  const handleChunkSelect = (chunkId) => {
    setSelectedChunkId(chunkId);
    setPlayingChunkId(chunkId);
    setPlaySingleSegment(true);
    setIsPlaying(true);
  };

  const handleChunkChange = useCallback((chunkId) => {
    setPlayingChunkId(chunkId);
    setSelectedChunkId(chunkId);
  }, []);

  const handlePlayingChange = useCallback((playing) => {
    setIsPlaying(playing);
    if (!playing) {
      setPlayingChunkId(null);
      setPlaySingleSegment(false);
    }
  }, []);

  if (!currentPDF || currentPDF.id !== parseInt(pdfId, 10)) {
    return null;
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.headerTop}>
            <Link to="/" className={styles.backLink} aria-label="Back">
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
            </Link>
            <div className={styles.docInfo}>
              <h1 className={styles.docTitle}>{docTitle}</h1>
              <div className={styles.meta}>
                <div className={styles.metaRow}>
                  <span className={styles.metaItem}>
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                    </svg>
                    {currentPDF.language_name ||
                      currentPDF.language ||
                      "Unknown"}
                  </span>
                  <span className={styles.metaSeparator}>·</span>
                  <span className={styles.metaItem}>
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                      <polyline points="10 9 9 9 8 9" />
                    </svg>
                    {chunks.length} segments
                  </span>
                </div>
                {voiceActorList.length > 0 && (
                  <div className={styles.metaRow}>
                    <span className={styles.metaItem}>
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
                      </svg>
                      <span className={styles.voiceActorsList}>
                        {voiceActorList.map(({ label, voiceName }, i) => {
                          const shortName = voiceName?.includes(" - ")
                            ? voiceName.split(" - ")[0].trim()
                            : voiceName;
                          return (
                            <span key={i} className={styles.voiceActorChip}>
                              {shortName ? `${label}: ${shortName}` : label}
                            </span>
                          );
                        })}
                      </span>
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <div className={styles.contentGrid}>
          {audioFiles.length > 0 && (
            <div
              className={
                playerSettingsPanel
                  ? styles.playerContainerTopExpanded
                  : styles.playerContainerTop
              }
            >
              <SequentialAudioPlayer
                chunks={chunks}
                audioFiles={audioFiles}
                startFromChunkId={playingChunkId}
                playOnlyChunkId={playSingleSegment ? playingChunkId : null}
                onChunkChange={handleChunkChange}
                onPlayingChange={handlePlayingChange}
                onPlayButtonClick={() => setPlaySingleSegment(false)}
                ambientTrackUrl={
                  currentPDF?.selected_ambient_track_id
                    ? getAmbientFileUrl(currentPDF.selected_ambient_track_id)
                    : null
                }
                customNarratorName={currentPDF?.custom_narrator_name}
                customVoiceActorName={currentPDF?.custom_voice_actor_name}
              />
              <div className={styles.playerSettingsButtons}>
                <button
                  type="button"
                  className={
                    playerSettingsPanel === "voice"
                      ? styles.playerSettingsBtnActive
                      : styles.playerSettingsBtn
                  }
                  onClick={() =>
                    setPlayerSettingsPanel((p) =>
                      p === "voice" ? null : "voice"
                    )
                  }
                  aria-expanded={playerSettingsPanel === "voice"}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
                  </svg>
                  Voice settings
                </button>
                <button
                  type="button"
                  className={
                    playerSettingsPanel === "font"
                      ? styles.playerSettingsBtnActive
                      : styles.playerSettingsBtn
                  }
                  onClick={() =>
                    setPlayerSettingsPanel((p) =>
                      p === "font" ? null : "font"
                    )
                  }
                  aria-expanded={playerSettingsPanel === "font"}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M4 7V4h16v3M9 20h6M12 4v16" />
                  </svg>
                  Font settings
                </button>
              </div>
              {playerSettingsPanel === "voice" && (
                <div className={styles.playerSettingsPanel}>
                  <div className={styles.voiceClonerSection}>
                    <div className={styles.voiceClonerHeader}>
                      <h3 className={styles.voiceClonerTitle}>Custom Voice</h3>
                      {!showVoiceCloner && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setShowVoiceCloner(true)}
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
                          Clone Voice from Audio
                        </Button>
                      )}
                    </div>
                    {showVoiceCloner && (
                      <VoiceCloner
                        onVoiceCloned={handleVoiceCloned}
                        onCancel={() => setShowVoiceCloner(false)}
                      />
                    )}
                  </div>
                  <div className={styles.ambientSection}>
                    <h3 className={styles.ambientTitle}>Ambient music</h3>
                    <input
                      ref={ambientFileInputRef}
                      type="file"
                      accept=".mp3,.wav,.m4a,.ogg"
                      className={styles.ambientFileInput}
                      onChange={handleAmbientUpload}
                    />
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => ambientFileInputRef.current?.click()}
                      disabled={ambientUploading}
                    >
                      {ambientUploading ? "Uploading…" : "Upload ambient"}
                    </Button>
                    <div className={styles.ambientSelectWrap}>
                      <label className={styles.ambientLabel}>
                        Play during audio
                      </label>
                      <select
                        className={styles.ambientSelect}
                        value={
                          currentPDF?.selected_ambient_track_id != null
                            ? String(currentPDF.selected_ambient_track_id)
                            : ""
                        }
                        onChange={(e) => handleSelectAmbient(e.target.value)}
                      >
                        <option value="">None</option>
                        {(ambientTracks || []).map((t) => (
                          <option key={t.id} value={String(t.id)}>
                            {t.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  {characters.length > 0 && (
                    <div className={styles.voiceSettingsSection}>
                      <VoiceCustomizer
                        characters={characters}
                        voiceSettings={voiceSettings}
                        availableVoices={availableVoices}
                        language={currentPDF.language || "en"}
                        onVoiceChange={() => {}}
                        onSave={handleVoiceSave}
                      />
                    </div>
                  )}
                </div>
              )}
              {playerSettingsPanel === "font" && (
                <div className={styles.playerSettingsPanel}>
                  <div className={styles.fontSettingsSection}>
                    <FontSelector />
                  </div>
                </div>
              )}
            </div>
          )}
          <main className={styles.mainContent}>
            <section
              className={`${styles.section} ${styles.sectionTranscription}`}
            >
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                  Transcription
                </h2>
              </div>
              <div className={styles.transcriptionContentWrap}>
                <div
                  className={styles.transcriptionContent}
                  ref={transcriptionScrollRef}
                >
                  <ChunkViewer
                    chunks={chunks}
                    selectedChunkId={selectedChunkId}
                    playingChunkId={playingChunkId}
                    onChunkSelect={handleChunkSelect}
                    scrollContainerRef={transcriptionScrollRef}
                    customNarratorName={currentPDF?.custom_narrator_name}
                    customVoiceActorName={currentPDF?.custom_voice_actor_name}
                  />
                </div>
                <div className={styles.transcriptionFade} aria-hidden />
              </div>
            </section>
          </main>

          <aside className={styles.sidebar}></aside>
        </div>
      </div>

      {error && <ErrorMessage message={error} onDismiss={clearError} />}
    </div>
  );
};

export default ResultPage;
