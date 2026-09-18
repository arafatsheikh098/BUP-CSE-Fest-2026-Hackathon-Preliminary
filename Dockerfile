FROM python:3.11-slim

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install CBC solver for PuLP Linear Programming optimization
RUN apt-get update && apt-get install -y --no-install-recommends \
    coinor-cbc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose default port (binds to 0.0.0.0, respects $PORT)
EXPOSE 8000

# Run FastAPI app with dynamic port binding
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
