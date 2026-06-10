# ATOS — Agente Técnico de Operaciones de Soporte

AI helpdesk agent: FastAPI backend + React frontend. The agent uses OpenAI with tool calling to execute real support actions, not just answer text.

---

## Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI — model set via `OPENAI_MODEL` env var (default `gpt-4.1-mini`) |
| Backend | Python 3.12 + FastAPI + SQLAlchemy async + Alembic |
| Database | PostgreSQL 16 (via asyncpg) |
| Auth | JWT (python-jose) + bcrypt passwords |
| Email | Resend (real sending via `RESEND_API_KEY`) |
| Frontend | React 18 + TypeScript + Vite |
| Frontend hosting | Cloudflare Pages → `https://atos.beluxio.org` |
| Public API | Cloudflare Tunnel → `https://api.beluxio.org` |
| Containerization | Docker + docker-compose |
| Demo portal | DataCo Analytics portal — `portal/` (React, Vite, port 5174) |

---

## Directory Structure

```
ATOS/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── agent.py           # OpenAI client, tool routing, chat loop
│   │   │   ├── tools/             # Tool modules (registered via decorator)
│   │   │   │   ├── registry.py    # TOOL_REGISTRY + get_tool_declarations()
│   │   │   │   ├── base_tools.py
│   │   │   │   ├── password_reset.py
│   │   │   │   ├── tickets.py
│   │   │   │   ├── faq.py
│   │   │   │   ├── troubleshooting.py
│   │   │   │   ├── dependencies.py
│   │   │   │   ├── environment.py
│   │   │   │   ├── automated_actions.py
│   │   │   │   └── memory.py
│   │   │   └── prompts/
│   │   │       └── system_prompt.py
│   │   ├── core/
│   │   │   ├── config.py          # Settings (pydantic-settings)
│   │   │   ├── database.py        # AsyncSession setup + init_db()
│   │   │   ├── auth.py            # JWT decode + get_current_user deps
│   │   │   ├── email.py           # Resend integration (async)
│   │   │   └── security.py        # ALLOWED_TOOLS whitelist + log_audit()
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── routers/               # One file per domain
│   │   │   ├── auth.py            # Login / register
│   │   │   ├── chat.py            # POST /api/chat
│   │   │   ├── admin.py           # Requires admin or agent role
│   │   │   ├── accounts.py        # Register requires admin; list requires admin or agent
│   │   │   ├── tickets.py
│   │   │   ├── faq.py
│   │   │   ├── troubleshooting.py
│   │   │   ├── environment.py
│   │   │   ├── actions.py
│   │   │   ├── history.py
│   │   │   └── password_reset.py  # Public endpoints (no auth required)
│   │   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                      # Main ATOS admin frontend
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── config.ts              # BACKEND_URL — always "https://api.beluxio.org"
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── portal/                        # DataCo demo portal (password reset demo)
│   ├── src/
│   │   ├── App.tsx                # Login + forgot password + ATOS widget
│   │   └── users.ts               # (removed — users registered directly in ATOS)
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── cloudflare-tunnel.md
```

---

## Environment Variables

Create `backend/.env` from `backend/.env.example`:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | Model to use (default: `gpt-4.1-mini`) |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://atos:atos@db:5432/atos` (Docker default) |
| `SECRET_KEY` | Yes | Random string for JWT signing — generate with `openssl rand -hex 32` |
| `ENVIRONMENT` | Yes | `development` (CORS open) or `production` (CORS restricted) |
| `ALLOWED_ORIGINS` | Prod only | Comma-separated origins, e.g. `https://atos.beluxio.org` |
| `RESEND_API_KEY` | No | Resend API key — if set, password reset emails are sent for real |
| `EMAIL_FROM` | No | Sender address (default: `ATOS Soporte <onboarding@resend.dev>`) |

> With `onboarding@resend.dev` as sender, Resend only delivers to the account owner's email.
> To send to any address, verify your own domain in Resend and set `EMAIL_FROM`.

---

## Dev Commands

### Start backend (Docker)
```powershell
docker-compose up -d
```
- API: http://localhost:8002
- Swagger docs: http://localhost:8002/docs
- Logs: `docker logs atos-api-1 -f`

