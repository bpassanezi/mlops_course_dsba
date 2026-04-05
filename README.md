# ImmoPrice - French Property Valuation & Market Intelligence

![home_screen](./images/home_screen.png)

> ImmoPrice is a production-ready API and web interface that helps you accurately price real estate, understand what drives a property's value, and spot the best investment opportunities, all powered by machine learning and tens of thousands of real French property transactions.

---

## Why ImmoPrice?

Pricing a property accurately is one of the most complex tasks in real estate. Overpricing leads to stagnant listings; underpricing leaves money on the table. ImmoPrice addresses this by:

- **Providing an objective, data-driven price estimate** rather than relying on gut feeling or manual comparisons.
- **Explaining *why* a property is estimated at a given price**, breaking down each factor's monetary contribution (surface, location, rooms, property type).
- **Benchmarking against real market data** — average prices, comparable recent sales, and historical growth trends.
- **Rating neighbourhood desirability** with our proprietary **Desirability Index**, a 1-to-10 score that instantly tells you whether a location commands a premium or sits below the market average.
- **Delivering an investment score** that synthesises rental yield, market momentum, and relative affordability into a single actionable number.

---

## Price Estimate

![home_screen](./images/price_valuation.png)

Enter a property's key characteristics and ImmoPrice returns an estimated price along with a full breakdown of what drives that number.

The inputs used are:

| Input | Description |
|---|---|
| Surface area (m²) | Built surface area of the property |
| Number of rooms | Count of main rooms |
| Department | French department code (`13`, `31`, `59`, `69`, `75`) |
| Property type | Apartment or House |

Each estimate comes with a **transparent breakdown** showing exactly how much each factor contributes to the final price — so you can see, in euros, the impact of location, surface area, number of rooms, and property type.

### How the Estimate is Calculated

Under the hood, the estimate is produced by a machine-learning model trained on tens of thousands of real property transactions across five French departments. The model learns patterns in the relationship between a property's characteristics and its sale price, then applies those patterns to new properties. For full technical details on the model architecture, preprocessing, and hyperparameters, see the [Technical Annex](#technical-annex).

### Price Breakdown

For every prediction, the model decomposes the estimated price into intuitive components:

| Component | What it represents |
|---|---|
| **Base value** | The market-wide average price — the starting point before any property-specific adjustments |
| **Surface** | The EUR added (or removed) because of the property's built surface area |
| **Location** | The EUR premium or discount driven by the department |
| **Rooms** | The EUR adjustment attributed to the number of rooms |
| **Property type** | The EUR delta between an apartment and a house in that market |

This turns the estimate into a transparent, auditable valuation. You can use it to justify a price to a client, identify which factors are inflating or deflating a value, or compare two properties on equal footing.

---

## Market Comparison

![market_comparison](./images/market_comparison.png)

ImmoPrice also surfaces the most similar recently sold properties in the same department. This lets you compare the estimated price against actual sale prices of comparable properties — the industry standard for validating any valuation.

Comparables are matched by surface area, number of rooms, and (where possible) property type, and ranked by similarity. Presenting real transaction prices alongside the model's estimate provides a concrete market sanity check that builds trust.

### Market Context

For every department, ImmoPrice provides **average and median price per m²**, computed from the full population of recorded transactions. Placing a specific property's estimated €/m² next to these benchmarks gives you an immediate sense of whether you're looking at a market-rate deal, a premium property, or a potential bargain.

### Desirability Index

The **Desirability Index** is ImmoPrice's proprietary location quality score — a **single number from 1 to 10** that answers the question: *"Is this a sought-after area, or a more affordable one?"*

It compares the property's implied price per m² against the department-wide average and maps the result to an intuitive scale centred on 5 (market average):

| Score | Label | What it means |
|---|---|---|
| 8 – 10 | **Premium Area** | Consistently high demand; prices well above the departmental norm |
| 6 – 7 | **Desirable** | Above-average neighbourhood with strong market activity |
| 4 – 5 | **Standard** | In line with the typical market; solid but undifferentiated |
| 1 – 3 | **Below Market** | Prices sit below the area average; may signal lower demand or an affordability opportunity |

The Desirability Index gives a buyer or agent an at-a-glance signal of neighbourhood quality without requiring local knowledge. Use it to justify a premium asking price in a high-scoring area, or to flag to a buyer that they are entering a lower-demand zone with room to negotiate.

---

## Investment Opportunities

![investment](./images/investment.png)

Beyond valuation, ImmoPrice evaluates the **investment attractiveness** of any property. Given the estimated price and surface area, the API returns:

### Rental Yield

The **gross annual rental yield** as a percentage of the property value, calibrated per department:

| Department | City | Yield |
|---|---|---|
| 75 | Paris | 3.2% |
| 69 | Lyon | 4.1% |
| 31 | Toulouse | 4.6% |
| 13 | Marseille | 5.3% |
| 59 | Lille | 5.8% |

