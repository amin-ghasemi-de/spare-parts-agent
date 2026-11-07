import re
from difflib import SequenceMatcher
from functools import lru_cache

import pandas as pd

from src.config import PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "data"
SHIPPING_DAYS = 2
MIN_SCORE = 60


@lru_cache(maxsize=1)
def load_catalog() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "parts_catalog.csv", encoding="utf-8")


@lru_cache(maxsize=1)
def load_stock() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "stock.csv", encoding="utf-8")


def normalize_part_no(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _text_similarity(query: str, text: str) -> float:
    query_tokens = _tokens(query)
    text_tokens = _tokens(text)
    if not query_tokens or not text_tokens:
        return 0.0

    total = 0.0
    for q in query_tokens:
        total += max(SequenceMatcher(None, q, t).ratio() for t in text_tokens)
    return total / len(query_tokens)


def _part_no_similarity(query: str, part_no: str) -> float:
    return SequenceMatcher(None, normalize_part_no(query), normalize_part_no(part_no)).ratio()


def search_part_catalog(query: str, machine_model: str | None = None, max_results: int = 5) -> dict:
    catalog = load_catalog()

    if machine_model:
        mask = catalog["compatible_models"].str.split(";").apply(lambda models: machine_model in models)
        catalog = catalog[mask]

    exact = catalog[catalog["part_no"].apply(normalize_part_no) == normalize_part_no(query)]
    if not exact.empty:
        row = exact.iloc[0]
        return {
            "query": query,
            "machine_model": machine_model,
            "exact_part_no_match": True,
            "results": [_row_to_result(row, score=100)],
        }

    results = []
    for _, row in catalog.iterrows():
        score = max(
            _text_similarity(query, row["name_de"]),
            _text_similarity(query, row["name_en"]),
            _part_no_similarity(query, row["part_no"]),
        )
        score = round(score * 100)
        if score >= MIN_SCORE:
            results.append(_row_to_result(row, score))

    results.sort(key=lambda result: result["score"], reverse=True)
    return {
        "query": query,
        "machine_model": machine_model,
        "exact_part_no_match": False,
        "results": results[:max_results],
    }


def _row_to_result(row: pd.Series, score: int) -> dict:
    return {
        "part_no": row["part_no"],
        "name_de": row["name_de"],
        "name_en": row["name_en"],
        "compatible_models": row["compatible_models"].split(";"),
        "unit_price_eur": float(row["unit_price_eur"]),
        "score": score,
    }


def check_stock(part_no: str, quantity: int) -> dict:
    stock = load_stock()
    rows = stock[stock["part_no"] == part_no]

    if rows.empty:
        return {"part_no": part_no, "found": False, "error": f"Unknown part number: {part_no}"}

    row = rows.iloc[0]
    available = int(row["qty_available"])
    lead_time = int(row["lead_time_days"])
    fully_available = available >= quantity

    return {
        "part_no": part_no,
        "found": True,
        "requested_qty": quantity,
        "qty_available": available,
        "fully_available": fully_available,
        "qty_from_stock": min(available, quantity),
        "qty_to_order": max(0, quantity - available),
        "delivery_days_from_stock": SHIPPING_DAYS,
        "delivery_days_for_rest": None if fully_available else lead_time + SHIPPING_DAYS,
    }
