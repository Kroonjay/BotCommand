"""Router aggregation for the OSRS backend API."""

from .item import router as item_router
from .action import router as action_router
from .task import router as task_router
from .healthcheck import router as healthcheck_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(item_router)
router.include_router(action_router)
router.include_router(task_router)
router.include_router(healthcheck_router)
