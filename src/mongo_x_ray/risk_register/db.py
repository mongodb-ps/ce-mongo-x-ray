"""ChromaDB-backed risk register with vector search."""

from __future__ import annotations

import logging
from typing import Optional

from mongo_x_ray.risk_register.shared import (
    CHROMA_COLLECTION,
    CHROMA_COLLECTION_DESCRIPTION,
    Risk,
    get_db_path,
)

# Mute chromadb telemetry errors (posthog API mismatch)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

_logger = logging.getLogger(__name__)


def _collection(collection_name: str = CHROMA_COLLECTION):
    """Return an initialized ChromaDB collection (lazy singleton)."""
    # Import chromadb lazily so importing this module stays cheap and the risk
    # register remains an optional best-effort enrichment.
    import chromadb  # pylint: disable=import-outside-toplevel
    from chromadb.config import Settings  # pylint: disable=import-outside-toplevel

    db_path = get_db_path() / "chroma"
    db_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(collection_name)


def ingest_risks(risks: list[Risk]) -> int:
    """Upsert risks into ChromaDB, returning the number of documents ingested.

    Each risk is embedded twice — once for the ``Name`` field and once for the
    ``Risk Description`` field — stored in two separate collections so that
    matching can fall back from Name to Risk Description. Risks without a Risk
    Description are only embedded in the Name collection. Existing documents
    with the same ID are replaced (upsert).
    """
    if not risks:
        return 0

    name_col = _collection(CHROMA_COLLECTION)
    desc_col = _collection(CHROMA_COLLECTION_DESCRIPTION)

    name_ids: list[str] = []
    name_documents: list[str] = []
    name_metadatas: list[dict] = []
    desc_ids: list[str] = []
    desc_documents: list[str] = []
    desc_metadatas: list[dict] = []

    for risk in risks:
        metadata = {
            "id": risk.id,
            "risk_level": risk.risk_level,
            "impact": risk.impact,
            "name": risk.name,
            "description": risk.description,
        }
        name_ids.append(risk.id)
        name_documents.append(risk.name)
        name_metadatas.append(metadata)
        if risk.description.strip():
            desc_ids.append(risk.id)
            desc_documents.append(risk.description)
            desc_metadatas.append(metadata)

    name_col.upsert(ids=name_ids, documents=name_documents, metadatas=name_metadatas)
    if desc_ids:
        desc_col.upsert(ids=desc_ids, documents=desc_documents, metadatas=desc_metadatas)
    _logger.info("Ingested %d risks into ChromaDB", len(risks))
    return len(risks)


def search_risks(
    query: str,
    n_results: int = 3,
    collection_name: str = CHROMA_COLLECTION,
) -> list[dict]:
    """Vector search for risks matching the query text.

    Args:
        query: The text to search for.
        n_results: Maximum number of results to return.
        collection_name: Which field collection to search; defaults to the
            risk ``Name`` collection.

    Returns:
        A list of dicts with keys: id, risk_level, impact, name,
        description, distance.
    """
    col = _collection(collection_name)
    results = col.query(query_texts=[query], n_results=n_results)
    entries: list[dict] = []
    if not results["ids"] or not results["ids"][0]:
        return entries
    for i, doc_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        distance = results["distances"][0][i] if results["distances"] else None
        entries.append(
            {
                "id": meta.get("id", doc_id),
                "risk_level": meta.get("risk_level", ""),
                "impact": meta.get("impact", ""),
                "name": meta.get("name", ""),
                "description": meta.get("description", ""),
                "distance": distance,
            }
        )
    return entries


def clear_risks() -> None:
    """Delete all documents from all risk collections."""
    for collection_name in (CHROMA_COLLECTION, CHROMA_COLLECTION_DESCRIPTION):
        col = _collection(collection_name)
        ids = col.get()["ids"]
        if ids:
            col.delete(ids=ids)
            _logger.info("Cleared %d risks from %s", len(ids), collection_name)


def _collection_count() -> int:
    """Return the number of documents in the Name collection."""
    col = _collection(CHROMA_COLLECTION)
    return col.count()


def match_risk(category: str, max_distance: float = 0.9) -> Optional[dict]:
    """Find the closest matching risk for a given issue.

    Two-stage fallback search:
    1. Match ``category`` against the risk ``Name`` field.
    2. If no ``Name`` match is found, fall back to matching the same
       ``category`` against the risk ``Risk Description`` field.

    Args:
        category: The issue category/title to match against risk names.
        max_distance: Maximum vector distance for a match to be considered
            valid. Lower values mean closer matches. Default 0.9.

    Returns:
        The best matching risk dict, or ``None`` if no match found.
    """
    for collection_name in (CHROMA_COLLECTION, CHROMA_COLLECTION_DESCRIPTION):
        results = search_risks(category, n_results=1, collection_name=collection_name)
        if not results:
            continue
        top = results[0]
        if top["distance"] is not None and top["distance"] > max_distance:
            continue
        return top
    return None


def enrich_test_results(test_results: list[dict], max_distance: float = 0.9) -> int:
    """Enrich a list of test results with matched risk information.

    Each result dict that has a ``title`` key will be matched against the
    risk register using the two-stage fallback search. If a match is found,
    a ``matched_risk`` key is added.

    Args:
        test_results: List of test result dicts (each has a ``title`` key).
        max_distance: Maximum vector distance for a match.

    Returns:
        Number of results that were successfully matched to a risk.
    """
    if _collection_count() == 0:
        _logger.warning("\033[33mRisk register is empty — run `x-ray ingest <csv>` first\033[0m")
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
