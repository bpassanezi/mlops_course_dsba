import os
import logging
import warnings
import pandas as pd
from api.constants import AVAILABLE_DEPARTMENTS, RAW_DATASETS

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")


def _load_dept_stats() -> dict:
    """Compute average price/m² per department from cleaned dataset."""
    cleaned_path = os.path.join(DATA_DIR, "cleaned_dataset.csv")
    if not os.path.exists(cleaned_path):
        logger.warning("cleaned_dataset.csv not found at '%s' — department stats will be empty.", cleaned_path)
        return {}
    try:
        df = pd.read_csv(cleaned_path, low_memory=False)
    except Exception as e:
        logger.error("Failed to read cleaned_dataset.csv: %s", e)
        return {}
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
            logger.warning("Raw dataset '%s' not found — skipping department %s.", filename, dept)
            continue
        try:
            df = pd.read_csv(path, usecols=cols, dtype={"code_departement": str, "nom_commune": str, "code_postal": str})
        except Exception as e:
            logger.error("Failed to read '%s': %s — skipping department %s.", filename, e, dept)
            continue
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
        logger.warning("cleaned_dataset.csv not found — comparables will be unavailable.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(cleaned_path, low_memory=False)
    except Exception as e:
        logger.error("Failed to read cleaned_dataset.csv for comparables: %s", e)
        return pd.DataFrame()
    df["code_departement"] = df["code_departement"].astype(str).str.strip()
    df = df[(df["surface_reelle_bati"] > 0) & (df["valeur_fonciere"] > 0)]
    df["price_per_m2"] = (df["valeur_fonciere"] / df["surface_reelle_bati"]).round(2)
    return df


def _compute_market_growth() -> dict:
    """Compute YoY median price/m² growth from last 2 full years in raw data."""
    growth = {}
    for dept, filename in RAW_DATASETS.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            logger.warning("Raw dataset '%s' not found — market growth unavailable for department %s.", filename, dept)
            continue
        try:
            df = pd.read_csv(
                path,
                usecols=["date_mutation", "valeur_fonciere", "surface_reelle_bati"],
                dtype=str,
            )
        except Exception as e:
            logger.error("Failed to read '%s' for market growth: %s", filename, e)
            continue
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


try:
    print("Loading department statistics...")
    DEPT_STATS = _load_dept_stats()
    print("Loading commune data...")
    COMMUNE_DATA, COMMUNE_COORDS = _load_commune_and_coords()
    print("Loading cleaned dataset...")
    CLEANED_DF = _load_cleaned_df()
    print("Data loading complete.")

    print("Computing market growth...")
    MARKET_GROWTH = _compute_market_growth()
    print("Market growth computed.")
except Exception as e:
    logger.error("Critical error during data loading: %s", e, exc_info=True)
    print(f"WARNING: Data loading failed ({e}). The API will start with empty data.")
    DEPT_STATS = DEPT_STATS if "DEPT_STATS" in dir() else {}
    COMMUNE_DATA = COMMUNE_DATA if "COMMUNE_DATA" in dir() else {}
    COMMUNE_COORDS = COMMUNE_COORDS if "COMMUNE_COORDS" in dir() else {}
    CLEANED_DF = CLEANED_DF if "CLEANED_DF" in dir() else pd.DataFrame()
    MARKET_GROWTH = MARKET_GROWTH if "MARKET_GROWTH" in dir() else {}
