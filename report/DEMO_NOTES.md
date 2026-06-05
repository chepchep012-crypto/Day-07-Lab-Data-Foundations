# Demo Notes — Lab 7 (Customer Support / FAQ)

**Người trình bày:** Nguyễn Đức Toàn — Nhóm G11
**Strategy cá nhân:** `SentenceChunker(max_sentences_per_chunk=2)`
**Backend:** `all-MiniLM-L6-v2` (local thật)
**Script chiếu live:** `python group_demo.py`

> Số liệu dưới đây là kết quả auto-score thật từ `group_demo.py` trên bộ data hiện tại (8 docs → 139 chunks). Nếu sửa data/strategy thì chạy lại script và cập nhật lại các con số.

---

## Kịch bản trình bày (~4 phút)

### 1. Domain & Data (30s)
- Domain: **Customer Support / FAQ** cho SaaS "AI Knowledge Assistant".
- **8 tài liệu** (4 FAQ EN + 2 FAQ VI + playbook + escalation policy), khai báo trong `data/group_manifest.json`.
- Metadata schema: `category` (account/billing/password/limits/escalation/general), `language` (en/vi), `audience` (customer/agent).

### 2. Strategy của tôi (45s)
- Chọn **SentenceChunker, 2 câu/chunk**.
- Lý do: FAQ là các **cặp Hỏi–Đáp ngắn** → tách theo câu rồi gom 2 câu thường gói trọn 1 cặp Q&A → chunk *coherent*, không cắt giữa câu (như FixedSize), không vụn (như Recursive @200).
- 8 docs → **139 chunks**.

### 3. So sánh trong nhóm (60s)
| Strategy | Điểm mạnh | Điểm yếu |
|---|---|---|
| **SentenceChunker(2)** — của tôi | Chunk theo Q&A, top-1 đúng ở câu hỏi FAQ ngắn | Hỏng với tài liệu có heading markdown (Q4) |
| FixedSizeChunker(200/50) — bạn khác | Ổn định, đơn giản | Cắt giữa câu, đứt ý |
| RecursiveChunker(200) — bạn khác | Tôn trọng separator | @200 chunk quá vụn (avg ~75 ký tự) |

→ Thông điệp: **không có strategy thắng mọi loại tài liệu** — chọn theo *cấu trúc dữ liệu*.

### 4. Kết quả benchmark (45s)
5 queries chung của nhóm (Q5 dùng metadata filter `language=vi`). Auto-score (gold-phrase trong top-3, 2/1/0 điểm):

| Q | Câu hỏi | Gold@rank | Điểm |
|---|---|---|---|
| 1 | reset forgotten password | top-1 | 2/2 |
| 2 | payment methods accepted | top-2 | 1/2 |
| 3 | Free plan document limit | top-1 | 2/2 |
| 4 | when to escalate to Engineering | **miss top-3** | 0/2 |
| 5 | tạo tài khoản mới (vi, filtered) | top-1 | 2/2 |

- **Precision (chunk đúng trong top-3): 4/5**
- **Retrieval Quality: 7/10**

### 5. Failure analysis + bài học (60s)
- **Q4 (escalate Engineering) — miss:** câu trả lời thật ("Escalate to Engineering for reproducible bugs, error codes…") nằm trong `escalation_policy.md` là **văn xuôi có heading markdown**. SentenceChunker tách câu làm chunk "## Purpose" (giàu từ khoá "escalation", "specialized team") ăn điểm cao hơn, đẩy chunk tiêu chí thật ra khỏi top-3.
- **Q2 (payment) — tụt top-2:** ranh giới câu khiến câu hỏi "Which payment methods are accepted?" bị dính vào cuối Q&A trước (về role billing), nên top-1 chứa *câu hỏi* nhưng không chứa *đáp án*; đáp án "Visa, Mastercard…" ở top-2.
- **Bài học:**
  1. Chunk theo **cấu trúc tài liệu** (section/heading cho .md) thay vì theo câu một cách máy móc.
  2. **Metadata filter là bắt buộc** với data song ngữ — MiniLM đơn ngữ gần như không match Anh↔Việt (Q5 chỉ ra đúng nhờ filter `language=vi`).
  3. **Đề xuất sửa:** chunk `escalation_policy.md` theo `##`, prepend tiêu đề section vào chunk, hoặc tăng `top_k` lên 5 để chunk đúng lọt vào context.

---

## Q&A dự kiến từ giám khảo
- *"Sao không dùng Recursive?"* → @200 chunk quá vụn (avg ~75 ký tự) → mất ngữ cảnh.
- *"Metadata filter giúp gì?"* → Q5 tiếng Việt chỉ đúng nhờ filter `language=vi`; không filter thì chunk EN cùng chủ đề lấn át.
- *"Strategy này dở ở đâu?"* → Q4: tài liệu markdown có heading → cần chunk theo section, không theo câu.

---

## Checklist trước khi demo
- [ ] Chạy thử `python group_demo.py` một lần, xác nhận bảng RETRIEVAL QUALITY SUMMARY hiện đúng.
- [ ] Mở sẵn `report/REPORT.md` (Section 3, 6, 7) phòng khi cần dẫn chứng.
- [ ] Cập nhật số trong report khớp với script (hiện tại: precision 4/5, retrieval 7/10).
