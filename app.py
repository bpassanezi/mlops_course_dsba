from fastapi import FastAPI
from pydantic import BaseModel
from scoring import scoring_function

app = FastAPI()

class ScoringRequest(BaseModel):
    # By using pydantic, it already does data validation for us
    address: str # required field
    surface: float  # required field
    num_rooms: float = None # optional field

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/scoring/")
async def get_scoring(request: ScoringRequest):
    surface = request.surface
    num_rooms = request.num_rooms if request.num_rooms is not None else 0
    return scoring_function(surface, num_rooms)