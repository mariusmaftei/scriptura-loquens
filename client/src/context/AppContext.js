import React, { createContext, useContext, useState, useCallback } from "react";
import { pdfAPI } from "../services/api";

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within AppProvider");
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [currentPDF, setCurrentPDF] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [voiceSettings, setVoiceSettings] = useState({});
  const [availableVoices, setAvailableVoices] = useState([]);
  const [audioFiles, setAudioFiles] = useState([]);
  const [ambientTracks, setAmbientTracks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const uploadPDF = useCallback(async (file) => {
    try {
      setLoading(true);
      setError(null);
      const result = await pdfAPI.uploadPDF(file);
      setCurrentPDF(result);
      return result;
    } catch (err) {
      const errorMessage =
        err.response?.data?.error ||
        err.response?.data?.message ||
        err.message ||
        "Failed to upload PDF";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const processPDF = useCallback(async (pdfId) => {
    try {
      setLoading(true);
      setError(null);
      const result = await pdfAPI.processPDF(pdfId);
      return result;
    } catch (err) {
      const errorMessage =
        err.response?.data?.error ||
        err.response?.data?.message ||
        err.message ||
        "Failed to process PDF";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPDFData = useCallback(async (pdfId) => {
    try {
      setLoading(true);
      setError(null);

      const [
        pdfData,
        chunksData,
        charactersData,
        voicesData,
        voiceSettingsData,
        audioData,
        ambientData,
      ] = await Promise.all([
        pdfAPI.getPDF(pdfId),
        pdfAPI.getChunks(pdfId).catch(() => []),
        pdfAPI.getCharacters(pdfId).catch(() => []),
        pdfAPI.getAvailableVoices(pdfId).catch(() => []),
        pdfAPI.getVoiceSettings(pdfId).catch(() => ({})),
        pdfAPI.getAudio(pdfId).catch(() => []),
        pdfAPI.getAmbientTracks(pdfId).catch(() => []),
      ]);

      setCurrentPDF(pdfData);
      setChunks(chunksData);
      setCharacters(charactersData);
      setAvailableVoices(voicesData);
      setVoiceSettings(voiceSettingsData);
      setAudioFiles(audioData);
      setAmbientTracks(ambientData);
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || "Failed to load PDF data";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateVoiceSettings = useCallback(async (pdfId, settings) => {
    try {
      setLoading(true);
      setError(null);
      const result = await pdfAPI.updateVoiceSettings(pdfId, settings);
      setVoiceSettings(result);
      return result;
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || "Failed to update voice settings";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const regenerateAudio = useCallback(
    async (pdfId) => {
      try {
        setLoading(true);
        setError(null);
        const result = await pdfAPI.regenerateAudio(pdfId);
        await loadPDFData(pdfId);
        return result;
      } catch (err) {
        const errorMessage =
          err.response?.data?.message || "Failed to regenerate audio";
        setError(errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [loadPDFData]
  );

  const loadAvailableVoices = useCallback(async (pdfId) => {
    try {
      const voicesData = await pdfAPI.getAvailableVoices(pdfId);
      setAvailableVoices(voicesData);
      return voicesData;
    } catch (err) {
      console.error("Failed to load voices:", err);
      throw err;
    }
  }, []);

  const uploadAmbient = useCallback(async (pdfId, file) => {
    try {
      const track = await pdfAPI.uploadAmbient(pdfId, file);
      setAmbientTracks((prev) => [track, ...prev]);
      return track;
    } catch (err) {
      const msg =
        err.response?.data?.error || err.message || "Failed to upload ambient";
      setError(msg);
      throw err;
    }
  }, []);

  const setSelectedAmbient = useCallback(async (pdfId, ambientTrackId) => {
    try {
      const id = typeof pdfId === "string" ? parseInt(pdfId, 10) : pdfId;
      await pdfAPI.setSelectedAmbient(pdfId, ambientTrackId);
      setCurrentPDF((prev) =>
        prev && prev.id === id
          ? { ...prev, selected_ambient_track_id: ambientTrackId }
          : prev
      );
    } catch (err) {
      const msg =
        err.response?.data?.error || err.message || "Failed to set ambient";
      setError(msg);
      throw err;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const reset = useCallback(() => {
    setCurrentPDF(null);
    setChunks([]);
    setCharacters([]);
    setVoiceSettings({});
    setAvailableVoices([]);
    setAudioFiles([]);
    setAmbientTracks([]);
    setError(null);
  }, []);

  const value = {
    currentPDF,
    chunks,
    characters,
    voiceSettings,
    availableVoices,
    audioFiles,
    ambientTracks,
    loading,
    error,
    uploadPDF,
    processPDF,
    loadPDFData,
    updateVoiceSettings,
    regenerateAudio,
    loadAvailableVoices,
    uploadAmbient,
    setSelectedAmbient,
    clearError,
    reset,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
