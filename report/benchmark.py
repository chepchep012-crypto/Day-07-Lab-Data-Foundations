"""
Personal benchmark harness for Day 7 — Customer Support / FAQ domain.

Runs everything needed for the personal report sections:
  - Section 3: chunking baseline (ChunkingStrategyComparator) + my strategy
  - Section 5: cosine similarity predictions on 5 sentence pairs
  - Section 6: 5 benchmark queries (incl. one metadata-filtered query)

Uses the real local embedder (all-MiniLM-L6-v2) when available so the
scores are meaningful; falls back to the deterministic mock embedder.

Run from the day folder:
    python report/benchmark.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sure THIS project's `src` package wins over any other on PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (  # noqa: E402
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    KnowledgeBaseAgent,
    RecursiveChunker,
    compute_similarity,
)

# --------------------------------------------------------------------------
# Embedding backend: prefer the real local model, fall back to mock.
# --------------------------------------------------------------------------
def make_embedder():
    try:
        from src import LocalEmbedder

        embedder = LocalEmbedder()
        print(f"[embedder] {embedder._backend_name} (real local model)\n")
        return embedder
    except Exception as exc:  # noqa: BLE001
        from src import _mock_embed

        print(f"[embedder] mock fallback ({type(exc).__name__}: {exc})\n")
        return _mock_embed


# --------------------------------------------------------------------------
# Document set: 8 customer-support FAQ docs with a shared metadata schema.
#   category | language | audience | source
# --------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DOC_META = {
    "faq_billing.txt":                 {"category": "billing",           "language": "en", "audience": "customer"},
    "faq_account_setup.txt":           {"category": "account_setup",     "language": "en", "audience": "customer"},
    "faq_password_recovery.txt":       {"category": "password_recovery", "language": "en", "audience": "customer"},
    "faq_service_limits.txt":          {"category": "service_limits",    "language": "en", "audience": "customer"},
    "faq_thanh_toan_vi.txt":           {"category": "billing",           "language": "vi", "audience": "customer"},
    "faq_thiet_lap_tai_khoan_vi.txt":  {"category": "account_setup",     "language": "vi", "audience": "customer"},
    "escalation_policy.md":            {"category": "escalation",        "language": "en", "audience": "internal"},
    "customer_support_playbook.txt":   {"category": "playbook",          "language": "en", "audience": "internal"},
}


def load_source_docs() -> list[Document]:
    docs = []
    for name, meta in DOC_META.items():
        content = (DATA_DIR / name).read_text(encoding="utf-8")
        docs.append(Document(id=name, content=content, metadata={"source": name, **meta}))
    return docs


# --------------------------------------------------------------------------
# My chunking strategy: RecursiveChunker tuned so each FAQ Q&A pair
# (a paragraph separated by a blank line) stays in one chunk.
# --------------------------------------------------------------------------
def chunk_documents(source_docs: list[Document], chunk_size: int = 400) -> list[Document]:
    chunker = RecursiveChunker(chunk_size=chunk_size)
    chunk_docs: list[Document] = []
    for doc in source_docs:
        for i, piece in enumerate(chunker.chunk(doc.content)):
            chunk_docs.append(
                Document(
                    id=f"{doc.id}#c{i}",
                    content=piece,
                    metadata={**doc.metadata, "parent": doc.id},
                )
            )
    return chunk_docs


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def run_baseline(source_docs: list[Document]) -> None:
    section("SECTION 3 — Chunking baseline (ChunkingStrategyComparator)")
    comparator = ChunkingStrategyComparator()
    for doc in source_docs[:3]:
        print(f"\nDocument: {doc.id} ({len(doc.content)} chars)")
        result = comparator.compare(doc.content, chunk_size=200)
        for name, stats in result.items():
            print(f"  {name:14s} count={stats['count']:3d}  avg_length={stats['avg_length']:.1f}")


def run_similarity_predictions(embedder) -> None:
    section("SECTION 5 — Cosine similarity predictions")
    pairs = [
        ("How do I reset my password?",
         "I forgot my password, how can I recover it?", "high"),
        ("What payment methods are accepted?",
         "How many documents can I store on the Free plan?", "low"),
        ("How do I cancel my subscription?",
         "Làm thế nào để hủy đăng ký?", "medium (cross-lingual)"),
        ("The Free plan stores up to 50 documents.",
         "The Pro plan stores up to 5,000 documents.", "high"),
        ("How do I enable two-factor authentication?",
         "The weather is sunny in the mountains today.", "low"),
    ]
    print(f"{'#':>2}  {'pred':<22} {'actual':>7}  pair")
    for i, (a, b, pred) in enumerate(pairs, start=1):
        score = compute_similarity(embedder(a), embedder(b))
        print(f"{i:>2}  {pred:<22} {score:>7.3f}  {a[:34]!r} | {b[:34]!r}")


BENCHMARK = [
    {"q": "How do I get a refund for a monthly plan?",
     "gold": "Within 14 days via Settings > Billing > History > Request refund; returns to the card in 5-10 business days.",
     "filter": None},
    {"q": "What are the password requirements?",
     "gold": "At least 12 characters with upper, lower, number, and symbol; cannot reuse the last 5 passwords.",
     "filter": None},
    {"q": "How many documents can the Free plan store?",
     "gold": "Up to 50 documents on Free (Pro: 5,000; Enterprise: no fixed cap).",
     "filter": None},
    {"q": "When should an agent escalate an issue to the Billing team?",
     "gold": "Unexplained charge, failed refund older than 10 business days, or tax/invoice correction; no refund over 200 USD without Billing approval.",
     "filter": None},
    {"q": "Làm thế nào để hủy đăng ký gói dịch vụ?",
     "gold": "Cài đặt > Thanh toán > Gói > Hủy đăng ký; quyền truy cập còn đến hết kỳ đã trả, không xóa tài liệu.",
     "filter": {"language": "vi"}},
]


def run_benchmark(store: EmbeddingStore) -> None:
    section("SECTION 6 — Benchmark queries (top-3 retrieval + agent answer)")
    agent = KnowledgeBaseAgent(store=store, llm_fn=lambda p: "(LLM answer grounded on the context above)")
    relevant_hits = 0
    for i, item in enumerate(BENCHMARK, start=1):
        if item["filter"]:
            results = store.search_with_filter(item["q"], top_k=3, metadata_filter=item["filter"])
            tag = f" [filter={item['filter']}]"
        else:
            results = store.search(item["q"], top_k=3)
            tag = ""
        print(f"\nQ{i}{tag}: {item['q']}")
        print(f"  gold: {item['gold']}")
        for rank, r in enumerate(results, start=1):
            preview = r["content"].replace("\n", " ")[:70]
            print(f"  top{rank} score={r['score']:.3f} [{r['metadata']['category']}/{r['metadata']['language']}] {preview}...")
        if results:
            relevant_hits += 1
    print(f"\nQueries with a chunk retrieved in top-3: {relevant_hits}/5")


def main() -> None:
    embedder = make_embedder()
    source_docs = load_source_docs()
    print(f"Loaded {len(source_docs)} source documents from {DATA_DIR}")

    run_baseline(source_docs)

    chunk_docs = chunk_documents(source_docs)
    print(f"\nMy strategy (RecursiveChunker, chunk_size=400) produced "
          f"{len(chunk_docs)} chunks from {len(source_docs)} documents.")

    store = EmbeddingStore(collection_name="support_faq", embedding_fn=embedder)
    store.add_documents(chunk_docs)
    print(f"Stored {store.get_collection_size()} chunks.")

    run_similarity_predictions(embedder)
    run_benchmark(store)


if __name__ == "__main__":
    main()
