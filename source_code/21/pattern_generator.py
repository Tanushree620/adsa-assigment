import csv
import random
import json
import unicodedata
from pathlib import Path

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

RESULT_DIR = BASE_DIR / "results"
QUERY_DIR = BASE_DIR / "queries"

QUERY_DIR.mkdir(parents=True, exist_ok=True)

BASE_SEED = 42

PATTERNS_PER_TYPE = 50

MAX_ATTEMPTS_MULTIPLIER = 200

PATTERN_CATEGORIES = {
    "short": (2, 3),
    "medium": (4, 6),
    "long": (7, 10),
    "very_long": (11, 15),
}

LANGUAGE_OFFSETS = {
    "tulu": 1000,
    "kannada": 2000,
    "english": 3000,
}


# --------------------------------------------------
# LOAD SAMPLED TITLES
# --------------------------------------------------


def load_titles(file_path):
    """
    Load title_nfc values from a sampled CSV.
    """

    titles = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or "title_nfc" not in reader.fieldnames:
            raise ValueError(f"Missing title_nfc column in {file_path}")

        for row in reader:
            title = row["title_nfc"]

            if not title:
                continue

            if unicodedata.normalize("NFC", title) != title:
                raise ValueError(f"Non-NFC title encountered: {title!r}")

            titles.append(title)

    return titles


# --------------------------------------------------
# EXTRACT RANDOM SUBSTRING
# --------------------------------------------------


def generate_substring(title, min_length, max_length, rng):
    """
    Extract a random substring using Python Unicode
    code-point indexing.
    """

    possible_lengths = [
        length for length in range(min_length, max_length + 1) if length <= len(title)
    ]

    if not possible_lengths:
        return None

    length = rng.choice(possible_lengths)

    start = rng.randrange(len(title) - length + 1)

    return title[start : start + length]


# --------------------------------------------------
# GENERATE ONE PATTERN
# --------------------------------------------------


def generate_pattern(titles, pattern_type, min_length, max_length, rng):
    """
    Generate either a matching or non-matching pattern.

    Matching:
        Pattern must occur in target title.

    Non-matching:
        Pattern is extracted from another title
        and must not occur in target title.
    """

    target = rng.choice(titles)

    if pattern_type == "matching":
        pattern = generate_substring(target, min_length, max_length, rng)

        if pattern is None:
            return None

        if pattern not in target:
            return None

        pattern_source = target

    else:
        # Select a different title as the donor.
        donor = rng.choice(titles)

        if donor == target:
            return None

        pattern = generate_substring(donor, min_length, max_length, rng)

        if pattern is None:
            return None

        # Reject patterns that occur in target.
        if pattern in target:
            return None

        pattern_source = donor

    expected_position = target.find(pattern)

    return {
        "target_title": target,
        "pattern": pattern,
        "pattern_source_title": pattern_source,
        "pattern_length": len(pattern),
        "pattern_type": pattern_type,
        "expected_found": expected_position != -1,
        "expected_position": expected_position,
    }


# --------------------------------------------------
# GENERATE PATTERN WORKLOAD
# --------------------------------------------------


