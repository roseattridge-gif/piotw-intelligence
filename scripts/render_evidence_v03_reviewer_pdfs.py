from __future__ import annotations

import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def main() -> None:
    destination = ROOT / "output/pdf/evidence_engine_v0_3"
    destination.mkdir(parents=True, exist_ok=True)
    with (ROOT / "data/evidence_engine_v0_3/corpus_manifest.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        source = (ROOT / row["source_artifact"]).resolve()
        output = (ROOT / row["reviewer_pdf"]).resolve()
        if output.exists() and output.stat().st_size > 10_000:
            continue
        subprocess.run([
            str(CHROME), "--headless", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={output}", source.as_uri(),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)


if __name__ == "__main__": main()
