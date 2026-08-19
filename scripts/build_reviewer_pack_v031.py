from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "reviewer_pack_v0_3_1"
PDFS = PACK / "01_reviewer_pdfs"
BLANK = PACK / "02_blank_annotation_files"
INSTRUCTIONS = PACK / "03_reviewer_instructions"
MANIFEST = PACK / "04_corpus_manifest"
CHANGE = PACK / "05_change_log"
ALB = "ee03-alb-0000915913-24-000156"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    for directory in (PDFS, BLANK, INSTRUCTIONS, MANIFEST, CHANGE):
        directory.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((ROOT / "reviewer_pack_v0_3/04_corpus_manifest/corpus_manifest_blinded.csv").open()))
    files = []
    for row in rows:
        document_id = row["document_id"]
        source = (ROOT / "output/pdf/evidence_engine_v0_3_1" / f"{document_id}-complete.pdf") if document_id == ALB else (ROOT / "output/pdf/evidence_engine_v0_3" / f"{document_id}.pdf")
        target = PDFS / f"{document_id}.pdf"
        shutil.copy2(source, target)
        files.append({"relative_path": str(target.relative_to(PACK)), "sha256": sha(target), "bytes": target.stat().st_size})
    for name in ("Reviewer Instructions.md", "Field Definitions.md"):
        shutil.copy2(ROOT / "reviewer_pack_v0_3/03_reviewer_instructions" / name, INSTRUCTIONS / name)
    manifest_out = MANIFEST / "corpus_manifest_blinded_v2.csv"
    with manifest_out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) + ["pack_version", "source_repair_status"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "pack_version": "v2", "source_repair_status": "exhibit_99_1_appended" if row["document_id"] == ALB else "unchanged"})
    for path in sorted(PACK.rglob("*")):
        if path.is_file() and path not in {MANIFEST / "pack_hash_manifest.json"} and not any(item["relative_path"] == str(path.relative_to(PACK)) for item in files):
            files.append({"relative_path": str(path.relative_to(PACK)), "sha256": sha(path), "bytes": path.stat().st_size})
    pack_manifest = {"pack_name": "Evidence Engine 0.3 - Blinded Reviewer Pack v2", "version": "v2",
        "blinded": True, "machine_answers_present": False, "pdf_count": len(rows),
        "original_pack_preserved": True, "files": sorted(files, key=lambda x: x["relative_path"])}
    (MANIFEST / "pack_hash_manifest.json").write_text(json.dumps(pack_manifest, indent=2) + "\n")
    print(json.dumps({"pdfs": len(rows), "files": len(files), "albemarle_sha256": sha(PDFS / f"{ALB}.pdf")}, indent=2))


if __name__ == "__main__":
    main()
