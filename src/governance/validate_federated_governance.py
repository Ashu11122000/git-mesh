import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

GOVERNANCE_CONFIG = (
    PROJECT_ROOT
    / "governance"
    / "federated_governance_standards.json"
)

DOMAINS = {
    "sales": {
        "metadata": (
            PROJECT_ROOT
            / "domains"
            / "sales"
            / "metadata"
            / "sales_transactions_metadata.json"
        ),
        "contract": (
            PROJECT_ROOT
            / "domains"
            / "sales"
            / "data_product"
            / "sales_data_product.json"
        ),
    },
    "customer_support": {
        "metadata": (
            PROJECT_ROOT
            / "domains"
            / "customer_support"
            / "metadata"
            / "support_tickets_metadata.json"
        ),
        "contract": (
            PROJECT_ROOT
            / "domains"
            / "customer_support"
            / "data_product"
            / "support_data_product.json"
        ),
    },
}


def load_json(file_path):
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def check_required_fields(data, required_fields, context):
    errors = []

    for field in required_fields:
        if field not in data:
            errors.append(
                f"{context}: Missing required field '{field}'"
            )

    return errors


def validate_metadata(metadata, standards, domain_name):
    errors = []

    required_fields = standards["required_metadata_fields"]

    errors.extend(
        check_required_fields(
            metadata,
            required_fields,
            f"{domain_name} metadata"
        )
    )

    # ---------------------------------------------------------
    # Domain identification
    # ---------------------------------------------------------
    if metadata.get("domain") != domain_name:
        errors.append(
            f"{domain_name}: Metadata domain does not match "
            "the expected domain"
        )

    # ---------------------------------------------------------
    # Dataset classification
    # ---------------------------------------------------------
    dataset = metadata.get("dataset", {})
    classification = dataset.get("classification")

    allowed_classifications = (
        standards["allowed_classifications"]
    )

    if classification not in allowed_classifications:
        errors.append(
            f"{domain_name}: Invalid classification "
            f"'{classification}'"
        )

    # ---------------------------------------------------------
    # Dataset format
    # ---------------------------------------------------------
    dataset_format = dataset.get("format")

    allowed_formats = standards["allowed_formats"]

    if dataset_format not in allowed_formats:
        errors.append(
            f"{domain_name}: Unsupported dataset format "
            f"'{dataset_format}'"
        )

    # ---------------------------------------------------------
    # Metadata tag validation
    # ---------------------------------------------------------
    metadata_tags = metadata.get("metadata_tags", [])

    required_tag_categories = (
        standards["required_metadata_tags"]
    )

    actual_tag_categories = {
        tag.split(":", 1)[0]
        for tag in metadata_tags
        if isinstance(tag, str) and ":" in tag
    }

    missing_tag_categories = [
        category
        for category in required_tag_categories
        if category not in actual_tag_categories
    ]

    if missing_tag_categories:
        errors.append(
            f"{domain_name}: Missing metadata tag categories "
            f"{missing_tag_categories}"
        )

    # ---------------------------------------------------------
    # Timestamp standardization
    # ---------------------------------------------------------
    standardization = metadata.get("standardization", {})
    timestamp_standard = standards["timestamp_standard"]

    if (
        standardization.get("timestamp_format")
        != timestamp_standard["format"]
    ):
        errors.append(
            f"{domain_name}: Timestamp format does not match "
            "the federated standard"
        )

    if (
        standardization.get("timezone")
        != timestamp_standard["timezone"]
    ):
        errors.append(
            f"{domain_name}: Timezone does not match "
            "the federated standard"
        )

    return errors


