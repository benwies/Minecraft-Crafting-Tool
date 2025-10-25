import json
import copy
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
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

# Index available images in PIC_DIR by base name (lowercase, no extension)
PIC_INDEX = {}
for p in PIC_DIR.glob("*.png"):
    try:
        key = p.stem.lower()
        PIC_INDEX[key] = p
    except Exception:
        pass


PROJECTS_DIR = BASE / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

# --- Undo/Redo history ---
UNDO_STACK = []  # list of snapshots
REDO_STACK = []
MAX_HISTORY = 5

def snapshot_state():
    return {
        "name": current_project.name if 'current_project' in globals() else "",
        "items": copy.deepcopy(current_project.items) if 'current_project' in globals() else {}
    }

def apply_state(state):
    try:
        current_project.name = state.get("name", current_project.name)
        current_project.items = dict(state.get("items", {}))
        # Reflect name into entry field
        try:
            entry_proj.delete(0, 'end')
            entry_proj.insert(0, current_project.name)
        except Exception:
            pass
        update_views()
    except Exception as e:
        logging.error(f"Failed to apply state: {e}")

def _update_undo_redo_buttons():
    try:
        btn_undo.config(state=("normal" if UNDO_STACK else "disabled"))
        btn_redo.config(state=("normal" if REDO_STACK else "disabled"))
    except Exception:
        pass

def record_undo(label: str = "change"):
    """Record the current state for undo, clear redo."""
    try:
        UNDO_STACK.append(snapshot_state())
        while len(UNDO_STACK) > MAX_HISTORY:
            UNDO_STACK.pop(0)
        REDO_STACK.clear()
        _update_undo_redo_buttons()
        logging.debug(f"Recorded undo snapshot ({label}); undo depth={len(UNDO_STACK)}")
    except Exception as e:
        logging.error(f"Failed to record undo: {e}")

def clear_history():
    UNDO_STACK.clear()
    REDO_STACK.clear()
    _update_undo_redo_buttons()


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

# --- Theming: Modern light/dark styles ---
current_theme = 'light'
THEME_PALETTE = {}

