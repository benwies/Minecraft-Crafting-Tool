"""Flatten merged recepies.json into a simple mapping item -> {ingredient: count}.

Rules used:
- If an item value is already a simple mapping (dict of ingredient->int), keep it.
- If an item value is a list of variants, pick the first variant that contains a 'recipe' list.
- Count occurrences of ingredient names in the 3x3 recipe array. Ignore null/empty entries.
- Normalize names to lowercase with underscores and strip parentheses.
- Write the simplified mapping back to `recepies.json` (backing up first to recepies.json.bak2).

This produces mappings where counts are the number of ingredient slots used in the recipe (per craft action).
For example: "redstone_torch": { "stick": 1, "redstone_dust": 1 }
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).parent

IN_FILE = BASE / "recepies.json"

BACKUP2 = BASE / "recepies.json.bak2"

def normalize(name: str) -> str:

    if not isinstance(name, str):

        return name

    s = name.strip()

    s = re.sub(r"\s*\([^)]*\)", "", s)

    s = s.replace("'", "")

    s = s.replace("\u2019", "")

    s = s.strip()

    s = s.lower()

    s = re.sub(r"[^a-z0-9 ]+", " ", s)

    s = re.sub(r"\s+", "_", s)

    return s

def load_json(path: Path):

    return json.loads(path.read_text(encoding="utf-8"))

def main():

    if not IN_FILE.exists():

        print(f"{IN_FILE} not found")

        return

    BACKUP2.write_bytes(IN_FILE.read_bytes())

    data = load_json(IN_FILE)

    out = {}

    for key, val in data.items():

        k = normalize(key)

        if isinstance(val, dict):

            simple = {normalize(ik): int(iv) for ik, iv in val.items()}

            out[k] = simple

            continue

        if isinstance(val, list):

            variant = None

            for v in val:

                if isinstance(v, dict) and 'recipe' in v and isinstance(v['recipe'], list):

                    variant = v

                    break

            if not variant:

                continue

            recipe = variant['recipe']

            counts = {}

            for slot in recipe:

                if not slot:

                    continue

                name = normalize(slot)

                counts[name] = counts.get(name, 0) + 1

            out[k] = counts

            continue

    IN_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote simplified recepies.json with {len(out)} items (backup at {BACKUP2.name})")

if __name__ == "__main__":

    main()
