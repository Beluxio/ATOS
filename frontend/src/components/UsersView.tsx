import { useEffect, useState } from "react";
import { useAccounts } from "../hooks/useAccounts";

interface Props {
  token: string | null;
}

export function UsersView({ token }: Props) {
  const { accounts, loading, error, success, fetchAccounts, register, toggleLock, updateJobRole } =
    useAccounts(token);

  const [form, setForm] = useState({ email: "", username: "", password: "", role: "user" });

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await register(form.email, form.username, form.password, form.role);
    setForm({ email: "", username: "", password: "", role: "user" });
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString("es", { dateStyle: "short", timeStyle: "short" });

  return (
    <div>
      <div className="panel-header">
        <h2>👥 Gestión de Usuarios</h2>
        <p>Crea cuentas de prueba para demostrar las funcionalidades de ATOS.</p>
      </div>

      <div className="card">
        <div className="card-title">✏️ Registrar nuevo usuario</div>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                placeholder="usuario@ejemplo.com"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                placeholder="nombre de usuario"
                value={form.username}
                onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                required
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Contraseña</label>
              <input
                type="password"
                placeholder="mínimo 6 caracteres"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label>Rol</label>
              <select
                value={form.role}
                onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
              >
                <option value="user">user</option>
                <option value="agent">agent</option>
                <option value="admin">admin</option>
              </select>
            </div>
          </div>
          <div className="form-actions">
            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? "Registrando..." : "Crear cuenta"}
            </button>
          </div>
          {success && <div className="alert success">✅ {success}</div>}
          {error   && <div className="alert error">⚠️ {error}</div>}
        </form>
      </div>

      <div className="card">
        <div className="card-title" style={{ justifyContent: "space-between" }}>
          <span>📋 Cuentas registradas</span>
          <button
            onClick={fetchAccounts}
            style={{ fontSize: 12, background: "transparent", border: "1px solid #2a2a44", color: "#6666a0", padding: "3px 10px", borderRadius: 6, cursor: "pointer" }}
          >
            Actualizar
          </button>
        </div>

        {accounts.length === 0 && !loading ? (
          <div style={{ color: "#33334a", fontSize: 13, textAlign: "center", padding: "20px 0" }}>
            No hay cuentas registradas aún. Crea la primera arriba.
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Usuario</th>
                  <th>Email</th>
                  <th>Rol</th>
                  <th>Job Role</th>
                  <th>Estado</th>
                  <th>Intentos</th>
                  <th>Creada</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((acc) => (
                  <tr key={acc.id}>
                    <td style={{ color: "#44445a" }}>{acc.id}</td>
                    <td style={{ fontWeight: 600, color: "#c0c0e0" }}>{acc.username}</td>
                    <td>{acc.email}</td>
                    <td>
                      <span className={`badge role-${acc.role}`}>{acc.role}</span>
                    </td>
                    <td>
                      <select
                        value={acc.job_role ?? ""}
                        onChange={e => updateJobRole(acc.email, e.target.value || null)}
                        style={{ fontSize: 11, padding: "2px 6px", background: "var(--surface)",
                          border: "1px solid var(--border)", borderRadius: 6, color: acc.job_role ? "#818cf8" : "#44445a",
                          cursor: "pointer" }}
                      >
                        <option value="">— sin rol —</option>
                        <option value="frontend_dev">Frontend Dev</option>
                        <option value="backend_dev">Backend Dev</option>
                        <option value="data_scientist">Data Scientist</option>
                      </select>
                    </td>
                    <td>
                      <span className={`badge ${acc.status}`}>{acc.status}</span>
                    </td>
                    <td style={{ textAlign: "center", color: acc.failed_login_attempts > 0 ? "#f87171" : "#44445a" }}>
                      {acc.failed_login_attempts}
                    </td>
                    <td style={{ color: "#55558a", fontSize: 12 }}>{formatDate(acc.created_at)}</td>
                    <td>
                      <button
                        onClick={() => toggleLock(acc.email, acc.status)}
                        style={{
                          fontSize: 11,
                          padding: "3px 10px",
                          borderRadius: 6,
                          border: "1px solid",
                          cursor: "pointer",
                          background: "transparent",
                          borderColor: acc.status === "locked" ? "#166534" : "#7f1d1d",
                          color: acc.status === "locked" ? "#4ade80" : "#f87171",
                        }}
                      >
                        {acc.status === "locked" ? "Desbloquear" : "Bloquear"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="alert info" style={{ marginTop: 0 }}>
        💡 <strong>Demo:</strong> Crea un usuario y luego en el Chat pide a ATOS:{" "}
        <em>"Resetea la contraseña de usuario@ejemplo.com"</em> o{" "}
        <em>"Bloquea la cuenta de usuario@ejemplo.com"</em>
      </div>
    </div>
  );
}
