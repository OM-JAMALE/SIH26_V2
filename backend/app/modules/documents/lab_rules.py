import re
from typing import Optional, Tuple, Dict, Any

# Standard clinical reference ranges for common lab tests (used when document does not specify or to cross-verify)
STANDARD_REFERENCE_RANGES: Dict[str, Dict[str, Any]] = {
    "hemoglobin": {"low": 13.0, "high": 17.5, "unit": "g/dL", "range_str": "13.0 - 17.5 g/dL"},
    "fasting blood sugar": {"low": 70.0, "high": 99.0, "unit": "mg/dL", "range_str": "70.0 - 99.0 mg/dL"},
    "fasting glucose": {"low": 70.0, "high": 99.0, "unit": "mg/dL", "range_str": "70.0 - 99.0 mg/dL"},
    "glucose": {"low": 70.0, "high": 99.0, "unit": "mg/dL", "range_str": "70.0 - 99.0 mg/dL"},
    "random blood sugar": {"low": 70.0, "high": 140.0, "unit": "mg/dL", "range_str": "70.0 - 140.0 mg/dL"},
    "hba1c": {"low": 4.0, "high": 5.6, "unit": "%", "range_str": "4.0 - 5.6 %"},
    "serum creatinine": {"low": 0.6, "high": 1.2, "unit": "mg/dL", "range_str": "0.6 - 1.2 mg/dL"},
    "creatinine": {"low": 0.6, "high": 1.2, "unit": "mg/dL", "range_str": "0.6 - 1.2 mg/dL"},
    "blood urea nitrogen": {"low": 7.0, "high": 20.0, "unit": "mg/dL", "range_str": "7.0 - 20.0 mg/dL"},
    "bun": {"low": 7.0, "high": 20.0, "unit": "mg/dL", "range_str": "7.0 - 20.0 mg/dL"},
    "troponin i": {"low": 0.0, "high": 0.03, "unit": "ng/mL", "range_str": "0.00 - 0.03 ng/mL"},
    "troponin": {"low": 0.0, "high": 0.03, "unit": "ng/mL", "range_str": "0.00 - 0.03 ng/mL"},
    "total cholesterol": {"low": None, "high": 200.0, "unit": "mg/dL", "range_str": "< 200.0 mg/dL"},
    "cholesterol": {"low": None, "high": 200.0, "unit": "mg/dL", "range_str": "< 200.0 mg/dL"},
    "ldl": {"low": None, "high": 100.0, "unit": "mg/dL", "range_str": "< 100.0 mg/dL"},
    "ldl cholesterol": {"low": None, "high": 100.0, "unit": "mg/dL", "range_str": "< 100.0 mg/dL"},
    "hdl": {"low": 40.0, "high": None, "unit": "mg/dL", "range_str": "> 40.0 mg/dL"},
    "hdl cholesterol": {"low": 40.0, "high": None, "unit": "mg/dL", "range_str": "> 40.0 mg/dL"},
    "triglycerides": {"low": None, "high": 150.0, "unit": "mg/dL", "range_str": "< 150.0 mg/dL"},
    "platelets": {"low": 150.0, "high": 450.0, "unit": "x10^3/uL", "range_str": "150 - 450 x10^3/uL"},
    "platelet count": {"low": 150.0, "high": 450.0, "unit": "x10^3/uL", "range_str": "150 - 450 x10^3/uL"},
    "wbc": {"low": 4.0, "high": 11.0, "unit": "x10^3/uL", "range_str": "4.0 - 11.0 x10^3/uL"},
    "white blood cells": {"low": 4.0, "high": 11.0, "unit": "x10^3/uL", "range_str": "4.0 - 11.0 x10^3/uL"},
    "potassium": {"low": 3.5, "high": 5.0, "unit": "mEq/L", "range_str": "3.5 - 5.0 mEq/L"},
    "sodium": {"low": 135.0, "high": 145.0, "unit": "mEq/L", "range_str": "135.0 - 145.0 mEq/L"},
    "alt": {"low": 7.0, "high": 56.0, "unit": "U/L", "range_str": "7.0 - 56.0 U/L"},
    "sgpt": {"low": 7.0, "high": 56.0, "unit": "U/L", "range_str": "7.0 - 56.0 U/L"},
    "ast": {"low": 10.0, "high": 40.0, "unit": "U/L", "range_str": "10.0 - 40.0 U/L"},
    "sgot": {"low": 10.0, "high": 40.0, "unit": "U/L", "range_str": "10.0 - 40.0 U/L"},
    "tsh": {"low": 0.4, "high": 4.0, "unit": "mIU/L", "range_str": "0.4 - 4.0 mIU/L"},
}


