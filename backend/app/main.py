import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import settings
from app.database import Base, async_session_factory, engine
from app.seed import run_seed

logger = logging.getLogger(__name__)

# Global reference so other modules (e.g. the /channels/{id}/test endpoint)
# can interact with the running bot instance.
telegram_bot = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_bot

    # Startup: create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default templates and sample data
    try:
        await run_seed()
    except Exception:
        logger.warning("Seed data could not be applied (database may be unavailable).", exc_info=True)

    # ------------------------------------------------------------------
    # Start Telegram bot (if a token is configured)
    # ------------------------------------------------------------------
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            from app.api.ws import manager as ws_manager
            from app.integrations.telegram import TelegramBot

            telegram_bot = TelegramBot(
                bot_token=settings.TELEGRAM_BOT_TOKEN,
                ws_manager=ws_manager,
                db_session_factory=async_session_factory,
            )
            await telegram_bot.start()
            # Store on the app instance so it's accessible from request state.
            app.state.telegram_bot = telegram_bot
            logger.info("Telegram bot started successfully (mode=%s).", settings.TELEGRAM_MODE)
        except Exception:
            logger.exception("Failed to start Telegram bot -- continuing without it.")
            telegram_bot = None
    else:
        logger.info("TELEGRAM_BOT_TOKEN not set -- Telegram integration disabled.")

    yield

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    if telegram_bot is not None:
        try:
            await telegram_bot.stop()
        except Exception:
            logger.exception("Error stopping Telegram bot.")

    await engine.dispose()


app = FastAPI(
    title="AI Agent Orchestration Platform",
    description="Backend API for managing AI agents, workflows, and executions",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes under /api prefix
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
