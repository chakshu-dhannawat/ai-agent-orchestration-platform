from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.channel import Channel
from app.schemas.channel import ChannelCreate, ChannelResponse

router = APIRouter()


class TestMessageRequest(BaseModel):
    chat_id: str | int = Field(..., description="Telegram chat ID to send the test message to")
    message: str = Field(
        default="Hello from the AI Agent Orchestration Platform! This is a test message.",
        description="Text to send",
    )


class TestMessageResponse(BaseModel):
    success: bool
    detail: str


@router.get("/", response_model=list[ChannelResponse])
async def list_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Channel).order_by(Channel.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/", response_model=ChannelResponse, status_code=201)
async def create_channel(data: ChannelCreate, db: AsyncSession = Depends(get_db)):
    channel = Channel(**data.model_dump())
    db.add(channel)
    await db.flush()
    await db.refresh(channel)
    return channel


@router.delete("/{channel_id}", status_code=204)
async def delete_channel(channel_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Channel).where(Channel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    await db.delete(channel)
    await db.flush()


@router.post(
    "/{channel_id}/test",
    response_model=TestMessageResponse,
    summary="Send a test message through a channel",
)
async def test_channel(
    channel_id: str,
    body: TestMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Send a test message to verify that the channel integration is working.

    For **Telegram** channels the request must include a ``chat_id`` (the
    numeric Telegram chat/user ID) and an optional ``message`` string.
    The platform will attempt to deliver the message via the running
    Telegram bot and report back whether it succeeded.
    """

    # Fetch the channel record.
    result = await db.execute(
        select(Channel).where(Channel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    if not channel.is_active:
        raise HTTPException(status_code=400, detail="Channel is not active")

    # --- Telegram ---------------------------------------------------------
    if channel.type == "telegram":
        # Try to get the running bot instance from app state.
        telegram_bot = getattr(request.app.state, "telegram_bot", None)

        if telegram_bot is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Telegram bot is not running. "
                    "Make sure TELEGRAM_BOT_TOKEN is set and the bot started successfully."
                ),
            )

        try:
            await telegram_bot.send_message(
                chat_id=body.chat_id,
                text=body.message,
            )
            return TestMessageResponse(
                success=True,
                detail=f"Test message sent to chat {body.chat_id}.",
            )
        except Exception as exc:
            return TestMessageResponse(
                success=False,
                detail=f"Failed to send message: {exc}",
            )

    # --- Other channel types (future) -------------------------------------
    raise HTTPException(
        status_code=400,
        detail=f"Test messages are not supported for channel type '{channel.type}' yet.",
    )
