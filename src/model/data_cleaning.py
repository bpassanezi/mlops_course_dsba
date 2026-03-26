import os
import pandas as pd
import numpy as np

# Data lives in the project root's data/ folder (two levels up from src/model/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")

DATASETS = [
    "bouches_du_rhone_dataset.csv",
    "haute_garonne_dataset.csv",
    "nord_dataset.csv",
    "paris_dataset.csv",
    "rhone_dataset.csv",
]

# Columns needed for the model (aligned with CESAR contract)
TARGET = "valeur_fonciere"
FEATURE_COLS = [
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "code_departement",
    "type_local",
]
EXTRA_COLS = [
    "longitude",
    "latitude",
    "surface_terrain",
    "code_postal",
    "nom_commune",
]
KEEP_COLS = [TARGET] + FEATURE_COLS + EXTRA_COLS

# Valid property types
VALID_TYPE_LOCAL = [
    "Appartement",
    "Maison",
    "Dépendance",
    "Local industriel. commercial ou assimilé",
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_dataset(filename: str) -> pd.DataFrame:
    """Load a single CSV and coerce key numeric columns."""
    filepath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(filepath, low_memory=False)
    numeric_cols = [
        "valeur_fonciere", "surface_reelle_bati", "nombre_pieces_principales",
        "surface_terrain", "longitude", "latitude", "adresse_numero",
        "code_postal", "code_type_local", "numero_volume",
        "lot1_surface_carrez", "lot2_surface_carrez", "lot3_surface_carrez",
        "lot4_surface_carrez", "lot5_surface_carrez",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_all_datasets() -> pd.DataFrame:
    """Load and concatenate all CSV datasets from the data folder."""
    frames = []
    for filename in DATASETS:
        frames.append(load_dataset(filename))
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# EDA helpers
# ---------------------------------------------------------------------------

def basic_info(df: pd.DataFrame, name: str) -> dict:
    """Return basic dataset information."""
    return {
        "dataset": name,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
        "duplicated_rows": int(df.duplicated().sum()),
    }


def missing_values_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return missing values count and percentage per column."""
    missing = df.isnull().sum()
    pct = (missing / len(df) * 100).round(2)
    summary = pd.DataFrame({"missing_count": missing, "missing_pct": pct})
    return summary[summary["missing_count"] > 0].sort_values(
        "missing_pct", ascending=False
    )


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Descriptive statistics for numeric columns."""
    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return pd.DataFrame()
    return num_df.describe().T


def categorical_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Value counts and unique values for categorical/object columns."""
    cat_cols = df.select_dtypes(include=["object", "string"]).columns
    records = []
    for col in cat_cols:
        records.append(
            {
                "column": col,
                "unique_values": df[col].nunique(),
                "most_frequent": df[col].mode().iloc[0] if not df[col].mode().empty else None,
                "most_frequent_count": int(df[col].value_counts().iloc[0]) if df[col].value_counts().shape[0] > 0 else 0,
                "most_frequent_pct": round(
                    df[col].value_counts(normalize=True).iloc[0] * 100, 2
                ) if df[col].value_counts().shape[0] > 0 else 0,
            }
        )
    return pd.DataFrame(records)


def target_variable_analysis(df: pd.DataFrame) -> dict:
    """Analyze valeur_fonciere (property value) - the likely target variable."""
    col = "valeur_fonciere"
    if col not in df.columns:
        return {}
    s = df[col].dropna()
    return {
        "count": len(s),
        "mean": round(s.mean(), 2),
        "median": round(s.median(), 2),
        "std": round(s.std(), 2),
        "min": round(s.min(), 2),
        "max": round(s.max(), 2),
        "skewness": round(s.skew(), 2),  # type: ignore
        "kurtosis": round(s.kurtosis(), 2),  # type: ignore
        "q1": round(s.quantile(0.25), 2),
        "q3": round(s.quantile(0.75), 2),
        "iqr": round(s.quantile(0.75) - s.quantile(0.25), 2),
    }


def mutation_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Distribution of transaction types (nature_mutation)."""
    if "nature_mutation" not in df.columns:
        return pd.DataFrame()
    counts = df["nature_mutation"].value_counts()
    pct = df["nature_mutation"].value_counts(normalize=True).mul(100).round(2)
    return pd.DataFrame({"count": counts, "pct": pct})


def property_type_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Distribution of property types (type_local)."""
    if "type_local" not in df.columns:
        return pd.DataFrame()
    counts = df["type_local"].value_counts()
    pct = df["type_local"].value_counts(normalize=True).mul(100).round(2)
    return pd.DataFrame({"count": counts, "pct": pct})


def top_communes(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N communes by number of transactions."""
    if "nom_commune" not in df.columns:
        return pd.DataFrame()
    counts = df["nom_commune"].value_counts().head(n)
    return pd.DataFrame({"transactions": counts})


def price_by_property_type(df: pd.DataFrame) -> pd.DataFrame:
    """Mean and median price per property type."""
    if "type_local" not in df.columns or "valeur_fonciere" not in df.columns:
        return pd.DataFrame()
    grouped = df.groupby("type_local")["valeur_fonciere"].agg(
        ["mean", "median", "count", "std"]
    )
    return grouped.round(2)


def surface_analysis(df: pd.DataFrame) -> dict:
    """Analyze surface_reelle_bati (built surface area)."""
    col = "surface_reelle_bati"
    if col not in df.columns:
        return {}
    s = df[col].dropna()
    if len(s) == 0:
        return {}
    return {
        "count": len(s),
        "mean": round(s.mean(), 2),
        "median": round(s.median(), 2),
        "std": round(s.std(), 2),
        "min": round(s.min(), 2),
        "max": round(s.max(), 2),
    }


def correlation_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix for key numeric features."""
    key_cols = [
        "valeur_fonciere",
        "surface_reelle_bati",
        "nombre_pieces_principales",
        "surface_terrain",
        "longitude",
        "latitude",
    ]
    available = [c for c in key_cols if c in df.columns]
    if len(available) < 2:
        return pd.DataFrame()
    return df[available].corr().round(3)


def outlier_detection(df: pd.DataFrame, column: str) -> dict:
    """Detect outliers using IQR method (reporting only, does not remove)."""
    if column not in df.columns:
        return {}
    s = df[column].dropna()
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = s[(s < lower) | (s > upper)]
    return {
        "total_values": len(s),
        "outliers_count": len(outliers),
        "outliers_pct": round(len(outliers) / len(s) * 100, 2),
        "lower_bound": round(lower, 2),
        "upper_bound": round(upper, 2),
    }


def run_eda(filename: str) -> None:
    """Run full EDA for a single dataset and print results."""
    name = filename.replace("_dataset.csv", "").replace("_", " ").title()
    print("=" * 80)
    print(f"  EDA - {name}")
    print("=" * 80)

    df = load_dataset(filename)

    # 1. Basic info
    info = basic_info(df, name)
    print("\n--- Basic Information ---")
    for k, v in info.items():
        print(f"  {k}: {v}")

    # 2. Missing values
    print("\n--- Missing Values (columns with missing data) ---")
    mv = missing_values_summary(df)
    if mv.empty:
        print("  No missing values.")
    else:
        print(mv.to_string())

    # 3. Numeric summary
    print("\n--- Numeric Columns Summary ---")
    print(numeric_summary(df).to_string())

    # 4. Categorical summary
    print("\n--- Categorical Columns Summary ---")
    cs = categorical_summary(df)
    if not cs.empty:
        print(cs.to_string(index=False))

    # 5. Target variable (valeur_fonciere)
    print("\n--- Target Variable: valeur_fonciere (Property Value) ---")
    tva = target_variable_analysis(df)
    for k, v in tva.items():
        print(f"  {k}: {v}")

    # 6. Mutation type distribution
    print("\n--- Transaction Type Distribution ---")
    mtd = mutation_type_distribution(df)
    if not mtd.empty:
        print(mtd.to_string())

    # 7. Property type distribution
    print("\n--- Property Type Distribution ---")
    ptd = property_type_distribution(df)
    if not ptd.empty:
        print(ptd.to_string())

    # 8. Top communes
    print("\n--- Top 10 Communes by Transactions ---")
    tc = top_communes(df, 10)
    if not tc.empty:
        print(tc.to_string())

    # 9. Price by property type
    print("\n--- Mean/Median Price by Property Type ---")
    pbp = price_by_property_type(df)
    if not pbp.empty:
        print(pbp.to_string())

    # 10. Surface analysis
    print("\n--- Surface Reelle Bati (Built Area) Analysis ---")
    sa = surface_analysis(df)
    for k, v in sa.items():
        print(f"  {k}: {v}")

    # 11. Correlation matrix
    print("\n--- Correlation Matrix (Key Features) ---")
    corr = correlation_analysis(df)
    if not corr.empty:
        print(corr.to_string())

    # 12. Outlier detection
    for col in ["valeur_fonciere", "surface_reelle_bati"]:
        print(f"\n--- Outlier Detection: {col} (IQR method) ---")
        od = outlier_detection(df, col)
        for k, v in od.items():
            print(f"  {k}: {v}")

    print("\n")


def run_all_eda() -> None:
    """Run EDA on every dataset."""
    for filename in DATASETS:
        run_eda(filename)


# ---------------------------------------------------------------------------
# Data cleaning
# ---------------------------------------------------------------------------

def remove_outliers_iqr(
    df: pd.DataFrame, column: str, factor: float = 1.5
) -> pd.DataFrame:
    """Remove outliers using the IQR method."""
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return df[(df[column] >= lower) & (df[column] <= upper)]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning steps and return a model-ready DataFrame.

    Steps:
      1. Filter to standard sales (Vente) only
      2. Keep only relevant columns
      3. Coerce numeric types
      4. Drop rows missing the target or required features
      5. Remove non-positive target / surface values
      6. Standardise type_local encoding
      7. Filter to valid property types
      8. Remove duplicate rows
      9. Remove outliers on valeur_fonciere and surface_reelle_bati
      10. Cast code_departement to string
    """
    # 1 – Keep only standard sales
    if "nature_mutation" in df.columns:
        df = df[df["nature_mutation"] == "Vente"].copy()

    # 2 – Select relevant columns
    available = [c for c in KEEP_COLS if c in df.columns]
    df = df[available].copy()

    # 3 – Coerce numeric columns
    numeric_cols = [
        "valeur_fonciere",
        "surface_reelle_bati",
        "nombre_pieces_principales",
        "surface_terrain",
        "longitude",
        "latitude",
        "code_postal",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4 – Drop rows where target or core features are missing
    required = [TARGET] + FEATURE_COLS
    df = df.dropna(subset=[c for c in required if c in df.columns])

    # 5 – Remove non-positive values
    df = df[df[TARGET] > 0]
    df = df[df["surface_reelle_bati"] > 0]
    df = df[df["nombre_pieces_principales"] > 0]

    # 6 – Fix encoding artefacts in type_local
    df["type_local"] = (
        df["type_local"]
        .str.strip()
        .str.replace("Dépendance", "Dépendance", regex=False)
        .str.replace("DÃ©pendance", "Dépendance", regex=False)
        .str.replace("assimilé", "assimilé", regex=False)
        .str.replace("assimilÃ©", "assimilé", regex=False)
    )

    # 7 – Keep only valid property types
    df = df[df["type_local"].isin(VALID_TYPE_LOCAL)]

    # 8 – Remove duplicate rows
    df = df.drop_duplicates()

    # 9 – Remove outliers
    df = remove_outliers_iqr(df, "valeur_fonciere")
    df = remove_outliers_iqr(df, "surface_reelle_bati")

    # 10 – Ensure code_departement is a string (e.g. "13", "75")
    df["code_departement"] = df["code_departement"].astype(str).str.strip()

    # 11 – Keep only the columns used for modelling
    model_cols = [TARGET] + FEATURE_COLS
    df = df[model_cols]

    df = df.reset_index(drop=True)
    return df


def load_and_clean() -> pd.DataFrame:
    """Entry-point: load all datasets, clean, and return a model-ready DataFrame."""
    raw = load_all_datasets()
    return clean_data(raw)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    usage = "Usage: python data_cleaning.py [eda | clean]  (default: clean)"

    mode = sys.argv[1] if len(sys.argv) > 1 else "clean"

    if mode == "eda":
        run_all_eda()

    elif mode == "clean":
        df = load_and_clean()
        out_path = os.path.join(DATA_DIR, "cleaned_dataset.csv")
        df.to_csv(out_path, index=False)
        print(f"Cleaned dataset: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"Columns: {list(df.columns)}")
        print(f"Saved to {out_path}")

    else:
        print(usage)
