from fastapi import APIRouter

from ..services.process import run


process_router = APIRouter()


@process_router.post("/process")
async def process() -> bool:
    """
    TODO: 처리합니다.

    """
    return run()
