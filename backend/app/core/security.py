from typing import Any
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from app.models.audit_log import AuditLog

ALLOWED_TOOLS: set[str] = set()


def register_tool(name: str) -> None:
    ALLOWED_TOOLS.add(name)


def is_tool_allowed(name: str) -> bool:
    return name in ALLOWED_TOOLS


async def log_audit(
    db: AsyncSession,
    tool_name: str,
    params: dict[str, Any],
    result: Any,
    session_id: str | None = None,
) -> None:
    await db.execute(
        insert(AuditLog).values(
            tool_name=tool_name,
            params_json=params,
            result_json={"result": str(result)},
            session_id=session_id,
            created_at=datetime.now(UTC),
        )
    )
    await db.commit()
