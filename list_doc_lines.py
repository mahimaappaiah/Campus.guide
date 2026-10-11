import os
from pathlib import Path

DOCS_DIR = Path("./docs")

for f in sorted(DOCS_DIR.glob("*.md")):
    if f.name == "SOURCES.md": continue
    print(f"\n==================== {f.name} ====================")
    lines = f.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, 1):
        if line.strip():
            print(f"{i:03d}: {line}")
