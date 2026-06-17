from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import init_db
from app.core.limiter import limiter
from app.core.scheduler import start_scheduler, stop_scheduler
from app.routers import chat, admin, password_reset, accounts, auth, tickets, faq, troubleshooting, environment, actions, history, database_access, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="ATOS — Agente Técnico de Operaciones de Soporte",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    schema.setdefault("components", {})["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    app.openapi_schema = schema
    return schema


app.openapi = _custom_openapi

# Always allow GitHub Pages + localhost; tunnel URL is open via wildcard in dev
ALWAYS_ALLOWED = [
    "https://atos.beluxio.org",
    "https://beluxio.org",
    "https://www.beluxio.org",
    "https://beluxio.github.io",
    "http://localhost:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5173",
]
if settings.environment == "development":
    origins = ["*"]
else:
    origins = list(set(ALWAYS_ALLOWED + settings.origins_list))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,   # JWT via Authorization header — credentials flag not needed
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(password_reset.router)
app.include_router(accounts.router)
app.include_router(tickets.router)
app.include_router(faq.router)
app.include_router(troubleshooting.router)
app.include_router(environment.router)
app.include_router(actions.router)
app.include_router(history.router)
app.include_router(database_access.router)
app.include_router(dashboard.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ATOS API"}
