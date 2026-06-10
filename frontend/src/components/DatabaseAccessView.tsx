import { useState, useEffect, useCallback } from "react";
import { BACKEND_URL } from "../config";

const DATABASES = ["DataCo Analytics", "Data Warehouse", "Reporting DB"];

const POLICY: Record<string, string[]> = {
  "Frontend Developer":  ["DataCo Analytics"],
  "Backend Developer":   ["DataCo Analytics", "Reporting DB"],
  "Data Scientist":      ["DataCo Analytics", "Data Warehouse", "Reporting DB"],
};

const STATUS_COLOR: Record<string, string> = {
  active:    "#4ade80",
  revoked:   "#f87171",
  suspended: "#facc15",
  expired:   "#f87171",
};

interface AccessRecord {
  id: number;
  user_email: string;
  database_name: string;
  db_username: string;
  db_password: string;
  status: string;
  granted_by: string | null;
  expires_at: string | null;
  days_left: number | null;
  expiring_soon: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

interface LogEntry {
  id: number;
  user_email: string;
  database_name: string;
  action: string;
  action_label: string;
  action_icon: string;
  performed_by: string | null;
  details: string | null;
  created_at: string;
}

interface Props { token: string | null }

export function DatabaseAccessView({ token }: Props) {
  const [records, setRecords]       = useState<AccessRecord[]>([]);
  const [logs, setLogs]             = useState<LogEntry[]>([]);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState("");
  const [filterDb, setFilterDb]     = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [newPassword, setNewPassword]   = useState<Record<number, string>>({});
  const [editingId, setEditingId]       = useState<number | null>(null);
  const [editDays, setEditDays]         = useState("");
  const [editNoExpiry, setEditNoExpiry] = useState(false);
  const [editNotes, setEditNotes]       = useState("");

  // Grant form
  const [grantEmail, setGrantEmail]   = useState("");
  const [grantDb, setGrantDb]         = useState(DATABASES[0]);
  const [grantDays, setGrantDays]     = useState("30");
  const [grantNoExpiry, setGrantNoExpiry] = useState(false);
  const [grantMsg, setGrantMsg]       = useState("");
  const [grantLoading, setGrantLoading] = useState(false);
  const [lastCredentials, setLastCredentials] = useState<{ username: string; password: string; db: string } | null>(null);

  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [recs, lgEntries] = await Promise.all([
        fetch(`${BACKEND_URL}/api/db-access`, { headers }),
        fetch(`${BACKEND_URL}/api/db-access/logs`, { headers }),
      ]);
      if (!recs.ok) { setError("Error al cargar accesos."); return; }
      setRecords(await recs.json());
      if (lgEntries.ok) setLogs(await lgEntries.json());
    } catch { setError("Sin conexión con el servidor."); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  async function handleGrant(e: React.FormEvent) {
    e.preventDefault();
    setGrantLoading(true);
    setGrantMsg("");
    setLastCredentials(null);
    try {
      const r = await fetch(`${BACKEND_URL}/api/db-access/grant`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          user_email: grantEmail,
          database_name: grantDb,
          days: grantNoExpiry ? null : parseInt(grantDays) || 30,
        }),
      });
      const d = await r.json();
      if (r.ok && d.status === "ok") {
        setGrantMsg(`✅ Acceso otorgado a ${grantEmail}`);
        setLastCredentials({
          username: d.access.db_username,
          password: d.access.db_password,
          db: grantDb,
        });
        setGrantEmail("");
        load();
      } else {
        setGrantMsg(`⚠️ ${d.message ?? "Error al otorgar acceso."}`);
      }
    } catch { setGrantMsg("Error de conexión."); }
    finally { setGrantLoading(false); }
  }

  function startEdit(rec: AccessRecord) {
    setEditingId(rec.id);
    setEditDays(rec.days_left?.toString() ?? "30");
    setEditNoExpiry(!rec.expires_at);
    setEditNotes(rec.notes ?? "");
  }

  async function handleEdit(rec: AccessRecord) {
    const body: Record<string, unknown> = {};
    if (editNoExpiry) {
      body.no_expiry = true;
    } else if (editDays) {
      body.days = parseInt(editDays);
    }
    if (editNotes !== (rec.notes ?? "")) body.notes = editNotes;
    await fetch(`${BACKEND_URL}/api/db-access/${rec.id}`, {
      method: "PATCH", headers,
      body: JSON.stringify(body),
    });
    setEditingId(null);
    load();
  }

  async function handleRevoke(record: AccessRecord) {
    if (!confirm(`¿Revocar acceso de ${record.user_email} a ${record.database_name}?`)) return;
    const r = await fetch(`${BACKEND_URL}/api/db-access/${record.id}/revoke`, { method: "POST", headers });
    if (r.ok) load();
  }

  async function handleResetPassword(record: AccessRecord) {
    const r = await fetch(`${BACKEND_URL}/api/db-access/${record.id}/reset-password`, { method: "POST", headers });
    const d = await r.json();
    if (r.ok) {
      setNewPassword(prev => ({ ...prev, [record.id]: d.db_password }));
      load();
    }
  }

  const filtered = records.filter(r =>
    (filterDb === "all" || r.database_name === filterDb) &&
    (filterStatus === "all" || r.status === filterStatus)
  );

  const stats = {
    active:  records.filter(r => r.status === "active").length,
    revoked: records.filter(r => r.status === "revoked").length,
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* Stats */}
      <div style={{ display: "flex", gap: 12 }}>
        {[
          { label: "Accesos activos",       value: stats.active,  color: "#4ade80" },
          { label: "Revocados / Expirados", value: stats.revoked, color: "#f87171" },
          { label: "Próximos a vencer",     value: records.filter(r => r.expiring_soon).length, color: "#facc15" },
          { label: "Bases de datos",        value: DATABASES.length, color: "#818cf8" },
        ].map(s => (
          <div key={s.label} style={{ flex: 1, background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 10, padding: "14px 18px" }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Policy table */}
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10, padding: 20 }}>
        <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 14 }}>📋 Política de acceso por job role</div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-muted)" }}>
              <th style={{ textAlign: "left", padding: "6px 10px", fontWeight: 500 }}>Job Role</th>
              {DATABASES.map(db => (
                <th key={db} style={{ textAlign: "center", padding: "6px 10px", fontWeight: 500 }}>{db}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(POLICY).map(([role, dbs]) => (
              <tr key={role} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "8px 10px", color: "#818cf8", fontWeight: 500 }}>{role}</td>
                {DATABASES.map(db => (
                  <td key={db} style={{ textAlign: "center", padding: "8px 10px" }}>
                    {dbs.includes(db)
                      ? <span style={{ color: "#4ade80" }}>✓</span>
                      : <span style={{ color: "#3a3a4a" }}>✕</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Grant form */}
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10, padding: 20 }}>
        <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 14 }}>➕ Otorgar acceso</div>
        <form onSubmit={handleGrant} style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div style={{ flex: 2, minWidth: 200 }}>
            <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Email del usuario</label>
            <input className="input" style={{ width: "100%" }} type="email" placeholder="usuario@dataco.com"
              value={grantEmail} onChange={e => setGrantEmail(e.target.value)} required />
          </div>
          <div style={{ flex: 1, minWidth: 160 }}>
            <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Base de datos</label>
            <select className="input" style={{ width: "100%" }} value={grantDb} onChange={e => setGrantDb(e.target.value)}>
              {DATABASES.map(db => <option key={db}>{db}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Días de vigencia</label>
            <input className="input" type="number" min={1} max={365} style={{ width: 80, fontSize: 13 }}
              value={grantDays} onChange={e => setGrantDays(e.target.value)} disabled={grantNoExpiry} />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, paddingBottom: 2 }}>
            <input type="checkbox" id="grantNoExpiry" checked={grantNoExpiry}
              onChange={e => setGrantNoExpiry(e.target.checked)} />
            <label htmlFor="grantNoExpiry" style={{ fontSize: 12, color: "var(--text-muted)", cursor: "pointer" }}>Sin expiración</label>
          </div>
          <button className="btn-primary" type="submit" disabled={grantLoading} style={{ height: 38 }}>
            {grantLoading ? "..." : "Otorgar"}
          </button>
        </form>

        {grantMsg && <div style={{ marginTop: 12, fontSize: 13, color: grantMsg.startsWith("✅") ? "#4ade80" : "#f87171" }}>{grantMsg}</div>}

        {lastCredentials && (
          <div style={{ marginTop: 12, padding: "12px 16px", background: "var(--bg)", borderRadius: 8,
            border: "1px solid #4ade8044", fontSize: 13 }}>
            <div style={{ color: "#4ade80", fontWeight: 600, marginBottom: 6 }}>🔑 Credenciales generadas — guárdalas ahora</div>
            <div><span style={{ color: "var(--text-muted)" }}>BD:</span> {lastCredentials.db}</div>
            <div><span style={{ color: "var(--text-muted)" }}>Usuario:</span> <code>{lastCredentials.username}</code></div>
            <div><span style={{ color: "var(--text-muted)" }}>Contraseña:</span> <code style={{ color: "#facc15" }}>{lastCredentials.password}</code></div>
          </div>
        )}
      </div>

      {/* Filters + table */}
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10, padding: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
          <div style={{ fontWeight: 600, fontSize: 14 }}>Registros de acceso</div>
          <div style={{ display: "flex", gap: 8 }}>
            <select className="input" style={{ fontSize: 13 }} value={filterDb} onChange={e => setFilterDb(e.target.value)}>
              <option value="all">Todas las BDs</option>
              {DATABASES.map(db => <option key={db}>{db}</option>)}
            </select>
            <select className="input" style={{ fontSize: 13 }} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
              <option value="all">Todos los estados</option>
              <option value="active">Activo</option>
              <option value="revoked">Revocado</option>
              <option value="suspended">Suspendido</option>
            </select>
            <button className="btn-secondary" onClick={load} style={{ fontSize: 13 }}>↺ Actualizar</button>
          </div>
        </div>

        {error && <div style={{ color: "#f87171", fontSize: 13, marginBottom: 12 }}>{error}</div>}
        {loading ? (
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Cargando...</div>
        ) : filtered.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "24px 0", textAlign: "center" }}>
            No hay registros con los filtros seleccionados.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-muted)" }}>
                  {["Usuario", "Base de datos", "Usuario BD", "Contraseña BD", "Estado", "Expira", "Otorgado por", "Acciones"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "8px 10px", fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(rec => (
                  <>
                  <tr key={rec.id} style={{ borderBottom: editingId === rec.id ? "none" : "1px solid var(--border)" }}>
                    <td style={{ padding: "10px" }}>{rec.user_email}</td>
                    <td style={{ padding: "10px" }}>{rec.database_name}</td>
                    <td style={{ padding: "10px" }}><code>{rec.db_username}</code></td>
                    <td style={{ padding: "10px" }}>
                      <code style={{ color: newPassword[rec.id] ? "#facc15" : "var(--text-muted)" }}>
                        {newPassword[rec.id] ?? rec.db_password}
                      </code>
                    </td>
                    <td style={{ padding: "10px" }}>
                      <span style={{ padding: "2px 8px", borderRadius: 4, fontSize: 12,
                        background: `${STATUS_COLOR[rec.status]}22`, color: STATUS_COLOR[rec.status] }}>
                        {rec.status}
                      </span>
                    </td>
                    <td style={{ padding: "10px" }}>
                      {rec.expires_at ? (
                        <span style={{ color: rec.expiring_soon ? "#facc15" : rec.days_left === 0 ? "#f87171" : "var(--text-muted)", fontSize: 12 }}>
                          {rec.days_left === 0 ? "Hoy" : rec.expiring_soon ? `⚠️ ${rec.days_left}d` : `${rec.days_left}d`}
                        </span>
                      ) : "—"}
                    </td>
                    <td style={{ padding: "10px", color: "var(--text-muted)" }}>{rec.granted_by ?? "—"}</td>
                    <td style={{ padding: "10px" }}>
                      {rec.status === "active" && (
                        <div style={{ display: "flex", gap: 6 }}>
                          <button className="btn-secondary" style={{ fontSize: 12, padding: "4px 10px" }}
                            onClick={() => startEdit(rec)}>✏️ Editar</button>
                          <button className="btn-secondary" style={{ fontSize: 12, padding: "4px 10px" }}
                            onClick={() => handleResetPassword(rec)}>🔑 Pwd</button>
                          <button style={{ fontSize: 12, padding: "4px 10px", background: "#f8717122",
                            color: "#f87171", border: "1px solid #f8717144", borderRadius: 6, cursor: "pointer" }}
                            onClick={() => handleRevoke(rec)}>✕</button>
                        </div>
                      )}
                    </td>
                  </tr>
                  {editingId === rec.id && (
                    <tr key={`edit-${rec.id}`} style={{ borderBottom: "1px solid var(--border)", background: "#1e1e2e" }}>
                      <td colSpan={8} style={{ padding: "12px 10px" }}>
                        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                          <div>
                            <label style={{ fontSize: 11, color: "var(--text-muted)", display: "block", marginBottom: 3 }}>Días de vigencia (desde hoy)</label>
                            <input className="input" type="number" min={1} max={365} style={{ width: 100, fontSize: 13 }}
                              value={editDays} onChange={e => setEditDays(e.target.value)} disabled={editNoExpiry} />
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <input type="checkbox" id="editNoExpiry" checked={editNoExpiry}
                              onChange={e => setEditNoExpiry(e.target.checked)} />
                            <label htmlFor="editNoExpiry" style={{ fontSize: 12, color: "var(--text-muted)", cursor: "pointer" }}>Sin expiración</label>
                          </div>
                          <div style={{ flex: 1, minWidth: 200 }}>
                            <label style={{ fontSize: 11, color: "var(--text-muted)", display: "block", marginBottom: 3 }}>Notas</label>
                            <input className="input" type="text" style={{ width: "100%", fontSize: 13 }}
                              placeholder="Ej: Renovado para proyecto X"
                              value={editNotes} onChange={e => setEditNotes(e.target.value)} />
                          </div>
                          <div style={{ display: "flex", gap: 6, alignItems: "flex-end", paddingBottom: 1 }}>
                            <button className="btn-primary" style={{ fontSize: 13, padding: "7px 14px" }}
                              onClick={() => handleEdit(rec)}>Guardar</button>
                            <button className="btn-secondary" style={{ fontSize: 13, padding: "7px 14px" }}
                              onClick={() => setEditingId(null)}>Cancelar</button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {/* Access log */}
      <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 10, padding: 20 }}>
        <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 14 }}>🕒 Historial de acciones</div>
        {logs.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontSize: 13, textAlign: "center", padding: "20px 0" }}>
            Sin acciones registradas aún.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {logs.map(log => (
              <div key={log.id} style={{ display: "flex", alignItems: "flex-start", gap: 12,
                padding: "10px 12px", background: "var(--bg)", borderRadius: 8,
                border: "1px solid var(--border)" }}>
                <span style={{ fontSize: 18, lineHeight: 1 }}>{log.action_icon}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>
                    {log.action_label} —{" "}
                    <span style={{ color: "#818cf8" }}>{log.database_name}</span>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                    Usuario: {log.user_email}
                    {log.performed_by && ` · Por: ${log.performed_by}`}
                    {log.details && ` · ${log.details}`}
                  </div>
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                  {new Date(log.created_at).toLocaleString("es", { dateStyle: "short", timeStyle: "short" })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
