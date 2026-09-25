# Member Role Report - Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                     |
|-----------------|--------------------------------------------------------------|
| Họ và tên       | Nguyễn Đức Danh                                              |
| MSSV            | 2A202602722                                                  |
| Khóa/Lớp        | K4-L3-DAY10                                                  |
| Tên nhóm        | DCCC                                                         |
| Vai trò chính   | Lead / Pipeline Integration                                  |
| Repository      | https://github.com/mysorf-9239/K4-L3-DAY10-DCCC-DataPipeline |
| Ngày hoàn thành | 2026-09-25                                                   |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable              | File/hàm phụ trách                                      | Input nhận vào         | Output bàn giao                      | Trạng thái |
|---------------------------------|---------------------------------------------------------|------------------------|--------------------------------------|------------|
| Baseline orchestration          | `src/pipelines/phase1.py::main`                         | Settings, raw records  | Clean data, index, metrics, report   | Hoàn thành |
| Corruption/repair orchestration | `src/pipelines/corruption_flow.py::main`                | Baseline artifacts     | Corrupted/repaired metrics và report | Hoàn thành |
| Entrypoints                     | `script/run_phase1.py`, `script/run_corruption_flow.py` | Environment            | Reproducible CLI flow                | Hoàn thành |
| Integration evidence            | `report/group_report.md`, `docs/TEAM.md`                | Artifacts và phân công | Hồ sơ nghiệm thu                     | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động               | Thành viên/module được hỗ trợ  | Kết quả                                          |
|-------------------------|--------------------------------|--------------------------------------------------|
| Kiểm tra data contract  | Ingestion, cleaning, retrieval | 24 records giữ schema ổn định xuyên pipeline     |
| Kiểm tra metrics/report | Observability & Evaluation     | Báo cáo khớp JSON metrics và quality             |
| Chuẩn bị demo offline   | RAG & Vector Index             | Model cache + `HF_HUB_OFFLINE=1` chạy thành công |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan  | Kết quả bàn giao                            | Cách xác minh                          |
|-----------------------|------------------------------|---------------------------------------------|----------------------------------------|
| Ghép baseline flow    | `phase1.py`                  | 24 clean rows, quality PASS, Hit Rate 1.000 | `python script/run_phase1.py`          |
| Ghép corruption flow  | `corruption_flow.py`         | PASS → FAIL → PASS                          | `python script/run_corruption_flow.py` |
| Xác minh idempotency  | Clean baseline/repaired JSON | Hai artifact bằng nhau                      | JSON equality assertion                |
| Hoàn thiện hồ sơ nhóm | TEAM + group report          | Đủ 4 thành viên, metrics và checklist       | Đối chiếu `SUBMISSION.md`              |

Output cụ thể do vai trò tích hợp bàn giao là `data/reports/corruption_report.md`: bảng này nối trực
tiếp kết quả quality, freshness và evaluation của baseline, corrupted, repaired trên cùng test set.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Các module ingestion, cleaning, observability, retrieval và evaluation có thể chạy riêng nhưng cần
một orchestration bảo đảm đúng dependency order, fail-fast khi baseline không đạt quality và giữ
artifact paths thống nhất. Repair phải dựng lại từ nguồn raw chứ không tái sử dụng corrupted state.

### Cách triển khai

Trong baseline flow, settings được load một lần; raw records lấy từ snapshot hoặc API, sau đó clean và
lưu CSV/JSON. Quality gate chạy trước indexing để ngăn dữ liệu lỗi. Khi PASS, pipeline build collection,
tạo hoặc load test set 10 câu, chạy evaluation và sinh report. Corruption flow kiểm tra artifact đầu vào,
đánh giá corrupted data, rồi đọc lại raw records để clean/index/evaluate repaired state. Mỗi state dùng
collection và manifest riêng để không rò trạng thái.

### Input, output và contract

| Thành phần              | Mô tả                                                                                   |
|-------------------------|-----------------------------------------------------------------------------------------|
| Input                   | `Settings`, Crossref raw records, clean baseline artifacts, fixed test set              |
| Output                  | Clean/corrupted/repaired data, Chroma collections, metrics, quality và Markdown reports |
| Module phụ thuộc        | `ingestion`, `observability`, `retrieval`, `evaluation`                                 |
| Module sử dụng output   | Demo, báo cáo nhóm, submission review                                                   |
| Điều kiện lỗi cần xử lý | Thiếu baseline artifacts, baseline quality FAIL, model chưa cache, API/network lỗi      |

### Cách xác minh

