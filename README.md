# DSBA MLOps – Real Estate Price Predictor

An end-to-end MLOps project for estimating French property values (`valeur_fonciere`) from DVF (Demandes de Valeurs Foncières) open data. The system covers the full lifecycle: **data cleaning**, **model training** (XGBoost), **REST API** (FastAPI), **interactive dashboard** (Streamlit), **tests**, and **Docker deployment**.

---

## Features

- **Price Estimation** – Predict property value from surface area, number of rooms, department, and property type.
- **Price Breakdown** – XGBoost feature contributions (base value, surface, location, rooms, property type).
- **Interactive Map** – Folium map centered on the selected department/city with distance indicators (car/train/bus from the department's main city).
- **Department Insights** – Average & median price per m², neighborhood score.
- **Comparable Properties** – Table of the most similar real transactions in the same department.
- **Investment Insight** – Estimated rental yield, year-over-year market growth (computed from real data), and a composite investment score.

---

## Source Data

Property transaction data from DVF:
https://app.dvf.etalab.gouv.fr/

The `data/` folder contains regional CSV extracts for five departments:

| Code | Department |
|------|------------|
| 13 | Bouches-du-Rhône |
| 31 | Haute-Garonne |
| 59 | Nord |
| 69 | Rhône |
| 75 | Paris |

The data cleaning pipeline merges, filters, and prepares them into `data/cleaned_dataset.csv`.

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
python -m src.model.data_cleaning
```

This produces `data/cleaned_dataset.csv`.

### 3. Train the Model

```bash
python -m src.model.train
```

Trains an XGBoost regressor with preprocessing (StandardScaler for numeric features, OneHotEncoder for categorical features, plus engineered features like `surface_per_room` and `log_surface`). Saves versioned artifacts to `models/`:

- `model_<version>.joblib` – the full sklearn pipeline
- `contract_<version>.json` – feature names, version, and evaluation metrics

### 4. Option 1: Run locally

#### 4.1 Run API

From the `src/` directory:

```bash
cd src
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

The API pre-loads department statistics, commune data, and the cleaned dataset at startup.

#### 4.2 Run the UI

In a separate terminal, from the `src/` directory:

```bash
cd src
streamlit run ui/app.py --server.headless true --server.port 8501
```

Open http://localhost:8501 in your browser.

### 5. Option 2: Run with docker

#### 5.1. Build & Run with Docker Compose

```bash
docker-compose up --build
```

This starts both the FastAPI backend (port 8000) and the Streamlit UI (port 8501).

#### 5.2. Access the Services
Once the logs show that the servers have started, you can access them at:
- **Streamlit UI**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend (Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Test the API

Send a scoring request:

```bash
curl -X POST http://127.0.0.1:8000/scoring/ \
     -H "Content-Type: application/json" \
     -d '{"surface_reelle_bati": 60, "nombre_pieces_principales": 3, "code_departement": "75", "type_local": "Appartement"}'
```

### 7. Run Tests

```bash
pytest tests/
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scoring/` | Predict price + breakdown + department stats |
| `GET` | `/departments/` | List available departments with map metadata |
| `GET` | `/communes/{dept}` | List communes and zipcodes for a department |
| `GET` | `/commune_coords/{dept}/{commune}` | Get average lat/lon for a commune |
| `GET` | `/zipcode_coords/{dept}/{zipcode}` | Get average lat/lon for a zipcode |
| `GET` | `/comparables/` | Find N most similar properties by surface & rooms |
| `GET` | `/investment/` | Rental yield, market growth, investment score |

---

## Repository Layout

```
├── data/                          # Raw & cleaned CSV datasets
│   ├── paris_dataset.csv
│   ├── rhone_dataset.csv
│   ├── nord_dataset.csv
│   ├── haute_garonne_dataset.csv
│   ├── bouches_du_rhone_dataset.csv
│   └── cleaned_dataset.csv
├── models/                        # Versioned model (.joblib) & contract (.json)
├── src/
│   ├── api/
│   │   ├── main.py                # FastAPI app main file
│   │   └── services.py            # FastAPI services/functions
│   │   └── routes.py              # FastAPI app with all routes (endpoints)
│   │   └── schemas.py              # FastAPI app with schemas for the endpoints
│   │   └── constants.py              # File with constant values used in API
│   ├── model/
│   │   ├── data_cleaning.py       # Merge & clean raw DVF CSVs
│   │   ├── train.py               # Train XGBoost pipeline, export artifacts
│   │   └── score.py               # Evaluation metrics (MAE, RMSE, R², etc.)
│   ├── scoring/
│   │   └── predict.py             # Scoring function with price breakdown
│   └── ui/
│       └── app.py                 # Streamlit dashboard
├── tests/
│   ├── test_api.py                # API endpoint tests
│   ├── test_data_cleaning_eda.py  # Data cleaning & EDA tests
│   └── test_model.py              # Model training & prediction tests
├── Dockerfile.api                 # Docker image for FastAPI
├── Dockerfile.ui                  # Docker image for Streamlit
├── docker-compose.yml             # Compose config for both services
├── conftest.py                    # Shared pytest fixtures
└── requirements.txt               # Python dependencies
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
| **Breakdown** | XGBoost `pred_contribs` for per-feature contribution to the prediction |

---

## UI Dashboard

The Streamlit dashboard provides a rich interactive experience:

1. **Inputs** – Select department, city (optional), surface, rooms, and property type.
2. **Map** – Interactive Folium map with the selected location. Distance indicators show travel time from the department's main city by car, train, and bus.
3. **Estimated Price** – Predicted value displayed as a prominent card.
4. **Price Breakdown** – Table showing how each feature contributes to the final estimate (base value → surface → location → rooms → property type → total).
5. **Department Insights** – Average/median price per m², neighborhood score on a 1–10 scale.
6. **Comparable Properties** – Table of the 5 most similar real transactions with price, surface, rooms, €/m², and difference vs. the estimate.
7. **Investment Insight** – Estimated gross rental yield (+ monthly rent), year-over-year market growth from real transaction data, and a composite investment score (0–10).