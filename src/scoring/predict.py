import os
import glob
import json
import logging
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from model.train import preprocess_data

logger = logging.getLogger(__name__)

def get_latest_artifacts_path():
    """Find the most recent model and contract files in the artifacts directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    artifact_dir = os.path.join(base_dir, "models")
    
    model_files = sorted(glob.glob(os.path.join(artifact_dir, "model_*.joblib")))
    contract_files = sorted(glob.glob(os.path.join(artifact_dir, "contract_*.json")))
    
    if not model_files or not contract_files:
        raise FileNotFoundError(
            f"No model artifacts found in '{artifact_dir}'. "
            "Run 'python -m src.model.train' to train a model first."
        )
    
    return model_files[-1], contract_files[-1]


def load_latest_artifacts():
    latest_model_path, latest_contract_path = get_latest_artifacts_path()

    try:
        model = joblib.load(latest_model_path)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load model from '{latest_model_path}': {e}. "
            "The file may be corrupted — try retraining with 'python -m src.model.train'."
        ) from e

    try:
        with open(latest_contract_path) as f:
            contract = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(
            f"Failed to load contract from '{latest_contract_path}': {e}. "
            "The file may be corrupted — try retraining with 'python -m src.model.train'."
        ) from e

    return model, contract


def create_df_from_request(
    surface_reelle_bati, nombre_pieces_principales, code_departement, type_local,
    features):

    if nombre_pieces_principales <= 0:
        raise ValueError(
            f"nombre_pieces_principales must be > 0, got {nombre_pieces_principales}"
        )
    if surface_reelle_bati <= 0:
        raise ValueError(
            f"surface_reelle_bati must be > 0, got {surface_reelle_bati}"
        )

    input_request = {
        "surface_reelle_bati": [surface_reelle_bati],
        "nombre_pieces_principales": [nombre_pieces_principales],
        "code_departement": [str(code_departement)],
        "type_local": [type_local],
    }

    df = pd.DataFrame(input_request)
    df = preprocess_data(df)

    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(
            f"Feature mismatch: the model expects columns {missing} "
            "which could not be derived from the input. "
            "This usually means the model was trained with a different feature set."
        )

    return df[features]


def _compute_contributions(model, df):
    """Compute per-feature contributions using XGBoost's pred_contribs.

    Returns a dict mapping transformed feature names to their contribution
    values, plus a 'base_value' key.
    """
    preprocessor = model.named_steps["preprocessor"]
    regressor = model.named_steps["regressor"]

    X_transformed = preprocessor.transform(df)
    feature_names = preprocessor.get_feature_names_out()

    booster = regressor.get_booster()
    dmatrix = xgb.DMatrix(X_transformed, feature_names=list(feature_names))
    contribs = booster.predict(dmatrix, pred_contribs=True)

    # contribs shape: (1, n_features + 1)  – last column is the bias
    row = contribs[0]
    base_value = float(row[-1])
    feature_contribs = {name: float(row[i]) for i, name in enumerate(feature_names)}

    return base_value, feature_contribs


def _group_contributions(base_value, feature_contribs):
    """Aggregate per-feature contributions into human-readable groups."""
    surface_keys = ["num__surface_reelle_bati", "num__surface_per_room", "num__log_surface"]
    rooms_keys = ["num__nombre_pieces_principales"]

    surface_contrib = sum(feature_contribs.get(k, 0) for k in surface_keys)
    rooms_contrib = sum(feature_contribs.get(k, 0) for k in rooms_keys)

    location_contrib = sum(
        v for k, v in feature_contribs.items() if k.startswith("cat__code_departement_")
    )
    property_type_contrib = sum(
        v for k, v in feature_contribs.items() if k.startswith("cat__type_local_")
    )

    return {
        "base_value": round(base_value, 2),
        "surface_contribution": round(surface_contrib, 2),
        "location_effect": round(location_contrib, 2),
        "rooms_adjustment": round(rooms_contrib, 2),
        "property_type_adjustment": round(property_type_contrib, 2),
    }


def predict(
    surface_reelle_bati: float,
    nombre_pieces_principales: float,
    code_departement: str,
    type_local: str,
):
    model, contract = load_latest_artifacts()
    features = contract.get("features")
    if not features:
        raise RuntimeError(
            "Model contract is missing the 'features' key. "
            "Retrain the model with 'python -m src.model.train'."
        )

    df = create_df_from_request(
        surface_reelle_bati=surface_reelle_bati,
        nombre_pieces_principales=nombre_pieces_principales,
        code_departement=code_departement,
        type_local=type_local,
        features=features,
    )

    try:
        prediction = model.predict(df)
    except Exception as e:
        raise RuntimeError(
            f"Model prediction failed: {e}. "
            "The model file may be incompatible with the current input."
        ) from e

    try:
        base_value, feature_contribs = _compute_contributions(model, df)
        breakdown = _group_contributions(base_value, feature_contribs)
    except Exception as e:
        logger.warning("Could not compute price breakdown: %s", e)
        breakdown = {
            "base_value": float(prediction[0]),
            "surface_contribution": 0.0,
            "location_effect": 0.0,
            "rooms_adjustment": 0.0,
            "property_type_adjustment": 0.0,
        }

    return float(prediction[0]), breakdown
