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

from model.score import evaluate_model

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODEL_DIR = os.path.join(os.path.dirname(__file__))
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

TARGET = "valeur_fonciere"
NUMERIC_FEATURES = ["surface_reelle_bati", "nombre_pieces_principales"]
CATEGORICAL_FEATURES = ["code_departement", "type_local"]
FEATURE_COLS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
ENGINEERED_FEATURES = ["surface_per_room", "log_surface"]


# Minimum price threshold – rows below this are not real sales
MIN_PRICE = 10000


def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset and filter unrealistic prices."""
    path = os.path.join(DATA_DIR, "cleaned_dataset.csv")
    df = pd.read_csv(path)
    df["code_departement"] = df["code_departement"].astype(str)
    df = df[df[TARGET] >= MIN_PRICE].reset_index(drop=True)

    # Feature engineering
    df["surface_per_room"] = df["surface_reelle_bati"] / df["nombre_pieces_principales"]
    df["log_surface"] = np.log1p(df["surface_reelle_bati"])

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
    joblib.dump(model, model_path)

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
    with open(contract_path, "w") as f:
        json.dump(contract, f, indent=2)

    print(f"\nModel saved to  {model_path}")
    print(f"Contract saved to {contract_path}")

    return {
        "version": version,
        "model_path": model_path,
        "contract_path": contract_path,
        "metrics": metrics,
    }


if __name__ == "__main__":
    train_and_export()
