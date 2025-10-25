import json
import re
from pathlib import Path

# Resolve project root (parent of tools directory)
BASE = Path(__file__).resolve().parents[1]
IN_FILE = BASE / "recepies.json"
BACKUP2 = BASE / "recepies.json.bak2"


def normalize(name: str) -> str:
    if not isinstance(name, str):
        return name
    s = name.strip()
    s = re.sub(r"\s*\([^)]*\)", "", s)
    s = s.replace("'", "")
    s = s.replace("\u2019", "")
    s = s.strip().lower()
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
                if (
                    isinstance(v, dict)
                    and "recipe" in v
                    and isinstance(v["recipe"], list)
                ):
                    variant = v
                    break
            if not variant:
                continue
            recipe = variant["recipe"]
            counts = {}
            for slot in recipe:
                if not slot:
                    continue
                name = normalize(slot)
                counts[name] = counts.get(name, 0) + 1
            out[k] = counts
            continue
    IN_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Wrote simplified recepies.json with {len(out)} items (backup at {BACKUP2.name})"
    )


if __name__ == "__main__":
    main()
