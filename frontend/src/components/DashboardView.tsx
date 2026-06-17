import { useEffect, useState, useCallback } from "react";
import { BACKEND_URL } from "../config";

interface DashboardData {
  tickets: {
    total: number;
    by_status: Record<string, number>;
    by_priority: Record<string, number>;
  };
  accounts: {
    total: number;
    locked: number;
    by_role: Record<string, number>;
    by_job_role: Record<string, number>;
  };
  db_access: {
    total_active: number;
    expiring_soon: number;
    by_database: Record<string, number>;
    actions: Record<string, number>;
  };
  incidents: {
    total: number;
    by_outcome: Record<string, number>;
    top_categories: { category: string; count: number }[];
  };
  agent: {
    total_tool_calls: number;
    top_tools: { tool: string; count: number }[];
  };
}

const STATUS_COLORS: Record<string, string> = {
  open: "#818cf8", in_progress: "#facc15", resolved: "#4ade80", closed: "#6b7280",
};
const PRIORITY_COLORS: Record<string, string> = {
  low: "#6b7280", medium: "#818cf8", high: "#facc15", critical: "#f87171",
};
const OUTCOME_COLORS: Record<string, string> = {
  resolved: "#4ade80", escalated: "#facc15", unresolved: "#f87171",
};
const ROLE_COLORS: Record<string, string> = {
  user: "#4ade80", agent: "#818cf8", admin: "#f59e0b",
};
const JOB_COLORS: Record<string, string> = {
  frontend_dev: "#38bdf8", backend_dev: "#818cf8", data_scientist: "#f472b6",
};
const JOB_LABELS: Record<string, string> = {
  frontend_dev: "Frontend Dev", backend_dev: "Backend Dev", data_scientist: "Data Scientist",
};

function Bar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
        <span style={{ color: "var(--text-muted)" }}>{label}</span>
        <span style={{ fontWeight: 600, color }}>{value}</span>
      </div>
      <div style={{ height: 6, background: "#2a2a3a", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 3,
          transition: "width 0.6s ease" }} />
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, color }: { label: string; value: number | string; sub?: string; color?: string }) {
  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10,
      padding: "16px 20px", flex: 1, minWidth: 120 }}>
      <div style={{ fontSize: 26, fontWeight: 700, color: color ?? "#f0f0f0" }}>{value}</div>
      <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: "#555", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10, padding: 20 }}>
      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 16 }}>{title}</div>
      {children}
    </div>
  );
}

