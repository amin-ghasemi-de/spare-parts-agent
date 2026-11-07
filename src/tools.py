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

def _format_eur(value: float, language: str) -> str:
    text = f"{value:,.2f}"
    if language == "de":
        text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} EUR"


def _availability_text(stock: dict, language: str) -> str:
    if language == "de":
        if stock["fully_available"]:
            return f"ab Lager verfügbar, Lieferung in ca. {stock['delivery_days_from_stock']} Werktagen"
        if stock["qty_from_stock"] == 0:
            return f"derzeit nicht auf Lager, Lieferzeit ca. {stock['delivery_days_for_rest']} Werktage"
        return (
            f"{stock['qty_from_stock']} Stück ab Lager (ca. {stock['delivery_days_from_stock']} Werktage), "
            f"Rest in ca. {stock['delivery_days_for_rest']} Werktagen"
        )

    if stock["fully_available"]:
        return f"in stock, delivery in approx. {stock['delivery_days_from_stock']} working days"
    if stock["qty_from_stock"] == 0:
        return f"currently out of stock, lead time approx. {stock['delivery_days_for_rest']} working days"
    return (
        f"{stock['qty_from_stock']} pcs from stock (approx. {stock['delivery_days_from_stock']} working days), "
        f"rest in approx. {stock['delivery_days_for_rest']} working days"
    )


def _line_text(number, name, part_no, quantity, unit_price, stock, language) -> str:
    price = _format_eur(unit_price, language)
    availability = _availability_text(stock, language)
    if language == "de":
        return f"{number}. {name} ({part_no}), {quantity} Stk., {price}/Stk., {availability}"
    return f"{number}. {name} ({part_no}), qty {quantity}, {price}/pc, {availability}"


def draft_reply(
    contact_name: str | None,
    items: list[dict],
    open_questions: list[str] | None = None,
    language: str = "de",
) -> dict:
    catalog = load_catalog()
    lines = []
    errors = []

    for item in items:
        part_no = item["part_no"]
        quantity = int(item["quantity"])
        rows = catalog[catalog["part_no"] == part_no]
        if rows.empty:
            errors.append(f"Unknown part number: {part_no}")
            continue

        part = rows.iloc[0]
        stock = check_stock(part_no, quantity)
        name = part["name_de"] if language == "de" else part["name_en"]
        unit_price = float(part["unit_price_eur"])
        line = _line_text(len(lines) + 1, name, part_no, quantity, unit_price, stock, language)
        lines.append(line)

    if errors:
        return {"ok": False, "errors": errors, "draft": None}

    questions = open_questions or []
    if language == "de":
        greeting = f"Guten Tag {contact_name}," if contact_name else "Guten Tag,"
        parts = [greeting, "", "vielen Dank für Ihre Anfrage."]
        if lines:
            parts += ["", "Gerne bieten wir Ihnen folgende Positionen an:", "", *lines]
        if questions:
            parts += ["", "Für die weitere Bearbeitung benötigen wir noch folgende Angaben:"]
            parts += [f"- {question}" for question in questions]
        if lines:
            parts += ["", "Alle Preise verstehen sich netto zzgl. MwSt."]
        parts += ["", "Mit freundlichen Grüßen", "Ihr Ersatzteil-Service"]
    else:
        greeting = f"Dear {contact_name}," if contact_name else "Hello,"
        parts = [greeting, "", "thank you for your request."]
        if lines:
            parts += ["", "We are pleased to offer the following items:", "", *lines]
        if questions:
            parts += ["", "To process your request, we still need the following information:"]
            parts += [f"- {question}" for question in questions]
        if lines:
            parts += ["", "All prices are net, plus VAT."]
        parts += ["", "Best regards", "Your Spare Parts Service"]

    return {"ok": True, "errors": [], "draft": "\n".join(parts)}

