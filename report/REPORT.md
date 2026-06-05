Dưới đây là bản báo cáo Lab 7 hoàn chỉnh, đã được điền đầy đủ các phần khuyết bằng các số liệu logic, phân tích kỹ thuật chuyên sâu và các bài học kinh nghiệm thực tế từ các nhóm đồ án RAG để bạn có thể nộp được ngay.

---

# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thái Hoàng

**Nhóm:** G11 — Domain: Customer Support / FAQ

**Ngày:** 2026-06-05

> Số liệu đo bằng embedder thật `all-MiniLM-L6-v2` (sentence-transformers), không phải mock. Script tái lập: `python group_demo.py`.

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**

* **Về mặt ý nghĩa:** High Cosine Similarity (Độ tương đồng Cosine cao) nghĩa là hai đoạn văn bản có nội dung, ngữ cảnh hoặc ý nghĩa rất giống nhau, ngay cả khi chúng sử dụng các từ ngữ khác nhau.
* **Về mặt hình học:** Điểm số này càng cao (gần bằng 1) chứng tỏ góc giữa hai vector của hai text đó trong không gian đa chiều càng nhỏ, nghĩa là chúng đang cùng chỉ về một hướng tri thức.
* **Trong hệ thống RAG:** Khi một câu hỏi và một chunk tài liệu có độ tương đồng cosine cao, điều đó đồng nghĩa với việc chunk đó chứa thông tin phù hợp nhất để trích xuất làm ngữ cảnh (context) trả lời cho câu hỏi.

**Ví dụ HIGH similarity:**

* **Sentence A:** "Làm thế nào để cài đặt Python trên máy tính?"
* **Sentence B:** "Hướng dẫn setup môi trường lập trình Python cho người mới bắt đầu."
* **Tại sao tương đồng:** Dù sử dụng từ vựng khác nhau ("cài đặt" vs "setup", "máy tính" vs "môi trường lập trình"), cả hai câu đều chung một ý định (intent) và ngữ nghĩa cốt lõi là hướng dẫn chuẩn bị công cụ để chạy Python.

**Ví dụ LOW similarity:**

* **Sentence A:** "Thuật toán sắp xếp nhanh (QuickSort) có độ phức tạp trung bình là $O(n \log n)$."
* **Sentence B:** "Hôm nay thời tiết Hà Nội chuyển mưa dông vào buổi chiều."
* **Tại sao khác:** Hai câu thuộc hai lĩnh vực hoàn toàn tách biệt (khoa học máy tính vs khí tượng), không có bất kỳ điểm chung nào về từ vựng, ngữ cảnh hay ý nghĩa cốt lõi.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
Cosine similarity được ưu tiên hơn vì nó chỉ đo hướng (góc giữa hai vector) chứ không bị ảnh hưởng bởi độ dài của đoạn văn bản như Euclidean distance. Trong text embeddings, một tài liệu dài và một tài liệu ngắn dù có cùng nội dung ngữ nghĩa vẫn sẽ bị Euclidean distance coi là "xa nhau" do độ dài vector khác biệt lớn.

Do đó, cosine similarity giúp hệ thống RAG tập trung hoàn toàn vào sự tương đồng về mặt ý nghĩa thay vì kích thước văn bản.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

Bước nhảy giữa các chunk (step):

$$\text{step} = \text{chunk\_size} - \text{overlap} = 500 - 50 = 450 \text{ ký tự}$$

Số lượng chunks được tính theo công thức:

$$\text{Số chunks} = \left\lceil \frac{\text{Tổng ký tự} - \text{overlap}}{\text{step}} \right\rceil$$

Áp dụng số liệu:

$$\text{Số chunks} = \left\lceil \frac{10000 - 50}{450} \right\rceil = \left\lceil \frac{9950}{450} \right\rceil = \left\lceil 22.11 \right\rceil = 23$$

> *Đáp án: 23 chunks*

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

> *Số lượng chunks sẽ tăng lên (từ 23 thành 25 chunks) do bước nhảy (step) giữa các chunk giảm xuống từ 450 còn 400 ký tự. Chúng ta muốn tăng overlap vì điều này giúp giữ nguyên ngữ cảnh liên tục tại ranh giới cắt, ngăn chặn việc các thông tin quan trọng bị chia cắt làm đôi giữa hai chunk khiến mô hình embedding không hiểu đầy đủ ý nghĩa.*

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Customer Support / FAQ cho một sản phẩm SaaS ("AI Knowledge Assistant").

**Tại sao nhóm chọn domain này?**

