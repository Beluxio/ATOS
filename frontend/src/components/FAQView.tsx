import { useEffect } from "react";
import { useFAQ, type FAQItem } from "../hooks/useFAQ";

const CATEGORY_COLORS: Record<string, string> = {
  password:  "#818cf8",
  account:   "#60a5fa",
  security:  "#f87171",
  tickets:   "#fbbf24",
  admin:     "#fb923c",
  technical: "#34d399",
  general:   "#6666a0",
};

const CATEGORIES = ["password", "account", "security", "tickets", "admin", "technical", "general"];

function FAQDetail({ item, onClose, onHelpful }: {
  item: FAQItem;
  onClose: () => void;
  onHelpful: () => void;
}) {
  return (
    <div className="ticket-detail-overlay" onClick={onClose}>
      <div className="ticket-detail" onClick={(e) => e.stopPropagation()}>
        <div className="ticket-detail-header">
          <div style={{ flex: 1 }}>
            <span
              className="badge-pill"
              style={{ background: (CATEGORY_COLORS[item.category] ?? "#6666a0") + "22", color: CATEGORY_COLORS[item.category] ?? "#6666a0", marginBottom: 6, display: "inline-block" }}
            >
              {item.category}
            </span>
            <h3 style={{ color: "#d0d0f0", marginTop: 4 }}>{item.question}</h3>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div style={{ padding: "16px 20px", overflowY: "auto", flex: 1 }}>
          <p style={{ fontSize: 14, color: "#b0b0d0", lineHeight: 1.65, marginBottom: 16 }}>
            {item.answer}
          </p>

          {item.steps.length > 0 && (
            <>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#6666a0", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 10 }}>
                Pasos a seguir
              </div>
              <ol className="faq-steps">
                {item.steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </>
          )}

          {item.tags.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 16 }}>
              {item.tags.map((tag) => (
                <span key={tag} className="badge-pill" style={{ background: "#1e1e32", color: "#6666a0" }}>
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: "12px 20px", borderTop: "1px solid #22223a", display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 12, color: "#44445a" }}>👁 {item.views} vistas · 👍 {item.helpful_count} útil</span>
          <button
            className="btn-primary"
            style={{ marginLeft: "auto", padding: "6px 16px", fontSize: 12 }}
            onClick={onHelpful}
          >
            👍 Fue útil
          </button>
        </div>
      </div>
    </div>
  );
}

export function FAQView() {
  const { items, selected, loading, query, setQuery, fetchAll, search, select, markHelpful, clearSelected } = useFAQ();

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    search(query);
  };

  // Group by category
  const grouped: Record<string, FAQItem[]> = {};
  for (const item of items) {
    if (!grouped[item.category]) grouped[item.category] = [];
    grouped[item.category].push(item);
  }

  return (
    <div>
      <div className="panel-header">
        <h2>❓ FAQ Inteligente</h2>
        <p>Base de conocimiento consultada por ATOS para responder preguntas frecuentes.</p>
      </div>

      {/* Buscador */}
      <div className="card" style={{ marginBottom: 16 }}>
        <form onSubmit={handleSearch} style={{ display: "flex", gap: 8 }}>
          <input
            className="reply-input"
            style={{ flex: 1, fontSize: 14, padding: "10px 14px" }}
            placeholder="Buscar en la FAQ... (ej: contraseña, bloqueo, ticket)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn-primary" type="submit" disabled={loading}>
            Buscar
          </button>
          {query && (
            <button
              type="button"
              onClick={() => { setQuery(""); fetchAll(); }}
              style={{ padding: "10px 14px", background: "transparent", border: "1px solid #2a2a44", color: "#6666a0", borderRadius: 10, cursor: "pointer", fontSize: 13 }}
            >
              Limpiar
            </button>
          )}
        </form>

        {/* Filtros por categoría */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 12 }}>
          <button
            onClick={() => { setQuery(""); fetchAll(); }}
            className="faq-cat-btn"
          >
            Todas
          </button>
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => { setQuery(""); fetchAll(cat); }}
              className="faq-cat-btn"
              style={{ color: CATEGORY_COLORS[cat] ?? "#6666a0", borderColor: (CATEGORY_COLORS[cat] ?? "#2a2a44") + "44" }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Lista */}
      {loading ? (
        <div style={{ color: "#33334a", textAlign: "center", padding: 40 }}>Cargando...</div>
      ) : items.length === 0 ? (
        <div style={{ color: "#33334a", textAlign: "center", padding: 40 }}>
          No se encontraron resultados para <em>"{query}"</em>
        </div>
      ) : query ? (
        /* Resultados de búsqueda: lista plana */
        <div className="card">
          <div className="card-title">{items.length} resultado{items.length !== 1 ? "s" : ""}</div>
          {items.map((item) => (
            <FAQCard key={item.id} item={item} onClick={() => select(item.id)} />
          ))}
        </div>
      ) : (
        /* Vista normal: agrupada por categoría */
        Object.entries(grouped).map(([cat, catItems]) => (
          <div key={cat} className="card" style={{ marginBottom: 16 }}>
            <div className="card-title" style={{ color: CATEGORY_COLORS[cat] ?? "#6666a0" }}>
              {cat.toUpperCase()} · {catItems.length}
            </div>
            {catItems.map((item) => (
              <FAQCard key={item.id} item={item} onClick={() => select(item.id)} />
            ))}
          </div>
        ))
      )}

      <div className="alert info" style={{ marginTop: 0 }}>
        💡 <strong>Demo:</strong> En el Chat pregunta: <em>"¿Cómo reseteo mi contraseña?"</em> o <em>"¿Qué roles existen?"</em> — ATOS consultará la FAQ automáticamente.
      </div>

      {selected && (
        <FAQDetail
          item={selected}
          onClose={clearSelected}
          onHelpful={() => markHelpful(selected.id)}
        />
      )}
    </div>
  );
}

function FAQCard({ item, onClick }: { item: FAQItem; onClick: () => void }) {
  return (
    <div className="faq-card" onClick={onClick}>
      <div className="faq-card-q">{item.question}</div>
      <div className="faq-card-a">{item.answer.slice(0, 100)}...</div>
      <div style={{ display: "flex", gap: 6, marginTop: 6, alignItems: "center" }}>
        {item.tags.slice(0, 3).map((tag) => (
          <span key={tag} className="badge-pill" style={{ background: "#1e1e32", color: "#44445a", fontSize: 10 }}>
            #{tag}
          </span>
        ))}
        <span style={{ marginLeft: "auto", fontSize: 10, color: "#33334a" }}>
          👁 {item.views} · 👍 {item.helpful_count}
        </span>
      </div>
    </div>
  );
}
