# ---- Stage 1: build the virtualenv with uv ----
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
WORKDIR /app

# Optional: trust an extra CA during the build only (e.g. a corporate TLS-inspecting proxy).
# Pass with: docker build --secret id=extra_ca,src=/path/to/ca.pem .
# The runtime stage below does not inherit this.
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -f /run/secrets/extra_ca ]; then cat /run/secrets/extra_ca >> /etc/ssl/certs/ca-certificates.crt; fi

# Install dependencies first (cached layer: only rebuilt when the lock file changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then install our own code
COPY src ./src
RUN uv sync --frozen --no-dev

# ---- Stage 2: small runtime image ----
FROM python:3.12-slim
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000

# Default command runs the API. The worker task overrides this command in ECS.
CMD ["uvicorn", "sdrag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
