import axios from "axios";

export const API_BASE_URL =
  process.env.REACT_APP_API_URL || "http://localhost:8000/api";

export const getAudioFileUrl = (audioId) =>
  `${API_BASE_URL}/audio/${audioId}/file`;

export const getAmbientFileUrl = (ambientId) =>
  `${API_BASE_URL}/ambient/${ambientId}/file`;

export const getBookCoverUrl = (pdf) =>
  pdf?.book_cover_path && pdf?.id
    ? `${API_BASE_URL}/pdf/${pdf.id}/book-cover`
    : null;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (res) => res,
  (err) => Promise.reject(err),
);

export const pdfAPI = {
  uploadPDF: async (file, options = {}) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("use_ai", "false");
    formData.append("pipeline", "bible");
    if (options.bookKey) formData.append("book_key", options.bookKey);
    if (options.bookDisplayName) formData.append("book_display_name", options.bookDisplayName);
    if (options.bookAuthor) formData.append("book_author", options.bookAuthor);
    if (options.bookGenre) formData.append("book_genre", options.bookGenre);
    if (options.cover) formData.append("cover", options.cover);

    const response = await api.post("/upload-pdf", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  getPDF: async (pdfId) => {
    const response = await api.get(`/pdf/${pdfId}`);
    return response.data;
  },

  updateCustomVoiceNames: async (pdfId, names) => {
    const response = await api.put(`/pdf/${pdfId}/custom-voice-names`, names);
    return response.data;
  },

  getPDFText: async (pdfId) => {
    const response = await api.get(`/pdf/${pdfId}/text`);
    return response.data;
  },

  processPDF: async (pdfId) => {
    const response = await api.post(`/pdf/${pdfId}/process`);
    return response.data;
  },

  getChunks: async (pdfId) => {
    const response = await api.get(`/pdf/${pdfId}/chunks`);
    return response.data;
  },

  getCharacters: async (pdfId) => {
    const response = await api.get(`/pdf/${pdfId}/characters`);
    return response.data;
  },

  getAvailableVoices: async (pdfId) => {
    const response = await api.get(`/pdf/${pdfId}/voices`);
    return response.data;
  },

  getVoiceSettings: async (pdfId) => {
    const response = await api.get(`/pdf/${pdfId}/voice-settings`);
    return response.data;
  },

  updateVoiceSettings: async (pdfId, settings) => {
    const response = await api.put(`/pdf/${pdfId}/voice-settings`, settings);
    return response.data;
  },

  regenerateAudio: async (pdfId) => {
    const response = await api.post(`/pdf/${pdfId}/regenerate-audio`);
    return response.data;
  },

  getAudio: async (pdfId) => {
    const response = await api.get(`/pdf/${pdfId}/audio`);
    return response.data;
  },

  uploadCustomChunkAudio: async (pdfId, chunkId, file) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post(
      `/pdf/${pdfId}/chunks/${chunkId}/custom-audio`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return response.data;
  },

  listPDFs: async () => {
    const response = await api.get("/pdfs");
    return response.data;
  },

  deletePDF: async (pdfId) => {
    const response = await api.delete(`/pdf/${pdfId}`);
    return response.data;
  },

  analyzePDFJson: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post("/analyze-pdf-json", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  getAmbientTracks: async (pdfId) => {
    const response = await api.get(`/pdf/${pdfId}/ambient`);
    return response.data;
  },

  uploadAmbient: async (pdfId, file) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post(`/pdf/${pdfId}/ambient`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  setSelectedAmbient: async (pdfId, ambientTrackId) => {
    const response = await api.put(`/pdf/${pdfId}/ambient/selected`, {
      ambient_track_id: ambientTrackId,
    });
    return response.data;
  },

  cloneVoice: async (
    audioFile,
    voiceName,
    description,
    removeBackgroundNoise,
  ) => {
    const formData = new FormData();
    formData.append("audio_file", audioFile);
    formData.append("voice_name", voiceName);
    if (description) {
      formData.append("description", description);
    }
    formData.append(
      "remove_background_noise",
      removeBackgroundNoise ? "true" : "false",
    );

    const response = await api.post("/voices/clone", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },
};

export default api;
