from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class ScoringRequest(BaseModel):
    surface_reelle_bati: float
    nombre_pieces_principales: float
    code_departement: str
    type_local: str

class ScoringResponse(BaseModel):
    score: float
    breakdown: Dict[str, float]
    dept_stats: Dict[str, Any]

class DepartmentResponse(BaseModel):
    departments: Dict[str, str]
    main_cities: Dict[str, str]
    centers: Dict[str, List[float]]
    zoom_levels: Dict[str, int]

class CommuneResponse(BaseModel):
    communes: List[str]
    zipcodes: List[str]

class CoordsResponse(BaseModel):
    coords: Optional[List[float]] = None

class ComparableItem(BaseModel):
    price: float
    surface: float
    rooms: int
    type: str
    price_per_m2: float

class ComparablesResponse(BaseModel):
    comparables: List[ComparableItem]

class InvestmentResponse(BaseModel):
    rental_yield: float
    monthly_rent: float
    market_growth: float
    investment_score: float
