import { useState } from "react";

interface Props {
  onLogin: (email: string, password: string) => Promise<boolean>;
  loading: boolean;
  error: string | null;
}

export function LoginView({ onLogin, loading, error }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onLogin(email, password);
  };

  return (
    <div className="login-overlay">
      <div className="login-card">
        <div className="login-logo">
          <span style={{ fontSize: 40 }}>⚙</span>
          <h1>ATOS</h1>
          <p>Agente Técnico de Operaciones de Soporte</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="usuario@ejemplo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>Contraseña</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <div className="alert error">⚠️ {error}</div>}

          <button className="btn-primary login-btn" type="submit" disabled={loading}>
            {loading ? "Iniciando sesión..." : "Iniciar sesión"}
          </button>
        </form>

        <p className="login-hint">
          ¿No tienes cuenta? Pide a un administrador que la cree en el panel de Usuarios.
        </p>
      </div>
    </div>
  );
}