def parse_reference_range(range_str: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Deterministically parses a clinical reference range string into (low, high) float bounds.
    Supports formats like:
      - '13.5 - 17.5' or '13.5 to 17.5'
      - '< 200' or '<= 200'
      - '> 40' or '>= 40'
      - '150,000 - 450,000' (with comma thousand separators)
    """
    if not range_str:
        return None, None

    # Remove commas between digits (e.g. 150,000 -> 150000)
    cleaned = re.sub(r"(?<=\d),(?=\d)", "", range_str.strip().lower())

    # Pattern 1: Bounded range: e.g. "70.0 - 99.0", "13.5 to 17.5"
    bounded_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)", cleaned)
    if bounded_match:
        try:
            low = float(bounded_match.group(1))
            high = float(bounded_match.group(2))
            return low, high
        except ValueError:
            pass

    # Pattern 2: Upper bound only: e.g. "< 200", "<= 200", "less than 200"
    upper_match = re.search(r"(?:<|<=|less\s+than)\s*(\d+(?:\.\d+)?)", cleaned)
    if upper_match:
        try:
            high = float(upper_match.group(1))
            return None, high
        except ValueError:
            pass

    # Pattern 3: Lower bound only: e.g. "> 40", ">= 40", "greater than 40"
    lower_match = re.search(r"(?:>|>=|greater\s+than)\s*(\d+(?:\.\d+)?)", cleaned)
    if lower_match:
        try:
            low = float(lower_match.group(1))
            return low, None
        except ValueError:
            pass

    return None, None


def parse_numeric_value(val_str: Optional[str]) -> Optional[float]:
    """Extracts first valid floating point number from a clinical value string, handling commas."""
    if not val_str:
        return None
    cleaned = re.sub(r"(?<=\d),(?=\d)", "", val_str.strip())
    match = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def evaluate_lab_result(
    test_name: str,
    raw_value: str,
    numeric_value: Optional[float] = None,
    unit: Optional[str] = None,
    reference_range: Optional[str] = None,
) -> Tuple[bool, Optional[str], str]:
    """
    Deterministic evaluation of lab results according to Module B requirements:
    is_abnormal = value < low or value > high.
    
    Returns:
      (is_abnormal: bool, abnormal_flag: "HIGH" | "LOW" | "NORMAL" | None, resolved_reference_range: str)
    """
    # 1. Determine numeric value if not provided
    num_val = numeric_value if numeric_value is not None else parse_numeric_value(raw_value)
    if num_val is None:
        return False, None, reference_range or "Not specified"

    # 2. Try parsing document's provided reference range
    low, high = parse_reference_range(reference_range)
    resolved_range = reference_range or ""

    # 3. If reference range not found in document, look up standard clinical reference database
    if low is None and high is None:
        key = test_name.strip().lower()
        matched_entry = None

        # Exact match first
        if key in STANDARD_REFERENCE_RANGES:
            matched_entry = STANDARD_REFERENCE_RANGES[key]
        else:
            # Sort keys by length descending to match specific multi-word keys before generic substrings
            # e.g., 'hdl cholesterol' or 'fasting blood sugar' before 'cholesterol' or 'glucose'
            sorted_std_keys = sorted(STANDARD_REFERENCE_RANGES.keys(), key=len, reverse=True)
            for std_key in sorted_std_keys:
                if std_key in key or (len(std_key) > 3 and re.search(rf"\b{re.escape(std_key)}\b", key)):
                    matched_entry = STANDARD_REFERENCE_RANGES[std_key]
                    break

        if matched_entry:
            low = matched_entry["low"]
            high = matched_entry["high"]
            resolved_range = matched_entry["range_str"]

    if not resolved_range:
        resolved_range = "Standard clinical range unavailable"

    # 4. Deterministic comparison
    if low is not None and num_val < low:
        return True, "LOW", resolved_range
    if high is not None and num_val > high:
        return True, "HIGH", resolved_range

    if low is not None or high is not None:
        return False, "NORMAL", resolved_range

    return False, None, resolved_range
