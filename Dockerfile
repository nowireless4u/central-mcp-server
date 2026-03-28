FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency and build files first for layer caching
COPY pyproject.toml uv.lock README.pypi.md ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY server.py config.py models.py utils.py INSTRUCTIONS.md ./
COPY services/ ./services/
COPY tools/ ./tools/

# Install the project itself
RUN uv sync --frozen --no-dev

# Environment variables (to be provided at runtime)
ENV CENTRAL_BASE_URL=""
ENV CENTRAL_CLIENT_ID=""
ENV CENTRAL_CLIENT_SECRET=""
ENV MCP_TRANSPORT="sse"

EXPOSE 8001

# Run with SSE transport for container use (stdio doesn't work in containers)
CMD ["uv", "run", "python", "server.py"]
