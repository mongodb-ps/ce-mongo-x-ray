"""Compatibility adapter around pyftdc for MongoDB diagnostic.data files."""

from collections.abc import Iterator
from datetime import datetime

from pyftdc import FTDCReader
from pyftdc._codec import (
    DecodedChunk,
    decode_metric_document,
    iter_bson_documents,
    timestamp_for_row,
    value_for_slot,
)


class MongoFTDCReader(FTDCReader):
    """Read standard MongoDB FTDC payloads using pyftdc's decoder.

    pyftdc 0.1.0 calls the compressed payload ``doc`` while MongoDB server
    archives call it ``data``. This adapter supplies the expected alias.
    """

    def _metric_chunks(self) -> Iterator[DecodedChunk]:
        for path in self._paths():
            with path.open("rb") as stream:
                for document in iter_bson_documents(stream, path):
                    if document.get("type") != 1:
                        continue
                    if "doc" not in document and "data" in document:
                        document = dict(document)
                        document["doc"] = document["data"]
                    yield decode_metric_document(document)

    def get_metrics(
        self,
        names: set[str],
        start: datetime,
        end: datetime,
        include_disk_operations: bool = False,
    ) -> dict[str, dict[datetime, float]]:
        """Read multiple metrics in one archive pass.

        pyftdc's public API reads the archive once per metric. Overview needs
        several counters, so batching avoids repeatedly decoding every chunk.
        """
        output: dict[str, dict[datetime, float]] = {}
        for chunk in self._metric_chunks():
            indexes = [
                index
                for index, slot in enumerate(chunk.slots)
                if slot.part == 0
                and (
                    slot.path in names
                    or (
                        include_disk_operations
                        and slot.path.startswith("systemMetrics.disks.")
                        and (slot.path.endswith(".reads") or slot.path.endswith(".writes"))
                    )
                )
            ]
            for row in chunk.rows:
                timestamp = timestamp_for_row(chunk, row)
                if not start <= timestamp <= end:
                    continue
                for index in indexes:
                    slot = chunk.slots[index]
                    output.setdefault(slot.path, {})[timestamp] = float(value_for_slot(slot, row[index]))
        return output
