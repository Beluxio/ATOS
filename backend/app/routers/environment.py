from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.agent.tools.environment import (
    generate_environment_report,
    check_tool_installed,
    check_minimum_requirements,
    ALLOWED_TOOLS,
)

router = APIRouter(prefix="/api/environment", tags=["environment"])


@router.get("/report")
async def get_environment_report(current_user: dict = Depends(get_current_user)):
    return await generate_environment_report({})


@router.get("/tool/{tool_name}")
async def get_tool_status(tool_name: str, current_user: dict = Depends(get_current_user)):
    return await check_tool_installed({"tool_name": tool_name})


@router.post("/check-requirements")
async def post_check_requirements(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    requirements = body.get("requirements", list(ALLOWED_TOOLS))
    return await check_minimum_requirements({"requirements": requirements})
