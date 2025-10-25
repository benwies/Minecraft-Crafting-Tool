import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from code import load_recipes, calculate_requirements, aggregate_requirements


BASE = Path(__file__).parent
RECIPES_PATHS = [BASE / "recepies.json", BASE / "recipes.json"]
RECIPES = {}
for p in RECIPES_PATHS:
    if p.exists():
        try:
            RECIPES = load_recipes(str(p))
            break
        except Exception:
            RECIPES = {}


PROJECTS_DIR = BASE / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)


def format_stacks(qty: int) -> str:
    stacks = qty // 64
    rem = qty % 64
    if stacks > 0:
        return f"{qty} ({stacks} stack(s) + {rem})"
    return f"{qty}"


class Project:
    def __init__(self, name: str, items=None):
        self.name = name
        self.items = items or {}  # item -> qty

    @classmethod
    def load(cls, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data.get("name", path.stem), data.get("items", {}))

    def save(self, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": self.name, "items": self.items}, f, indent=2)


def list_project_files():
    return sorted([p for p in PROJECTS_DIR.glob("*.json")])


root = tk.Tk()
root.title("Minecraft Farm Resource Calculator - Projects")

main = ttk.Frame(root, padding=12)
main.pack(fill="both", expand=True)

# Top: project controls
proj_frame = ttk.Frame(main)
proj_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
ttk.Label(proj_frame, text="Project name:").grid(row=0, column=0)
entry_proj = ttk.Entry(proj_frame)
entry_proj.grid(row=0, column=1, sticky="ew")
btn_new = ttk.Button(proj_frame, text="New Project")
btn_new.grid(row=0, column=2, padx=4)
btn_save = ttk.Button(proj_frame, text="Save Project")
btn_save.grid(row=0, column=3, padx=4)
ttk.Label(proj_frame, text="Open:").grid(row=0, column=4)
combo_projects = ttk.Combobox(proj_frame, values=[p.name for p in list_project_files()])
combo_projects.grid(row=0, column=5, sticky="ew")
btn_load = ttk.Button(proj_frame, text="Load")
btn_load.grid(row=0, column=6, padx=4)

proj_frame.columnconfigure(1, weight=1)
proj_frame.columnconfigure(5, weight=1)


# Left: add items
left = ttk.LabelFrame(main, text="Project Items", padding=8)
left.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
ttk.Label(left, text="Item:").grid(row=0, column=0, sticky="w")
entry_item = ttk.Combobox(left, values=sorted(list(RECIPES.keys())))
entry_item.grid(row=0, column=1, sticky="ew")
ttk.Label(left, text="Qty:").grid(row=1, column=0, sticky="w")
entry_qty = ttk.Entry(left)
entry_qty.grid(row=1, column=1, sticky="ew")
entry_qty.insert(0, "1")
btn_add = ttk.Button(left, text="Add / Increment")
btn_add.grid(row=2, column=0, columnspan=2, pady=6)

items_tree = ttk.Treeview(left, columns=("item", "qty", "stacks"), show="headings", height=12)
items_tree.heading("item", text="Item")
items_tree.heading("qty", text="Qty")
items_tree.heading("stacks", text="Stacks")
items_tree.column("item", width=200, anchor="w")
items_tree.column("qty", width=80, anchor="center")
items_tree.column("stacks", width=120, anchor="w")
items_tree.grid(row=3, column=0, columnspan=2, sticky="nsew")
left.columnconfigure(1, weight=1)


# Right: raw materials
right = ttk.LabelFrame(main, text="Raw Materials", padding=8)
right.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
materials_tree = ttk.Treeview(right, columns=("item", "qty", "stacks"), show="headings", height=20)
materials_tree.heading("item", text="Item")
materials_tree.heading("qty", text="Qty")
materials_tree.heading("stacks", text="Stacks")
materials_tree.column("item", width=220, anchor="w")
materials_tree.column("qty", width=80, anchor="center")
materials_tree.column("stacks", width=140, anchor="w")
materials_tree.grid(row=0, column=0, sticky="nsew")
right.columnconfigure(0, weight=1)


# Internal state
current_project = Project("untitled")


def refresh_projects_combo():
    combo_projects["values"] = [p.name for p in list_project_files()]


def refresh_items_view():
    for r in items_tree.get_children():
        items_tree.delete(r)
    for itm, q in sorted(current_project.items.items()):
        items_tree.insert("", "end", iid=itm, values=(itm, q, format_stacks(q)))


def refresh_materials_view():
    try:
        mats = aggregate_requirements(RECIPES, current_project.items)
        for r in materials_tree.get_children():
            materials_tree.delete(r)
        for mat, q in sorted(mats.items()):
            materials_tree.insert("", "end", iid=mat, values=(mat, q, format_stacks(q)))
    except Exception as e:
        messagebox.showerror("Calculation error", f"Failed to calculate materials: {e}")


def update_views():
    refresh_items_view()
    refresh_materials_view()


def on_new_project():
    name = entry_proj.get().strip() or "untitled"
    logging.info(f"Creating new project: {name}")
    global current_project
    current_project = Project(name, {})
    entry_proj.delete(0, "end")
    entry_proj.insert(0, name)
    update_views()


def on_save_project():
    name = entry_proj.get().strip() or current_project.name or "untitled"
    path = PROJECTS_DIR / f"{name}.json"
    logging.info(f"Saving project '{name}' to {path}")
    logging.debug(f"Project contents: {current_project.items}")
    current_project.name = name
    current_project.save(path)
    refresh_projects_combo()
    messagebox.showinfo("Saved", f"Project saved to {path}")


def on_load_project():
    val = combo_projects.get().strip()
    logging.info(f"Attempting to load project: {val}")
    if not val:
        logging.warning("No project selected for loading")
        messagebox.showinfo("Select", "Please select a project to load")
        return
    path = PROJECTS_DIR / val
    if not path.exists():
        # try with .json
        path = PROJECTS_DIR / (val + ".json")
    if not path.exists():
        logging.error(f"Project file not found: {val}")
        messagebox.showerror("Not found", f"Project file not found: {val}")
        return
    global current_project
    current_project = Project.load(path)
    logging.info(f"Loaded project '{current_project.name}' with {len(current_project.items)} items")
    logging.debug(f"Loaded project contents: {current_project.items}")
    entry_proj.delete(0, "end")
    entry_proj.insert(0, current_project.name)
    update_views()


def on_add_item():
    itm = entry_item.get().strip()
    logging.info(f"Adding item: {itm}")
    if not itm:
        logging.warning("No item name provided")
        messagebox.showinfo("Input", "Please enter an item name")
        return
    if itm not in RECIPES:
        logging.error(f"Invalid item requested: {itm}")
        messagebox.showerror("Invalid Item", f"Item does not exist: {itm}")
        return
    try:
        q = int(entry_qty.get())
        if q <= 0:
            raise ValueError("Quantity must be positive")
        logging.info(f"Adding {q}x {itm}")
        logging.debug(f"Current project items before add: {current_project.items}")
    except ValueError as e:
        logging.error(f"Invalid quantity entered: {entry_qty.get()}")
        messagebox.showerror("Quantity", "Enter a positive integer quantity")
        return
    current_project.items[itm] = current_project.items.get(itm, 0) + q
    logging.debug(f"Updated project items: {current_project.items}")
    update_views()


# Wire buttons
btn_new.config(command=on_new_project)
btn_save.config(command=on_save_project)
btn_load.config(command=on_load_project)
btn_add.config(command=on_add_item)

# Initial population
refresh_projects_combo()
update_views()

for i in range(3):
    main.columnconfigure(i, weight=1)

root.mainloop()
