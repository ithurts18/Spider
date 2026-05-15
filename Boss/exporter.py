from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DEFAULT_SHEET_NAME, EXCEL_COLUMNS, OUTPUT_DIR
from .models import JobRecord


def export_to_excel(records: list[JobRecord], output_path: Path) -> None:
    dataframe = build_dataframe(records)
    ensure_output_dir(output_path)
    dataframe.to_excel(output_path, index=False, sheet_name=DEFAULT_SHEET_NAME)


def export_to_csv(records: list[JobRecord], output_path: Path) -> None:
    dataframe = build_dataframe(records)
    ensure_output_dir(output_path)
    dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")


def export_outputs(records: list[JobRecord], excel_output_path: Path) -> dict[str, Path]:
    csv_output_path = excel_output_path.with_suffix(".csv")
    export_to_excel(records, excel_output_path)
    export_to_csv(records, csv_output_path)
    return {"excel": excel_output_path, "csv": csv_output_path}


def build_dataframe(records: list[JobRecord]) -> pd.DataFrame:
    rows = [record.to_row() for record in records]
    return pd.DataFrame(rows, columns=EXCEL_COLUMNS)


def ensure_output_dir(output_path: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
