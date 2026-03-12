from fastapi import FastAPI
from pydantic import BaseModel
from scoring.predict import scoring_function

app = FastAPI()

class ScoringRequest(BaseModel):
    surface_reelle_bati: float
    nombre_pieces_principales: float
    code_departement: str
    type_local: str

@app.post("/scoring/")
async def get_scoring(request: ScoringRequest):
    # Call the scoring function with validated data from the request
    prediction = scoring_function(
        surface_reelle_bati=request.surface_reelle_bati,
        nombre_pieces_principales=request.nombre_pieces_principales,
        code_departement=request.code_departement,
        type_local=request.type_local
    )

    return {"score": prediction}