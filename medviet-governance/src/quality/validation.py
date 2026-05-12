import re
from pathlib import Path

import great_expectations as gx
import pandas as pd
from great_expectations.core.expectation_suite import ExpectationSuite

VALID_CONDITIONS = {"Tieu duong", "Huyet ap cao", "Tim mach", "Khoe manh"}
IMPORTANT_COLUMNS = ["patient_id", "cccd", "email", "benh", "ket_qua_xet_nghiem"]
EMAIL_REGEX = r"^[\w.!#$%&'*+/=?^`{|}~-]+@[\w-]+(?:\.[\w-]+)+$"


def build_patient_expectation_suite() -> ExpectationSuite:
    """
    Build a lightweight expectation suite definition for patient data.

    Great Expectations APIs differ across versions; returning an
    ExpectationSuite keeps this function usable for documentation and extension,
    while validate_anonymized_data performs the concrete checks used by tests.
    """
    try:
        return ExpectationSuite(name="patient_data_suite")
    except TypeError:
        return gx.ExpectationSuite(expectation_suite_name="patient_data_suite")


def _fail(results: dict, check_name: str) -> None:
    results["success"] = False
    results["failed_checks"].append(check_name)


def validate_anonymized_data(filepath: str) -> dict:
    """Validate anonymized patient data and return a compact report."""
    df = pd.read_csv(filepath, dtype={"cccd": str, "so_dien_thoai": str})
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns),
        },
    }

    if "cccd" not in df.columns or not df["cccd"].astype(str).str.fullmatch(r"\d{11,12}").all():
        _fail(results, "cccd_format")

    missing_columns = [column for column in IMPORTANT_COLUMNS if column not in df.columns]
    if missing_columns:
        results["stats"]["missing_columns"] = missing_columns
        _fail(results, "required_columns_present")
    else:
        null_columns = [column for column in IMPORTANT_COLUMNS if df[column].isna().any()]
        if null_columns:
            results["stats"]["null_columns"] = null_columns
            _fail(results, "important_columns_not_null")

    if "patient_id" in df.columns and df["patient_id"].duplicated().any():
        _fail(results, "patient_id_unique")

    if "email" in df.columns and not df["email"].astype(str).map(lambda value: re.fullmatch(EMAIL_REGEX, value) is not None).all():
        _fail(results, "email_format")

    if "ket_qua_xet_nghiem" in df.columns and not df["ket_qua_xet_nghiem"].between(0, 50).all():
        _fail(results, "lab_result_range")

    if "benh" in df.columns and not set(df["benh"].dropna()).issubset(VALID_CONDITIONS):
        _fail(results, "valid_conditions")

    original_path = Path("data/raw/patients_raw.csv")
    if original_path.exists():
        original_rows = len(pd.read_csv(original_path))
        results["stats"]["original_rows"] = original_rows
        if len(df) != original_rows:
            _fail(results, "row_count_matches_original")

    return results
