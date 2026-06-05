# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *Viết 1-2 câu:*

**Ví dụ HIGH similarity:**
- Sentence A:
- Sentence B:
- Tại sao tương đồng:

**Ví dụ LOW similarity:**
- Sentence A:
- Sentence B:
- Tại sao khác:

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Viết 1-2 câu:*

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> *Đáp án:*

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Viết 1-2 câu:*

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Customer Support / FAQ cho một sản phẩm SaaS ("AI Knowledge Assistant").

**Tại sao nhóm chọn domain này?**
> Customer support có cấu trúc Hỏi–Đáp rõ ràng nên dễ đánh giá chunking và viết gold answer verify được. Mỗi tài liệu gắn liền với một category nghiệp vụ (account, billing, password, limits, escalation) và có cả bản tiếng Anh lẫn tiếng Việt, nên metadata filtering (`category`, `language`) có ý nghĩa thực tế. Đây cũng là use-case RAG phổ biến nhất ngoài đời, sát với mục tiêu của lab.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | customer_support_playbook.txt | Mẫu có sẵn của lab | 1703 | category=general, language=en, audience=agent |
| 2 | faq_account_setup.txt | Nhóm tự soạn | 1429 | category=account, language=en, audience=customer |
| 3 | faq_billing.txt | Nhóm tự soạn | 1711 | category=billing, language=en, audience=customer |
| 4 | faq_password_recovery.txt | Nhóm tự soạn | 1567 | category=password, language=en, audience=customer |
| 5 | faq_service_limits.txt | Nhóm tự soạn | 1427 | category=limits, language=en, audience=customer |
| 6 | faq_thiet_lap_tai_khoan_vi.txt | Nhóm tự soạn (VI) | 1888 | category=account, language=vi, audience=customer |
| 7 | faq_thanh_toan_vi.txt | Nhóm tự soạn (VI) | 1914 | category=billing, language=vi, audience=customer |
| 8 | escalation_policy.md | Nhóm tự soạn | 1866 | category=escalation, language=en, audience=agent |

> Metadata cho từng file được khai báo tập trung trong `data/group_manifest.json` để nạp kèm khi tạo `Document`.

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `category` | str | account, billing, password, limits, escalation, general | Thu hẹp tìm kiếm về đúng nhóm nghiệp vụ; tránh nhiễu giữa các FAQ giống nhau về ngôn từ |
| `language` | str | en, vi | Lọc theo ngôn ngữ câu hỏi; tránh trả về chunk khác ngôn ngữ với người dùng |
| `audience` | str | customer, agent | Tách tài liệu hướng dẫn khách (FAQ) khỏi tài liệu nội bộ (playbook, escalation policy) |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Strategy Của Tôi

**Loại:** [FixedSizeChunker / SentenceChunker / RecursiveChunker / custom strategy]

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: strategy chunk thế nào? Dựa trên dấu hiệu gì?*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu: domain có pattern gì mà strategy khai thác?*

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | | | |
| | **của tôi** | | | |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | | | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Viết 2-3 câu: dùng regex gì để detect sentence? Xử lý edge case nào?*

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Viết 2-3 câu: algorithm hoạt động thế nào? Base case là gì?*

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Viết 2-3 câu: lưu trữ thế nào? Tính similarity ra sao?*

**`search_with_filter` + `delete_document`** — approach:
> *Viết 2-3 câu: filter trước hay sau? Delete bằng cách nào?*

### KnowledgeBaseAgent

**`answer`** — approach:
> *Viết 2-3 câu: prompt structure? Cách inject context?*

### Test Results

```
# Paste output of: pytest tests/ -v
```

**Số tests pass:** __ / __

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | high / low | | |
| 2 | | | high / low | | |
| 3 | | | high / low | | |
| 4 | | | high / low | | |
| 5 | | | high / low | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Viết 2-3 câu:*

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer | Chunk nguồn |
|---|-------|-------------|-------------|
| 1 | How do I reset a forgotten password? | Bấm "Forgot password" trên trang login, nhập email; link reset gửi trong 2 phút và có hiệu lực 60 phút; mở link, đặt mật khẩu mới rồi xác nhận. | faq_password_recovery.txt |
| 2 | Which payment methods are accepted? | Visa, Mastercard, American Express; cộng chuyển khoản ngân hàng theo hóa đơn cho gói Enterprise năm. Không hỗ trợ thẻ ghi nợ và PayPal. | faq_billing.txt |
| 3 | How many documents can I store on the Free plan? | Tối đa 50 tài liệu trên gói Free (Pro: 5.000; Enterprise: không giới hạn cố định). | faq_service_limits.txt |
| 4 | When should an agent escalate an issue to Engineering? | Khi gặp bug tái hiện được, mã lỗi FAQ không cover, lỗi rate-limit còn sau khi back-off đúng, hoặc nghi ngờ mất dữ liệu — luôn đính kèm request ID và ảnh chụp. | escalation_policy.md |
| 5 | Làm thế nào để tạo tài khoản mới? *(filter language=vi)* | Mở app.assistant.example/signup, nhập email công việc, bấm "Tạo tài khoản"; email xác minh đến trong 2 phút, bấm link để kích hoạt. | faq_thiet_lap_tai_khoan_vi.txt |

> **Query #5** yêu cầu **metadata filtering** (`language=vi`): nếu không lọc, phiên bản tiếng Anh `faq_account_setup.txt` có thể lẫn vào top-3. Đây là query bắt buộc dùng `search_with_filter()`.

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** __ / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
