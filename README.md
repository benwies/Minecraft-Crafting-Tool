# MC Crafting Calculator

A fast, friendly Windows tool to plan Minecraft builds by calculating all required raw materials for your project. Create projects, add items (by quantity or stacks), and get a clear list of everything you need — with sorting, progress tracking, and autosave.

## Download and install

- Recommended (Installer): Download the latest “MCCraftingCalculator-Setup-…​.exe” from the latest release and run it.
- Portable (No install): Download the “MCCraftingCalculator-Portable-…​.zip”, extract, then run `MCCraftingCalculator.exe`.

Latest release: https://github.com/benwies/mc/releases/latest

Windows SmartScreen: Because this app isn’t code‑signed, Windows may warn on first run. Click “More info” → “Run anyway”.

## Key features

- Project-based planning with autosave
- Calculate total raw materials for any set of items
- Add items by quantity or stacks (64)
- Sort materials by item, missing qty, stacks, or acquired
- Track progress: mark acquired/done, add custom materials
- Light/Dark theme, clean modern UI
- Image previews for items; add your own images to override

## Quick start

1) Open the app and name your project (top left).
2) Add items:
	 - Choose “Qty” or “Stacks”, enter a value, pick an item, and click “Add”.
3) Review the “Raw Materials” list and sort as needed.
4) Track progress:
	 - Enter “Acquired” amounts to see missing quantities update live.
	 - Use the context/row actions to mark items done/undone.
5) Save/Load projects from the toolbar.

Tips
- Use the search suggestions when adding items or materials.
- Add custom materials in the “Raw Materials” panel (e.g., Dirt, Sand, etc.).
- Right‑click or use UI actions to set/override an image for any material.

## Where data is stored

- Projects and logs: `%LOCALAPPDATA%\MC Crafting Calculator\`
- Custom images (optional): `%LOCALAPPDATA%\MC Crafting Calculator\pic\` (PNG files)

These locations don’t require admin rights and are created automatically.

## Requirements

- Windows 10 or 11
- No separate Python install needed when using the installer or portable ZIP

## Build it yourself (optional)

If you want to reproduce the Windows artifacts locally:

1) Install Python 3.10+ and Inno Setup (for the installer).
2) Run the all‑in‑one build script in PowerShell:

```powershell
& .\tools\build\build_all.ps1 -Version "1.0.0" -Publisher "Benedikt Wiesner"
```

This produces:
- One‑folder app: `dist/MCCraftingCalculator/`
- Portable ZIP: `dist/MCCraftingCalculator-portable.zip`
- Installer EXE: `dist/installer/MCCraftingCalculator-Setup.exe`

## Troubleshooting

- Missing or wrong item image:
	- Place a PNG named like the material (e.g., `oak_planks.png`) in `%LOCALAPPDATA%\MC Crafting Calculator\pic\`.
- SmartScreen/AV warning:
	- The app is unsigned; use “More info” → “Run anyway”, or use the portable ZIP.
- Logs:
	- Check `%LOCALAPPDATA%\MC Crafting Calculator\minecraft_calculator.log` for details.

## License

This project’s license (if any) is provided in the repository. If no license is present, all rights are reserved by the author.


