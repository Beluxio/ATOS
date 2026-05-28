from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from app.models.incident_history import IncidentHistory, SolutionEffectiveness

_SEED_INCIDENTS = [
    {
        "description": "npm install falla con ERESOLVE conflicto de peer dependencies en proyecto React 18",
        "solution_used": "npm install --legacy-peer-deps",
        "outcome": "resolved",
        "category": "nodejs",
        "tags": ["npm", "peer-deps", "react"],
    },
    {
        "description": "ModuleNotFoundError: No module named 'psycopg2' al arrancar aplicación FastAPI",
        "solution_used": "pip install psycopg2-binary",
        "outcome": "resolved",
        "category": "python",
        "tags": ["pip", "psycopg2", "fastapi"],
    },
    {
        "description": "Permission denied al ejecutar scripts npm en carpeta del proyecto",
        "solution_used": "sudo chown -R $USER:$(id -gn) . && npm install",
        "outcome": "resolved",
        "category": "permissions",
        "tags": ["npm", "permissions", "chown"],
    },
    {
        "description": "docker: Cannot connect to the Docker daemon. Is the docker daemon running?",
        "solution_used": "sudo systemctl start docker && sudo usermod -aG docker $USER",
        "outcome": "resolved",
        "category": "docker",
        "tags": ["docker", "daemon", "systemctl"],
    },
    {
        "description": "esbuild native binary mismatch después de cambiar versión de Node",
        "solution_used": "npm rebuild esbuild",
        "outcome": "resolved",
        "category": "nodejs",
        "tags": ["esbuild", "npm", "native-binary"],
    },
    {
        "description": "git push rechazado: remote contains work you do not have locally",
        "solution_used": "git pull --rebase origin main && git push",
        "outcome": "resolved",
        "category": "git",
        "tags": ["git", "push", "rebase"],
    },
    {
        "description": "ENOSPC: no space left on device al hacer npm install",
        "solution_used": "docker system prune -f && npm cache clean --force && npm install",
        "outcome": "resolved",
        "category": "environment",
        "tags": ["disk-space", "npm", "docker"],
    },
    {
        "description": "Cannot find module 'express' al ejecutar servidor Node",
        "solution_used": "npm install",
        "outcome": "resolved",
        "category": "nodejs",
        "tags": ["npm", "module-not-found", "express"],
    },
    {
        "description": "Python virtual environment activado pero pip instala en sistema global",
        "solution_used": "deactivate && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt",
        "outcome": "resolved",
        "category": "python",
        "tags": ["venv", "pip", "python"],
    },
    {
        "description": "ETIMEDOUT al hacer npm install desde red corporativa con proxy",
        "solution_used": "npm config set proxy http://proxy:3128 && npm install --prefer-offline",
        "outcome": "resolved",
        "category": "network",
        "tags": ["npm", "proxy", "network"],
    },
    {
        "description": "node-gyp FAIL: Python no encontrado para compilar módulos nativos",
        "solution_used": "npm install --ignore-scripts",
        "outcome": "resolved",
        "category": "nodejs",
        "tags": ["node-gyp", "python", "native"],
    },
    {
        "description": "Conflicto react@17 y react-dom@18 impide arrancar aplicación",
        "solution_used": "npm install react@18 react-dom@18",
        "outcome": "resolved",
        "category": "nodejs",
        "tags": ["react", "version-conflict", "npm"],
    },
    {
        "description": "ImportError: cannot import name 'BaseSettings' from 'pydantic'",
        "solution_used": "pip install pydantic-settings",
        "outcome": "resolved",
        "category": "python",
        "tags": ["pydantic", "pydantic-settings", "fastapi"],
    },
    {
        "description": "docker-compose up falla con bind: address already in use en puerto 5432",
        "solution_used": "sudo lsof -i :5432 | grep LISTEN | awk '{print $2}' | xargs sudo kill -9",
        "outcome": "resolved",
        "category": "docker",
        "tags": ["docker", "port-conflict", "postgres"],
    },
    {
        "description": "yarn install falla con error de integridad en lockfile corrupto",
        "solution_used": "rm yarn.lock && yarn cache clean && yarn install",
        "outcome": "resolved",
        "category": "nodejs",
        "tags": ["yarn", "lockfile", "cache"],
    },
]

