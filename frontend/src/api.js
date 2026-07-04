import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000" });

export const uploadPaper = (file, onProgress) => {
  const form = new FormData();
  form.append("file", file);
  console.log("[upload] sending file:", file.name, "size:", file.size, "type:", file.type);
  return api.post("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      const pct = Math.round((e.loaded * 100) / e.total);
      console.log("[upload] progress:", pct + "%");
      onProgress && onProgress(pct);
    },
  });
};

export const recallFromPapers = (question) =>
  api.post("/recall", { question });

export const improveMemory = (dataset = "main_dataset") =>
  api.post("/improve", { dataset });

export const deletePaper = (paperName) =>
  api.delete(`/paper/${encodeURIComponent(paperName)}`);

export const fetchPapers = () => api.get("/papers");

export const fetchStats = () => api.get("/stats");

export const fetchHealth = () => api.get("/health");
