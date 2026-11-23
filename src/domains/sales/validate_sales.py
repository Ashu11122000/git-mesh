
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_FILE = (
    PROJECT_ROOT
    / "domains"
    / "sales"
    / "data"
    / "sales_transactions.json"
)

SCHEMA_FILE = (
    PROJECT_ROOT
    / "domains"
    / "sales"
    / "schemas"
    / "sales_transactions.schema.json"
)


# ---------------------------------------------------------
# Load JSON files
# ---------------------------------------------------------

def load_json_file(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------
# Schema validation
# ---------------------------------------------------------

def validate_sales_dataset():
    dataset = load_json_file(DATA_FILE)
    schema = load_json_file(SCHEMA_FILE)

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker()
    )

    errors = sorted(
        validator.iter_errors(dataset),
        key=lambda error: list(error.path)
    )

    print("=" * 60)
    print("SALES DATA PRODUCT SCHEMA VALIDATION")
    print("=" * 60)

    if errors:
        print("\nVALIDATION STATUS: FAILED")
        print(f"Total validation errors: {len(errors)}")

        for error in errors:
            location = ".".join(str(item) for item in error.path)
            print(f"\nError location: {location or 'Dataset root'}")
            print(f"Error message: {error.message}")

        return False

    print("\nVALIDATION STATUS: PASSED")
    print("Dataset successfully complies with the Sales JSON Schema.")
    print(f"Domain: {dataset['domain']}")
    print(f"Dataset: {dataset['dataset_name']}")
    print(f"Records validated: {len(dataset['records'])}")

    return True


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    validate_sales_dataset()