def apply_theme(name: str = 'light'):
    global current_theme
    current_theme = name
    style = ttk.Style()
    # Use a configurable theme as base
    try:
        style.theme_use('clam')
    except Exception:
        pass

    # Palettes
    LIGHT = {
        'bg': '#F3F4F6',
        'surface': '#FFFFFF',
        'text': '#111827',
        'subtext': '#374151',
        'accent': '#2563EB',
        'border': '#E5E7EB',
        'hover': '#E5E7EB',
        'select': '#DBEAFE',
        'header_bg': '#EEF2F7',
        'header_text': '#111827',
        'tree_bg': '#FFFFFF',
        'tree_alt': '#F9FAFB',
    }
    DARK = {
        'bg': '#0F172A',
        'surface': '#111827',
        'text': '#E5E7EB',
        'subtext': '#9CA3AF',
        'accent': '#60A5FA',
        'border': '#1F2937',
        'hover': '#1F2937',
        'select': '#1E3A8A',
        'header_bg': '#1F2937',
        'header_text': '#E5E7EB',
        'tree_bg': '#111827',
        'tree_alt': '#0F172A',
    }
    global THEME_PALETTE
    P = LIGHT if name == 'light' else DARK
    THEME_PALETTE = P

    # Fonts
    try:
        default_font = tkfont.nametofont('TkDefaultFont')
        default_font.configure(family='Segoe UI', size=10)
        text_font = tkfont.nametofont('TkTextFont')
        text_font.configure(family='Segoe UI', size=10)
        heading_font = tkfont.nametofont('TkHeadingFont')
        heading_font.configure(family='Segoe UI Semibold', size=10)
    except Exception:
        pass

    root.configure(bg=P['bg'])
    style.configure('TFrame', background=P['bg'])
    style.configure('Topbar.TFrame', background=P['surface'])
    style.configure('TLabel', background=P['bg'], foreground=P['text'])
    style.configure('Topbar.TLabel', background=P['surface'], foreground=P['text'])
    style.configure('TLabelframe', background=P['bg'], bordercolor=P['border'])
    style.configure('TLabelframe.Label', background=P['bg'], foreground=P['subtext'])
    style.configure('TButton', padding=(10, 6), relief='flat')
    style.map('TButton', background=[('active', P['hover'])])
    style.configure('Toolbutton', padding=(6, 4), relief='flat')
    style.map('Toolbutton', background=[('active', P['hover'])])

    # Inputs
    style.configure('TEntry', fieldbackground=P['surface'], foreground=P['text'])
    style.configure('TCombobox', fieldbackground=P['surface'], foreground=P['text'], background=P['surface'])
    # Specialized style for the Mode combobox (Qty/Stacks)
    if name == 'dark':
        mode_bg = '#FFFFFF'
        mode_fg = '#111827'
    else:
        mode_bg = P['surface']
        mode_fg = P['text']
    style.configure('Mode.TCombobox', fieldbackground=mode_bg, foreground=mode_fg, background=mode_bg)
    style.map('Mode.TCombobox', fieldbackground=[('readonly', mode_bg)], foreground=[('readonly', mode_fg)])
    # Selection and cursor colors via option database (applies to native subwidgets)
    try:
        root.option_clear()
    except Exception:
        pass
    root.option_add('*Entry.selectBackground', P['select'])
    root.option_add('*Entry.selectForeground', P['text'])
    root.option_add('*Entry.insertBackground', P['text'])
    # Combobox dropdown (Listbox inside the popdown)
    if name == 'dark':
        # In dark mode, use light menu with dark text for readability
        root.option_add('*TCombobox*Listbox*background', '#FFFFFF')
        root.option_add('*TCombobox*Listbox*foreground', '#111827')
        root.option_add('*TCombobox*Listbox*selectBackground', '#DBEAFE')
        root.option_add('*TCombobox*Listbox*selectForeground', '#111827')
    else:
        root.option_add('*TCombobox*Listbox*background', P['surface'])
        root.option_add('*TCombobox*Listbox*foreground', P['text'])
        root.option_add('*TCombobox*Listbox*selectBackground', P['select'])
        root.option_add('*TCombobox*Listbox*selectForeground', P['text'])

    # Treeview
    style.configure('Treeview', background=P['tree_bg'], fieldbackground=P['tree_bg'],
                    foreground=P['text'], bordercolor=P['border'], rowheight=26)
    style.configure('Treeview.Heading', background=P['header_bg'], foreground=P['header_text'], relief='flat')
    style.map('Treeview', background=[('selected', P['select'])], foreground=[('selected', P['text'])])

    # Apply alternating row tags if trees exist
    try:
        items_tree.tag_configure('even', background=P['tree_bg'])
        items_tree.tag_configure('odd', background=P['tree_alt'])
    except Exception:
        pass
    try:
        materials_tree.tag_configure('even', background=P['tree_bg'])
        materials_tree.tag_configure('odd', background=P['tree_alt'])
        # Done rows: grey + strike-through
        try:
            done_font = tkfont.nametofont('TkDefaultFont').copy()
            done_font.configure(overstrike=1)
        except Exception:
            done_font = ('Segoe UI', 10, 'overstrike')
        materials_tree.tag_configure('done', foreground=P['subtext'], font=done_font)
    except Exception:
        pass
    # Update theme toggle button glyph
    try:
        btn_theme.config(text=('☀' if name == 'dark' else '☾'))
    except Exception:
        pass

def toggle_theme():
    new_mode = 'dark' if current_theme == 'light' else 'light'
    apply_theme(new_mode)
    try:
        btn_theme.config(text='☀' if new_mode == 'dark' else '☾')
    except Exception:
        pass
    update_views()

# Top: project controls
proj_frame = ttk.Frame(main)
proj_frame.grid(row=0, column=0, columnspan=3, sticky="ew")

# Toolbar-like Undo/Redo on the top-left (icon-like buttons using Unicode arrows)
toolbar = ttk.Frame(proj_frame, style='Topbar.TFrame')
toolbar.grid(row=0, column=0, sticky="w")
btn_undo = ttk.Button(toolbar, text="⟲", width=3, style="Toolbutton", state="disabled")
btn_undo.pack(side="left", padx=(4, 2))
btn_redo = ttk.Button(toolbar, text="⟳", width=3, style="Toolbutton", state="disabled")
btn_redo.pack(side="left", padx=(2, 4))
spacer = ttk.Frame(toolbar)
spacer.pack(side="left", expand=True, fill="x")
btn_theme = ttk.Button(toolbar, text="☾", width=3, style="Toolbutton", command=toggle_theme)
btn_theme.pack(side="left", padx=(2, 4))

