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

export function LogsView() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/logs?limit=50`);
      const data = await res.json();
      setLogs(data);
    } catch {
      /* silently fail */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString("es", { dateStyle: "short", timeStyle: "medium" });

  return (
    <div>
      <div className="panel-header">
        <h2>📋 Audit Logs</h2>
        <p>Registro de todas las acciones ejecutadas por ATOS en tiempo real.</p>
      </div>

      <div className="card">
        <div className="card-title" style={{ justifyContent: "space-between" }}>
          <span>🔍 Últimas 50 acciones</span>
          <button
            onClick={fetchLogs}
            style={{ fontSize: 12, background: "transparent", border: "1px solid #2a2a44", color: "#6666a0", padding: "3px 10px", borderRadius: 6, cursor: "pointer" }}
          >
            {loading ? "Cargando..." : "Actualizar"}
          </button>
        </div>

        {logs.length === 0 ? (
          <div style={{ color: "#33334a", fontSize: 13, textAlign: "center", padding: "24px 0" }}>
            Sin registros aún. Usa el Chat y aquí aparecerán las acciones ejecutadas.
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
                {logs.map((log) => (
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
        💡 <strong>Demo:</strong> Cada acción que ATOS ejecuta queda registrada aquí con sus parámetros y resultado — útil para auditoría y transparencia.
      </div>
    </div>
  );
}
