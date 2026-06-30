"""Base class for FTDC analysis items."""

from abc import ABC, abstractmethod
import logging
from pathlib import Path


class BaseItem(ABC):
    """Analyze FTDC files and render one section of the report."""

    def __init__(self, output_folder: str, config: dict, **kwargs) -> None:
        self.config = config
        self.output_folder = Path(output_folder)
        self._logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """Human-readable item name."""
        return self.__class__.__name__

    @abstractmethod
    def analyze(self, file_path: Path) -> None:
        """Ingest one FTDC file."""
        raise NotImplementedError

    def finalize_analysis(self) -> None:
        """Finish analysis after all input files have been ingested."""

    @abstractmethod
    def review_results_markdown(self, output, section_number: int = 1) -> None:
        """Write this item's report section as Markdown."""
        raise NotImplementedError
