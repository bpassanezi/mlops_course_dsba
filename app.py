from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()

class ScoringRequest(BaseModel):
    # By using pydantic, it already does data validation for us
    address: str # required field
    surface: float  # required field
    num_rooms: float = None # optional field

# Define very simple room for scoring
def scoring_function(surface: float, num_rooms: float = 0) -> int:
    current_value = 10
    if surface > 50:
        current_value += 100
    if num_rooms >= 2:
        current_value = current_value*2

    return current_value

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/scoring/")
async def get_scoring(request: ScoringRequest):
    surface = request.surface
    num_rooms = request.num_rooms if request.num_rooms is not None else 0
    return scoring_function(surface, num_rooms)