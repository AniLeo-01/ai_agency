# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy project metadata and source
COPY pyproject.toml .
COPY src/ src/

# Install dependencies into a virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir .

# Install dev dependencies (tests, linting) into the same venv
RUN pip install --no-cache-dir ".[dev]"

# --- Stage 2: Runtime ---
FROM python:3.11-slim AS runtime

# Create non-root user
RUN groupadd --gid 1000 agency && \
    useradd --uid 1000 --gid agency --create-home agency

WORKDIR /app

# Copy the virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Ensure volume-mounted source takes priority over installed package
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Copy source (needed for volume-mount override in dev, and as default in prod)
COPY src/ src/
COPY tests/ tests/
COPY pyproject.toml .

# Output directory
RUN mkdir -p /app/output && chown agency:agency /app/output

USER agency

ENTRYPOINT ["ai-agency"]
CMD ["--help"]

# --- Stage 3: Web server ---
FROM runtime AS web

EXPOSE 8000

ENTRYPOINT ["uvicorn"]
CMD ["ai_agency.web.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/src"]
