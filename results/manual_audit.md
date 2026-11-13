# Kết quả Audit Thủ Công — 5 Khía Cạnh Đánh Giá

**Corpus:** OpenStax Introduction to Computer Science (37 trang nội dung cốt lõi, p.19–55)  
**Mô hình Embedding:** OpenAI `text-embedding-3-small` (1536 chiều)  
**Vector Store:** PostgreSQL 16 + pgvector local  

---

## 1. Retrieval Accuracy (Độ chính xác truy xuất tự động)

| Chiến lược | Tập dữ liệu | Hit@1 (n/N, %) | Evidence Hit@3 (n/N, %) |
|---|---|---|---|
| **A (Fixed-size 500/50)** | Dev (15 câu) | 10/15 (66.7%) | 14/15 (93.3%) |
| **A (Fixed-size 500/50)** | Test (5 câu) | 2/5 (40.0%) | 2/5 (40.0%) |
| **B (Semantic Paragraph max 800)** | Dev (15 câu) | 8/15 (53.3%) | 13/15 (86.7%) |
| **B (Semantic Paragraph max 800)** | Test (5 câu) | 2/5 (40.0%) | 2/5 (40.0%) |
| **C (Paragraph + Metadata Filter)** | Dev (15 câu) | 8/15 (53.3%) | 13/15 (86.7%) |
| **C (Paragraph + Metadata Filter)** | Test (5 câu) | 2/5 (40.0%) | 2/5 (40.0%) |

*File trace chi tiết:* `results/traces_strategy_a.jsonl`, `results/traces_strategy_b.jsonl`, `results/traces_strategy_c.jsonl`.

---

## 2. Chunk Coherence (Tính mạch lạc của Chunk)
*Phương pháp:* Chọn cố định chunk thứ hai (chunk index 1) của 10 trang đầu tiên (trang 19 đến 28) để đánh giá sự khác biệt rõ nét nhất giữa việc chia cắt cố định (A) và chia theo đoạn văn (B/C).  
*Thang điểm:*  
* **0:** Bị cắt đứt từ/câu, thiếu chủ ngữ/vị ngữ khiến không hiểu được ý trọn vẹn.  
* **1:** Hiểu được một phần, nhưng thiếu ngữ cảnh hoặc bị ngắt lửng câu.  
* **2:** Giữ trọn ý, tự hiểu được, câu cú và ranh giới đoạn văn hoàn chỉnh.  

| Vị trí nguồn | Chiến lược A (Fixed-size) | Điểm A | Chiến lược B/C (Paragraph) | Điểm B/C |
|---|---|:---:|---|:---:|
| **Trang 19** | Bị cắt ở giữa đoạn văn, mất câu mở đầu. | 1 | Giữ trọn đoạn văn giới thiệu, câu từ hoàn chỉnh. | 2 |
| **Trang 20** | Cắt đôi từ `"science"` thành `"ience."` ở đầu chunk; cuối chunk bị ngắt lửng danh sách mục tiêu. | 0 | Đoạn giới thiệu phân hệ phần cứng và xử lý thông tin nguyên vẹn. | 2 |
| **Trang 21** | Cắt ngang bước công thức nấu ăn, mất ngữ cảnh mở đầu. | 1 | Giữ trọn ví dụ công thức bánh mì kẹp mứt và phân tích thuật toán. | 2 |
| **Trang 22** | Bắt đầu bằng từ `"ore"` (cắt từ `"more"`), kết thúc lửng ở `"as 'the theor"`. | 0 | Giữ trọn vẹn đoạn định nghĩa Khoa học máy tính của GS. George Forsythe. | 2 |
| **Trang 23** | Bắt đầu câu không có chủ ngữ (`"re made of physical..."`), mất ngữ cảnh phần cứng. | 1 | Trình bày đầy đủ khái niệm bộ nhớ và đèn chân không của máy ENIAC. | 2 |
| **Trang 24** | Bắt đầu bằng `"f 'Women holding...'"` (cắt từ `"credit"`), kết thúc lửng ở `"every computer has"`. | 0 | Đoạn văn hoàn chỉnh giải thích về máy Turing và tính Turing-complete. | 2 |
| **Trang 25** | Mất cụm từ mở đầu, ngắt giữa câu giải thích mạng ARPANET. | 1 | Đoạn văn đầy đủ về sự chuyển dịch trong ngành từ silicon sang tương tác người-máy. | 2 |
| **Trang 26** | Hiểu được một phần về đào tạo nhưng bị cắt cụm từ chỉ mốc thời gian. | 1 | Đoạn văn độc lập, câu cú hoàn chỉnh về lịch sử các khoa CNTT ban đầu. | 2 |
| **Trang 27** | Bị cắt đôi danh sách nhân vật lịch sử giữa hai chunk kế tiếp. | 1 | Giữ trọn vẹn đoạn giới thiệu cuốn sách *"Black Software"*. | 2 |
| **Trang 28** | Đoạn số liệu bị ngắt làm đôi, tách rời số liệu 26% khỏi bối cảnh BLS. | 1 | Khối phân tích nhu cầu lao động CNTT và visa H-1B được giữ trọn vẹn. | 2 |
| **Trung bình** | | **0.70 / 2.0** | | **2.00 / 2.0** |

