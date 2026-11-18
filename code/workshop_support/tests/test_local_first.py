"""Tests for the local-first fork: endpoint settings and offline search."""

import importlib

import pytest

import workshop_support
from workshop_support import local_search


@pytest.fixture
def ws(monkeypatch):
    for name in ("NVIDIA_BASE_URL", "NVIDIA_API_KEY", "WORKSHOP_SEARCH"):
        monkeypatch.delenv(name, raising=False)
    return importlib.reload(workshop_support)


def test_hosted_by_default_without_base_url(ws):
    assert ws.get_base_url() == ws.HOSTED_BASE_URL
    assert not ws.is_local()
    assert ws.get_api_key() == ""


def test_local_base_url_fills_placeholder_key(ws, monkeypatch):
    monkeypatch.setenv("NVIDIA_BASE_URL", "http://local-gateway:8000/v1/")
    assert ws.get_base_url() == "http://local-gateway:8000/v1"
    assert ws.is_local()
    assert ws.get_api_key() == ws.LOCAL_KEY_PLACEHOLDER


def test_real_key_wins_over_placeholder(ws, monkeypatch):
    monkeypatch.setenv("NVIDIA_BASE_URL", "http://local-gateway:8000/v1")
    monkeypatch.setenv("NVIDIA_API_KEY", "lan-key")
    assert ws.get_api_key() == "lan-key"


def test_search_backend_defaults_to_local_and_rejects_typos(ws, monkeypatch):
    assert ws.get_search_backend() == "local"
    monkeypatch.setenv("WORKSHOP_SEARCH", "Tavily")
    assert ws.get_search_backend() == "tavily"
    monkeypatch.setenv("WORKSHOP_SEARCH", "google")
    with pytest.raises(ValueError):
        ws.get_search_backend()


@pytest.mark.parametrize("query, expected", [
    ("reset my password", "reset-password.md"),
    ("report a security incident", "security-incident-reporting.md"),
    ("HPC cluster access", "hpc-cluster-access.md"),
    ("join an email distribution list", "email-distribution-lists.md"),
])
def test_local_search_finds_the_matching_article(query, expected):
    results = local_search.search(query, max_results=2)["results"]
    assert results and results[0]["url"].endswith(expected)


def test_local_search_results_have_tavily_shape():
    result = local_search.search("wifi", max_results=1)["results"][0]
    assert set(result) == {"title", "url", "content", "raw_content", "score"}
    assert result["url"].startswith("file://data/it-knowledge-base/")
    assert result["score"] == 1.0


def test_local_search_handles_empty_and_unmatched_queries():
    assert local_search.search("", max_results=3)["results"] == []
    assert local_search.search("zzzqqq", max_results=3)["results"] == []


def test_data_designer_provider_follows_the_workshop_endpoint(ws, monkeypatch):
    pytest.importorskip("data_designer.config.models")
    monkeypatch.setenv("NVIDIA_BASE_URL", "http://local-gateway:8000/v1")
    [provider] = ws.data_designer_providers()
    # Same name as Data Designer's built-in provider, so ModelConfig(provider="nvidia") keeps working.
    assert provider.name == "nvidia"
    assert provider.endpoint == "http://local-gateway:8000/v1"
    assert provider.api_key == "NVIDIA_API_KEY"  # an environment variable name, resolved at call time
    import os
    assert os.environ["NVIDIA_API_KEY"] == ws.LOCAL_KEY_PLACEHOLDER
    monkeypatch.delenv("NVIDIA_BASE_URL")
    assert ws.data_designer_providers()[0].endpoint == ws.HOSTED_BASE_URL


def test_local_mcp_port_does_not_collide_with_other_module_services(ws):
    # 8000: Module 5 backend, 8001: Module 4 reward server, 2024: langgraph dev.
    assert ws.LOCAL_MCP_PORT not in (8000, 8001, 2024)
    assert ws.LOCAL_MCP_URL == f"http://localhost:{ws.LOCAL_MCP_PORT}/mcp/"


def test_search_results_tool_mimics_tavily_search_results():
    tool = local_search.make_search_results_tool(max_results=2)
    assert tool.name == "tavily_search_results_json"
    hits = tool.invoke({"query": "connect to the VPN"})
    assert 1 <= len(hits) <= 2
    assert set(hits[0]) == {"title", "url", "content", "score"}
    assert hits[0]["url"].endswith("vpn.md")
    assert tool.invoke({"query": "zzzqqq"}) == []
