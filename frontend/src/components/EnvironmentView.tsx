import { useEffect, useState } from "react";
import { BACKEND_URL } from "../config";

const API_BASE = BACKEND_URL;

interface ToolInfo {
  tool: string;
  version: string;
}

interface Resources {
  ram_gb:   { total: number; available: number };
  disk_gb:  { total: number; available: number };
  cpu_cores: number;
}

interface EnvReport {
  os: string;
  architecture: string;
  installed_tools: ToolInfo[];
  missing_tools: string[];
  path_entries: string[];
  resources: Resources;
  environment_variables: Record<string, string>;
}

interface ReportResponse {
  status: string;
  health: string;
  warnings: string[];
  report: EnvReport;
  note: string;
}

const STATUS_COLOR: Record<string, string> = {
  good: "#4ade80",
  warnings: "#facc15",
  error: "#f87171",
};

export function EnvironmentView({ token }: { token: string | null }) {
  const [data, setData] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toolQuery, setToolQuery] = useState("");
  const [toolResult, setToolResult] = useState<{
    tool: string; installed: boolean; version?: string; suggestion?: string; message?: string;
  } | null>(null);
  const [toolLoading, setToolLoading] = useState(false);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/environment/report`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      setData(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  };

  const checkTool = async () => {
    if (!toolQuery.trim()) return;
    setToolLoading(true);
    setToolResult(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/environment/tool/${encodeURIComponent(toolQuery.trim())}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      const json = await res.json();
      setToolResult(json);
    } catch {
      setToolResult(null);
    } finally {
      setToolLoading(false);
    }
  };

  useEffect(() => { fetchReport(); }, []);

  const healthColor = data ? (STATUS_COLOR[data.health] ?? "#6666a0") : "#555";

  return (
    <div>
      <div className="panel-header">
        <h2>⚙ Validación de Entorno</h2>
        <p>Verifica herramientas instaladas, versiones y recursos disponibles del sistema.</p>
      </div>

      {/* Reporte general */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <div className="card-title" style={{ margin: 0 }}>Reporte del Sistema</div>
          <button className="btn-primary" onClick={fetchReport} disabled={loading} style={{ padding: "6px 14px", fontSize: 12 }}>
            {loading ? "Cargando..." : "↺ Actualizar"}
          </button>
        </div>

        {error && <div className="alert error">❌ {error}</div>}

        {loading && !data && (
          <div style={{ color: "#33334a", textAlign: "center", padding: 40 }}>Generando reporte...</div>
        )}

        {data && (
          <>
            {/* Health summary */}
            <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
              <div className="stat-card" style={{ flex: 1, minWidth: 140 }}>
                <div style={{ fontSize: 11, color: "#44445a", textTransform: "uppercase", marginBottom: 4 }}>Estado</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: healthColor }}>
                  {data.health === "good" ? "✅ Bueno" : "⚠️ Advertencias"}
                </div>
              </div>
              <div className="stat-card" style={{ flex: 1, minWidth: 140 }}>
                <div style={{ fontSize: 11, color: "#44445a", textTransform: "uppercase", marginBottom: 4 }}>S.O.</div>
                <div style={{ fontSize: 12, color: "#d0d0f0" }}>{data.report.os}</div>
              </div>
              <div className="stat-card" style={{ flex: 1, minWidth: 140 }}>
                <div style={{ fontSize: 11, color: "#44445a", textTransform: "uppercase", marginBottom: 4 }}>Arquitectura</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#d0d0f0" }}>{data.report.architecture}</div>
              </div>
            </div>

            {/* Warnings */}
            {data.warnings.length > 0 && (
              <div className="alert warning" style={{ marginBottom: 12 }}>
                ⚠️ <strong>Herramientas faltantes:</strong> {data.warnings.join(", ")}
              </div>
            )}

            {/* Resources */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#6666a0", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>
                Recursos
              </div>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <ResourceBar label="RAM" used={data.report.resources.ram_gb.total - data.report.resources.ram_gb.available} total={data.report.resources.ram_gb.total} unit="GB" />
                <ResourceBar label="Disco" used={data.report.resources.disk_gb.total - data.report.resources.disk_gb.available} total={data.report.resources.disk_gb.total} unit="GB" />
                <div className="stat-card" style={{ flex: 1, minWidth: 120 }}>
                  <div style={{ fontSize: 11, color: "#44445a", textTransform: "uppercase", marginBottom: 4 }}>CPU</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "#60a5fa" }}>{data.report.resources.cpu_cores} cores</div>
                </div>
              </div>
            </div>

            {/* Installed tools */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#6666a0", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>
                Herramientas instaladas
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {data.report.installed_tools.map((t) => (
                  <div key={t.tool} style={{
                    background: "#4ade8011",
                    border: "1px solid #4ade8033",
                    borderRadius: 8,
                    padding: "6px 12px",
                    fontSize: 12,
                  }}>
                    <span style={{ color: "#4ade80", fontWeight: 700 }}>{t.tool}</span>
                    <span style={{ color: "#44445a", marginLeft: 6 }}>{t.version}</span>
                  </div>
                ))}
                {data.report.missing_tools.map((t) => (
                  <div key={t} style={{
                    background: "#f8717111",
                    border: "1px solid #f8717133",
                    borderRadius: 8,
                    padding: "6px 12px",
                    fontSize: 12,
                  }}>
                    <span style={{ color: "#f87171", fontWeight: 700 }}>{t}</span>
                    <span style={{ color: "#44445a", marginLeft: 6 }}>no instalado</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Env vars */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#6666a0", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>
                Variables de entorno relevantes
              </div>
              <div style={{ background: "#0e0e1a", borderRadius: 8, padding: "12px 14px", fontSize: 12, fontFamily: "monospace" }}>
                {Object.entries(data.report.environment_variables).map(([k, v]) => (
                  <div key={k} style={{ marginBottom: 4 }}>
                    <span style={{ color: "#a78bfa" }}>{k}</span>
                    <span style={{ color: "#44445a" }}>=</span>
                    <span style={{ color: "#d0d0f0" }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ fontSize: 11, color: "#33334a", marginTop: 10 }}>ℹ️ {data.note}</div>
          </>
        )}
      </div>

      {/* Tool checker */}
      <div className="card">
        <div className="card-title">Verificar herramienta</div>
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <input
            className="reply-input"
            style={{ flex: 1, fontSize: 14, padding: "10px 14px" }}
            placeholder='Nombre de herramienta (ej: node, git, docker, python3...)'
            value={toolQuery}
            onChange={(e) => setToolQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && checkTool()}
          />
          <button className="btn-primary" onClick={checkTool} disabled={toolLoading || !toolQuery.trim()}>
            {toolLoading ? "..." : "Verificar"}
          </button>
        </div>

        {toolResult && (
          <div style={{
            background: toolResult.installed ? "#4ade8011" : "#f8717111",
            border: `1px solid ${toolResult.installed ? "#4ade8033" : "#f8717133"}`,
            borderRadius: 10,
            padding: "12px 16px",
          }}>
            <div style={{ fontWeight: 700, color: toolResult.installed ? "#4ade80" : "#f87171", marginBottom: 4 }}>
              {toolResult.installed ? "✅ Instalado" : "❌ No encontrado"}
              {" "}— <span style={{ fontFamily: "monospace" }}>{toolResult.tool}</span>
            </div>
            {toolResult.version && (
              <div style={{ fontSize: 13, color: "#d0d0f0" }}>Versión: {toolResult.version}</div>
            )}
            {toolResult.suggestion && (
              <div style={{ fontSize: 13, color: "#facc15", marginTop: 4 }}>{toolResult.suggestion}</div>
            )}
            {toolResult.message && (
              <div style={{ fontSize: 12, color: "#f87171", marginTop: 4 }}>{toolResult.message}</div>
            )}
          </div>
        )}

        <div className="alert info" style={{ marginTop: 12 }}>
          💬 <strong>Tip:</strong> En el Chat dile a ATOS: <em>"¿Tengo Node instalado?"</em> o <em>"Genera un reporte del entorno"</em>
        </div>
      </div>
    </div>
  );
}

function ResourceBar({ label, used, total, unit }: { label: string; used: number; total: number; unit: string }) {
  const pct = Math.round((used / total) * 100);
  const color = pct > 85 ? "#f87171" : pct > 65 ? "#facc15" : "#4ade80";
  return (
    <div className="stat-card" style={{ flex: 1, minWidth: 160 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: "#44445a", textTransform: "uppercase" }}>{label}</span>
        <span style={{ fontSize: 11, color: "#6666a0" }}>{used}/{total} {unit}</span>
      </div>
      <div style={{ background: "#0e0e1a", borderRadius: 4, height: 6, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.5s" }} />
      </div>
      <div style={{ fontSize: 11, color, marginTop: 4 }}>{pct}% en uso</div>
    </div>
  );
}
