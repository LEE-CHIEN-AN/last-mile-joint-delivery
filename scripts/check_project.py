"""Check repository layout without network requests or recalculating model results."""
import argparse
import ast
import csv
import json
import math
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-raw", action="store_true", help="Also require local course data")
    args = parser.parse_args()
    errors = []
    for name in ("notebooks", "scripts", "src", "data/external", "data/processed",
                 "data/cache/routing", "outputs/figures", "outputs/profiling", "docs/planning"):
        if not (ROOT / name).is_dir():
            errors.append(f"Missing directory: {name}")

    raw = ["delivery_plan/monthly", "delivery_plan_other_depots", "gps_traces",
           "store_master", "tms_delivery_records", "vehicle_can_telematics", "vehicle_class_by_V.csv"]
    missing_raw = [name for name in raw if not (ROOT / "data/raw" / name).exists()]
    if args.require_raw:
        errors.extend(f"Missing raw input: data/raw/{name}" for name in missing_raw)

    documents = [(ROOT / "README.md", (ROOT / "README.md").read_text(encoding="utf-8"))]
    for folder in ("docs", "data", "notebooks", "scripts", "src", "outputs"):
        documents.extend((path, path.read_text(encoding="utf-8"))
                         for path in (ROOT / folder).rglob("*.md"))
    notebooks = sorted((ROOT / "notebooks").rglob("*.ipynb"))
    for path in notebooks:
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
            if notebook.get("nbformat") != 4:
                errors.append(f"Unexpected notebook format: {path.relative_to(ROOT)}")
            for index, cell in enumerate(notebook["cells"]):
                source = "".join(cell.get("source", []))
                if cell["cell_type"] == "code":
                    ast.parse(source, filename=f"{path.name}:cell {index}")
                elif cell["cell_type"] == "markdown":
                    documents.append((path, source))
        except (ValueError, KeyError, SyntaxError) as exc:
            errors.append(f"Invalid notebook {path.relative_to(ROOT)}: {exc}")

    modules = sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "src").glob("*.py"))
    for path in modules:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(str(exc))

    for path, source in documents:
        source = re.sub(r"```.*?```", "", source, flags=re.DOTALL)
        for match in re.finditer(r"!?\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", source):
            target = match.group(1).strip("<>")
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target = unquote(target.split("#", 1)[0])
            if not (path.parent / target).exists():
                errors.append(f"Broken link in {path.relative_to(ROOT)}: {target}")

    try:
        with (ROOT / "data/processed/ne_stores_verified.csv").open(encoding="utf-8-sig", newline="") as handle:
            stores = list(csv.DictReader(handle))
        included = sum(row["include"] == "1" for row in stores)
        excluded = sum(row["include"] == "0" for row in stores)
        if (included, excluded) != (33, 4):
            errors.append(f"Store scope changed: {included} included, {excluded} excluded; review docs and results")
        with (ROOT / "data/cache/routing/rebuild_calibrated.json").open(encoding="utf-8") as handle:
            calibrated = json.load(handle)["25"]
        brands = ["7-Eleven", "全家", "OK", "萊爾富"]
        zones = ["05", "12", "remote"]
        independent = sum(calibrated[brand][zone]["km"] for brand in brands for zone in zones)
        joint = sum(calibrated["B"][zone]["km"] for zone in zones)
        # Regression guard for the existing scenario; update deliberately when the model changes.
        if not math.isclose(independent, 206.7682, abs_tol=0.001) or not math.isclose(joint, 132.1158, abs_tol=0.001):
            errors.append(f"Q25 cache changed: independent={independent:.4f}, joint={joint:.4f}; review README")
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f"Unable to check store list / calibrated cache: {exc}")

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        raise SystemExit(1)
    print(f"OK: layout, local links, {len(notebooks)} notebooks, {len(modules)} Python files, store list and Q25 cache")
    print("Raw inputs: " + ("present" if not missing_raw else "not included locally (use --require-raw to enforce)"))
    print("No model recalculation or network requests performed.")


if __name__ == "__main__":
    main()
