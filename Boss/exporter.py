from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DEFAULT_SHEET_NAME, EXCEL_COLUMNS, OUTPUT_DIR
from .models import JobRecord


def export_to_excel(records: list[JobRecord], output_path: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [record.to_row() for record in records]
    dataframe = pd.DataFrame(rows, columns=EXCEL_COLUMNS)
    dataframe.to_excel(output_path, index=False, sheet_name=DEFAULT_SHEET_NAME)

