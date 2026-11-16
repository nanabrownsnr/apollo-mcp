"""Apollo MCP server entry point."""

from app.config import settings
from app.tools.apollo import register_apollo_tools
from fastmcp import FastMCP

# Create FastMCP server
mcp = FastMCP(
    title="Apollo.io - B2B Prospecting & Enrichment",
    description="Single API key setup for Apollo.io. Provides company/people search and lead enrichment.",
    version="0.1.0",
)

# Register Apollo tools
register_apollo_tools(mcp)

# Optional: Health check
@mcp.tool(name="apollo_health")
async def apollo_health() -> dict:
    """Check Apollo API key validity."""
    try:
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": settings.APOLLO_API_KEY,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.apollo.io/v1/people",
                headers=headers,
                params={"limit": 1},
            )
            if response.status_code == 200:
                return {"status": "ok", "api_key_valid": True}
            else:
                return {"status": "error", "api_key_valid": False, "error": response.text}
    except Exception as e:
        return {"status": "error", "api_key_valid": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
