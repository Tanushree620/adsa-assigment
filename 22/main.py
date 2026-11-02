
import csv
import json
import time
import statistics
import unicodedata
from pathlib import Path

from naive import naive_search

# Project directories
BASE_DIR = Path(__file__).resolve().parents[1]
QUERY_DIR = BASE_DIR / "queries"
RESULT_DIR = BASE_DIR / "results"

RESULT_DIR.mkdir(parents=True, exist_ok=True)

REPEATS = 10


def run_experiment(query_file):

    results = []
    passed = 0
    failed = 0
    total_comparisons = 0
    total_found = 0
    total_not_found = 0
    execution_times = []

    with open(query_file, "r", encoding="utf-8-sig",
              newline="") as file:

        reader = csv.DictReader(file)

        required = [
            "language", "sample_size",
            "pattern_category", "pattern_type",
            "target_title", "pattern",
            "expected_position"
        ]

        for column in required:
            if column not in (reader.fieldnames or []):
                raise ValueError(f"Missing column: {column}")

        for row in reader:

            title = unicodedata.normalize(
                "NFC", row["target_title"]
            )
            pattern = unicodedata.normalize(
                "NFC", row["pattern"]
            )

            expected = int(row["expected_position"])

            times = []

            for _ in range(REPEATS):
                start = time.perf_counter_ns()

                position, comparisons = naive_search(
                    title, pattern
                )

                end = time.perf_counter_ns()
                times.append(end - start)

            median_time = statistics.median(times)

            # Validate using Python's reference search
            reference_position = title.find(pattern)

            correct = (
                position == expected
                and position == reference_position
            )

            if correct:
                passed += 1
            else:
                failed += 1

            if position == -1:
                total_not_found += 1
            else:
                total_found += 1

            total_comparisons += comparisons
            execution_times.append(median_time)

            results.append({
                "language": row["language"],
                "sample_size": row["sample_size"],
                "pattern_category": row["pattern_category"],
                "pattern_type": row["pattern_type"],
                "target_title": title,
                "pattern": pattern,
                "position": position,
                "expected_position": expected,
                "comparisons": comparisons,
                "execution_time_ns": median_time,
                "correct": correct
            })

    summary = {
        "algorithm": "Naive String Matching",
        "input_file": query_file.name,
        "total_queries": len(results),
        "total_found": total_found,
        "total_not_found": total_not_found,
        "total_comparisons": total_comparisons,
        "average_execution_time_ns": (
            statistics.mean(execution_times)
            if execution_times else 0
        ),
        "passed": passed,
        "failed": failed,
        "all_correct": failed == 0
    }

    return results, summary


def save_results(results, summary, query_file):

    name = query_file.stem.replace("_patterns", "")

    csv_path = RESULT_DIR / f"naive_{name}_results.csv"
    json_path = RESULT_DIR / f"naive_{name}_summary.json"

    if results:
        with open(csv_path, "w", encoding="utf-8",
                  newline="") as file:

            writer = csv.DictWriter(
                file, fieldnames=results[0].keys()
            )
            writer.writeheader()
            writer.writerows(results)

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)

    print("Saved:", csv_path.name)
    print("Saved:", json_path.name)


def main():

    query_files = sorted(
        QUERY_DIR.glob("*_patterns.csv")
    )

    if not query_files:
        raise FileNotFoundError(
            "No pattern CSV files found in queries folder."
        )

    for query_file in query_files:

        print("\nProcessing:", query_file.name)

        results, summary = run_experiment(query_file)

        save_results(results, summary, query_file)

        print("\nExperiment summary:")

        for key, value in summary.items():
            print(f"{key}: {value}")

    print("\nAll Naive experiments completed!")


if __name__ == "__main__":
    main()

