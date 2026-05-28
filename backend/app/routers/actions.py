from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, require_role
from app.agent.tools.automated_actions import (
    generate_report,
    execute_allowed_action,
    ALLOWED_ACTIONS,
    ALLOWED_REPORT_TYPES,
)

router = APIRouter(prefix="/api/actions", tags=["actions"])


@router.get("/available")
async def list_available_actions(current_user: dict = Depends(get_current_user)):
    return {
        "actions": sorted(ALLOWED_ACTIONS),
        "report_types": sorted(ALLOWED_REPORT_TYPES),
    }


@router.post("/report")
async def post_generate_report(
    body: dict,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    report_type = body.get("report_type", "tickets")
    filters = body.get("filters", {})
    return await generate_report({"report_type": report_type, "filters": filters})


@router.post("/execute")
async def post_execute_action(
    body: dict,
    current_user: dict = Depends(require_role("admin")),
):
    return await execute_allowed_action({
        "action_name": body.get("action_name", ""),
        "params": body.get("params", {}),
        "confirmed": body.get("confirmed", False),
    })
