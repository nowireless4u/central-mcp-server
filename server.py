import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastmcp import FastMCP
from fastmcp.experimental.transforms.code_mode import CodeMode
from services.central_service import get_conn, verify_connection
from tools import sites, devices, clients, alerts, prompts, events

logger = logging.getLogger(__name__)

_INSTRUCTIONS = (Path(__file__).parent / "INSTRUCTIONS.md").read_text()


@asynccontextmanager
async def lifespan(_server: FastMCP):
    conn = None
    try:
        conn = get_conn()
        verify_connection(conn)
    except Exception as e:
        logger.warning(
            "Central connection not available at startup: %s. "
            "Tools will fail until valid credentials are provided.",
            e,
        )
    try:
        yield {"conn": conn}
    finally:
        pass  # NewCentralBase has no explicit close; placeholder for future cleanup


mcp = FastMCP(
    "Central MCP",
    lifespan=lifespan,
    instructions=_INSTRUCTIONS,
    transforms=[CodeMode()],
)

sites.register(mcp)
devices.register(mcp)
clients.register(mcp)
alerts.register(mcp)
prompts.register(mcp)
events.register(mcp)


def run():
    mcp.run()


if __name__ == "__main__":
    import os

    if os.getenv("MCP_TRANSPORT", "stdio") == "sse":
        mcp.run(transport="sse", host="0.0.0.0", port=8001)
    else:
        mcp.run()

# Test
# uv run pytest tests/ -v

# Tool Test
# python -m watchfiles --filter python "python server.py" .
