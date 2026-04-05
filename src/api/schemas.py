from pydantic import BaseModel, field_validator
from typing import Optional, Dict, List, Any

class ScoringRequest(BaseModel):
    surface_reelle_bati: float
    nombre_pieces_principales: float
    code_departement: str
    type_local: str

    @field_validator("surface_reelle_bati")
    @classmethod
    def surface_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("surface_reelle_bati must be greater than 0")
        return v

    @field_validator("nombre_pieces_principales")
    @classmethod
    def rooms_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("nombre_pieces_principales must be greater than 0")
        return v

    @field_validator("type_local")
    @classmethod
    def type_local_must_be_valid(cls, v):
        allowed = {"Appartement", "Maison"}
        if v not in allowed:
            raise ValueError(f"type_local must be one of {allowed}, got '{v}'")
        return v

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
