# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                     |
|-----------------|--------------------------------------------------------------|
| Họ và tên       | Đinh Tiến Cảnh                                               |
| MSSV            | 2A202602918                                                  |
| Khóa/Lớp        | K4-L3-DAY10                                                  |
| Tên nhóm        | DCCC                                                         |
| Vai trò chính   | RAG & Vector Index                                           |
| Repository      | https://github.com/mysorf-9239/K4-L3-DAY10-DCCC-DataPipeline |
| Ngày hoàn thành | 2026-09-25                                                   |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách        | Input nhận vào                     | Output bàn giao                 | Trạng thái |
|--------------------|---------------------------|------------------------------------|---------------------------------|------------|
| Embedding backend  | `retrieval/embeddings.py` | Embedding text                     | Normalized MiniLM vectors       | Hoàn thành |
| Chroma index       | `retrieval/index.py`      | Clean/corrupted/repaired dataframe | 3 persistent collections        | Hoàn thành |
| Retrieval/QA       | `retrieval/qa.py`         | Query + index                      | Ranked docs và extracted answer | Hoàn thành |
| Index manifests    | `data/embeddings/*.json`  | Indexed documents                  | Reproducibility metadata        | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                     | Thành viên/module được hỗ trợ | Kết quả                                   |
|-------------------------------|-------------------------------|-------------------------------------------|
| Kiểm tra retrieval smoke test | Evaluation                    | Semantic search trả đúng top-k            |
| Chuẩn bị offline model        | Pipeline Lead                 | Demo không phụ thuộc mạng sau lần tải đầu |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện     | File/hàm/artifact liên quan | Kết quả bàn giao                       | Cách xác minh           |
|---------------------------|-----------------------------|----------------------------------------|-------------------------|
| Map rows thành documents  | `_build_documents`          | Content + metadata + stable record IDs | Embedding manifests     |
| Build/rebuild collections | `LocalEmbeddingIndex.build` | 24 docs mỗi state                      | Chroma collection count |
| Semantic search           | `search`/`semantic_search`  | Cosine ranked results                  | Top-k smoke test        |
| Exact title lookup        | `lookup`, `answer_question` | Grounded QA extraction                 | Baseline answers JSON   |

Output tiêu biểu là ChromaDB gồm `papers-baseline`, `papers-corrupted`, `papers-repaired`, mỗi collection
24 documents và có manifest ghi model, path, collection cùng document metadata.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Ba data states phải được index độc lập để so sánh khách quan, không để vectors hoặc metadata cũ rò
giữa các lần chạy. Retrieval cũng cần stable DOI để đánh giá với ground truth.

### Cách triển khai

MiniLM encode text và normalize embeddings. Chroma collection dùng cosine space. Mỗi build xóa collection
cùng tên trước khi add, tránh duplicate vectors. Record ID kết hợp DOI với row index để Chroma chấp nhận
corrupted duplicate rows, còn metadata giữ DOI gốc cho evaluation. Search chuyển distance thành similarity;
QA bổ sung exact-title result khi câu hỏi trích dẫn tiêu đề.

### Input, output và contract

| Thành phần              | Mô tả                                                        |
|-------------------------|--------------------------------------------------------------|
| Input                   | Dataframe có DOI, title, embedding text và metadata helpers  |
| Output                  | Chroma collection, embedding manifest, `SearchResult` list   |
| Module phụ thuộc        | sentence-transformers, ChromaDB, pandas                      |
| Module sử dụng output   | QA và evaluation metrics                                     |
| Điều kiện lỗi cần xử lý | Model chưa cache, collection chưa build, duplicated DOI rows |

### Cách xác minh

```bash
HF_HUB_OFFLINE=1 python -c "from core.config import load_settings; from retrieval.index import LocalEmbeddingIndex; s=load_settings(); i=LocalEmbeddingIndex(s, 'papers-baseline'); i.build_from_clean(); print(len(i.semantic_search('machine learning', 2)))"
```

- **Kết quả mong đợi:** In `2`.
- **Kết quả thực tế:** Semantic search trả 2 documents; baseline collection có 24 documents.
- **Artifact/log:** `data/chroma/`, `data/embeddings/papers_embeddings.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Có thể ghi đè một collection hoặc tách ba collections.
- **Các phương án đã cân nhắc:** Một collection tuần tự; ba database paths; ba collections chung DB.
- **Phương án đã chọn:** Ba collection names trong một persistent Chroma database.
- **Lý do:** Cô lập state nhưng vẫn gọn artifact, dễ load/compare, tránh vector contamination.
- **Bằng chứng quyết định phù hợp:** Chroma list chỉ có ba collection và mỗi collection count = 24.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Không kết nối được Hugging Face và model chưa có trong cache.
- **Lệnh hoặc bước tái hiện:** Build baseline index trên máy chưa tải MiniLM.
- **Nguyên nhân gốc:** Embedding weights là external dependency.
- **Cách xử lý:** Download một lần, sau đó bật `HF_HUB_OFFLINE=1`.
- **Cách xác minh sau khi sửa:** Hai flows chạy exit 0 bằng cache.
- **Điều học được:** Model artifact phải nằm trong deployment/setup checklist.

## 7. Hiểu biết về luồng end-to-end

1. Clean text từ Crossref được MiniLM encode và lưu cùng metadata vào Chroma.
2. Ground-truth DOI được so với DOI retrieval để tính hit; answer được so với reference để tính F1.
3. Quality đo cấu trúc/nội dung, freshness đo độ tuổi corpus.
4. Fixed test set bảo đảm metric variation đến từ data/index.
5. Repair thành công khi repaired collection lấy lại baseline retrieval/answer metrics.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal        | Baseline | Corrupted | Repaired | Nhận xét của cá nhân                          |
|----------------------|---------:|----------:|---------:|-----------------------------------------------|
| `retrieval_hit_rate` |    1.000 |     0.000 |    1.000 | Target docs không còn trong corrupted index   |
| `mean_token_f1`      |    0.963 |     0.451 |    0.963 | Retrieval/content corruption ảnh hưởng answer |
| `judge_accuracy`     |    1.000 |     0.500 |    1.000 | Phục hồi hoàn toàn                            |
| `mean_judge_score`   |    4.800 |     2.600 |    4.800 | Phục hồi hoàn toàn                            |
| Quality checks       |     PASS |      FAIL |     PASS | Index size không thay được GX                 |
| Freshness status     |     PASS |      FAIL |     PASS | Metadata dates phản ánh staleness             |

### Kết luận từ số liệu

1. Drop benchmark documents nhưng thêm duplicates → index vẫn 24 docs → Hit Rate vẫn giảm về 0.
2. Rebuild clean documents và collection → Hit Rate/F1 trở lại baseline.

Drop latest ảnh hưởng rõ nhất. Điều khác kỳ vọng là collection size không đổi; kiểm tra DOI list cho thấy
duplicates đã bù cho missing documents, chứng minh cần retrieval benchmark thay vì chỉ count vectors.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Vector collection rebuild phải idempotent.
2. Index count không phản ánh corpus completeness.
3. Stable document identity quyết định độ tin cậy của retrieval evaluation.

### Nếu có thêm thời gian

Thêm kiểm tra hash/document IDs giữa manifest và Chroma, cùng retrieval regression tests; đo bằng tỷ lệ
manifest-index consistency 100% và recall@k trên nhiều queries hơn.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.