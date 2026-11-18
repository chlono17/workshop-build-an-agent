"""The local MCP server (mcp_server.py) lists and runs its search tool over both transports.

Local-first fork: with WORKSHOP_SEARCH=local the server needs no key and no internet,
so these tests start it for real on a free port and talk to it as rag_agent.py does.
"""

import asyncio
import importlib
import os
from pathlib import Path
import socket
import sys
import threading
import time
import urllib.request

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

uvicorn = pytest.importorskip("uvicorn")
pytest.importorskip("langchain_mcp_adapters.client")


def load_server(monkeypatch, backend="local", key=None):
    monkeypatch.setenv("WORKSHOP_SEARCH", backend)
    if key is None:
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    else:
        monkeypatch.setenv("TAVILY_API_KEY", key)
    # load_secrets() would re-read secrets.env; keep the test's environment.
    import workshop_support
    monkeypatch.setattr(workshop_support, "load_secrets", lambda *a, **k: None)
    sys.modules.pop("mcp_server", None)
    return importlib.import_module("mcp_server")


@pytest.fixture
def server(monkeypatch):
    module = load_server(monkeypatch)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    config = uvicorn.Config(module.app, host="127.0.0.1", port=port, log_level="warning")
    instance = uvicorn.Server(config)
    thread = threading.Thread(target=instance.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not instance.started:
        if time.time() > deadline:
            raise RuntimeError("MCP server did not start")
        time.sleep(0.05)
    yield module, f"http://127.0.0.1:{port}"
    instance.should_exit = True
    thread.join(timeout=10)


def test_local_mode_needs_no_tavily_key(monkeypatch):
    module = load_server(monkeypatch)
    assert module.SEARCH_BACKEND == "local"
    assert module.tavily is None


def test_tavily_mode_still_requires_its_key(monkeypatch):
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        load_server(monkeypatch, backend="tavily")


def test_handlers_list_and_call_the_search_tool(monkeypatch):
    module = load_server(monkeypatch)
    tools = asyncio.run(module.list_tools())
    assert [t.name for t in tools] == ["tavily_search"]
    assert tools[0].inputSchema["required"] == ["query"]
    text = asyncio.run(module.call_tool("tavily_search", {"query": "connect to VPN"}))[0].text
    assert "URL: file://data/it-knowledge-base/vpn.md" in text.split("---")[0]
    assert asyncio.run(module.call_tool("tavily_search", {"query": "zzzqqq"}))[0].text == "No results found."
    with pytest.raises(ValueError):
        asyncio.run(module.call_tool("other_tool", {}))


def test_health_route_reports_backend(server):
    _, base = server
    with urllib.request.urlopen(f"{base}/health", timeout=5) as response:
        assert b'"backend":"local"' in response.read()


@pytest.mark.parametrize("transport, path", [("streamable_http", "/mcp/"), ("sse", "/sse")])
def test_mcp_client_lists_and_calls_the_tool(server, transport, path):
    """Same calls rag_agent.py's web_search makes, over each transport."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    _, base = server

    async def run():
        connection = {"transport": transport, "url": base + path}
        if transport == "streamable_http":
            connection["headers"] = {}  # as MCP_HEADERS is in local mode
        client = MultiServerMCPClient({"tavily": connection})
        async with client.session("tavily") as session:
            listed = await session.list_tools()
            result = await session.call_tool("tavily_search", {"query": "reset my password"})
        return [t.name for t in listed.tools], result.content[0].text

    names, text = asyncio.run(run())
    assert names == ["tavily_search"]
    assert "reset-password.md" in text.split("---")[0]
