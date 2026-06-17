import { useState, useCallback } from "react";
import { BACKEND_URL } from "../config";

export interface TicketResponse {
  id: number;
  content: string;
  author: string;
  is_auto: boolean;
  created_at: string;
}

export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: "open" | "in_progress" | "resolved" | "closed" | "escalated";
  priority: "critical" | "high" | "medium" | "low";
  category: string;
  tags: string[];
  user_email: string;
  assigned_to: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
  responses: TicketResponse[];
}

export function useTickets(token: string | null) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selected, setSelected] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const headers = useCallback(
    () => ({
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }),
    [token]
  );

  const fetchTickets = useCallback(
    async (filters: { status?: string; priority?: string } = {}) => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (filters.status)   params.set("status", filters.status);
        if (filters.priority) params.set("priority", filters.priority);
        const res = await fetch(`${BACKEND_URL}/api/tickets?${params}`, { headers: headers() });
        setTickets(await res.json());
      } catch {
        setError("No se pudo conectar al servidor.");
      } finally {
        setLoading(false);
      }
    },
    [headers]
  );

  const fetchTicket = useCallback(
    async (id: number) => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/tickets/${id}`, { headers: headers() });
        const data = await res.json();
        setSelected(data);
      } catch {
        setError("Error al cargar el ticket.");
      }
    },
    [headers]
  );

  const createTicket = useCallback(
    async (title: string, description: string, user_email: string) => {
      setError(null);
      setSuccess(null);
      setLoading(true);
      try {
        const res = await fetch(`${BACKEND_URL}/api/tickets`, {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({ title, description, user_email }),
        });
        const data = await res.json();
        if (data.id) {
          setSuccess(`Ticket #${data.id} creado.`);
          await fetchTickets();
        } else {
          setError(data.detail || "Error al crear el ticket.");
        }
      } catch {
        setError("Error al conectar con el servidor.");
      } finally {
        setLoading(false);
      }
    },
    [headers, fetchTickets]
  );

  const updateStatus = useCallback(
    async (id: number, new_status: string, note?: string) => {
      try {
        await fetch(`${BACKEND_URL}/api/tickets/${id}/status`, {
          method: "PATCH",
          headers: headers(),
          body: JSON.stringify({ new_status, note }),
        });
        await fetchTickets();
        if (selected?.id === id) await fetchTicket(id);
      } catch {
        setError("Error al actualizar el ticket.");
      }
    },
    [headers, fetchTickets, fetchTicket, selected]
  );

  const addResponse = useCallback(
    async (id: number, content: string, author?: string) => {
      setError(null);
      try {
        await fetch(`${BACKEND_URL}/api/tickets/${id}/responses`, {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({ content, author: author || "Agente" }),
        });
        await fetchTicket(id);
        setSuccess("Respuesta añadida.");
      } catch {
        setError("Error al añadir respuesta.");
      }
    },
    [headers, fetchTicket]
  );

  const assignTicket = useCallback(
    async (id: number, assigned_to: string | null) => {
      setError(null);
      try {
        const res = await fetch(`${BACKEND_URL}/api/tickets/${id}/assign`, {
          method: "PATCH",
          headers: headers(),
          body: JSON.stringify({ assigned_to }),
        });
        const data = await res.json();
        if (data.id) {
          setSelected(data);
          await fetchTickets();
        }
      } catch {
        setError("Error al asignar el ticket.");
      }
    },
    [headers, fetchTickets]
  );

  return {
    tickets, selected, loading, error, success,
    fetchTickets, fetchTicket, createTicket, updateStatus, addResponse, assignTicket,
    clearSelected: () => setSelected(null),
  };
}
