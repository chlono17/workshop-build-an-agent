"""One OpenAI/NIM-compatible URL in front of the local models on a DGX Spark.

The workshop's clients (ChatNVIDIA, NVIDIAEmbeddings, NVIDIARerank, ChatOpenAI)
all read NVIDIA_BASE_URL. This gateway lets that single URL serve every role:

  /v1/chat/completions, /v1/completions -> the chat model (NVIDIA Sync Model Launcher, 27B)
  /v1/embeddings                         -> the local embedding server
  /v1/ranking  (NIM reranking format)    -> translated to the local reranker's /rerank
  /v1/models                             -> union of the upstream model lists

Settings come from environment variables (see compose.yaml):
  CHAT_URL, SPARK_LLM_API_KEY (or CHAT_API_KEY), EMBED_URL, RERANK_URL
"""

import json
import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

CHAT_URL = os.environ.get("CHAT_URL", "http://host.docker.internal:18765/v1").rstrip("/")
# Model Launcher LAN-mode key, saved in secrets.env (loaded through compose env_file).
CHAT_API_KEY = os.environ.get("CHAT_API_KEY") or os.environ.get("SPARK_LLM_API_KEY", "")
EMBED_URL = os.environ.get("EMBED_URL", "http://local-embed:8000/v1").rstrip("/")
RERANK_URL = os.environ.get("RERANK_URL", "http://local-rerank:8000/v1").rstrip("/")
# Fields the NVIDIA embedding API accepts but a vLLM pooling server may reject.
NVIDIA_ONLY_EMBED_FIELDS = ("input_type", "truncate")

app = FastAPI(title="DGX Spark local model gateway")
client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0))


def _headers(key: str = "") -> dict:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


async def _forward(url: str, body: dict, key: str = ""):
    """Forward a JSON request; stream the reply when the client asked for a stream."""
    if body.get("stream"):
        request = client.build_request("POST", url, json=body, headers=_headers(key))
        upstream = await client.send(request, stream=True)

        async def chunks():
            try:
                async for chunk in upstream.aiter_raw():
                    yield chunk
            finally:
                await upstream.aclose()

        return StreamingResponse(chunks(), status_code=upstream.status_code,
                                 media_type=upstream.headers.get("content-type", "text/event-stream"))
    upstream = await client.post(url, json=body, headers=_headers(key))
    return Response(upstream.content, status_code=upstream.status_code,
                    media_type=upstream.headers.get("content-type", "application/json"))


@app.get("/health")
@app.get("/v1/health/ready")
async def health():
    status = {}
    for name, base, key in (("chat", CHAT_URL, CHAT_API_KEY), ("embed", EMBED_URL, ""), ("rerank", RERANK_URL, "")):
        try:
            reply = await client.get(base + "/models", headers=_headers(key), timeout=5)
            status[name] = "ok" if reply.status_code == 200 else f"HTTP {reply.status_code}"
        except httpx.HTTPError as exc:
            status[name] = f"unreachable ({type(exc).__name__})"
    ready = all(value == "ok" for value in status.values())
    return JSONResponse({"ready": ready, "upstreams": status}, status_code=200 if ready else 503)


@app.get("/v1/models")
async def models():
    data, seen = [], set()
    for base, key in ((CHAT_URL, CHAT_API_KEY), (EMBED_URL, ""), (RERANK_URL, "")):
        try:
            reply = await client.get(base + "/models", headers=_headers(key), timeout=5)
            for item in reply.json().get("data", []):
                if item.get("id") not in seen:
                    seen.add(item.get("id"))
                    data.append(item)
        except (httpx.HTTPError, ValueError):
            continue  # one server being down should not hide the others
    return {"object": "list", "data": data}


@app.post("/v1/chat/completions")
async def chat(request: Request):
    return await _forward(CHAT_URL + "/chat/completions", await request.json(), CHAT_API_KEY)


@app.post("/v1/completions")
async def completions(request: Request):
    return await _forward(CHAT_URL + "/completions", await request.json(), CHAT_API_KEY)


@app.post("/v1/embeddings")
async def embeddings(request: Request):
    body = await request.json()
    for field in NVIDIA_ONLY_EMBED_FIELDS:
        body.pop(field, None)
    return await _forward(EMBED_URL + "/embeddings", body)


@app.post("/v1/ranking")
@app.post("/v1/retrieval/{_path:path}/reranking")
async def ranking(request: Request, _path: str = ""):
    """Translate NVIDIA's ranking API to vLLM's /rerank and back.

    NVIDIA request:  {"model", "query": {"text"}, "passages": [{"text"}], "truncate"?}
    NVIDIA response: {"rankings": [{"index", "logit"}]}, best first
    vLLM request:    {"model", "query", "documents": [str]}
    vLLM response:   {"results": [{"index", "relevance_score"}]}
    """
    body = await request.json()
    query = body.get("query")
    query = query.get("text", "") if isinstance(query, dict) else str(query or "")
    documents = [p.get("text", "") if isinstance(p, dict) else str(p) for p in body.get("passages", [])]
    upstream = await client.post(RERANK_URL + "/rerank", headers=_headers(),
                                 json={"model": body.get("model"), "query": query, "documents": documents})
    if upstream.status_code != 200:
        return Response(upstream.content, status_code=upstream.status_code,
                        media_type=upstream.headers.get("content-type", "application/json"))
    results = upstream.json().get("results", [])
    rankings = [{"index": r["index"], "logit": float(r.get("relevance_score", r.get("score", 0.0)))} for r in results]
    rankings.sort(key=lambda r: r["logit"], reverse=True)
    return {"rankings": rankings}


@app.post("/v1/rerank")
async def rerank(request: Request):
    return await _forward(RERANK_URL + "/rerank", await request.json())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
