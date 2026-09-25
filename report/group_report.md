# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin       | Nội dung                                                     |
|-----------------|--------------------------------------------------------------|
| Khóa/Lớp        | K4-L3-DAY10                                                  |
| Tên nhóm        | DCCC                                                         |
| Repository      | https://github.com/mysorf-9239/K4-L3-DAY10-DCCC-DataPipeline |
| Ngày hoàn thành | 2026-09-25                                                   |

### Thành viên và phân công

| STT | Họ và tên         | MSSV        | Vai trò chính               | Module/deliverable sở hữu                          |
|----:|-------------------|-------------|-----------------------------|----------------------------------------------------|
|   1 | Nguyễn Đức Danh   | 2A202602722 | Lead / Pipeline Integration | `core/`, `pipelines/`, entrypoints, nghiệm thu     |
|   2 | Bùi Gia Chính     | 2A202602693 | Data Foundation & Recovery  | `ingestion/`, raw/clean data, corruption và repair |
|   3 | Đinh Tiến Cảnh    | 2A202602918 | RAG & Vector Index          | `retrieval/`, MiniLM, ChromaDB, QA                 |
|   4 | Nguyễn Quốc Cường | 2A202602886 | Observability & Evaluation  | `quality.py`, `evaluation/`, reporting             |

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm đã hoàn thiện pipeline Crossref theo chuỗi raw preservation, cleaning, Great Expectations 1.x,
freshness SLA, MiniLM embeddings, ChromaDB, benchmark, controlled corruption và idempotent repair.
Baseline tạo 24 records sạch, ba lớp artifact raw/clean/index, test set cố định 10 câu cùng metrics và
báo cáo. Baseline đạt retrieval hit rate 1.000, mean token F1 0.963; quality và freshness đều PASS.
Sáu corruption scenario làm mất năm documents mới nhất, tạo summary rỗng, text noise, title ngắn,
stale dates và DOI trùng. Corrupted quality/freshness chuyển sang FAIL, hit rate giảm còn 0.000 và
token F1 còn 0.451. Repair không vá dữ liệu hỏng mà rebuild từ immutable raw records; clean repaired
khớp baseline, quality/freshness trở lại PASS, hit rate và token F1 phục hồi 100%. Blocker chính là
MiniLM cần tải một lần từ Hugging Face; sau khi cache, demo có thể chạy offline. LLM judge và Ragas
được để opt-in để pipeline vẫn tái lập được khi không có API credentials.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API / offline snapshot
    -> raw response/raw records
    -> cleaning, deduplication, age_days, text_for_embedding
    -> GX 1.x quality gate + freshness SLA
    -> MiniLM embeddings + ChromaDB index
    -> fixed benchmark + baseline evaluation
    -> six deterministic corruption scenarios
    -> corrupted re-index + re-evaluation
    -> repair từ immutable raw records
    -> repaired evaluation + comparison report
