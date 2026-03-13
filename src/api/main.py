import os
import warnings
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from scoring.predict import scoring_function

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

app = FastAPI()

# ---------------------------------------------------------------------------
# Pre-compute department-level statistics at startup
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")

AVAILABLE_DEPARTMENTS = {
    "13": "Bouches-du-Rhône",
    "31": "Haute-Garonne",
    "59": "Nord",
    "69": "Rhône",
    "75": "Paris",
}

DEPT_MAIN_CITY = {
    "13": "Marseille",
    "31": "Toulouse",
    "59": "Lille",
    "69": "Lyon",
    "75": "Paris",
}

DEPT_CENTER = {
    "13": [43.45, 5.05],
    "31": [43.35, 1.25],
    "59": [50.35, 3.25],
    "69": [45.85, 4.60],
    "75": [48.86, 2.35],
}

DEPT_ZOOM = {
    "13": 9,
    "31": 9,
    "59": 9,
    "69": 9,
    "75": 12,
}

RAW_DATASETS = {
    "13": "bouches_du_rhone_dataset.csv",
    "31": "haute_garonne_dataset.csv",
    "59": "nord_dataset.csv",
    "69": "rhone_dataset.csv",
    "75": "paris_dataset.csv",
}


def _load_dept_stats() -> dict:
    """Compute average price/m² per department from cleaned dataset."""
    cleaned_path = os.path.join(DATA_DIR, "cleaned_dataset.csv")
    if not os.path.exists(cleaned_path):
        return {}
    df = pd.read_csv(cleaned_path, low_memory=False)
    df["code_departement"] = df["code_departement"].astype(str).str.strip()
    df = df[(df["surface_reelle_bati"] > 0) & (df["valeur_fonciere"] > 0)]
    df["price_per_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]

    stats = {}
    for dept in AVAILABLE_DEPARTMENTS:
        sub = df[df["code_departement"] == dept]
        if sub.empty:
            continue
        stats[dept] = {
            "avg_price_per_m2": round(float(sub["price_per_m2"].mean()), 2),
            "median_price_per_m2": round(float(sub["price_per_m2"].median()), 2),
            "transaction_count": int(len(sub)),
        }
    return stats


def _load_commune_and_coords() -> tuple:
    """Load commune names, zipcodes, and average coordinates per commune."""
    commune_data = {}
    commune_coords = {}
    cols = ["code_departement", "nom_commune", "code_postal", "longitude", "latitude"]
    for dept, filename in RAW_DATASETS.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, usecols=cols, dtype={"code_departement": str, "nom_commune": str, "code_postal": str})
        df["code_departement"] = df["code_departement"].str.strip()
        sub = df[df["code_departement"] == dept]

        # Communes and zipcodes
        communes = sorted(sub["nom_commune"].dropna().unique().tolist())
        raw_zips = sub["code_postal"].dropna().unique()
        zipcodes = sorted([z.split(".")[0] for z in raw_zips])  # handle "75001.0"
        commune_data[dept] = {"communes": communes, "zipcodes": zipcodes}

        # Coordinates
        sub_geo = sub.dropna(subset=["longitude", "latitude"])
        sub_geo = sub_geo.copy()
        sub_geo["longitude"] = pd.to_numeric(sub_geo["longitude"], errors="coerce")
        sub_geo["latitude"] = pd.to_numeric(sub_geo["latitude"], errors="coerce")
        sub_geo = sub_geo.dropna(subset=["longitude", "latitude"])

        for commune, grp in sub_geo.groupby("nom_commune"):
            commune_coords[f"{dept}_{commune}"] = [float(grp["latitude"].mean()), float(grp["longitude"].mean())]

        for zc, grp in sub_geo.groupby("code_postal"):
            commune_coords[f"{dept}_zip_{zc.split('.')[0]}"] = [float(grp["latitude"].mean()), float(grp["longitude"].mean())]

    return commune_data, commune_coords


def _load_cleaned_df() -> pd.DataFrame:
    """Load cleaned dataset for comparables queries."""
    cleaned_path = os.path.join(DATA_DIR, "cleaned_dataset.csv")
    if not os.path.exists(cleaned_path):
        return pd.DataFrame()
    df = pd.read_csv(cleaned_path, low_memory=False)
    df["code_departement"] = df["code_departement"].astype(str).str.strip()
    df = df[(df["surface_reelle_bati"] > 0) & (df["valeur_fonciere"] > 0)]
    df["price_per_m2"] = (df["valeur_fonciere"] / df["surface_reelle_bati"]).round(2)
    return df


print("Loading department statistics...")
DEPT_STATS = _load_dept_stats()
print("Loading commune data...")
COMMUNE_DATA, COMMUNE_COORDS = _load_commune_and_coords()
print("Loading cleaned dataset...")
CLEANED_DF = _load_cleaned_df()
print("Data loading complete.")


class ScoringRequest(BaseModel):
    surface_reelle_bati: float
    nombre_pieces_principales: float
    code_departement: str
    type_local: str