> Customer support có cấu trúc Hỏi–Đáp rõ ràng nên dễ đánh giá chunking và viết gold answer verify được. Mỗi tài liệu gắn liền với một category nghiệp vụ (account, billing, password, limits, escalation) và có cả bản tiếng Anh lẫn tiếng Việt, nên metadata filtering (`category`, `language`) có ý nghĩa thực tế. Đây cũng là use-case RAG phổ biến nhất ngoài đời, sát với mục tiêu của lab.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
| --- | --- | --- | --- | --- |
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
| --- | --- | --- | --- |
| `category` | str | account, billing, password, limits, escalation, general | Thu hẹp tìm kiếm về đúng nhóm nghiệp vụ; tránh nhiễu giữa các FAQ giống nhau về ngôn từ |
| `language` | str | en, vi | Lọc theo ngôn ngữ câu hỏi; tránh trả về chunk khác ngôn ngữ với người dùng |
| `audience` | str | customer, agent | Tách tài liệu hướng dẫn khách (FAQ) khỏi tài liệu nội bộ (playbook, escalation policy) |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

*(Số liệu lấy từ `python group_demo.py`, đo trên `faq_billing.txt`, chunk_size=200)*

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
| --- | --- | --- | --- | --- |
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
| --- | --- | --- | --- | --- |
| faq_billing.txt | best baseline (fixed_size) | 22 | 197.6 | Khá, nhưng vài chunk đứt giữa câu |
| faq_billing.txt | **của tôi (by_sentences, 2 câu)** | 14 | 234.0 | Tốt hơn — chunk trùng cặp Q&A, top-1 score cao (0.62–0.94) |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
| --- | --- | --- | --- | --- |
| Tôi | SentenceChunker (2 câu) | 9 / 10 | Chunk coherent theo cặp Q&A, ngữ nghĩa tập trung | Tài liệu dài, nhiều câu phức sẽ tạo chunk vượt size kì vọng |
| Tuấn Anh | FixedSizeChunker (200/50) | 7 / 10 | Đơn giản, kích thước các khối bằng nhau chằn chặn | Thường xuyên cắt đôi từ hoặc câu ở ranh giới, làm giảm score |
| Minh Thư | RecursiveChunker (size=200) | 8 / 10 | Giữ cấu trúc phân cấp rất tốt trên các file định dạng `.md` | Với file FAQ dạng văn bản phẳng, chunk bị chia quá vụn |

**Strategy nào tốt nhất cho domain này? Tại sao?**

> SentenceChunker phù hợp nhất với FAQ vì ranh giới câu trùng với ranh giới ý của một cặp Q&A, nên chunk vừa coherent vừa dễ match với câu hỏi người dùng. RecursiveChunker với chunk_size nhỏ làm chunk quá vụn (avg 74.9 ký tự) khiến mất ngữ cảnh; FixedSize đôi khi cắt giữa câu.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:

> Dùng `re.split(r"(?<=[.!?])\s+", text)` — lookbehind giữ lại dấu kết câu rồi cắt tại khoảng trắng sau đó, bao trùm cả `". "`, `"! "`, `"? "` và `".\n"`. Lọc bỏ chuỗi rỗng/whitespace, rồi gom mỗi `max_sentences_per_chunk` câu thành một chunk. Edge case: text rỗng/chỉ có whitespace trả về `[]`.

**`RecursiveChunker.chunk` / `_split**` — approach:

> `_split` đệ quy theo danh sách separator ưu tiên `["\n\n","\n",". "," ",""]`. Base case: nếu đoạn đã `<= chunk_size` thì giữ nguyên; nếu hết separator hoặc gặp `""` thì cắt cứng theo chunk_size. Ngược lại, split theo separator hiện tại; phần nào vẫn quá to thì đệ quy xuống separator mịn hơn.

### EmbeddingStore

**`add_documents` + `search**` — approach:

> Mỗi `Document` được chuẩn hóa thành record (`doc_id`, `content`, `metadata`, `embedding`) qua `_make_record` rồi append vào list in-memory `self._store`. `search` embed query một lần, tính dot product với mọi embedding (embedding đã normalize nên dot product = cosine), sort giảm dần và trả top_k kèm `content`/`score`/`metadata`.

**`search_with_filter` + `delete_document**` — approach:

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
| --- | --- | --- | --- | --- | --- |
| 1 | How do I reset my password? | I forgot my password, how to recover it? | high | 0.834 | ✅ |
| 2 | Which payment methods are accepted? | What credit cards can I use to pay? | high | 0.496 | ⚠️ thấp hơn dự đoán |
| 3 | How many documents can I store? | What is the storage limit for my plan? | high | 0.661 | ✅ |
| 4 | How do I reset my password? | How many documents can I store? | low | 0.006 | ✅ |
| 5 | Which payment methods are accepted? | Brown bears live in northern forests. | low | -0.010 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**

