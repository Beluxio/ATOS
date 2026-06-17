# ATOS — Agente Técnico de Operaciones de Soporte

Agente de helpdesk con IA que ejecuta acciones reales (resets de contraseña, tickets, accesos a BD) mediante lenguaje natural.

- **Panel admin:** https://atos.beluxio.org
- **Portal empleados:** https://portal.beluxio.org
- **API:** https://api.beluxio.org/docs

---

## Stack

| Capa | Tecnología |
|---|---|
| IA | OpenAI `gpt-4.1-mini` con tool calling |
| Backend | Python 3.12 + FastAPI + SQLAlchemy async |
| Base de datos | PostgreSQL 16 |
| Auth | JWT (python-jose) + bcrypt |
| Email | Resend |
| Frontend | React 18 + TypeScript + Vite + Recharts |
| Hosting frontend | Cloudflare Pages |
| Exposición pública | Cloudflare Tunnel → `api.beluxio.org` |
| Contenedores | Docker + docker-compose |

---

## Requisitos previos

Instala las siguientes herramientas antes de continuar:

| Herramienta | Descarga |
|---|---|
| **Git** | https://git-scm.com/download/win |
| **Docker Desktop** | https://www.docker.com/products/docker-desktop/ |
| **cloudflared** | Ver instrucciones abajo |

**Instalar cloudflared** — PowerShell como administrador:
```powershell
winget install --id Cloudflare.cloudflared
```
Si `winget` no funciona: descarga `cloudflared-windows-amd64.exe` desde
https://github.com/cloudflare/cloudflared/releases/latest,
renómbralo a `cloudflared.exe` y muévelo a `C:\Windows\System32\`.

> Después de instalar Docker Desktop **reinicia el PC** antes de continuar.

---

## Instalación

### 1. Clonar el repositorio
```powershell
git clone https://github.com/Beluxio/ATOS.git
cd ATOS
```

### 2. Configurar el archivo `.env`
El administrador del proyecto te enviará el archivo `.env` por mensaje privado.
Colócalo dentro de la carpeta `backend\`:

```
ATOS\
└── backend\
    └── .env   ← aquí
```

Si necesitas crear uno propio, copia el ejemplo y rellena los valores:
```powershell
copy backend\.env.example backend\.env
notepad backend\.env
```

### 3. Configurar el túnel de Cloudflare
El administrador te enviará 3 archivos:
- `config.yml`
- `cert.pem`
- `956c7924-0310-44a6-b0c9-d322aeb14037.json`

Crea la carpeta del túnel:
```powershell
mkdir "$env:USERPROFILE\.cloudflared"
```

Copia los 3 archivos dentro de `C:\Users\TU_USUARIO\.cloudflared\`

Abre `config.yml` con el Bloc de notas y reemplaza `TU_USUARIO` con tu nombre de usuario de Windows:
```yaml
tunnel: 956c7924-0310-44a6-b0c9-d322aeb14037
credentials-file: C:\Users\TU_USUARIO\.cloudflared\956c7924-0310-44a6-b0c9-d322aeb14037.json

ingress:
  - hostname: api.beluxio.org
    service: http://localhost:8002
  - service: http_status:404
```

> Para conocer tu nombre de usuario exacto: `echo $env:USERNAME`

---

## Levantar el sistema

Necesitas **dos terminales** abiertas al mismo tiempo.

**Terminal 1 — Backend:**
```powershell
docker-compose up -d
```

Verifica que funciona (~30 segundos después):
```powershell
curl http://localhost:8002/health
# Respuesta esperada: {"status":"ok","service":"ATOS API"}
```

**Terminal 2 — Túnel (mantener abierta):**
```powershell
cloudflared tunnel run atos-api
```

Cuando veas `Connection established`, el sistema está online en https://api.beluxio.org.

---

## Uso diario

### Encender
```powershell
# Terminal 1
docker-compose up -d

# Terminal 2 (dejar abierta)
cloudflared tunnel run atos-api
```

### Apagar
```powershell
# Ctrl+C en la Terminal 2

# Terminal 1
docker-compose down
```

### Ver logs (para depurar)
```powershell
docker logs atos-api-1 -f
```

---

## Variables de entorno

Ver `backend\.env.example` para la lista completa con descripciones.

| Variable | Requerida | Descripción |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | API key de OpenAI |
| `OPENAI_MODEL` | No | Modelo (default: `gpt-4.1-mini`) |
| `DATABASE_URL` | ✅ | No cambiar si usas docker-compose |
| `SECRET_KEY` | ✅ | Clave para firmar JWT |
| `ENVIRONMENT` | ✅ | `development` o `production` |
| `RESEND_API_KEY` | No | Sin esto los emails no se envían |
| `EMAIL_FROM` | No | Dirección remitente de emails |

---

## Documentación técnica

Para entender la arquitectura, cada archivo, los flujos principales y prepararte para una entrevista técnica sobre el proyecto, lee [DOCUMENTACION.md](DOCUMENTACION.md).
