"""A small MCP server that exposes one search tool to any MCP client.

Local-first fork: with WORKSHOP_SEARCH=local (the default in variables.env) the tool
searches the bundled IT knowledge base (data/it-knowledge-base) with keyword (BM25)
ranking - no key and no internet. With WORKSHOP_SEARCH=tavily it wraps Tavily web
search, as in the original workshop, and needs TAVILY_API_KEY.

The tool keeps the name `tavily_search` and the same input ({"query": ...}) in both
modes, so the agent code and the exercise answers are the same either way.

Run it from code/2-agentic-rag:

    uvicorn mcp_server:app --port 8002

It serves two MCP transports on the same port:
  - Streamable HTTP at /mcp/  (what PART 2A of rag_agent.py connects to)
  - SSE at /sse               (the optional PART 2B example)
and a plain /health route for Workshop Health.
"""

import contextlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workshop_support import get_search_backend, load_secrets
load_secrets()
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import mcp.types as types

SEARCH_BACKEND = get_search_backend()
TOOL_NAME = "tavily_search"  # same name in both modes; see the module docstring
MAX_RESULTS = 5

# 1. Initialize Server Logic
mcp_server = Server("workshop-search")

if SEARCH_BACKEND == "tavily":
    if not os.environ.get("TAVILY_API_KEY"):
        raise ValueError("TAVILY_API_KEY environment variable is required when WORKSHOP_SEARCH=tavily")
    from tavily import TavilyClient

    tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    TOOL_DESCRIPTION = "Search the web for current information"
else:
    from workshop_support import local_search

    tavily = None
    TOOL_DESCRIPTION = ("Keyword search over the company's offline document collection "
                        "(local, no internet). Returns titles, file:// URLs and excerpts.")


def run_search(query: str) -> dict:
    """Return a Tavily-shaped {"results": [...]} dict from the configured backend."""
    if SEARCH_BACKEND == "tavily":
        return tavily.search(query=query, max_results=MAX_RESULTS, search_depth="advanced")
    return local_search.search(query, max_results=MAX_RESULTS)


# 2. Define Tools
@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name=TOOL_NAME,
            description=TOOL_DESCRIPTION,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != TOOL_NAME:
        raise ValueError(f"Unknown tool: {name}")

    try:
        query = arguments.get("query")
        # Added print for debugging so you can see it working in the server terminal
        print(f"Executing search for: {query}")

        response = run_search(query)

        formatted_results = []
        for r in response.get("results", []):
            formatted_results.append(
                f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}"
            )

        if not formatted_results:
            return [types.TextContent(type="text", text="No results found.")]
        return [types.TextContent(type="text", text="\n---\n".join(formatted_results))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

# 3. Set up the transports with Starlette
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request):
    """Handle the initial connection handshake."""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )
    # The SSE transport already sent the response; Starlette still needs an
    # endpoint return value, or it logs a TypeError after every session.
    return Response()


# Streamable HTTP: the transport hosted servers such as Tavily's use.
session_manager = StreamableHTTPSessionManager(app=mcp_server, stateless=True)


async def handle_streamable_http(scope, receive, send):
    await session_manager.handle_request(scope, receive, send)


async def health(request: Request):
    return JSONResponse({"status": "ok", "backend": SEARCH_BACKEND, "tool": TOOL_NAME})


@contextlib.asynccontextmanager
async def lifespan(app):
    async with session_manager.run():
        yield


app = Starlette(
    routes=[
        Route("/health", endpoint=health),
        Mount("/mcp", app=handle_streamable_http),
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message), # Use Mount, not Route
    ],
    lifespan=lifespan,
)
