from PIL import Image
import sys
from pathlib import Path

# Usage:
#   - Auto-detect: python tools/build/make_icon.py
#     Finds PNG/JPG in the same folder and writes tools/build/app.ico
#   - Manual: python tools/build/make_icon.py <input.(png|jpg)> [output.ico]
# Produces a multi-size Windows .ico suitable for PyInstaller and Inno Setup shortcuts.


def _find_source_image() -> Path | None:
    folder = Path(__file__).parent
    # Prefer files named "icon" first
    preferred = [
        folder / "icon.png",
        folder / "icon.jpg",
        folder / "icon.jpeg",
    ]
    for p in preferred:
        if p.exists():
            return p
    # Otherwise, pick the most recently modified png/jpg/jpeg in the folder
    candidates = (
        list(folder.glob("*.png"))
        + list(folder.glob("*.jpg"))
        + list(folder.glob("*.jpeg"))
    )
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def main():
    if len(sys.argv) >= 2:
        src = Path(sys.argv[1])
    else:
        src = _find_source_image()

    if not src or not src.exists():
        print(
            "No source image found. Place an icon.png/.jpg next to make_icon.py or pass a path."
        )
        sys.exit(1)

    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "app.ico"

    img = Image.open(src).convert("RGBA")
    # Common Windows icon sizes
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = [img.resize(sz, Image.Resampling.LANCZOS) for sz in sizes]
    dst.parent.mkdir(parents=True, exist_ok=True)
    icons[0].save(dst, format="ICO", sizes=sizes)
    print(f"Source: {src}")
    print(f"Wrote icon: {dst}")


if __name__ == "__main__":
    main()
