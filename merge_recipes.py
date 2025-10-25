"""Merge individual recipe JSON files from the `recepies/` folder into recepies.json.

This script:
- backs up the existing `recepies.json` to `recepies.json.bak` (if present)
- reads every .json file under `recepies/`
- expects each file to contain a JSON object mapping one or more item names to recipe lists
- merges entries: if an item already exists, appends recipe variants
- writes the merged object to `recepies.json`

Run from project root (d:\code\mc):
  python merge_recipes.py
"""

import json
from pathlib import Path


BASE = Path(__file__).parent
IN_DIR = BASE / "recepies"
OUT_FILE = BASE / "recepies.json"
BACKUP = BASE / "recepies.json.bak"


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Failed to read {path}: {e}")
        return {}


def main():
    if not IN_DIR.exists() or not IN_DIR.is_dir():
        print(f"Input folder not found: {IN_DIR}")
        return

    if OUT_FILE.exists():
        BACKUP.write_bytes(OUT_FILE.read_bytes())
        print(f"Backed up existing {OUT_FILE.name} -> {BACKUP.name}")

    merged = {}
    files = sorted([p for p in IN_DIR.iterdir() if p.suffix.lower() == ".json"])
    print(f"Merging {len(files)} files from {IN_DIR}")
    for p in files:
        data = load_json(p)
        if not isinstance(data, dict):
            print(f"Skipping {p} (not an object)")
            continue
        for k, v in data.items():
            if k in merged and isinstance(merged[k], list) and isinstance(v, list):
                merged[k].extend(v)
            elif (
                k in merged and isinstance(merged[k], list) and not isinstance(v, list)
            ):
                # unlikely, but wrap
                merged[k].append(v)
            else:
                merged.setdefault(k, [])
                if isinstance(v, list):
                    merged[k].extend(v)
                else:
                    merged[k].append(v)

    # Sort keys for stable output
    out = {k: merged[k] for k in sorted(merged.keys(), key=lambda s: s.lower())}
    OUT_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote merged recipes to {OUT_FILE} ({len(out)} items)")


if __name__ == "__main__":
    main()
