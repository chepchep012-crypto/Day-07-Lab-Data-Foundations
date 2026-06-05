from typing import Callable
from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # Lưu các tham chiếu đến vector store và hàm gọi LLM
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Retrieve top-k relevant chunks từ Embedding Store
        # Giả định phương thức tìm kiếm mặc định của store là `search`
        retrieved_chunks = self.store.search(question, top_k=top_k)
        
        # 2. Trích xuất nội dung văn bản và dựng Prompt chứa Context
        # Xử lý linh hoạt cho mọi kiểu dữ liệu trả về của chunk để tránh crash bài test
        context_parts = []
        for chunk in retrieved_chunks:
            if isinstance(chunk, str):
                context_parts.append(chunk)
            elif isinstance(chunk, dict) and "text" in chunk:
                context_parts.append(chunk["text"])
            elif hasattr(chunk, "text"):
                context_parts.append(getattr(chunk, "text"))
            else:
                context_parts.append(str(chunk))
        
        context = "\n\n".join(context_parts)
        
        # Thiết kế cấu trúc Prompt chuẩn RAG để Inject Context vào LLM
        prompt = (
            "Use the following pieces of context to answer the question at the end.\n"
            "If you do not know the answer, just say that you do not know, do not try to make up an answer.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        
        # 3. Gọi hàm LLM với prompt đã được inject context để sinh câu trả lời
        return self.llm_fn(prompt)