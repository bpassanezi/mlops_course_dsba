from fastapi import APIRouter, HTTPException
import logging
from typing import Optional
from scoring.predict import scoring_function
from api.constants import AVAILABLE_DEPARTMENTS, DEPT_MAIN_CITY, DEPT_CENTER, DEPT_ZOOM
from api.schemas import (
    ScoringRequest, 
    ScoringResponse, 
    DepartmentResponse, 
    CommuneResponse, 
    CoordsResponse, 
    ComparablesResponse, 
    InvestmentResponse
)
from api.services import (
    DEPT_STATS, 
    COMMUNE_DATA, 
    COMMUNE_COORDS, 
    CLEANED_DF, 
    MARKET_GROWTH
)

# Realistic gross rental yields for each department (annual % of property value)
RENTAL_YIELDS = {
    "13": 5.3,   # Marseille
    "31": 4.6,   # Toulouse
    "59": 5.8,   # Lille
    "69": 4.1,   # Lyon
    "75": 3.2,   # Paris
}

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/scoring/", response_model=ScoringResponse)
async def get_scoring(request: ScoringRequest):
    dept = request.code_departement.strip()
    if dept not in AVAILABLE_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown department '{dept}'. Available: {list(AVAILABLE_DEPARTMENTS.keys())}",
        )

    try:
        prediction, breakdown = scoring_function(
            surface_reelle_bati=request.surface_reelle_bati,
            nombre_pieces_principales=request.nombre_pieces_principales,
            code_departement=dept,
            type_local=request.type_local
        )
    except FileNotFoundError as e:
        logger.error("Model artifacts missing: %s", e)
        raise HTTPException(
            status_code=503,
            detail="No trained model is available. Please train a model first.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Scoring failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Scoring failed unexpectedly: {e}",
        )

    dept_stats = DEPT_STATS.get(dept, {})

    return {"score": prediction, "breakdown": breakdown, "dept_stats": dept_stats}


@router.get("/departments/", response_model=DepartmentResponse)
async def get_departments():
    return {
        "departments": AVAILABLE_DEPARTMENTS,
        "main_cities": DEPT_MAIN_CITY,
        "centers": DEPT_CENTER,
        "zoom_levels": DEPT_ZOOM,
    }


@router.get("/communes/{dept_code}", response_model=CommuneResponse)
async def get_communes(dept_code: str):
    data = COMMUNE_DATA.get(dept_code.strip(), {"communes": [], "zipcodes": []})
    return data


@router.get("/commune_coords/{dept_code}/{commune_name}", response_model=CoordsResponse)
async def get_commune_coords(dept_code: str, commune_name: str):
    key = f"{dept_code.strip()}_{commune_name}"
    coords = COMMUNE_COORDS.get(key)
    return {"coords": coords}


@router.get("/zipcode_coords/{dept_code}/{zipcode}", response_model=CoordsResponse)
async def get_zipcode_coords(dept_code: str, zipcode: str):
    key = f"{dept_code.strip()}_zip_{zipcode.strip()}"
    coords = COMMUNE_COORDS.get(key)
    return {"coords": coords}


@router.get("/comparables/", response_model=ComparablesResponse)
async def get_comparables(
    code_departement: str,
    surface_reelle_bati: float,
    nombre_pieces_principales: float,
    type_local: str,
    n: int = 5,
):
    """Return the N most similar properties in the same department."""
    dept = code_departement.strip()
    if dept not in AVAILABLE_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown department '{dept}'. Available: {list(AVAILABLE_DEPARTMENTS.keys())}",
        )

    if CLEANED_DF.empty:
        return {"comparables": []}
    sub = CLEANED_DF[CLEANED_DF["code_departement"] == dept].copy()

    # Filter to same property type
    same_type = sub[sub["type_local"] == type_local]
    if len(same_type) >= n:
        sub = same_type

    # Compute a similarity score (weighted distance on surface and rooms)
    sub = sub.copy()
    sub["_surf_diff"] = ((sub["surface_reelle_bati"] - surface_reelle_bati) / max(surface_reelle_bati, 1)) ** 2
    sub["_room_diff"] = ((sub["nombre_pieces_principales"] - nombre_pieces_principales) / max(nombre_pieces_principales, 1)) ** 2
    sub["_dist"] = sub["_surf_diff"] + sub["_room_diff"]

    top = sub.nsmallest(n, "_dist")

    comparables = []
    for _, row in top.iterrows():
        comparables.append({
            "price": round(float(row["valeur_fonciere"]), 0),
            "surface": round(float(row["surface_reelle_bati"]), 1),
            "rooms": int(row["nombre_pieces_principales"]),
            "type": row["type_local"],
            "price_per_m2": round(float(row["price_per_m2"]), 0),
        })

    return {"comparables": comparables}


@router.get("/investment/", response_model=InvestmentResponse)
async def get_investment(
    code_departement: str,
    prediction: float,
    surface_reelle_bati: float,
):
    """Return investment insight metrics for a given prediction."""
    dept = code_departement.strip()
    if dept not in AVAILABLE_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown department '{dept}'. Available: {list(AVAILABLE_DEPARTMENTS.keys())}",
        )
    if prediction <= 0:
        raise HTTPException(status_code=400, detail="prediction must be > 0")
    if surface_reelle_bati <= 0:
        raise HTTPException(status_code=400, detail="surface_reelle_bati must be > 0")

    rental_yield = RENTAL_YIELDS.get(dept)
    if rental_yield is None:
        raise HTTPException(
            status_code=500,
            detail=f"No rental yield data configured for department '{dept}'.",
        )

    market_growth = MARKET_GROWTH.get(dept)
    if market_growth is None:
        raise HTTPException(
            status_code=503,
            detail=f"Market growth data is unavailable for department '{dept}'. "
                   "The raw dataset may be missing.",
        )

    # Estimated monthly rent from yield
    monthly_rent = prediction * (rental_yield / 100) / 12

    # Investment score (0-10):
    #   rental yield component (40%): higher is better, baseline 3%
    #   market growth component (30%): positive growth is good
    #   affordability component (30%): lower price/m² vs dept avg is better
    yield_score = min(10, max(0, (rental_yield - 1) / 0.7))  # 1%->0, 8%->10
    growth_score = min(10, max(0, (market_growth + 5) / 1.5))  # -5%->0, 10%->10

    pred_pm2 = prediction / max(surface_reelle_bati, 1)
    dept_avg = DEPT_STATS.get(dept, {}).get("avg_price_per_m2")
    if dept_avg is None or dept_avg <= 0:
        raise HTTPException(
            status_code=503,
            detail=f"Average price per m² is unavailable for department '{dept}'. "
                   "Run data cleaning to regenerate cleaned_dataset.csv.",
        )

    afford_ratio = pred_pm2 / dept_avg
    afford_score = min(10, max(0, (2 - afford_ratio) * 10))  # ratio 0.5->15(cap 10), 1.0->10, 2.0->0

    investment_score = round(yield_score * 0.4 + growth_score * 0.4 + afford_score * 0.2, 1)
    investment_score = min(10.0, max(0.0, investment_score))

    return {
        "rental_yield": rental_yield,
        "monthly_rent": round(monthly_rent, 0),
        "market_growth": market_growth,
        "investment_score": investment_score,
    }
