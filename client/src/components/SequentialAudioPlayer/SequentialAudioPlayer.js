import React, { useState, useRef, useEffect, useMemo } from "react";
import styles from "./SequentialAudioPlayer.module.css";
import { getAudioFileUrl } from "../../services/api";

const DEFAULT_AMBIENT_VOLUME = 0.25;

const SequentialAudioPlayer = ({
  chunks = [],
  audioFiles = [],
  startFromChunkId = null,
  playOnlyChunkId = null,
  onChunkChange,
  onPlayingChange,
  onPlayButtonClick,
  onAllChunksEnded = null,
  initialAutoPlay = false,
  onAutoPlayStarted = null,
  ambientTrackUrl = null,
  customNarratorName = null,
  customVoiceActorName = null,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [ambientVolume, setAmbientVolume] = useState(DEFAULT_AMBIENT_VOLUME);
  const audioRef = useRef(null);
  const ambientRef = useRef(null);
  const currentChunkIdRef = useRef(null);
  const autoPlayDoneRef = useRef(false);

  const sortedChunks = useMemo(
    () => [...chunks].sort((a, b) => a.position - b.position),
    [chunks]
  );
  const chunkAudioMap = useMemo(
    () => new Map(audioFiles.map((af) => [af.chunk_id, af])),
    [audioFiles]
  );

  const getChunkAudioUrl = (chunkId) => {
    const audioFile = chunkAudioMap.get(chunkId);
    return audioFile ? getAudioFileUrl(audioFile.id) : null;
  };

  useEffect(() => {
    if (initialAutoPlay) {
      autoPlayDoneRef.current = false;
    }
  }, [initialAutoPlay]);

  useEffect(() => {
    if (startFromChunkId !== null && sortedChunks.length > 0) {
      const idx = sortedChunks.findIndex((c) => c.id === startFromChunkId);
      const startIdx = idx >= 0 ? idx : 0;
      setCurrentIndex((prev) => {
        if (startIdx !== prev) {
          setCurrentTime(0);
          return startIdx;
        }
        return prev;
      });
    }
  }, [startFromChunkId, sortedChunks.length]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);
    const handleEnded = () => {
      if (
        playOnlyChunkId != null &&
        currentChunkIdRef.current === playOnlyChunkId
      ) {
        setIsPlaying(false);
        setCurrentTime(0);
        onPlayingChange?.(false);
        return;
      }
      setCurrentIndex((prev) => {
        if (prev < sortedChunks.length - 1) {
          setCurrentTime(0);
          return prev + 1;
        } else {
          setIsPlaying(false);
          setCurrentTime(0);
          if (sortedChunks.length > 0) {
            onAllChunksEnded?.();
          }
          return prev;
        }
      });
    };
    const handleError = () => {
      setCurrentIndex((prev) => {
        if (prev < sortedChunks.length - 1) {
          return prev + 1;
        } else {
          setIsPlaying(false);
          return prev;
        }
      });
    };

    audio.addEventListener("timeupdate", updateTime);
    audio.addEventListener("loadedmetadata", updateDuration);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    return () => {
      audio.removeEventListener("timeupdate", updateTime);
      audio.removeEventListener("loadedmetadata", updateDuration);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
    };
  }, [sortedChunks.length, playOnlyChunkId, onAllChunksEnded]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || sortedChunks.length === 0) return;

    const currentChunk = sortedChunks[currentIndex];
    if (!currentChunk) return;

    const audioUrl = getChunkAudioUrl(currentChunk.id);
    if (!audioUrl) {
      if (currentIndex < sortedChunks.length - 1) {
        setCurrentIndex((prev) => prev + 1);
      } else {
        setIsPlaying(false);
      }
      return;
    }

    currentChunkIdRef.current = currentChunk.id;
    audio.src = audioUrl;
    audio.volume = volume;
    setCurrentTime(0);
    setDuration(0);

    if (isPlaying) {
      audio.play().catch(() => setIsPlaying(false));
    } else if (initialAutoPlay && !autoPlayDoneRef.current && audioUrl) {
      autoPlayDoneRef.current = true;
      const doPlay = () => {
        audio.play().then(() => {
          setIsPlaying(true);
          onAutoPlayStarted?.();
        }).catch(() => {});
      };
      const onCanPlay = () => {
        audio.removeEventListener("canplay", onCanPlay);
        doPlay();
      };
      audio.addEventListener("canplay", onCanPlay);
      if (audio.readyState >= 2) {
        onCanPlay();
      } else {
        audio.load();
      }
    }

    onChunkChange?.(currentChunk.id);
  }, [currentIndex, sortedChunks.length, isPlaying, volume, initialAutoPlay, onAutoPlayStarted]);

  useEffect(() => {
    if (startFromChunkId !== null) {
      setIsPlaying((prev) => {
        if (!prev) return true;
        return prev;
      });
    }
  }, [startFromChunkId]);

  useEffect(() => {
    onPlayingChange?.(isPlaying);
  }, [isPlaying]);

  useEffect(() => {
    const ambient = ambientRef.current;
    if (!ambient) return;
    if (ambientTrackUrl) {
      ambient.src = ambientTrackUrl;
      ambient.loop = true;
      ambient.volume = ambientVolume;
    } else {
      ambient.src = "";
      ambient.pause();
    }
  }, [ambientTrackUrl]);

  useEffect(() => {
    const ambient = ambientRef.current;
    if (!ambient) return;
    ambient.volume = ambientVolume;
  }, [ambientVolume]);

  useEffect(() => {
    const ambient = ambientRef.current;
    if (!ambient || !ambientTrackUrl) return;
    if (isPlaying) {
      ambient.play().catch(() => {});
    } else {
      ambient.pause();
    }
  }, [isPlaying, ambientTrackUrl]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = volume;
  }, [volume]);

  const togglePlayPause = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
      return;
    }

    onPlayButtonClick?.();

    const currentChunk = sortedChunks[currentIndex];
    if (!currentChunk) return;

    const audioUrl = getChunkAudioUrl(currentChunk.id);
    if (!audioUrl) {
      const nextIdx = currentIndex + 1;
      if (nextIdx < sortedChunks.length) {
        setCurrentIndex(nextIdx);
        return;
      }
      return;
    }

    try {
      await audio.play();
      setIsPlaying(true);
    } catch (err) {
      setIsPlaying(false);
    }
  };

  const handleSeek = (e) => {
    const audio = audioRef.current;
    if (!audio || duration === 0) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * duration;

    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (e) => {
    setVolume(parseFloat(e.target.value));
  };

  const handleAmbientVolumeChange = (e) => {
    setAmbientVolume(parseFloat(e.target.value));
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const currentChunk = sortedChunks[currentIndex];
  const audioUrl = currentChunk ? getChunkAudioUrl(currentChunk.id) : null;
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
  const totalChunks = sortedChunks.length;
  const chunksWithAudio = sortedChunks.filter((c) =>
    chunkAudioMap.has(c.id)
  ).length;

  if (chunksWithAudio === 0) {
    return (
      <div className={styles.empty}>
        <p>No audio available. Assign voices and click Save to generate.</p>
      </div>
    );
  }

  return (
    <div className={styles.sequentialPlayer}>
      <audio ref={audioRef} />
      <audio ref={ambientRef} />

      <div className={styles.info}>
        <span className={styles.chunkInfo}>
          Segment {currentIndex + 1} of {totalChunks}
        </span>
        {currentChunk && (
          <span className={styles.roleLabel}>
            {currentChunk.role === "narrator"
              ? customNarratorName
                ? `Narrator (${customNarratorName})`
                : "Narrator"
              : customVoiceActorName
              ? `${
                  currentChunk.character_name || "Character"
                } (${customVoiceActorName})`
              : currentChunk.character_name || "Character"}
          </span>
        )}
      </div>

      <div className={styles.controlsRow}>
        <button
          type="button"
          className={styles.playBtn}
          onClick={togglePlayPause}
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? (
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        <span className={styles.timeCurrent}>{formatTime(currentTime)}</span>

        <div
          className={styles.progressBar}
          onClick={handleSeek}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              e.currentTarget.click();
            }
          }}
          aria-label="Seek"
        >
          <div className={styles.progressTrack}>
            <div
              className={styles.progress}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <span className={styles.timeTotal}>{formatTime(duration)}</span>

        <div className={styles.volumeWrap} title="Voice / narration volume">
          <span className={styles.volumeLabel}>Voice</span>
          <svg
            className={styles.volumeIcon}
            width="18"
            height="18"
            fill="currentColor"
            viewBox="0 0 24 24"
            aria-hidden
          >
            <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" />
          </svg>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={volume}
            onChange={handleVolumeChange}
            className={styles.volumeSlider}
            aria-label="Voice volume"
          />
        </div>
        {ambientTrackUrl && (
          <div
            className={styles.ambientVolumeWrap}
            title="Background / ambient music volume"
          >
            <span className={styles.volumeLabel}>Ambient</span>
            <svg
              className={styles.volumeIcon}
              width="18"
              height="18"
              fill="currentColor"
              viewBox="0 0 24 24"
              aria-hidden
            >
              <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
            </svg>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={ambientVolume}
              onChange={handleAmbientVolumeChange}
              className={styles.volumeSlider}
              aria-label="Ambient volume"
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default SequentialAudioPlayer;
