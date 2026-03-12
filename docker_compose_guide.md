# 🐳 Docker Compose Deployment Guide

This project uses **Docker Compose** to orchestrate the FastAPI backend and the Streamlit UI. This setup ensures that both services can communicate with each other seamlessly.

---

## 🚀 Quick Start (Recommended)

The easiest way to get everything running is using a single command. Docker Compose will automatically build both images and link them together.

### 1. Build and Start
Run this from the project root:
```bash
docker-compose up --build
```

### 2. Access the Services
Once the logs show that the servers have started, you can access them at:
- **Streamlit UI**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend (Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠 Useful Commands

### Running in Background
If you want to run the containers without locking your terminal:
```bash
docker-compose up -d --build
```

### Checking Status
To see which containers are running and their ports:
```bash
docker-compose ps
```

### Viewing Logs
If running in the background, you can follow the logs of both services:
```bash
docker-compose logs -f
```

### Stopping the Services
To stop and remove the containers:
```bash
docker-compose down
```

---

## 📁 Project Architecture

- **`Dockerfile.api`**: Instructions for the FastAPI backend.
- **[Dockerfile.ui](file:///Users/bpassanezi/Documents/Masters/T2/mlops_course_dsba/Dockerfile.ui)**: Instructions for the Streamlit frontend.
- **[docker-compose.yml](file:///Users/bpassanezi/Documents/Masters/T2/mlops_course_dsba/docker-compose.yml)**: The orchestration file that defines:
    - Networking (UI talks to Backend via `http://backend`)
    - Volumes (Mounts the `models/` folder to the containers)
    - Port mapping (`8000` for API, `8501` for UI)

---

## ⚠️ Troubleshooting

1. **Docker Daemon Error**: If you see `Cannot connect to the Docker daemon`, make sure **Docker Desktop** is open and running on your Mac.
2. **Connection Refused in UI**: If the UI says it can't connect to the API, ensure the `backend` service is fully started. The UI is configured to look for `http://backend/scoring/` inside the Docker network.
3. **Model Not Found**: Ensure you have run the training script (`python src/model/train.py`) at least once so the `models/` folder contains the necessary [.joblib](file:///Users/bpassanezi/Documents/Masters/T2/mlops_course_dsba/model/artifacts/model_20260310140216.joblib) and [.json](file:///Users/bpassanezi/Documents/Masters/T2/mlops_course_dsba/model/artifacts/contract_20260310141431.json) artifacts.
