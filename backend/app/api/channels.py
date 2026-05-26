import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.channel import Channel
from app.schemas.channel import ChannelCreate, ChannelResponse

router = APIRouter()


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
async def delete_channel(channel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Channel).where(Channel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    await db.delete(channel)
    await db.flush()
