"""Snapshot the SWE-bench Lite dataset state post-hoc.

Writes outputs/round2/h_lite/dataset_revision.json with the best-effort
identifiers available at snapshot time. Does not modify run_meta.json,
does not load instance content, does not call any LLM.

If the HuggingFace Hub API call fails, the script raises and exits
with a non-zero status; no partial JSON is written. The dataset
revision snapshot is therefore an all-or-nothing artefact.
"""

import datetime
import json
from pathlib import Path

import datasets
from huggingface_hub import HfApi

DATASET_NAME = "princeton-nlp/SWE-bench_Lite"
SPLIT = "test"
OUT_PATH = Path("outputs/round2/h_lite/dataset_revision.json")


def main() -> None:
    ds = datasets.load_dataset(DATASET_NAME, split=SPLIT)
    info = ds.info
    sha = HfApi().dataset_info(DATASET_NAME).sha

    download_checksums = info.download_checksums or {}
    record = {
        "dataset_name": DATASET_NAME,
        "split": SPLIT,
        "hf_commit_sha": sha,
        "ds_info_version": str(info.version) if info.version is not None else None,
        "ds_info_download_checksums_keys": sorted(download_checksums.keys()),
        "ds_info_dataset_size": info.dataset_size,
        "datasets_library_version": datasets.__version__,
        "snapshot_taken_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "note": (
            "Snapshot taken post-hoc; Round 1 may have loaded against an "
            "earlier or later revision. This is the best-effort identifier "
            "of the dataset state at snapshot time."
        ),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
