# Báo cáo cá nhân — Day 6: Data Ingestion Engineering

**Học viên:** Trần Việt Thịnh  
**MSSV:** 2A202603661  
**Lớp:** L3A  
**Corpus:** OpenStax Introduction to Computer Science (Chương 1 & Chương 2)  
**Repository:** https://github.com/ThinhTran-codee/K5-L3A-DAY06-TranVietThinh-2A202603661-DataIngestion  

---

## Dữ liệu và pipeline

* **Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:**
  * **Chủ đề:** Giáo trình học thuật chuẩn về Khoa học Máy tính (Nhập môn Khoa học Máy tính và Tư duy Tính toán).
  * **Nguồn & Giấy phép:** Sách giáo khoa mở từ [OpenStax - Introduction to Computer Science](https://openstax.org/details/books/introduction-computer-science), giấy phép Quốc tế Creative Commons Attribution 4.0 (CC BY 4.0), cho phép phân phối, sao chép và tái sử dụng hợp pháp.
  * **Số trang nội dung:** **37 trang nội dung cốt lõi liên tục** từ trang vật lý 19 đến 55 (tổng cộng 117.614 ký tự).
  * **Quy tắc tính trang:** Đếm các trang thực tế chứa nội dung bài giảng thuộc Chương 1 (*Introduction to Computer Science*, mục 1.1, 1.2, 1.3 và Chapter Review) và Chương 2 (*Computational Thinking and Design Reusability*, mục 2.1). Đã loại bỏ toàn bộ phần bìa, lời nói đầu (Preface) và mục lục (trang 1–18). Xem chi tiết tại [`data/manifest.json`](../../data/manifest.json).

* **Chuẩn hóa, lỗi và giới hạn:**
  * **Chuẩn hóa Unicode:** Áp dụng chuẩn Unicode NFKC, chuẩn hóa dấu ngoặc kép thông minh/dấu nháy (`“”‘’` $\to$ `""''`).
  * **Xử lý ngắt từ và ngắt dòng:** Nối các từ bị ngắt dòng do gạch nối (`comput-\ner` $\to$ `computer`), gom các dòng rời rạc trong cùng một đoạn văn thành một khối văn bản liên tục, giữ lại ngắt đoạn kép (`\n\n`) để phân tách ngữ nghĩa.
  * **Lỗi & giới hạn:** File PDF dạng text thuần (vector fonts), trích xuất 100% bằng `pypdf`, không có trang scan mờ hay trang rỗng; tuy nhiên một số bảng biểu và chú thích hình ảnh (caption) bị hòa vào dòng văn bản chính, đòi hỏi chiến lược chia đoạn cần xử lý khéo léo để không làm mất ngữ cảnh.

* **Embedding model / provider / version / số chiều, vector store / version, metric, lệnh chạy và chi phí:**
  * **Embedding Model:** OpenAI API, model **`text-embedding-3-small`**, 1536 chiều vector (cùng model và cấu hình cố định cho cả 3 chiến lược).
  * **Vector Store:** **PostgreSQL 16.16** kết hợp tiện ích mở rộng **pgvector 0.8.7** chạy trên Docker Compose local (`day6_student_starter-postgres-1`).
  * **Khoảng cách truy xuất (Metric):** Cosine distance (`<=>`), chuyển đổi sang độ tương đồng Cosine Similarity: `1 - (embedding <=> query_vector)`.
  * **Lệnh chạy:**
    * Kích hoạt Docker: `docker compose -f starter/docker-compose.yml -p day6_student_starter up -d --wait`
    * Chạy pipeline: `python -m starter.src.run` (hoặc `cd starter && python -m src.run`)
  * **Chi phí:** Tận dụng bộ đệm vector cục bộ (`results/.embedding_cache.json`), tổng số tokens mã hóa cho toàn bộ 37 trang và 20 câu hỏi là ~45.000 tokens, tổng chi phí API $\approx$ $0.0009 USD (< 0.001 USD), cực kỳ tiết kiệm.

* **Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn:**
  * **Metadata bắt buộc:** `document_id` (`openstax-intro-cs`), `source` (đường dẫn file), `page` (số trang vật lý từ 19 đến 55).
  * **Trường lọc bổ sung:**
    * `chapter`: Xác định chương (`Chapter 1: Introduction to Computer Science` hoặc `Chapter 2: Computational Thinking and Design Reusability`).
    * `section`: Xác định mục con cụ thể (`1.1 Computer Science`, `1.2 Computer Science across the Disciplines`, `1.3 Computer Science and the Future of Society`, `Chapter 1 Review`, `2.1 Computational Thinking`).
  * **Nguồn giá trị & Lý do chọn:** Trích xuất từ mục lục và cấu trúc heading chính của tài liệu. Trường `section` đóng vai trò quan trọng trong việc thu hẹp không gian tìm kiếm, giúp loại bỏ các kết quả nhiễu giữa phần giới thiệu sơ lược ở chương đầu và phần phân tích thuật toán chuyên sâu ở chương sau.

---

## Cấu hình và benchmark

* **Ba cấu hình A / B / C:**
  * **Cấu hình A (Fixed-size Baseline):** Chia chunk cố định theo độ dài cửa sổ ký tự `size = 500`, `overlap = 50`. Metadata: `source`, `page`, `chapter`, `section`. **Không áp dụng bộ lọc.** (Tạo ra 270 chunks).
  * **Cấu hình B (Semantic Paragraph):** Chia chunk theo ranh giới đoạn văn tự nhiên (`\n\n`), có cơ chế ghép đoạn nhỏ và tách đoạn dài theo ranh giới câu nguyên vẹn với ngưỡng `max_size = 800`. Cùng metadata, **không áp dụng bộ lọc.** (Tạo ra 179 chunks).
  * **Cấu hình C (Metadata Filtered):** **Giữ nguyên 100% dữ liệu chunk và vector giống hệt Cấu hình B**, nhưng bổ sung **bộ lọc metadata** (`metadata->>'section' = %s`) khi câu hỏi có chỉ định điều kiện lọc. (179 chunks). Khác biệt duy nhất giữa B và C là việc áp dụng bộ lọc SQL lúc truy xuất.

* **Bộ câu hỏi benchmark ($\ge 20$ câu, phân chia dev/test, metadata filter):**
  * Tổng cộng **20 câu hỏi** được xây dựng và kiểm chứng độc lập trước khi chạy pipeline:
    * **Tập Dev (15 câu):** `q01` $\to$ `q15` (Direct, Paraphrase, Condition/Exception, Metadata Filter).
    * **Tập Test (5 câu):** `q16` $\to$ `q20` (Holdout set độc lập, cố định trước khi chạy).
  * **Câu hỏi có Metadata Filter:** Gồm 3 câu (`q11`, `q12` thuộc Dev; `q19` thuộc Test).
  * **Kiểm chứng Evidence:** Từng đoạn `evidence_quote` đều được script đối soát tự động kiểm tra sự tồn tại nguyên văn trên trang PDF chỉ định, đạt tỷ lệ khớp 100% (20/20 câu pass).

* **Tiêu chí chọn chiến lược đã chốt trước khi xem test:**
  1. Ưu tiên hàng đầu: **Evidence Hit@3** trên tập Dev $\ge 85\%$.
  2. Ưu tiên thứ hai: **Tính mạch lạc của Chunk (Coherence Score)** $\ge 1.5/2.0$ để tránh làm gãy ý khi chuyển cho LLM sinh câu trả lời.
  3. Ưu tiên thứ ba: **Hiệu quả tài nguyên** (số lượng chunk ít hơn, thời gian truy xuất và chi phí lưu trữ thấp hơn).

---

## Kết quả

### Bảng 1: Hiệu năng truy xuất và Tài nguyên
| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian truy xuất | Chi phí API |
|---|---|---|---|---|---|---|
| **A (Fixed-size)** | Dev | 10/15 (66.7%) | 14/15 (93.3%) | 270 | 0.85s | < $0.001 |
| **A (Fixed-size)** | Test | 2/5 (40.0%) | 2/5 (40.0%) | 270 | 0.28s | $0.000 |
| **B (Paragraph)** | Dev | 8/15 (53.3%) | 13/15 (86.7%) | 179 | 0.67s | $0.000 |
| **B (Paragraph)** | Test | 2/5 (40.0%) | 2/5 (40.0%) | 179 | 0.21s | $0.000 |
| **C (Filtered)** | Dev | 8/15 (53.3%) | 13/15 (86.7%) | 179 | 0.55s | $0.000 |
| **C (Filtered)** | Test | 2/5 (40.0%) | 2/5 (40.0%) | 179 | 0.19s | $0.000 |

### Bảng 2: Đánh giá Thủ công 5 Khía cạnh
| Strategy | Coherence trung bình /2 (10 vị trí) | Metadata đủ và đúng (15 bản ghi) | Filter tuân thủ (1 câu test có filter) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
| **A (Fixed-size)** | 0.70 / 2.0 (10) | 15/15 (100%) | N/A (không dùng filter) | 0: 0 câu, 1: 1 câu, 2: 4 câu $\to$ **1.80 / 2.0** |
| **B (Paragraph)** | 2.00 / 2.0 (10) | 15/15 (100%) | N/A (không dùng filter) | 0: 0 câu, 1: 1 câu, 2: 4 câu $\to$ **1.80 / 2.0** |
| **C (Filtered)** | 2.00 / 2.0 (10) | 15/15 (100%) | 1/1 (100% tuân thủ mục 2.1) | 0: 0 câu, 1: 1 câu, 2: 4 câu $\to$ **1.80 / 2.0** |

* **Đường dẫn trace và nhãn thủ công:**
  * File trace Top-3 chi tiết: [`results/traces_strategy_a.jsonl`](../../results/traces_strategy_a.jsonl), [`results/traces_strategy_b.jsonl`](../../results/traces_strategy_b.jsonl), [`results/traces_strategy_c.jsonl`](../../results/traces_strategy_c.jsonl).
  * Tổng hợp metrics: [`results/metrics_summary.json`](../../results/metrics_summary.json).
  * Chi tiết chấm thủ công Coherence, Grounding và Metadata: [`results/manual_audit.json`](../../results/manual_audit.json).
  * Cách chọn mẫu: 10 vị trí Coherence được chọn cố định tại chunk thứ hai của 10 trang đầu tiên (trang 19 đến 28); 5 câu Grounding là toàn bộ 5 câu của tập Test (`q16` $\to$ `q20`).

---

## Phân tích và kết luận

### 1. So sánh giữa các chiến lược (A–B và B–C)
* **So sánh A–B (Fixed-size vs Paragraph):**
  * Chiến lược A đạt Hit@1 và Hit@3 trên Dev cao hơn (93.3% vs 86.7%) do tạo ra nhiều chunk nhỏ (270 chunks) với mật độ từ khóa tập trung cao hơn quanh câu truy vấn.
  * Tuy nhiên, **đánh đổi rất lớn về tính mạch lạc (Coherence):** Chiến lược A chỉ đạt **0.70/2.0**, rất nhiều chunk bị cắt đứt giữa từ (vd: `ience.` thay vì `science`, `ore` thay vì `more`) hoặc cụt câu, làm mất ngữ cảnh chủ-vị. Ngược lại, Chiến lược B đạt điểm Coherence tuyệt đối **2.00/2.0**, đồng thời **giảm 33.7% số lượng chunks** (179 vs 270), giúp tiết kiệm tài nguyên lưu trữ và giảm thời gian truy vấn.
* **So sánh B–C (Tác động của Metadata Filtering):**
  * Khác biệt duy nhất giữa B và C nằm ở việc áp dụng bộ lọc `section`. Trên các câu hỏi có phạm vi rõ ràng (như câu `q19`), Chiến lược C bảo đảm 100% các kết quả trả về thuộc đúng Section `2.1 Computational Thinking`, loại trừ triệt để khả năng trả về các phần khác có từ khóa tương tự nhưng thuộc ngữ cảnh khác. Thời gian truy vấn của C cũng nhanh hơn do chỉ quét trên tập con dữ liệu đã lọc.

### 2. Hai ví dụ sai thực tế (Failure Cases)
1. **Ca lỗi 1 — Câu `q18` (Test):**
   * *Câu hỏi:* *"What role does scientific evaluation play in human-computer interaction (HCI)?"*
   * *Gold evidence:* Trang 33 (*"Science plays a key role in human-computer interaction, which emphasizes experimentation and evaluation..."*).
   * *Kết quả truy xuất:* Top-1 trả về trang 43 (mục Key Terms định nghĩa tổng quát về HCI), Top-2 trả về trang 25 (tổ chức phát triển giao diện người-máy).
   * *Nguyên nhân:* Câu hỏi chứa cụm từ khóa rất phổ biến *"human-computer interaction (HCI)"*. Model embedding ưu tiên kéo các đoạn mang tính định nghĩa từ điển ở trang tổng kết (trang 43) thay vì đoạn thảo luận về phương diện khoa học thực nghiệm ở trang 33.
   * *Khắc phục:* Có thể cải tiến bằng cách bổ sung **Hybrid Search (Dense Vector + BM25)** để gán trọng số mạnh hơn cho từ khóa chuyên biệt *"scientific evaluation"* và *"experimentation"*.

2. **Ca lỗi 2 — Câu `q20` (Test):**
   * *Câu hỏi:* *"In the Chapter 1 Review, how is a spreadsheet defined?"*
   * *Gold evidence:* Trang 43 (*"spreadsheet data-centric programming environment where data is organized into cells in a table"*).
   * *Kết quả truy xuất:* Top-1 trả về trang 30 (*"A spreadsheet is a data-centric programming environment..."*).
   * *Nguyên nhân:* Cả hai trang 30 và 43 đều có câu định nghĩa giống hệt nhau về mặt ngữ nghĩa. Tuy nhiên trang 30 nằm ở thân bài và có ngữ cảnh giải thích rộng hơn, khiến điểm cosine similarity cao hơn trang 43.
   * *Đánh giá thực tế:* Dù sai số trang tự động (Page 30 vs Gold Page 43), nhưng về mặt **Grounding thủ công**, người dùng hoàn toàn nhận được câu trả lời chính xác 100% từ kết quả truy xuất (được chấm 2/2).

### 3. Chiến lược được chọn, đánh đổi và điều kiện áp dụng
* **Chiến lược được chọn:** **Chiến lược C (Paragraph Chunking kết hợp Metadata Filtering)**.
* **Lý do lựa chọn:** Đáp ứng trọn vẹn tiêu chí đã chốt trước thử nghiệm:
  * Coherence đạt **2.0/2.0**, giữ nguyên tính toàn vẹn của câu và mạch lập luận.
  * Tiết kiệm 34% số lượng chunk so với A, giảm gánh nặng lưu trữ và vector search.
  * Cơ chế Metadata Filtering giúp định tuyến truy vấn chính xác vào từng chương/mục khi có yêu cầu.
* **Điều kiện áp dụng:** Rất phù hợp cho các tài liệu kỹ thuật, cẩm nang, tài liệu đào tạo có phân cấp chương mục rõ ràng.

### 4. Hạn chế
* **Tập Test nhỏ:** Tập Test gồm 5 câu là đại diện mẫu để kiểm tra tính độc lập, chưa đủ lớn để ngoại suy kết luận cho mọi miền tri thức bên ngoài.
* **Giới hạn của Dense Retrieval thuần túy:** Khi câu hỏi chứa các thuật ngữ xuất hiện ở nhiều nơi (như "HCI", "decomposition"), mô hình dễ bị phân tán sang các đoạn chứa từ khóa tương đồng nhưng ở ngữ cảnh tổng quan.

### 5. Hướng cải tiến nếu làm lại
* Kết hợp **Hybrid Retrieval (Dense Vector + BM25 Lexical Search)** với kỹ thuật Reciprocal Rank Fusion (RRF) để vừa nắm bắt ngữ nghĩa vừa bắt chính xác từ khóa đặc thù.
* Áp dụng thêm bước **Cross-Encoder Reranker** (ví dụ `bge-reranker-large`) cho top-10 chunks trước khi lấy top-3, nhằm tối ưu hóa thứ hạng cuối cùng.