def validate_contract(contract, standards, domain_name):
    errors = []

    required_contract_fields = (
        standards["required_data_product_contract_fields"]
    )

    errors.extend(
        check_required_fields(
            contract,
            required_contract_fields,
            f"{domain_name} contract"
        )
    )

    # ---------------------------------------------------------
    # Ownership validation
    # ---------------------------------------------------------
    ownership = contract.get("ownership", {})
    publishing = contract.get("publishing_principles", {})

    # Sales contract uses publishing_principles for ownership.
    # Support contract also includes ownership.domain_owned.
    domain_owned = (
        ownership.get("domain_owned")
        or publishing.get("domain_owned")
    )

    if domain_owned is not True:
        errors.append(
            f"{domain_name}: Domain ownership must be enabled"
        )

    # ---------------------------------------------------------
    # Raw-data centralization validation
    # ---------------------------------------------------------
    if (
        publishing.get("raw_data_centralized")
        is not False
    ):
        errors.append(
            f"{domain_name}: Raw data centralization "
            "must be prohibited"
        )

    # ---------------------------------------------------------
    # Schema ownership
    # ---------------------------------------------------------
    if (
        publishing.get("schema_owned_by_domain")
        is not True
    ):
        errors.append(
            f"{domain_name}: Schema must be owned by its domain"
        )

    # ---------------------------------------------------------
    # Metadata ownership
    # ---------------------------------------------------------
    if (
        publishing.get("metadata_owned_by_domain")
        is not True
    ):
        errors.append(
            f"{domain_name}: Metadata must be owned by its domain"
        )

    # ---------------------------------------------------------
    # Governance compliance
    # ---------------------------------------------------------
    if (
        publishing.get("governance_compliance_required")
        is not True
    ):
        errors.append(
            f"{domain_name}: Governance compliance "
            "must be required"
        )

    # ---------------------------------------------------------
    # Required metadata tags in contract
    # ---------------------------------------------------------
    metadata_contract = contract.get("metadata_contract", {})

    if not metadata_contract.get("metadata_required", False):
        errors.append(
            f"{domain_name}: Metadata must be required "
            "by the contract"
        )

    contract_tags = metadata_contract.get("required_tags", [])

    required_categories = standards["required_metadata_tags"]

    contract_tag_categories = {
        tag.split(":", 1)[0]
        for tag in contract_tags
        if isinstance(tag, str) and ":" in tag
    }

    missing_contract_categories = [
        category
        for category in required_categories
        if category not in contract_tag_categories
    ]

    if missing_contract_categories:
        errors.append(
            f"{domain_name}: Contract missing required "
            f"metadata tag categories "
            f"{missing_contract_categories}"
        )

    return errors


def validate_domain(domain_name, files, standards):
    metadata = load_json(files["metadata"])
    contract = load_json(files["contract"])

    errors = []

    errors.extend(
        validate_metadata(
            metadata,
            standards,
            domain_name
        )
    )

    errors.extend(
        validate_contract(
            contract,
            standards,
            domain_name
        )
    )

    return errors


def main():
    standards_config = load_json(GOVERNANCE_CONFIG)

    print("=" * 70)
    print("FEDERATED DATA MESH GOVERNANCE VALIDATION")
    print("=" * 70)

    print(
        f"\nGovernance model: "
        f"{standards_config['governance_model']}"
    )

    all_errors = []
    domain_results = {}

    for domain_name, files in DOMAINS.items():
        print("\n" + "-" * 70)
        print(f"DOMAIN: {domain_name.upper()}")
        print("-" * 70)

        errors = validate_domain(
            domain_name,
            files,
            standards_config
        )

        domain_results[domain_name] = errors

        if errors:
            print("GOVERNANCE STATUS: FAILED")

            for error in errors:
                print(f"- {error}")

            all_errors.extend(errors)

        else:
            print("GOVERNANCE STATUS: PASSED")
            print(
                "Metadata and contract comply with "
                "federated governance standards."
            )

    # ---------------------------------------------------------
    # Final report
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("FINAL GOVERNANCE REPORT")
    print("=" * 70)

    total_domains = len(DOMAINS)
    passed_domains = sum(
        1
        for errors in domain_results.values()
        if not errors
    )

    print(f"Domains evaluated : {total_domains}")
    print(f"Domains passed   : {passed_domains}")
    print(f"Domains failed   : {total_domains - passed_domains}")
    print(f"Total errors     : {len(all_errors)}")

    if all_errors:
        print("\nOVERALL STATUS: FAILED")

    else:
        print("\nOVERALL STATUS: PASSED")
        print(
            "All domains comply with shared federated "
            "governance standards."
        )

    print("\nRAW DATA CENTRALIZATION CHECK")
    print("-" * 70)
    print("Raw domain datasets were not loaded by this validator.")
    print("Governance was performed against metadata and contracts.")
    print("Raw data remains independently owned by each domain.")

    return len(all_errors) == 0


if __name__ == "__main__":
    main()