### Restart after code change
```powershell
docker-compose up -d --force-recreate api
```

### Start frontend
```powershell
cd frontend
npm install
npm run dev
```
Frontend: http://localhost:5173

### Start demo portal
```powershell
cd portal
npm install
npm run dev
```
Portal: http://localhost:5174

### Stop everything
```powershell
docker-compose down
```

---

## Database Migrations (Alembic)

```powershell
# Generate migration after model changes
docker exec atos-api-1 alembic revision --autogenerate -m "description"

# Apply migrations
docker exec atos-api-1 alembic upgrade head

# Check current version
docker exec atos-api-1 alembic current
```

---

## Deploy

### Frontend → Cloudflare Pages
Cloudflare Pages pulls pre-built files from the `gh-pages` branch automatically on push.

```powershell
cd frontend
npm run deploy   # = npm run build && npx gh-pages -d dist
```

### Backend → public via Cloudflare Tunnel
The fixed production tunnel is `https://api.beluxio.org` — configured in Cloudflare Zero Trust.

```powershell
# Start tunnel (keep this window open)
cloudflared tunnel run atos-api

# Stop: Ctrl+C
```

> The tunnel connects Cloudflare's edge to your local Docker backend.
> Both `docker-compose up -d` AND `cloudflared tunnel run atos-api` must be running for the public API to work.

---

## Agent Architecture

The agent (`backend/app/agent/agent.py`) follows a tool-call loop:

1. Receive message + history
2. Select relevant tools via keyword routing (`_KEYWORD_TOOLS`) — avoids sending all 30+ tools every request
3. Call OpenAI API with selected tools (max 6 iterations)
4. Execute tools via `TOOL_REGISTRY`, log each call via `log_audit()`
5. Return final text response + updated history

**Adding a new tool:**
1. Create a function in the appropriate `backend/app/agent/tools/*.py` module
2. Register it with the tool registry decorator
3. Add its name to `_ALWAYS_INCLUDE` or the relevant `_KEYWORD_TOOLS` entry in `agent.py`
4. Import the module in `agent.py` (the `# noqa: F401` imports trigger registration)

**Tool security:** All tool names pass through `log_audit()`. The `ALLOWED_TOOLS` set in `security.py` is the whitelist — do not bypass it.

---

## Key Patterns

- **Routers**: one file per domain in `backend/app/routers/`. Always add new routers to `main.py`.
- **Frontend hooks**: data fetching lives in `src/hooks/`, components stay presentational.
- **CORS**: In `development` ENVIRONMENT, all origins are allowed (`"*"`). In `production`, only `ALLOWED_ORIGINS` + hardcoded list. Never change this logic without understanding the security implications.
- **JWT**: Passed via `Authorization: Bearer <token>` header. `allow_credentials=False` in CORS is intentional.
- **History trimming**: Agent keeps last 4 user turns (`_MAX_HISTORY_TURNS`) to cap token usage.
- **Swagger**: Available at `/docs`. Includes JWT Bearer auth — click Authorize and paste your token to test protected endpoints.
- **Postman**: Import collection from `/openapi.json`.

---

## Endpoint Security

| Endpoint | Auth required |
|---|---|
| `POST /api/auth/login` | No |
| `GET /api/auth/me` | Yes (any role) |
| `POST /api/accounts/register` | Yes — `admin` only |
| `GET /api/accounts` | Yes — `admin` or `agent` |
| `GET /api/admin/logs` | Yes — `admin` or `agent` |
| `POST /api/reset-password/*` | No (public) |
| `POST /api/chat` | No (optional auth — enriches context) |
| `POST /api/actions/report` | Yes — `admin` or `agent` |
| `POST /api/actions/execute` | Yes — `admin` only |

---

## What NOT to Do

- Do not add arbitrary shell command execution — the tool whitelist in `security.py` is intentional
- Do not switch the LLM provider without updating `agent.py`, `requirements.txt`, and `.env.example`
- Do not commit `backend/.env` (contains secrets)
- Do not force-push to `main` — it's deployed
- Do not hardcode `BACKEND_URL` anywhere except `frontend/src/config.ts`
- Do not change `portal/src/App.tsx` API URL to localhost before deploying — it must point to `https://api.beluxio.org`
