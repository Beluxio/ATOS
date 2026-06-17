import { useState, useEffect, useRef } from "react";
import type { Notification } from "../hooks/useNotifications";

const TYPE_ICON: Record<Notification["type"], string> = {
  new_ticket:      "🎫",
  expiring_access: "⏰",
  access_revoked:  "🔒",
};

const TYPE_COLOR: Record<Notification["type"], string> = {
  new_ticket:      "#818cf8",
  expiring_access: "#facc15",
  access_revoked:  "#f87171",
};

interface Props {
  notifications: Notification[];
  unread: number;
  onMarkAllRead: () => void;
  onDismiss: (id: string) => void;
}

export function NotificationBell({ notifications, unread, onMarkAllRead, onDismiss }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const toggle = () => {
    setOpen(o => {
      if (!o && unread > 0) onMarkAllRead();
      return !o;
    });
  };

  return (
    <div ref={ref} style={{ position: "relative" }}>
      {/* Bell button */}
      <button
        onClick={toggle}
        style={{
          background: "transparent",
          border: "none",
          cursor: "pointer",
          padding: "6px 8px",
          borderRadius: 8,
          fontSize: 18,
          lineHeight: 1,
          position: "relative",
          color: "#f0f0f0",
          transition: "background 0.15s",
        }}
        title="Notificaciones"
      >
        🔔
        {unread > 0 && (
          <span style={{
            position: "absolute",
            top: 2,
            right: 2,
            background: "#f87171",
            color: "#fff",
            borderRadius: "50%",
            width: 16,
            height: 16,
            fontSize: 10,
            fontWeight: 700,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            lineHeight: 1,
          }}>
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div style={{
          position: "absolute",
          top: "calc(100% + 8px)",
          right: 0,
          width: 340,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 10,
          boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
          zIndex: 9999,
          overflow: "hidden",
        }}>
          {/* Header */}
          <div style={{
            padding: "12px 16px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}>
            <span style={{ fontWeight: 600, fontSize: 13 }}>Notificaciones</span>
            {notifications.length > 0 && (
              <button
                onClick={() => {
                  notifications.forEach(n => onDismiss(n.id));
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--text-muted)",
                  fontSize: 11,
                  padding: "2px 6px",
                }}
              >
                Limpiar todo
              </button>
            )}
          </div>

          {/* List */}
          <div style={{ maxHeight: 380, overflowY: "auto" }}>
            {notifications.length === 0 ? (
              <div style={{ padding: "24px 16px", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
                Sin notificaciones
              </div>
            ) : (
              notifications.map(n => (
                <div
                  key={n.id}
                  style={{
                    padding: "12px 16px",
                    borderBottom: "1px solid var(--border)",
                    display: "flex",
                    gap: 10,
                    alignItems: "flex-start",
                    background: n.read ? "transparent" : "rgba(129,140,248,0.05)",
                  }}
                >
                  <span style={{ fontSize: 18, lineHeight: 1.2 }}>{TYPE_ICON[n.type]}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: TYPE_COLOR[n.type] }}>
                      {n.message}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2, wordBreak: "break-word" }}>
                      {n.detail}
                    </div>
                    <div style={{ fontSize: 10, color: "#555", marginTop: 4 }}>
                      {n.at.toLocaleTimeString()}
                    </div>
                  </div>
                  <button
                    onClick={() => onDismiss(n.id)}
                    style={{
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                      color: "#555",
                      fontSize: 14,
                      padding: 2,
                      lineHeight: 1,
                      flexShrink: 0,
                    }}
                    title="Descartar"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
