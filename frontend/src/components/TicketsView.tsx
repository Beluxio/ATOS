import { useEffect, useState } from "react";
import { useTickets, type Ticket } from "../hooks/useTickets";

interface Props {
  token: string | null;
  userEmail: string;
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

function TicketDetail({ ticket, onClose, onStatusChange, onAddResponse }: {
  ticket: Ticket;
  onClose: () => void;
  onStatusChange: (status: string) => void;
  onAddResponse: (content: string) => void;
}) {
  const [reply, setReply] = useState("");

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

        <div className="ticket-responses">
          {ticket.responses.map((r) => (
            <div key={r.id} className={`response-item ${r.is_auto ? "auto" : "manual"}`}>
              <div className="response-author">{r.author} · {formatDate(r.created_at)}</div>
              <div className="response-content">{r.content}</div>
            </div>
          ))}
        </div>

        <div className="ticket-actions">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Cambiar estado</label>
            <select value={ticket.status} onChange={(e) => onStatusChange(e.target.value)}>
              {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
            </select>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <input
              className="reply-input"
              placeholder="Añadir nota o respuesta..."
              value={reply}
              onChange={(e) => setReply(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && reply.trim()) {
                  onAddResponse(reply.trim());
                  setReply("");
                }
              }}
            />
            <button
              className="btn-primary"
              style={{ padding: "8px 16px" }}
              disabled={!reply.trim()}
              onClick={() => { onAddResponse(reply.trim()); setReply(""); }}
            >
              Enviar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function TicketsView({ token, userEmail }: Props) {
  const {
    tickets, selected, loading, error, success,
    fetchTickets, fetchTicket, createTicket, updateStatus, addResponse, clearSelected,
  } = useTickets(token);

  const [filterStatus, setFilterStatus] = useState("");
  const [form, setForm] = useState({ title: "", description: "", user_email: userEmail });

  useEffect(() => {
    fetchTickets({ status: filterStatus || undefined });
  }, [fetchTickets, filterStatus]);

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
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{ fontSize: 12, padding: "3px 8px", background: "#0f0f1a", border: "1px solid #2a2a44", color: "#6666a0", borderRadius: 6 }}
            >
              <option value="">Todos</option>
              {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
            </select>
            <button
              onClick={() => fetchTickets({ status: filterStatus || undefined })}
              style={{ fontSize: 12, background: "transparent", border: "1px solid #2a2a44", color: "#6666a0", padding: "3px 10px", borderRadius: 6, cursor: "pointer" }}
            >
              Actualizar
            </button>
          </div>
        </div>

        {tickets.length === 0 && !loading ? (
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
                  <th>Categoría</th>
                  <th>Creado</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => fetchTicket(t.id)}
                    style={{ cursor: "pointer" }}
                  >
                    <td style={{ color: "#44445a" }}>#{t.id}</td>
                    <td style={{ fontWeight: 600, color: "#c0c0e0", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
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
                    <td style={{ color: "#6666a0", fontSize: 12 }}>{t.category}</td>
                    <td style={{ color: "#55558a", fontSize: 12 }}>{formatDate(t.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="alert info" style={{ marginTop: 0 }}>
        💡 <strong>Demo:</strong> En el Chat dile a ATOS: <em>"Tengo un problema con mi contraseña, crea un ticket"</em>
      </div>

      {selected && (
        <TicketDetail
          ticket={selected}
          onClose={clearSelected}
          onStatusChange={(s) => updateStatus(selected.id, s)}
          onAddResponse={(c) => addResponse(selected.id, c)}
        />
      )}
    </div>
  );
}
