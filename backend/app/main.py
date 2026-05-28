from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routers import chat, admin, password_reset, accounts, auth, tickets, faq, troubleshooting, environment, actions, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="ATOS — Agente Técnico de Operaciones de Soporte",
    version="0.1.0",
    lifespan=lifespan,
)

origins = ["*"] if settings.environment == "development" else settings.origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=settings.environment != "development",
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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ATOS API"}
