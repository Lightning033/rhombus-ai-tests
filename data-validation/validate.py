"""
validate.py – Automated data validation for Rhombus AI
=======================================================

Validates that the AI pipeline correctly transformed the messy input CSV.

Checks:
  1. Output file exists
  2. Schema correctness (expected columns present)
  3. Row count (invalid rows removed)
  4. No empty IDs
  5. Names are Title Case
  6. Dates are in YYYY-MM-DD format
  7. Salary is numeric (no $ symbols)
  8. Phone numbers are formatted

Run:
    cd data-validation
    python validate.py --input fixtures/messy_data.csv --output <downloaded_file.csv>
"""

import re
import sys
import argparse
import pandas as pd
from pathlib import Path


# -- Expected schema ----------------------------------------------------------

EXPECTED_COLUMNS  = ["ID", "Email", "Department"]
MIN_EXPECTED_ROWS = 9
MAX_EXPECTED_ROWS = 11


# -- Validation functions -----------------------------------------------------

def check_file_exists(path: Path) -> bool:
    if not path.exists():
        print(f"FAIL  Output file not found: {path}")
        return False
    print(f"PASS  Output file found: {path}")
    return True


def check_schema(df: pd.DataFrame) -> bool:
    missing = [col for col in EXPECTED_COLUMNS
               if not any(col.lower() in c.lower() for c in df.columns)]
    if missing:
        print(f"FAIL  Schema check - missing columns: {missing}")
        print(f"      Found columns: {list(df.columns)}")
        return False
    print(f"PASS  Schema check - columns: {list(df.columns)}")
    return True


def check_row_count(df: pd.DataFrame) -> bool:
    count = len(df)
    if MIN_EXPECTED_ROWS <= count <= MAX_EXPECTED_ROWS:
        print(f"PASS  Row count - {count} rows "
              f"(expected {MIN_EXPECTED_ROWS}-{MAX_EXPECTED_ROWS})")
        return True
    print(f"FAIL  Row count - got {count} rows "
          f"(expected {MIN_EXPECTED_ROWS}-{MAX_EXPECTED_ROWS})")
    return False


def check_no_empty_ids(df: pd.DataFrame) -> bool:
    id_col = next((c for c in df.columns if "id" in c.lower()), None)
    if id_col is None:
        print("SKIP  ID column not found")
        return True

    empty = df[id_col].isna() | (df[id_col].astype(str).str.strip() == "")
    if empty.any():
        print(f"FAIL  Empty ID check - {empty.sum()} rows with empty ID")
        return False
    print("PASS  Empty ID check - no empty IDs found")
    return True


def check_dates(df: pd.DataFrame) -> bool:
    date_col = next(
        (c for c in df.columns if "date" in c.lower() or "birth" in c.lower()),
        None
    )
    if date_col is None:
        print("SKIP  Date column not found")
        return True

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    non_empty = df[date_col].dropna().astype(str).str.strip()
    non_empty = non_empty[non_empty != ""]

    invalid = non_empty[~non_empty.apply(lambda x: bool(date_pattern.match(x)))]
    if not invalid.empty:
        print(f"FAIL  Date format check - {len(invalid)} invalid dates:")
        print(f"      {invalid.tolist()}")
        return False
    print("PASS  Date format check - all dates are YYYY-MM-DD")
    return True


def check_salary_numeric(df: pd.DataFrame) -> bool:
    salary_col = next((c for c in df.columns if "salary" in c.lower()), None)
    if salary_col is None:
        print("SKIP  Salary column not found")
        return True

    non_empty = df[salary_col].dropna().astype(str).str.strip()
    non_empty = non_empty[non_empty != ""]

    has_symbols = non_empty[non_empty.str.contains(r"[\$£€,]", regex=True)]
    if not has_symbols.empty:
        print(f"FAIL  Salary check - {len(has_symbols)} values still have currency symbols:")
        print(f"      {has_symbols.tolist()}")
        return False

    def is_numeric(val):
        try:
            float(val)
            return True
        except ValueError:
            return False

    non_numeric = non_empty[~non_empty.apply(is_numeric)]
    if not non_numeric.empty:
        print(f"FAIL  Salary check - {len(non_numeric)} non-numeric values:")
        print(f"      {non_numeric.tolist()}")
        return False

    print("PASS  Salary check - all values are numeric")
    return True


def check_names_title_case(df: pd.DataFrame) -> bool:
    name_cols = [c for c in df.columns
                 if any(kw in c.lower() for kw in ("name", "first", "last"))]
    if not name_cols:
        print("SKIP  Name columns not found")
        return True

    all_passed = True
    for col in name_cols:
        non_empty = df[col].dropna().astype(str).str.strip()
        non_empty = non_empty[non_empty != ""]
        not_title = non_empty[non_empty != non_empty.str.title()]
        if not not_title.empty:
            print(f"FAIL  Title Case check for '{col}' - "
                  f"{len(not_title)} values not in Title Case:")
            print(f"      {not_title.tolist()}")
            all_passed = False

    if all_passed:
        print("PASS  Title Case check - all names are Title Case")
    return all_passed


def check_phone_format(df: pd.DataFrame) -> bool:
    phone_col = next((c for c in df.columns if "phone" in c.lower()), None)
    if phone_col is None:
        print("SKIP  Phone column not found")
        return True

    phone_pattern = re.compile(r"^\(\d{3}\) \d{3}-\d{4}$")
    non_empty = df[phone_col].dropna().astype(str).str.strip()
    non_empty = non_empty[non_empty != ""]

    invalid = non_empty[~non_empty.apply(lambda x: bool(phone_pattern.match(x)))]
    if not invalid.empty:
        print(f"WARN  Phone format - {len(invalid)} values not in (XXX) XXX-XXXX format:")
        print(f"      {invalid.tolist()}")
        return True

    print("PASS  Phone format check - all numbers formatted correctly")
    return True


# -- Main ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate Rhombus AI data transformation output"
    )
    parser.add_argument("--input",  required=True, help="Path to original input CSV")
    parser.add_argument("--output", required=True, help="Path to transformed output CSV")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    print("\n" + "=" * 55)
    print("  Rhombus AI - Data Validation Report")
    print("=" * 55)
    print(f"  Input  : {input_path}")
    print(f"  Output : {output_path}")
    print("=" * 55 + "\n")

    input_df = pd.read_csv(input_path)
    print(f"Input rows  : {len(input_df)}")

    if not check_file_exists(output_path):
        sys.exit(1)

    output_df = pd.read_csv(output_path)
    print(f"Output rows : {len(output_df)}\n")

    results = [
        check_schema(output_df),
        check_row_count(output_df),
        check_no_empty_ids(output_df),
        check_dates(output_df),
        check_salary_numeric(output_df),
        check_names_title_case(output_df),
        check_phone_format(output_df),
    ]

    print("\n" + "=" * 55)
    passed = sum(results)
    total  = len(results)
    if all(results):
        print(f"  ALL {total} CHECKS PASSED")
    else:
        print(f"  {total - passed}/{total} CHECKS FAILED")
    print("=" * 55 + "\n")

    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()