ttk.Label(proj_frame, text="Project name:").grid(row=1, column=0)
entry_proj = ttk.Entry(proj_frame)
entry_proj.grid(row=1, column=1, sticky="ew")
btn_new = ttk.Button(proj_frame, text="New Project")
btn_new.grid(row=1, column=2, padx=4)
btn_save = ttk.Button(proj_frame, text="Save Project")
btn_save.grid(row=1, column=3, padx=4)
ttk.Label(proj_frame, text="Open:").grid(row=1, column=4)
combo_projects = ttk.Combobox(proj_frame, values=[p.name for p in list_project_files()])
combo_projects.grid(row=1, column=5, sticky="ew")
btn_load = ttk.Button(proj_frame, text="Load")
btn_load.grid(row=1, column=6, padx=4)

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
_tab_pressed = False  # Flag to track if Tab was just pressed

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
        _suggestion_listbox = tk.Listbox(
            _suggestion_win, 
            activestyle='dotbox', 
            exportselection=False,
            selectmode='browse',
            highlightthickness=0
        )
        # Apply theme colors to suggestion list
        try:
            _suggestion_listbox.configure(
                bg=THEME_PALETTE.get('surface', '#FFFFFF'),
                fg=THEME_PALETTE.get('text', '#000000'),
                selectbackground=THEME_PALETTE.get('select', '#DBEAFE'),
                selectforeground=THEME_PALETTE.get('text', '#000000'),
                relief='flat', bd=1
            )
        except Exception:
            pass
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
        # Don't hide on FocusOut since we want to keep it visible during Tab navigation
    except Exception:
        _hide_suggestions()


def _update_item_suggestions(event=None):
    global _tab_pressed
    
    # Skip update if Tab was just pressed
    if _tab_pressed:
        _tab_pressed = False
        return
    
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


def _on_item_tab(event):
    """Handle Tab key to cycle through autocomplete suggestions"""
    global _suggestion_listbox, _tab_pressed
    
    # Set flag to prevent KeyRelease from updating suggestions
    _tab_pressed = True
    
    if _suggestion_listbox:
        # If suggestions are visible, cycle through them
        try:
            sel = _suggestion_listbox.curselection()
            if not sel:
                # Nothing selected yet, select first
                _suggestion_listbox.selection_clear(0, 'end')
                _suggestion_listbox.selection_set(0)
                _suggestion_listbox.activate(0)
                _suggestion_listbox.see(0)
            else:
                # Move to next suggestion
                current_idx = sel[0]
                next_idx = (current_idx + 1) % _suggestion_listbox.size()
                _suggestion_listbox.selection_clear(0, 'end')
                _suggestion_listbox.selection_set(next_idx)
                _suggestion_listbox.activate(next_idx)
                _suggestion_listbox.see(next_idx)
            # Keep focus on entry_item so user can continue typing or press Enter
            entry_item.focus_set()
            return "break"  # Prevent default Tab behavior
        except Exception as e:
            print(f"Tab error: {e}")
            _tab_pressed = False
            pass
    return None


def _on_item_enter(event):
    """Handle Enter key in item field to accept suggestion or move to quantity"""
    global _suggestion_listbox
    if _suggestion_listbox:
        # If suggestions are visible, accept the selected one
        _accept_suggestion()
        # After accepting, move to quantity field
        entry_qty.focus_set()
        entry_qty.select_range(0, 'end')
    else:
        # No suggestions, just move to quantity field
        entry_qty.focus_set()
        entry_qty.select_range(0, 'end')
    return "break"


def _on_item_escape(event):
    """Handle Escape key to close suggestions"""
    _hide_suggestions()
    return "break"


def _on_qty_enter(event):
    """Handle Enter key in quantity field to add the item"""
    on_add_item()
    return "break"


