import json
import sys

from src.agent import run_agent
from src.config import PROJECT_ROOT

EMAIL_DIR = PROJECT_ROOT / "data" / "emails"


def main() -> None:
    file_name = sys.argv[1] if len(sys.argv) > 1 else "email_001.txt"
    email_text = (EMAIL_DIR / file_name).read_text(encoding="utf-8")

    result = run_agent(email_text)

    print(f"=== {file_name} | status: {result.status} | steps: {result.steps_used} ===\n")
    print("--- Tool calls ---")
    for number, record in enumerate(result.trace, start=1):
        print(f"{number}. {record.tool}({json.dumps(record.arguments, ensure_ascii=False)})")
        short_result = json.dumps(record.result, ensure_ascii=False)
        print(f"   -> {short_result[:200]}{'...' if len(short_result) > 200 else ''}")

    print("\n--- Draft ---")
    print(result.draft or "(no draft)")
    print("\n--- Summary for employee ---")
    print(result.summary or "(no summary)")


if __name__ == "__main__":
    main()