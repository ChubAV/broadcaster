import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_current_user_id, get_db, get_settings
from app.services.billing_service import get_balance_info, get_transaction_history
from app.services.payment_service import create_payment, handle_webhook

logger = structlog.get_logger()

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/balance")
async def get_balance(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    info = await get_balance_info(db, user_id)
    return info


@router.get("/packages")
async def list_packages(settings: Settings = Depends(get_settings)):
    return {"packages": settings.parsed_message_packages}


@router.get("/transactions")
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    txs = await get_transaction_history(db, user_id, limit=limit, offset=offset)
    return {"transactions": txs}


class PurchaseRequest(BaseModel):
    package_index: int


@router.post("/purchase")
async def purchase_package(
    data: PurchaseRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    packages = settings.parsed_message_packages
    if data.package_index < 0 or data.package_index >= len(packages):
        raise HTTPException(status_code=400, detail="Invalid package index")

    pkg = packages[data.package_index]
    result = await create_payment(
        db,
        user_id=user_id,
        package_name=pkg["name"],
        messages_count=pkg["count"],
        price=pkg["price"],
    )
    return result


@router.post("/webhook")
async def yookassa_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
        event = body.get("event", "")
        payment_data = body

        logger.info("yookassa_webhook_received", event=event)

        processed = await handle_webhook(db, event, payment_data)
        return {"ok": processed}
    except Exception as e:
        logger.error("webhook_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")
