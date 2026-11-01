import csv
import json
import random
import unicodedata
from pathlib import Path

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets"
RESULT_DIR = BASE_DIR / "results"

RESULT_DIR.mkdir(parents=True, exist_ok=True)

BASE_SEED = 42

DATASETS = {
    "tulu": {
        "file": "tulu_titles.csv",
        "sizes": [1000, 4536],
        "seed_offset": 1000,
    },
    "kannada": {
        "file": "kannada_titles.csv",
        "sizes": [1000, 5000, 10000, 25000],
        "seed_offset": 2000,
    },
    "english": {
        "file": "english_titles.csv",
        "sizes": [1000, 5000, 10000, 25000],
        "seed_offset": 3000,
    },
}


# --------------------------------------------------
# RESERVOIR SAMPLING
# --------------------------------------------------


def reservoir_sample(file_path, sample_size, seed):
    """
    Select a uniform random sample without loading
    the complete CSV into memory.

    Only title_nfc is used as the search representation.
    All original CSV columns are preserved.
    """

    rng = random.Random(seed)

    reservoir = []
    valid_count = 0
    fieldnames = None

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames

        if not fieldnames or "title_nfc" not in fieldnames:
            raise ValueError(f"Missing title_nfc column in {file_path}")

        for row in reader:
            title = row["title_nfc"]

            # Ignore empty titles.
            if not title:
                continue

            # Ensure the selected representation is NFC.
            if unicodedata.normalize("NFC", title) != title:
                raise ValueError(f"Non-NFC title found: {title!r}")

            # Fill the reservoir initially.
            if valid_count < sample_size:
                reservoir.append(row)

            else:
                # Select a random replacement position.
                position = rng.randrange(valid_count + 1)

                if position < sample_size:
                    reservoir[position] = row

            valid_count += 1

    if valid_count < sample_size:
        raise ValueError(
            f"Requested {sample_size} titles, "
            f"but only {valid_count} valid titles exist."
        )

    return reservoir, fieldnames, valid_count


# --------------------------------------------------
# SAVE CSV
# --------------------------------------------------


def save_sample(rows, fieldnames, output_path):

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------
# MAIN
# --------------------------------------------------


def main():

    sampling_manifest = {}

    for language, config in DATASETS.items():
        print(f"\nProcessing {language.upper()} dataset")

        dataset_path = DATASET_DIR / config["file"]

        if not dataset_path.exists():
            raise FileNotFoundError(dataset_path)

        requested_sizes = sorted(config["sizes"])
        maximum_size = max(requested_sizes)

        # One complete CSV pass per language.
        # Retain only the largest required reservoir.
        reservoir_seed = BASE_SEED + config["seed_offset"]

        reservoir, fieldnames, total_titles = reservoir_sample(
            dataset_path, maximum_size, reservoir_seed
        )

        print(f"Valid titles found: {total_titles}")

        for size in requested_sizes:
            sample_seed = BASE_SEED + config["seed_offset"] + size

            rng = random.Random(sample_seed)

            # Each smaller sample is selected uniformly
            # from the maximum-size reservoir.
            sampled_rows = rng.sample(reservoir, size)

            output_path = RESULT_DIR / f"{language}_{size}_sample.csv"

            save_sample(sampled_rows, fieldnames, output_path)

            sampling_manifest[f"{language}_{size}"] = {
                "language": language,
                "source_file": config["file"],
                "sample_file": output_path.name,
                "sample_size": size,
                "valid_titles_in_source": total_titles,
                "sampling_method": "Reservoir sampling",
                "sampling_seed": reservoir_seed,
                "subsample_seed": sample_seed,
                "search_column": "title_nfc",
                "normalization": "Unicode NFC",
                "random_sampling": True,
            }

            print(f"Saved {size:,} titles: {output_path}")

    # Save sampling metadata.
    manifest_path = RESULT_DIR / "sampling_manifest.json"

    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(sampling_manifest, file, indent=4, ensure_ascii=False)

    print("\n--------------------------------")
    print("DATASET SAMPLING COMPLETED")
    print("--------------------------------")
    print(f"Sample files: {len(sampling_manifest)}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
