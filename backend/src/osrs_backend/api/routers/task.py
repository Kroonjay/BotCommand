"""Task assignment endpoint for DreamBot scripts."""

from fastapi import APIRouter, Depends
from prisma import Prisma
from logging import getLogger

from osrs_backend.db.database import get_db

logger = getLogger(__name__)

router = APIRouter(prefix="/task", tags=["tasks"])


@router.get("/")
async def get_tasks(db: Prisma = Depends(get_db), limit: int = 100):
    """Get current task assignment."""
    # TODO: Implement actual task assignment logic
    content = {
        "task": "TAN_LEATHER",
        "params": {"rawHideName": "Green dragonhide"},
    }

    return content
