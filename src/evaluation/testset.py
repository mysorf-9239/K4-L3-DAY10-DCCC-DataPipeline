from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, read_json, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build a ten-question benchmark covering five question types.

    Pseudo-code:
    1. Kiem tra so luong document toi thieu.
    2. Chon mot so paper dai dien.
    3. Tao nhieu loai cau hoi:
       - summary
       - authors
       - date
       - categories
    4. Moi row can co:
       - id
       - question_type
       - question
       - ground_truth
       - ground_truth_doc_ids
    5. Ghi file JSON vao output_path.
    """
    if len(df) < 5:
        raise ValueError("At least five cleaned documents are required to build the test set.")
    chosen = df.sort_values(["published", "paper_id"], ascending=[False, True]).head(5).to_dict("records")
    samples = [
        {
            "id": "eval_001", "type": "summary", "question_type": "summary",
            "question": f"What is the summary of the paper '{chosen[0]['title']}'?",
            "ground_truth": first_sentence(chosen[0]["summary"]),
            "ground_truth_doc_ids": [chosen[0]["paper_id"]],
        },
        {
            "id": "eval_002", "type": "authors", "question_type": "authors",
            "question": f"Who authored the paper '{chosen[0]['title']}'?",
            "ground_truth": chosen[0]["authors_joined"],
            "ground_truth_doc_ids": [chosen[0]["paper_id"]],
        },
        {
            "id": "eval_003", "type": "date", "question_type": "date",
            "question": f"When was the paper '{chosen[1]['title']}' published?",
            "ground_truth": chosen[1]["published"],
            "ground_truth_doc_ids": [chosen[1]["paper_id"]],
        },
        {
            "id": "eval_004", "type": "category", "question_type": "categories",
            "question": f"What categories describe the paper '{chosen[1]['title']}'?",
            "ground_truth": chosen[1]["categories_joined"],
            "ground_truth_doc_ids": [chosen[1]["paper_id"]],
        },
        {
            "id": "eval_005", "type": "summary", "question_type": "summary",
            "question": f"What is the summary of the paper '{chosen[2]['title']}'?",
            "ground_truth": first_sentence(chosen[2]["summary"]),
            "ground_truth_doc_ids": [chosen[2]["paper_id"]],
        },
        {
            "id": "eval_006", "type": "authors", "question_type": "authors",
            "question": f"Who authored the paper '{chosen[2]['title']}'?",
            "ground_truth": chosen[2]["authors_joined"],
            "ground_truth_doc_ids": [chosen[2]["paper_id"]],
        },
        {
            "id": "eval_007", "type": "date", "question_type": "date",
            "question": f"When was the paper '{chosen[3]['title']}' published?",
            "ground_truth": chosen[3]["published"],
            "ground_truth_doc_ids": [chosen[3]["paper_id"]],
        },
        {
            "id": "eval_008", "type": "category", "question_type": "categories",
            "question": f"What categories describe the paper '{chosen[3]['title']}'?",
            "ground_truth": chosen[3]["categories_joined"],
            "ground_truth_doc_ids": [chosen[3]["paper_id"]],
        },
        {
            "id": "eval_009", "type": "summary", "question_type": "summary",
            "question": f"What is the summary of the paper '{chosen[4]['title']}'?",
            "ground_truth": first_sentence(chosen[4]["summary"]),
            "ground_truth_doc_ids": [chosen[4]["paper_id"]],
        },
        {
            "id": "eval_010", "type": "multi_hop", "question_type": "multi_hop",
            "question": (
                f"Compare the research focus of '{chosen[0]['title']}' and "
                f"'{chosen[4]['title']}'."
            ),
            "ground_truth": f"{first_sentence(chosen[0]['summary'])} {first_sentence(chosen[4]['summary'])}",
            "ground_truth_doc_ids": [chosen[0]["paper_id"], chosen[4]["paper_id"]],
        },
    ]
    write_json(output_path, samples)
    return samples


def load_or_create_test_set(df: pd.DataFrame, output_path, refresh: bool = False) -> list[dict[str, Any]]:
    if not refresh and output_path.exists():
        payload = read_json(output_path)
        if isinstance(payload, list) and payload:
            return payload
    return build_test_set(df, output_path)
