FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI
RUN npm install -g @anthropic-ai/claude-code

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install rlm-toolkit (separate layer for caching)
RUN pip install --no-cache-dir "rlm-toolkit[all]"

# -------- Final image --------
FROM python:3.12-slim

WORKDIR /app

# Copy node, npm from builder (apt-installed)
COPY --from=builder /usr/bin/node /usr/bin/node
COPY --from=builder /usr/bin/npm /usr/bin/npm

# Copy npm global packages (claude CLI installed via npm install -g)
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules

# Copy Python packages from builder (includes uvicorn, mcp, etc.)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY jefest/ ./jefest/
COPY templates/ ./templates/
COPY skills/ ./skills/
COPY supervisord.conf ./supervisord.conf
COPY entrypoint.sh ./entrypoint.sh
COPY VERSION ./VERSION

RUN sed -i 's/\r$//' ./entrypoint.sh && chmod +x ./entrypoint.sh

# Create required directories
RUN mkdir -p /data /workspace

VOLUME ["/data", "/workspace"]

EXPOSE 8300

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8300/health', timeout=3).raise_for_status()" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
