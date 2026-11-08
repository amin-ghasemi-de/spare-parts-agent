import json
import re
from pathlib import Path

from src.config import PROJECT_ROOT

EVAL_DIR = PROJECT_ROOT / "eval"
GROUND_TRUTH_FILE = EVAL_DIR / "ground_truth.json"
RESULTS_DIR = EVAL_DIR / "results"


def load_ground_truth() -> list[dict]:
    return json.loads(GROUND_TRUTH_FILE.read_text(encoding="utf-8"))


def run_dir(run: int) -> Path:
    return RESULTS_DIR / f"run_{run}"


def normalize(text: str | None) -> str | None:
    if not text:
        return None
    return re.sub(r"[^A-Z0-9]", "", text.upper()) or None


def _last_draft_call(result: dict) -> dict | None:
    for record in reversed(result.get("trace", [])):
        if record["tool"] == "draft_reply" and record["result"].get("ok"):
            return record["arguments"]
    return None


def offered_items(result: dict) -> dict[str, int]:
    call = _last_draft_call(result)
    if call is None:
        return {}
    return {item["part_no"]: int(item["quantity"]) for item in call.get("items", [])}


def asked_question(result: dict) -> bool:
    call = _last_draft_call(result)
    return bool(call and call.get("open_questions"))


def score_case(truth: dict, result: dict) -> dict:
    score = {"id": truth["id"], "split": truth["split"], "error": result.get("error")}
    if score["error"]:
        return score

    extraction = result["extraction"]
    usage = result.get("usage", {})
    score["tokens"] = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
    score["llm_calls"] = usage.get("llm_calls", 0)
    score["seconds"] = result.get("duration_seconds", 0.0)
    score["request_ok"] = extraction["is_spare_part_request"] == truth["is_spare_part_request"]

    if not truth["is_spare_part_request"]:
        return score

    expected = {item["part_no"]: item["quantity"] for item in truth["expected_items"]}
    offered = offered_items(result)

    score["model_ok"] = normalize(extraction["machine_model"]) == normalize(truth["machine_model"])
    score["urgency_ok"] = extraction["urgency"] in truth["urgency"]
    score["language_ok"] = extraction["language"] in truth["language"]
    score["item_count_ok"] = len(extraction["items"]) == truth["requested_item_count"]

    score["parts_expected"] = len(expected)
    score["parts_found"] = sum(1 for part_no in expected if part_no in offered)
    score["qty_correct"] = sum(1 for part_no, qty in expected.items() if offered.get(part_no) == qty)
    score["wrong_parts"] = sum(1 for part_no in offered if part_no not in expected)
    score["offer_exact"] = offered == expected
    score["offered"] = offered

    must_ask = truth["must_ask"]
    score["ask_ok"] = None if must_ask is None else asked_question(result) == must_ask
    score["attention_ok"] = result.get("needs_attention", False) == truth["needs_attention"]
    return score


def _ratio(hits: int, total: int) -> str:
    if total == 0:
        return "–"
    return f"{hits}/{total} ({100 * hits / total:.0f}%)"


def summarize(scores: list[dict]) -> dict[str, str]:
    ok = [s for s in scores if not s["error"]]
    requests = [s for s in ok if "model_ok" in s]
    ask_scored = [s for s in requests if s["ask_ok"] is not None]

    def count(items: list[dict], key: str) -> int:
        return sum(1 for s in items if s[key])

    parts_expected = sum(s["parts_expected"] for s in requests)
    summary = {
        "Runs (e-mail × run)": str(len(scores)),
        "Errors": str(len(scores) - len(ok)),
        "Request detected correctly": _ratio(count(ok, "request_ok"), len(ok)),
        "Machine model extracted": _ratio(count(requests, "model_ok"), len(requests)),
        "Urgency extracted": _ratio(count(requests, "urgency_ok"), len(requests)),
        "Language detected": _ratio(count(requests, "language_ok"), len(requests)),
        "Number of requested items": _ratio(count(requests, "item_count_ok"), len(requests)),
        "Expected parts found": _ratio(sum(s["parts_found"] for s in requests), parts_expected),
        "Expected parts with correct quantity": _ratio(sum(s["qty_correct"] for s in requests), parts_expected),
        "Wrong parts offered (total)": str(sum(s["wrong_parts"] for s in requests)),
        "Offer exactly right": _ratio(count(requests, "offer_exact"), len(requests)),
        "Asked customer when needed (and only then)": _ratio(count(ask_scored, "ask_ok"), len(ask_scored)),
        "Urgency warning correct": _ratio(count(requests, "attention_ok"), len(requests)),
    }
    if ok:
        summary["Avg tokens per e-mail"] = f"{sum(s['tokens'] for s in ok) / len(ok):,.0f}"
        summary["Avg LLM calls per e-mail"] = f"{sum(s['llm_calls'] for s in ok) / len(ok):.1f}"
        summary["Avg seconds per e-mail"] = f"{sum(s['seconds'] for s in ok) / len(ok):.1f}"
    return summary


def consistency(scores_by_run: dict[int, list[dict]]) -> str:
    offers: dict[str, list] = {}
    for scores in scores_by_run.values():
        for s in scores:
            if not s["error"] and "offered" in s:
                offers.setdefault(s["id"], []).append(s["offered"])
    compared = [values for values in offers.values() if len(values) >= 2]
    same = sum(1 for values in compared if all(v == values[0] for v in values))
    return _ratio(same, len(compared))