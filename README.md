# Day 06 · Data Ingestion Engineering

**Học viên:** Trần Việt Thịnh · **MSSV:** 2A202603661 · **Lớp:** L3A  
**Corpus:** OpenStax Introduction to Computer Science (37 trang học thuật, CC BY 4.0)

---

## 🚀 Hướng dẫn chạy và tái lập kết quả (Reproduction Guide)

### 1. Khởi động PostgreSQL + pgvector (Docker)
```bash
docker compose -f starter/docker-compose.yml -p day6_student_starter up -d --wait
```

### 2. Cài đặt thư viện Python
```bash
python -m pip install -r starter/requirements.txt
```

### 3. Cấu hình môi trường (.env)
Sao chép và điền `OPENAI_API_KEY` (hoặc cấu hình database nếu đổi cổng):
```bash
# Windows PowerShell:
Copy-Item starter/.env.example starter/.env
```
Đảm bảo biến `OPENAI_API_KEY` đã được cung cấp trong `starter/.env`.

### 4. Chạy toàn bộ Pipeline thực nghiệm
Bạn có thể chạy từ thư mục gốc hoặc từ `starter/`:
```bash
# Chạy từ thư mục gốc:
python -m starter.src.run

# Hoặc chạy từ thư mục starter:
cd starter
python -m src.run
```

Lệnh trên sẽ tự động:
1. Đọc và trích xuất 37 trang nội dung cốt lõi từ file PDF theo [`data/manifest.json`](data/manifest.json).
2. Tạo chunks cho cả 3 chiến lược:
   * **Chiến lược A:** Fixed-size (500 ký tự, overlap 50) $\to$ 270 chunks.
   * **Chiến lược B:** Semantic Paragraph (max 800 ký tự) $\to$ 179 chunks.
   * **Chiến lược C:** Semantic Paragraph + Metadata Filtering $\to$ 179 chunks.
3. Sinh vector embedding qua OpenAI `text-embedding-3-small` (1536 chiều) và lưu vào PostgreSQL/pgvector.
4. Truy xuất Top-3 cho 20 câu hỏi benchmark (15 Dev, 5 Test).
5. Lưu kết quả trace tại [`results/`](results/) và cập nhật [`artifacts/experiment_log.csv`](artifacts/experiment_log.csv).

---

## 📊 Tóm tắt kết quả Benchmark

| Chiến lược | Phân chia | Hit@1 | Evidence Hit@3 | Số chunks | Coherence /2 | Grounding /2 |
|---|---|---|---|---|---|---|
| **A (Fixed-size)** | Dev / Test | 66.7% / 40.0% | 93.3% / 40.0% | 270 | 0.70 / 2.0 | 1.80 / 2.0 |
| **B (Paragraph)** | Dev / Test | 53.3% / 40.0% | 86.7% / 40.0% | 179 | 2.00 / 2.0 | 1.80 / 2.0 |
| **C (Filtered)** | Dev / Test | 53.3% / 40.0% | 86.7% / 40.0% | 179 | 2.00 / 2.0 | 1.80 / 2.0 |

> **Báo cáo phân tích chuyên sâu:** Đọc chi tiết tại [Báo cáo cá nhân 2A202603661_TranVietThinh.md](report/individual/2A202603661_TranVietThinh.md).

---

## 📂 Cấu trúc Repository

```text
├── STUDENT.md                              # Thông tin học viên
├── README.md                               # Hướng dẫn setup & chạy tái lập
├── data/
│   └── manifest.json                       # Bảng kê 37 trang nội dung, nguồn, bản quyền
├── benchmark/
│   ├── benchmark.json                      # 20 câu hỏi (15 dev, 5 test) kèm evidence quote
│   └── benchmark.csv                       # Phiên bản CSV của bộ câu hỏi
├── starter/
│   ├── docker-compose.yml                  # PostgreSQL 16 + pgvector container
│   ├── init.sql                            # Khởi tạo extension pgvector
│   ├── requirements.txt                    # Danh mục thư viện Python
│   ├── src/
│   │   ├── models.py                       # Data contracts (DocumentPage, Chunk, RetrievalHit)
│   │   ├── ingestion.py                    # Trích xuất PDF & chuẩn hóa văn bản
│   │   ├── chunking.py                     # Fixed-size và Paragraph chunking
│   │   ├── embeddings.py                   # OpenAI embedding adapter kèm local cache
│   │   ├── store.py                        # PgVectorStore quản lý lưu trữ và SQL metadata filter
│   │   ├── evaluation.py                   # Đo Hit@1, Evidence Hit@3 và ghi trace
│   │   └── run.py                          # Kịch bản điều phối toàn bộ pipeline
│   ├── scripts/
│   │   ├── check_setup.py                  # Kiểm tra kết nối pgvector
│   │   ├── build_benchmark.py              # Script đối soát và sinh benchmark
│   │   └── generate_manual_audit.py        # Script chấm thủ công Coherence & Grounding
│   └── data/                               # File PDF giáo trình OpenStax
├── artifacts/
│   └── experiment_log.csv                  # Nhật ký thí nghiệm cho cả 3 chiến lược
├── results/
│   ├── traces_strategy_a.jsonl             # Trace Top-3 chi tiết Chiến lược A
│   ├── traces_strategy_b.jsonl             # Trace Top-3 chi tiết Chiến lược B
│   ├── traces_strategy_c.jsonl             # Trace Top-3 chi tiết Chiến lược C
│   ├── metrics_summary.json                # Thống kê tổng hợp số liệu
│   └── manual_audit.json                   # Dữ liệu chấm thủ công 5 khía cạnh
└── report/individual/
    └── 2A202603661_TranVietThinh.md        # Báo cáo cá nhân hoàn chỉnh
```