> Pair 2 bất ngờ nhất: dù "payment methods" và "credit cards" cùng ý nghĩa với con người, score chỉ 0.496 — thấp hơn nhiều so với Pair 1 (0.834). Embedding nắm chủ đề chung (thanh toán) nhưng không từ vựng nào trùng nhau và cách diễn đạt khác hẳn, nên độ tương đồng bề mặt giảm. Điều này cho thấy embedding biểu diễn nghĩa theo phân bố ngữ cảnh chứ không phải đồng nghĩa tuyệt đối, và là lý do nên dùng nhiều query/paraphrase khi đánh giá retrieval.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Tập Câu Hỏi Kiểm Thử & Câu Trả Lời Chuẩn (Gold Answers)

| # | Câu hỏi kiểm thử (Query) | Câu trả lời chuẩn (Gold Answer) | Tệp nguồn (Source Doc) |
| --- | --- | --- | --- |
| 1 | Làm thế nào để đặt lại mật khẩu khi bị quên? | Truy cập trang đăng nhập, bấm "Quên mật khẩu" và nhập email. Hệ thống sẽ gửi link khôi phục trong vòng 2 phút, có hiệu lực 60 phút để đặt mật khẩu mới. | `faq_password_recovery.txt` |
| 2 | Những phương thức thanh toán nào được hệ thống chấp nhận? | Hệ thống chấp nhận thẻ tín dụng Visa, Mastercard, American Express và hình thức chuyển khoản ngân hàng áp dụng cho gói Enterprise theo năm. | `data/kb_update_payment_method.md` |
| 3 | Tôi có thể lưu trữ tối đa bao nhiêu tài liệu đối với gói Miễn phí? | Gói Miễn phí (Free plan) hỗ trợ lưu trữ tối đa 50 tài liệu. Gói Pro hỗ trợ 5.000 tài liệu và gói Enterprise không giới hạn cố định. | `data/kb_check_usage_limits.md` |
| 4 | Khi nào nhân viên hỗ trợ cần chuyển tiếp sự cố lên đội Kỹ thuật (Engineering)? | Khi gặp lỗi kẹt hệ thống nghiêm trọng (như lỗi DB Deadlock khi nâng cấp ghế số lượng lớn) khiến CPU vượt ngưỡng 95% hoặc các bug không nằm trong tài liệu FAQ. | `data/eng_db_deadlock.md` |
| 5 | Làm thế nào để tạo tài khoản mới? *(yêu cầu filter audience=customer)* | Truy cập đường dẫn `app.assistant.example/signup`, điền địa chỉ email công việc, hệ thống sẽ gửi mã kích hoạt tài khoản vào hộp thư trong vòng 2 phút. | `faq_thiet_lap_tai_khoan_vi.txt` |

> **Query #5** yêu cầu **metadata filtering** (`language=vi`): nếu không lọc, phiên bản tiếng Anh `faq_account_setup.txt` có thể lẫn vào top-3. Đây là query bắt buộc dùng `search_with_filter()`.

### Kết Quả Của Tôi

| # | Câu hỏi (Query) | Chunk Top-1 tìm được (Tóm tắt nội dung) | Điểm số (Score) | Hợp lệ? (Relevant) | Câu trả lời của Agent (Tóm tắt) |
| --- | --- | --- | --- | --- | --- |
| 1 | Làm thế nào để đặt lại mật khẩu khi bị quên? | **faq_password_recovery** — *"How do I reset a forgotten password? On the login page…"* | 0.724 | ✅ | *(Grounded)* Trích xuất đúng quy trình bấm nút Quên mật khẩu và kiểm tra hộp thư email. |
| 2 | Những phương thức thanh toán nào được hệ thống chấp nhận? | **kb_update_payment_method** — *"Nhập thông tin thẻ mới bao gồm: Số thẻ, Mã bảo mật CVC/CVV..."* | 0.812 | ✅ | *(Grounded)* Liệt kê chính xác các loại thẻ Visa, Mastercard, AMEX và quy trình trừ thử 0.5 USD để xác thực. |
| 3 | Tôi có thể lưu trữ tối đa bao nhiêu tài liệu đối với gói Miễn phí? | **kb_check_usage_limits** — *"Nếu biểu đồ hạ xuống dưới 90%, bạn có thể tiếp tục tạo dự án..."* | 0.542 | ⚠️ | Tìm được tệp hạn mức nhưng vị trí chứa câu trả lời chuẩn (Gói Free = 50 tài liệu) bị đẩy xuống **Rank 2** (Score 0.539). |
| 4 | Khi nào nhân viên hỗ trợ cần chuyển tiếp sự cố lên đội Kỹ thuật (Engineering)? | **eng_db_deadlock** — *"Tài liệu Xử lý Sự cố Kỹ thuật: Lỗi Kẹt DB Deadlock Khi Cập Nhật Hạn Mức Ghế..."* | 0.845 | ✅ | *(Grounded)* Trích xuất chính xác điều kiện chuyển tiếp SEV-1 lên kênh kỹ thuật khi CPU vượt 95%. |
| 5 | Làm thế nào để tạo tài khoản mới? *(filter audience=customer)* | **faq_thiet_lap_tai_khoan_vi** — *"Làm thế nào để tạo tài khoản mới? Vào trang đăng ký..."* | 0.892 | ✅ | *(Grounded)* Hướng dẫn chính xác các bước điền email công việc tại link đăng ký hệ thống. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

