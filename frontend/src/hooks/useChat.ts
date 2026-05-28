import { useState, useCallback, useRef } from "react";
import { BACKEND_URL } from "../config";

export interface Message {
  role: "user" | "assistant";
  text: string;
}

type History = Array<Record<string, unknown>>;

function generateSessionId(): string {
  return crypto.randomUUID();
}

export function useChat(token: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const historyRef = useRef<History>([]);
  const sessionId = useRef(generateSessionId());

  const checkBackend = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/health`, { signal: AbortSignal.timeout(4000) });
      setBackendOnline(res.ok);
    } catch {
      setBackendOnline(false);
    }
  }, []);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || loading) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message: text,
          session_id: sessionId.current,
          history: historyRef.current,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      historyRef.current = data.history;
      setBackendOnline(true);
      setMessages((prev) => [...prev, { role: "assistant", text: data.reply }]);
    } catch {
      setBackendOnline(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "No pude conectar con el servidor. Asegúrate de que Docker y el tunnel estén activos.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [loading, token]);

  return { messages, loading, backendOnline, sendMessage, checkBackend };
}
