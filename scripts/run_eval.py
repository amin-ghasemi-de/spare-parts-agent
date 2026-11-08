import argparse
import json
import time

from openai import RateLimitError

from src.agent import run_agent
from src.config import PROJECT_ROOT
from src.evaluation import load_ground_truth, run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agent on the evaluation set.")
    parser.add_argument("--run", type=int, default=1, help="Run number (1, 2, ...)")
    parser.add_argument("--pause", type=float, default=10, help="Seconds to wait between e-mails")
    parser.add_argument("--only", nargs="*", help="Only these e-mail ids, e.g. --only 001 008")
    args = parser.parse_args()

    output_dir = run_dir(args.run)
    output_dir.mkdir(parents=True, exist_ok=True)

    cases = load_ground_truth()
    if args.only:
        cases = [case for case in cases if case["id"] in args.only]

    for case in cases:
        output_file = output_dir / f"{case['id']}.json"
        if output_file.exists():
            print(f"{case['id']}: already done, skipping")
            continue

        email_text = (PROJECT_ROOT / case["file"]).read_text(encoding="utf-8")
        print(f"{case['id']}: running ...", end=" ", flush=True)
        try:
            result = run_agent(email_text).model_dump()
        except RateLimitError as error:
            print(f"\nRate limit reached, stopping. Run the same command again later.\n{error}")
            return
        except Exception as error:
            result = {"error": f"{type(error).__name__}: {error}"}

        output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"{result['status']}, {result['usage']['llm_calls']} calls, {result['duration_seconds']} s")
        time.sleep(args.pause)

    print("Done.")


if __name__ == "__main__":
    main()