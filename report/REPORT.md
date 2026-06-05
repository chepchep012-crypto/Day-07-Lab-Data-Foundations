# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đức Toàn
**Nhóm:** G11 — Domain: Customer Support / FAQ
**Ngày:** 2026-06-05

> Số liệu đo bằng embedder thật `all-MiniLM-L6-v2` (sentence-transformers), không phải mock. Script tái lập: `python group_demo.py`.

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai chunk có cosine similarity cao nghĩa là vector embedding của chúng chỉ về gần cùng một hướng trong không gian nghĩa — tức chúng nói về cùng chủ đề/ý, bất kể độ dài văn bản.

**Ví dụ HIGH similarity:**
- Sentence A: "How do I reset my password?"
- Sentence B: "I forgot my password, how can I recover it?"
- Tại sao tương đồng: Cùng ý định (khôi phục mật khẩu), cùng trường từ vựng → vector gần nhau (đo thực tế: 0.834).

**Ví dụ LOW similarity:**
- Sentence A: "Which payment methods are accepted?"
- Sentence B: "Brown bears live in northern forests."
- Tại sao khác: Khác hoàn toàn chủ đề, không chung ngữ cảnh → vector gần như trực giao (đo thực tế: -0.010).

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine chỉ quan tâm **hướng** của vector chứ không quan tâm độ lớn, nên không bị ảnh hưởng bởi độ dài văn bản (chunk dài có vector lớn hơn). Hai đoạn cùng nghĩa nhưng khác độ dài vẫn được coi là tương đồng, trong khi Euclidean sẽ phạt sự chênh lệch độ lớn.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> Đáp án: **23 chunks**.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks` — tăng từ 23 lên **25**. Overlap nhiều hơn giúp giữ ngữ cảnh vắt qua ranh giới chunk (câu/ý bị cắt vẫn xuất hiện trọn vẹn ở chunk kế), giảm rủi ro mất thông tin khi retrieve, đổi lại tốn thêm lưu trữ và tính toán.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Customer Support / FAQ cho một sản phẩm SaaS ("AI Knowledge Assistant").

**Tại sao nhóm chọn domain này?**
> Customer support có cấu trúc Hỏi–Đáp rõ ràng nên dễ đánh giá chunking và viết gold answer verify được. Mỗi tài liệu gắn liền với một category nghiệp vụ (account, billing, password, limits, escalation) và có cả bản tiếng Anh lẫn tiếng Việt, nên metadata filtering (`category`, `language`) có ý nghĩa thực tế. Đây cũng là use-case RAG phổ biến nhất ngoài đời, sát với mục tiêu của lab.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | customer_support_playbook.txt | Nhóm soạn (mở rộng từ mẫu) | 2959 | category=general, language=en, audience=agent |
| 2 | faq_account_setup.txt | Nhóm tự soạn | 2983 | category=account, language=en, audience=customer |
| 3 | faq_billing.txt | Nhóm tự soạn | 3298 | category=billing, language=en, audience=customer |
| 4 | faq_password_recovery.txt | Nhóm tự soạn | 2995 | category=password, language=en, audience=customer |
| 5 | faq_service_limits.txt | Nhóm tự soạn | 2760 | category=limits, language=en, audience=customer |
| 6 | faq_thiet_lap_tai_khoan_vi.txt | Nhóm tự soạn (VI) | 3790 | category=account, language=vi, audience=customer |
| 7 | faq_thanh_toan_vi.txt | Nhóm tự soạn (VI) | 3995 | category=billing, language=vi, audience=customer |
| 8 | escalation_policy.md | Nhóm tự soạn | 2835 | category=escalation, language=en, audience=agent |

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

*(Số liệu lấy từ `python group_demo.py`, đo trên `faq_billing.txt`, chunk_size=200)*

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| faq_billing.txt | FixedSizeChunker (`fixed_size`) | 22 | 197.6 | Trung bình — cắt giữa câu, có thể đứt ý |
| faq_billing.txt | SentenceChunker (`by_sentences`) | 14 | 234.0 | Tốt — chunk trùng ranh giới câu/Q&A |
| faq_billing.txt | RecursiveChunker (`recursive`) | 43 | 74.9 | Kém ở đây — chunk quá vụn (tách theo `. `) |

### Strategy Của Tôi

**Loại:** SentenceChunker (`max_sentences_per_chunk=2`)

**Mô tả cách hoạt động:**
> Strategy tách văn bản tại ranh giới câu bằng regex `(?<=[.!?])\s+`, rồi gom mỗi 2 câu thành một chunk. Vì FAQ được viết theo cặp Hỏi–Đáp ngắn (1 câu hỏi + 1-2 câu trả lời), gom 2 câu giúp mỗi chunk thường chứa trọn một cặp Q&A, giữ được ngữ cảnh đủ để retrieve mà không lẫn nhiều chủ đề.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain Customer Support FAQ có đơn vị ngữ nghĩa tự nhiên là **câu/cặp Q&A**, không phải đoạn dài. SentenceChunker khai thác đúng pattern đó: chunk coherent, không cắt giữa câu như FixedSize và không vụn như Recursive. Kết quả benchmark cho thấy top-1 đúng doc ở cả 5/5 query.

**Code snippet (nếu custom):**
```python
# Dùng built-in SentenceChunker với tham số tinh chỉnh cho FAQ:
MY_CHUNKER = SentenceChunker(max_sentences_per_chunk=2)
# 8 docs -> 139 chunks; mỗi chunk ~ 1 cặp Q&A.
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| faq_billing.txt | best baseline (fixed_size) | 22 | 197.6 | Khá, nhưng vài chunk đứt giữa câu |
| faq_billing.txt | **của tôi (by_sentences, 2 câu)** | 14 | 234.0 | Tốt hơn — chunk trùng cặp Q&A, top-1 score cao (0.62–0.94) |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | SentenceChunker (2 câu) | 9 | Chunk coherent theo Q&A, top-1 đúng 5/5 | Doc rất dài có thể tạo chunk hơi to |
| [Tên] | FixedSizeChunker (200/50) | | | |
| [Tên] | RecursiveChunker (chunk_size=200) | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> SentenceChunker phù hợp nhất với FAQ vì ranh giới câu trùng với ranh giới ý của một cặp Q&A, nên chunk vừa coherent vừa dễ match với câu hỏi người dùng. RecursiveChunker với chunk_size nhỏ làm chunk quá vụn (avg 64 ký tự) khiến mất ngữ cảnh; FixedSize đôi khi cắt giữa câu.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Dùng `re.split(r"(?<=[.!?])\s+", text)` — lookbehind giữ lại dấu kết câu rồi cắt tại khoảng trắng sau đó, bao trùm cả `". "`, `"! "`, `"? "` và `".\n"`. Lọc bỏ chuỗi rỗng/whitespace, rồi gom mỗi `max_sentences_per_chunk` câu thành một chunk. Edge case: text rỗng/chỉ có whitespace trả về `[]`.

