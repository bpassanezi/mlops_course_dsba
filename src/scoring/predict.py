import os
import glob
import json
import joblib
import pandas as pd
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
        features=features
    )

    prediction = model.predict(df)

    return float(prediction[0])
