# ATOS — Agente Técnico de Operaciones de Soporte

Agente de helpdesk inteligente con Gemini 2.5 Flash, FastAPI, PostgreSQL y React.

## Requisitos

- Docker Desktop
- Node.js 20+
- Python 3.12+ (solo para desarrollo local sin Docker)
- cloudflared (para exponer públicamente)

## Inicio rápido

### 1. Configurar variables de entorno

```bash
cp backend/.env.example backend/.env
# Editar backend/.env y poner tu GEMINI_API_KEY y SECRET_KEY
```

Obtén tu API key gratuita en: https://aistudio.google.com/apikey

### 2. Levantar el backend

```bash
docker-compose up -d
```

Backend disponible en: http://localhost:8002
Documentación API: http://localhost:8002/docs

### 3. Instalar y correr el frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponible en: http://localhost:5173

### 4. Exponer públicamente (opcional)

```bash
cloudflared tunnel --url http://localhost:8002
# Copiar el URL generado → pegar en frontend/src/config.ts
# Rebuild: npm run build && npx gh-pages -d dist
```

Ver instrucciones completas en [cloudflare-tunnel.md](./cloudflare-tunnel.md)

## Bloques implementados

- [x] Bloque 0: Foundation & Core Agent
- [x] Bloque 1: Reset de Contraseñas
- [ ] Bloque 2: Gestión de Cuentas
- [ ] Bloque 3: Gestión de Tickets
- [ ] Bloque 4: FAQ Inteligente
- [ ] Bloque 5: Troubleshooting Guiado
- [ ] Bloque 6: Reparación de Dependencias
- [ ] Bloque 7: Validación de Entorno
- [ ] Bloque 8: Acciones Automatizadas
- [ ] Bloque 9: Historial y Memoria

## Stack

| Capa | Tecnología |
|------|-----------|
| IA | Gemini 2.5 Flash (gratis) |
| Backend | Python 3.12 + FastAPI |
| Base de datos | PostgreSQL 16 |
| Frontend | React 18 + Vite + TypeScript |
| Hosting frontend | GitHub Pages |
| Exposición pública | Cloudflare Tunnel |
| Contenerización | Docker + docker-compose |
