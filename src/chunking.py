from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
<<<<<<< HEAD
        if not text:
            return []

        # Tách câu và giữ lại các ký tự phân tách câu (delimiters)
        parts = re.split(r"(\. |! |\? |\.\n)", text)
        sentences: list[str] = []

        # Tái cấu trúc lại câu hoàn chỉnh bằng cách gộp phần text và delimiter đi kèm
        for i in range(0, len(parts) - 1, 2):
            sentence = parts[i] + parts[i + 1]
            if sentence:
                sentences.append(sentence)
        
        # Nếu còn phần text dư cuối cùng không chứa delimiter lẻ ở cuối mảng
        if len(parts) % 2 != 0 and parts[-1]:
            sentences.append(parts[-1])

        # Gộp các câu lại thành từng chunk dựa trên số lượng max_sentences_per_chunk
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_group = sentences[i : i + self.max_sentences_per_chunk]
            combined_chunk = "".join(chunk_group).strip()
            if combined_chunk:
                chunks.append(combined_chunk)

=======
        if not text or not text.strip():
            return []

        # Split right after a sentence terminator (. ! ?) followed by whitespace.
        # This covers ". ", "! ", "? " and ".\n" as required.
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: list[str] = []
        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[start : start + self.max_sentences_per_chunk]
            chunks.append(" ".join(group))
>>>>>>> 3ef2405e66a067c795d70f09e71525bf8fa1d630
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
<<<<<<< HEAD
        # Điểm dừng đệ quy: nếu kích thước text đã nhỏ hơn hoặc bằng chunk_size mong muốn
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Nếu không còn ký tự phân tách nào hoặc gặp ký tự rỗng "", thực hiện cắt ép buộc theo chunk_size
        if not remaining_separators:
=======
        # Small enough already — keep as a single chunk.
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text else []

        # No separator left (or the empty-string separator) — hard split by size.
        if not remaining_separators or remaining_separators[0] == "":
>>>>>>> 3ef2405e66a067c795d70f09e71525bf8fa1d630
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

<<<<<<< HEAD
        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        if sep == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        # Tiến hành tách đoạn văn bản hiện tại bằng ký tự phân tách có ưu tiên cao nhất
        parts = current_text.split(sep)
        final_chunks: list[str] = []
        current_good_chunk: list[str] = []
        current_len = 0

        for part in parts:
            # Nếu bản thân một sub-part vượt quá chunk_size, áp dụng đệ quy với separator tiếp theo
            sub_parts = [part]
            if len(part) > self.chunk_size:
                sub_parts = self._split(part, next_seps)

            for sp in sub_parts:
                # Tính toán độ dài dự kiến khi thêm sp vào chunk hiện tại (bao gồm cả ký tự phân tách)
                sep_len = len(sep) if current_good_chunk else 0
                if current_len + sep_len + len(sp) <= self.chunk_size:
                    current_good_chunk.append(sp)
                    current_len += sep_len + len(sp)
                else:
                    # Đóng gói chunk cũ khi đã đầy và khởi tạo một chunk mới
                    if current_good_chunk:
                        final_chunks.append(sep.join(current_good_chunk))
                    current_good_chunk = [sp]
                    current_len = len(sp)

        # Đóng gói phần dữ liệu còn sót lại cuối cùng
        if current_good_chunk:
            final_chunks.append(sep.join(current_good_chunk))

        return final_chunks
=======
        separator = remaining_separators[0]
        rest = remaining_separators[1:]

        chunks: list[str] = []
        for part in current_text.split(separator):
            if not part:
                continue
            if len(part) <= self.chunk_size:
                chunks.append(part)
            else:
                # Still too big — try the next, finer separator.
                chunks.extend(self._split(part, rest))
        return chunks
>>>>>>> 3ef2405e66a067c795d70f09e71525bf8fa1d630


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
<<<<<<< HEAD
    # Tính độ dài (magnitude) của từng vector
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(x * x for x in vec_b))

    # Tránh lỗi chia cho 0 nếu một trong hai vector có độ dài bằng 0
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (mag_a * mag_b)
=======
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)
>>>>>>> 3ef2405e66a067c795d70f09e71525bf8fa1d630


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
<<<<<<< HEAD
        # Khởi tạo 3 chiến lược chunking cơ bản theo cấu hình bài Lab
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=20),
            "sentence": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison_results = {}

        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            lengths = [len(c) for c in chunks]

            comparison_results[name] = {
                "num_chunks": len(chunks),
                "avg_length": sum(lengths) / len(lengths) if lengths else 0,
                "max_length": max(lengths) if lengths else 0,
                "min_length": min(lengths) if lengths else 0,
                "chunks": chunks,
            }

        return comparison_results
=======
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size).chunk(text),
            "by_sentences": SentenceChunker().chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
        }

        comparison: dict = {}
        for name, chunks in strategies.items():
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count else 0.0
            comparison[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return comparison
>>>>>>> 3ef2405e66a067c795d70f09e71525bf8fa1d630