def generate_patterns(titles, language, sample_size, seed):

    rng = random.Random(seed)

    records = []

    # Avoid duplicate target-pattern combinations
    # within the same category and pattern type.
    seen = set()

    for category, (min_length, max_length) in PATTERN_CATEGORIES.items():
        for pattern_type in ("matching", "non_matching"):
            generated = 0
            attempts = 0

            max_attempts = PATTERNS_PER_TYPE * MAX_ATTEMPTS_MULTIPLIER

            while generated < PATTERNS_PER_TYPE and attempts < max_attempts:
                attempts += 1

                result = generate_pattern(
                    titles, pattern_type, min_length, max_length, rng
                )

                if result is None:
                    continue

                target = result["target_title"]
                pattern = result["pattern"]

                unique_key = (category, pattern_type, target, pattern)

                if unique_key in seen:
                    continue

                seen.add(unique_key)

                # Verify the expected result independently.
                actual_position = target.find(pattern)

                if actual_position != result["expected_position"]:
                    raise AssertionError("Expected position validation failed")

                if pattern_type == "matching":
                    if actual_position == -1:
                        raise AssertionError("Matching pattern not found")

                else:
                    if actual_position != -1:
                        raise AssertionError("Non-matching pattern was found")

                records.append(
                    {
                        "language": language,
                        "sample_size": sample_size,
                        "pattern_category": category,
                        "pattern_type": pattern_type,
                        "target_title": target,
                        "pattern": pattern,
                        "pattern_source_title": (result["pattern_source_title"]),
                        "pattern_length": len(pattern),
                        "expected_found": (result["expected_found"]),
                        "expected_position": (result["expected_position"]),
                        "random_seed": seed,
                    }
                )

                generated += 1

            if generated < PATTERNS_PER_TYPE:
                print(
                    f"WARNING: {language}, "
                    f"{category}, {pattern_type}: "
                    f"generated {generated}/"
                    f"{PATTERNS_PER_TYPE} patterns"
                )

    return records


# --------------------------------------------------
# SAVE GENERATED PATTERNS
# --------------------------------------------------


def save_patterns(records, output_path):

    if not records:
        print(f"No patterns generated for {output_path}")
        return

    fieldnames = list(records[0].keys())

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(records)


# --------------------------------------------------
# GENERATE SUMMARY
# --------------------------------------------------


def generate_summary(records):

    summary = {}

    for category in PATTERN_CATEGORIES:
        summary[category] = {
            "matching": 0,
            "non_matching": 0,
        }

    for record in records:
        category = record["pattern_category"]
        pattern_type = record["pattern_type"]

        summary[category][pattern_type] += 1

    return summary


# --------------------------------------------------
# MAIN
# --------------------------------------------------


def main():

    sample_files = sorted(RESULT_DIR.glob("*_sample.csv"))

    if not sample_files:
        raise FileNotFoundError("No sampled CSV files found in results/")

    generation_manifest = {}

    for sample_file in sample_files:
        # Example:
        # english_1000_sample.csv

        parts = sample_file.stem.split("_")

        if len(parts) != 3:
            print(f"Skipping unexpected file: {sample_file}")
            continue

        language = parts[0]
        sample_size = int(parts[1])

        if language not in LANGUAGE_OFFSETS:
            print(f"Unknown language: {language}")
            continue

        seed = BASE_SEED + LANGUAGE_OFFSETS[language] + sample_size + 100000

        print("\n--------------------------------")
        print(f"Language: {language.upper()}")
        print(f"Sample size: {sample_size}")
        print("--------------------------------")

        titles = load_titles(sample_file)

        print(f"Loaded titles: {len(titles)}")

        records = generate_patterns(titles, language, sample_size, seed)

        output_path = QUERY_DIR / f"{language}_{sample_size}_patterns.csv"

        save_patterns(records, output_path)

        summary = generate_summary(records)

        generation_manifest[f"{language}_{sample_size}"] = {
            "sample_file": sample_file.name,
            "output_file": output_path.name,
            "language": language,
            "sample_size": sample_size,
            "pattern_seed": seed,
            "patterns_generated": len(records),
            "patterns_per_type_requested": (PATTERNS_PER_TYPE),
            "category_summary": summary,
        }

        print(f"\nPatterns generated: {len(records)}")
        print(f"Saved: {output_path}")

        for category, counts in summary.items():
            print(
                f"{category}: "
                f"Matching={counts['matching']}, "
                f"Non-matching={counts['non_matching']}"
            )

    # Save generation metadata.
    manifest_path = QUERY_DIR / "pattern_generation_manifest.json"

    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(generation_manifest, file, indent=4, ensure_ascii=False)

    print("\n================================")
    print("PATTERN GENERATION COMPLETED")
    print("================================")
    print(f"Workloads generated: {len(generation_manifest)}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
