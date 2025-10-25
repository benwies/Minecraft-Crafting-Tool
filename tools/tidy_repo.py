import os

from pathlib import Path

import re

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", "__pycache__"}


def is_import(line: str) -> bool:

    s = line.lstrip()

    return s.startswith("import ") or s.startswith("from ")


def compact_import_newlines(text: str) -> str:

    lines = text.splitlines()

    out = []

    n = len(lines)

    def next_nonblank_is_import(idx: int) -> bool:

        j = idx + 1

        while j < n and lines[j].strip() == "":

            j += 1

        if j < n:

            return is_import(lines[j])

        return False

    prev_is_import = False

    for i, line in enumerate(lines):

        if line.strip() == "" and prev_is_import and next_nonblank_is_import(i):

            continue

        out.append(line)

        prev_is_import = is_import(line)

    i = 0

    while i < len(out) and (out[i].strip() == "" or is_import(out[i])):

        i += 1

    start = i - 1

    while start >= 0 and out[start].strip() == "":

        start -= 1

    if start >= 0 and any((is_import(l) for l in out[: start + 1])):

        out = out[: start + 1] + [""] + out[i:]

    return "\n".join(out)


def collapse_blanks_and_trailing(text: str) -> str:

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []

    for ln in text.split("\n"):

        leading = len(ln) - len(ln.lstrip("\t"))

        if leading:

            ln = " " * 4 * leading + ln.lstrip("\t")

        ln = re.sub("[\\t ]+$", "", ln)

        lines.append(ln)

    text = "\n".join(lines)

    text = re.sub("\\n{3,}", "\n\n", text)

    text = re.sub("\\n{2,}", "\n\n", text)

    return text


def tidy_code(text: str) -> str:

    a = compact_import_newlines(text)

    b = collapse_blanks_and_trailing(a)

    if not b.endswith("\n"):

        b += "\n"

    return b


def main():

    changed = 0

    checked = 0

    for root, dirs, files in os.walk(ROOT):

        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in files:

            if not fname.endswith(".py"):

                continue

            p = Path(root) / fname

            try:

                src = p.read_text(encoding="utf-8")

            except Exception:

                try:

                    src = p.read_text(encoding="latin-1")

                except Exception:

                    continue

            checked += 1

            out = tidy_code(src)

            if out != src:

                try:

                    p.write_text(out, encoding="utf-8")

                    changed += 1

                except Exception:

                    pass

    print(f"Tidy completed. Checked {checked} .py files, modified {changed}.")


if __name__ == "__main__":

    main()
