from src.evaluation import asked_question, normalize, offered_items, score_case, summarize

TRUTH = {
    "id": "003",
    "split": "dev",
    "is_spare_part_request": True,
    "machine_model": "HPC-500",
    "urgency": ["low"],
    "language": ["de"],
    "requested_item_count": 1,
    "expected_items": [{"part_no": "HPC-VLV-202", "quantity": 1}],
    "must_ask": True,
    "needs_attention": False,
    "note": "",
}


def make_result(items, questions, machine_model="HPC-500", attention=False):
    return {
        "extraction": {
            "is_spare_part_request": True,
            "machine_model": machine_model,
            "urgency": "low",
            "language": "de",
            "items": [{"part_no": "HPC-VLV-220", "description": "Druckventil", "quantity": 1}],
        },
        "trace": [
            {
                "tool": "draft_reply",
                "arguments": {"items": items, "open_questions": questions, "language": "de"},
                "result": {"ok": True},
            }
        ],
        "usage": {"llm_calls": 5, "prompt_tokens": 5000, "completion_tokens": 500},
        "duration_seconds": 4.2,
        "needs_attention": attention,
        "status": "finished",
    }


def test_normalize_ignores_spaces_hyphens_and_case():
    assert normalize("hpc300") == normalize("HPC-300") == "HPC300"
    assert normalize(None) is None


def test_offered_items_and_question_come_from_draft_reply():
    result = make_result([{"part_no": "HPC-VLV-202", "quantity": 1}], ["Bitte bestätigen"])
    assert offered_items(result) == {"HPC-VLV-202": 1}
    assert asked_question(result) is True


def test_perfect_result_scores_everything_correct():
    result = make_result([{"part_no": "HPC-VLV-202", "quantity": 1}], ["Bitte bestätigen"])
    score = score_case(TRUTH, result)
    assert score["offer_exact"] is True
    assert score["ask_ok"] is True
    assert score["wrong_parts"] == 0
    assert score["tokens"] == 5500


def test_wrong_part_and_missing_question_are_detected():
    result = make_result([{"part_no": "HPC-VLV-201", "quantity": 1}], [])
    score = score_case(TRUTH, result)
    assert score["parts_found"] == 0
    assert score["wrong_parts"] == 1
    assert score["ask_ok"] is False


def test_error_result_is_counted_as_error():
    score = score_case(TRUTH, {"error": "ValueError: bad json"})
    summary = summarize([score])
    assert summary["Errors"] == "1"