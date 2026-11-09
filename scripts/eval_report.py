import json

from src.evaluation import RESULTS_DIR, consistency, load_ground_truth, score_case, summarize


def main() -> None:
    truths = {case["id"]: case for case in load_ground_truth()}

    scores_by_run: dict[int, list[dict]] = {}
    for folder in sorted(RESULTS_DIR.glob("run_*")):
        run = int(folder.name.removeprefix("run_"))
        scores = []
        for result_file in sorted(folder.glob("*.json")):
            case_id = result_file.stem
            if case_id in truths:
                result = json.loads(result_file.read_text(encoding="utf-8"))
                scores.append(score_case(truths[case_id], result))
        scores_by_run[run] = scores

    if not any(scores_by_run.values()):
        print("No results found. Run: python -m scripts.run_eval --run 1")
        return

    last_run = max(scores_by_run)
    latest = scores_by_run[last_run]
    columns = {f"run {run} (all)": scores for run, scores in scores_by_run.items()}
    columns[f"run {last_run}: dev"] = [s for s in latest if s["split"] == "dev"]
    columns[f"run {last_run}: held-out"] = [s for s in latest if s["split"] == "test"]
    summaries = {name: summarize(scores) for name, scores in columns.items()}

    lines = ["# Evaluation report", ""]
    lines.append(f"Runs: {', '.join(str(run) for run in scores_by_run)}")
    lines.append(f"Same offer in every run (consistency): {consistency(scores_by_run)}")
    lines.append("")
    lines.append("| Metric | " + " | ".join(summaries) + " |")
    lines.append("|---|" + "---|" * len(summaries))
    first = next(iter(summaries.values()))
    for metric in first:
        values = [summaries[name].get(metric, "–") for name in summaries]
        lines.append(f"| {metric} | " + " | ".join(values) + " |")

    lines += ["", "## Per e-mail", "", "| Run | Id | Split | Offer exact | Asked ok | Wrong parts | Offered | Extraction issues | Note |"]
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for run, scores in scores_by_run.items():
        for s in scores:
            note = truths[s["id"]]["note"]
            if s["error"]:
                lines.append(f"| {run} | {s['id']} | {s['split']} | ERROR | | | {s['error'][:60]} | | {note} |")
                continue
            if "offer_exact" not in s:
                status = "ok" if s["request_ok"] else "WRONG"
                lines.append(f"| {run} | {s['id']} | {s['split']} | not a request: {status} | | | | | {note} |")
                continue
            ask = "–" if s["ask_ok"] is None else ("yes" if s["ask_ok"] else "NO")
            offer = "yes" if s["offer_exact"] else "NO"
            offered = ", ".join(f"{p}×{q}" for p, q in s["offered"].items()) or "none"
            issues = ", ".join(s["extraction_issues"]) or "–"
            lines.append(
                f"| {run} | {s['id']} | {s['split']} | {offer} | {ask} | {s['wrong_parts']} | {offered} "
                f"| {issues} | {note} |"
            )

    report = "\n".join(lines) + "\n"
    report_file = RESULTS_DIR / "report.md"
    report_file.write_text(report, encoding="utf-8")
    print(report)
    print(f"Saved to {report_file}")


if __name__ == "__main__":
    main()