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
| **Git** | https://git-scm.com/download/win |22222

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

---

## Levantar el sistema

Un solo comando levanta el backend, la base de datos y el túnel de Cloudflare:

```powershell
docker-compose up -d
```

Verifica que funciona (~30 segundos después):
```powershell
curl http://localhost:8250/health
# Respuesta esperada: {"status":"ok","service":"ATOS API"}
```

El túnel conecta automáticamente y `api.beluxio.org` queda online.

---

## Uso diario

### Encender
```powershell
docker-compose up -d
```

### Apagar
```powershell
docker-compose down
```

### Ver logs (para depurar)
```powershell
# API
docker logs atos-api-1 -f

# Túnel
docker logs atos-tunnel-1 -f
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
