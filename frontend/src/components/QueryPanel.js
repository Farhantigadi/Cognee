import { useState } from "react";
import { Search, ThumbsUp, ThumbsDown, BookOpen, Tag, Clock } from "lucide-react";
import toast from "react-hot-toast";
import { recallFromPapers, improveMemory } from "../api";

export default function QueryPanel({ papers }) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [feedbackGiven, setFeedbackGiven] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setResult(null);
    setFeedbackGiven(false);

    try {
      const { data } = await recallFromPapers(question.trim());
      setResult(data);
      setHistory((prev) =>
        [{ question: question.trim(), answer: data.answer, sources: data.sources }, ...prev].slice(0, 5)
      );
    } catch (e) {
      toast.error(e.response?.data?.detail || "Query failed");
    } finally {
      setLoading(false);
    }
  };

  const handleThumbsUp = async () => {
    if (feedbackGiven || !result?.sources?.length) return;
    setFeedbackGiven(true);
    try {
      await Promise.all(result.sources.map((s) => improveMemory(s)));
      toast.success("Memory improved! ✨", { icon: "🧠" });
    } catch {
      // silent — improve is best-effort
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleAsk();
  };

  const noPapers = papers.length === 0;

  return (
    <div style={styles.wrapper}>
      <h2 style={styles.heading}>Ask Across All Papers</h2>
      <p style={styles.sub}>
        {noPapers
          ? "Upload at least one paper to start asking questions."
          : `Searching across ${papers.length} paper${papers.length !== 1 ? "s" : ""} in memory.`}
      </p>

      {/* Input */}
      <div style={styles.inputRow}>
        <textarea
          style={{ ...styles.textarea, opacity: noPapers ? 0.4 : 1 }}
          placeholder={"Ask a question across all your papers...\n\nExamples:\n• How did attention mechanisms evolve?\n• What is the relationship between BERT and GPT?\n• Which papers discuss scaling limitations?"}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={noPapers || loading}
          rows={4}
        />
        <button
          style={{
            ...styles.askBtn,
            opacity: !question.trim() || noPapers || loading ? 0.4 : 1,
            cursor: !question.trim() || noPapers || loading ? "not-allowed" : "pointer",
          }}
          onClick={handleAsk}
          disabled={!question.trim() || noPapers || loading}
        >
          <Search size={16} />
          {loading ? "Searching..." : "Ask"}
        </button>
      </div>
      <p style={styles.hint}>Ctrl+Enter to submit</p>

      {/* Loading skeleton */}
      {loading && <AnswerSkeleton />}

      {/* Answer card */}
      {result && !loading && (
        <div style={styles.answerCard}>
          {/* Confidence bar */}
          <div style={styles.confidenceRow}>
            <span style={styles.confidenceLabel}>Confidence</span>
            <div style={styles.confidenceTrack}>
              <div style={{ ...styles.confidenceFill, width: `${(result.confidence ?? 0) * 100}%` }} />
            </div>
            <span style={styles.confidencePct}>{Math.round((result.confidence ?? 0) * 100)}%</span>
          </div>

          {/* Answer text */}
          <div style={styles.answerText}>
            {result.answer || "No answer found. Try rephrasing or upload more papers."}
          </div>

          {/* Sources + Concepts */}
          <div style={styles.metaRow}>
            {result.sources?.length > 0 && (
              <div style={styles.metaSection}>
                <div style={styles.metaLabel}>
                  <BookOpen size={12} /> Sources
                </div>
                <div style={styles.tagRow}>
                  {result.sources.map((s) => (
                    <span key={s} style={styles.sourceTag}>{s.replace(/_/g, " ")}</span>
                  ))}
                </div>
              </div>
            )}
            {result.related_concepts?.length > 0 && (
              <div style={styles.metaSection}>
                <div style={styles.metaLabel}>
                  <Tag size={12} /> Related Concepts
                </div>
                <div style={styles.tagRow}>
                  {result.related_concepts.slice(0, 8).map((c) => (
                    <span key={c} style={styles.conceptTag}>{c}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Feedback */}
          <div style={styles.feedbackRow}>
            <span style={styles.feedbackLabel}>Was this helpful?</span>
            <button
              style={{ ...styles.feedbackBtn, ...(feedbackGiven ? styles.feedbackBtnActive : {}) }}
              onClick={handleThumbsUp}
              disabled={feedbackGiven}
              title="Good answer — improve memory"
            >
              <ThumbsUp size={14} />
            </button>
            <button
              style={styles.feedbackBtn}
              onClick={() => setFeedbackGiven(true)}
              title="Poor answer"
            >
              <ThumbsDown size={14} />
            </button>
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div style={styles.historySection}>
          <div style={styles.historyLabel}>
            <Clock size={13} /> Recent Questions
          </div>
          {history.map((item, i) => (
            <div
              key={i}
              style={styles.historyItem}
              onClick={() => setQuestion(item.question)}
              title="Click to re-ask"
            >
              <div style={styles.historyQ}>{item.question}</div>
              {item.answer && (
                <div style={styles.historyA}>
                  {item.answer.slice(0, 100)}{item.answer.length > 100 ? "..." : ""}
                </div>
              )}
              {item.sources?.length > 0 && (
                <div style={styles.historySources}>
                  {item.sources.map((s) => (
                    <span key={s} style={styles.historySourceTag}>{s.replace(/_/g, " ")}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AnswerSkeleton() {
  return (
    <div style={skeletonStyles.card}>
      {[100, 80, 60].map((w, i) => (
        <div key={i} style={{ ...skeletonStyles.line, width: `${w}%`, animationDelay: `${i * 0.1}s` }} />
      ))}
    </div>
  );
}

const styles = {
  wrapper: { maxWidth: 720, margin: "0 auto" },
  heading: { fontSize: 22, fontWeight: 700, color: "#f0f0f0", marginBottom: 6 },
  sub: { fontSize: 14, color: "#666", marginBottom: 20 },
  inputRow: { display: "flex", gap: 10, alignItems: "flex-start" },
  textarea: {
    flex: 1,
    background: "#1a1a1a",
    border: "1px solid #2a2a2a",
    borderRadius: 10,
    color: "#e0e0e0",
    fontSize: 14,
    padding: "12px 14px",
    resize: "none",
    fontFamily: "inherit",
    lineHeight: 1.6,
    outline: "none",
    transition: "border-color 0.2s",
  },
  askBtn: {
    display: "flex",
    alignItems: "center",
    gap: 7,
    background: "#6366f1",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    padding: "12px 20px",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    whiteSpace: "nowrap",
    transition: "opacity 0.2s",
  },
  hint: { fontSize: 11, color: "#444", marginTop: 6, marginBottom: 0 },
  answerCard: {
    marginTop: 20,
    background: "#1a1a1a",
    border: "1px solid #2a2a2a",
    borderLeft: "3px solid #6366f1",
    borderRadius: "0 10px 10px 0",
    padding: "18px 20px",
    animation: "fadeIn 0.3s ease",
  },
  confidenceRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 14,
  },
  confidenceLabel: { fontSize: 11, color: "#555", whiteSpace: "nowrap" },
  confidenceTrack: {
    flex: 1,
    height: 4,
    background: "#2a2a2a",
    borderRadius: 99,
    overflow: "hidden",
  },
  confidenceFill: {
    height: "100%",
    background: "linear-gradient(90deg, #6366f1, #818cf8)",
    borderRadius: 99,
    transition: "width 0.5s ease",
  },
  confidencePct: { fontSize: 11, color: "#6366f1", fontWeight: 600, whiteSpace: "nowrap" },
  answerText: {
    fontSize: 15,
    color: "#d0d0d0",
    lineHeight: 1.7,
    marginBottom: 16,
  },
  metaRow: { display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 16 },
  metaSection: { flex: 1, minWidth: 200 },
  metaLabel: {
    display: "flex",
    alignItems: "center",
    gap: 5,
    fontSize: 11,
    color: "#555",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    marginBottom: 6,
  },
  tagRow: { display: "flex", flexWrap: "wrap", gap: 5 },
  sourceTag: {
    background: "#1e1b4b",
    color: "#a5b4fc",
    border: "1px solid #3730a3",
    borderRadius: 99,
    padding: "3px 10px",
    fontSize: 11,
    textTransform: "capitalize",
  },
  conceptTag: {
    background: "#2d1b4b",
    color: "#c4b5fd",
    border: "1px solid #5b21b6",
    borderRadius: 99,
    padding: "3px 10px",
    fontSize: 11,
  },
  feedbackRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    borderTop: "1px solid #222",
    paddingTop: 12,
  },
  feedbackLabel: { fontSize: 12, color: "#555", marginRight: 4 },
  feedbackBtn: {
    background: "#222",
    border: "1px solid #333",
    borderRadius: 6,
    padding: "5px 10px",
    cursor: "pointer",
    color: "#666",
    display: "flex",
    alignItems: "center",
    transition: "all 0.15s",
  },
  feedbackBtnActive: {
    background: "#1e1b4b",
    borderColor: "#6366f1",
    color: "#818cf8",
  },
  historySection: { marginTop: 32 },
  historyLabel: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 12,
    color: "#555",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    marginBottom: 10,
  },
  historyItem: {
    background: "#161616",
    border: "1px solid #222",
    borderRadius: 8,
    padding: "10px 14px",
    marginBottom: 6,
    cursor: "pointer",
    transition: "border-color 0.15s",
  },
  historyQ: { fontSize: 13, fontWeight: 500, color: "#bbb", marginBottom: 4 },
  historyA: { fontSize: 12, color: "#555", lineHeight: 1.4, marginBottom: 4 },
  historySources: { display: "flex", gap: 4, flexWrap: "wrap" },
  historySourceTag: {
    background: "#1a1a2e",
    color: "#6366f1",
    borderRadius: 99,
    padding: "1px 7px",
    fontSize: 10,
    textTransform: "capitalize",
  },
};

const skeletonStyles = {
  card: {
    marginTop: 20,
    background: "#1a1a1a",
    border: "1px solid #222",
    borderRadius: 10,
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  line: {
    height: 14,
    background: "linear-gradient(90deg, #222 25%, #2a2a2a 50%, #222 75%)",
    backgroundSize: "200% 100%",
    borderRadius: 6,
    animation: "shimmer 1.4s infinite",
  },
};
