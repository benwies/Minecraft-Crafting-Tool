from pathlib import Path

p = Path("d:\\code\\mc\\test_calc.py")

b = p.read_bytes()

print("Bytes:", b)

print("Has tab?", 9 in b)

print("Has CR?", 13 in b)

print("Has non-breaking space?", 160 in b)

print("Lines and leading bytes:")

for i, line in enumerate(b.splitlines(True), 1):

    prefix = []

    for ch in line[:8]:

        prefix.append(ch)

    print(i, prefix, line.rstrip())
