from pathlib import Path

import re


def collapse_blank_lines(text: str) -> str:

    text = text.replace("\r\n", "\n")

    lines = [re.sub("[\\t ]+$", "", line) for line in text.split("\n")]

    text = "\n".join(lines)

    text = re.sub("\\n{3,}", "\n\n", text)

    return text


if __name__ == "__main__":

    p = Path("d:\\code\\mc\\main.py")

    src = p.read_text(encoding="utf-8")

    out = collapse_blank_lines(src)

    if out != src:

        p.write_text(out, encoding="utf-8")

        print("Updated main.py (collapsed blank lines).")

    else:

        print("No changes needed.")
