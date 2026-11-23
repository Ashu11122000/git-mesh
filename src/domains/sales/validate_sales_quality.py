import json
from pathlib import Path
from datetime import datetime
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_FILE = (
    PROJECT_ROOT
    / "domains"
    / "sales"
    / "data"
    / "sales_transactions.json"
)


def load_dataset():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_sales_quality(dataset):
    records = dataset["records"]

    errors = []
    warnings = []

    # ---------------------------------------------------------
    # 1. Check transaction_id uniqueness
    # ---------------------------------------------------------
    transaction_ids = [
        record.get("transaction_id")
        for record in records
    ]

    id_counts = Counter(transaction_ids)

    duplicate_ids = [
        transaction_id
        for transaction_id, count in id_counts.items()
        if count > 1
    ]

    if duplicate_ids:
        errors.append(
            f"Duplicate transaction IDs found: {duplicate_ids}"
        )

    # ---------------------------------------------------------
    # 2. Check required business fields
    # ---------------------------------------------------------
    required_fields = [
        "transaction_id",
        "order_id",
        "product_id",
        "customer_id",
        "quantity",
        "unit_price",
        "total_amount",
        "transaction_timestamp",
    ]

    for index, record in enumerate(records, start=1):
        for field in required_fields:
            if field not in record or record[field] is None:
                errors.append(
                    f"Record {index}: Missing required field '{field}'"
                )

    # ---------------------------------------------------------
    # 3. Quantity must be positive
    # ---------------------------------------------------------
    for index, record in enumerate(records, start=1):
        quantity = record.get("quantity")

        if quantity is not None and quantity <= 0:
            errors.append(
                f"Record {index}: Quantity must be greater than zero"
            )

    # ---------------------------------------------------------
    # 4. Unit price must not be negative
    # ---------------------------------------------------------
    for index, record in enumerate(records, start=1):
        unit_price = record.get("unit_price")

        if unit_price is not None and unit_price < 0:
            errors.append(
                f"Record {index}: Unit price cannot be negative"
            )

    # ---------------------------------------------------------
    # 5. Total amount must not be negative
    # ---------------------------------------------------------
    for index, record in enumerate(records, start=1):
        total_amount = record.get("total_amount")

        if total_amount is not None and total_amount < 0:
            errors.append(
                f"Record {index}: Total amount cannot be negative"
            )

    # ---------------------------------------------------------
    # 6. Validate total_amount calculation
    # ---------------------------------------------------------
    for index, record in enumerate(records, start=1):
        quantity = record.get("quantity")
        unit_price = record.get("unit_price")
        total_amount = record.get("total_amount")

        if (
            quantity is not None
            and unit_price is not None
            and total_amount is not None
        ):
            expected_total = quantity * unit_price

            if abs(expected_total - total_amount) > 0.01:
                errors.append(
                    f"Record {index}: Total amount mismatch. "
                    f"Expected {expected_total}, "
                    f"but found {total_amount}"
                )

    # ---------------------------------------------------------
    # 7. Validate timestamp standardization
    # ---------------------------------------------------------
    timestamp_format = "%Y-%m-%dT%H:%M:%SZ"

    for index, record in enumerate(records, start=1):
        timestamp = record.get("transaction_timestamp")

        if timestamp:
            try:
                datetime.strptime(timestamp, timestamp_format)
            except ValueError:
                errors.append(
                    f"Record {index}: Timestamp does not follow "
                    "standard UTC format YYYY-MM-DDTHH:mm:ssZ"
                )

    # ---------------------------------------------------------
    # 8. Calculate dataset-level metrics
    # ---------------------------------------------------------
    total_records = len(records)

    total_units = sum(
        record.get("quantity", 0)
        for record in records
    )

    total_sales = sum(
        record.get("total_amount", 0)
        for record in records
    )

    unique_customers = len({
        record.get("customer_id")
        for record in records
    })

    unique_products = len({
        record.get("product_id")
        for record in records
    })

    # ---------------------------------------------------------
    # 9. Display validation report
    # ---------------------------------------------------------
    print("=" * 65)
    print("SALES DATA PRODUCT - DATA QUALITY VALIDATION")
    print("=" * 65)

    print("\nDATASET SUMMARY")
    print("-" * 65)
    print(f"Domain                 : {dataset['domain']}")
    print(f"Dataset               : {dataset['dataset_name']}")
    print(f"Total records          : {total_records}")
    print(f"Total units sold       : {total_units}")
    print(f"Total sales amount    : {total_sales:.2f}")
    print(f"Unique customers       : {unique_customers}")
    print(f"Unique products       : {unique_products}")

    print("\nDATA QUALITY CHECKS")
    print("-" * 65)

    if duplicate_ids:
        print("Transaction ID uniqueness : FAILED")
    else:
        print("Transaction ID uniqueness : PASSED")

    print(
        "Positive quantity         : "
        + ("FAILED" if any(
            record.get("quantity", 0) <= 0
            for record in records
        ) else "PASSED")
    )

    print(
        "Non-negative unit price   : "
        + ("FAILED" if any(
            record.get("unit_price", 0) < 0
            for record in records
        ) else "PASSED")
    )

    print(
        "Non-negative total amount : "
        + ("FAILED" if any(
            record.get("total_amount", 0) < 0
            for record in records
        ) else "PASSED")
    )

    print(
        "Total amount calculation : "
        + ("FAILED" if any(
            abs(
                record.get("quantity", 0)
                * record.get("unit_price", 0)
                - record.get("total_amount", 0)
            ) > 0.01
            for record in records
        ) else "PASSED")
    )

    print(
        "Timestamp standardization : "
        + ("FAILED" if any(
            not record.get("transaction_timestamp")
            for record in records
        ) else "PASSED")
    )

    print("\nVALIDATION RESULT")
    print("-" * 65)

    if errors:
        print("STATUS: FAILED")
        print(f"Total errors: {len(errors)}")

        for error in errors:
            print(f"- {error}")

    else:
        print("STATUS: PASSED")
        print("All Sales business data quality checks passed.")

    return len(errors) == 0


if __name__ == "__main__":
    dataset = load_dataset()
    validate_sales_quality(dataset)