FROM python:3.11-slim

WORKDIR /app

# HIPAA/SaMD: Create a non-root user for execution
RUN groupadd -r medicaluser && useradd -r -g medicaluser medicaluser

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Set ownership to non-root user
RUN chown -R medicaluser:medicaluser /app

# Switch to non-root user
USER medicaluser

# Expose port and define healthcheck
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Production run command
ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
