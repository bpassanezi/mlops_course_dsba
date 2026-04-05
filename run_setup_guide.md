
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

### 4. Hugging Face Setup (Data & Models)

The application automatically pulls datasets and trained model artifacts from a secure Hugging Face Bucket at runtime. To authorise the application, you need to configure your environment.

**1. Create a secret file:**
At the very root of the project (next to `docker-compose.yml`), create a file named exactly `.env`.

**2. Add your access token:**
Insert your Hugging Face Access Token *(with Read access)* into the `.env` file:
```env
HF_TOKEN=hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
*(You can get a token from: https://huggingface.co/settings/tokens)*

**How authentication behaves:**
- **Local Runs** (`uvicorn`): The API will automatically pick up your environment variables if configured, or you can globally securely authenticate your local terminal using `huggingface-cli login`.
- **Docker Runs** (`docker-compose`): Docker will automatically consume the `.env` file and seamlessly inject `HF_TOKEN` directly into the backend container!

### 5. Option A: Run Locally

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

### 6. Option B: Run with Docker

```bash
docker-compose up --build
```

Starts both services:
- **Streamlit UI**: [http://localhost:8501](http://localhost:8501)
- **FastAPI (interactive docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 7. Run Tests

```bash
pytest tests/
```
