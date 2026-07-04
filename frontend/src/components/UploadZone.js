import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";
import { uploadPaper } from "../api";

export default function UploadZone({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [lastResult, setLastResult] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;
    if (!file.name.endsWith(".pdf")) {
      toast.error("Only PDF files are supported");
      return;
    }

    setUploading(true);
    setProgress(0);
    setLastResult(null);

    const toastId = toast.loading(`Ingesting "${file.name}"...`);

    try {
      const { data } = await uploadPaper(file, (pct) => setProgress(pct));
      console.log("[upload] success response:", data);
      setLastResult(data);
      toast.success(`"${data.paper_name}" added to memory!`, { id: toastId });
      onUploadComplete();
    } catch (e) {
      console.error("[upload] error:", e);
      console.error("[upload] response status:", e.response?.status);
      console.error("[upload] response data:", e.response?.data);
      console.error("[upload] message:", e.message);
      const msg = e.response?.data?.detail || e.message || "Upload failed";
      toast.error(msg, { id: toastId });
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: false,
    disabled: uploading,
  });

  return (
    <div style={styles.wrapper}>
      <h2 style={styles.heading}>Upload a Research Paper</h2>
      <p style={styles.sub}>
        Drop a PDF and ChronoResearch will extract, chunk, and build a knowledge graph from it.
      </p>

      <div
        {...getRootProps()}
        style={{
          ...styles.dropzone,
          borderColor: isDragActive ? "#6366f1" : uploading ? "#333" : "#2a2a2a",
          background: isDragActive ? "#1e1b4b22" : "#1a1a1a",
          cursor: uploading ? "not-allowed" : "pointer",
        }}
      >
        <input {...getInputProps()} />
        <Upload size={32} color={isDragActive ? "#6366f1" : "#444"} />
        {isDragActive ? (
          <p style={styles.dropText}>Drop it here...</p>
        ) : uploading ? (
          <p style={styles.dropText}>Ingesting into memory...</p>
        ) : (
          <>
            <p style={styles.dropText}>Drag & drop a PDF here, or click to browse</p>
            <p style={styles.dropHint}>Supports any text-based PDF</p>
          </>
        )}
      </div>

      {/* Progress bar */}
      {uploading && (
        <div style={styles.progressWrap}>
          <div style={styles.progressTrack}>
            <div style={{ ...styles.progressFill, width: `${progress}%` }} />
          </div>
          <span style={styles.progressLabel}>{progress}% uploaded</span>
        </div>
      )}

      {/* Result card */}
      {lastResult && !uploading && (
        <div style={styles.resultCard}>
          <CheckCircle size={18} color="#22c55e" />
          <div>
            <div style={styles.resultTitle}>
              <FileText size={14} color="#6366f1" />
              {lastResult.paper_name.replace(/_/g, " ")}
            </div>
            <div style={styles.resultMeta}>
              {lastResult.chunks} chunks ingested &nbsp;·&nbsp;
              {lastResult.nodes} nodes &nbsp;·&nbsp;
              {lastResult.edges} edges in graph
            </div>
          </div>
        </div>
      )}

      {/* How it works */}
      {!lastResult && !uploading && (
        <div style={styles.steps}>
          {["Extract text from every page", "Split into 500-word chunks", "Build knowledge graph with Cognee", "Ask questions across all papers"].map((s, i) => (
            <div key={i} style={styles.step}>
              <div style={styles.stepNum}>{i + 1}</div>
              <span style={styles.stepText}>{s}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  wrapper: { maxWidth: 640, margin: "0 auto" },
  heading: { fontSize: 22, fontWeight: 700, color: "#f0f0f0", marginBottom: 6 },
  sub: { fontSize: 14, color: "#666", marginBottom: 24, lineHeight: 1.5 },
  dropzone: {
    border: "2px dashed",
    borderRadius: 12,
    padding: "48px 32px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 12,
    transition: "border-color 0.2s, background 0.2s",
  },
  dropText: { fontSize: 15, color: "#aaa", margin: 0, textAlign: "center" },
  dropHint: { fontSize: 12, color: "#555", margin: 0 },
  progressWrap: {
    marginTop: 16,
    display: "flex",
    alignItems: "center",
    gap: 12,
  },
  progressTrack: {
    flex: 1,
    height: 6,
    background: "#222",
    borderRadius: 99,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    background: "linear-gradient(90deg, #6366f1, #818cf8)",
    borderRadius: 99,
    transition: "width 0.3s ease",
  },
  progressLabel: { fontSize: 12, color: "#666", whiteSpace: "nowrap" },
  resultCard: {
    marginTop: 20,
    background: "#0f2a1a",
    border: "1px solid #166534",
    borderRadius: 10,
    padding: "14px 16px",
    display: "flex",
    alignItems: "flex-start",
    gap: 12,
    animation: "fadeIn 0.3s ease",
  },
  resultTitle: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 14,
    fontWeight: 600,
    color: "#d0d0d0",
    textTransform: "capitalize",
    marginBottom: 4,
  },
  resultMeta: { fontSize: 12, color: "#666" },
  steps: {
    marginTop: 32,
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 12,
  },
  step: {
    background: "#1a1a1a",
    border: "1px solid #222",
    borderRadius: 10,
    padding: "14px 16px",
    display: "flex",
    alignItems: "flex-start",
    gap: 10,
  },
  stepNum: {
    width: 22,
    height: 22,
    borderRadius: "50%",
    background: "#1e1b4b",
    border: "1px solid #3730a3",
    color: "#818cf8",
    fontSize: 11,
    fontWeight: 700,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  stepText: { fontSize: 13, color: "#888", lineHeight: 1.4 },
};
