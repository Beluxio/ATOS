import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def _run_expire_check():
    """Revoca accesos vencidos y notifica. Corre cada hora."""
    from app.services.database_access_service import expire_check
    try:
        async with AsyncSessionLocal() as db:
            result = await expire_check(db)
            if result["expired_count"] > 0:
                logger.info("Scheduler: %d acceso(s) expirado(s) y revocados.", result["expired_count"])
    except Exception as e:
        logger.error("Scheduler expire_check error: %s", e)


async def _run_expiry_warnings():
    """Envía aviso 7 días antes de expiración (una sola vez por acceso). Corre diariamente."""
    from app.models.database_access import DatabaseAccess
    from app.core.email import send_expiry_warning_email
    try:
        now = datetime.now(timezone.utc)
        warning_threshold = now + timedelta(days=7)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(DatabaseAccess).where(
                    DatabaseAccess.status == "active",
                    DatabaseAccess.expires_at.isnot(None),
                    DatabaseAccess.expires_at <= warning_threshold,
                    DatabaseAccess.expires_at > now,
                    DatabaseAccess.expiry_warning_sent == False,  # noqa: E712
                )
            )
            accesses = result.scalars().all()

            for access in accesses:
                exp = access.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                days_left = max(0, (exp - now).days)
                sent = await send_expiry_warning_email(
                    access.user_email, access.database_name, days_left
                )
                if sent:
                    await db.execute(
                        update(DatabaseAccess)
                        .where(DatabaseAccess.id == access.id)
                        .values(expiry_warning_sent=True)
                    )
                    logger.info(
                        "Aviso de expiración enviado a %s para %s (%d días).",
                        access.user_email, access.database_name, days_left,
                    )

            if accesses:
                await db.commit()

    except Exception as e:
        logger.error("Scheduler expiry_warnings error: %s", e)


def start_scheduler():
    scheduler.add_job(_run_expire_check,    "interval", hours=1,  id="expire_check",    replace_existing=True)
    scheduler.add_job(_run_expiry_warnings, "interval", hours=24, id="expiry_warnings", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler iniciado — expire_check cada 1h, expiry_warnings cada 24h.")


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler detenido.")
