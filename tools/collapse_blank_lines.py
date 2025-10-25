from pathlib import Path
import re

def collapse_blank_lines(text: str) -> str:
    # Normalize Windows line endings
    text = text.replace('\r\n', '\n')
    # Strip trailing whitespace on each line
    lines = [re.sub(r'[\t ]+$', '', line) for line in text.split('\n')]
    text = '\n'.join(lines)
    # Collapse 3+ consecutive newlines to a single blank line
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

if __name__ == '__main__':
    p = Path(r'd:\code\mc\main.py')
    src = p.read_text(encoding='utf-8')
    out = collapse_blank_lines(src)
    if out != src:
        p.write_text(out, encoding='utf-8')
        print('Updated main.py (collapsed blank lines).')
    else:
        print('No changes needed.')
