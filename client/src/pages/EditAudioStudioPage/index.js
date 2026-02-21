import React, { useState, useEffect, useRef, useCallback } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { pdfAPI, getAudioFileUrl } from "../../services/api";
import Container from "../../components/Container/Container";
import styles from "./EditAudioStudioPage.module.css";

const FILTER_ALL = "all";
const FILTER_NARRATOR = "narrator";
const FILTER_VOICE_ACTOR = "voice_actor";

const getRoleLabel = (chunk) =>
  chunk.role === "narrator" ? "Narator" : chunk.character_name || "Personaj";

const EditAudioStudioPage = () => {
  const { pdfId } = useParams();
  const navigate = useNavigate();
  const [pdf, setPdf] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [audioFiles, setAudioFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploadingChunkId, setUploadingChunkId] = useState(null);
  const [recordingChunkId, setRecordingChunkId] = useState(null);
  const [roleFilter, setRoleFilter] = useState(FILTER_ALL);
  const [narratorName, setNarratorName] = useState("");
  const [voiceActorName, setVoiceActorName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [expandedChunkId, setExpandedChunkId] = useState(null);
  const [previewChunkId, setPreviewChunkId] = useState(null);
  const [countdownValue, setCountdownValue] = useState(null);
  const [pendingRecordChunkId, setPendingRecordChunkId] = useState(null);
  const fileInputRefs = useRef({});
  const mediaRecorderRef = useRef(null);
  const previewAudioRef = useRef(null);
  const waveformCanvasRef = useRef(null);
  const waveformCleanupRef = useRef(null);
  const countdownTimerRef = useRef(null);
  const recordingStreamRef = useRef(null);
  const previewCacheBustRef = useRef(0);
  const chunksRef = useRef([]);

  const loadData = useCallback(async () => {
    if (!pdfId) return;
    try {
      setLoading(true);
      setError(null);
      const [pdfData, chunksData, audioData] = await Promise.all([
        pdfAPI.getPDF(pdfId),
        pdfAPI.getChunks(pdfId),
        pdfAPI.getAudio(pdfId).catch(() => []),
      ]);
      setPdf(pdfData);
      const sorted = (chunksData || []).sort((a, b) => a.position - b.position);
      setChunks(sorted);
      setAudioFiles(audioData || []);
      chunksRef.current = sorted;
      setNarratorName(pdfData.custom_narrator_name || "");
      setVoiceActorName(pdfData.custom_voice_actor_name || "");
    } catch (err) {
      setError(err.response?.data?.error || "Eroare la încărcarea documentului");
    } finally {
      setLoading(false);
    }
  }, [pdfId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const chunkHasCustomAudio = (chunkId) =>
    audioFiles.some((a) => a.chunk_id === chunkId && a.voice_id === "custom");

  const getCustomAudioForChunk = (chunkId) =>
    audioFiles.find((a) => a.chunk_id === chunkId && a.voice_id === "custom");

  const handlePreviewToggle = (chunkId) => {
    const audio = previewAudioRef.current;
    if (!audio) return;
    if (previewChunkId === chunkId) {
      audio.pause();
      audio.currentTime = 0;
      setPreviewChunkId(null);
      return;
    }
    const custom = getCustomAudioForChunk(chunkId);
    if (!custom) return;
    const url = `${getAudioFileUrl(custom.id)}?v=${
      previewCacheBustRef.current || Date.now()
    }`;
    audio.src = url;
    audio.onended = () => setPreviewChunkId(null);
    audio.play().catch(() => setPreviewChunkId(null));
    setPreviewChunkId(chunkId);
  };

  const handleFileSelect = async (chunkId, e) => {
    const file = e?.target?.files?.[0];
    if (!file || !pdfId) return;
    e.target.value = "";
    try {
      setUploadingChunkId(chunkId);
      const result = await pdfAPI.uploadCustomChunkAudio(pdfId, chunkId, file);
      setAudioFiles((prev) => {
        const rest = prev.filter(
          (a) => !(a.chunk_id === chunkId && a.voice_id === "custom")
        );
        return [...rest, result];
      });
      previewCacheBustRef.current = Date.now();
      setExpandedChunkId(null);
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploadingChunkId(null);
    }
  };

  useEffect(() => {
    if (countdownValue === null || pendingRecordChunkId === null) return;
    if (countdownValue > 1) {
      countdownTimerRef.current = setTimeout(
        () => setCountdownValue((v) => v - 1),
        1000
      );
      return () => clearTimeout(countdownTimerRef.current);
    }
    countdownTimerRef.current = setTimeout(() => {
      setCountdownValue(null);
      const id = pendingRecordChunkId;
      setPendingRecordChunkId(null);
      startRecordingForChunk(id);
    }, 1000);
    return () => clearTimeout(countdownTimerRef.current);
  }, [countdownValue, pendingRecordChunkId]);

  const startWaveformVisualization = (stream, canvasEl) => {
    if (!canvasEl || !stream) return () => {};
    const ctx = canvasEl.getContext("2d");
    if (!ctx) return () => {};
    let audioContext;
    try {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
      return () => {};
    }
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.7;
    source.connect(analyser);
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    let animationId;
    const W = canvasEl.width;
    const H = canvasEl.height;
    const barCount = Math.min(32, analyser.frequencyBinCount);
    const barWidth = Math.max(2, W / barCount - 2);

    const draw = () => {
      animationId = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);
      ctx.fillStyle = "rgba(241, 235, 226, 0.15)";
      ctx.fillRect(0, 0, W, H);
      for (let i = 0; i < barCount; i++) {
        const v = dataArray[Math.floor((i / barCount) * dataArray.length)] || 0;
        const h = Math.max(4, (v / 255) * H * 0.8);
        const x = (W / barCount) * i + 1;
        ctx.fillStyle = "#8b7355";
        ctx.fillRect(x, (H - h) / 2, barWidth, h);
      }
    };
    draw();

    return () => {
      cancelAnimationFrame(animationId);
      try {
        audioContext.close();
      } catch (_) {}
    };
  };

  const startRecordingForChunk = async (chunkId) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recordingStreamRef.current = stream;
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream);
      const chunks = [];
      recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        recordingStreamRef.current = null;
        waveformCleanupRef.current?.();
        waveformCleanupRef.current = null;
        const blob = new Blob(chunks, { type: mime });
        const ext = mime.includes("webm") ? ".webm" : ".mp3";
        const file = new File([blob], `record_${chunkId}${ext}`, {
          type: blob.type,
        });
        try {
          setUploadingChunkId(chunkId);
          const result = await pdfAPI.uploadCustomChunkAudio(
            pdfId,
            chunkId,
            file
          );
          setAudioFiles((prev) => {
            const rest = prev.filter(
              (a) => !(a.chunk_id === chunkId && a.voice_id === "custom")
            );
            return [...rest, result];
          });
          previewCacheBustRef.current = Date.now();
          setExpandedChunkId(null);
        } catch (err) {
          console.error("Upload recording failed:", err);
        } finally {
          setUploadingChunkId(null);
        }
      };
      mediaRecorderRef.current = recorder;
      recorder.start(200);
      setRecordingChunkId(chunkId);
      requestAnimationFrame(() => {
        waveformCleanupRef.current = startWaveformVisualization(
          stream,
          waveformCanvasRef.current
        );
      });
    } catch (err) {
      console.error("Microphone access failed:", err);
    }
  };

  const startRecording = (chunkId) => {
    if (recordingChunkId || countdownValue !== null) return;
    setPendingRecordChunkId(chunkId);
    setCountdownValue(3);
  };

  const stopRecording = () => {
    if (countdownValue !== null) {
      clearTimeout(countdownTimerRef.current);
      setCountdownValue(null);
      setPendingRecordChunkId(null);
      return;
    }
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    recordingStreamRef.current?.getTracks().forEach((t) => t.stop());
    recordingStreamRef.current = null;
    waveformCleanupRef.current?.();
    waveformCleanupRef.current = null;
    setRecordingChunkId(null);
  };

  const sortedChunks = [...chunks].sort((a, b) => a.position - b.position);
  const filteredChunks =
    roleFilter === FILTER_NARRATOR
      ? sortedChunks.filter((c) => c.role === "narrator")
      : roleFilter === FILTER_VOICE_ACTOR
      ? sortedChunks.filter((c) => c.role !== "narrator")
      : sortedChunks;

  const allHaveCustom =
    sortedChunks.length > 0 &&
    sortedChunks.every((c) => chunkHasCustomAudio(c.id));
  const canSubmit = allHaveCustom;

  const handleSubmit = async () => {
    if (!canSubmit || !pdfId) return;
    try {
      setSubmitting(true);
      await pdfAPI.updateCustomVoiceNames(pdfId, {
        custom_narrator_name: narratorName.trim() || null,
        custom_voice_actor_name: voiceActorName.trim() || null,
      });
      navigate(`/documents/${pdfId}`);
    } catch (err) {
      console.error("Submit failed:", err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Container>
        <div className={styles.page}>
          <div className={styles.loading}>Se încarcă...</div>
        </div>
      </Container>
    );
  }

  if (error || !pdf) {
    return (
      <Container>
        <div className={styles.page}>
          <div className={styles.error}>{error || "Document negăsit"}</div>
          <Link to="/post-productie" className={styles.backLink}>
            ← Înapoi la Post-producție
          </Link>
        </div>
      </Container>
    );
  }

  return (
    <Container>
      <audio ref={previewAudioRef} style={{ display: "none" }} />
      <div className={styles.page}>
        <div className={styles.header}>
          <Link to="/post-productie" className={styles.backLink}>
            ← Înapoi la Post-producție
          </Link>
          <h1 className={styles.title}>Editare custom – Studio</h1>
          <p className={styles.subtitle}>
            Atașează sau înregistrează propriul tău audio pentru fiecare
            segment. Audio-ul custom înlocuiește TTS la redare.
          </p>
          <p className={styles.docName}>
            {(pdf.filename || "").replace(/\.pdf$/i, "")}
          </p>

          <div className={styles.nameInputs}>
            <label className={styles.nameLabel}>
              <span>Nume narator</span>
              <input
                type="text"
                className={styles.nameInput}
                placeholder="ex. Ion Popescu"
                value={narratorName}
                onChange={(e) => setNarratorName(e.target.value)}
              />
            </label>
            <label className={styles.nameLabel}>
              <span>Nume actor voce</span>
              <input
                type="text"
                className={styles.nameInput}
                placeholder="ex. Maria Ionescu"
                value={voiceActorName}
                onChange={(e) => setVoiceActorName(e.target.value)}
              />
            </label>
          </div>
          <p className={styles.nameHint}>
            Aceste nume vor apărea în vizualizarea documentului pentru a găsi
            înregistrarea ta custom.
          </p>

          <div className={styles.filterRow}>
            <span className={styles.filterLabel}>Afișează:</span>
            <div className={styles.filterButtons}>
              <button
                type="button"
                className={
                  roleFilter === FILTER_ALL
                    ? styles.filterBtnActive
                    : styles.filterBtn
                }
                onClick={() => setRoleFilter(FILTER_ALL)}
              >
                Toate
              </button>
              <button
                type="button"
                className={
                  roleFilter === FILTER_NARRATOR
                    ? styles.filterBtnActive
                    : styles.filterBtn
                }
                onClick={() => setRoleFilter(FILTER_NARRATOR)}
              >
                Narator
              </button>
              <button
                type="button"
                className={
                  roleFilter === FILTER_VOICE_ACTOR
                    ? styles.filterBtnActive
                    : styles.filterBtn
                }
                onClick={() => setRoleFilter(FILTER_VOICE_ACTOR)}
              >
                Actor voce
              </button>
            </div>
          </div>
        </div>

        <div className={styles.segmentList}>
          {filteredChunks.map((chunk) => {
            const isUploading = uploadingChunkId === chunk.id;
            const isRecording = recordingChunkId === chunk.id;
            const hasCustom = chunkHasCustomAudio(chunk.id);
            const isExpanded = expandedChunkId === chunk.id;
            const showCollapsed = hasCustom && !isExpanded;
            const text = chunk.text || "";
            const truncated = text.length > 80 ? `${text.slice(0, 80)}…` : text;
            return (
              <div
                key={chunk.id}
                className={`${styles.segment} ${
                  showCollapsed ? styles.segmentCollapsed : ""
                } ${hasCustom ? styles.segmentHasCustom : ""}`}
              >
                {showCollapsed ? (
                  <div className={styles.collapsedRow}>
                    <span className={styles.roleLabel}>
                      {getRoleLabel(chunk)}
                    </span>
                    <span className={styles.badge}>Audio custom</span>
                    <span className={styles.collapsedText}>{truncated}</span>
                    <button
                      type="button"
                      className={
                        previewChunkId === chunk.id
                          ? styles.previewBtnActive
                          : styles.previewBtn
                      }
                      onClick={() => handlePreviewToggle(chunk.id)}
                      aria-label={
                        previewChunkId === chunk.id
                          ? "Oprește previzualizare"
                          : "Redă previzualizare"
                      }
                    >
                      {previewChunkId === chunk.id ? (
                        <>
                          <span className={styles.recordDot} />
                          Oprește
                        </>
                      ) : (
                        <>
                          <svg
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="currentColor"
                          >
                            <path d="M8 5v14l11-7z" />
                          </svg>
                          Redă
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      className={styles.replaceBtn}
                      onClick={() => setExpandedChunkId(chunk.id)}
                    >
                      Înlocuiește
                    </button>
                  </div>
                ) : (
                  <>
                    <div className={styles.segmentHeader}>
                      <span className={styles.roleLabel}>
                        {getRoleLabel(chunk)}
                      </span>
                      {hasCustom && (
                        <span className={styles.badge}>Audio custom</span>
                      )}
                    </div>
                    <p className={styles.segmentText}>{text}</p>
                    <div className={styles.segmentActions}>
                      {pendingRecordChunkId === chunk.id &&
                      countdownValue !== null ? (
                        <div className={styles.countdownWrap}>
                          <span className={styles.countdownNum}>
                            {countdownValue}
                          </span>
                          <span className={styles.countdownLabel}>
                            Pregătește-te…
                          </span>
                          <button
                            type="button"
                            className={styles.cancelCountdownBtn}
                            onClick={stopRecording}
                          >
                            Anulează
                          </button>
                        </div>
                      ) : recordingChunkId === chunk.id ? (
                        <div className={styles.recordingWrap}>
                          <canvas
                            ref={waveformCanvasRef}
                            className={styles.waveformCanvas}
                            width={280}
                            height={48}
                          />
                          <button
                            type="button"
                            className={styles.recordBtnActive}
                            onClick={stopRecording}
                            aria-label="Oprește înregistrarea"
                          >
                            <span className={styles.recordDot} />
                            Oprește
                          </button>
                        </div>
                      ) : (
                        <>
                          <input
                            ref={(el) => (fileInputRefs.current[chunk.id] = el)}
                            type="file"
                            accept=".mp3,.wav,.m4a,.ogg,.webm,audio/*"
                            className={styles.fileInput}
                            onChange={(e) => handleFileSelect(chunk.id, e)}
                          />
                          <button
                            type="button"
                            className={styles.attachBtn}
                            onClick={() =>
                              fileInputRefs.current[chunk.id]?.click()
                            }
                            disabled={isUploading || isRecording}
                          >
                            {isUploading ? "Se încarcă…" : "Atașează fișier"}
                          </button>
                          <button
                            type="button"
                            className={styles.recordBtn}
                            onClick={() => startRecording(chunk.id)}
                            disabled={
                              isUploading ||
                              countdownValue !== null ||
                              !!recordingChunkId
                            }
                            aria-label="Înregistrează"
                          >
                            <svg
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="currentColor"
                            >
                              <circle cx="12" cy="12" r="6" />
                            </svg>
                            Înregistrează
                          </button>
                          {hasCustom && (
                            <>
                              <button
                                type="button"
                                className={
                                  previewChunkId === chunk.id
                                    ? styles.previewBtnActive
                                    : styles.previewBtn
                                }
                                onClick={() => handlePreviewToggle(chunk.id)}
                                aria-label={
                                  previewChunkId === chunk.id
                                    ? "Oprește previzualizare"
                                    : "Redă previzualizare"
                                }
                              >
                                {previewChunkId === chunk.id ? (
                                  <>
                                    <span className={styles.recordDot} />
                                    Oprește
                                  </>
                                ) : (
                                  <>
                                    <svg
                                      width="14"
                                      height="14"
                                      viewBox="0 0 24 24"
                                      fill="currentColor"
                                    >
                                      <path d="M8 5v14l11-7z" />
                                    </svg>
                                    Previzualizare
                                  </>
                                )}
                              </button>
                              <button
                                type="button"
                                className={styles.collapseBtn}
                                onClick={() => setExpandedChunkId(null)}
                              >
                                Restrânge
                              </button>
                            </>
                          )}
                        </>
                      )}
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>

        <div className={styles.submitRow}>
          {!allHaveCustom && sortedChunks.length > 0 && (
            <p className={styles.submitHint}>
              Atașează sau înregistrează audio pentru fiecare segment pentru a
              trimite.
            </p>
          )}
          <button
            type="button"
            className={styles.submitBtn}
            onClick={handleSubmit}
            disabled={!canSubmit || submitting}
          >
            {submitting ? "Se salvează…" : "Trimite și deschide documentul"}
          </button>
        </div>
      </div>
    </Container>
  );
};

export default EditAudioStudioPage;
