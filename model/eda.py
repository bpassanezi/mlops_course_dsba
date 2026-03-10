import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

DATASETS = [
    "bouches_du_rhone_dataset.csv",
    "haute_garonne_dataset.csv",
    "nord_dataset.csv",
    "paris_dataset.csv",
    "rhone_dataset.csv",
]


def load_dataset(filename: str) -> pd.DataFrame:
    filepath = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(filepath, low_memory=False)
    # Coerce key numeric columns that may have mixed types
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
    """Analyze valeur_fonciere (property value) — the likely target variable."""
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
        "skewness": round(s.skew(), 2), # pyright: ignore[reportArgumentType] # type: ignore
        "kurtosis": round(s.kurtosis(), 2), # type: ignore
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
    """Detect outliers using IQR method."""
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
    print(f"  EDA — {name}")
    print("=" * 80)

    df = load_dataset(filename)

    # 1. Basic info
    info = basic_info(df, name)
    print(f"\n--- Basic Information ---")
    for k, v in info.items():
        print(f"  {k}: {v}")

    # 2. Missing values
    print(f"\n--- Missing Values (columns with missing data) ---")
    mv = missing_values_summary(df)
    if mv.empty:
        print("  No missing values.")
    else:
        print(mv.to_string())

    # 3. Numeric summary
    print(f"\n--- Numeric Columns Summary ---")
    print(numeric_summary(df).to_string())

    # 4. Categorical summary
    print(f"\n--- Categorical Columns Summary ---")
    cs = categorical_summary(df)
    if not cs.empty:
        print(cs.to_string(index=False))

    # 5. Target variable (valeur_fonciere)
    print(f"\n--- Target Variable: valeur_fonciere (Property Value) ---")
    tva = target_variable_analysis(df)
    for k, v in tva.items():
        print(f"  {k}: {v}")

    # 6. Mutation type distribution
    print(f"\n--- Transaction Type Distribution ---")
    mtd = mutation_type_distribution(df)
    if not mtd.empty:
        print(mtd.to_string())

    # 7. Property type distribution
    print(f"\n--- Property Type Distribution ---")
    ptd = property_type_distribution(df)
    if not ptd.empty:
        print(ptd.to_string())

    # 8. Top communes
    print(f"\n--- Top 10 Communes by Transactions ---")
    tc = top_communes(df, 10)
    if not tc.empty:
        print(tc.to_string())

    # 9. Price by property type
    print(f"\n--- Mean/Median Price by Property Type ---")
    pbp = price_by_property_type(df)
    if not pbp.empty:
        print(pbp.to_string())

    # 10. Surface analysis
    print(f"\n--- Surface Reelle Bati (Built Area) Analysis ---")
    sa = surface_analysis(df)
    for k, v in sa.items():
        print(f"  {k}: {v}")

    # 11. Correlation matrix
    print(f"\n--- Correlation Matrix (Key Features) ---")
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


def main():
    for filename in DATASETS:
        run_eda(filename)


if __name__ == "__main__":
    main()
