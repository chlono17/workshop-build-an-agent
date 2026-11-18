"""Offline search over bundled documents, shaped like a Tavily response.

The local-first fork uses this instead of Tavily web search by default
(WORKSHOP_SEARCH=local). Results keep Tavily's keys (title, url, content,
raw_content, score) so the existing formatting code works unchanged.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path

from . import PROJECT_ROOT

DEFAULT_CORPUS = PROJECT_ROOT / "data" / "it-knowledge-base"
_TOKEN = re.compile(r"[a-z0-9]+|[一-鿿]")  # English words, or single CJK characters
# Common question words carry no topic; without this list "how do I ... from home"
# outranks the one word that matters ("vpn").
_STOPWORDS = set("""
a about after all also an and any are as at be been before by can could did do does
for from get go has have how i if in into is it its may me more my no not of on or our
should so some than that the their them then there these this to up us use was we what
when where which who why will with would you your
""".split())
_TITLE_WEIGHT = 3  # a match in the document title counts this many times


_SUFFIXES = ("ions", "ion", "ing", "ed", "es", "s")


def _stem(word: str) -> str:
    """Very small suffix stripper so "connecting" and "connect" match."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _tokens(text: str) -> list[str]:
    return [_stem(t) for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS]


@lru_cache(maxsize=4)
def _load(corpus_dir: str) -> list[dict]:
    docs = []
    for path in sorted(Path(corpus_dir).glob("**/*")):
        if path.suffix.lower() not in (".md", ".txt") or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        heading = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), "")
        docs.append({
            "title": heading or path.stem.replace("-", " ").title(),
            "url": f"file://{path.relative_to(PROJECT_ROOT)}" if path.is_relative_to(PROJECT_ROOT) else path.as_uri(),
            "text": text,
            "tokens": _tokens((heading + " ") * _TITLE_WEIGHT + text),
        })
    return docs


def _snippet(text: str, terms: set[str], width: int = 400) -> str:
    """Return the paragraph that mentions the most query terms."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and not p.strip().startswith("#")]
    if not paragraphs:
        return text[:width]
    best = max(paragraphs, key=lambda p: len(terms & set(_tokens(p))))
    return best[:width]


def search(query: str, max_results: int = 3, corpus_dir: str | Path = DEFAULT_CORPUS) -> dict:
    """Rank documents with BM25 and return a Tavily-shaped {"query", "results"} dict."""
    docs = _load(str(corpus_dir))
    terms = _tokens(query)
    if not docs or not terms:
        return {"query": query, "results": []}
    n = len(docs)
    avg_len = sum(len(d["tokens"]) for d in docs) / n
    k1, b = 1.5, 0.75
    scored = []
    for doc in docs:
        length = len(doc["tokens"])
        score = 0.0
        for term in set(terms):
            tf = doc["tokens"].count(term)
            if not tf:
                continue
            df = sum(1 for d in docs if term in d["tokens"])
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * length / avg_len))
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:max_results]
    best = top[0][0] if top else 1.0
    return {
        "query": query,
        "results": [
            {
                "title": doc["title"],
                "url": doc["url"],
                "content": _snippet(doc["text"], set(terms)),
                "raw_content": doc["text"],
                "score": round(score / best, 4),
            }
            for score, doc in top
        ],
    }


SEARCH_RESULTS_TOOL_NAME = "tavily_search_results_json"


def make_search_results_tool(max_results: int = 3, name: str = SEARCH_RESULTS_TOOL_NAME):
    """A LangChain tool shaped like TavilySearchResults, backed by the offline search.

    Local-first fork: Modules 5-7 offer a "Web Search" option built on Tavily's
    TavilySearchResults tool. This stand-in keeps that tool's name and output (a list
    of {"title", "url", "content", "score"} dicts) so capability checks, UI icons and
    prompts keep working, but searches data/it-knowledge-base with no key and no internet.
    """
    from langchain_core.tools import StructuredTool

    def search_documents(query: str) -> list[dict]:
        """Keyword search over the company's offline IT documents."""
        return [{key: hit[key] for key in ("title", "url", "content", "score")}
                for hit in search(query, max_results=max_results)["results"]]

    return StructuredTool.from_function(
        func=search_documents,
        name=name,
        description=("Keyword search over the company's offline IT knowledge base (local documents, "
                     "no internet). Input: a search query. Returns titles, file:// URLs and excerpts."),
    )
