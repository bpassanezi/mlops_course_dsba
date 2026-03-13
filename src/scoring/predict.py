import os
import glob
import json
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from model.train import preprocess_data

def get_latest_artifacts_path():
    """Find the most recent model and contract files in the artifacts directory."""
    # The artifacts are in the root model/artifacts directory
    # Current file is in src/scoring/predict.py
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    artifact_dir = os.path.join(base_dir, "models")
    
    model_files = sorted(glob.glob(os.path.join(artifact_dir, "model_*.joblib")))
    contract_files = sorted(glob.glob(os.path.join(artifact_dir, "contract_*.json")))
    
    if not model_files or not contract_files:
        raise FileNotFoundError(f"No model artifacts found in {artifact_dir}")
    
    return model_files[-1], contract_files[-1]


def load_latest_artifacts():
    latest_model_path, latest_contract_path = get_latest_artifacts_path()

    model = joblib.load(latest_model_path)

    with open(latest_contract_path) as f:
        contract = json.load(f)

    return model, contract


def create_df_from_request(
    surface_reelle_bati, nombre_pieces_principales, code_departement, type_local,
    features):

    input_request = {
        "surface_reelle_bati": [surface_reelle_bati],
        "nombre_pieces_principales": [nombre_pieces_principales],
        "code_departement": [str(code_departement)],
        "type_local": [type_local],
    }

    df = pd.DataFrame(
        input_request
    )

    df = preprocess_data(df)

    # Ensure we only return the features the model expects
    df = df[features]

    return df


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


def scoring_function(
    surface_reelle_bati: float,
    nombre_pieces_principales: float,
    code_departement: str,
    type_local: str,
):
    model, contract = load_latest_artifacts()
    features = contract["features"]

    df = create_df_from_request(
        surface_reelle_bati=surface_reelle_bati,
        nombre_pieces_principales=nombre_pieces_principales,
        code_departement=code_departement,
        type_local=type_local,
        features=features,
    )

    prediction = model.predict(df)

    base_value, feature_contribs = _compute_contributions(model, df)
    breakdown = _group_contributions(base_value, feature_contribs)

    return float(prediction[0]), breakdown
