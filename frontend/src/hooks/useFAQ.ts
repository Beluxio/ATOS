import { useState, useCallback } from "react";
import { BACKEND_URL } from "../config";

export interface FAQItem {
  id: number;
  question: string;
  answer: string;
  steps: string[];
  tags: string[];
  category: string;
  views: number;
  helpful_count: number;
}

export function useFAQ() {
  const [items, setItems] = useState<FAQItem[]>([]);
  const [selected, setSelected] = useState<FAQItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");

  const fetchAll = useCallback(async (category?: string) => {
    setLoading(true);
    try {
      const params = category ? `?category=${category}` : "";
      const res = await fetch(`${BACKEND_URL}/api/faq${params}`);
      setItems(await res.json());
      setSelected(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const search = useCallback(async (q: string) => {
    if (!q.trim()) { fetchAll(); return; }
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/faq/search?q=${encodeURIComponent(q)}`);
      setItems(await res.json());
      setSelected(null);
    } finally {
      setLoading(false);
    }
  }, [fetchAll]);

  const select = useCallback(async (id: number) => {
    const res = await fetch(`${BACKEND_URL}/api/faq/${id}`);
    setSelected(await res.json());
  }, []);

  const markHelpful = useCallback(async (id: number) => {
    await fetch(`${BACKEND_URL}/api/faq/${id}/helpful`, { method: "POST" });
    setSelected((prev) => prev ? { ...prev, helpful_count: prev.helpful_count + 1 } : prev);
  }, []);

  return { items, selected, loading, query, setQuery, fetchAll, search, select, markHelpful, clearSelected: () => setSelected(null) };
}
