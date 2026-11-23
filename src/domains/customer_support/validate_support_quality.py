import json
from pathlib import Path
from datetime import datetime
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_FILE = (
    PROJECT_ROOT
    / "domains"
    / "customer_support"
    / "data"
    / "support_tickets.json"
)

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def load_dataset():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_support_quality(dataset):
    records = dataset["records"]

    errors = []

    # ---------------------------------------------------------
    # 1. Ticket ID uniqueness
    # ---------------------------------------------------------
    ticket_ids = [
        record.get("ticket_id")
        for record in records
    ]

    ticket_counts = Counter(ticket_ids)

    duplicate_ticket_ids = [
        ticket_id
        for ticket_id, count in ticket_counts.items()
        if count > 1
    ]

    if duplicate_ticket_ids:
        errors.append(
            f"Duplicate ticket IDs found: {duplicate_ticket_ids}"
        )

    # ---------------------------------------------------------
    # 2. Required fields
    # ---------------------------------------------------------
    required_fields = [
        "ticket_id",
        "customer_id",
        "issue_category",
        "priority",
        "status",
        "created_timestamp",
        "resolved_timestamp",
        "resolution_hours",
    ]

    for index, record in enumerate(records, start=1):
        for field in required_fields:
            if field not in record:
                errors.append(
                    f"Record {index}: Missing field '{field}'"
                )

    # ---------------------------------------------------------
    # 3. Valid priority values
    # ---------------------------------------------------------
    valid_priorities = {"Low", "Medium", "High"}

    for index, record in enumerate(records, start=1):
        priority = record.get("priority")

        if priority not in valid_priorities:
            errors.append(
                f"Record {index}: Invalid priority '{priority}'"
            )

    # ---------------------------------------------------------
    # 4. Valid status values
    # ---------------------------------------------------------
    valid_statuses = {"Open", "In Progress", "Resolved"}

    for index, record in enumerate(records, start=1):
        status = record.get("status")

        if status not in valid_statuses:
            errors.append(
                f"Record {index}: Invalid status '{status}'"
            )

    # ---------------------------------------------------------
    # 5. Resolution duration must be non-negative
    # ---------------------------------------------------------
    for index, record in enumerate(records, start=1):
        resolution_hours = record.get("resolution_hours")

        if (
            resolution_hours is not None
            and resolution_hours < 0
        ):
            errors.append(
                f"Record {index}: Resolution hours cannot be negative"
            )

    # ---------------------------------------------------------
    # 6. Resolved tickets must contain resolution information
    # ---------------------------------------------------------
    for index, record in enumerate(records, start=1):
        if record.get("status") == "Resolved":
            if record.get("resolved_timestamp") is None:
                errors.append(
                    f"Record {index}: Resolved ticket is missing "
                    "resolved_timestamp"
                )

            if record.get("resolution_hours") is None:
                errors.append(
                    f"Record {index}: Resolved ticket is missing "
                    "resolution_hours"
                )

    # ---------------------------------------------------------
    # 7. Open and In Progress tickets must not have resolution data
    # ---------------------------------------------------------
    for index, record in enumerate(records, start=1):
        if record.get("status") in {"Open", "In Progress"}:
            if record.get("resolved_timestamp") is not None:
                errors.append(
                    f"Record {index}: Unresolved ticket has "
                    "resolved_timestamp"
                )

            if record.get("resolution_hours") is not None:
                errors.append(
                    f"Record {index}: Unresolved ticket has "
                    "resolution_hours"
                )

    # ---------------------------------------------------------
    # 8. Timestamp validity and ordering
    # ---------------------------------------------------------
    for index, record in enumerate(records, start=1):
        created_timestamp = record.get("created_timestamp")
        resolved_timestamp = record.get("resolved_timestamp")

        created_datetime = None
        resolved_datetime = None

        if created_timestamp:
            try:
                created_datetime = datetime.strptime(
                    created_timestamp,
                    TIMESTAMP_FORMAT
                )
            except ValueError:
                errors.append(
                    f"Record {index}: Invalid created_timestamp format"
                )

        if resolved_timestamp:
            try:
                resolved_datetime = datetime.strptime(
                    resolved_timestamp,
                    TIMESTAMP_FORMAT
                )
            except ValueError:
                errors.append(
                    f"Record {index}: Invalid resolved_timestamp format"
                )

        if (
            created_datetime is not None
            and resolved_datetime is not None
            and resolved_datetime < created_datetime
        ):
            errors.append(
                f"Record {index}: Resolution occurred before "
                "ticket creation"
            )

    # ---------------------------------------------------------
    # 9. Resolution hours must match timestamp difference
    # ---------------------------------------------------------
    for index, record in enumerate(records, start=1):
        created_timestamp = record.get("created_timestamp")
        resolved_timestamp = record.get("resolved_timestamp")
        resolution_hours = record.get("resolution_hours")

        if (
            created_timestamp
            and resolved_timestamp
            and resolution_hours is not None
        ):
            try:
                created_datetime = datetime.strptime(
                    created_timestamp,
                    TIMESTAMP_FORMAT
                )

                resolved_datetime = datetime.strptime(
                    resolved_timestamp,
                    TIMESTAMP_FORMAT
                )

                calculated_hours = (
                    resolved_datetime - created_datetime
                ).total_seconds() / 3600

                if abs(calculated_hours - resolution_hours) > 0.01:
                    errors.append(
                        f"Record {index}: Resolution hours mismatch. "
                        f"Expected {calculated_hours:.2f}, "
                        f"found {resolution_hours:.2f}"
                    )

            except ValueError:
                # Timestamp format errors are reported separately.
                pass

    # ---------------------------------------------------------
    # 10. Dataset metrics
    # ---------------------------------------------------------
    total_tickets = len(records)

    status_counts = Counter(
        record.get("status")
        for record in records
    )

    category_counts = Counter(
        record.get("issue_category")
        for record in records
    )

    resolved_records = [
        record
        for record in records
        if record.get("status") == "Resolved"
    ]

    unresolved_records = [
        record
        for record in records
        if record.get("status") in {"Open", "In Progress"}
    ]

    resolved_count = len(resolved_records)
    unresolved_count = len(unresolved_records)

    resolution_times = [
        record["resolution_hours"]
        for record in resolved_records
        if record.get("resolution_hours") is not None
    ]

    average_resolution_hours = (
        sum(resolution_times) / len(resolution_times)
        if resolution_times
        else 0
    )

    resolution_rate = (
        resolved_count / total_tickets * 100
        if total_tickets
        else 0
    )

    high_priority_count = sum(
        1
        for record in records
        if record.get("priority") == "High"
    )

    # ---------------------------------------------------------
    # 11. Print validation report
    # ---------------------------------------------------------
    print("=" * 65)
    print("CUSTOMER SUPPORT DATA PRODUCT - DATA QUALITY VALIDATION")
    print("=" * 65)

    print("\nDATASET SUMMARY")
    print("-" * 65)
    print(f"Domain                  : {dataset['domain']}")
    print(f"Dataset                : {dataset['dataset_name']}")
    print(f"Total tickets          : {total_tickets}")
    print(f"Resolved tickets       : {resolved_count}")
    print(f"Unresolved tickets     : {unresolved_count}")
    print(f"Resolution rate        : {resolution_rate:.2f}%")
    print(
        f"Average resolution time : "
        f"{average_resolution_hours:.2f} hours"
    )
    print(f"High-priority tickets  : {high_priority_count}")

    print("\nTICKET STATUS DISTRIBUTION")
    print("-" * 65)

    for status, count in sorted(status_counts.items()):
        print(f"{status:<20}: {count}")

    print("\nISSUE CATEGORY DISTRIBUTION")
    print("-" * 65)

    for category, count in sorted(category_counts.items()):
        print(f"{category:<20}: {count}")

    print("\nDATA QUALITY CHECKS")
    print("-" * 65)

    print(
        "Ticket ID uniqueness       : "
        + ("FAILED" if duplicate_ticket_ids else "PASSED")
    )

    print(
        "Required fields             : "
        + (
            "FAILED"
            if any("Missing field" in error for error in errors)
            else "PASSED"
        )
    )

    print(
        "Valid priority values       : "
        + (
            "FAILED"
            if any("Invalid priority" in error for error in errors)
            else "PASSED"
        )
    )

    print(
        "Valid status values         : "
        + (
            "FAILED"
            if any("Invalid status" in error for error in errors)
            else "PASSED"
        )
    )

    print(
        "Non-negative resolution time: "
        + (
            "FAILED"
            if any("cannot be negative" in error for error in errors)
            else "PASSED"
        )
    )

    print(
        "Resolution data consistency : "
        + (
            "FAILED"
            if any(
                "Resolved ticket is missing" in error
                or "Unresolved ticket has" in error
                for error in errors
            )
            else "PASSED"
        )
    )

    print(
        "Timestamp ordering          : "
        + (
            "FAILED"
            if any("Resolution occurred before" in error for error in errors)
            else "PASSED"
        )
    )

    print(
        "Resolution calculation      : "
        + (
            "FAILED"
            if any("Resolution hours mismatch" in error for error in errors)
            else "PASSED"
        )
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
        print("All Customer Support business data quality checks passed.")

    return len(errors) == 0


if __name__ == "__main__":
    dataset = load_dataset()
    validate_support_quality(dataset)