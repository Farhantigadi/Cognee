import { FileText, Brain, GitBranch } from "lucide-react";

export default function StatsCard({ stats, loading }) {
  const items = [
    { icon: <FileText size={20} color="#6366f1" />, value: stats?.total_papers ?? 0, label: "Total Papers" },
    { icon: <Brain size={20} color="#8b5cf6" />, value: stats?.total_nodes ?? 0, label: "Knowledge Nodes" },
    { icon: <GitBranch size={20} color="#a78bfa" />, value: stats?.total_edges ?? 0, label: "Graph Edges" },
  ];

  return (
    <div style={styles.row}>
      {items.map(({ icon, value, label }) => (
        <div key={label} style={styles.card}>
          <div style={styles.iconWrap}>{icon}</div>
          <div style={styles.value}>
            {loading ? <div style={styles.skeleton} /> : value.toLocaleString()}
          </div>
          <div style={styles.label}>{label}</div>
        </div>
      ))}
    </div>
  );
}

const styles = {
  row: {
    display: "flex",
    gap: 12,
    marginBottom: 28,
  },
  card: {
    flex: 1,
    background: "#1a1a1a",
    border: "1px solid #222",
    borderRadius: 12,
    padding: "16px 20px",
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  iconWrap: { marginBottom: 2 },
  value: {
    fontSize: 28,
    fontWeight: 700,
    color: "#f0f0f0",
    lineHeight: 1,
  },
  label: {
    fontSize: 12,
    color: "#555",
    fontWeight: 500,
  },
  skeleton: {
    width: 48,
    height: 28,
    background: "linear-gradient(90deg, #222 25%, #2a2a2a 50%, #222 75%)",
    backgroundSize: "200% 100%",
    borderRadius: 6,
    animation: "shimmer 1.4s infinite",
  },
};
