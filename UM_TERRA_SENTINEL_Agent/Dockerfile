# ────────────────────────────────────────────────────────────────────
#  UM_TERRA_SENTINEL Agent — Docker Container Definition
#  © 2026 Utsav Mukherjee <utsavmukherjee143@gmail.com>. All rights reserved.
#
#  Secure, minimal Red Hat UBI9 Python 3.11 base image.
#  Non-root execution. No secrets baked in.
# ────────────────────────────────────────────────────────────────────

FROM registry.redhat.io/ubi9/python-311-minimal:latest

# Install git (required for submodule initialisation)
USER root
RUN microdnf install -y git && microdnf clean all

# Create non-root application user
RUN useradd -m -u 1001 appuser

WORKDIR /app

# Copy submodule config first (needed for git submodule update)
COPY .gitmodules ./

# Copy application source
COPY requirements.txt ./
COPY config.py main.py um_terra_sentinel_agent.py a2a_factory.py tools.py test_client.py ./

# Copy the aicoe-agent-utils submodule
COPY aicoe-agent-utils/ ./aicoe-agent-utils/

# Initialise submodules if needed (handles cases where git clone was shallow)
RUN git init && git submodule update --init --recursive || true

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Transfer ownership to non-root user
RUN chown -R appuser:appuser /app

USER 1001

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/.well-known/agent.json', timeout=5).raise_for_status()"

CMD ["python", "main.py"]
