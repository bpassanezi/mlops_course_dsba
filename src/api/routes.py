import logging
from fastapi import APIRouter, HTTPException
from scoring import predict
from api.constants import AVAILABLE_DEPARTMENTS, DEPT_MAIN_CITY, DEPT_CENTER, DEPT_ZOOM
from api.schemas import (
    ScoringRequest,
    ScoringResponse,
    DepartmentResponse,
    CommuneResponse,
    CoordsResponse,
    ComparablesResponse,
    InvestmentResponse,
)
from api.scoring_service import get_dept_stats
from api.geography_service import (
    get_communes_for_dept,
    get_coords_for_commune,
    get_coords_for_zipcode,
)
from api.comparables_service import find_comparables
from api.investment_service import compute_investment_metrics

router = APIRouter()
logger = logging.getLogger(__name__)


def _validate_dept(dept: str) -> None:
    """Raise HTTP 400 if the department code is not supported."""
    if dept not in AVAILABLE_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown department '{dept}'. Available: {list(AVAILABLE_DEPARTMENTS.keys())}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/scoring/", response_model=ScoringResponse)
async def get_scoring(request: ScoringRequest):
    dept = request.code_departement.strip()
    _validate_dept(dept)

    try:
        prediction, breakdown = predict(
            surface_reelle_bati=request.surface_reelle_bati,
            nombre_pieces_principales=request.nombre_pieces_principales,
            code_departement=dept,
            type_local=request.type_local,
        )
    except FileNotFoundError as e:
        logger.error("Model artifacts missing: %s", e)
        raise HTTPException(status_code=503, detail="No trained model is available. Please train a model first.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Scoring failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scoring failed unexpectedly: {e}")

    return {"score": prediction, "breakdown": breakdown, "dept_stats": get_dept_stats(dept)}


@router.get("/departments/", response_model=DepartmentResponse)
async def get_departments():
    return {
        "departments": AVAILABLE_DEPARTMENTS,
        "main_cities":  DEPT_MAIN_CITY,
        "centers":      DEPT_CENTER,
        "zoom_levels":  DEPT_ZOOM,
    }


@router.get("/communes/{dept_code}", response_model=CommuneResponse)
async def get_communes(dept_code: str):
    return get_communes_for_dept(dept_code.strip())


@router.get("/commune_coords/{dept_code}/{commune_name}", response_model=CoordsResponse)
async def get_commune_coords(dept_code: str, commune_name: str):
    return {"coords": get_coords_for_commune(dept_code.strip(), commune_name)}


@router.get("/zipcode_coords/{dept_code}/{zipcode}", response_model=CoordsResponse)
async def get_zipcode_coords(dept_code: str, zipcode: str):
    return {"coords": get_coords_for_zipcode(dept_code.strip(), zipcode.strip())}


@router.get("/comparables/", response_model=ComparablesResponse)
async def get_comparables(
    code_departement: str,
    surface_reelle_bati: float,
    nombre_pieces_principales: float,
    type_local: str,
    n: int = 5,
):
    dept = code_departement.strip()
    _validate_dept(dept)

    comparables = find_comparables(
        dept=dept,
        surface=surface_reelle_bati,
        rooms=nombre_pieces_principales,
        type_local=type_local,
        n=n,
    )
    return {"comparables": comparables}


@router.get("/investment/", response_model=InvestmentResponse)
async def get_investment(
    code_departement: str,
    prediction: float,
    surface_reelle_bati: float,
):
    dept = code_departement.strip()
    _validate_dept(dept)

    if prediction <= 0:
        raise HTTPException(status_code=400, detail="prediction must be > 0")
    if surface_reelle_bati <= 0:
        raise HTTPException(status_code=400, detail="surface_reelle_bati must be > 0")

    try:
        metrics = compute_investment_metrics(dept=dept, prediction=prediction, surface=surface_reelle_bati)
    except KeyError as e:
        raise HTTPException(status_code=503, detail=f"Data unavailable for department {e}.")
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return metrics
