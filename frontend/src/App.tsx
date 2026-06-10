import { useEffect } from "react";
import { Sidebar, type View } from "./components/Sidebar";
import { ChatView } from "./components/ChatView";
import { UsersView } from "./components/UsersView";
import { LogsView } from "./components/LogsView";
import { LoginView } from "./components/LoginView";
import { TicketsView } from "./components/TicketsView";
import { FAQView } from "./components/FAQView";
import { TroubleshootingView } from "./components/TroubleshootingView";
import { EnvironmentView } from "./components/EnvironmentView";
import { HistoryView } from "./components/HistoryView";
import { DatabaseAccessView } from "./components/DatabaseAccessView";
import { DashboardView } from "./components/DashboardView";
import { useChat } from "./hooks/useChat";
import { useAuth } from "./hooks/useAuth";
import "./App.css";
import { useState } from "react";

const VIEW_META: Record<View, { title: string; subtitle: string }> = {
  chat:    { title: "💬 Chat con ATOS",       subtitle: "Conversa y ejecuta acciones de soporte" },
  users:   { title: "👥 Gestión de Usuarios",  subtitle: "Crea y administra cuentas del sistema" },
  tickets:         { title: "🎫 Tickets",           subtitle: "Sistema de gestión de incidencias" },
  faq:             { title: "❓ FAQ Inteligente",    subtitle: "Base de conocimiento del agente" },
  troubleshooting: { title: "🔧 Troubleshooting",   subtitle: "Flujos de diagnóstico guiado paso a paso" },
  environment:     { title: "⚙ Entorno",            subtitle: "Validación de herramientas, versiones y recursos del sistema" },
  history:         { title: "🧠 Historial",          subtitle: "Memoria de incidencias y soluciones probadas por ATOS" },
  logs:            { title: "📋 Audit Logs",        subtitle: "Historial de acciones ejecutadas por ATOS" },
  "db-access":     { title: "🗄️ DB Access",         subtitle: "Gestión de accesos a bases de datos" },
  dashboard:       { title: "📊 Dashboard",          subtitle: "Métricas y estado general del sistema" },
};

export default function App() {
  const [view, setView] = useState<View>("chat");
  const { token, user, loading: authLoading, error: authError, login, logout } = useAuth();
  const { messages, loading, backendOnline, sendMessage, checkBackend } = useChat(token);

  useEffect(() => {
    checkBackend();
  }, [checkBackend]);

  if (!user) {
    return (
      <LoginView
        onLogin={login}
        loading={authLoading}
        error={authError}
      />
    );
  }

  const meta = VIEW_META[view];

  return (
    <div className="layout">
      <Sidebar
        active={view}
        onChange={setView}
        backendOnline={backendOnline}
        user={user}
        onLogout={logout}
      />

      <div className="main">
        <div className="topbar">
          <div>
            <div className="topbar-title">{meta.title}</div>
            <div className="topbar-subtitle">{meta.subtitle}</div>
          </div>
          <span
            className="status-dot"
            style={{
              background:
                backendOnline === null ? "#555" : backendOnline ? "#4ade80" : "#f87171",
            }}
          />
          <span
            className="status-label"
            style={{
              color: backendOnline === null ? "#555" : backendOnline ? "#4ade80" : "#f87171",
              fontSize: 11,
            }}
          >
            {backendOnline === null ? "..." : backendOnline ? "Online" : "Offline"}
          </span>
        </div>

        <div
          className="content"
          style={view === "chat" ? { display: "flex", flexDirection: "column", overflow: "hidden", padding: "16px 24px" } : {}}
        >
          {view === "chat"    && <ChatView messages={messages} loading={loading} onSend={sendMessage} />}
          {view === "users"   && <UsersView token={token} />}
          {view === "tickets" && <TicketsView token={token} userEmail={user.email} />}
          {view === "logs"    && <LogsView />}
          {view === "faq"             && <FAQView />}
          {view === "troubleshooting" && <TroubleshootingView />}
          {view === "environment"     && <EnvironmentView token={token} />}
          {view === "history"         && <HistoryView token={token} />}
          {view === "db-access"      && <DatabaseAccessView token={token} />}
          {view === "dashboard"      && <DashboardView token={token} />}
        </div>
      </div>
    </div>
  );
}
