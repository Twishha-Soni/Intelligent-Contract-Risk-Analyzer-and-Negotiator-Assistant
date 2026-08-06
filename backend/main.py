from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.database.db import init_db, init_feedback_table
from app.database.vector_store import get_client, ensure_collection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    ensure_collection(get_client())

    yield

app = FastAPI(
    title='Contract Risk Analyzer',
    lifespan=lifespan
)

app.include_router(router)