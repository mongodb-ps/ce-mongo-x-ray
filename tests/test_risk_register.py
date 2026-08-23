"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

import pytest

from mongo_x_ray.risk_register import db
from mongo_x_ray.risk_register.shared import (
    CHROMA_COLLECTION,
    CHROMA_COLLECTION_DESCRIPTION,
    Risk,
)

RISK_R1 = {
    "id": "R1",
    "risk_level": "High",
    "impact": "Medium",
    "name": "Replication Lag",
    "description": "oplog falls behind",
    "distance": 0.1,
}


def test_match_risk_uses_name_collection_first(monkeypatch):
    calls = []

    def fake_search(query, n_results=3, collection_name=CHROMA_COLLECTION):
        calls.append((query, n_results, collection_name))
        return [dict(RISK_R1)]

    monkeypatch.setattr(db, "search_risks", fake_search)

    risk = db.match_risk("Replication Lag")

    assert risk == RISK_R1
    assert calls == [("Replication Lag", 1, CHROMA_COLLECTION)]


def test_match_risk_falls_back_to_description_with_same_query(monkeypatch):
    calls = []

    def fake_search(query, n_results=3, collection_name=CHROMA_COLLECTION):
        calls.append((query, n_results, collection_name))
        if collection_name == CHROMA_COLLECTION:
            return []
        return [dict(RISK_R1)]

    monkeypatch.setattr(db, "search_risks", fake_search)

    risk = db.match_risk("Unrelated Topic")

    assert risk == RISK_R1
    assert calls == [
        ("Unrelated Topic", 1, CHROMA_COLLECTION),
        ("Unrelated Topic", 1, CHROMA_COLLECTION_DESCRIPTION),
    ]


def test_match_risk_falls_back_when_name_match_is_too_far(monkeypatch):
    calls = []

    def fake_search(query, n_results=3, collection_name=CHROMA_COLLECTION):
        calls.append((query, n_results, collection_name))
        far = dict(RISK_R1)
        far["distance"] = 2.0
        return [far] if collection_name == CHROMA_COLLECTION else [dict(RISK_R1)]

    monkeypatch.setattr(db, "search_risks", fake_search)

    risk = db.match_risk("Replication Lag", max_distance=1.0)

    assert risk == RISK_R1
    assert len(calls) == 2


def test_match_risk_returns_none_when_both_stages_miss(monkeypatch):
    def fake_search(query, n_results=3, collection_name=CHROMA_COLLECTION):  # pylint: disable=unused-argument
        return []

    monkeypatch.setattr(db, "search_risks", fake_search)

    assert db.match_risk("Unrelated Topic") is None


def test_enrich_test_results_matches_by_title(monkeypatch):
    monkeypatch.setattr(db, "_collection_count", lambda: 1)
    captured = {}

    def fake_match_risk(title, max_distance=1.0):  # pylint: disable=unused-argument
        captured["title"] = title
        return dict(RISK_R1)

    monkeypatch.setattr(db, "match_risk", fake_match_risk)

    results = [{"host": "h", "severity": "High", "title": "Replication Lag", "message": "secondary oplog behind"}]
    matched = db.enrich_test_results(results)

    assert matched == 1
    assert results[0]["matched_risk"] == RISK_R1
    assert captured == {"title": "Replication Lag"}


@pytest.mark.integration
def test_ingest_and_two_stage_search(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "get_db_path", lambda: tmp_path)

    risks = [
        Risk(
            id="R1",
            risk_level="High",
            impact="Medium",
            name="Replication Lag",
            description="Replication lag occurs when the secondary's oplog application falls behind the primary.",
        ),
        Risk(
            id="R2",
            risk_level="Medium",
            impact="Low",
            name="Missing Index",
            description="Queries scan the entire collection because no matching index exists.",
        ),
        Risk(id="R3", risk_level="Low", impact="Low", name="Backup Failure", description="   "),
    ]

    assert db.ingest_risks(risks) == 3

    name_col = db._collection(CHROMA_COLLECTION)  # pylint: disable=protected-access
    desc_col = db._collection(CHROMA_COLLECTION_DESCRIPTION)  # pylint: disable=protected-access
    assert name_col.count() == 3
    assert desc_col.count() == 2  # R3 has no Risk Description

    # Stage 1: title matches risk Name.
    assert db.match_risk("Replication Lag")["id"] == "R1"
    assert db.match_risk("Missing Index")["id"] == "R2"

    # Stage 2: Name misses, the same title matches Risk Description.
    risk = db.match_risk("the secondary's oplog application falls behind the primary")
    assert risk is not None and risk["id"] == "R1"

    # No match at either stage.
    assert db.match_risk("Unrelated Topic XYZ") is None

    # clear_risks empties both collections.
    db.clear_risks()
    assert name_col.count() == 0
    assert desc_col.count() == 0
