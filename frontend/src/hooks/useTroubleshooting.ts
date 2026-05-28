import { useState, useCallback } from "react";
import { BACKEND_URL } from "../config";

export interface TSStep {
  step: number;
  title: string;
  action: string;
  expected: string;
  hint: string;
}

export interface TSFlow {
  id: number;
  name: string;
  description: string;
  category: string;
  trigger_patterns: string[];
  step_count: number;
  steps?: TSStep[];
}

export function useTroubleshooting() {
  const [flows, setFlows] = useState<TSFlow[]>([]);
  const [selected, setSelected] = useState<TSFlow | null>(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");

  const fetchAll = useCallback(async (category?: string) => {
    setLoading(true);
    try {
      const params = category ? `?category=${category}` : "";
      const res = await fetch(`${BACKEND_URL}/api/troubleshooting${params}`);
      setFlows(await res.json());
      setSelected(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const search = useCallback(async (q: string) => {
    if (!q.trim()) { fetchAll(); return; }
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/troubleshooting/search?q=${encodeURIComponent(q)}`);
      setFlows(await res.json());
      setSelected(null);
    } finally {
      setLoading(false);
    }
  }, [fetchAll]);

  const selectFlow = useCallback(async (id: number) => {
    const res = await fetch(`${BACKEND_URL}/api/troubleshooting/${id}`);
    setSelected(await res.json());
  }, []);

  return { flows, selected, loading, query, setQuery, fetchAll, search, selectFlow, clearSelected: () => setSelected(null) };
}
