import json

import logging
import os

from collections import defaultdict

from typing import Dict, Any

from datetime import datetime


def _user_log_file_path() -> str:
    """Return a user-writable log file path in the new app folder only."""
    base = os.getenv("LOCALAPPDATA")
    if not base:
        # Fallback for non-Windows or if env var is missing
        base = os.path.join(os.path.expanduser("~"), "AppData", "Local")
    app_dir = os.path.join(base, "MC Crafting Calculator")
    try:
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, "minecraft_calculator.log")
    except Exception:
        # As a last resort, drop the log next to the user's home
        return os.path.join(os.path.expanduser("~"), "minecraft_calculator.log")


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(_user_log_file_path(), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def load_recipes(path: str) -> Dict[str, Any]:

    with open(path, "r", encoding="utf-8") as f:

        return json.load(f)


def calculate_requirements(
    recipes: Dict[str, Dict[str, int]], item: str, qty: int, expand_all: bool = False
) -> Dict[str, int]:

    logging.debug(f"Calculating requirements for {qty}x {item}")

    totals = defaultdict(int)

    recipe_stack = []

    def is_base_material(recipe_item: str, depth: int) -> bool:

        if any((recipe_item.endswith("_planks") for x in recipe_item.split("_"))):

            return True

        if recipe_item.endswith("_ingot"):

            return True

        if recipe_item.endswith("_block") and (not recipe_item.startswith("stripped_")):

            return True

        return False

    def helper(cur_item: str, cur_qty: int, depth=0):

        indent = "  " * depth

        logging.debug(f"{indent}Processing: {cur_qty}x {cur_item}")

        logging.debug(f"{indent}Current recipe stack: {' -> '.join(recipe_stack)}")

        if cur_item in recipe_stack:

            cycle = " -> ".join(recipe_stack + [cur_item])

            logging.error(f"{indent}Recipe cycle detected: {cycle}")

            raise ValueError(f"Recipe cycle detected: {cycle}")

        if (
            cur_item not in recipes
            or not recipes[cur_item]
            or (not expand_all and depth > 0 and is_base_material(cur_item, depth))
        ):

            logging.debug(f"{indent}Adding material: {cur_qty}x {cur_item}")

            totals[cur_item] += cur_qty

            return

        recipe_stack.append(cur_item)

        try:

            logging.debug(f"{indent}Found recipe for {cur_item}: {recipes[cur_item]}")

            for sub, sub_q in recipes[cur_item].items():

                total_sub_qty = cur_qty * int(sub_q)

                logging.debug(
                    f"{indent}Need {total_sub_qty}x {sub} for {cur_qty}x {cur_item}"
                )

                helper(sub, total_sub_qty, depth + 1)

        finally:

            recipe_stack.pop()

    helper(item, int(qty), depth=0)

    logging.debug(f"Final totals for {qty}x {item}: {dict(totals)}")

    return dict(totals)


def aggregate_requirements(
    recipes: Dict[str, Dict[str, int]], items: Dict[str, int]
) -> Dict[str, int]:

    logging.info(f"Calculating aggregate requirements for items: {items}")

    totals = defaultdict(int)

    for itm, q in items.items():

        logging.debug(f"Processing requirements for {q}x {itm}")

        sub = calculate_requirements(recipes, itm, q, expand_all=False)

        logging.debug(f"Requirements for {q}x {itm}: {sub}")

        for mat, mq in sub.items():

            totals[mat] += mq

            logging.debug(f"Updated total for {mat}: {totals[mat]}")

    logging.info(f"Final aggregate totals: {dict(totals)}")

    return dict(totals)


if __name__ == "__main__":

    sample = {"redstone_torch": {"stick": 1, "redstone": 1}}

    print(calculate_requirements(sample, "redstone_torch", 10))
