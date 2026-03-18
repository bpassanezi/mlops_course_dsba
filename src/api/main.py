import warnings
import pandas as pd
from fastapi import FastAPI
from api.routes import router

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

app = FastAPI(
    title="ImmoPrice API", 
    description="API for scoring properties and compiling market insights."
)

app.include_router(router)