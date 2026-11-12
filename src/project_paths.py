"""Shared paths for notebooks; resolve from this file rather than the working directory."""
from pathlib import Path
import pickle

ROOT = str(Path(__file__).resolve().parents[1])


def project_path(*parts):
    return str(Path(ROOT).joinpath(*parts))


def load_profile_results():
    """Read our trusted local cache, adapting historical input paths in memory."""
    with open(project_path("outputs", "profiling", "results.pkl"), "rb") as handle:
        results = pickle.load(handle)
    raw_names = {
        "delivery_plan", "delivery_plan_other_depots", "gps_traces", "store_master",
        "tms_delivery_records", "vehicle_can_telematics",
    }
    for dataset in results.values():
        if not isinstance(dataset, dict):
            continue
        perfile = dataset.get("perfile")
        if perfile is None or "file" not in perfile:
            continue

        def adapt(value):
            if not isinstance(value, str):
                return value
            normalized = value.replace("\\", "/")
            if normalized.split("/", 1)[0] in raw_names:
                return "data/raw/" + normalized
            return value

        perfile["file"] = perfile["file"].map(adapt)
    return results
