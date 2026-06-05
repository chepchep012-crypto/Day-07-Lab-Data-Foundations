"""
Group benchmark runner for Day 7 — Customer Support / FAQ domain.

Pipeline:
    1. Load documents + metadata from data/group_manifest.json
    2. Chunk each document with a chosen strategy, then add chunks to the store
    3. Run the 5 group benchmark queries (query #5 uses metadata filtering)
    4. Run the ChunkingStrategyComparator baseline on a few docs
    5. Run 5 cosine-similarity predictions

Usage:
    python group_demo.py
"""
from __future__ import annotations

import json
from pathlib import Path

from src import (
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    RecursiveChunker,
    SentenceChunker,
    compute_similarity,
)

try:
    from src import LocalEmbedder

    embedder = LocalEmbedder()
except Exception:  # pragma: no cover - fallback for classrooms without the model
    from src import _mock_embed as embedder

MANIFEST = json.loads(Path("data/group_manifest.json").read_text(encoding="utf-8"))

# My chosen strategy for this domain (FAQ = short Q&A blocks):
MY_CHUNKER = SentenceChunker(max_sentences_per_chunk=2)


def load_manifest_documents() -> list[dict]:
    docs = []
    for entry in MANIFEST["documents"]:
        content = Path(entry["file"]).read_text(encoding="utf-8")
        docs.append({"id": entry["id"], "content": content, "metadata": entry["metadata"]})
    return docs


def build_store(raw_docs: list[dict], chunker) -> EmbeddingStore:
    store = EmbeddingStore(collection_name="cs_faq", embedding_fn=embedder)
    chunk_docs: list[Document] = []
    for d in raw_docs:
        for i, chunk in enumerate(chunker.chunk(d["content"])):
            meta = dict(d["metadata"])
            meta["doc_id"] = d["id"]
            chunk_docs.append(Document(id=f"{d['id']}__{i}", content=chunk, metadata=meta))
    store.add_documents(chunk_docs)
    return store


def extractive_llm(prompt: str) -> str:
    """Grounded demo LLM: return the first retrieved [1] block as the answer."""
    marker = "Context:\n"
    if marker in prompt:
        body = prompt.split(marker, 1)[1]
        first = body.strip().split("\n\n")[0].strip()
        return f"(grounded) {first}"
    return "(no context)"


def section_backend() -> None:
    print(f"Embedding backend: {getattr(embedder, '_backend_name', 'mock')}\n")


def section_benchmark(store: EmbeddingStore) -> None:
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
    queries = [
        ("How do I reset a forgotten password?", None),
        ("Which payment methods are accepted?", None),
        ("How many documents can I store on the Free plan?", None),
        ("When should an agent escalate an issue to Engineering?", None),
        ("Làm thế nào để tạo tài khoản mới?", {"language": "vi"}),
    ]
    print("=" * 70)
    print("SECTION 6 — BENCHMARK QUERIES (top-3)")
    print("=" * 70)
    for n, (q, mfilter) in enumerate(queries, start=1):
        if mfilter:
            results = store.search_with_filter(q, top_k=3, metadata_filter=mfilter)
            tag = f" [filter={mfilter}]"
        else:
            results = store.search(q, top_k=3)
            tag = ""
        print(f"\nQ{n}: {q}{tag}")
        for rank, r in enumerate(results, start=1):
            preview = r["content"][:80].replace("\n", " ")
            print(f"  {rank}. score={r['score']:.3f} doc={r['metadata'].get('doc_id')} | {preview}")
        answer = agent.answer(q, top_k=3)
        print(f"  AGENT: {answer[:160]}")


def section_comparator(raw_docs: list[dict]) -> None:
    print("\n" + "=" * 70)
    print("SECTION 3 — CHUNKING STRATEGY BASELINE (compare on 3 docs)")
    print("=" * 70)
    comparator = ChunkingStrategyComparator()
    for d in raw_docs[:3]:
        print(f"\nDoc: {d['id']}")
        result = comparator.compare(d["content"], chunk_size=200)
        for strategy, stats in result.items():
            print(f"  {strategy:12s} count={stats['count']:3d} avg_length={stats['avg_length']:.1f}")


def section_similarity() -> None:
    print("\n" + "=" * 70)
    print("SECTION 5 — COSINE SIMILARITY PREDICTIONS")
    print("=" * 70)
    pairs = [
        ("How do I reset my password?", "I forgot my password, how to recover it?"),
        ("Which payment methods are accepted?", "What credit cards can I use to pay?"),
        ("How many documents can I store?", "What is the storage limit for my plan?"),
        ("How do I reset my password?", "How many documents can I store?"),
        ("Which payment methods are accepted?", "Brown bears live in northern forests."),
    ]
    for n, (a, b) in enumerate(pairs, start=1):
        score = compute_similarity(embedder(a), embedder(b))
        print(f"  Pair {n}: sim={score:.3f}")
        print(f"     A: {a}")
        print(f"     B: {b}")


def main() -> None:
    section_backend()
    raw_docs = load_manifest_documents()
    store = build_store(raw_docs, MY_CHUNKER)
    print(f"Loaded {len(raw_docs)} docs -> {store.get_collection_size()} chunks "
          f"(strategy={MY_CHUNKER.__class__.__name__})\n")
    section_benchmark(store)
    section_comparator(raw_docs)
    section_similarity()


if __name__ == "__main__":
    main()