---

## 3. Metadata Usefulness (Tính hữu dụng của Metadata)
* **Số bản ghi kiểm tra thủ công:** 15 bản ghi (5 câu test $\times$ top 3 chunks).
* **Tính đầy đủ và chính xác:** **15/15 bản ghi (100%)** có metadata `document_id`, `source`, `page`, `chapter`, `section` hoàn toàn khớp với thực tế trong PDF.
* **Tỷ lệ tuân thủ bộ lọc (Filter Compliance):**
  * Câu test `q19` có yêu cầu lọc: `{"section": "2.1 Computational Thinking"}`.
  * **Chiến lược A & B:** N/A (không sử dụng bộ lọc).
  * **Chiến lược C:** **1/1 câu (100% tuân thủ)** — cả 3 chunk trả về trong top-3 đều thuộc đúng section `2.1 Computational Thinking`.
* **Phân tích:** Việc gắn `section` giúp thu hẹp không gian tìm kiếm, loại trừ các đoạn giới thiệu khái quát ở Chương 1 khi truy vấn về kỹ thuật tính toán chuyên sâu ở Chương 2.

---

## 4. Grounding Quality (Chất lượng Ngữ cảnh Bằng chứng)
*Phương pháp:* Đọc và chấm thủ công top-3 kết quả trả về của **5 câu tập Test** (`q16` $\to$ `q20`).  
*Thang điểm:*  
* **0:** Không có bằng chứng nào liên quan để trả lời.  
* **1:** Có thông tin liên quan nhưng thiếu điều kiện hoặc bị cắt cụt ngữ cảnh cần thiết.  
* **2:** Có đầy đủ bằng chứng và điều kiện để trả lời chính xác câu hỏi và truy được nguồn.  

| ID | Câu hỏi | Gold Page | Điểm A | Điểm B | Điểm C | Lý do chấm điểm |
|---|---|:---:|:---:|:---:|:---:|---|
| **q16** | What physical technology did the ENIAC use instead of silicon? | 23 | 2 | 2 | 2 | Cả 3 chiến lược đều đưa đoạn chứa *"vacuum tube"* lên Top-1. Chiến lược B & C câu văn trọn vẹn và tự nhiên hơn. |
| **q17** | Why did the One Laptop per Child (OLPC) educational vision fail to truly materialize? | 29 | 2 | 2 | 2 | Top-1 cung cấp đầy đủ nguyên nhân do thiếu đào tạo giáo viên và học sinh dùng máy để giải trí. |
| **q18** | What role does scientific evaluation play in human-computer interaction (HCI)? | 33 | 1 | 1 | 1 | Top-3 trả về các đoạn định nghĩa tổng quát về HCI (trang 43, 25), có liên quan đến HCI nhưng thiếu đoạn nói sâu về vai trò khoa học tại trang 33. |
| **q19** | In section 2.1 Computational Thinking, what does decomposition involve when tackling complex problems? | 54 | 2 | 2 | 2 | Dù gold page là 54, nhưng Top-3 trả về trang 51 và 53 đều định nghĩa trọn vẹn bản chất của decomposition. Cung cấp đầy đủ căn cứ trả lời. |
| **q20** | In the Chapter 1 Review, how is a spreadsheet defined? | 43 | 2 | 2 | 2 | Top-1 trả về trang 30 chứa nguyên văn câu định nghĩa spreadsheet giống hệt glossary trang 43, đủ căn cứ trả lời chính xác. |
| **Trung bình** | | | **1.80** | **1.80** | **1.80** | **4 câu đạt điểm 2/2; 1 câu đạt điểm 1/2.** |

---

## 5. Data Strategy Impact & Phân tích Đánh đổi
1. **Giữa Chiến lược A và B:**
   * A có Hit@3 trên Dev cao hơn (93.3% vs 86.7%) do chia nhỏ 500 ký tự với overlap 50 làm tăng mật độ từ khóa trùng khớp.
   * Nhưng A phải trả giá đắt ở tính toàn vẹn (Coherence chỉ đạt **0.70/2.0** so với **2.00/2.0** của B). Trong hệ thống RAG thực tế, việc nạp các chunk bị đứt từ (`ience.`, `ore`) vào context của LLM sẽ gây suy giảm nghiêm trọng độ tin cậy của câu trả lời.
   * Chiến lược B tiết kiệm **34% số lượng chunks** (179 vs 270), giúp giảm kích thước index và tăng tốc độ vector search.
2. **Giữa Chiến lược B và C:**
   * C giữ nguyên tính mạch lạc cao của B nhưng bổ sung khả năng định tuyến tìm kiếm theo phân vùng tri thức thông qua Metadata Filtering, đảm bảo 100% tuân thủ ngữ cảnh khi người dùng xác định phạm vi cần tra cứu.
