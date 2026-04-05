import warnings
import pandas as pd
from fastapi import FastAPI
from api.routes import router

from contextlib import asynccontextmanager
from api import market_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize data load from Bucket on startup
    market_data.initialize()
    yield

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

app = FastAPI(
    title="ImmoPrice API", 
    description="API for scoring properties and compiling market insights.",
    lifespan=lifespan
)

app.include_router(router)