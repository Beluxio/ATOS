import { useState, useCallback } from "react";
import { BACKEND_URL } from "../config";

export interface Account {
  id: number;
  email: string;
  username: string;
  status: "active" | "locked" | "pending";
  role: "user" | "agent" | "admin";
  job_role: "frontend_dev" | "backend_dev" | "data_scientist" | null;
  failed_login_attempts: number;
  locked_until: string | null;
  created_at: string;
  updated_at: string;
}

export function useAccounts(token: string | null) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const authHeaders = useCallback(
    (extra?: Record<string, string>) => ({
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...extra,
    }),
    [token]
  );

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/accounts`, { headers: authHeaders() });
      const data = await res.json();
      setAccounts(data);
    } catch {
      setError("No se pudo conectar al servidor.");
    } finally {
      setLoading(false);
    }
  }, [authHeaders]);

  const register = useCallback(
    async (email: string, username: string, password: string, role: string = "user") => {
      setError(null);
      setSuccess(null);
      setLoading(true);
      try {
        const res = await fetch(`${BACKEND_URL}/api/accounts/register`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ email, username, password, role }),
        });
        const data = await res.json();
        if (data.status === "ok") {
          setSuccess(data.message);
          await fetchAccounts();
        } else {
          setError(data.message);
        }
      } catch {
        setError("Error al conectar con el servidor.");
      } finally {
        setLoading(false);
      }
    },
    [authHeaders, fetchAccounts]
  );

  const toggleLock = useCallback(
    async (email: string, currentStatus: string) => {
      const action = currentStatus === "locked" ? "unlock" : "lock";
      try {
        await fetch(`${BACKEND_URL}/api/accounts/${encodeURIComponent(email)}/${action}`, {
          method: "POST",
          headers: authHeaders(),
        });
        await fetchAccounts();
      } catch {
        setError("Error al actualizar la cuenta.");
      }
    },
    [authHeaders, fetchAccounts]
  );

  const updateJobRole = useCallback(
    async (email: string, job_role: string | null) => {
      try {
        await fetch(`${BACKEND_URL}/api/accounts/${encodeURIComponent(email)}/job-role`, {
          method: "PATCH",
          headers: authHeaders(),
          body: JSON.stringify({ job_role }),
        });
        await fetchAccounts();
      } catch {
        setError("Error al actualizar el job role.");
      }
    },
    [authHeaders, fetchAccounts]
  );

  return { accounts, loading, error, success, fetchAccounts, register, toggleLock, updateJobRole };
}
