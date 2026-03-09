FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code ONLY
COPY src/ ./src/

# Set PYTHONPATH to include src
ENV PYTHONPATH="/app/src"

# Run the API
# FastAPI will automatically find the app in src/api/main.py
CMD ["fastapi", "run", "src/api/main.py", "--port", "80"]