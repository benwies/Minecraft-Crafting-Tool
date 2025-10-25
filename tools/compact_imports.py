from pathlib import Path


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

    j = i - 1

    start = j

    while start >= 0 and out[start].strip() == "":

        start -= 1

    if start >= 0 and any((is_import(l) for l in out[: start + 1])):

        out = out[: start + 1] + [""] + out[i:]

    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


if __name__ == "__main__":

    p = Path("d:\\code\\mc\\main.py")

    src = p.read_text(encoding="utf-8")

    out = compact_import_newlines(src)

    if out != src:

        p.write_text(out, encoding="utf-8")

        print("Compacted import newlines in main.py")

    else:

        print("No import newline changes needed")
