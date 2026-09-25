# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                     |
|-----------------|--------------------------------------------------------------|
| Họ và tên       | Nguyễn Quốc Cường                                            |
| MSSV            | 2A202602886                                                  |
| Khóa/Lớp        | K4-L3-DAY10                                                  |
| Tên nhóm        | DCCC                                                         |
| Vai trò chính   | Observability & Evaluation                                   |
| Repository      | https://github.com/mysorf-9239/K4-L3-DAY10-DCCC-DataPipeline |
| Ngày hoàn thành | 2026-09-25                                                   |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách                      | Input nhận vào     | Output bàn giao             | Trạng thái |
|--------------------|-----------------------------------------|--------------------|-----------------------------|------------|
| GX quality gate    | `observability/quality.py`              | Dataframe          | Quality JSON                | Hoàn thành |
| Freshness SLA      | `build_freshness_report`                | Published/age_days | Freshness status/report     | Hoàn thành |
| Benchmark          | `evaluation/testset.py`                 | Clean dataframe    | 10-question fixed set       | Hoàn thành |
| Metrics/reporting  | `evaluation/metrics.py`, `reporting.py` | Answers + quality  | Metrics và Markdown reports | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                  | Thành viên/module được hỗ trợ | Kết quả                                     |
|----------------------------|-------------------------------|---------------------------------------------|
| Đối chiếu report với JSON  | Pipeline Lead                 | Bảng ba trạng thái khớp artifacts           |
| Kiểm tra corrupted signals | Data Foundation               | GX bắt duplicate/blank; freshness bắt stale |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện  | File/hàm/artifact liên quan    | Kết quả bàn giao                  | Cách xác minh        |
|------------------------|--------------------------------|-----------------------------------|----------------------|
| Tạo GX ephemeral batch | `run_data_quality_checks`      | 6 validations/4 expectation types | Baseline quality 6/6 |
| Đo freshness           | `build_freshness_report`       | Baseline PASS, corrupted FAIL     | Quality JSON         |
| Tạo benchmark          | `build_test_set`               | 10 câu/5 loại                     | `test_set.json`      |
| Đánh giá và report     | `evaluate_pipeline`, reporting | 3 metrics bundles + 2 reports     | Data results/reports |

Output tiêu biểu là `data/quality/corrupted_quality_report.json`, chỉ ra uniqueness và summary length
FAIL cùng freshness ratio 66.67%, đủ bằng chứng phát hiện data corruption.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Silent failure không làm pipeline crash, nên cần quality/freshness signals và benchmark cố định để chứng
minh data lỗi kéo chất lượng RAG xuống, sau đó đo mức phục hồi.

### Cách triển khai

GX 1.x ephemeral context tạo pandas source/asset/batch. Row count, not-null, uniqueness và summary length
được validate; not-null áp dụng cho ba critical columns nên có sáu results. Freshness tính
`age_days > 180` và FAIL nếu stale ratio vượt 25%. Test set dùng năm newest documents tạo 10 câu thuộc
năm loại. Metrics tính retrieval hit, token F1 và judge; Ragas/LLM judge thật là opt-in.

### Input, output và contract

| Thành phần              | Mô tả                                                                     |
|-------------------------|---------------------------------------------------------------------------|
| Input                   | Clean/corrupted/repaired dataframe, Chroma index, fixed test set          |
| Output                  | Quality/freshness JSON, answers, metrics và Markdown reports              |
| Module phụ thuộc        | Great Expectations, pandas, retrieval QA                                  |
| Module sử dụng output   | Pipelines, demo, submission reports                                       |
| Điều kiện lỗi cần xử lý | Empty/duplicate/short content, stale ratio cao, LLM evaluator unavailable |

### Cách xác minh

```bash
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); print(run_data_quality_checks(pd.read_json(s.paths.clean_json), s, 'test')['success'])"
```

- **Kết quả mong đợi:** `True` trên baseline.
- **Kết quả thực tế:** Baseline/repaired True; corrupted False.
- **Artifact/log:** `data/quality/`, `data/results/`, `data/reports/`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Freshness là dataset-level ratio, không phải chỉ validation từng cell.
- **Các phương án đã cân nhắc:** GX custom expectation; pandas calculation riêng; chỉ check latest date.
- **Phương án đã chọn:** Pandas freshness report riêng và gộp boolean vào overall quality success.
- **Lý do:** Minh bạch stale count/ratio, dễ giải thích, không phụ thuộc GX custom plugin.
- **Bằng chứng quyết định phù hợp:** Corrupted freshness FAIL 16/24 trong khi baseline/repaired chỉ 1/24.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** VLearn mô tả 5 câu nhưng repo rubric/checkpoints yêu cầu 10 câu.
- **Lệnh hoặc bước tái hiện:** Đối chiếu nội dung bài và `docs/Guide.md`, `CHECKPOINTS.md`, `RUBRIC.md`.
- **Nguyên nhân gốc:** Hai phiên bản hướng dẫn chưa đồng bộ.
- **Cách xử lý:** Tạo 10 câu nhưng phủ đủ cả năm loại, bao gồm multi-hop.
- **Cách xác minh sau khi sửa:** Test set count = 10, types đủ năm, cả ba state dùng cùng file.
- **Điều học được:** Khi tài liệu mâu thuẫn, chọn yêu cầu rộng hơn và ghi rõ quyết định.

## 7. Hiểu biết về luồng end-to-end

1. Crossref → raw → clean → GX/freshness → MiniLM/Chroma → evaluation.
2. Ground-truth DOI đo retrieval; reference answers đo Token F1/judge.
3. Quality đo validity/completeness/uniqueness; freshness đo timeliness toàn corpus.
4. Fixed test set giữ benchmark constant qua ba states.
5. Repair đạt khi signals PASS và metrics trở lại baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal        | Baseline | Corrupted | Repaired | Nhận xét của cá nhân            |
|----------------------|---------:|----------:|---------:|---------------------------------|
| `retrieval_hit_rate` |    1.000 |     0.000 |    1.000 | Retrieval degradation rõ ràng   |
| `mean_token_f1`      |    0.963 |     0.451 |    0.963 | Answer quality giảm và phục hồi |
| `judge_accuracy`     |    1.000 |     0.500 |    1.000 | Một nửa corrupted answers fail  |
| `mean_judge_score`   |    4.800 |     2.600 |    4.800 | Phục hồi 100%                   |
| Quality checks       |     PASS |      FAIL |     PASS | Unique/length phát hiện lỗi     |
| Freshness status     |     PASS |      FAIL |     PASS | Stale ratio vượt SLA            |

### Kết luận từ số liệu

1. Blank/duplicate/stale/drop → GX và freshness FAIL → retrieval/answer metrics cùng giảm.
2. Raw rebuild → quality/freshness PASS → metrics phục hồi đúng baseline.

Drop documents ảnh hưởng trực tiếp nhất đến Hit Rate; stale dates ảnh hưởng rõ nhất đến freshness. Không
có kết quả trái kỳ vọng sau khi xem đồng thời metrics và data-quality artifacts.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Quality và freshness là hai signal bổ sung, không thay thế nhau.
2. Benchmark phải cố định và có stable ground-truth IDs.
3. Report chỉ đáng tin khi số liệu được sinh trực tiếp từ artifacts.

### Nếu có thêm thời gian

Thêm data docs/dashboard và trend theo nhiều run dates; đo bằng alert precision/recall trên nhiều corruption
seeds và thời gian phát hiện từ ingestion đến gate.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.
