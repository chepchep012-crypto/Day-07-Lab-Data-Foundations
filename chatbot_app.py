"""
Customer Support FAQ Chatbot — demo UI for Day 7 (RAG over EmbeddingStore).

Run:
    streamlit run chatbot_app.py

What it shows:
    - A chat box: type a question, get a grounded answer.
    - The retrieved chunks behind every answer (score + source doc) — so the
      audience can SEE retrieval, not just the final text.
    - Live metadata filtering (language / category) to demo search_with_filter().
    - A switch between the three chunking strategies to demo their impact.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import streamlit as st

from src import (
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    RecursiveChunker,
    SentenceChunker,
)

MANIFEST_PATH = Path("data/group_manifest.json")


# --------------------------------------------------------------------------- #
# Backend: embedder + store (cached so we build them once per setting)
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Loading embedding model…")
def get_embedder():
    """Prefer a real local embedder; fall back to the deterministic mock."""
    try:
        from src import LocalEmbedder

        embedder = LocalEmbedder()
        return embedder, getattr(embedder, "_backend_name", "local")
    except Exception:
        from src import _mock_embed

        return _mock_embed, "mock embeddings fallback"


def make_chunker(name: str, size: int, sentences: int):
    if name == "SentenceChunker":
        return SentenceChunker(max_sentences_per_chunk=sentences)
    if name == "FixedSizeChunker":
        return FixedSizeChunker(chunk_size=size, overlap=50)
    return RecursiveChunker(chunk_size=size)


@st.cache_resource(show_spinner="Indexing documents…")
def build_store(chunker_name: str, size: int, sentences: int):
    """Chunk every manifest doc and index it. Cached per (strategy, params)."""
    embedder, backend = get_embedder()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    chunker = make_chunker(chunker_name, size, sentences)

    store = EmbeddingStore(collection_name="faq_chatbot", embedding_fn=embedder)
    chunk_docs: list[Document] = []
    for entry in manifest["documents"]:
        content = Path(entry["file"]).read_text(encoding="utf-8")
        for i, chunk in enumerate(chunker.chunk(content)):
            meta = dict(entry["metadata"])
            meta["doc_id"] = entry["id"]
            chunk_docs.append(Document(id=f"{entry['id']}__{i}", content=chunk, metadata=meta))
    store.add_documents(chunk_docs)
    return store, backend, len(chunk_docs)


def _clean_answer(text: str) -> str:
    """Turn a raw FAQ chunk into a readable answer.

    Drops a leading title line (no end punctuation) and a leading echoed
    question line, then collapses whitespace.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Drop a leading FAQ title (e.g. "Billing FAQ for the AI Knowledge Assistant").
    if len(lines) > 1 and not lines[0].endswith((".", "!", "?", ":")):
        lines = lines[1:]
    # Drop a single leading echoed question line so the answer leads with the answer.
    if len(lines) > 1 and lines[0].endswith("?"):
        lines = lines[1:]
    answer = " ".join(" ".join(lines).split())
    # FAQ chunks often inline "Question? Answer." — strip the leading question.
    if "? " in answer:
        head, tail = answer.split("? ", 1)
        if tail and len(head) < 160:
            answer = tail
    return answer or " ".join(text.split())


def grounded_llm(prompt: str) -> str:
    """Offline grounded 'LLM': extract the top retrieved block and clean it.

    Robust to chunks that themselves contain blank lines: we split only on the
    "\\n\\n[N] " boundaries that separate retrieved chunks, not on any "\\n\\n".
    """
    marker = "Context:\n"
    if marker not in prompt:
        return "Xin lỗi, mình không tìm thấy thông tin phù hợp trong tài liệu."
    body = prompt.split(marker, 1)[1].split("\n\nQuestion:", 1)[0]
    blocks = re.split(r"\n\n\[\d+\]\s", body)          # split between chunks only
    top = re.sub(r"^\[\d+\]\s", "", blocks[0]).strip()  # strip the "[1] " tag
    return _clean_answer(top)


def build_context_prompt(question: str, results: list[dict]) -> str:
    """Same prompt shape as KnowledgeBaseAgent, for the metadata-filter path."""
    context = "\n\n".join(f"[{i}] {r['content']}" for i, r in enumerate(results, start=1))
    return (
        "Answer the question using ONLY the context below.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="FAQ Chatbot — RAG Demo", page_icon="🤖", layout="centered")
st.title("🤖 Customer Support FAQ Chatbot")
st.caption("RAG demo · EmbeddingStore + KnowledgeBaseAgent · Day 7 — Nhóm G11")

with st.sidebar:
    st.header("⚙️ Cấu hình retrieval")
    strategy = st.selectbox(
        "Chunking strategy",
        ["SentenceChunker", "FixedSizeChunker", "RecursiveChunker"],
        index=0,
    )
    sentences = st.slider("max_sentences_per_chunk", 1, 5, 2)
    size = st.slider("chunk_size (Fixed/Recursive)", 100, 500, 200, step=50)
    top_k = st.slider("top_k (số chunk lấy về)", 1, 5, 3)

    st.divider()
    st.subheader("🏷️ Metadata filter")
    lang = st.selectbox("language", ["(không lọc)", "en", "vi"], index=0)
    category = st.selectbox(
        "category",
        ["(không lọc)", "account", "billing", "password", "limits", "escalation", "general"],
        index=0,
    )

    metadata_filter: dict = {}
    if lang != "(không lọc)":
        metadata_filter["language"] = lang
    if category != "(không lọc)":
        metadata_filter["category"] = category

store, backend, n_chunks = build_store(strategy, size, sentences)
agent = KnowledgeBaseAgent(store=store, llm_fn=grounded_llm)

with st.sidebar:
    st.divider()
    st.caption(f"**Backend:** {backend}")
    st.caption(f"**Chunks đã index:** {n_chunks}")
    if metadata_filter:
        st.success(f"Đang lọc: {metadata_filter}")
    if st.button("🗑️ Xoá hội thoại"):
        st.session_state.messages = []
        st.rerun()

# Sample questions to click
st.write("**Thử nhanh:**")
samples = [
    "How do I reset a forgotten password?",
    "Which payment methods are accepted?",
    "How many documents can I store on the Free plan?",
    "Làm thế nào để tạo tài khoản mới?",
]
cols = st.columns(2)
clicked = None
for i, q in enumerate(samples):
    if cols[i % 2].button(q, use_container_width=True):
        clicked = q

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"🔎 {len(msg['sources'])} chunk được retrieve"):
                for rank, s in enumerate(msg["sources"], start=1):
                    st.markdown(
                        f"**{rank}. score `{s['score']:.3f}`** · `{s['metadata'].get('doc_id')}` "
                        f"· lang=`{s['metadata'].get('language')}` cat=`{s['metadata'].get('category')}`"
                    )
                    st.caption(s["content"][:300])


def handle(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})

    if metadata_filter:
        results = store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        if results:
            answer = grounded_llm(build_context_prompt(question, results))
        else:
            answer = "Không có tài liệu nào khớp bộ lọc metadata hiện tại."
    else:
        results = store.search(question, top_k=top_k)
        answer = agent.answer(question, top_k=top_k)  # uses KnowledgeBaseAgent + grounded_llm

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": results}
    )


prompt = st.chat_input("Hỏi về account, billing, password, limits, escalation…")
if clicked:
    handle(clicked)
    st.rerun()
if prompt:
    handle(prompt)
    st.rerun()