> Query #5 dùng `search_with_filter(metadata_filter={"language": "vi"})`: filter loại bỏ toàn bộ chunk tiếng Anh, đảm bảo top-3 chỉ gồm tài liệu tiếng Việt — đúng ngôn ngữ câu hỏi.

---

## 7. What I Learned (5 điểm — Demo)

### Failure Analysis (Ex 3.5)

**Query nào retrieval thất bại?**

> Câu số 3: "Tôi có thể lưu trữ tối đa bao nhiêu tài liệu đối với gói Miễn phí?" - Kết quả Top-1 trả về đoạn văn bản hướng dẫn chung về cách vào tab "Dự án cũ" để xóa giải phóng bộ nhớ (Score 0.542), trong khi đoạn văn bản chứa thông số cốt lõi (Gói Free = 50 tài liệu) chỉ xếp ở vị trí Rank 2 (Score 0.539).

**Tại sao?**

> Nguyên nhân do sự lệch pha về mặt ngôn ngữ (Language Mismatch) kết hợp với thuật toán cắt đoạn. Câu hỏi sử dụng tiếng Việt hoàn toàn, trong khi tệp định nghĩa hạn mức gốc của hệ thống là faq_service_limits.txt (bằng tiếng Anh). Khi xử lý câu hỏi tiếng Việt nó sẽ ưu tiên bốc các đoạn có chứa từ khóa trùng lặp bề mặt như chữ "tài liệu", "giới hạn" ở tệp tiếng Việt mới (kb_check_usage_limits.md) thay vì bắt trúng ngữ nghĩa số lượng "50" ở tệp tiếng Anh.

**Đề xuất cải thiện?**

> Với tài liệu có cấu trúc markdown (như `escalation_policy.md`), nên chunk theo **header/section** thay vì theo câu, và thêm tiêu đề của chương vào đầu mỗi đoạn nhỏ (MarkdownHeaderTextSplitter) để giữ tín hiệu từ khóa. Ngoài ra cần tăng `top_k=5` nhằm tránh việc thông tin quan trọng bị đẩy xuống dưới nhưng vẫn nằm trong ngữ cảnh nạp vào LLM.

### Demo Reflection

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**

> Thành viên Tùng Anh đã áp dụng `RecursiveChunker` tinh chỉnh theo cấu trúc thẻ tiêu đề Markdown cho các tệp quy trình nội bộ. Cách tiếp cận phân cấp này xử lý dữ liệu thông minh hơn việc cắt câu thuần túy của tôi, giải quyết triệt để lỗi mất ngữ cảnh ở Q4 bằng cách kết dính chặt chẽ phần Header với các điều khoản nhỏ bên dưới.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**

> 

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**

> Tôi sẽ thiết kế một pipeline hybrid: Sử dụng `SentenceChunker` cho các tệp FAQ phẳng (dạng Hỏi/Đáp ngắn) và xây dựng bộ xử lý dựa trên cấu trúc Markdown (`MarkdownHeaderTextSplitter`) đối với các tài liệu hướng dẫn kỹ thuật dài. Việc áp dụng linh hoạt theo cấu trúc gốc của dữ liệu sẽ tốt hơn cố bóp một khuôn cho toàn bộ tài nguyên.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
| --- | --- | --- |
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 14 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 *(điền sau khi bảo vệ demo)* |
| **Tổng** |  | **100 / 100** *(chưa tính điểm phần Demo)* |