export function DashboardView({ token }: { token: string | null }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${BACKEND_URL}/api/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) { setError("Error al cargar métricas."); return; }
      setData(await r.json());
    } catch { setError("Sin conexión con el servidor."); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div style={{ color: "var(--text-muted)", padding: 24 }}>Cargando métricas...</div>;
  if (error)   return <div style={{ color: "#f87171", padding: 24 }}>{error}</div>;
  if (!data)   return null;

  const maxTicketStatus   = Math.max(...Object.values(data.tickets.by_status), 1);
  const maxTicketPriority = Math.max(...Object.values(data.tickets.by_priority), 1);
  const maxTool           = Math.max(...data.agent.top_tools.map(t => t.count), 1);
  const maxDbAccess       = Math.max(...Object.values(data.db_access.by_database), 1);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* Top stats */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <StatCard label="Tickets totales"       value={data.tickets.total}             color="#818cf8" />
        <StatCard label="Cuentas registradas"   value={data.accounts.total}            color="#4ade80"
          sub={data.accounts.locked > 0 ? `${data.accounts.locked} bloqueadas` : undefined} />
        <StatCard label="Accesos BD activos"    value={data.db_access.total_active}    color="#38bdf8"
          sub={data.db_access.expiring_soon > 0 ? `${data.db_access.expiring_soon} por vencer` : undefined} />
        <StatCard label="Incidencias resueltas" value={data.incidents.by_outcome.resolved ?? 0} color="#4ade80" />
        <StatCard label="Llamadas al agente"    value={data.agent.total_tool_calls}    color="#f59e0b" />
      </div>

      {/* Row 1 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>

        <Section title="🎫 Tickets por estado">
          {Object.entries(data.tickets.by_status).length === 0
            ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Sin tickets aún.</div>
            : Object.entries(data.tickets.by_status).map(([s, n]) => (
              <Bar key={s} label={s} value={n} max={maxTicketStatus} color={STATUS_COLORS[s] ?? "#818cf8"} />
            ))}
        </Section>

        <Section title="🔥 Tickets por prioridad">
          {Object.entries(data.tickets.by_priority).length === 0
            ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Sin tickets aún.</div>
            : Object.entries(data.tickets.by_priority).map(([p, n]) => (
              <Bar key={p} label={p} value={n} max={maxTicketPriority} color={PRIORITY_COLORS[p] ?? "#818cf8"} />
            ))}
        </Section>

      </div>

      {/* Row 2 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>

        <Section title="🗄️ Accesos activos por BD">
          {Object.entries(data.db_access.by_database).length === 0
            ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Sin accesos activos.</div>
            : Object.entries(data.db_access.by_database).map(([db, n]) => (
              <Bar key={db} label={db} value={n} max={maxDbAccess} color="#38bdf8" />
            ))}
          <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid var(--border)", display: "flex", gap: 16, flexWrap: "wrap" }}>
            {Object.entries(data.db_access.actions).map(([action, n]) => (
              <div key={action} style={{ fontSize: 12 }}>
                <span style={{ color: "var(--text-muted)" }}>{action}: </span>
                <span style={{ fontWeight: 600 }}>{n}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section title="👥 Cuentas por rol">
          {Object.entries(data.accounts.by_role).map(([role, n]) => (
            <Bar key={role} label={role} value={n} max={data.accounts.total} color={ROLE_COLORS[role] ?? "#818cf8"} />
          ))}
          {Object.keys(data.accounts.by_job_role).length > 0 && (
            <>
              <div style={{ fontSize: 12, color: "var(--text-muted)", margin: "12px 0 8px" }}>Job roles asignados</div>
              {Object.entries(data.accounts.by_job_role).map(([jr, n]) => (
                <Bar key={jr} label={JOB_LABELS[jr] ?? jr} value={n}
                  max={Math.max(...Object.values(data.accounts.by_job_role))} color={JOB_COLORS[jr] ?? "#818cf8"} />
              ))}
            </>
          )}
        </Section>

      </div>

      {/* Row 3 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>

        <Section title="🧠 Incidencias por resultado">
          {Object.entries(data.incidents.by_outcome).length === 0
            ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Sin incidencias registradas.</div>
            : Object.entries(data.incidents.by_outcome).map(([o, n]) => (
              <Bar key={o} label={o} value={n} max={data.incidents.total} color={OUTCOME_COLORS[o] ?? "#818cf8"} />
            ))}
          {data.incidents.top_categories.length > 0 && (
            <>
              <div style={{ fontSize: 12, color: "var(--text-muted)", margin: "12px 0 8px" }}>Categorías más frecuentes</div>
              {data.incidents.top_categories.map(c => (
                <div key={c.category} style={{ display: "flex", justifyContent: "space-between",
                  fontSize: 12, padding: "4px 0", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ color: "var(--text-muted)" }}>{c.category}</span>
                  <span style={{ fontWeight: 600 }}>{c.count}</span>
                </div>
              ))}
            </>
          )}
        </Section>

        <Section title="🤖 Herramientas más usadas por el agente">
          {data.agent.top_tools.length === 0
            ? <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Sin actividad del agente aún.</div>
            : data.agent.top_tools.map(t => (
              <Bar key={t.tool} label={t.tool} value={t.count} max={maxTool} color="#f59e0b" />
            ))}
          <div style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
            Total de llamadas: <strong style={{ color: "#f0f0f0" }}>{data.agent.total_tool_calls}</strong>
          </div>
        </Section>

      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {[
            { label: "📋 Tickets",          path: "tickets" },
            { label: "👥 Cuentas",          path: "accounts" },
            { label: "🗄️ Accesos BD",       path: "db-access" },
            { label: "🕒 Historial BD",     path: "db-access-logs" },
            { label: "🤖 Audit Logs",       path: "audit-logs" },
          ].map(({ label, path }) => (
            <a
              key={path}
              href={`${BACKEND_URL}/api/export/${path}`}
              download
              onClick={e => {
                e.preventDefault();
                const a = document.createElement("a");
                a.href = `${BACKEND_URL}/api/export/${path}`;
                const headers = new Headers({ Authorization: `Bearer ${token}` });
                fetch(a.href, { headers })
                  .then(r => r.blob())
                  .then(blob => {
                    const url = URL.createObjectURL(blob);
                    a.href = url;
                    a.download = `${path}_${new Date().toISOString().slice(0,10)}.csv`;
                    a.click();
                    URL.revokeObjectURL(url);
                  });
              }}
              style={{ textDecoration: "none" }}
            >
              <button className="btn-secondary" style={{ fontSize: 12, padding: "6px 12px" }}>
                ⬇ {label}
              </button>
            </a>
          ))}
        </div>
        <button className="btn-secondary" style={{ fontSize: 13 }} onClick={load}>↺ Actualizar</button>
      </div>

    </div>
  );
}