```

### Trách nhiệm của từng khối

| Khối              | Input                    | Xử lý chính                                         | Output/artifact                    | Owner             |
|-------------------|--------------------------|-----------------------------------------------------|------------------------------------|-------------------|
| Ingestion         | Crossref API/snapshot    | Fetch, retry, fallback, parse, remove JATS          | `data/raw/*.json`                  | Bùi Gia Chính     |
| Cleaning          | `PaperRecord`            | Normalize, date parsing, deduplicate, derive fields | `data/clean/papers_clean.*`        | Bùi Gia Chính     |
| Embedding/index   | Clean dataframe          | MiniLM normalized vector, cosine Chroma             | `data/chroma/`, `data/embeddings/` | Đinh Tiến Cảnh    |
| Evaluation        | Fixed test set + index   | Hit Rate, Token F1, judge metrics                   | `data/results/*metrics.json`       | Nguyễn Quốc Cường |
| Observability     | Dataframe                | GX checks và freshness SLA                          | `data/quality/*.json`              | Nguyễn Quốc Cường |
| Corruption/repair | Clean + raw records      | 6 corruptions; rebuild từ raw                       | Corrupted/repaired artifacts       | Bùi Gia Chính     |
| Orchestration     | Settings + stage outputs | Dependency order, fail-fast, reports                | `data/reports/*.md`                | Nguyễn Đức Danh   |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng                                                    |
|---------------------------|--------------------------------------------------------------------|
| `LLM_PROVIDER`            | Gemini theo `.env`; pipeline mặc định không bắt buộc gọi LLM judge |
| `LLM_MODEL`               | `gemini-2.5-flash`                                                 |
| Embedding model           | `sentence-transformers/all-MiniLM-L6-v2`                           |
| Số lượng Crossref records | 24                                                                 |
| Retrieval `top_k`         | 4                                                                  |
| Freshness threshold       | 180 ngày; stale ratio tối đa 25%                                   |
| Random seed               | Không dùng; corruption chọn vị trí deterministically               |

### Lệnh cài đặt

```bash
uv sync
```

### Lệnh chạy

```bash
HF_HUB_OFFLINE=1 uv run python script/run_phase1.py
HF_HUB_OFFLINE=1 uv run python script/run_corruption_flow.py
```

`HF_HUB_OFFLINE=1` chỉ dùng sau khi MiniLM đã được tải một lần. Lần setup đầu cần mạng để tải model.

### Kết quả tái hiện

| Lệnh              | Trạng thái         | Thời điểm chạy gần nhất | Bằng chứng                          |
|-------------------|--------------------|-------------------------|-------------------------------------|
| Baseline pipeline | Thành công, exit 0 | 2026-09-25              | `data/reports/phase1_report.md`     |
| Corruption flow   | Thành công, exit 0 | 2026-09-25              | `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính            | Giá trị                                                                                                   |
|-----------------------|-----------------------------------------------------------------------------------------------------------|
| Source                | Crossref REST API; fallback `data/raw/crossref_response.json`                                             |
| Query/filter          | `agentic retrieval augmented generation large language model`; từ ngày hiện tại trừ 180 ngày; có abstract |
| Thời điểm lấy dữ liệu | Snapshot đi kèm starter; pipeline xác minh lại 2026-09-25                                                 |
| Số record nhận được   | 24                                                                                                        |
| Cơ chế retry/backoff  | Tối đa 3 lần, exponential backoff; fallback local nếu HTTP/JSON lỗi                                       |

### Raw và clean schema

| Trường               | Kiểu dữ liệu | Bắt buộc?           | Ý nghĩa                 | Xử lý khi thiếu/sai                          |
|----------------------|--------------|---------------------|-------------------------|----------------------------------------------|
| `paper_id`           | string/DOI   | Có                  | Document identity       | Lowercase, trim; bỏ record rỗng; deduplicate |
| `title`              | string       | Có                  | Tiêu đề paper           | Normalize whitespace; bỏ record rỗng         |
| `summary`            | string       | Có tại quality gate | Abstract đã làm sạch    | Unescape, remove HTML/JATS; GX min length 30 |
| `authors`            | list[string] | Không               | Danh sách tác giả       | Ghép given/family; tạo `authors_joined`      |
| `categories`         | list[string] | Không               | Lĩnh vực                | Normalize; tạo `categories_joined`           |
| `published`          | ISO date     | Có                  | Ngày công bố            | Parse UTC; bỏ record không parse được        |
| `age_days`           | integer      | Có                  | Tuổi dữ liệu            | `max(0, run_date - published)`               |
| `text_for_embedding` | string       | Có                  | Nội dung đưa vào MiniLM | Ghép 5 phần theo format cố định              |

### Quy tắc cleaning

| Quy tắc                                  | Quality dimension   |    Số record bị tác động | Cách xác minh                           |
|------------------------------------------|---------------------|-------------------------:|-----------------------------------------|
| Remove HTML/JATS và normalize whitespace | Validity            |        24 được chuẩn hóa | Không còn tag trong `papers_clean.json` |
| Parse ISO date và tính `age_days`        | Validity/Timeliness |                       24 | Cột `published`, `age_days`             |
| Deduplicate theo DOI                     | Uniqueness          |   0 duplicate ở baseline | GX uniqueness PASS                      |
| Filter DOI/title/date không hợp lệ       | Completeness        | 0 trên snapshot hiện tại | Input 24, output 24                     |
| Derive joined/helper fields              | Consistency         |                       24 | Clean CSV/JSON schema                   |

`text_for_embedding` gồm Title, Authors, Published, Categories và Summary trên các dòng riêng.
Document ID dùng DOI đã lowercase để ổn định qua cả ba trạng thái. `age_days` là số ngày nguyên giữa
thời điểm chạy UTC và `published`, chặn tối thiểu ở 0 để xử lý ngày tương lai trong snapshot.

## 6. Evaluation setup

| Thành phần               | Cấu hình thực tế                                                                                      |
|--------------------------|-------------------------------------------------------------------------------------------------------|
| Số câu hỏi               | 10                                                                                                    |
| Các `question_type`      | `summary`, `authors`, `date`, `categories`, `multi_hop`                                               |
| Ground-truth document ID | DOI lấy trực tiếp từ clean dataframe                                                                  |
| Embedding model          | `sentence-transformers/all-MiniLM-L6-v2`                                                              |
| Vector store/collection  | Chroma cosine: `papers-baseline`, `papers-corrupted`, `papers-repaired`                               |
| Retrieval `top_k`        | 4                                                                                                     |
| LLM provider/model       | Gemini 2.5 Flash khi opt-in; mặc định deterministic token-F1 judge                                    |
| Test set dùng chung      | `data/eval/test_set.json`; SHA-256 `dc38184e3499b7e01b6e9d29dfd1fa26bc6912fea8250ceaaefa46bf3346564b` |

Giữ nguyên test set và ground truth giúp mọi chênh lệch metric phản ánh thay đổi corpus/index, không
phải do thay câu hỏi. Cả ba evaluation đều đọc cùng một artifact path.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                    | Trạng thái | Ghi chú                           |
|--------------------------|--------------------------------------|------------|-----------------------------------|
| Raw response/records     | `data/raw/`                          | Có         | 2 JSON, 24 records                |
| Cleaned dataset          | `data/clean/`                        | Có         | CSV + JSON, 24 unique rows        |
| Embedding manifest/index | `data/embeddings/`, `data/chroma/`   | Có         | 3 collections, 24 docs/collection |
| Evaluation set           | `data/eval/test_set.json`            | Có         | 10 câu, 5 loại                    |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có         | 10 samples                        |
| Quality/freshness        | `data/quality/`                      | Có         | Baseline PASS                     |
| Baseline report          | `data/reports/phase1_report.md`      | Có         | Metrics + observability           |

### Baseline metrics

| Metric               | Giá trị | Diễn giải                                       |
|----------------------|--------:|-------------------------------------------------|
| `retrieval_hit_rate` |   1.000 | 10/10 câu retrieve ít nhất một ground-truth DOI |
| `mean_token_f1`      |   0.963 | Answer tokens gần khớp ground truth             |
| `judge_accuracy`     |   1.000 | 10/10 đạt ngưỡng deterministic judge            |
| `mean_judge_score`   |   4.800 | Điểm trung bình trên thang 5                    |
| Ragas                |     N/A | Chỉ chạy khi `RUN_RAGAS=1` và có credentials    |

## 8. Data quality và freshness

### Quality checks

| Check             | Quality dimension | Ngưỡng/kỳ vọng                      | Kết quả baseline | Bằng chứng                     |
|-------------------|-------------------|-------------------------------------|------------------|--------------------------------|
| Row count         | Volume            | 5–5000                              | PASS: 24         | `baseline_quality_report.json` |
| Critical not-null | Completeness      | DOI/title/embedding text không null | PASS             | Cùng report                    |
| DOI unique        | Uniqueness        | 100% unique                         | PASS             | Cùng report                    |
| Summary length    | Completeness      | ≥30 ký tự                           | PASS             | Cùng report                    |

### Freshness

| Thuộc tính            | Giá trị                                  |
|-----------------------|------------------------------------------|
| Freshness được đo tại | Clean dataframe qua `age_days`           |
| Timestamp mới nhất    | 2026-07-22                               |
| Ngưỡng freshness      | `age_days > 180`; stale ratio tối đa 25% |
| Trạng thái baseline   | Fresh / PASS                             |
| Lý do                 | 1/24 stale = 4.17%, thấp hơn 25%         |

## 9. Corruption scenarios và repair

| Corruption     | Cách tạo           | Record tác động | Signal kỳ vọng    | Tác động thực tế                  | Cách repair             |
|----------------|--------------------|----------------:|-------------------|-----------------------------------|-------------------------|
| Drop latest    | Bỏ 5 rows mới nhất |               5 | Retrieval giảm    | Hit Rate 0.000                    | Rebuild từ raw          |
| Blank summary  | Gán chuỗi rỗng     |               3 | Length FAIL       | 6 unexpected vì rows bị duplicate | Rebuild từ raw          |
| Inject noise   | Thêm token rác     |               3 | Embedding nhiễu   | Token F1 giảm                     | Rebuild từ raw          |
| Truncate title | Giữ 7 ký tự        |               3 | Metadata suy giảm | Title không còn đầy đủ            | Rebuild từ raw          |
| Stale date     | Lùi khoảng 5 năm   |              10 | Freshness FAIL    | 16/24 stale sau duplicate         | Rebuild từ raw          |
| Duplicate rows | Nhân 5 rows        |               5 | Uniqueness FAIL   | 10 unexpected rows                | Deduplicate khi rebuild |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có, đủ 6 scenarios.
- Nhận xét: Log ghi input/output row count, affected rows, replacement date và DOI cho drop/duplicate.

Repair đọc lại normalized raw records, chạy toàn bộ cleaning và index build vào collection riêng.
Nó không che lỗi bằng cách sửa metrics hay bỏ validation. So sánh JSON xác nhận repaired clean data
khớp baseline; chạy lặp lại không tăng row hoặc duplicate DOI.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal        | Baseline | Corrupted | Repaired |   Thay đổi do corruption | Mức phục hồi | Nhận xét                               |
|----------------------|---------:|----------:|---------:|-------------------------:|-------------:|----------------------------------------|
| `retrieval_hit_rate` |    1.000 |     0.000 |    1.000 |                   -1.000 |         100% | Ground-truth docs bị drop rồi phục hồi |
| `mean_token_f1`      |    0.963 |     0.451 |    0.963 |                   -0.512 |         100% | Answer quality giảm rõ                 |
| `judge_accuracy`     |    1.000 |     0.500 |    1.000 |                   -0.500 |         100% | Một nửa corrupted answers dưới ngưỡng  |
| `mean_judge_score`   |    4.800 |     2.600 |    4.800 |                   -2.200 |         100% | Phục hồi đúng baseline                 |
| Quality checks       |     PASS |      FAIL |     PASS | Uniqueness + length fail |    Hoàn toàn | GX phát hiện lỗi                       |
| Freshness            |     PASS |      FAIL |     PASS |     4.17% → 66.67% stale |    Hoàn toàn | Trở lại 4.17%                          |

1. Drop ground-truth documents cùng corruption nội dung → quality/freshness FAIL → Hit Rate giảm từ
   1.000 xuống 0.000 và Token F1 giảm từ 0.963 xuống 0.451.
2. Rebuild từ raw → uniqueness, summary length và freshness trở lại PASS → toàn bộ retrieval/answer
   metrics trở về đúng baseline.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Pipeline không build được vector index khi MiniLM chưa tồn tại trong cache.
- **Nguyên nhân:** Lần đầu `SentenceTransformer` cần tải model từ Hugging Face.
- **Cách xử lý:** Cho phép tải model một lần; dùng cache và `HF_HUB_OFFLINE=1` cho demo sau đó.
- **Cách xác minh:** Hai entrypoint exit 0; Chroma có đúng 3 collections, mỗi collection 24 docs.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại                    | Ảnh hưởng                              | Hướng cải thiện có thể kiểm chứng              |
|--------------------------------------|----------------------------------------|------------------------------------------------|
| Judge mặc định là heuristic          | Chưa đánh giá hết semantic equivalence | Chạy `RUN_LLM_JUDGE=1`, so sánh correlation    |
| Ragas tắt mặc định                   | Chưa có faithfulness/context metrics   | Chạy `RUN_RAGAS=1` với credentials             |
| Corpus nhỏ, corruption deterministic | Chưa mô phỏng hết production drift     | Thêm nhiều corpus/seed và confidence intervals |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên có báo cáo vai trò riêng để review và xác nhận.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
- [x] Mỗi thành viên đã review nội dung, tạo contribution thật trên `main` và tự nộp VLearn.
