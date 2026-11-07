import pandas as pd

from src.config import PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "data"


def main() -> None:
    catalog = pd.read_csv(DATA_DIR / "parts_catalog.csv", encoding="utf-8")
    stock = pd.read_csv(DATA_DIR / "stock.csv", encoding="utf-8")

    print(f"Catalog: {len(catalog)} parts")
    print(f"Stock:   {len(stock)} rows")

    print("\nParts per machine model:")
    models = catalog["compatible_models"].str.split(";").explode()
    print(models.value_counts().to_string())

    missing = set(catalog["part_no"]) - set(stock["part_no"])
    extra = set(stock["part_no"]) - set(catalog["part_no"])
    print(f"\nParts without stock entry: {sorted(missing) or 'none'}")
    print(f"Stock entries without part: {sorted(extra) or 'none'}")

    out_of_stock = stock[stock["qty_available"] == 0]["part_no"].tolist()
    print(f"Out of stock: {out_of_stock}")

    email_files = sorted((DATA_DIR / "emails").glob("*.txt"))
    print(f"\nE-mails found: {len(email_files)}")
    for path in email_files:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        print(f" - {path.name}: {first_line}")


if __name__ == "__main__":
    main() 