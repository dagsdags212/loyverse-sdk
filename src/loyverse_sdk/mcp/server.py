from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from loyverse_sdk import LoyverseClient
from loyverse_sdk.core.config import config
from loyverse_sdk.core.paths import resolve_db_path


@asynccontextmanager
async def lifespan(server: FastMCP):
    client = LoyverseClient()
    engine = None
    db_path = str(resolve_db_path(config.LOYVERSE_DB_PATH))
    try:
        from loyverse_sdk.analytics import AnalyticsEngine

        engine = AnalyticsEngine(db_path)
    except Exception:
        pass
    try:
        yield {"client": client, "engine": engine}
    finally:
        if engine is not None:
            engine.close()
        await client.close()


mcp = FastMCP("loyverse_mcp", lifespan=lifespan)
