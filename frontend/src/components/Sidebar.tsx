import type { AuthUser } from "../hooks/useAuth";

export type View = "chat" | "users" | "tickets" | "faq" | "troubleshooting" | "environment" | "history" | "logs";

interface NavItem {
  id: View;
  icon: string;
  label: string;
  badge?: string;
  section?: string;
}

const NAV: NavItem[] = [
  { id: "chat",    icon: "💬", label: "Chat ATOS",  section: "Agente" },
  { id: "users",   icon: "👥", label: "Usuarios",   section: "Gestión" },
  { id: "tickets", icon: "🎫", label: "Tickets",    section: "" },
  { id: "faq",             icon: "❓", label: "FAQ" },
  { id: "troubleshooting", icon: "🔧", label: "Troubleshooting" },
  { id: "environment",     icon: "⚙",  label: "Entorno" },
  { id: "history",         icon: "🧠", label: "Historial" },
  { id: "logs",            icon: "📋", label: "Audit Logs", section: "Sistema" },
];

const ROLE_COLORS: Record<string, string> = {
  admin: "#f59e0b",
  agent: "#6366f1",
  user:  "#4ade80",
};

interface Props {
  active: View;
  onChange: (v: View) => void;
  backendOnline: boolean | null;
  user: AuthUser;
  onLogout: () => void;
}

export function Sidebar({ active, onChange, backendOnline, user, onLogout }: Props) {
  const dotColor =
    backendOnline === null ? "#555" : backendOnline ? "#4ade80" : "#f87171";
  const dotLabel =
    backendOnline === null ? "Verificando..." : backendOnline ? "Servidor activo" : "Servidor offline";

  let lastSection = "";

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>⚙ ATOS</h1>
        <p>Agente Técnico de<br />Operaciones de Soporte</p>
      </div>

      <nav className="sidebar-nav">
        {NAV.map((item) => {
          const showSection = item.section && item.section !== lastSection;
          if (item.section) lastSection = item.section;
          const disabled = item.badge === "pronto";

          return (
            <div key={item.id}>
              {showSection && (
                <div className="nav-section">{item.section}</div>
              )}
              <button
                className={`nav-item ${active === item.id ? "active" : ""}`}
                onClick={() => !disabled && onChange(item.id)}
                style={{ opacity: disabled ? 0.45 : 1, cursor: disabled ? "default" : "pointer" }}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
                {item.badge && <span className="nav-badge">{item.badge}</span>}
              </button>
            </div>
          );
        })}
      </nav>

      {/* User info */}
      <div className="sidebar-user">
        <div className="sidebar-user-info">
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className="sidebar-user-name">{user.username}</span>
            <span
              className="sidebar-user-role"
              style={{ color: ROLE_COLORS[user.role] ?? "#4ade80" }}
            >
              {user.role}
            </span>
          </div>
          <span className="sidebar-user-email">{user.email}</span>
        </div>
        <button className="logout-btn" onClick={onLogout} title="Cerrar sesión">
          ⏻
        </button>
      </div>

      <div className="sidebar-footer">
        <span
          style={{
            display: "inline-block",
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: dotColor,
            marginRight: 6,
            verticalAlign: "middle",
          }}
        />
        <span style={{ color: dotColor, fontSize: 11 }}>{dotLabel}</span>
      </div>
    </aside>
  );
}
