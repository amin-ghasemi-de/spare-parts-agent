from src.config import PROJECT_ROOT
from src.extractor import extract_request

EMAIL_DIR = PROJECT_ROOT / "data" / "emails"


def main() -> None:
    for path in sorted(EMAIL_DIR.glob("*.txt")):
        email_text = path.read_text(encoding="utf-8")

        print("=" * 70)
        print(path.name)
        print("=" * 70)

        try:
            result = extract_request(email_text)
            print(result.model_dump_json(indent=2))
        except Exception as error:
            print(f"ERROR: {error}")

        print()


if __name__ == "__main__":
    main()