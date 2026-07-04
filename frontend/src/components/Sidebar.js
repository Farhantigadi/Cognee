import { useState } from "react";
import { Brain, Trash2, FileText, Zap, GitBranch, BookOpen } from "lucide-react";
import toast from "react-hot-toast";
import { deletePaper, improveMemory } from "../api";

export default function Sidebar({ papers, stats, onPaperRemoved, onMemoryImproved }) {
  const [removingId, setRemovingId] = useState(null);
  const [improving, setImproving] = useState(false);

  const handleRemove = async (name) => {
    setRemovingId(name);
    try {
      await deletePaper(name);
      toast.success(`"${name}" removed from memory`);
      onPaperRemoved();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to remove paper");
    } finally {
      setRemovingId(null);
    }
  };

  const handleImprove = async () => {
    if (!papers.length) return toast.error("No papers in memory to improve");
    setImproving(true);
    try {
      await Promise.all(papers.map((p) => improveMemory(p.name)));
      toast.success("Memory enriched across all papers ✨");
      onMemoryImproved();
    } catch (e) {
      toast.error("Improve failed");
    } finally {
      setImproving(false);
    }
  };

  return (
    <aside style={styles.sidebar}>
      {/* Logo */}
      <div style={styles.logo}>
        <BookOpen size={22} color="#6366f1" />
        <div>
          <div style={styles.logoTitle}>ChronoResearch</div>
          <div style={styles.logoSub}>Papers That Talk To Each Other</div>
        </div>
      </div>

      <div style={styles.divider} />

      {/* Stats */}
      <div style={styles.statsRow}>
        <StatPill icon={<FileText size={13} />} value={stats?.total_papers ?? 0} label="Papers" />
        <StatPill icon={<Brain size={13} />} value={stats?.total_nodes ?? 0} label="Nodes" />
        <StatPill icon={<GitBranch size={13} />} value={stats?.total_edges ?? 0} label="Edges" />
      </div>

      <div style={styles.divider} />

      {/* Papers list */}
      <div style={styles.sectionLabel}>IN MEMORY</div>

      <div style={styles.paperList}>
        {papers.length === 0 && (
          <div style={styles.emptyNote}>No papers yet. Upload a PDF to start.</div>
        )}
        {papers.map((p) => (
          <div key={p.name} style={styles.paperRow}>
            <div style={styles.paperInfo}>
              <div style={styles.paperName}>{p.name.replace(/_/g, " ")}</div>
              <div style={styles.paperMeta}>{p.chunks} chunks</div>
            </div>
            <button
              style={styles.removeBtn}
              onClick={() => handleRemove(p.name)}
              disabled={removingId === p.name}
              title={`Remove ${p.name}`}
            >
              <Trash2 size={14} color={removingId === p.name ? "#555" : "#ef4444"} />
            </button>
          </div>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      {/* Improve button */}
      <button
        style={{ ...styles.improveBtn, opacity: improving ? 0.6 : 1 }}
        onClick={handleImprove}
        disabled={improving}
      >
        <Zap size={15} />
        {improving ? "Enriching..." : "Improve Memory"}
      </button>
    </aside>
  );
}

function StatPill({ icon, value, label }) {
  return (
    <div style={styles.statPill}>
      {icon}
      <span style={styles.statValue}>{value}</span>
      <span style={styles.statLabel}>{label}</span>
    </div>
  );
}

const styles = {
  sidebar: {
    width: 260,
    minHeight: "100vh",
    background: "#111111",
    borderRight: "1px solid #222",
    display: "flex",
    flexDirection: "column",
    padding: "20px 16px",
    gap: 0,
    flexShrink: 0,
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginBottom: 16,
  },
  logoTitle: {
    fontSize: 15,
    fontWeight: 700,
    color: "#f0f0f0",
    lineHeight: 1.2,
  },
  logoSub: {
    fontSize: 10,
    color: "#555",
    lineHeight: 1.3,
  },
  divider: {
    height: 1,
    background: "#222",
    margin: "12px 0",
  },
  statsRow: {
    display: "flex",
    gap: 6,
    marginBottom: 4,
  },
  statPill: {
    flex: 1,
    background: "#1a1a1a",
    border: "1px solid #2a2a2a",
    borderRadius: 8,
    padding: "6px 4px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 2,
    color: "#888",
  },
  statValue: {
    fontSize: 16,
    fontWeight: 700,
    color: "#6366f1",
    lineHeight: 1,
  },
  statLabel: {
    fontSize: 9,
    color: "#555",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  sectionLabel: {
    fontSize: 10,
    color: "#444",
    fontWeight: 600,
    letterSpacing: "0.1em",
    marginBottom: 8,
  },
  paperList: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    overflowY: "auto",
    maxHeight: 340,
  },
  emptyNote: {
    fontSize: 12,
    color: "#444",
    lineHeight: 1.5,
    padding: "8px 0",
  },
  paperRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    background: "#1a1a1a",
    border: "1px solid #222",
    borderRadius: 8,
    padding: "8px 10px",
    gap: 8,
  },
  paperInfo: {
    flex: 1,
    minWidth: 0,
  },
  paperName: {
    fontSize: 12,
    fontWeight: 500,
    color: "#d0d0d0",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    textTransform: "capitalize",
  },
  paperMeta: {
    fontSize: 10,
    color: "#555",
    marginTop: 1,
  },
  removeBtn: {
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: 4,
    borderRadius: 4,
    display: "flex",
    alignItems: "center",
    flexShrink: 0,
  },
  improveBtn: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 7,
    background: "#1e1b4b",
    border: "1px solid #3730a3",
    color: "#a5b4fc",
    borderRadius: 8,
    padding: "10px 0",
    fontSize: 13,
    fontWeight: 500,
    cursor: "pointer",
    width: "100%",
    marginTop: 12,
    transition: "opacity 0.2s",
  },
};
