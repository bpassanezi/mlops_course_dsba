import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

try:
    from model.score import evaluate_model
except ModuleNotFoundError:
    from score import evaluate_model

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Base folder is project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
ARTIFACT_DIR = os.path.join(BASE_DIR, "models")

 
TARGET = "valeur_fonciere"
NUMERIC_FEATURES = ["surface_reelle_bati", "nombre_pieces_principales"]
CATEGORICAL_FEATURES = ["code_departement", "type_local"]
FEATURE_COLS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
ENGINEERED_FEATURES = ["surface_per_room", "log_surface"]


# Minimum price threshold – rows below this are not real sales
MIN_PRICE = 10000


def preprocess_data(df) -> pd.DataFrame(): # type: ignore
    """Preprocess input df"""

    df["code_departement"] = df["code_departement"].astype(str)

    # Feature engineering
    if (df["nombre_pieces_principales"] == 0).any():
        raise ValueError(
            "nombre_pieces_principales contains zero values — cannot compute surface_per_room. "
            "Filter these rows before preprocessing."
        )
    df["surface_per_room"] = df["surface_reelle_bati"] / df["nombre_pieces_principales"]
    df["log_surface"] = np.log1p(df["surface_reelle_bati"])

    return df

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset and filter unrealistic prices."""
    path = os.path.join(DATA_DIR, "cleaned_dataset.csv")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Cleaned dataset not found at '{path}'. "
            "Run 'python -m src.model.data_cleaning' first."
        )

    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read '{path}': {e}") from e

    df = df[df[TARGET] >= MIN_PRICE].reset_index(drop=True)
    if df.empty:
        raise ValueError(
            f"No rows remaining after filtering prices >= {MIN_PRICE}. "
            "Check that the cleaned dataset contains valid data."
        )

    df = preprocess_data(df)

    return df

def build_pipeline() -> Pipeline:
    """Build an sklearn pipeline with preprocessing + XGBRegressor."""

    all_numeric = NUMERIC_FEATURES + ENGINEERED_FEATURES

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), all_numeric),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    xgb = XGBRegressor(
        n_estimators=1000,
        max_depth=8,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        reg_alpha=1.0,
        reg_lambda=5.0,
        random_state=42,
        n_jobs=-1,
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", xgb),
        ]
    )

    return model


def train_and_export(
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """Train the model, evaluate, save artifacts, and return metrics.

    Saves:
      - artifacts/model_<version>.joblib   (the full sklearn pipeline)
      - artifacts/contract_<version>.json  (feature names, version, metadata)
    """
    # Load data
    df = load_cleaned_data()
    all_features = FEATURE_COLS + ENGINEERED_FEATURES
    X = df[all_features]
    y = df[TARGET]

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Build & fit
    model = build_pipeline()
    model.fit(X_train, y_train)

    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    train_metrics = evaluate_model(y_train.values, y_pred_train, prefix="train") # type: ignore
    test_metrics = evaluate_model(y_test.values, y_pred_test, prefix="test") # type: ignore
    metrics = {**train_metrics, **test_metrics}

    # Print metrics
    print("\n=== Training Metrics ===")
    for k, v in train_metrics.items():
        print(f"  {k}: {v}")
    print("\n=== Test Metrics ===")
    for k, v in test_metrics.items():
        print(f"  {k}: {v}")

    # Save artifacts
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    model_path = os.path.join(ARTIFACT_DIR, f"model_{version}.joblib")
    try:
        joblib.dump(model, model_path)
    except OSError as e:
        raise RuntimeError(
            f"Failed to save model to '{model_path}': {e}"
        ) from e

    contract = {
        "version": version,
        "target": TARGET,
        "features": all_features,
        "numeric_features": NUMERIC_FEATURES,
        "engineered_features": ENGINEERED_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "metrics": metrics,
    }
    contract_path = os.path.join(ARTIFACT_DIR, f"contract_{version}.json")
    try:
        with open(contract_path, "w") as f:
            json.dump(contract, f, indent=2)
    except OSError as e:
        raise RuntimeError(
            f"Failed to save contract to '{contract_path}': {e}"
        ) from e

    print(f"\nModel saved to  {model_path}")
    print(f"Contract saved to {contract_path}")

    return {
        "version": version,
        "model_path": model_path,
        "contract_path": contract_path,
        "metrics": metrics,
    }


if __name__ == "__main__":
    try:
        train_and_export()
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"ERROR: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error during training: {e}")
        exit(1)
