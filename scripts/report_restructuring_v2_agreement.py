from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validation.adjudication import agreement_report
from validation.restructuring_v2_data import read_csv


def main() -> None:
    report = agreement_report(
        read_csv(ROOT / "data/restructuring_v2/adjudications_reviewer_1.csv"),
        read_csv(ROOT / "data/restructuring_v2/adjudications_reviewer_2.csv"),
    )
    output = ROOT / "data/derived/restructuring_adjudication_agreement_v2.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
