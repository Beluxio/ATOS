# ATOS — Documentación Completa del Proyecto

> **Agente Técnico de Operaciones de Soporte**  
> Un agente de IA para helpdesk que ejecuta acciones reales, no solo responde texto.

---

## Tabla de contenidos

1. [¿Qué es ATOS?](#1-qué-es-atos)
2. [Stack tecnológico — por qué se eligió cada cosa](#2-stack-tecnológico)
3. [Arquitectura general](#3-arquitectura-general)
4. [Cómo funciona el agente (el corazón del proyecto)](#4-cómo-funciona-el-agente)
5. [Estructura de archivos — cada archivo explicado](#5-estructura-de-archivos)
6. [Flujos principales paso a paso](#6-flujos-principales)
7. [Base de datos — modelos y relaciones](#7-base-de-datos)
8. [Seguridad — JWT, roles y whitelist](#8-seguridad)
9. [Email y notificaciones](#9-email-y-notificaciones)
10. [Tareas automáticas en segundo plano](#10-tareas-automáticas)
11. [Notificaciones en tiempo real (SSE)](#11-notificaciones-en-tiempo-real)
12. [Deploy y exposición pública](#12-deploy)
13. [Para la entrevista — preguntas y respuestas](#13-para-la-entrevista)

---

## 1. ¿Qué es ATOS?

ATOS es un **agente de helpdesk con IA** construido para la empresa ficticia DataCo Analytics. No es un chatbot simple que responde texto: cuando un usuario le pide "resetea mi contraseña" o "crea un ticket", el agente **ejecuta esas acciones realmente** contra la base de datos.

**El problema que resuelve:** los equipos de soporte pierden tiempo en tareas repetitivas (resets de contraseña, desbloquear cuentas, crear tickets). ATOS automatiza esas tareas mediante lenguaje natural.

**Componentes del sistema:**
- **Backend API** (FastAPI + PostgreSQL): gestiona toda la lógica y los datos
- **Frontend admin** (React): panel para agentes y administradores en `atos.beluxio.org`
- **Portal DataCo** (React): lo que verían los empleados en `portal.beluxio.org`
- **Agente IA** (OpenAI gpt-4.1-mini): procesa el lenguaje natural y decide qué acciones ejecutar

---

## 2. Stack tecnológico

### Por qué cada tecnología

| Tecnología | Rol | Por qué se eligió |
|---|---|---|
| **FastAPI** | Framework web del backend | Async nativo, tipado con Pydantic, documentación Swagger automática, rendimiento comparable a Node.js |
| **OpenAI gpt-4.1-mini** | LLM del agente | Soporte nativo de tool calling estructurado, relación calidad/precio, confiabilidad |
| **SQLAlchemy async** | ORM de base de datos | Queries async sin bloquear el event loop, tipado con Python type hints |
| **PostgreSQL 16** | Base de datos | Soporte JSON nativo (JSONB para tags), robusto, ampliamente conocido |
| **Alembic** | Migraciones de BD | Integrado con SQLAlchemy, control de versiones del schema |
| **python-jose + bcrypt** | Auth | JWT estándar de la industria, bcrypt para hashing seguro de contraseñas |
| **Resend** | Envío de emails | API simple, dominio verificado propio (`send.beluxio.org`), logs de entrega |
| **APScheduler** | Tareas programadas | Scheduler async que corre dentro del mismo proceso FastAPI |
| **slowapi** | Rate limiting | Middleware compatible con FastAPI, limita por IP |
| **React 18 + TypeScript** | Frontend | Tipado estático previene errores, ecosistema maduro |
| **Vite** | Bundler frontend | Build en segundos, HMR instantáneo en desarrollo |
| **Recharts** | Gráficas | Librería React nativa, composable, sin canvas |
| **Docker + docker-compose** | Contenedores | Reproducibilidad: mismo entorno en cualquier máquina |
| **Cloudflare Pages** | Hosting frontend | CDN global, SSL automático, deploy desde CLI |
| **Cloudflare Tunnel** | Exposición pública del API | Sin abrir puertos en el router, cifrado extremo a extremo |

---

## 3. Arquitectura general

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTERNET / USUARIOS                         │
└──────────────┬──────────────────────────────┬───────────────────┘
               │                              │
       atos.beluxio.org              portal.beluxio.org
   (Cloudflare Pages CDN)         (Cloudflare Pages CDN)
               │                              │
       frontend/dist/                   portal/dist/
       (React build)                   (React build)
               │                              │
               └──────────────┬───────────────┘
                              │ HTTPS
                    api.beluxio.org
                  (Cloudflare Tunnel)
                              │
                    ┌─────────▼──────────┐
                    │  TU PC / SERVIDOR  │
                    │  Docker            │
                    │  ┌──────────────┐  │
                    │  │  FastAPI     │  │  :8002
                    │  │  (atos-api)  │  │
                    │  └──────┬───────┘  │
                    │         │          │
                    │  ┌──────▼───────┐  │
                    │  │  PostgreSQL  │  │  :5432
                    │  │  (atos-db)   │  │
                    │  └──────────────┘  │
                    └────────────────────┘
```

**Flujo de una petición:**
1. Usuario en `atos.beluxio.org` hace clic en algo
2. React hace `fetch` a `https://api.beluxio.org/api/...`
3. Cloudflare Tunnel recibe la petición y la reenvía al Docker local en `:8002`
4. FastAPI procesa, consulta PostgreSQL, responde
5. La respuesta viaja de vuelta por el mismo túnel hasta el browser

---

## 4. Cómo funciona el agente

Este es el núcleo del proyecto. Entiéndelo bien.

### Tool Calling — la diferencia clave

Un chatbot normal genera texto. ATOS usa **tool calling** de OpenAI: el modelo puede "pausar" su respuesta y decir *"necesito ejecutar esta función con estos argumentos"*. FastAPI ejecuta la función real y le devuelve el resultado al modelo, que luego formula la respuesta final.

```
Usuario: "Resetea mi contraseña"
         │
         ▼
   OpenAI recibe el mensaje + las herramientas disponibles
         │
         ▼
   OpenAI decide: llamar request_password_reset(email="user@empresa.com")
         │
         ▼
   FastAPI ejecuta la función → genera token → envía email
         │
         ▼
   FastAPI devuelve resultado a OpenAI: {"token": "ABC123", "email_sent": true}
         │
         ▼
   OpenAI formula respuesta: "Te envié un email con el token ABC123"
```

### El loop de iteraciones (`agent.py`)

El agente puede encadenar múltiples tool calls en una sola conversación. Por eso hay un loop con máximo 6 iteraciones:

```python
for _ in range(6):                          # máximo 6 vueltas
    response = await openai.chat(...)
    
    if response tiene tool_calls:
        ejecutar cada tool
        agregar resultado al historial
        continuar el loop              # ← OpenAI puede pedir más tools
    else:
        response_text = respuesta final
        break                          # ← salir cuando OpenAI ya no pide tools
```

### Routing de herramientas — optimización de tokens

Hay más de 30 herramientas registradas. Enviarlas todas en cada petición costaría ~6.000 tokens extra. La solución: **routing por keywords**.

```python
_KEYWORD_TOOLS = [
    (["password", "contraseña", "reset"], ["request_password_reset", ...]),
    (["ticket", "incidencia"],            ["get_ticket", "create_ticket", ...]),
    ...
]
```

Si el mensaje contiene "contraseña", solo se envían las herramientas de contraseña + las 4 herramientas base. El modelo nunca sabe que existen las otras.

### Registro de herramientas — el decorador

Cada herramienta se registra con un decorador en `registry.py`:

```python
@register({
    "type": "function",
    "function": {
        "name": "create_ticket",
        "description": "Crea un ticket de soporte",
        "parameters": { ... }   # ← esto es lo que ve OpenAI
    }
})
async def create_ticket(args: dict) -> dict:
    # lógica real aquí
    ...
```

El decorador almacena la función en `TOOL_REGISTRY["create_ticket"]` y la declaración en `_TOOL_DECLARATIONS`. Cuando `agent.py` necesita ejecutar una tool, hace `TOOL_REGISTRY["create_ticket"](args)`.

---

## 5. Estructura de archivos

```
ATOS/
├── backend/
│   ├── app/
│   │   ├── agent/                    ← EL AGENTE IA
│   │   │   ├── agent.py              ← Loop principal, routing, ejecución de tools
│   │   │   ├── tools/
│   │   │   │   ├── registry.py       ← TOOL_REGISTRY + decorador @register
│   │   │   │   ├── base_tools.py     ← search_faq, identify_error, suggest_fix
│   │   │   │   ├── password_reset.py ← request/validate/confirm reset
│   │   │   │   ├── accounts.py       ← unlock, check_status, manage_session
│   │   │   │   ├── tickets.py        ← create, get, list, update, escalate tickets
│   │   │   │   ├── faq.py            ← get_faq_item, list_faq_categories
│   │   │   │   ├── troubleshooting.py ← flujos de diagnóstico paso a paso
│   │   │   │   ├── dependencies.py   ← detectar deps rotas, limpiar cache
│   │   │   │   ├── environment.py    ← check_tool_installed, validate_path
│   │   │   │   ├── automated_actions.py ← execute_allowed_action, generate_report
│   │   │   │   ├── memory.py         ← historial de incidencias y soluciones
│   │   │   │   └── database_access.py ← grant/revoke/check acceso a BDs
│   │   │   └── prompts/
│   │   │       └── system_prompt.py  ← Instrucciones base del agente + contexto de sesión
│   │   │
│   │   ├── core/                     ← INFRAESTRUCTURA TRANSVERSAL
│   │   │   ├── config.py             ← Variables de entorno via pydantic-settings
│   │   │   ├── database.py           ← Engine async, get_db(), init_db()
│   │   │   ├── auth.py               ← Crear/decodificar JWT, dependencias FastAPI
│   │   │   ├── security.py           ← ALLOWED_TOOLS, log_audit()
│   │   │   ├── email.py              ← Todas las funciones de email (Resend)
│   │   │   ├── limiter.py            ← Rate limiter (slowapi)
│   │   │   ├── scheduler.py          ← APScheduler: expirar accesos, avisos email
│   │   │   └── job_role_policy.py    ← Qué BDs puede acceder cada job role
│   │   │
│   │   ├── models/                   ← TABLAS DE LA BASE DE DATOS (SQLAlchemy ORM)
│   │   │   ├── account.py            ← users: email, hashed_password, role, job_role
│   │   │   ├── ticket.py             ← tickets + ticket_responses (con resolved_at)
│   │   │   ├── database_access.py    ← accesos BD: user, database, expires_at
│   │   │   ├── database_access_log.py ← historial de acciones en BD
│   │   │   ├── audit_log.py          ← cada tool call del agente queda registrado
│   │   │   ├── faq.py                ← preguntas/respuestas de la base de conocimiento
│   │   │   ├── troubleshooting.py    ← flujos de diagnóstico
│   │   │   ├── incident_history.py   ← soluciones anteriores que el agente recuerda
│   │   │   └── password_reset_token.py ← tokens temporales para reset
│   │   │
│   │   ├── schemas/                  ← VALIDACIÓN DE REQUESTS/RESPONSES (Pydantic)
│   │   │   └── chat.py               ← ChatRequest, ChatResponse
│   │   │
│   │   ├── services/                 ← LÓGICA DE NEGOCIO (sin HTTP, testeable)
│   │   │   ├── account_service.py    ← register, lock, unlock, update_password
│   │   │   ├── ticket_service.py     ← create, list, update_status, assign_ticket, SLA
│   │   │   ├── auth_service.py       ← hash_password, verify_password
│   │   │   ├── faq_service.py        ← CRUD de FAQ + seed inicial
│   │   │   ├── troubleshooting_service.py ← flujos + seed
│   │   │   ├── memory_service.py     ← incidencias históricas + seed
│   │   │   ├── database_access_service.py ← grant, revoke, expire_check
│   │   │   └── password_reset_service.py  ← generar/validar tokens
│   │   │
│   │   ├── routers/                  ← ENDPOINTS HTTP (un archivo por dominio)
│   │   │   ├── auth.py               ← POST /api/auth/login, GET /api/auth/me
│   │   │   ├── chat.py               ← POST /api/chat (el endpoint del agente)
│   │   │   ├── accounts.py           ← CRUD de cuentas (register requiere admin)
│   │   │   ├── tickets.py            ← CRUD de tickets + assign + escalate
│   │   │   ├── dashboard.py          ← GET /api/dashboard, GET /api/dashboard/trend
│   │   │   ├── database_access.py    ← grant, revoke, list accesos BD
│   │   │   ├── notifications.py      ← GET /api/notifications/stream (SSE)
│   │   │   ├── export.py             ← GET /api/export/* (CSV downloads)
│   │   │   ├── admin.py              ← GET /api/admin/logs
│   │   │   ├── faq.py                ← CRUD de FAQ
│   │   │   ├── troubleshooting.py    ← flujos de diagnóstico
│   │   │   ├── environment.py        ← herramientas del entorno
│   │   │   ├── actions.py            ← acciones automatizadas
│   │   │   ├── history.py            ← historial de incidencias
│   │   │   └── password_reset.py     ← endpoints públicos de reset
│   │   │
│   │   └── main.py                   ← Punto de entrada: registra routers, CORS, lifespan
│   │
│   ├── requirements.txt              ← Dependencias Python
│   ├── Dockerfile                    ← Imagen del API
│   └── .env.example                  ← Template de variables de entorno
│
├── frontend/                         ← PANEL ADMIN (React + TypeScript)
│   ├── src/
│   │   ├── App.tsx                   ← Raíz: routing de vistas, layout
│   │   ├── config.ts                 ← BACKEND_URL (único lugar donde está la URL del API)
│   │   ├── App.css                   ← Todos los estilos (tema oscuro)
│   │   ├── components/
│   │   │   ├── LoginView.tsx         ← Pantalla de login
│   │   │   ├── Sidebar.tsx           ← Navegación lateral (filtra por rol)
│   │   │   ├── NotificationBell.tsx  ← Campana de notificaciones en tiempo real
│   │   │   ├── ChatView.tsx          ← Interfaz del chat con el agente
│   │   │   ├── DashboardView.tsx     ← Métricas, SLA, gráficas de tendencia
│   │   │   ├── TicketsView.tsx       ← Lista, detalle, asignación, timeline de tickets
│   │   │   ├── UsersView.tsx         ← Gestión de cuentas
│   │   │   ├── DatabaseAccessView.tsx ← Gestión de accesos a BD
│   │   │   ├── LogsView.tsx          ← Audit logs del agente
│   │   │   ├── FAQView.tsx           ← Base de conocimiento
│   │   │   ├── TroubleshootingView.tsx ← Flujos de diagnóstico
│   │   │   ├── EnvironmentView.tsx   ← Validación de entorno
│   │   │   └── HistoryView.tsx       ← Historial de incidencias
│   │   └── hooks/
│   │       ├── useAuth.ts            ← Login, logout, token, user en localStorage
│   │       ├── useChat.ts            ← Enviar mensajes, historial del chat
│   │       ├── useTickets.ts         ← CRUD de tickets, asignar, responder
│   │       └── useNotifications.ts   ← Conexión SSE, cola de notificaciones
│   └── vite.config.ts
│
├── portal/                           ← PORTAL EMPLEADOS DataCo (React)
│   └── src/
│       └── App.tsx                   ← Login, forgot password, widget de ATOS chat,
│                                        "Mis accesos a BD"
│
├── docker-compose.yml                ← Define servicios: api + db
├── CLAUDE.md                         ← Instrucciones del proyecto para el AI
└── DOCUMENTACION.md                  ← Este archivo
```

---

## 6. Flujos principales

### Flujo: usuario pide reset de contraseña en el portal

```
1. Usuario escribe en el chat del portal: "Olvidé mi contraseña"

2. portal/App.tsx → fetch POST /api/chat
   { message: "Olvidé mi contraseña", session_id: "abc", history: [] }

3. chat.py router → agent.chat(message, history, db, session_id)

4. agent.py:
   - _select_tools("olvidé mi contraseña") → detecta "contraseña"
   - Incluye: request_password_reset, validate_reset_token, confirm_password_reset
   - OpenAI recibe el mensaje + esas tools

5. OpenAI decide llamar: request_password_reset(email="user@empresa.com")

6. agent.py ejecuta TOOL_REGISTRY["request_password_reset"](args)
   → password_reset_service.request_reset(db, email)
   → genera token aleatorio, lo guarda en BD con expiración de 15 min
   → llama email.send_password_reset_email() → Resend envía el email

7. Resultado vuelve a OpenAI: {"token": "XYZ789", "email_sent": true}

8. OpenAI formula: "Te envié un email. Tu token es XYZ789. 
   Úsalo junto con tu nueva contraseña."

9. Portal muestra el formulario de nueva contraseña

10. Usuario ingresa token + nueva contraseña
    → POST /api/reset-password/confirm
    → se valida el token, se hashea la contraseña con bcrypt, se guarda
```

### Flujo: agente asigna ticket y manda email

```
1. Admin en TicketsView abre ticket #5
2. Selecciona agente en el dropdown "Asignar a"
3. useTickets.assignTicket(5, "agente@empresa.com")
   → PATCH /api/tickets/5/assign { assigned_to: "agente@empresa.com" }

4. tickets.py router → require_role("admin", "agent") ✓
   → ticket_service.assign_ticket(db, 5, "agente@empresa.com", "admin@empresa.com")

5. ticket_service:
   - UPDATE tickets SET assigned_to=..., updated_at=...
   - INSERT ticket_response (nota en el timeline: "Asignado a: agente@...")
   - email.send_ticket_assigned_email("agente@empresa.com", 5, "título", "high", "admin@")

6. Resend envía email al agente con el título y prioridad del ticket

7. Si la API SSE está conectada, la próxima iteración del polling
   no detecta el ticket como "nuevo" (ya existía), pero el timeline se actualiza
```

### Flujo: SLA se calcula al resolver un ticket

```
1. Agente cambia estado → "resolved"
2. PATCH /api/tickets/5/status { new_status: "resolved" }
3. ticket_service.update_status():
   IF new_status in ("resolved", "closed") AND ticket.resolved_at IS NULL:
       resolved_at = datetime.now(UTC)    ← se guarda SOLO la primera vez
4. Frontend lee el ticket: resolved_at = "2024-01-15T14:30:00Z"
   slaInfo(ticket):
       hours = (resolved_at - created_at) / 3600 = 6.5h
       limit = SLA_HOURS["high"] = 8h
       ok = 6.5 <= 8 → true
5. En la tabla: ✅ 6.5h
6. En el detalle del ticket: "✅ Resuelto en 6.5h (SLA high: 8h — cumplido)"
```

---

## 7. Base de datos

### Relaciones principales

```
accounts (usuarios del sistema)
  id, email, username, hashed_password, role, job_role, status, failed_login_attempts

tickets (incidencias)
  id, title, description, status, priority, category, tags (JSONB)
  user_email, assigned_to, resolved_at, created_at, updated_at
  └── ticket_responses (timeline: comentarios y cambios de estado)
       id, ticket_id (FK), content, author, is_auto, created_at

database_accesses (accesos a BDs)
  id, user_email, database_name, db_username, db_password (generada)
  status, granted_by, expires_at, expiry_warning_sent, notes

database_access_logs (historial de acciones en accesos BD)
  id, user_email, database_name, action, performed_by, details

audit_logs (todo lo que hace el agente)
  id, tool_name, params_json, result_json, session_id, created_at

faq (base de conocimiento)
  id, question, answer, category, tags

troubleshooting_flows (guías paso a paso)
  id, name, category, steps (JSONB: lista de pasos con condiciones)

incident_history (memoria del agente)
  id, title, description, category, resolution, outcome, effectiveness

password_reset_tokens
  id, email, token (hash), expires_at, used
```

### `init_db()` — por qué no se usan migraciones en producción aquí

`database.py` usa `Base.metadata.create_all` al arrancar: crea tablas que no existen. Para columnas añadidas después del deploy inicial, se usan `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` — esto es idempotente (si ya existe la columna, no falla). No se usa Alembic en producción para simplificar el deploy, aunque el CLI de Alembic sí está disponible.

---

## 8. Seguridad

### JWT — cómo funciona

```
Login: POST /api/auth/login
  → auth_service.verify_password(plain, hashed) ← bcrypt
  → create_access_token(email, role)
  → retorna { access_token: "eyJ..." }

Petición protegida:
  Header: Authorization: Bearer eyJ...
  → oauth2_scheme extrae el token
  → decode_token(token) ← python-jose valida firma + expiración (8 horas)
  → retorna { sub: "email", role: "admin", exp: ... }
```

### Roles y permisos

| Rol | Puede hacer |
|---|---|
| `user` | Chat, ver sus propios tickets, cambiar su contraseña |
| `agent` | Todo lo de user + ver todos los tickets, asignar tickets, ver audit logs |
| `admin` | Todo lo de agent + crear/bloquear cuentas, ejecutar acciones, ver dashboard |

El sistema de roles actúa en dos niveles:
1. **Routers FastAPI**: `Depends(require_role("admin"))` rechaza antes de llegar al servicio
2. **System prompt del agente**: le dice al LLM qué puede hacer según el rol del usuario autenticado

### Rate limiting

```python
@limiter.limit("10/minute")   # /api/auth/login — previene fuerza bruta
@limiter.limit("20/minute")   # /api/chat — controla costos de OpenAI
@limiter.limit("3/hour")      # /api/reset-password/request — previene spam de emails
```

### Whitelist de herramientas

`security.py` mantiene `ALLOWED_TOOLS`. Cada vez que se registra una herramienta con `@register(...)`, se añade a esa lista. `log_audit()` registra cada llamada. El agente nunca puede ejecutar código arbitrario — solo funciones explícitamente registradas.

---

## 9. Email y notificaciones

Todos los emails van por **Resend** con dominio verificado `send.beluxio.org`. Si `RESEND_API_KEY` no está en el `.env`, los emails simplemente no se envían (no falla la operación).

### Emails que ATOS envía

| Evento | Función | Asunto |
|---|---|---|
| Reset de contraseña solicitado | `send_password_reset_email` | "Token de reset de contraseña — ATOS" |
| Acceso a BD otorgado | `send_db_access_email` | "Credenciales de acceso — {database}" |
| Acceso BD por vencer (7 días) | `send_expiry_warning_email` | "⚠️ Tu acceso a {database} expira en X días" |
| Acceso BD expirado | `send_expiry_email` | "Acceso expirado — {database}" |
| Comentario en ticket | `send_ticket_comment_email` | "Re: Ticket #{id} — {título}" |
| Ticket asignado al agente | `send_ticket_assigned_email` | "[ATOS] Ticket #{id} asignado" |
| Cuenta creada (onboarding) | `send_welcome_email` | "Bienvenido/a a ATOS — DataCo Analytics" |

---

## 10. Tareas automáticas

`scheduler.py` usa **APScheduler** con dos jobs que arrancan junto con FastAPI:

### Job 1: `expire_check` — cada hora
- Busca accesos BD con `status="active"` y `expires_at <= ahora`
- Los marca como `status="expired"`
- Envía email de notificación al usuario
- Registra en `database_access_logs`

### Job 2: `expiry_warnings` — cada 24 horas
- Busca accesos activos que vencen en ≤ 7 días y `expiry_warning_sent=False`
- Envía email de aviso una sola vez (el flag evita emails repetidos)
- Marca `expiry_warning_sent=True`

---

## 11. Notificaciones en tiempo real

ATOS usa **SSE (Server-Sent Events)** en lugar de WebSockets porque las notificaciones van en una sola dirección (servidor → cliente), lo cual hace SSE más simple y suficiente.

### Por qué SSE y no WebSockets

| SSE | WebSockets |
|---|---|
| Solo servidor → cliente | Bidireccional |
| HTTP nativo, funciona con proxies | Requiere upgrade de protocolo |
| Auto-reconexión del browser | Hay que implementarla |
| Suficiente para notificaciones | Necesario para chat en tiempo real |

### Cómo funciona

```
Browser: GET /api/notifications/stream?token=eyJ...
         (EventSource — conexión persistente)

Servidor: cada 15 segundos consulta la BD:
  - ¿Tickets nuevos desde la última vez? → evento "new_ticket"
  - ¿Accesos BD por vencer con aviso reciente? → evento "expiring_access"
  - ¿Accesos recién revocados/expirados? → evento "access_revoked"

Formato SSE:
  event: new_ticket
  data: {"id": 42, "title": "Error de login", "priority": "high"}

Browser: EventSource.addEventListener("new_ticket", handler)
  → useNotifications.ts acumula hasta 50 notificaciones
  → NotificationBell.tsx muestra el badge y el dropdown
```

### Por qué el token va en la URL (query param)

El browser no permite agregar headers personalizados en `EventSource`. La solución es pasar el JWT como `?token=...`. El servidor lo valida igual con `decode_token(token)`.

---

## 12. Deploy

### Backend (Docker)

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    volumes: [atos_data:/var/lib/postgresql/data]  # datos persistentes

  api:
    build: ./backend
    depends_on: [db]
    ports: ["8002:8000"]
    env_file: ./backend/.env
```

El `Dockerfile` instala dependencias y corre `uvicorn` con hot-reload en desarrollo.

### Frontend → Cloudflare Pages

```bash
cd frontend
npm run build                                              # TypeScript + Vite → dist/
npx wrangler pages deploy dist --project-name atos        # sube a Cloudflare Pages
```

El resultado es un sitio estático en CDN global. Solo hay que redesplegar cuando cambia el código del frontend.

### API pública → Cloudflare Tunnel

```bash
cloudflared tunnel run atos-api
```

Cloudflare Tunnel crea una conexión saliente desde tu máquina a los servidores de Cloudflare. No abre ningún puerto en el router. El tráfico que llega a `api.beluxio.org` Cloudflare lo reenvía a `localhost:8002` por ese túnel.

**Para que el sistema esté online necesitas tener corriendo:**
1. `docker-compose up -d` (backend + BD)
2. `cloudflared tunnel run atos-api` (el túnel)

---

## 13. Para la entrevista

### "¿Qué es ATOS?"

> ATOS es un agente de helpdesk con IA que ejecuta acciones reales usando tool calling de OpenAI. Cuando un usuario pide resetear su contraseña, el agente no solo responde texto — ejecuta la acción contra la base de datos, genera un token, envía el email, y confirma el resultado. Está construido con FastAPI en el backend, React en el frontend, PostgreSQL como base de datos, y está desplegado públicamente usando Cloudflare Tunnel y Cloudflare Pages.

### "¿Por qué FastAPI y no Django o Flask?"

> FastAPI tiene soporte async nativo, lo cual es importante porque el agente hace múltiples llamadas a OpenAI y a la base de datos que pueden correr en paralelo. También genera documentación Swagger automáticamente a partir de los tipos de Python, lo que acelera el desarrollo. Django es más completo pero tiene más overhead. Flask no tiene async nativo.

### "¿Cómo funciona el tool calling?"

> OpenAI recibe el mensaje del usuario junto con las declaraciones de las herramientas disponibles (nombre, descripción, parámetros). El modelo decide qué herramienta llamar y con qué argumentos. FastAPI ejecuta la función real, obtiene el resultado, y se lo devuelve al modelo para que formule la respuesta final. Esto puede repetirse hasta 6 veces en una sola conversación para encadenar múltiples acciones.

### "¿Cómo manejaste la autenticación?"

> JWT con `python-jose`. El token se genera al hacer login con la firma del `SECRET_KEY`, tiene una expiración de 8 horas, y contiene el email y el rol del usuario. Se pasa en el header `Authorization: Bearer`. Los endpoints protegidos usan `Depends(get_current_user)` de FastAPI que extrae y valida el token automáticamente. Las contraseñas se hashean con bcrypt.

### "¿Por qué SSE en lugar de WebSockets para notificaciones?"

> Las notificaciones van en una sola dirección: el servidor notifica al cliente. SSE es HTTP nativo, más simple de implementar, funciona con proxies y CDN sin configuración especial, y el browser reconecta automáticamente si se cae. WebSockets hubiera sido innecesariamente complejo para este caso de uso.

### "¿Cómo gestionas las tareas en segundo plano?"

> Con APScheduler integrado en el proceso de FastAPI. Hay dos jobs: uno horario que revoca accesos a bases de datos vencidos, y uno diario que envía emails de aviso 7 días antes de que expire un acceso. Se inician en el evento `startup` de FastAPI y se detienen en `shutdown`. El flag `expiry_warning_sent` en la base de datos garantiza que el email de aviso se envíe solo una vez por acceso.

### "¿Qué es el SLA en este contexto?"

> SLA (Service Level Agreement) es el tiempo máximo acordado para resolver un ticket según su prioridad: Critical 4h, High 8h, Medium 24h, Low 72h. Cuando un ticket se marca como resuelto, se guarda `resolved_at`. El sistema calcula si el tiempo entre `created_at` y `resolved_at` estuvo dentro del límite. Esto se muestra en el dashboard como porcentaje de cumplimiento por prioridad y en la tabla de tickets como un badge verde o rojo.

### "¿Cómo optimizaste el uso de tokens con OpenAI?"

> Implementé dos optimizaciones. Primero, routing de herramientas: analizo el mensaje del usuario por keywords y solo envío las herramientas relevantes al modelo — si el mensaje es sobre contraseñas, no envío las herramientas de tickets. Esto ahorra ~6.000 tokens por request. Segundo, trimming del historial: solo mantengo los últimos 4 turnos del usuario en el historial, y trunco los resultados de herramientas antiguos a 300 caracteres.

### "¿Cómo manejas la seguridad en el agente?"

> En tres niveles. Primero, una whitelist en `security.py`: el agente solo puede ejecutar funciones explícitamente registradas con el decorador `@register`. Segundo, el system prompt le dice al LLM qué puede hacer según el rol del usuario (user/agent/admin). Tercero, cada tool call queda registrado en `audit_logs` con los parámetros y el resultado. El agente no puede ejecutar comandos arbitrarios de shell.

### "¿Qué haría diferente si lo volviera a hacer?"

> Implementaría un sistema de migraciones con Alembic desde el principio en lugar de usar `ALTER TABLE IF NOT EXISTS` manual. También separaría el portal de empleados en un proyecto completamente independiente con su propio backend, y usaría Redis para el pub/sub de notificaciones en lugar de polling SSE — eso permitiría escalar a múltiples instancias del API.

---

*Documentación generada el 17/06/2026 — versión actual del proyecto.*
