import sys

import os

import io

import tokenize

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {"__pycache__", ".git", "pic", "projects"}

SKIP_FILES = {__file__}


def strip_hash_comments_from_code(code: str) -> str:

    src = io.StringIO(code)

    out = io.StringIO()

    prev_end = (1, 0)

    try:

        tokens = list(tokenize.generate_tokens(src.readline))

    except Exception:

        return code

    for tok_type, tok_str, start, end, line in tokens:

        if tok_type == tokenize.COMMENT:

            continue

        srow, scol = start

        prow, pcol = prev_end

        if srow == prow:

            out.write(" " * max(0, scol - pcol))

        else:

            out.write("\n" * (srow - prow))

            out.write(" " * scol)

        out.write(tok_str)

        prev_end = end

    return out.getvalue()


essentials = []

for root, dirs, files in os.walk(ROOT):

    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    for fname in files:

        if not fname.endswith(".py"):

            continue

        fpath = Path(root) / fname

        if fpath.resolve() == Path(__file__).resolve():

            continue

        essentials.append(fpath)

changed = []

for f in essentials:

    try:

        original = f.read_text(encoding="utf-8")

    except Exception:

        try:

            original = f.read_text(encoding="latin-1")

        except Exception:

            continue

    updated = strip_hash_comments_from_code(original)

    if updated != original:

        try:

            f.write_text(updated, encoding="utf-8")

            changed.append(str(f))

        except Exception:

            pass

if __name__ == "__main__":

    print(f"Processed {len(essentials)} .py files. Updated {len(changed)} files.")

    for c in changed:

        print(c)
