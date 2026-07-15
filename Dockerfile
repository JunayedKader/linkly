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

# Create a system group named "appgroup" with no login shell and no
# home directory. GID is assigned automatically.
# System accounts (-r) are intended for services, not human users —
# they get a lower UID/GID and are excluded from some system tooling.
RUN groupadd -r appgroup && \
    # Create a system user named "appuser" in "appgroup".
    # -r: system account
    # -g appgroup: assign to our group
    # -s /sbin/nologin: no interactive shell — this account cannot be
    #   logged into directly, only used to run the process
    # -d /app: home directory set to /app
    # -M: do NOT create the home directory (we create it with WORKDIR)
    useradd -r -g appgroup -s /sbin/nologin -d /app -M appuser

ARG APP_DIR=/app

WORKDIR ${APP_DIR}

# Copy only the installed venv from the builder stage — not pip, not build tools.
# COPY --from=builder references the named stage above by its AS name.
COPY --from=builder /venv /venv

# Copy application source code from the local build context (your machine),
# not from the builder stage — app code was never in builder.
COPY app/ .

# Change ownership of /app and /venv to appuser so the process can
# read its own files. Without this, appuser cannot read /app/app.py
# or execute anything in /venv/bin.
RUN chown -R appuser:appgroup /app /venv


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

# Switch from root to appuser for all subsequent instructions and
# for the final running container process.
# Everything after USER runs as appuser — not root.
USER appuser

CMD ["python", "app.py"]
