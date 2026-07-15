# ── Stage 1: builder ──────────────────────────────────────────────────────────
# Uses the full python image which has pip and all build tools available.
# Everything installed here stays in this stage only — it never reaches
# the final image unless we explicitly copy it.
FROM python:3.12-slim AS builder

# Build-time variable — lets you override Python path at build time if needed.
# ARG is only available during the build process, not at runtime.
# ENV is available both during build AND at runtime inside the container.
# Use ARG for build-time config, ENV for runtime config.
ARG APP_DIR=/app

WORKDIR ${APP_DIR}

# Create a virtual environment inside the builder stage.
# This isolates installed packages into a single directory (/app/venv)
# that we can copy cleanly into the runtime stage in one COPY instruction.
RUN python -m venv /venv

# Activate the venv for subsequent RUN commands by prepending it to PATH.
# Without this, pip and python commands would use the system Python,
# not the venv.
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt .

# Install dependencies into the venv — not the system Python.
# --no-cache-dir prevents pip from storing the download cache,
# keeping this layer smaller.
RUN pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
# Fresh slim image — no build tools, no pip cache, no intermediate files.
# Only what we explicitly copy from the builder stage arrives here.
FROM python:3.12-slim AS runtime

ARG APP_DIR=/app

WORKDIR ${APP_DIR}

# Copy only the installed venv from the builder stage — not pip, not build tools.
# COPY --from=builder references the named stage above by its AS name.
COPY --from=builder /venv /venv

# Copy application source code from the local build context (your machine),
# not from the builder stage — app code was never in builder.
COPY app/ .

# Make the venv's Python and installed packages the active ones at runtime.
# This mirrors what we did in the builder stage.
ENV PATH="/venv/bin:$PATH"

# Runtime env var — sets PYTHONDONTWRITEBYTECODE so Python doesn't write
# .pyc files inside the container (no benefit, just noise in the filesystem).
ENV PYTHONDONTWRITEBYTECODE=1

# Makes Python output unbuffered — logs appear in docker logs immediately
# instead of being held in a buffer until it fills up.
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "app.py"]
