"""Healthcheck endpoint for DreamBot scripts."""

from fastapi import APIRouter, Request, HTTPException
from http import HTTPStatus
from logging import getLogger
import gzip
import json

from osrs_backend.models.healthcheck import HealthCheckPayload

router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])

logger = getLogger(__name__)


@router.post("/")
async def receive_healthcheck(request: Request):
    """
    Receive a healthcheck from a DreamBot script.
    Handles gzip-encoded request bodies and converts automatically into a Pydantic model.
    """
    body = await request.body()

    content_encoding = request.headers.get("content-encoding", "").lower()
    if content_encoding == "gzip":
        body = gzip.decompress(body)

    try:
        payload_dict = json.loads(body)
        payload = HealthCheckPayload(**payload_dict)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse healthcheck payload: {e}")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=f"Invalid payload format: {e}"
        )

    logger.info(
        f"[HEALTHCHECK] Instance {payload.instance_id}: task={payload.task}, hp={payload.hp}"
    )
    logger.debug(f"[LOCATION] x={payload.x} y={payload.y} plane={payload.plane}")

    for skill, xp in payload.xp_gained.items():
        logger.debug(f"[XP] {skill} +{xp}")

    return {"status": "ok"}
