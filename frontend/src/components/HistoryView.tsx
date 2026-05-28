import { useEffect, useState } from "react";
import { BACKEND_URL } from "../config";

const API = BACKEND_URL;

const CATEGORY_META: Record<string, { icon: string; color: string }> = {
  nodejs:      { icon: "⬡",  color: "#4ade80" },
  python:      { icon: "🐍", color: "#facc15" },
  network:     { icon: "🌐", color: "#60a5fa" },
  permissions: { icon: "🔒", color: "#f87171" },
  docker:      { icon: "🐳", color: "#38bdf8" },
  git:         { icon: "⎇",  color: "#fb923c" },
  environment: { icon: "⚙",  color: "#a78bfa" },
};

interface CategoryDist { category: string; count: number }
interface TopSolution {
  solution: string;
  success: number;
  failure: number;
  effectiveness_pct: number;
  category: string;
}
interface Stats {
  total_incidents: number;
  resolved: number;
  escalated: number;
  resolution_rate_pct: number;
  category_distribution: CategoryDist[];
  top_solutions: TopSolution[];
}
interface IncidentResult {
  id: number;
  description: string;
  solution_used: string;
  outcome: string;
  category: string;
  created_at: string;
  relevance_score: number;
}

function StatBig({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="stat-card" style={{ flex: 1, minWidth: 120 }}>
      <div style={{ fontSize: 11, color: "#44445a", textTransform: "uppercase", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: color ?? "#d0d0f0" }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: "#44445a", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

export function HistoryView({ token }: { token: string | null }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<IncidentResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchStats = async () => {
    setStatsLoading(true);
    try {
      const res = await fetch(`${API}/api/history/stats`, { headers });
      if (res.ok) setStats(await res.json());
    } finally {
      setStatsLoading(false);
    }
  };

  const doSearch = async () => {
    if (!query.trim()) return;
    setSearchLoading(true);
    setSearched(true);
    try {
      const res = await fetch(
        `${API}/api/history/search?q=${encodeURIComponent(query)}`,
        { headers },
      );
      const json = await res.json();
      setResults(json.results ?? []);
    } finally {
      setSearchLoading(false);
    }
  };

  useEffect(() => { fetchStats(); }, []);

  return (
    <div>
      <div className="panel-header">
        <h2>🧠 Historial de Incidencias</h2>
        <p>Memoria persistente del agente. ATOS consulta este historial para reutilizar soluciones probadas.</p>
      </div>

      {/* Stats summary */}
      {statsLoading && !stats ? (
        <div style={{ color: "#33334a", textAlign: "center", padding: 40 }}>Cargando estadísticas...</div>
      ) : stats && (
        <>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
            <StatBig label="Total incidencias" value={stats.total_incidents} color="#60a5fa" />
            <StatBig label="Resueltas" value={stats.resolved} color="#4ade80" />
            <StatBig label="Escaladas" value={stats.escalated} color="#f87171" />
            <StatBig label="Tasa de resolución" value={`${stats.resolution_rate_pct}%`} color="#4ade80" sub="incidencias resueltas" />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
            {/* Category distribution */}
            <div className="card">
              <div className="card-title">Distribución por categoría</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {stats.category_distribution.map((c) => {
                  const meta = CATEGORY_META[c.category] ?? { icon: "🔧", color: "#6666a0" };
                  const maxCount = stats.category_distribution[0]?.count ?? 1;
                  const pct = Math.round((c.count / maxCount) * 100);
                  return (
                    <div key={c.category}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                        <span style={{ fontSize: 12, color: meta.color }}>
                          {meta.icon} {c.category}
                        </span>
                        <span style={{ fontSize: 12, color: "#6666a0" }}>{c.count}</span>
                      </div>
                      <div style={{ background: "#0e0e1a", borderRadius: 3, height: 5 }}>
                        <div style={{ width: `${pct}%`, height: "100%", background: meta.color + "99", borderRadius: 3 }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Top solutions */}
            <div className="card">
              <div className="card-title">Soluciones más efectivas</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {stats.top_solutions.map((s, i) => {
                  const meta = CATEGORY_META[s.category] ?? { icon: "🔧", color: "#6666a0" };
                  return (
                    <div key={i} style={{ fontSize: 12 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                        <span style={{ color: "#d0d0f0", fontFamily: "monospace", fontSize: 11 }}>
                          {s.solution.length > 36 ? s.solution.slice(0, 33) + "..." : s.solution}
                        </span>
                        <span style={{ color: "#4ade80", fontWeight: 700, marginLeft: 8, flexShrink: 0 }}>
                          {s.effectiveness_pct}%
                        </span>
                      </div>
                      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                        <span className="badge-pill" style={{ background: meta.color + "22", color: meta.color, fontSize: 10 }}>
                          {s.category}
                        </span>
                        <span style={{ color: "#44445a", fontSize: 11 }}>
                          ✓ {s.success} · ✗ {s.failure}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Search */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">Buscar en historial</div>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            className="reply-input"
            style={{ flex: 1, fontSize: 14, padding: "10px 14px" }}
            placeholder='Describe el problema (ej: "npm install peer deps", "python module not found")'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && doSearch()}
          />
          <button className="btn-primary" onClick={doSearch} disabled={searchLoading || !query.trim()}>
            {searchLoading ? "..." : "Buscar"}
          </button>
          {searched && (
            <button
              onClick={() => { setQuery(""); setResults([]); setSearched(false); }}
              style={{ padding: "10px 14px", background: "transparent", border: "1px solid #2a2a44", color: "#6666a0", borderRadius: 10, cursor: "pointer", fontSize: 13 }}
            >
              Limpiar
            </button>
          )}
        </div>

        {searched && !searchLoading && (
          <div style={{ marginTop: 14 }}>
            {results.length === 0 ? (
              <div style={{ color: "#33334a", textAlign: "center", padding: 20 }}>
                No se encontraron incidencias similares para <em>"{query}"</em>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div style={{ fontSize: 12, color: "#6666a0" }}>{results.length} resultado{results.length !== 1 ? "s" : ""} encontrado{results.length !== 1 ? "s" : ""}</div>
                {results.map((r) => {
                  const meta = CATEGORY_META[r.category] ?? { icon: "🔧", color: "#6666a0" };
                  return (
                    <div key={r.id} style={{
                      background: "#0e0e1a",
                      border: "1px solid #22223a",
                      borderRadius: 10,
                      padding: "12px 14px",
                    }}>
                      <div style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "flex-start" }}>
                        <span className="badge-pill" style={{ background: meta.color + "22", color: meta.color, flexShrink: 0 }}>
                          {meta.icon} {r.category}
                        </span>
                        <span style={{
                          fontSize: 10, background: r.outcome === "resolved" ? "#0f2a1a" : "#2a0f0f",
                          color: r.outcome === "resolved" ? "#4ade80" : "#f87171",
                          border: `1px solid ${r.outcome === "resolved" ? "#166534" : "#7f1d1d"}`,
                          borderRadius: 20, padding: "2px 8px", flexShrink: 0,
                        }}>
                          {r.outcome}
                        </span>
                      </div>
                      <div style={{ fontSize: 13, color: "#c0c0e0", marginBottom: 6 }}>{r.description}</div>
                      <div style={{
                        fontSize: 12, fontFamily: "monospace",
                        background: "#13132a", borderRadius: 6, padding: "6px 10px",
                        color: "#4ade80",
                      }}>
                        $ {r.solution_used}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="alert info">
        💬 <strong>Tip:</strong> En el Chat pega un error y ATOS consultará este historial automáticamente
        antes de sugerir una solución. Dice cosas como: <em>"Encontré 2 casos similares en el historial..."</em>
      </div>
    </div>
  );
}
