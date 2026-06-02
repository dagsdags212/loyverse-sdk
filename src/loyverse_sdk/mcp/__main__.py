import loyverse_sdk.mcp.tools  # noqa: F401 — registers @mcp.tool decorators at import time

from loyverse_sdk.mcp.server import mcp


def main():
    mcp.run()


if __name__ == "__main__":
    main()
