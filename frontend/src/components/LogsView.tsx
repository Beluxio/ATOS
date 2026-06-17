import { useEffect, useState, useCallback } from "react";
import { BACKEND_URL } from "../config";

interface LogEntry {
  id: number;
  tool_name: string;
  params: Record<string, unknown>;
  result: Record<string, unknown>;
  session_id: string | null;
  created_at: string;
}

const VIOLATION_CATEGORY_LABELS: Record<string, string> = {
  hate: "Odio / discriminación",
  "hate/threatening": "Amenaza de odio",
  harassment: "Lenguaje ofensivo",
  "harassment/threatening": "Amenaza / intimidación",
  sexual: "Contenido sexual",
  "sexual/minors": "Contenido sexual (menores)",
  violence: "Violencia",
  "violence/graphic": "Violencia explícita",
  "self-harm": "Autolesiones",
  "self-harm/intent": "Autolesiones (intención)",
  "self-harm/instructions": "Autolesiones (instrucciones)",
  jailbreak: "Jailbreak / manipulación",
};

export function LogsView() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<"all" | "violations">("all");

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/logs?limit=100`);
      const data = await res.json();
      setLogs(data);
    } catch {
      /* silently fail */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString("es", { dateStyle: "short", timeStyle: "medium" });

  const violations = logs.filter(l => l.tool_name === "content_violation");
  const actions    = logs.filter(l => l.tool_name !== "content_violation");
  const displayed  = tab === "violations" ? violations : actions;

  const tabStyle = (active: boolean): React.CSSProperties => ({
    padding: "5px 14px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontSize: 12,
    fontWeight: active ? 600 : 400,
    background: active ? "#1e1e3a" : "transparent",
    color: active ? "#818cf8" : "#6666a0",
  });

  return (
    <div>
      <div className="panel-header">
        <h2>📋 Audit Logs</h2>
        <p>Registro de acciones del agente y violaciones de políticas de contenido.</p>
      </div>

      {violations.length > 0 && (
        <div className="alert" style={{
          background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.3)",
          color: "#f87171", marginBottom: 0,
        }}>
          🚫 <strong>{violations.length} violación{violations.length !== 1 ? "es" : ""} de políticas</strong> detectada{violations.length !== 1 ? "s" : ""} — revisa la pestaña <strong>Violaciones</strong>.
        </div>
      )}

      <div className="card">
        <div className="card-title" style={{ justifyContent: "space-between" }}>
          <div style={{ display: "flex", gap: 4 }}>
            <button style={tabStyle(tab === "all")} onClick={() => setTab("all")}>
              🤖 Acciones del agente ({actions.length})
            </button>
            <button style={tabStyle(tab === "violations")} onClick={() => setTab("violations")}>
              🚫 Violaciones ({violations.length})
            </button>
          </div>
          <button
            onClick={fetchLogs}
            style={{ fontSize: 12, background: "transparent", border: "1px solid #2a2a44", color: "#6666a0", padding: "3px 10px", borderRadius: 6, cursor: "pointer" }}
          >
            {loading ? "Cargando..." : "Actualizar"}
          </button>
        </div>

        {displayed.length === 0 ? (
          <div style={{ color: "#33334a", fontSize: 13, textAlign: "center", padding: "24px 0" }}>
            {tab === "violations"
              ? "Sin violaciones registradas. El sistema está limpio."
              : "Sin registros aún. Usa el Chat y aquí aparecerán las acciones ejecutadas."}
          </div>
        ) : tab === "violations" ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Categoría</th>
                  <th>Usuario</th>
                  <th>Mensaje (extracto)</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {displayed.map((log) => {
                  const category = log.params?.category as string | undefined;
                  const userEmail = log.params?.user_email as string | undefined;
                  const message = log.params?.message as string | undefined;
                  return (
                    <tr key={log.id}>
                      <td style={{ color: "#44445a" }}>{log.id}</td>
                      <td>
                        <span style={{
                          background: "rgba(248,113,113,0.12)", color: "#f87171",
                          borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600,
                        }}>
                          {VIOLATION_CATEGORY_LABELS[category ?? ""] ?? category ?? "—"}
                        </span>
                      </td>
                      <td style={{ fontSize: 12, color: "#6666a0" }}>{userEmail ?? "Anónimo"}</td>
                      <td style={{ fontSize: 11, color: "#6666a0", maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {message ?? "—"}
                      </td>
                      <td style={{ color: "#55558a", fontSize: 11, whiteSpace: "nowrap" }}>
                        {formatDate(log.created_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Tool</th>
                  <th>Parámetros</th>
                  <th>Resultado</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {displayed.map((log) => (
                  <tr key={log.id}>
                    <td style={{ color: "#44445a" }}>{log.id}</td>
                    <td>
                      <code style={{ color: "#818cf8", fontSize: 12 }}>{log.tool_name}</code>
                    </td>
                    <td style={{ fontSize: 11, color: "#6666a0", fontFamily: "monospace", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>
                      {JSON.stringify(log.params)}
                    </td>
                    <td style={{ fontSize: 11, color: "#6666a0", fontFamily: "monospace", maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis" }}>
                      {JSON.stringify(log.result)}
                    </td>
                    <td style={{ color: "#55558a", fontSize: 11, whiteSpace: "nowrap" }}>
                      {formatDate(log.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="alert info">
        💡 Las violaciones de políticas son bloqueadas antes de llegar al agente y quedan registradas con el usuario, categoría y extracto del mensaje.
      </div>
    </div>
  );
}
