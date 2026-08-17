# ---------------------------------------------------------------------------
# Willovate AI Automation Engine — Dockerfile
# ---------------------------------------------------------------------------
# Builds a production-ready image that serves the FastAPI pipeline via
# Uvicorn on port 8000.
#
# Build:  docker build -t willovate-ai .
# Run:    docker run -p 8000:8000 willovate-ai
# ---------------------------------------------------------------------------

FROM python:3.11-slim

# Metadata
LABEL maintainer="Willovate"
LABEL description="Willovate AI Automation Engine API"

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory inside the container
WORKDIR /app

# ---------------------------------------------------------------------------
# System dependencies (for Playwright if browser automation is needed)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Application code
# ---------------------------------------------------------------------------
COPY . .

# Create output directory (evaluation reports, generated JSONs)
RUN mkdir -p outputs

# ---------------------------------------------------------------------------
# Expose API port
# ---------------------------------------------------------------------------
EXPOSE 8000

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# ---------------------------------------------------------------------------
# Start the API server
# ---------------------------------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
