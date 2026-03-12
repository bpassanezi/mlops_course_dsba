# DSBA MLOps – Property Valuation Model

A modular MLOps project for estimating French property values (`valeur_fonciere`) from DVF (Demandes de Valeurs Foncières) open data. The system covers the full lifecycle: **data cleaning**, **model training** (XGBoost), **scoring API** (FastAPI), **tests**, and **Docker deployment**.

---

## Goal

- **Estimate** the value of a property from a small set of features: surface area, number of rooms, department code, and property type.
- **Serve** predictions via a REST API (`POST /scoring/`).

---

## Source Data

Property transaction data from DVF:
https://app.dvf.etalab.gouv.fr/

The `model/data/` folder contains regional CSV extracts (Paris, Rhône, Nord, Bouches-du-Rhône, Haute-Garonne). The data cleaning pipeline merges, filters, and prepares them for training.

---

## How to Run

### Prerequisites

- Python 3.9+
- pip

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Clean the Data

Merge raw regional CSVs into a single cleaned dataset:

```bash
python -m model.data_cleaning
```

This produces `model/data/cleaned_dataset.csv`.

### 3. Train the Model

```bash
python -m model.train
```

Trains an XGBoost regressor with preprocessing (StandardScaler for numeric features, OneHotEncoder for categorical features, plus engineered features like `surface_per_room` and `log_surface`). Saves versioned artifacts to `model/artifacts/`:

- `model_<version>.joblib` – the full sklearn pipeline
- `contract_<version>.json` – feature names, version, and evaluation metrics

### 4. Run the API

```bash
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test the API

Send a scoring request:

```bash
curl -X POST http://127.0.0.1:8000/scoring/ \
     -H "Content-Type: application/json" \
     -d '{"address": "my_address", "surface": 100, "num_rooms": 3}'
```

### 6. Run Tests

```bash
pytest tests/
```

Parametrized tests cover valid inputs, expected scores, and invalid-input validation (422 responses).

---

## Docker

### 1. Build the Image

```bash
docker build -t scoring-api .
```

### 2. Run the Container

```bash
docker run -d --name scoring-container -p 8000:80 scoring-api
```

Maps port 8000 on your machine to port 80 inside the container.

### 3. Verify it's Working

```bash
curl -X POST http://127.0.0.1:8000/scoring/ \
     -H "Content-Type: application/json" \
     -d '{"address": "my_address", "surface": 100, "num_rooms": 3}'
```

### Useful Docker Commands

| Command | Description |
|---------|-------------|
| `docker logs scoring-container` | Check container logs |
| `docker stop scoring-container` | Stop the container |
| `docker rm scoring-container` | Remove the container |

---

## Repository Layout

```
├── app.py                  # Legacy root-level API entrypoint
├── api/
│   └── app.py              # FastAPI scoring API (uses model.score)
├── model/
│   ├── data_cleaning.py    # Merge & clean raw DVF CSVs
│   ├── train.py            # Train XGBoost pipeline, export artifacts
│   ├── score.py            # Evaluation metrics (MAE, RMSE, R², etc.)
│   ├── data/               # Raw & cleaned CSV datasets
│   └── artifacts/          # Versioned model (.joblib) & contract (.json)
├── src/
│   ├── api/main.py         # Alternative API entrypoint (used by Docker)
│   ├── scoring/predict.py  # Simple rule-based scoring function
│   └── training/train.py   # (placeholder for future training logic)
├── tests/
│   └── test_api.py         # Parametrized API tests (pytest)
├── Dockerfile              # Container definition
└── requirements.txt        # Python dependencies
```

---

## Model Details

| Aspect | Detail |
|--------|--------|
| **Algorithm** | XGBoost (`XGBRegressor`) wrapped in an sklearn `Pipeline` |
| **Features** | `surface_reelle_bati`, `nombre_pieces_principales`, `code_departement`, `type_local` |
| **Engineered** | `surface_per_room`, `log_surface` |
| **Preprocessing** | `StandardScaler` (numeric) + `OneHotEncoder` (categorical) via `ColumnTransformer` |
| **Target** | `valeur_fonciere` (property sale price in EUR) |
| **Metrics** | MAE, RMSE, MedAE, MAPE, R² |

---

## Ideas to Implement

1. **Easier** – Add more test cases; add a `/health` or `/model_info` endpoint; use the trained XGBoost model in the API instead of the rule-based scorer.
2. **Medium** – CI/CD with GitHub Actions (lint + test on push); confidence intervals (quantile regression); experiment tracking (log each training run to a CSV).
3. **Larger** – Model registry (MLflow); authentication on the API; Kubernetes deployment with readiness probes; version comparison between two deployed models.