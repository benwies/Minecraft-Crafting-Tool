import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from PIL import Image, ImageTk
from code import load_recipes, calculate_requirements, aggregate_requirements


BASE = Path(__file__).parent
RECIPES_PATHS = [BASE / "recepies.json", BASE / "recipes.json"]
PIC_DIR = BASE / "pic"
RECIPES = {}
for p in RECIPES_PATHS:
    if p.exists():
        try:
            RECIPES = load_recipes(str(p))
            break
        except Exception:
            RECIPES = {}

# Cache for item images
ITEM_IMAGES = {}


PROJECTS_DIR = BASE / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)


def format_stacks(qty: int) -> str:
    stacks = qty // 64
    rem = qty % 64
    if stacks > 0:
        return f"{stacks} stack(s) + {rem}"
    return "-"


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
# Autocomplete: keep an all-items list and use a StringVar to track typing
ALL_ITEMS = sorted(list(RECIPES.keys()))
item_var = tk.StringVar()
entry_item = ttk.Combobox(left, textvariable=item_var, values=ALL_ITEMS)
entry_item.grid(row=0, column=1, sticky="ew")

# --- Autocomplete popup (Toplevel + Listbox) ---
# We'll show a small popup listbox under the combobox entry so suggestions
# remain visible while the user keeps typing (the popup won't steal focus).
_suggestion_win = None
_suggestion_listbox = None

def _hide_suggestions():
    global _suggestion_win, _suggestion_listbox
    try:
        if _suggestion_win:
            _suggestion_win.destroy()
    except Exception:
        pass
    _suggestion_win = None
    _suggestion_listbox = None


def _accept_suggestion(evt=None):
    global _suggestion_listbox
    if not _suggestion_listbox:
        return
    sel = _suggestion_listbox.curselection()
    if not sel:
        return
    value = _suggestion_listbox.get(sel[0])
    item_var.set(value)
    _hide_suggestions()
    try:
        entry_item.icursor('end')
    except Exception:
        pass


def _show_suggestions(suggestions):
    global _suggestion_win, _suggestion_listbox
    _hide_suggestions()
    if not suggestions:
        return
    try:
        _suggestion_win = tk.Toplevel(root)
        _suggestion_win.wm_overrideredirect(True)
        _suggestion_win.attributes('-topmost', True)
        _suggestion_listbox = tk.Listbox(_suggestion_win, activestyle='none')
        for s in suggestions:
            _suggestion_listbox.insert('end', s)
        _suggestion_listbox.pack(fill='both', expand=True)

        x = entry_item.winfo_rootx()
        y = entry_item.winfo_rooty() + entry_item.winfo_height()
        width = entry_item.winfo_width()
        height = min(6, len(suggestions)) * 20
        _suggestion_win.geometry(f"{width}x{height}+{x}+{y}")

        _suggestion_listbox.bind('<Double-Button-1>', _accept_suggestion)
        _suggestion_listbox.bind('<Return>', _accept_suggestion)
        _suggestion_listbox.bind('<FocusOut>', lambda e: _hide_suggestions())
    except Exception:
        _hide_suggestions()


def _update_item_suggestions(event=None):
    typed = item_var.get() or ""
    if typed == "":
        _hide_suggestions()
        return
    lower = typed.lower()
    suggestions = [it for it in ALL_ITEMS if lower in it.lower()]
    if suggestions:
        _show_suggestions(suggestions)
    else:
        _hide_suggestions()


# Bind key releases to update suggestions as the user types
entry_item.bind('<KeyRelease>', _update_item_suggestions)
entry_item.bind('<Down>', lambda e: (_suggestion_listbox.focus_set(), _suggestion_listbox.selection_set(0)) if _suggestion_listbox else None)
# Quantity mode: either raw quantity or stacks of 64
mode_var = tk.StringVar(value="Qty")
ttk.Label(left, text="Mode:").grid(row=1, column=0, sticky="w")
mode_combo = ttk.Combobox(left, textvariable=mode_var, values=("Qty", "Stacks"), width=8, state="readonly")
mode_combo.grid(row=1, column=0, sticky="e", padx=(0,6))
# Numeric entry for the chosen mode (Qty or Stacks)
entry_qty = ttk.Entry(left)
entry_qty.grid(row=1, column=1, sticky="ew")
entry_qty.insert(0, "1")

def _mode_changed(event=None):
    """Optional: keep focus in the qty entry after changing mode."""
    try:
        entry_qty.focus_set()
        entry_qty.select_range(0, 'end')
    except Exception:
        pass

mode_combo.bind('<<ComboboxSelected>>', _mode_changed)
btn_add = ttk.Button(left, text="Add / Increment")
btn_add.grid(row=2, column=0, sticky="ew", padx=2, pady=6)
# Remove button for selected project item(s)
btn_remove = ttk.Button(left, text="Remove Selected")
btn_remove.grid(row=2, column=1, sticky="ew", padx=2, pady=6)

items_tree = ttk.Treeview(left, columns=("item", "qty", "stacks"), show="tree headings", height=12)
items_tree.heading("#0", text="")  # Image column
items_tree.heading("item", text="Item")
items_tree.heading("qty", text="Qty")
items_tree.heading("stacks", text="Stacks")
items_tree.column("#0", width=40, stretch=False)  # Fixed width for images
items_tree.column("item", width=180, anchor="w", stretch=True)
items_tree.column("qty", width=60, anchor="center", stretch=False)
items_tree.column("stacks", width=100, anchor="w", stretch=False)
items_tree.grid(row=4, column=0, columnspan=2, sticky="nsew")
# Make the two button columns equally sized so Add / Remove look balanced
left.columnconfigure(0, weight=1, uniform="btn")
left.columnconfigure(1, weight=1, uniform="btn")


