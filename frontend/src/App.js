import { useState, useEffect, useCallback } from "react";
import { Toaster } from "react-hot-toast";
import { Upload, MessageSquare } from "lucide-react";
import Sidebar from "./components/Sidebar";
import UploadZone from "./components/UploadZone";
import QueryPanel from "./components/QueryPanel";
import StatsCard from "./components/StatsCard";
import { fetchPapers, fetchStats } from "./api";

const TABS = [
  { id: "upload", label: "Upload & Learn", icon: <Upload size={15} /> },
  { id: "ask",    label: "Ask Anything",   icon: <MessageSquare size={15} /> },
];

export default function App() {
  const [tab, setTab] = useState("upload");
  const [papers, setPapers] = useState([]);
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const refresh = useCallback(async () => {
    setStatsLoading(true);
    try {
      const [papersRes, statsRes] = await Promise.all([fetchPapers(), fetchStats()]);
      setPapers(papersRes.data);
      setStats(statsRes.data);
    } catch {
      // API may not be up yet — fail silently
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <>
      <style>{globalStyles}</style>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: "#1a1a1a", color: "#e0e0e0", border: "1px solid #333", fontSize: 13 },
        }}
      />

      <div style={styles.layout}>
        <Sidebar
          papers={papers}
          stats={stats}
          onPaperRemoved={refresh}
          onMemoryImproved={refresh}
        />

        <main style={styles.main}>
          {/* Stats row */}
          <StatsCard stats={stats} loading={statsLoading} />

          {/* Tabs */}
          <div style={styles.tabBar}>
            {TABS.map((t) => (
              <button
                key={t.id}
                style={{ ...styles.tab, ...(tab === t.id ? styles.tabActive : {}) }}
                onClick={() => setTab(t.id)}
              >
                {t.icon}
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div style={styles.content}>
            {tab === "upload" && (
              <UploadZone onUploadComplete={refresh} />
            )}
            {tab === "ask" && (
              <QueryPanel papers={papers} />
            )}
          </div>
        </main>
      </div>
    </>
  );
}

const styles = {
  layout: {
    display: "flex",
    minHeight: "100vh",
    background: "#0f0f0f",
    fontFamily: "'Inter', system-ui, sans-serif",
  },
  main: {
    flex: 1,
    padding: "28px 36px",
    overflowY: "auto",
    minWidth: 0,
  },
  tabBar: {
    display: "flex",
    gap: 4,
    marginBottom: 24,
    borderBottom: "1px solid #222",
    paddingBottom: 0,
  },
  tab: {
    display: "flex",
    alignItems: "center",
    gap: 7,
    background: "none",
    border: "none",
    borderBottom: "2px solid transparent",
    color: "#555",
    fontSize: 14,
    fontWeight: 500,
    padding: "8px 16px",
    cursor: "pointer",
    marginBottom: -1,
    transition: "color 0.15s, border-color 0.15s",
    fontFamily: "inherit",
  },
  tabActive: {
    color: "#6366f1",
    borderBottomColor: "#6366f1",
  },
  content: {
    animation: "fadeIn 0.2s ease",
  },
};

const globalStyles = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f0f; color: #e0e0e0; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #111; }
  ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
  textarea:focus { border-color: #6366f1 !important; }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  @media (max-width: 768px) {
    aside { display: none; }
  }
`;