@app.post("/scoring/")
async def get_scoring(request: ScoringRequest):
    prediction, breakdown = scoring_function(
        surface_reelle_bati=request.surface_reelle_bati,
        nombre_pieces_principales=request.nombre_pieces_principales,
        code_departement=request.code_departement,
        type_local=request.type_local
    )

    dept = request.code_departement.strip()
    dept_stats = DEPT_STATS.get(dept, {})

    return {"score": prediction, "breakdown": breakdown, "dept_stats": dept_stats}


@app.get("/departments/")
async def get_departments():
    return {
        "departments": AVAILABLE_DEPARTMENTS,
        "main_cities": DEPT_MAIN_CITY,
        "centers": DEPT_CENTER,
        "zoom_levels": DEPT_ZOOM,
    }


@app.get("/communes/{dept_code}")
async def get_communes(dept_code: str):
    data = COMMUNE_DATA.get(dept_code.strip(), {"communes": [], "zipcodes": []})
    return data


@app.get("/commune_coords/{dept_code}/{commune_name}")
async def get_commune_coords(dept_code: str, commune_name: str):
    key = f"{dept_code.strip()}_{commune_name}"
    coords = COMMUNE_COORDS.get(key)
    return {"coords": coords}


@app.get("/zipcode_coords/{dept_code}/{zipcode}")
async def get_zipcode_coords(dept_code: str, zipcode: str):
    key = f"{dept_code.strip()}_zip_{zipcode.strip()}"
    coords = COMMUNE_COORDS.get(key)
    return {"coords": coords}


@app.get("/comparables/")
async def get_comparables(
    code_departement: str,
    surface_reelle_bati: float,
    nombre_pieces_principales: float,
    type_local: str,
    n: int = 5,
):
    """Return the N most similar properties in the same department."""
    if CLEANED_DF.empty:
        return {"comparables": []}

    dept = code_departement.strip()
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


# ---------------------------------------------------------------------------
# Investment insight helpers
# ---------------------------------------------------------------------------

# Realistic gross rental yields for each department (annual % of property value)
RENTAL_YIELDS = {
    "13": 5.3,   # Marseille
    "31": 4.6,   # Toulouse
    "59": 5.8,   # Lille
    "69": 4.1,   # Lyon
    "75": 3.2,   # Paris
}


def _compute_market_growth() -> dict:
    """Compute YoY median price/m² growth from last 2 full years in raw data."""
    growth = {}
    for dept, filename in RAW_DATASETS.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            continue
        df = pd.read_csv(
            path,
            usecols=["date_mutation", "valeur_fonciere", "surface_reelle_bati"],
            dtype=str,
        )
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors="coerce")
        df["valeur_fonciere"] = pd.to_numeric(df["valeur_fonciere"], errors="coerce")
        df["surface_reelle_bati"] = pd.to_numeric(df["surface_reelle_bati"], errors="coerce")
        df = df[(df["surface_reelle_bati"] > 0) & (df["valeur_fonciere"] > 0)].dropna(subset=["date_mutation"])
        df["year"] = df["date_mutation"].dt.year
        df["ppm2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]
        yearly = df.groupby("year")["ppm2"].median()
        if len(yearly) >= 2:
            last2 = yearly.iloc[-2:]
            pct = (last2.iloc[-1] - last2.iloc[-2]) / last2.iloc[-2] * 100
            growth[dept] = round(float(pct), 1)
        else:
            growth[dept] = 0.0
    return growth


print("Computing market growth...")
MARKET_GROWTH = _compute_market_growth()
print("Market growth computed.")


@app.get("/investment/")
async def get_investment(
    code_departement: str,
    prediction: float,
    surface_reelle_bati: float,
):
    """Return investment insight metrics for a given prediction."""
    dept = code_departement.strip()
    rental_yield = RENTAL_YIELDS.get(dept, 4.5)
    market_growth = MARKET_GROWTH.get(dept, 0.0)

    # Estimated monthly rent from yield
    monthly_rent = prediction * (rental_yield / 100) / 12

    # Investment score (0-10):
    #   rental yield component (40%): higher is better, baseline 3%
    #   market growth component (30%): positive growth is good
    #   affordability component (30%): lower price/m² vs dept avg is better
    yield_score = min(10, max(0, (rental_yield - 1) / 0.7))  # 1%->0, 8%->10
    growth_score = min(10, max(0, (market_growth + 5) / 1.5))  # -5%->0, 10%->10

    pred_pm2 = prediction / max(surface_reelle_bati, 1)
    dept_avg = DEPT_STATS.get(dept, {}).get("avg_price_per_m2", pred_pm2)
    if dept_avg > 0:
        afford_ratio = pred_pm2 / dept_avg
        afford_score = min(10, max(0, (2 - afford_ratio) * 10))  # ratio 0.5->15(cap 10), 1.0->10, 2.0->0
    else:
        afford_score = 5.0

    investment_score = round(yield_score * 0.4 + growth_score * 0.4 + afford_score * 0.2, 1)
    investment_score = min(10.0, max(0.0, investment_score))

    return {
        "rental_yield": rental_yield,
        "monthly_rent": round(monthly_rent, 0),
        "market_growth": market_growth,
        "investment_score": investment_score,
    }