**`RecursiveChunker.chunk` / `_split`** — approach:
> `_split` đệ quy theo danh sách separator ưu tiên `["\n\n","\n",". "," ",""]`. Base case: nếu đoạn đã `<= chunk_size` thì giữ nguyên; nếu hết separator hoặc gặp `""` thì cắt cứng theo chunk_size. Ngược lại, split theo separator hiện tại; phần nào vẫn quá to thì đệ quy xuống separator mịn hơn.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Mỗi `Document` được chuẩn hóa thành record (`doc_id`, `content`, `metadata`, `embedding`) qua `_make_record` rồi append vào list in-memory `self._store`. `search` embed query một lần, tính dot product với mọi embedding (embedding đã normalize nên dot product = cosine), sort giảm dần và trả top_k kèm `content`/`score`/`metadata`.

**`search_with_filter` + `delete_document`** — approach:
> Filter **trước rồi mới search**: lọc các record có metadata khớp toàn bộ cặp key-value trong `metadata_filter`, sau đó chạy `_search_records` trên tập đã lọc (không filter → dùng nguyên `self._store`). `delete_document` dựng lại list chỉ giữ record có `doc_id` khác, trả `True` nếu kích thước thay đổi.

### KnowledgeBaseAgent

**`answer`** — approach:
> Retrieve top_k chunk qua `store.search`, ghép thành context đánh số `[1] ... [2] ...`, nhúng vào prompt yêu cầu "trả lời CHỈ dựa trên context, nếu thiếu thì nói rõ", rồi gọi `llm_fn(prompt)`. Cách này ép câu trả lời grounded vào tài liệu đã retrieve.

### Test Results