# Right: raw materials
right = ttk.LabelFrame(main, text="Raw Materials", padding=8)
right.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
materials_tree = ttk.Treeview(right, columns=("item", "qty", "stacks"), show="tree headings", height=20)
materials_tree.heading("#0", text="")  # Image column
materials_tree.heading("item", text="Item")
materials_tree.heading("qty", text="Qty")
materials_tree.heading("stacks", text="Stacks")
materials_tree.column("#0", width=40, stretch=False)  # Fixed width for images
materials_tree.column("item", width=200, anchor="w", stretch=True)
materials_tree.column("qty", width=60, anchor="center", stretch=False)
materials_tree.column("stacks", width=120, anchor="w", stretch=False)
materials_tree.grid(row=0, column=0, sticky="nsew")
right.columnconfigure(0, weight=1)


# Internal state
current_project = Project("untitled")

def load_item_image(item_name):
    """Load and cache an item's image"""
    # If we've already cached this exact key, return it
    if item_name in ITEM_IMAGES:
        return ITEM_IMAGES[item_name]

    # Preserve the originally requested name (e.g. 'planks') and
    # map it to a concrete texture name to look up (e.g. 'oak_planks').
    requested_name = item_name
    # Define mappings for generic material names to specific textures
    material_mappings = {
        "planks": "oak_planks",
        "stone_tool_materials": "cobblestone",
        "wooden_tool_materials": "oak_planks",
        "iron_tool_materials": "iron_ingot",
        "diamond_tool_materials": "diamond",
        "gold_tool_materials": "gold_ingot",
        "copper_tool_materials": "copper_ingot",
        "stone_crafting_materials": "cobblestone",
    }
    lookup_name = material_mappings.get(item_name, item_name)

    # If the lookup image has already been cached under its concrete name,
    # reuse it and also cache it under the requested name.
    if lookup_name in ITEM_IMAGES:
        ITEM_IMAGES[requested_name] = ITEM_IMAGES[lookup_name]
        return ITEM_IMAGES[requested_name]

    # Try common item image patterns for the lookup name
    possible_names = [
        f"{lookup_name}.png",
        f"{lookup_name}_top.png",
        f"{lookup_name}_side.png",
        f"{lookup_name}_front.png"
    ]
    
    for name in possible_names:
        img_path = PIC_DIR / name
        if img_path.exists():
            try:
                # Load and resize the image to 24x24 pixels
                img = Image.open(img_path)
                # Convert to RGBA if necessary
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img = img.resize((20, 20), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                # Cache under both the concrete lookup name and the originally
                # requested name so future lookups succeed regardless of which
                # key is used.
                ITEM_IMAGES[lookup_name] = photo
                ITEM_IMAGES[requested_name] = photo
                return photo
            except Exception as e:
                logging.warning(f"Failed to load image for {item_name} ({name}): {e}")
                continue
    
    logging.debug(f"No image found for {requested_name} (lookup: {lookup_name})")
    # If no image found, cache None under the requested name to avoid repeated disk checks
    ITEM_IMAGES[requested_name] = None
    return None


def refresh_projects_combo():
    combo_projects["values"] = [p.name for p in list_project_files()]


def refresh_items_view():
    style = ttk.Style()
    style.configure('Treeview', rowheight=26)  # Increase row height to fit images
    
    for r in items_tree.get_children():
        items_tree.delete(r)
    for itm, q in sorted(current_project.items.items()):
        img = load_item_image(itm)
        items_tree.insert("", "end", iid=itm, image=img if img else "", text="", values=(format_item_name(itm), q, format_stacks(q)))


def format_item_name(name: str) -> str:
    """Convert item_name_with_underscores to Title Case With Spaces"""
    # Handle special cases
    name_mappings = {
        "copper_tool_materials": "Copper Ingot",
        "stone_tool_materials": "Cobblestone",
        "wooden_tool_materials": "Oak Planks",
        "iron_tool_materials": "Iron Ingot",
        "diamond_tool_materials": "Diamond",
        "gold_tool_materials": "Gold Ingot",
        "stone_crafting_materials": "Cobblestone",
        "planks": "Oak Planks"
    }
    if name in name_mappings:
        return name_mappings[name]
    # Default formatting: replace underscores with spaces and title case
    return name.replace('_', ' ').title()

def refresh_materials_view():
    try:
        style = ttk.Style()
        style.configure('Treeview', rowheight=26)  # Increase row height to fit images
        
        mats = aggregate_requirements(RECIPES, current_project.items)
        for r in materials_tree.get_children():
            materials_tree.delete(r)
        for mat, q in sorted(mats.items()):
            img = load_item_image(mat)
            materials_tree.insert("", "end", iid=mat, image=img if img else "", text="", values=(format_item_name(mat), q, format_stacks(q)))
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
        raw = int(entry_qty.get())
        if mode_var.get() == "Stacks":
            q = raw * 64
        else:
            q = raw
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


def on_remove_item():
    """Remove the selected item(s) from the current project and refresh views."""
    sel = items_tree.selection()
    if not sel:
        messagebox.showinfo("Select", "Please select one or more items to remove")
        return
    removed = []
    for iid in sel:
        # Ensure we remove from project state if present
        if iid in current_project.items:
            removed.append(iid)
            del current_project.items[iid]
    logging.info(f"Removed items from project: {removed}")
    update_views()


# Wire buttons
btn_new.config(command=on_new_project)
btn_save.config(command=on_save_project)
btn_load.config(command=on_load_project)
btn_add.config(command=on_add_item)
btn_remove.config(command=on_remove_item)

# Initial population
refresh_projects_combo()
update_views()

for i in range(3):
    main.columnconfigure(i, weight=1)

root.mainloop()
