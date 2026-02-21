import React, { useState, useRef, useEffect } from "react";
import styles from "./AudioPlayer.module.css";
import Button from "../Button/Button";

const AudioPlayer = ({ audioUrl, title, onEnded }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [loadError, setLoadError] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    setLoadError(false);
  }, [audioUrl]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);
    const handleEnded = () => {
      setIsPlaying(false);
      onEnded?.();
    };
    const handleError = () => setLoadError(true);

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
  }, [onEnded]);

  const togglePlayPause = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
      return;
    }
    try {
      await audio.play();
      setIsPlaying(true);
    } catch (err) {
      setLoadError(true);
      setIsPlaying(false);
    }
  };

  const handleSeek = (e) => {
    const audio = audioRef.current;
    if (!audio) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * duration;

    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (!audioUrl) {
    return (
      <div className={styles.empty}>
        <p>No audio available. Assign voices and click Save to generate.</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={styles.audioPlayer}>
        {title && <h3 className={styles.title}>{title}</h3>}
        <div className={styles.empty}>
          <p>
            Unable to load audio. Save voices below to generate, or try another
            segment.
          </p>
        </div>
      </div>
    );
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className={styles.audioPlayer}>
      {title && <h3 className={styles.title}>{title}</h3>}

      <audio ref={audioRef} src={audioUrl} />

      <div className={styles.controls}>
        <Button
          variant="primary"
          size="md"
          onClick={togglePlayPause}
          className={styles.playButton}
        >
          {isPlaying ? (
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </Button>

        <div className={styles.progressContainer}>
          <div
            className={styles.progressBar}
            onClick={handleSeek}
            role="button"
            tabIndex={0}
            aria-label="Seek audio"
          >
            <div
              className={styles.progress}
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className={styles.timeDisplay}>
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        <div className={styles.volumeContainer}>
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
            <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
          </svg>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={volume}
            onChange={handleVolumeChange}
            className={styles.volumeSlider}
            aria-label="Volume"
          />
        </div>
      </div>
    </div>
  );
};

export default AudioPlayer;
