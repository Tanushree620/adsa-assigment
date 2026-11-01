import csv
from pathlib import Path
from collections import Counter
import unicodedata

BASE_DIR = Path(__file__).resolve().parent.parent

RESULT_DIR = BASE_DIR / "results"
QUERY_DIR = BASE_DIR / "queries"

EXPECTED_PER_TYPE = 50

CATEGORY_LENGTHS = {
    "short": (2, 3),
    "medium": (4, 6),
    "long": (7, 10),
    "very_long": (11, 15),
}


def validate_workload(pattern_file):

    sample_name = pattern_file.stem.replace("_patterns", "_sample") + ".csv"

    sample_file = RESULT_DIR / sample_name

    if not sample_file.exists():
        raise FileNotFoundError(sample_file)

    with open(sample_file, encoding="utf-8-sig") as f:
        sampled_titles = {row["title_nfc"] for row in csv.DictReader(f)}

    counts = Counter()
    errors = []

    with open(pattern_file, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            title = row["target_title"]
            pattern = row["pattern"]
            pattern_type = row["pattern_type"]
            category = row["pattern_category"]

            expected_position = int(row["expected_position"])

            expected_found = row["expected_found"].lower() == "true"

            actual_position = title.find(pattern)

            # Check sample membership.
            if title not in sampled_titles:
                errors.append("Target not in sample")

            # Check Unicode NFC.
            if (
                unicodedata.normalize("NFC", title) != title
                or unicodedata.normalize("NFC", pattern) != pattern
            ):
                errors.append("Unicode NFC validation failed")

            # Check pattern length.
            if len(pattern) != int(row["pattern_length"]):
                errors.append("Pattern length mismatch")

            minimum, maximum = CATEGORY_LENGTHS[category]

            if not minimum <= len(pattern) <= maximum:
                errors.append("Pattern category mismatch")

            # Check expected position.
            if actual_position != expected_position:
                errors.append("Expected position mismatch")

            if (actual_position != -1) != expected_found:
                errors.append("Expected match status mismatch")

            # Check pattern type.
            if pattern_type == "matching":
                if actual_position == -1:
                    errors.append("Invalid matching pattern")

            elif pattern_type == "non_matching":
                if actual_position != -1:
                    errors.append("Invalid non-matching pattern")

            else:
                errors.append("Unknown pattern type")

            # Check pattern source.
            source = row["pattern_source_title"]

            if pattern not in source:
                errors.append("Pattern absent from source title")

            if pattern_type == "non_matching" and source == title:
                errors.append("Non-matching donor equals target")

            counts[(category, pattern_type)] += 1

    # Check expected workload balance.
    for category in CATEGORY_LENGTHS:
        for pattern_type in ("matching", "non_matching"):
            actual = counts[(category, pattern_type)]

            if actual != EXPECTED_PER_TYPE:
                errors.append(
                    f"{category}/{pattern_type}: "
                    f"expected {EXPECTED_PER_TYPE}, got {actual}"
                )

    print(f"\nChecking: {pattern_file.name}")
    print(f"Total patterns: {sum(counts.values())}")

    if errors:
        print(f"FAILED: {len(errors)} validation errors")

        for error in errors[:20]:
            print(" -", error)

        return False

    print("PASSED: All validation checks successful")
    return True


def main():

    pattern_files = sorted(QUERY_DIR.glob("*_patterns.csv"))

    if not pattern_files:
        raise FileNotFoundError("No pattern files found")

    successful = 0

    for file in pattern_files:
        if validate_workload(file):
            successful += 1

    print("\n==============================")
    print("VALIDATION SUMMARY")
    print("==============================")
    print(f"Workloads checked: {len(pattern_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(pattern_files) - successful}")

    if successful != len(pattern_files):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
