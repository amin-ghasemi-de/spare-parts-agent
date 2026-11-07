from src.tools import check_stock, search_part_catalog


def top_part_no(result: dict) -> str:
    return result["results"][0]["part_no"]


def test_exact_part_number_is_found():
    result = search_part_catalog("HPC-SEA-110")
    assert result["exact_part_no_match"] is True
    assert top_part_no(result) == "HPC-SEA-110"


def test_part_number_with_spaces_is_found():
    result = search_part_catalog("hpc sea 110")
    assert result["exact_part_no_match"] is True
    assert top_part_no(result) == "HPC-SEA-110"


def test_machine_model_decides_between_same_names():
    result_300 = search_part_catalog("Kolbenringsatz", machine_model="HPC-300")
    result_500 = search_part_catalog("Kolbenringsatz", machine_model="HPC-500")
    assert top_part_no(result_300) == "HPC-SEA-110"
    assert top_part_no(result_500) == "HPC-SEA-210"


def test_english_name_is_found():
    result = search_part_catalog("breakaway coupling", machine_model="H2D-700")
    assert top_part_no(result) == "H2D-BRK-303"


def test_wrong_part_number_is_not_an_exact_match():
    result = search_part_catalog("HPC-VLV-220", machine_model="HPC-500")
    assert result["exact_part_no_match"] is False


def test_description_finds_correct_part_for_wrong_number():
    result = search_part_catalog("Druckventil (komplett)", machine_model="HPC-500")
    assert top_part_no(result) == "HPC-VLV-202"


def test_ambiguous_request_returns_both_sizes():
    result = search_part_catalog("Rückschlagventil", machine_model="H2D-350")
    part_numbers = [r["part_no"] for r in result["results"][:2]]
    assert set(part_numbers) == {"H2D-VLV-310", "H2D-VLV-311"}


def test_unknown_part_returns_no_results():
    result = search_part_catalog("Kaffeemaschine")
    assert result["results"] == []


def test_stock_fully_available():
    result = check_stock("HPC-SEA-110", 2)
    assert result["fully_available"] is True
    assert result["qty_to_order"] == 0


def test_stock_out_of_stock():
    result = check_stock("H2D-BRK-303", 1)
    assert result["fully_available"] is False
    assert result["qty_from_stock"] == 0
    assert result["delivery_days_for_rest"] == 30


def test_stock_partially_available():
    result = check_stock("HPC-SEA-210", 3)
    assert result["qty_from_stock"] == 1
    assert result["qty_to_order"] == 2


def test_stock_unknown_part():
    result = check_stock("XYZ-000", 1)
    assert result["found"] is False