import { useEffect, useState, useCallback } from "react";
import { BACKEND_URL } from "../config";
import { useTickets, type Ticket } from "../hooks/useTickets";

interface Props {
  token: string | null;
  userEmail: string;
  userRole?: string;
}

const SLA_HOURS: Record<string, number> = { critical: 4, high: 8, medium: 24, low: 72 };

function slaInfo(ticket: Ticket): { hours: number; limit: number; ok: boolean } | null {
  if (!ticket.resolved_at) return null;
  const hours = (new Date(ticket.resolved_at).getTime() - new Date(ticket.created_at).getTime()) / 3_600_000;
  const limit = SLA_HOURS[ticket.priority] ?? 24;
  return { hours: Math.round(hours * 10) / 10, limit, ok: hours <= limit };
}

const STATUS_COLORS: Record<string, string> = {
  open:        "#60a5fa",
  in_progress: "#fbbf24",
  resolved:    "#4ade80",
  closed:      "#44445a",
  escalated:   "#f87171",
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: "#f87171",
  high:     "#fb923c",
  medium:   "#fbbf24",
  low:      "#4ade80",
};

const STATUSES = ["open", "in_progress", "resolved", "closed", "escalated"];

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("es", { dateStyle: "short", timeStyle: "short" });
}

function TicketDetail({ ticket, authorEmail, agents, onClose, onStatusChange, onAddResponse, onAssign }: {
  ticket: Ticket;
  authorEmail: string;
  agents: string[];
  onClose: () => void;
  onStatusChange: (status: string) => void;
  onAddResponse: (content: string, author: string) => void;
  onAssign: (assigned_to: string | null) => void;
}) {
  const [reply, setReply] = useState("");
  const sla = slaInfo(ticket);

  const submit = () => {
    if (!reply.trim()) return;
    onAddResponse(reply.trim(), authorEmail);
    setReply("");
  };

  return (
    <div className="ticket-detail-overlay" onClick={onClose}>
      <div className="ticket-detail" onClick={(e) => e.stopPropagation()}>
        <div className="ticket-detail-header">
          <div>
            <span style={{ color: "#44445a", fontSize: 12 }}>Ticket #{ticket.id}</span>
            <h3 style={{ color: "#d0d0f0", margin: "4px 0 0" }}>{ticket.title}</h3>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="ticket-meta-row">
          <span className="badge-pill" style={{ background: STATUS_COLORS[ticket.status] + "22", color: STATUS_COLORS[ticket.status] }}>
            {ticket.status.replace("_", " ")}
          </span>
          <span className="badge-pill" style={{ background: PRIORITY_COLORS[ticket.priority] + "22", color: PRIORITY_COLORS[ticket.priority] }}>
            {ticket.priority}
          </span>
          <span className="badge-pill" style={{ background: "#1e1e32", color: "#6666a0" }}>
            {ticket.category}
          </span>
          <span style={{ marginLeft: "auto", fontSize: 11, color: "#44445a" }}>
            {ticket.user_email} · {formatDate(ticket.created_at)}
          </span>
        </div>

        <p style={{ fontSize: 13, color: "#b0b0d0", lineHeight: 1.6, padding: "12px 0", borderBottom: "1px solid #22223a" }}>
          {ticket.description}
        </p>

        {/* Timeline */}
        <div className="ticket-responses" style={{ maxHeight: 280, overflowY: "auto" }}>
          {ticket.responses.map((r) => (
            <div key={r.id} style={{
              display: "flex",
              gap: 10,
              padding: "10px 0",
              borderBottom: "1px solid #1a1a2e",
            }}>
              <div style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: r.is_auto ? "#1e1e3a" : "#1a2e1a",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 14,
                flexShrink: 0,
              }}>
                {r.is_auto ? "🤖" : "💬"}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: r.is_auto ? "#6666a0" : "#4ade80" }}>
                    {r.author}
                  </span>
                  <span style={{ fontSize: 10, color: "#44445a" }}>{formatDate(r.created_at)}</span>
                </div>
                <div style={{ fontSize: 13, color: "#b0b0d0", lineHeight: 1.5 }}>{r.content}</div>
              </div>
            </div>
          ))}
        </div>

        {sla && (
          <div style={{
            padding: "8px 12px", borderRadius: 6, marginBottom: 8,
            background: sla.ok ? "rgba(74,222,128,0.08)" : "rgba(248,113,113,0.08)",
            border: `1px solid ${sla.ok ? "#4ade8044" : "#f8717144"}`,
            fontSize: 12, color: sla.ok ? "#4ade80" : "#f87171",
          }}>
            {sla.ok ? "✅" : "⚠️"} Resuelto en <strong>{sla.hours}h</strong>
            {" "}(SLA {ticket.priority}: {sla.limit}h — {sla.ok ? "cumplido" : "excedido"})
          </div>
        )}

        <div className="ticket-actions">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Estado</label>
              <select value={ticket.status} onChange={(e) => onStatusChange(e.target.value)}>
                {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Asignar a</label>
              <select
                value={ticket.assigned_to || ""}
                onChange={(e) => onAssign(e.target.value || null)}
              >
                <option value="">— Sin asignar —</option>
                {agents.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <input
              className="reply-input"
              placeholder="Añadir comentario... (el usuario recibirá un email)"
              value={reply}
              onChange={(e) => setReply(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
            />
            <button
              className="btn-primary"
              style={{ padding: "8px 16px" }}
              disabled={!reply.trim()}
              onClick={submit}
            >
              Enviar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function TicketsView({ token, userEmail, userRole }: Props) {
  const {
    tickets, selected, loading, error, success,
    fetchTickets, fetchTicket, createTicket, updateStatus, addResponse, assignTicket, clearSelected,
  } = useTickets(token);

  const [filterStatus, setFilterStatus] = useState("");
  const [filterAgent, setFilterAgent] = useState("");
  const [agents, setAgents] = useState<string[]>([]);
  const [form, setForm] = useState({ title: "", description: "", user_email: userEmail });

  const canAssign = userRole === "admin" || userRole === "agent";

  const loadAgents = useCallback(async () => {
    if (!token || !canAssign) return;
    try {
      const r = await fetch(`${BACKEND_URL}/api/accounts`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (r.ok) {
        const all: { email: string; role: string }[] = await r.json();
        setAgents(all.filter(a => a.role === "agent" || a.role === "admin").map(a => a.email));
      }
    } catch { /* sin agentes disponibles */ }
  }, [token, canAssign]);

  useEffect(() => {
    fetchTickets({ status: filterStatus || undefined });
  }, [fetchTickets, filterStatus]);

  useEffect(() => { loadAgents(); }, [loadAgents]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createTicket(form.title, form.description, form.user_email);
    setForm({ title: "", description: "", user_email: userEmail });
  };

  return (
    <div>
      <div className="panel-header">
        <h2>🎫 Gestión de Tickets</h2>
        <p>Crea y gestiona incidencias. ATOS puede crearlas automáticamente desde el chat.</p>
      </div>

      {/* Crear ticket */}
      <div className="card">
        <div className="card-title">✏️ Nuevo ticket</div>
        <form onSubmit={handleCreate}>
          <div className="form-row">
            <div className="form-group">
              <label>Título</label>
              <input
                placeholder="Resumen breve del problema"
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label>Email del usuario</label>
              <input
                type="email"
                value={form.user_email}
                onChange={(e) => setForm((f) => ({ ...f, user_email: e.target.value }))}
                required
              />
            </div>
          </div>
          <div className="form-group">
            <label>Descripción</label>
            <textarea
              placeholder="Describe el problema con detalle..."
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              required
              rows={3}
            />
          </div>
          <div className="form-actions">
            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? "Creando..." : "Crear ticket"}
            </button>
          </div>
          {success && <div className="alert success">✅ {success}</div>}
          {error   && <div className="alert error">⚠️ {error}</div>}
        </form>
      </div>

      {/* Lista de tickets */}
      <div className="card">
        <div className="card-title" style={{ justifyContent: "space-between" }}>
          <span>📋 Tickets</span>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{ fontSize: 12, padding: "3px 8px", background: "#0f0f1a", border: "1px solid #2a2a44", color: "#6666a0", borderRadius: 6 }}
            >
              <option value="">Todos los estados</option>
              {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
            </select>
            {canAssign && agents.length > 0 && (
              <select
                value={filterAgent}
                onChange={(e) => setFilterAgent(e.target.value)}
                style={{ fontSize: 12, padding: "3px 8px", background: "#0f0f1a", border: "1px solid #2a2a44", color: "#6666a0", borderRadius: 6 }}
              >
                <option value="">Todos los agentes</option>
                <option value="unassigned">Sin asignar</option>
                {agents.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            )}
            <button
              onClick={() => fetchTickets({ status: filterStatus || undefined })}
              style={{ fontSize: 12, background: "transparent", border: "1px solid #2a2a44", color: "#6666a0", padding: "3px 10px", borderRadius: 6, cursor: "pointer" }}
            >
              Actualizar
            </button>
          </div>
        </div>

        {(() => {
          const filtered = tickets.filter(t => {
            if (filterAgent === "unassigned") return !t.assigned_to;
            if (filterAgent) return t.assigned_to === filterAgent;
            return true;
          });
          return filtered.length === 0 && !loading ? (
            <div style={{ color: "#33334a", fontSize: 13, textAlign: "center", padding: "20px 0" }}>
              No hay tickets. Crea uno arriba o pídele a ATOS: <em>"Crea un ticket por problema de login"</em>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Título</th>
                    <th>Usuario</th>
                    <th>Estado</th>
                    <th>Prioridad</th>
                    <th>Asignado a</th>
                    <th>SLA</th>
                    <th>Creado</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((t) => {
                    const sla = slaInfo(t);
                    return (
                      <tr key={t.id} onClick={() => fetchTicket(t.id)} style={{ cursor: "pointer" }}>
                        <td style={{ color: "#44445a" }}>#{t.id}</td>
                        <td style={{ fontWeight: 600, color: "#c0c0e0", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {t.title}
                        </td>
                        <td style={{ fontSize: 12 }}>{t.user_email}</td>
                        <td>
                          <span className="badge-pill" style={{ background: STATUS_COLORS[t.status] + "22", color: STATUS_COLORS[t.status] }}>
                            {t.status.replace("_", " ")}
                          </span>
                        </td>
                        <td>
                          <span className="badge-pill" style={{ background: PRIORITY_COLORS[t.priority] + "22", color: PRIORITY_COLORS[t.priority] }}>
                            {t.priority}
                          </span>
                        </td>
                        <td style={{ fontSize: 11, color: t.assigned_to ? "#818cf8" : "#33334a" }}>
                          {t.assigned_to ? t.assigned_to.split("@")[0] : "—"}
                        </td>
                        <td style={{ fontSize: 11 }}>
                          {sla ? (
                            <span style={{ color: sla.ok ? "#4ade80" : "#f87171" }}>
                              {sla.ok ? "✅" : "⚠️"} {sla.hours}h
                            </span>
                          ) : (
                            <span style={{ color: "#33334a" }}>—</span>
                          )}
                        </td>
                        <td style={{ color: "#55558a", fontSize: 12 }}>{formatDate(t.created_at)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          );
        })()}
      </div>

      <div className="alert info" style={{ marginTop: 0 }}>
        💡 <strong>Demo:</strong> En el Chat dile a ATOS: <em>"Tengo un problema con mi contraseña, crea un ticket"</em>
      </div>

      {selected && (
        <TicketDetail
          ticket={selected}
          authorEmail={userEmail}
          agents={agents}
          onClose={clearSelected}
          onStatusChange={(s) => updateStatus(selected.id, s)}
          onAddResponse={(c, author) => addResponse(selected.id, c, author)}
          onAssign={(a) => assignTicket(selected.id, a)}
        />
      )}
    </div>
  );
}
