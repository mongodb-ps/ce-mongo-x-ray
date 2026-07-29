"""ChromaDB-backed risk register with vector search."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Sequence

# Suppress chromadb telemetry (posthog API incompatibility in 0.5.x)
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.config import Settings

from x_ray.risk_register.shared import CHROMA_COLLECTION, EMBED_FIELDS, Risk, get_db_path

# Mute chromadb telemetry errors (posthog API mismatch)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

_logger = logging.getLogger(__name__)


def _collection():
    """Return an initialized ChromaDB collection (lazy singleton)."""
    db_path = get_db_path() / "chroma"
    db_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(CHROMA_COLLECTION)


def ingest_risks(risks: list[Risk]) -> int:
    """Upsert risks into ChromaDB, returning the number of documents ingested.

    Existing documents with the same ID are replaced (upsert).
    """
    if not risks:
        return 0

    col = _collection()
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for risk in risks:
        ids.append(risk.id)
        documents.append(risk.name)
        metadatas.append({
            "id": risk.id,
            "risk_level": risk.risk_level,
            "impact": risk.impact,
            "name": risk.name,
            "description": risk.description,
        })

    col.upsert(ids=ids, documents=documents, metadatas=metadatas)
    _logger.info("Ingested %d risks into ChromaDB", len(risks))
    return len(risks)


def search_risks(query: str, n_results: int = 3) -> list[dict]:
    """Vector search for risks matching the query text.

    Returns a list of dicts with keys: id, risk_level, impact, name,
    description, distance.
    """
    col = _collection()
    results = col.query(query_texts=[query], n_results=n_results)
    entries: list[dict] = []
    if not results["ids"] or not results["ids"][0]:
        return entries
    for i, doc_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        distance = results["distances"][0][i] if results["distances"] else None
        entries.append({
            "id": meta.get("id", doc_id),
            "risk_level": meta.get("risk_level", ""),
            "impact": meta.get("impact", ""),
            "name": meta.get("name", ""),
            "description": meta.get("description", ""),
            "distance": distance,
        })
    return entries


def clear_risks() -> None:
    """Delete all documents from the collection."""
    col = _collection()
    ids = col.get()["ids"]
    if ids:
        col.delete(ids=ids)
        _logger.info("Cleared %d risks from ChromaDB", len(ids))


def _collection_count() -> int:
    """Return the number of documents in the collection."""
    col = _collection()
    return col.count()


def match_risk(category: str, max_distance: float = 1.0) -> Optional[dict]:
    """Find the closest matching risk for a given issue category.

    Args:
        category: The issue category/title to match against risk names.
        max_distance: Maximum vector distance for a match to be considered
            valid. Lower values mean closer matches. Default 1.0.

    Returns:
        The best matching risk dict, or ``None`` if no match found.
    """
    results = search_risks(category, n_results=1)
    if not results:
        return None
    top = results[0]
    if top["distance"] is not None and top["distance"] > max_distance:
        return None
    return top


def enrich_test_results(test_results: list[dict], max_distance: float = 1.0) -> int:
    """Enrich a list of test results with matched risk information.

    Each result dict that has a ``title`` key will be matched against the
    risk register. If a match is found, a ``matched_risk`` key is added.

    Args:
        test_results: List of test result dicts (each has a ``title`` key).
        max_distance: Maximum vector distance for a match.

    Returns:
        Number of results that were successfully matched to a risk.
    """
    if _collection_count() == 0:
        _logger.warning(
            "\033[33mRisk register is empty — run `x-ray ingest <csv>` first\033[0m"
        )
        return 0
    matched = 0
    for result in test_results:
        title = result.get("title", "")
        if not title:
            continue
        risk = match_risk(title, max_distance=max_distance)
        if risk:
            result["matched_risk"] = risk
            matched += 1
    return matched
