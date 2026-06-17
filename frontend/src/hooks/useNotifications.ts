import { useEffect, useRef, useState, useCallback } from "react";
import { BACKEND_URL } from "../config";

export interface Notification {
  id: string;
  type: "new_ticket" | "expiring_access" | "access_revoked";
  message: string;
  detail: string;
  at: Date;
  read: boolean;
}

let _counter = 0;
const uid = () => String(++_counter);

function buildNotification(event: string, data: Record<string, unknown>): Notification | null {
  const at = new Date();
  if (event === "new_ticket") {
    return {
      id: uid(),
      type: "new_ticket",
      message: "Ticket nuevo",
      detail: `#${data.id} — ${data.title} (${data.priority})`,
      at,
      read: false,
    };
  }
  if (event === "expiring_access") {
    return {
      id: uid(),
      type: "expiring_access",
      message: "Acceso BD por vencer",
      detail: `${data.user_email} → ${data.database_name} (${data.days_left}d restantes)`,
      at,
      read: false,
    };
  }
  if (event === "access_revoked") {
    return {
      id: uid(),
      type: "access_revoked",
      message: "Acceso BD revocado",
      detail: `${data.user_email} → ${data.database_name} (${data.status})`,
      at,
      read: false,
    };
  }
  return null;
}

export function useNotifications(token: string | null) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const esRef = useRef<EventSource | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const unread = notifications.filter(n => !n.read).length;

  const markAllRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }, []);

  const dismiss = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const push = useCallback((n: Notification) => {
    setNotifications(prev => [n, ...prev].slice(0, 50));
  }, []);

  useEffect(() => {
    if (!token) return;

    function connect() {
      // EventSource doesn't support custom headers — pass token as query param
      const url = `${BACKEND_URL}/api/notifications/stream?token=${encodeURIComponent(token!)}`;
      const es = new EventSource(url);
      esRef.current = es;

      es.addEventListener("new_ticket", (e: MessageEvent) => {
        const n = buildNotification("new_ticket", JSON.parse(e.data));
        if (n) push(n);
      });
      es.addEventListener("expiring_access", (e: MessageEvent) => {
        const n = buildNotification("expiring_access", JSON.parse(e.data));
        if (n) push(n);
      });
      es.addEventListener("access_revoked", (e: MessageEvent) => {
        const n = buildNotification("access_revoked", JSON.parse(e.data));
        if (n) push(n);
      });

      es.onerror = () => {
        es.close();
        esRef.current = null;
        retryRef.current = setTimeout(connect, 10_000);
      };
    }

    connect();

    return () => {
      esRef.current?.close();
      esRef.current = null;
      if (retryRef.current) clearTimeout(retryRef.current);
    };
  }, [token, push]);

  return { notifications, unread, markAllRead, dismiss };
}