# Bind key releases to update suggestions as the user types
entry_item.bind('<KeyRelease>', _update_item_suggestions)
entry_item.bind('<Down>', lambda e: (_suggestion_listbox.focus_set(), _suggestion_listbox.selection_set(0)) if _suggestion_listbox else None)
entry_item.bind('<Tab>', _on_item_tab)
entry_item.bind('<Return>', _on_item_enter)
entry_item.bind('<Escape>', _on_item_escape)
# Quantity mode: either raw quantity or stacks of 64
mode_var = tk.StringVar(value="Qty")
ttk.Label(left, text="Mode:").grid(row=1, column=0, sticky="w")
mode_combo = ttk.Combobox(left, textvariable=mode_var, values=("Qty", "Stacks"), width=8, state="readonly", style='Mode.TCombobox')
mode_combo.grid(row=1, column=0, sticky="e", padx=(0,6))
# Numeric entry for the chosen mode (Qty or Stacks)
entry_qty = ttk.Entry(left)
entry_qty.grid(row=1, column=1, sticky="ew")
entry_qty.insert(0, "1")
entry_qty.bind('<Return>', _on_qty_enter)

def _mode_changed(event=None):
    """Optional: keep focus in the qty entry after changing mode."""
    try:
        entry_qty.focus_set()
        entry_qty.select_range(0, 'end')
    except Exception:
        pass

mode_combo.bind('<<ComboboxSelected>>', _mode_changed)
btn_add = ttk.Button(left, text="Add")
btn_add.grid(row=2, column=0, sticky="ew", padx=2, pady=6)

# Items table with per-row delete and editable qty
items_tree = ttk.Treeview(left, columns=("item", "qty", "stacks", "del"), show="tree headings", height=12)
items_tree.heading("#0", text="Img")  # Image column
items_tree.heading("item", text="Item")
items_tree.heading("qty", text="Qty")
items_tree.heading("stacks", text="Stacks")
items_tree.heading("del", text="Remove")
items_tree.column("#0", width=40, stretch=False)  # Fixed width for images
items_tree.column("item", width=180, anchor="w", stretch=True)
items_tree.column("qty", width=70, anchor="center", stretch=False)
items_tree.column("stacks", width=100, anchor="w", stretch=False)
items_tree.column("del", width=70, anchor="center", stretch=False)
items_tree.grid(row=4, column=0, columnspan=2, sticky="nsew")
# Balance buttons row
left.columnconfigure(0, weight=1)


# Right: raw materials
right = ttk.LabelFrame(main, text="Raw Materials", padding=8)
right.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
materials_tree = ttk.Treeview(right, columns=("item", "qty", "stacks", "acq"), show="tree headings", height=20)
materials_tree.heading("#0", text="Img")  # Image column
materials_tree.heading("item", text="Item")
materials_tree.heading("qty", text="Qty (missing)")
materials_tree.heading("stacks", text="Stacks")
materials_tree.heading("acq", text="Acquired")
materials_tree.column("#0", width=40, stretch=False)  # Fixed width for images
materials_tree.column("item", width=200, anchor="w", stretch=True)
materials_tree.column("qty", width=120, anchor="center", stretch=False)
materials_tree.column("stacks", width=120, anchor="w", stretch=False)
materials_tree.column("acq", width=80, anchor="center", stretch=False)
materials_tree.grid(row=0, column=0, sticky="nsew")
# Ensure the Qty header fits fully based on current font metrics
try:
    _hdr_font = tkfont.nametofont('TkHeadingFont')
    _needed_w = _hdr_font.measure("Qty (missing)") + 24  # padding for sort arrow/margins
    _cur_w = materials_tree.column("qty", option="width")
    if _needed_w > _cur_w:
        materials_tree.column("qty", width=_needed_w)
except Exception:
    pass
right.columnconfigure(0, weight=1)


# Internal state
current_project = Project("untitled")
ACQUIRED_MATS = {}  # material -> acquired quantity (int)
DONE_MATS = set()   # set of materials marked done