_SEED_SOLUTIONS = [
    {"solution_name": "npm install --legacy-peer-deps", "success_count": 34, "failure_count": 3, "category": "nodejs"},
    {"solution_name": "pip install -r requirements.txt", "success_count": 28, "failure_count": 2, "category": "python"},
    {"solution_name": "npm install", "success_count": 25, "failure_count": 1, "category": "nodejs"},
    {"solution_name": "docker system prune -f", "success_count": 18, "failure_count": 0, "category": "docker"},
    {"solution_name": "npm rebuild esbuild", "success_count": 15, "failure_count": 1, "category": "nodejs"},
    {"solution_name": "git pull --rebase origin main", "success_count": 12, "failure_count": 2, "category": "git"},
    {"solution_name": "npm install --ignore-scripts", "success_count": 10, "failure_count": 4, "category": "nodejs"},
    {"solution_name": "pip install pydantic-settings", "success_count": 9, "failure_count": 0, "category": "python"},
]


async def seed(db: AsyncSession) -> None:
    count_inc = await db.scalar(select(func.count()).select_from(IncidentHistory))
    if count_inc == 0:
        for inc in _SEED_INCIDENTS:
            db.add(IncidentHistory(**inc))

    count_sol = await db.scalar(select(func.count()).select_from(SolutionEffectiveness))
    if count_sol == 0:
        for sol in _SEED_SOLUTIONS:
            db.add(SolutionEffectiveness(**sol))

    await db.commit()


async def search_incidents(db: AsyncSession, query: str, limit: int = 5) -> list[dict]:
    terms = query.lower().split()
    rows = await db.execute(
        select(IncidentHistory).order_by(desc(IncidentHistory.created_at)).limit(100)
    )
    all_incidents = rows.scalars().all()

    scored = []
    for inc in all_incidents:
        text_blob = (inc.description + " " + inc.solution_used + " " + (inc.category or "")).lower()
        score = sum(1 for t in terms if t in text_blob)
        if score > 0:
            scored.append((score, inc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "id": inc.id,
            "description": inc.description,
            "solution_used": inc.solution_used,
            "outcome": inc.outcome,
            "category": inc.category,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "relevance_score": score,
        }
        for score, inc in scored[:limit]
    ]


async def get_stats(db: AsyncSession) -> dict:
    total = await db.scalar(select(func.count()).select_from(IncidentHistory))
    resolved = await db.scalar(
        select(func.count()).select_from(IncidentHistory).where(IncidentHistory.outcome == "resolved")
    )
    escalated = await db.scalar(
        select(func.count()).select_from(IncidentHistory).where(IncidentHistory.outcome == "escalated")
    )

    # Category distribution
    cat_rows = await db.execute(
        select(IncidentHistory.category, func.count().label("cnt"))
        .group_by(IncidentHistory.category)
        .order_by(desc("cnt"))
        .limit(5)
    )
    categories = [{"category": r.category, "count": r.cnt} for r in cat_rows]

    # Top solutions
    sol_rows = await db.execute(
        select(SolutionEffectiveness)
        .order_by(desc(SolutionEffectiveness.success_count))
        .limit(5)
    )
    solutions = [
        {
            "solution": s.solution_name,
            "success": s.success_count,
            "failure": s.failure_count,
            "effectiveness_pct": round(
                s.success_count / (s.success_count + s.failure_count) * 100
                if (s.success_count + s.failure_count) > 0 else 0,
                1,
            ),
            "category": s.category,
        }
        for s in sol_rows.scalars().all()
    ]

    return {
        "total_incidents": total,
        "resolved": resolved,
        "escalated": escalated,
        "resolution_rate_pct": round(resolved / total * 100 if total else 0, 1),
        "category_distribution": categories,
        "top_solutions": solutions,
    }


async def save_incident(
    db: AsyncSession,
    description: str,
    solution_used: str,
    outcome: str,
    ticket_id: int | None = None,
    category: str | None = None,
    tags: list | None = None,
) -> dict:
    inc = IncidentHistory(
        description=description,
        solution_used=solution_used,
        outcome=outcome,
        ticket_id=ticket_id,
        category=category,
        tags=tags or [],
    )
    db.add(inc)

    # Update or create solution effectiveness
    existing = await db.scalar(
        select(SolutionEffectiveness).where(SolutionEffectiveness.solution_name == solution_used)
    )
    if existing:
        if outcome in ("resolved", "success"):
            existing.success_count += 1
        else:
            existing.failure_count += 1
    else:
        db.add(SolutionEffectiveness(
            solution_name=solution_used,
            success_count=1 if outcome in ("resolved", "success") else 0,
            failure_count=0 if outcome in ("resolved", "success") else 1,
            category=category,
        ))

    await db.commit()
    await db.refresh(inc)
    return {"id": inc.id, "description": inc.description, "outcome": inc.outcome}
