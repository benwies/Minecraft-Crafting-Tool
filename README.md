# Minecraft Farm Resource Calculator — MVP

Simple Python/Tkinter MVP that calculates base materials needed to craft a given quantity of an item using a small internal recipe database.

Quick start (Windows PowerShell):

1. Make sure you have Python 3 installed and available on PATH.
2. From the project folder (`D:\code\mc`) run:

```powershell
# Run the test
C:/Users/phnx/AppData/Local/Programs/Python/Python313/python.exe .\test_calc.py
# or to run the GUI
C:/Users/phnx/AppData/Local/Programs/Python/Python313/python.exe .\main.py
```

Files used here:
- `recepies.json` — small built-in recipe database (note spelling preserved)
- `code.py` — calculation logic (load_recipes + recursive aggregator)
- `main.py` — Tkinter GUI runner
- `test_calc.py` — tiny test to validate the core logic

Notes:
- This MVP treats any item not present in `recepies.json` as a base material.
- Future improvements: import/export recipes, autocomplete/search, inventory accounting, full crafting tree expansion.
