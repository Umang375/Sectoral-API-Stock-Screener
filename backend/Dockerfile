# 1. Base Image: Use Python 3.12 slim variant for minimal disk size and attack surface
FROM python:3.12-slim

# 2. Environment Configuration: Prevent bytecode compilation and buffer buffering for instant logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 3. System Dependencies: Install minimal C-compilers and PostgreSQL driver libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Working Directory: Define the container root directory for app execution
WORKDIR /app

# 5. Dependency Caching Layer: Copy requirements FIRST to speed up future container builds
COPY requirements.txt .

# 6. Python Packages: Install dependencies without storing pip cache to keep image small
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. Security Hardening: Create a dedicated non-root user to run the app securely
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 8. Source Code Ingestion: Copy the remaining backend Python project files
COPY --chown=appuser:appuser . .

# 9. Network Port Documentation: Inform Docker that traffic arrives on port 8000
EXPOSE 8000

# 10. Startup Process: Launch Uvicorn ASGI server listening on all IPv4 addresses
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
