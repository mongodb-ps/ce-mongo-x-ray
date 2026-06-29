"""Compatibility adapter around pyftdc for MongoDB diagnostic.data files."""

from collections.abc import Iterator

from pyftdc import FTDCReader
from pyftdc._codec import DecodedChunk, decode_metric_document, iter_bson_documents


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
