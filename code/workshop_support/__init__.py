"""Shared model settings and secrets loading for the workshop."""

import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_model(role: str) -> str:
    """Return the configured model for a workshop role (WORKSHOP_<ROLE>_MODEL overrides models.json)."""
    settings = json.loads(Path(__file__).with_name("models.json").read_text())
    if role not in settings:
        raise ValueError(f"Unknown workshop model role: {role}")
    return os.environ.get(f"WORKSHOP_{role.upper()}_MODEL", settings[role]["id"])


HOSTED_BASE_URL = "https://integrate.api.nvidia.com/v1"
LOCAL_KEY_PLACEHOLDER = "local-spark"


def get_base_url() -> str:
    """Return the OpenAI-compatible endpoint every workshop model call uses.

    Local-first fork: set NVIDIA_BASE_URL (see variables.env) to the local gateway.
    The langchain-nvidia-ai-endpoints clients (ChatNVIDIA, NVIDIAEmbeddings,
    NVIDIARerank) read the same variable, so learner code needs no base_url argument.
    Unset it to go back to NVIDIA's hosted API Catalog.
    """
    return (os.environ.get("NVIDIA_BASE_URL") or HOSTED_BASE_URL).rstrip("/")


def is_local() -> bool:
    """True when model calls go to a self-hosted endpoint instead of the API Catalog."""
    return get_base_url() != HOSTED_BASE_URL


def get_api_key() -> str:
    """Return the key sent with model calls; local endpoints accept a placeholder."""
    key = os.environ.get("NVIDIA_API_KEY", "")
    if not key and is_local():
        key = LOCAL_KEY_PLACEHOLDER
        # The NVIDIA SDK clients read the key from the environment too.
        os.environ["NVIDIA_API_KEY"] = key
    return key


def get_search_backend() -> str:
    """Return "local" (bundled documents, default) or "tavily" (web search, needs a key)."""
    backend = os.environ.get("WORKSHOP_SEARCH", "local").strip().lower()
    if backend not in ("local", "tavily"):
        raise ValueError(f"WORKSHOP_SEARCH must be 'local' or 'tavily', not {backend!r}")
    return backend


# Module 2's MCP server (code/2-agentic-rag/mcp_server.py). Not 8000 (the Module 5
# backend) or 8001 (the Module 4 reward server), so they can run side by side.
LOCAL_MCP_PORT = 8002
LOCAL_MCP_URL = f"http://localhost:{LOCAL_MCP_PORT}/mcp/"


def load_secrets(project_root: str | Path | None = None) -> Path:
    """Load saved workshop settings, including key updates and clears."""
    from dotenv import load_dotenv

    path = Path(project_root or PROJECT_ROOT) / "secrets.env"
    load_dotenv(path, override=True)
    if not (os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")):
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
    get_api_key()  # fill the local placeholder key when NVIDIA_BASE_URL is local
    return path
