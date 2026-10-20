# Use lightweight official Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies (leveraging Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Preserve the package boundary required by the relative imports.
COPY . ./rag/

# Expose default service port
EXPOSE 8000

# Run Uvicorn server using exec form for graceful shutdown signals
CMD ["uvicorn", "rag.server:app", "--host", "0.0.0.0", "--port", "8000"]