> Higher yields in cities like Lille and Marseille reflect lower purchase prices relative to achievable rents. Paris's lower yield reflects elevated property prices despite strong rental demand.

### Market Growth

The **year-over-year change in median price per m²**, computed from actual transaction data. A positive value indicates a rising market; a negative value indicates a correction.

### Investment Score

A **composite score from 0 to 10** that brings together the three most important investment dimensions:

| Component | Weight | What it captures |
|---|---|---|
| **Yield** | 40% | Higher rental yield → higher score |
| **Growth** | 40% | Stronger market growth → higher score |
| **Affordability** | 20% | Properties priced below the department average score higher |

The investment score lets you quickly rank and compare properties or markets, focusing your attention where the opportunity is greatest.

---

## Data Sources

All market statistics (averages, growth rates, comparables) are derived from **DVF (Demandes de Valeurs Foncières)**, the official French government dataset of property transactions, available at [app.dvf.etalab.gouv.fr](https://app.dvf.etalab.gouv.fr/). Because they are computed directly from recorded sales, they reflect actual market activity rather than survey-based estimates.

The API currently covers five departments:

| Code | Department | Main City |
|---|---|---|
| `13` | Bouches-du-Rhône | Marseille |
| `31` | Haute-Garonne | Toulouse |
| `59` | Nord | Lille |
| `69` | Rhône | Lyon |
| `75` | Paris | Paris |

---

## How to Run

### Prerequisites

- Python 3.9+
- pip

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare the Data

```bash
python -m src.model.data_cleaning
```

Merges the raw regional CSVs into `data/cleaned_dataset.csv`.

### 3. Train the Model

```bash
python -m src.model.train
```

Trains the model and saves versioned artifacts to `models/`:
- `model_<version>.joblib` — the trained pipeline
- `contract_<version>.json` — feature schema, version tag, and evaluation metrics

### 4. Option A: Run Locally

**Start the API** (from `src/`):
```bash
cd src
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Start the UI** (in a separate terminal, from `src/`):
```bash
cd src
streamlit run ui/app.py --server.headless true --server.port 8501
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### 5. Option B: Run with Docker

```bash
docker-compose up --build
```

Starts both services:
- **Streamlit UI**: [http://localhost:8501](http://localhost:8501)
- **FastAPI (interactive docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Run Tests

```bash
pytest tests/
```

---

## Model Versioning & Upgrade Strategy

ImmoPrice follows a simple but disciplined versioning strategy designed to keep the model traceable and the serving layer reliable.

### How Versions Work

Every training run produces a **timestamped pair** of artefacts in the `models/` directory:

| File | Content |
|---|---|
| `model_<version>.joblib` | The full serialised pipeline (preprocessing + regressor) |
| `contract_<version>.json` | Feature list, dataset size, train/test metrics, and version tag |

The version tag is a UTC timestamp (`YYYYMMDDHHMMSS`), so artefacts are naturally sorted chronologically. At startup, the API automatically loads the **latest** pair (highest timestamp), requiring no manual configuration or environment variable.

### Retraining Workflow

To produce a new model version:

```bash
# 1. Refresh & clean the data
python -m src.model.data_cleaning

# 2. Train — a new timestamped model + contract are created automatically
python -m src.model.train

# 3. Restart the API to pick up the new version
```

Previous versions remain in `models/` and can be restored by simply removing the newer files, or by adjusting the loading logic to target a specific version.

### Model Contract

The contract file (`contract_<version>.json`) acts as a lightweight model registry entry. It records:

- **Feature schema** the exact list of input features the model expects, split by type (numeric, categorical, engineered).
- **Dataset dimensions** number of train and test rows, for reproducibility tracking.
- **Evaluation metrics** full train and test metrics (MAE, RMSE, MedAE, MAPE, R²), enabling comparison across versions.

This makes it straightforward to audit any deployed model: you can check which features it uses, how much data it saw, and how it performed before going live.

### Rollback

Because all previous artefacts are retained, rolling back is as simple as deleting the latest files (or renaming them). The API will automatically pick up the next most recent pair on restart.

### Future Improvements

- **Automated performance gating** compare new model metrics against a baseline before promoting to production.
- **A/B serving** serve two model versions simultaneously and route a fraction of traffic to the challenger.
- **Scheduled retraining** trigger `data_cleaning` + `train` on a cron schedule as new DVF data is published.
- **Remote artefact storage** move model files to a cloud object store (S3, GCS) with a model registry (MLflow, Weights & Biases) for team-wide traceability.

---

## Model Performance

Evaluation metrics for each trained model are stored in `models/contract_<version>.json`. To interpret the metrics in those files:

| Metric | Description |
|---|---|
| **MAE** | Mean Absolute Error — average EUR difference between predicted and actual price |
| **RMSE** | Root Mean Square Error — penalises large errors more heavily than MAE |
| **MedAE** | Median Absolute Error — robust measure unaffected by outlier transactions |
| **MAPE** | Mean Absolute Percentage Error — relative accuracy across different price ranges |
| **R²** | Coefficient of determination — proportion of price variance explained by the model |

---

## Technical Annex

This annex provides full technical details on the modelling pipeline, scoring methodology, and algorithm internals. It is intended for data scientists, engineers, or reviewers who want to understand or audit the system at a deeper level.

---

### A1. Model Architecture

The predictive model is an **XGBoost** gradient-boosted tree regressor (`XGBRegressor`) wrapped in a scikit-learn `Pipeline`. The pipeline chains a preprocessing stage with the regressor so that feature transformation and prediction happen in a single, serialisable object.

#### Preprocessing

The `ColumnTransformer` applies different transformations depending on feature type:

| Feature group | Features | Transformer |
|---|---|---|
| **Numeric** | `surface_reelle_bati`, `nombre_pieces_principales`, `surface_per_room`, `log_surface` | `StandardScaler` (zero-mean, unit-variance) |
| **Categorical** | `code_departement`, `type_local` | `OneHotEncoder` (`handle_unknown="ignore"`, dense output) |

#### Feature Engineering

Two features are derived before the data enters the pipeline:

| Feature | Formula | Rationale |
|---|---|---|
| `surface_per_room` | `surface_reelle_bati / nombre_pieces_principales` | Captures room density: a 100 m² flat with 2 rooms signals a different market segment than one with 5 rooms |
| `log_surface` | `ln(1 + surface_reelle_bati)` | Compresses the wide distribution of surface areas, reducing the influence of very large properties and improving tree split efficiency |

#### XGBoost Hyperparameters

| Parameter | Value | Purpose |
|---|---|---|
| `n_estimators` | 1 000 | Number of boosting rounds |
| `max_depth` | 8 | Maximum tree depth — controls model complexity |
| `learning_rate` | 0.03 | Shrinkage per step — lower values reduce overfitting at the cost of more rounds |
| `subsample` | 0.8 | Row sampling ratio per tree — adds stochastic regularisation |
| `colsample_bytree` | 0.8 | Feature sampling ratio per tree |
| `min_child_weight` | 5 | Minimum sum of instance weights in a leaf — prevents overly specific splits |
| `reg_alpha` | 1.0 | L1 regularisation on leaf weights |
| `reg_lambda` | 5.0 | L2 regularisation on leaf weights |
| `random_state` | 42 | Ensures reproducibility |

#### Training Process

1. The cleaned dataset is loaded and filtered (transactions below €10 000 are excluded as non-representative).
2. Engineered features are computed.
3. An 80/20 train/test split is performed (`random_state=42`).
4. The pipeline is fit on the training set.
5. Metrics are computed on both splits and saved alongside the model.

#### Artefact Versioning

Each training run produces two versioned files (timestamp format `YYYYMMDDHHMMSS`):

- `model_<version>.joblib` — the full sklearn `Pipeline` (preprocessor + regressor), loadable with `joblib.load`.
- `contract_<version>.json` — a contract file containing the feature list, version tag, and all train/test evaluation metrics.

At serving time, the API always loads the **latest** artefact pair (sorted lexicographically by filename).

---

### A2. Price Breakdown — Prediction Contributions

The price breakdown uses XGBoost's native **`pred_contribs`** mode. For a single input row, the booster returns an array of shape `(1, n_features + 1)` where:

- Each of the first `n_features` values is the **SHAP-style additive contribution** of that transformed feature to the prediction.
- The last value is the **bias** (base value), which equals the average prediction across the training set.

The sum of all contributions plus the bias exactly equals the final prediction.

#### Grouping Logic

The raw per-feature contributions (which operate on one-hot-encoded and scaled features) are aggregated into five user-facing groups:

| Group | Contributing transformed features |
|---|---|
| `base_value` | Bias term (last element of `pred_contribs`) |
| `surface` | `num__surface_reelle_bati` + `num__surface_per_room` + `num__log_surface` |
| `location` | All `cat__code_departement_*` columns |
| `rooms` | `num__nombre_pieces_principales` |
| `property_type` | All `cat__type_local_*` columns |

---

### A3. Comparable Selection Algorithm

Given a query property $(s_q, r_q)$ (surface, rooms), the algorithm computes a normalised Euclidean distance to every transaction $(s_i, r_i)$ in the same department:

$$d_i = \left(\frac{s_q - s_i}{s_q}\right)^2 + \left(\frac{r_q - r_i}{r_q}\right)^2$$

Normalisation by the query values ensures that surface and room differences are weighted proportionally regardless of their absolute magnitudes.

**Type filtering:** if at least $N$ transactions share the same `type_local` as the query, only those are considered. Otherwise, the full department dataset is used.

The $N$ transactions with the smallest $d_i$ are returned.

---

### A4. Department Statistics

At API startup, the following are computed from `cleaned_dataset.csv`:

| Statistic | Computation |
|---|---|
| **Average price / m²** | `mean(valeur_fonciere / surface_reelle_bati)` per department |
| **Median price / m²** | `median(valeur_fonciere / surface_reelle_bati)` per department |
| **Transaction count** | Number of valid rows (surface > 0, price > 0) per department |

These are stored in memory and served by the `/departments/` and `/scoring/` endpoints.

---

### A5. Desirability Index — Detailed Calculation

1. Compute the property's implied price per m²:
$$\text{pred\_pm2} = \frac{\text{prediction}}{\text{surface\_reelle\_bati}}$$
2. Compute the ratio to the department average:
$$\text{ratio} = \frac{\text{pred\_pm2}}{\text{dept\_avg\_pm2}}$$
3. Map to a 1–10 scale centred on 5:
$$\text{raw\_score} = 5 + (\text{ratio} - 1) \times 3$$
$$\text{desirability\_index} = \text{clamp}(\text{raw\_score},\ 1,\ 10)$$

A ratio of 1.0 (exactly average) yields **5**. Each 0.33 above or below average shifts the score by ±1 point.

---

### A6. Investment Score — Detailed Calculation

The investment score is a weighted composite of three sub-scores, each scaled 0–10:

#### Yield Score (40%)

$$\text{yield\_score} = \min\!\left(10,\ \max\!\left(0,\ \frac{\text{rental\_yield} - 1}{0.7}\right)\right)$$

Calibrated so that a 1% yield maps to 0 and an 8% yield maps to 10.

#### Growth Score (40%)

$$\text{growth\_score} = \min\!\left(10,\ \max\!\left(0,\ \frac{\text{market\_growth} + 5}{1.5}\right)\right)$$

Calibrated so that −5% YoY growth maps to 0 and +10% maps to 10.

#### Affordability Score (20%)

$$\text{afford\_score} = \min\!\left(10,\ \max\!\left(0,\ (2 - \text{ratio}) \times 10\right)\right)$$

where $\text{ratio} = \text{pred\_pm2} / \text{dept\_avg\_pm2}$. A property at half the average price scores 10; one at double the average scores 0.

#### Final Score

$$\text{investment\_score} = \text{yield\_score} \times 0.4 + \text{growth\_score} \times 0.4 + \text{afford\_score} \times 0.2$$

Clamped to $[0,\ 10]$ and rounded to one decimal.

---

### A7. Market Growth Calculation

For each department, the year-over-year growth is computed from the raw CSV:

1. Parse `date_mutation` and extract the year.
2. Compute `price_per_m2 = valeur_fonciere / surface_reelle_bati` for every valid transaction.
3. Group by year and compute the **median** price per m².
4. Take the two most recent complete years and compute:

$$\text{market\_growth (\%)} = \frac{\text{median\_last\_year} - \text{median\_prior\_year}}{\text{median\_prior\_year}} \times 100$$

The median is used rather than the mean to reduce sensitivity to extreme luxury or distressed sales.

---

### A8. Rental Yield Assumptions

Gross rental yields are hard-coded per department based on typical market rates:

| Department | City | Gross Yield | Source rationale |
|---|---|---|---|
| `75` | Paris | 3.2% | High absolute prices depress yield despite strong rental demand |
| `69` | Lyon | 4.1% | Second-tier city with solid demand and moderate prices |
| `31` | Toulouse | 4.6% | Growing tech hub with favourable rent-to-price ratio |
| `13` | Marseille | 5.3% | Lower purchase prices relative to rental income |
| `59` | Lille | 5.8% | Most affordable market covered; highest relative yields |

These are static values. A future improvement would be to compute them dynamically from rental market data.

---

### A9. Evaluation Metrics — Formulas

| Metric | Formula |
|---|---|
| **MAE** | $\frac{1}{n}\sum_{i=1}^{n}\lvert y_i - \hat{y}_i \rvert$ |
| **RMSE** | $\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}$ |
| **MedAE** | $\text{median}(\lvert y_i - \hat{y}_i \rvert)$ |
| **MAPE** | $\frac{100}{n}\sum_{i=1}^{n}\frac{\lvert y_i - \hat{y}_i \rvert}{\lvert y_i \rvert}$ |
| **R²** | $1 - \frac{\sum(y_i - \hat{y}_i)^2}{\sum(y_i - \bar{y})^2}$ |

Metrics are computed on both train and test splits. The contract JSON stores them with `train_` and `test_` prefixes respectively.