import { useState, useRef, useEffect } from "react";
import type { Message } from "../hooks/useChat";

interface Props {
  messages: Message[];
  loading: boolean;
  onSend: (text: string) => void;
}

export function ChatView({ messages, loading, onSend }: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput("");
    inputRef.current?.focus();
  };

  return (
    <div className="chat-layout" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="chat-messages" style={{ flex: 1, overflowY: "auto" }}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="emoji">🤖</div>
            <h2>Hola, soy ATOS</h2>
            <p>Puedo resetear contraseñas, gestionar cuentas, crear tickets y más.</p>
            <p style={{ marginTop: 8 }}>¿En qué puedo ayudarte hoy?</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`bubble-wrap ${msg.role}`}>
            <div className={`bubble ${msg.role}`}>
              {msg.role === "assistant" && (
                <div className="bubble-name">ATOS</div>
              )}
              {msg.text}
            </div>
          </div>
        ))}

        {loading && (
          <div className="bubble-wrap assistant">
            <div className="typing-dots">
              <span /><span /><span />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-bar">
        <input
          ref={inputRef}
          type="text"
          placeholder="Escribe tu consulta o pide una acción..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          disabled={loading}
          autoFocus
        />
        <button className="btn-primary" onClick={handleSend} disabled={loading || !input.trim()}>
          Enviar
        </button>
      </div>
    </div>
  );
}