```
$ python -m pytest tests/ -q
..........................................                               [100%]
42 passed, 1 warning in 1.13s
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

*(Đo bằng `compute_similarity` trên embedding `all-MiniLM-L6-v2`, xem `group_demo.py` Section 5)*

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | How do I reset my password? | I forgot my password, how to recover it? | high | 0.834 | ✅ |
| 2 | Which payment methods are accepted? | What credit cards can I use to pay? | high | 0.496 | ⚠️ thấp hơn dự đoán |
| 3 | How many documents can I store? | What is the storage limit for my plan? | high | 0.661 | ✅ |
| 4 | How do I reset my password? | How many documents can I store? | low | 0.006 | ✅ |
| 5 | Which payment methods are accepted? | Brown bears live in northern forests. | low | -0.010 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 2 bất ngờ nhất: dù "payment methods" và "credit cards" cùng nghĩa với con người, score chỉ 0.496 — thấp hơn nhiều so với Pair 1 (0.834). Embedding nắm chủ đề chung (thanh toán) nhưng không từ vựng nào trùng nhau và cách diễn đạt khác hẳn, nên độ tương đồng bề mặt giảm. Điều này cho thấy embedding biểu diễn nghĩa theo phân bố ngữ cảnh chứ không phải đồng nghĩa tuyệt đối, và là lý do nên dùng nhiều query/paraphrase khi đánh giá retrieval.

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

*(Backend: `all-MiniLM-L6-v2`, chunker: SentenceChunker(2), top_k=3 — xem `benchmark_output.txt`)*

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | How do I reset a forgotten password? | faq_password_recovery — "How do I reset a forgotten password? On the login page…" | 0.831 | ✅ | (grounded) "On the login page click 'Forgot password'…submit." |
| 2 | Which payment methods are accepted? | faq_billing — "…Which payment methods are accepted?…" | 0.617 | ✅ | (grounded) "Visa, Mastercard, American Express… + bank transfer" |
| 3 | How many documents can I store on the Free plan? | faq_service_limits — "…The Free plan stores up to 50 documents." | 0.935 | ✅ | (grounded) trích đúng quota Free=50 |
| 4 | When should an agent escalate an issue to Engineering? | escalation_policy — "# Support Escalation Policy… ## Purpose…" | 0.483 | ⚠️ | top-1 là chunk intro; chunk đúng (request ID) ở rank 2 (0.480) |
| 5 | Làm thế nào để tạo tài khoản mới? *(filter language=vi)* | faq_thiet_lap_tai_khoan_vi — "Làm thế nào để tạo tài khoản mới?…" | 0.809 | ✅ | (grounded) "Mở trang đăng ký tại app.assistant.example/signup…" |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

> Query #5 dùng `search_with_filter(metadata_filter={"language": "vi"})`: filter loại bỏ toàn bộ chunk tiếng Anh, đảm bảo top-3 chỉ gồm tài liệu tiếng Việt — đúng ngôn ngữ câu hỏi.

---

## 7. What I Learned (5 điểm — Demo)

### Failure Analysis (Ex 3.5)

**Query nào retrieval thất bại?**
> Q4 "When should an agent escalate an issue to Engineering?" — top-1 lại là chunk mở đầu "# Support Escalation Policy … ## Purpose …" (score **0.483**), trong khi chunk thật sự chứa tiêu chí escalate Engineering ("Always attach the request ID and a screenshot…") chỉ xếp **rank 2** (score **0.480**). Khoảng cách cực sát (0.003) cho thấy chunk tổng quát suýt che mất chunk đúng.

**Tại sao?**
> SentenceChunker tách theo câu nên tiêu đề markdown ("## When to escalate to Engineering") bị gộp/loãng tín hiệu; đồng thời chunk "## Purpose" vô tình chứa nhiều từ khoá của query ("escalate", "specialized team"). Đây là vấn đề **chunk coherence** (ranh giới câu không trùng ranh giới section markdown) và **retrieval precision** (chunk tổng quát lấn át chunk cụ thể).

**Đề xuất cải thiện?**
> Với tài liệu có cấu trúc markdown (như `escalation_policy.md`), nên chunk theo **header/section** thay vì theo câu, và prepend tiêu đề section vào mỗi chunk để tăng tín hiệu. Có thể thêm metadata `section` để filter, và tăng top_k lên 5 để chunk đúng vẫn lọt vào context của agent.

### Demo Reflection

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *(Điền sau buổi so sánh nhóm — ví dụ: thành viên dùng RecursiveChunker theo header cho file .md cho kết quả Q4 tốt hơn strategy theo câu của tôi.)*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *(Điền sau demo liên nhóm.)*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ chunk các file markdown theo section/header thay vì theo câu, và thêm metadata `section` để hỗ trợ filter — nhằm vá đúng failure case Q4 ở trên.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 14 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | _ / 5 *(điền sau demo)* |
| **Tổng** | | **94 / 100** *(chưa tính Demo)* |