```bash
HF_HUB_OFFLINE=1 .venv/bin/python script/run_phase1.py
HF_HUB_OFFLINE=1 .venv/bin/python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Baseline PASS, corrupted FAIL, repaired PASS; cả hai lệnh exit 0.
- **Kết quả thực tế:** Hit Rate `1.000 → 0.000 → 1.000`; Token F1 `0.963 → 0.451 → 0.963`.
- **Artifact/log:** `data/reports/phase1_report.md`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần repair dữ liệu sau khi sáu corruption scenario đã làm thay đổi nhiều cột và rows.
- **Các phương án đã cân nhắc:** Vá trực tiếp từng lỗi; rollback từ clean baseline; rebuild từ raw records.
- **Phương án đã chọn:** Rebuild từ `data/raw/crossref_records.json` rồi chạy lại cleaning và indexing.
- **Lý do:** Raw là lineage source đáng tin cậy; cách này deterministic, không bỏ sót mutation và idempotent.
- **Bằng chứng quyết định phù hợp:** Repaired JSON bằng baseline JSON, quality/freshness PASS và toàn bộ metrics phục
  hồi 100%.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Không thể kết nối Hugging Face và không tìm thấy MiniLM trong local cache.
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_phase1.py` trên môi trường chưa có model.
- **Nguyên nhân gốc:** `SentenceTransformer` phải tải weights trong lần dùng đầu tiên.
- **Cách xử lý:** Tải model một lần khi có mạng; sau đó chạy demo với `HF_HUB_OFFLINE=1`.
- **Cách xác minh sau khi sửa:** Hai pipeline exit 0; Chroma có ba collections, mỗi collection 24 docs.
- **Điều học được:** Dependency model cần được xem như artifact setup, không nên phụ thuộc mạng trong live demo.

## 7. Hiểu biết về luồng end-to-end

1. Crossref payload được lưu raw, parse thành `PaperRecord`, clean/deduplicate, ghép embedding text rồi
   MiniLM tạo vector để nạp vào ChromaDB.
2. Mỗi câu hỏi có ground-truth DOI; nếu retrieval trả một DOI đúng thì tính hit. Answer được so token
   với ground truth để tính F1 và judge metrics.
3. Quality checks đo volume, completeness, uniqueness và độ dài; freshness đo timeliness ở cấp dataset
   dựa trên stale ratio.
4. Cùng test set giúp so sánh ba state công bằng, không trộn ảnh hưởng của dữ liệu với thay đổi đề thi.
5. Repair thành công khi repaired clean data khớp baseline, GX/freshness PASS và metrics trở về baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal        | Baseline | Corrupted | Repaired | Nhận xét của cá nhân                              |
|----------------------|---------:|----------:|---------:|---------------------------------------------------|
| `retrieval_hit_rate` |    1.000 |     0.000 |    1.000 | Drop target docs làm retrieval thất bại hoàn toàn |
| `mean_token_f1`      |    0.963 |     0.451 |    0.963 | Nội dung nhiễu/thiếu kéo answer quality xuống     |
| `judge_accuracy`     |    1.000 |     0.500 |    1.000 | Một nửa corrupted answers dưới ngưỡng             |
| `mean_judge_score`   |    4.800 |     2.600 |    4.800 | Phục hồi đúng baseline                            |
| Quality checks       |     PASS |      FAIL |     PASS | GX phát hiện duplicate và summary rỗng            |
| Freshness status     |     PASS |      FAIL |     PASS | Stale ratio 4.17% → 66.67% → 4.17%                |

### Kết luận từ số liệu

1. Drop five latest ground-truth documents và làm bẩn content → quality/freshness FAIL → Hit Rate về
   0.000, Token F1 giảm 0.512.
2. Rebuild từ raw → uniqueness/summary/freshness phục hồi → Hit Rate, F1 và judge metrics trở lại baseline.

Corruption ảnh hưởng rõ nhất là drop latest records vì năm documents được benchmark dùng đều bị loại,
khiến retrieval hit rate về 0 dù row count vẫn là 24 do duplicate bù số lượng. Kết quả khác trực giác
là row count không giảm; kiểm tra corruption log và DOI uniqueness chứng minh corpus thực tế đã mất dữ liệu.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Orchestration phải kiểm tra contract và quality trước khi cho dữ liệu vào serving index.
2. Idempotent repair cần source of truth ở raw layer, không chỉ một clean snapshot có thể đã bị thay đổi.
3. Row count hoặc log “pipeline thành công” không đủ; cần metrics, quality và freshness cùng lúc.

### Nếu có thêm thời gian

Mình sẽ thêm pytest end-to-end và CI kiểm tra artifact schema, idempotency hash, ba Chroma collection,
metric ordering và secret scan. Cải thiện được đo bằng coverage trên 80% và CI chạy lại từ clean checkout.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.