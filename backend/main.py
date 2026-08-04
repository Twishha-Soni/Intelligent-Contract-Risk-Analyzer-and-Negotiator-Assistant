from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.database.db import init_db, init_feedback_table

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    init_feedback_table()

    yield

app = FastAPI(
    title='Contract Risk Analyzer',
    lifespan=lifespan
)

app.include_router(router)