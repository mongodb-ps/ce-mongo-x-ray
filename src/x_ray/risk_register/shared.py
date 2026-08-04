"""Shared constants and data model for the Risk Register module."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

# Embed the Risk Name and Risk Description fields for vector search.
# Each field lives in its own collection so matching can fall back from
# Name to Risk Description.
CHROMA_COLLECTION = "risk_register"
CHROMA_COLLECTION_DESCRIPTION = "risk_register_description"
EMBED_FIELDS = ("Name", "Risk Description")


@dataclass
class Risk:
    """A single risk entry from the CSV risk register."""

    id: str
    risk_level: str
    impact: str
    name: str
    description: str


def load_risks_from_csv(csv_path: Path) -> list[Risk]:
    """Parse a CSV risk register file.

    Expected columns:
        ID, Risk Level, Impact, Name, Risk Description
    """
    risks: list[Risk] = []
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            risk = Risk(
                id=row.get("ID", "").strip(),
                risk_level=row.get("Risk Level", "").strip(),
                impact=row.get("Impact", "").strip(),
                name=row.get("Name", "").strip(),
                description=row.get("Risk Description", "").strip(),
            )
            if risk.id and risk.name:
                risks.append(risk)
    return risks


def get_db_path() -> Path:
    """Return the platform-specific database directory path."""
    import platform

    system = platform.system()
    if system == "Windows":
        base = Path.home() / "AppData" / "Roaming"
    else:
        base = Path.home()
    return base / ".x-ray"