_acq_edit_entry = None
_hover_done_btn = None
_hover_row = None
_hide_done_after_id = None
_over_done_btn = False

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

    # Normalize the lookup key
    key = str(lookup_name).lower().replace(' ', '_')

    def _load_and_cache(img_path: Path):
        try:
            img = Image.open(img_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img = img.resize((20, 20), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            ITEM_IMAGES[lookup_name] = photo
            ITEM_IMAGES[requested_name] = photo
            return photo
        except Exception as e:
            logging.warning(f"Failed to load image for {requested_name} from {img_path.name}: {e}")
            return None

    # 1) Direct exact match
    if key in PIC_INDEX:
        photo = _load_and_cache(PIC_INDEX[key])
        if photo:
            return photo

    # 2) Try common suffix variants
    for suffix in ("", "_top", "_side", "_front"):
        cand = key + suffix
        if cand in PIC_INDEX:
            photo = _load_and_cache(PIC_INDEX[cand])
            if photo:
                return photo

    # 3) Token-based fuzzy match: prefer filenames containing all tokens
    tokens = [t for t in key.split('_') if t]
    best = None
    best_score = -1
    for base, path in PIC_INDEX.items():
        score = 0
        ok = True
        for t in tokens:
            if t in base:
                score += 1
            else:
                ok = False
                break
        if ok and score > best_score:
            best_score = score
            best = path
    if best is not None:
        photo = _load_and_cache(best)
        if photo:
            return photo

    # 3.5) Structural fallback: strip common suffix tokens and prefer base material images
    suffix_tokens = {
        'stairs','slab','wall','plate','pressure','button','door','trapdoor','fence','gate',
        'sign','hanging','pane','carpet','bed','boat','minecart','helmet','chestplate','leggings','boots',
        'concrete','powder','terracotta','glazed','stained','glass','pane','block','ore','ingot','nugget',
        'dust','tile','tiles','bricks','brick'
    }
    btokens = tokens[:]
    while btokens and btokens[-1] in suffix_tokens:
        btokens.pop()
    if btokens:
        base_key = '_'.join(btokens)
        # Direct base match
        if base_key in PIC_INDEX:
            photo = _load_and_cache(PIC_INDEX[base_key])
            if photo:
                return photo
        # Prefer wood planks for wood-type bases
        wood_types = [
            'oak','spruce','birch','jungle','acacia','dark_oak','mangrove',
            'cherry','bamboo','crimson','warped'
        ]
        if len(btokens) == 1 and btokens[0] in wood_types:
            cand = f"{btokens[0]}_planks"
            if cand in PIC_INDEX:
                photo = _load_and_cache(PIC_INDEX[cand])
                if photo:
                    return photo
        # Prefer the shortest filename beginning with base_key_
        candidates = [(base, path) for base, path in PIC_INDEX.items() if base.startswith(base_key + '_')]
        if candidates:
            candidates.sort(key=lambda x: (len(x[0].split('_')), x[0]))
            photo = _load_and_cache(candidates[0][1])
            if photo:
                return photo

    # 4) Wood fallback: if name includes a wood type, fall back to its planks
    wood_types = [
        'oak','spruce','birch','jungle','acacia','dark_oak','mangrove',
        'cherry','bamboo','crimson','warped'
    ]
    for wt in wood_types:
        if wt in key:
            plank_key = f"{wt}_planks"
            if plank_key in PIC_INDEX:
                photo = _load_and_cache(PIC_INDEX[plank_key])
                if photo:
                    return photo
            break

    logging.debug(f"No image found for {requested_name} (lookup: {lookup_name}); caching None")
    ITEM_IMAGES[requested_name] = None
    return None


_qty_edit_entry = None

def _begin_qty_edit(item_id: str):
    """Overlay an Entry over the Qty cell for inline edit."""
    global _qty_edit_entry
    try:
        bbox = items_tree.bbox(item_id, '#2')  # Qty column
        if not bbox:
            return
        x, y, w, h = bbox
        # Create entry
        _qty_edit_entry = ttk.Entry(items_tree)
        _qty_edit_entry.place(x=x, y=y, width=w, height=h)
        _qty_edit_entry.insert(0, str(current_project.items.get(item_id, 0)))
        _qty_edit_entry.focus_set()
        _qty_edit_entry.select_range(0, 'end')

        def _commit(*_):
            global _qty_edit_entry
            try:
                new_val = int(_qty_edit_entry.get())
            except Exception:
                new_val = None
            _qty_edit_entry.destroy()
            _qty_edit_entry = None
            if new_val is None:
                return
            if new_val <= 0:
                # Remove the item if set to 0 or negative
                record_undo("edit_qty_remove")
                current_project.items.pop(item_id, None)
            else:
                record_undo("edit_qty")
                current_project.items[item_id] = new_val
            update_views()

        def _cancel(*_):
            global _qty_edit_entry
            if _qty_edit_entry:
                _qty_edit_entry.destroy()
                _qty_edit_entry = None

        _qty_edit_entry.bind('<Return>', _commit)
        _qty_edit_entry.bind('<FocusOut>', _commit)
        _qty_edit_entry.bind('<Escape>', _cancel)
    except Exception as e:
        logging.error(f"Failed to begin qty edit for {item_id}: {e}")


def _on_items_tree_double_click(event):
    """Start editing qty when double-clicking the Qty cell."""
    row_id = items_tree.identify_row(event.y)
    col = items_tree.identify_column(event.x)
    if not row_id:
        return
    if col == '#2':  # Qty column
        _begin_qty_edit(row_id)


def _on_items_tree_click(event):
    """Handle delete click on X column."""
    row_id = items_tree.identify_row(event.y)
    col = items_tree.identify_column(event.x)
    if not row_id:
        return
    if col == '#4':  # del column
        if row_id in current_project.items:
            record_undo("delete_item")
            del current_project.items[row_id]
            update_views()


def refresh_projects_combo():
    combo_projects["values"] = [p.name for p in list_project_files()]


def refresh_items_view():
    style = ttk.Style()
    style.configure('Treeview', rowheight=26)  # Increase row height to fit images
    
    for r in items_tree.get_children():
        items_tree.delete(r)
    for idx, (itm, q) in enumerate(sorted(current_project.items.items())):
        img = load_item_image(itm)
        tag = 'odd' if idx % 2 else 'even'
        items_tree.insert("", "end", iid=itm, image=img if img else "", text="", values=(format_item_name(itm), q, format_stacks(q), "X"), tags=(tag,))


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
        for idx, (mat, q) in enumerate(sorted(mats.items())):
            img = load_item_image(mat)
            tag = 'odd' if idx % 2 else 'even'
            acq = max(int(ACQUIRED_MATS.get(mat, 0)), 0)
            missing = max(q - acq, 0)
            qty_display = f"{q} ({missing})"
            row = materials_tree.insert("", "end", iid=mat, image=img if img else "", text="", values=(format_item_name(mat), qty_display, format_stacks(q), acq), tags=(tag,))
            # Apply done tag if marked done
            if mat in DONE_MATS:
                materials_tree.item(row, tags=(tag, 'done'))
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
    clear_history()
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
    clear_history()
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
    # Record undo before mutating
    record_undo("add_item")
    current_project.items[itm] = current_project.items.get(itm, 0) + q
    logging.debug(f"Updated project items: {current_project.items}")
    update_views()
    
    # Clear inputs after successful add
    entry_item.delete(0, "end")  # Clear item field
    entry_qty.delete(0, "end")   # Clear quantity field (leave empty)
    entry_item.focus_set()       # Set focus back to item field
    _hide_suggestions()          # Hide the suggestion popup if visible


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

# Bind tree interactions for inline edit/delete
items_tree.bind('<Double-1>', _on_items_tree_double_click)
items_tree.bind('<Button-1>', _on_items_tree_click)

# Undo/Redo handlers
def on_undo():
    if not UNDO_STACK:
        return
    # Push current to redo, restore from undo
    REDO_STACK.append(snapshot_state())
    state = UNDO_STACK.pop()
    apply_state(state)
    _update_undo_redo_buttons()


def on_redo():
    if not REDO_STACK:
        return
    UNDO_STACK.append(snapshot_state())
    state = REDO_STACK.pop()
    apply_state(state)
    _update_undo_redo_buttons()

btn_undo.config(command=on_undo)
btn_redo.config(command=on_redo)

# --- Materials interactions: inline edit for Acquired and hover Done button ---
def _begin_acq_edit(mat_id: str):
    global _acq_edit_entry
    try:
        bbox = materials_tree.bbox(mat_id, 'acq')
        if not bbox:
            return
        x, y, w, h = bbox
        _acq_edit_entry = ttk.Entry(materials_tree)
        _acq_edit_entry.place(x=x, y=y, width=w, height=h)
        _acq_edit_entry.insert(0, str(ACQUIRED_MATS.get(mat_id, 0)))
        _acq_edit_entry.focus_set()
        _acq_edit_entry.select_range(0, 'end')

        def _commit(*_):
            global _acq_edit_entry
            val = _acq_edit_entry.get().strip()
            try:
                n = int(val)
            except Exception:
                n = 0
            _acq_edit_entry.destroy()
            _acq_edit_entry = None
            ACQUIRED_MATS[mat_id] = max(n, 0)
            refresh_materials_view()

        def _cancel(*_):
            global _acq_edit_entry
            if _acq_edit_entry:
                _acq_edit_entry.destroy()
                _acq_edit_entry = None

        _acq_edit_entry.bind('<Return>', _commit)
        _acq_edit_entry.bind('<FocusOut>', _commit)
        _acq_edit_entry.bind('<Escape>', _cancel)
    except Exception as e:
        logging.error(f"Failed to begin acquired edit for {mat_id}: {e}")


def _on_materials_double_click(event):
    row_id = materials_tree.identify_row(event.y)
    col = materials_tree.identify_column(event.x)
    if not row_id:
        return
    # If double-click Acquired column, edit
    if col in ('#4', 'acq'):
        _begin_acq_edit(row_id)


def _cancel_hide_done():
    global _hide_done_after_id
    if _hide_done_after_id is not None:
        try:
            root.after_cancel(_hide_done_after_id)
        except Exception:
            pass
        _hide_done_after_id = None


def _schedule_hide_done(delay=150):
    global _hide_done_after_id
    _cancel_hide_done()
    try:
        _hide_done_after_id = root.after(delay, _hide_done_button)
    except Exception:
        _hide_done_button()


def _on_done_enter(event=None):
    global _over_done_btn
    _over_done_btn = True
    _cancel_hide_done()


def _on_done_leave(event=None):
    global _over_done_btn
    _over_done_btn = False
    _schedule_hide_done(150)


def _ensure_done_button():
    global _hover_done_btn
    if _hover_done_btn is None:
        _hover_done_btn = ttk.Button(materials_tree, text='Done', style='Toolbutton')
        _hover_done_btn.bind('<Button-1>', _on_done_click)
        _hover_done_btn.bind('<Enter>', _on_done_enter)
        _hover_done_btn.bind('<Leave>', _on_done_leave)


def _on_done_click(event=None):
    global _hover_row
    if not _hover_row:
        return
    mat = _hover_row
    if mat in DONE_MATS:
        DONE_MATS.remove(mat)
    else:
        DONE_MATS.add(mat)
    refresh_materials_view()
    _hide_done_button()


def _hide_done_button():
    global _hover_done_btn
    _cancel_hide_done()
    if _hover_done_btn:
        _hover_done_btn.place_forget()


def _on_materials_motion(event):
    """Show a small Done button when hovering over a material row."""
    global _hover_row
    _cancel_hide_done()
    row = materials_tree.identify_row(event.y)
    if not row:
        _hover_row = None
        # If pointer is not over the tree rows and not over the button, schedule hide
        if not _over_done_btn:
            _schedule_hide_done(120)
        return
    if row != _hover_row:
        _hover_row = row
    # Place button at right edge of the Item column
    try:
        bbox = materials_tree.bbox(row, 'item')
        if not bbox:
            _hide_done_button()
            return
        x, y, w, h = bbox
        _ensure_done_button()
        _hover_done_btn.configure(text=('Undo' if row in DONE_MATS else 'Done'))
        # Position a bit inside the item cell on the right
        btn_w = 50
        _hover_done_btn.place(x=x + max(w - btn_w - 4, 0), y=y, width=btn_w, height=h)
    except Exception:
        _hide_done_button()


def _on_materials_leave(event):
    # When leaving the tree (e.g., moving onto the button), don't instantly hide; debounce instead
    if not _over_done_btn:
        _schedule_hide_done(150)


materials_tree.bind('<Double-1>', _on_materials_double_click)
materials_tree.bind('<Motion>', _on_materials_motion)
materials_tree.bind('<Leave>', _on_materials_leave)

# Initial population and apply theme last so styles reach all widgets
apply_theme('dark')
refresh_projects_combo()
update_views()

for i in range(3):
    main.columnconfigure(i, weight=1)

root.mainloop()
