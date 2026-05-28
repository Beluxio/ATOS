import { useEffect } from "react";
import { useTroubleshooting, type TSFlow } from "../hooks/useTroubleshooting";

const CATEGORY_META: Record<string, { icon: string; color: string }> = {
  nodejs:      { icon: "⬡", color: "#4ade80" },
  python:      { icon: "🐍", color: "#facc15" },
  network:     { icon: "🌐", color: "#60a5fa" },
  permissions: { icon: "🔒", color: "#f87171" },
  docker:      { icon: "🐳", color: "#38bdf8" },
  git:         { icon: "⎇",  color: "#fb923c" },
  environment: { icon: "⚙",  color: "#a78bfa" },
};

const CATEGORIES = Object.keys(CATEGORY_META);

function FlowDetail({ flow, onClose }: { flow: TSFlow; onClose: () => void }) {
  const meta = CATEGORY_META[flow.category] ?? { icon: "🔧", color: "#6666a0" };

  return (
    <div className="ticket-detail-overlay" onClick={onClose}>
      <div className="ticket-detail" onClick={(e) => e.stopPropagation()}>
        <div className="ticket-detail-header">
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: 11, color: meta.color, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px" }}>
              {meta.icon} {flow.category}
            </span>
            <h3 style={{ color: "#d0d0f0", marginTop: 4 }}>{flow.name}</h3>
            <p style={{ fontSize: 12, color: "#55558a", marginTop: 4 }}>{flow.description}</p>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div style={{ overflowY: "auto", flex: 1, padding: "16px 20px" }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#6666a0", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 14 }}>
            {flow.steps?.length} pasos de diagnóstico
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {flow.steps?.map((step) => (
              <div key={step.step} className="ts-step">
                <div className="ts-step-num" style={{ background: meta.color + "22", color: meta.color }}>
                  {step.step}
                </div>
                <div className="ts-step-body">
                  <div className="ts-step-title">{step.title}</div>
                  <div className="ts-step-action">
                    <span style={{ color: "#44445a", fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>Acción: </span>
                    {step.action}
                  </div>
                  <div className="ts-step-expected">
                    <span style={{ color: "#166534", fontSize: 11, fontWeight: 700 }}>✓ Esperado: </span>
                    {step.expected}
                  </div>
                  {step.hint && (
                    <div className="ts-step-hint">💡 {step.hint}</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="alert info" style={{ marginTop: 16 }}>
            💬 <strong>Tip:</strong> En el Chat dile a ATOS:{" "}
            <em>"{flow.trigger_patterns[0]}"</em> y te guiará paso a paso.
          </div>
        </div>
      </div>
    </div>
  );
}

function FlowCard({ flow, onClick }: { flow: TSFlow; onClick: () => void }) {
  const meta = CATEGORY_META[flow.category] ?? { icon: "🔧", color: "#6666a0" };
  return (
    <div className="faq-card" onClick={onClick}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 18 }}>{meta.icon}</span>
        <span className="faq-card-q" style={{ margin: 0 }}>{flow.name}</span>
      </div>
      <div className="faq-card-a">{flow.description}</div>
      <div style={{ display: "flex", gap: 6, marginTop: 8, alignItems: "center" }}>
        <span className="badge-pill" style={{ background: meta.color + "22", color: meta.color }}>
          {flow.category}
        </span>
        <span style={{ fontSize: 11, color: "#44445a", marginLeft: "auto" }}>
          {flow.step_count} pasos
        </span>
      </div>
    </div>
  );
}

export function TroubleshootingView() {
  const { flows, selected, loading, query, setQuery, fetchAll, search, selectFlow, clearSelected } = useTroubleshooting();

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    search(query);
  };

  const grouped: Record<string, TSFlow[]> = {};
  for (const f of flows) {
    if (!grouped[f.category]) grouped[f.category] = [];
    grouped[f.category].push(f);
  }

  return (
    <div>
      <div className="panel-header">
        <h2>🔧 Troubleshooting Guiado</h2>
        <p>Flujos de diagnóstico paso a paso para errores comunes. ATOS los ejecuta interactivamente en el chat.</p>
      </div>

      {/* Buscador */}
      <div className="card" style={{ marginBottom: 16 }}>
        <form onSubmit={handleSearch} style={{ display: "flex", gap: 8 }}>
          <input
            className="reply-input"
            style={{ flex: 1, fontSize: 14, padding: "10px 14px" }}
            placeholder='Buscar flujo... (ej: "npm error", "permission denied", "docker")'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn-primary" type="submit" disabled={loading}>Buscar</button>
          {query && (
            <button type="button" onClick={() => { setQuery(""); fetchAll(); }}
              style={{ padding: "10px 14px", background: "transparent", border: "1px solid #2a2a44", color: "#6666a0", borderRadius: 10, cursor: "pointer", fontSize: 13 }}>
              Limpiar
            </button>
          )}
        </form>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 12 }}>
          <button onClick={() => { setQuery(""); fetchAll(); }} className="faq-cat-btn">Todos</button>
          {CATEGORIES.map((cat) => {
            const m = CATEGORY_META[cat];
            return (
              <button key={cat} onClick={() => { setQuery(""); fetchAll(cat); }}
                className="faq-cat-btn"
                style={{ color: m.color, borderColor: m.color + "44" }}>
                {m.icon} {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Lista */}
      {loading ? (
        <div style={{ color: "#33334a", textAlign: "center", padding: 40 }}>Cargando...</div>
      ) : flows.length === 0 ? (
        <div style={{ color: "#33334a", textAlign: "center", padding: 40 }}>
          No se encontraron flujos para <em>"{query}"</em>
        </div>
      ) : query ? (
        <div className="card">
          <div className="card-title">{flows.length} resultado{flows.length !== 1 ? "s" : ""}</div>
          {flows.map((f) => <FlowCard key={f.id} flow={f} onClick={() => selectFlow(f.id)} />)}
        </div>
      ) : (
        Object.entries(grouped).map(([cat, catFlows]) => {
          const m = CATEGORY_META[cat] ?? { icon: "🔧", color: "#6666a0" };
          return (
            <div key={cat} className="card" style={{ marginBottom: 16 }}>
              <div className="card-title" style={{ color: m.color }}>
                {m.icon} {cat.toUpperCase()} · {catFlows.length}
              </div>
              {catFlows.map((f) => <FlowCard key={f.id} flow={f} onClick={() => selectFlow(f.id)} />)}
            </div>
          );
        })
      )}

      <div className="alert info" style={{ marginTop: 0 }}>
        💡 <strong>Demo:</strong> En el Chat pega un error real y dile a ATOS:{" "}
        <em>"Tengo este error: Cannot find module 'express'"</em> — identificará el flujo y te guiará paso a paso.
      </div>

      {selected && (
        <FlowDetail flow={selected} onClose={clearSelected} />
      )}
    </div>
  );
}
