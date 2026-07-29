"""Shared constants and data model for the Risk Register module."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

# Embed the Risk Name field for vector search.
CHROMA_COLLECTION = "risk_register"
EMBED_FIELDS = ("Name",)


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
