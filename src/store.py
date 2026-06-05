from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document

# Reserved metadata key used to track the owning Document id inside ChromaDB
# (Chroma has no separate id-per-record field we can filter the same way).
_DOC_ID_KEY = "__doc_id__"


class EmbeddingStore:
    """
    A vector store for text chunks.

    Two backends:
      - In-memory (default): a plain Python list. Deterministic, no deps —
        used by the test suite.
      - ChromaDB (opt-in via use_chroma=True): a real, persistent vector
        database written to `persist_dir` on disk. Data survives restarts.

    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
        use_chroma: bool = False,
        persist_dir: str = "chroma_db",
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._persist_dir = persist_dir
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._client = None
        self._collection = None
        self._next_index = 0

        if use_chroma:
            try:
                import chromadb

                # PersistentClient writes the database to disk, so embeddings
                # are saved and reloaded across runs.
                self._client = chromadb.PersistentClient(path=persist_dir)
                self._collection = self._client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                self._use_chroma = True
            except Exception:
                # Any failure (not installed, version mismatch) → in-memory.
                self._use_chroma = False
                self._client = None
                self._collection = None

    # ------------------------------------------------------------------ #
    # In-memory helpers
    # ------------------------------------------------------------------ #
    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document."""
        record = {
            "index": self._next_index,
            "doc_id": doc.id,
            "content": doc.content,
            "metadata": dict(doc.metadata),
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run an in-memory similarity search over the provided records."""
        query_embedding = self._embedding_fn(query)

        scored: list[dict[str, Any]] = []
        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored.append(
                {
                    "doc_id": record["doc_id"],
                    "content": record["content"],
                    "metadata": record["metadata"],
                    "score": score,
                }
            )

        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]

    # ------------------------------------------------------------------ #
    # ChromaDB helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_where(metadata_filter: dict | None) -> dict | None:
        """Translate a flat metadata filter into a Chroma `where` clause."""
        if not metadata_filter:
            return None
        if len(metadata_filter) == 1:
            return dict(metadata_filter)
        return {"$and": [{key: value} for key, value in metadata_filter.items()]}

    def _chroma_query(self, query: str, top_k: int, where: dict | None) -> list[dict[str, Any]]:
        if self._collection.count() == 0:
            return []
        result = self._collection.query(
            query_embeddings=[self._embedding_fn(query)],
            n_results=max(1, top_k),
            where=where,
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        out: list[dict[str, Any]] = []
        for content, meta, dist in zip(documents, metadatas, distances):
            meta = dict(meta or {})
            doc_id = meta.pop(_DOC_ID_KEY, None)
            out.append(
                {
                    "doc_id": doc_id,
                    "content": content,
                    "metadata": meta,
                    # cosine distance -> similarity, so higher = better (matches in-memory)
                    "score": 1.0 - dist,
                }
            )
        return out

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: collection.upsert(ids, documents, embeddings, metadatas)
        For in-memory: append dicts to self._store
        """
        if self._use_chroma:
            ids, documents, embeddings, metadatas = [], [], [], []
            for doc in docs:
                ids.append(f"{doc.id}__{self._next_index}")
                self._next_index += 1
                documents.append(doc.content)
                embeddings.append(self._embedding_fn(doc.content))
                meta = dict(doc.metadata)
                meta[_DOC_ID_KEY] = doc.id  # reserved key for filter/delete
                metadatas.append(meta)
            # upsert keeps re-runs idempotent (same ids overwrite, no duplicates)
            self._collection.upsert(
                ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
            )
            return

        for doc in docs:
            self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find the top_k most similar documents to query."""
        if self._use_chroma:
            return self._chroma_query(query, top_k, where=None)
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if self._use_chroma:
            return self._chroma_query(query, top_k, where=self._build_where(metadata_filter))

        if metadata_filter:
            candidates = [
                record
                for record in self._store
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
        else:
            candidates = self._store

        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            before = self._collection.count()
            self._collection.delete(where={_DOC_ID_KEY: doc_id})
            return self._collection.count() < before

        remaining = [record for record in self._store if record["doc_id"] != doc_id]
        removed = len(remaining) != len(self._store)
        self._store = remaining
        return removed
>>>>>>> 3ef2405e66a067c795d70f09e71525bf8fa1d630
