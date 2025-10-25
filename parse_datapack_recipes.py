"""Parse Minecraft datapack-style recipe JSON files under recepies/ and produce a simplified
mapping file `recepies.json` where each key is a normalized result name and the value is
an ingredient->count dict (counts are per craft action as present in the recipe pattern).

This handles common recipe formats: crafting_shaped (pattern + key), crafting_shapeless
(ingredients), and cooking/smelting (single ingredient), and result with item/count.
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).parent

IN_DIR = BASE / "recepies"

OUT_FILE = BASE / "recepies.json"

BACKUP = BASE / "recepies.json.bak_dp"

def normalize_item(raw: str) -> str:

    if not raw:

        return raw

    if ':' in raw:

        raw = raw.split(':', 1)[1]

    raw = raw.strip().lower()

    raw = re.sub(r"[^a-z0-9 ]+", " ", raw)

    raw = re.sub(r"\s+", "_", raw)

    return raw

def extract_result(data: dict):

    if 'result' in data:

        res = data['result']

        if isinstance(res, str):

            return normalize_item(res), 1

        if isinstance(res, dict):

            item = res.get('item') or res.get('id') or res.get('name')

            count = res.get('count', 1)

            return normalize_item(item), int(count)

    if 'minecraft:result' in data:

        r = data['minecraft:result']

        if isinstance(r, dict):

            return normalize_item(r.get('item')), int(r.get('count', 1))

    return None, None

def parse_ingredient_obj(obj):

    if isinstance(obj, str):

        s = obj.lstrip('#')

        return normalize_item(s)

    if isinstance(obj, dict):

        it = obj.get('item') or obj.get('tag') or obj.get('name')

        if isinstance(it, dict):

            return None

        return normalize_item(it)

    return None

def parse_file(path: Path):

    j = json.loads(path.read_text(encoding='utf-8'))

    result_name, result_count = extract_result(j)

    if not result_name:

        return None, None

    ingredients_count = {}

    if j.get('type', '').endswith('crafting_shaped') or 'pattern' in j and 'key' in j:

        pattern = j.get('pattern', [])

        key = j.get('key', {})

        symbol_counts = {}

        for row in pattern:

            for ch in row:

                if ch == ' ':

                    continue

                symbol_counts[ch] = symbol_counts.get(ch, 0) + 1

        for sym, obj in key.items():

            item = parse_ingredient_obj(obj)

            if not item:

                continue

            cnt = symbol_counts.get(sym, 0)

            if cnt:

                ingredients_count[item] = ingredients_count.get(item, 0) + cnt

        return result_name, ingredients_count

    if j.get('type', '').endswith('crafting_shapeless') or 'ingredients' in j:

        ingreds = j.get('ingredients', [])

        for ing in ingreds:

            item = parse_ingredient_obj(ing)

            if not item:

                continue

            ingredients_count[item] = ingredients_count.get(item, 0) + 1

        return result_name, ingredients_count

    if 'ingredient' in j:

        item = parse_ingredient_obj(j['ingredient'])

        if item:

            ingredients_count[item] = ingredients_count.get(item, 0) + 1

            return result_name, ingredients_count

    if 'recipe' in j and isinstance(j['recipe'], dict):

        r = j['recipe']

        if 'pattern' in r and 'key' in r:

            pattern = r.get('pattern', [])

            key = r.get('key', {})

            symbol_counts = {}

            for row in pattern:

                for ch in row:

                    if ch == ' ':

                        continue

                    symbol_counts[ch] = symbol_counts.get(ch, 0) + 1

            for sym, obj in key.items():

                item = parse_ingredient_obj(obj)

                if not item:

                    continue

                cnt = symbol_counts.get(sym, 0)

                if cnt:

                    ingredients_count[item] = ingredients_count.get(item, 0) + cnt

            return result_name, ingredients_count

    return result_name, ingredients_count

def main():

    if not IN_DIR.exists():

        print(f"Folder not found: {IN_DIR}")

        return

    if OUT_FILE.exists():

        BACKUP.write_bytes(OUT_FILE.read_bytes())

    merged = {}

    files = sorted([p for p in IN_DIR.rglob('*.json')])

    print(f"Parsing {len(files)} recipe files...")

    for p in files:

        try:

            res, ic = parse_file(p)

            if not res:

                continue

            if res in merged:

                continue

            merged[res] = ic

        except Exception as e:

            print(f"Failed to parse {p.name}: {e}")

    OUT_FILE.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f"Wrote {len(merged)} simplified recipes to {OUT_FILE.name} (backup {BACKUP.name if BACKUP.exists() else 'none'})")

if __name__ == '__main__':

    main()
