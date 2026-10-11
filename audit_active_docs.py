import os
from pathlib import Path

DOCS_DIR = Path("./docs")

print("=" * 80)
print("AUDIT OF ACTIVE POLICY DOCUMENTS IN docs/")
print("=" * 80)

files = sorted(list(DOCS_DIR.glob("*.md")))
for f in files:
    content = f.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # Boilerplate detection
    boilerplate_words = ["home", "menu", "login", "contact", "copyright", "skip to content", "gallery & media"]
    boilerplate_lines = []
    for l in lines:
        stripped = l.strip()
        if not stripped or stripped.startswith("#"):
            continue
        words = stripped.split()
        if len(words) < 4 or any(w in stripped.lower() for w in boilerplate_words):
            boilerplate_lines.append(stripped)
            
    print(f"\n--- FILE: {f.name} ---")
    print(f"Character Count: {len(content)}")
    print(f"Line Count:      {len(lines)}")
    print(f"Boilerplate Line Candidates ({len(boilerplate_lines)}):")
    for bl in boilerplate_lines[:5]:
        print(f"  * {bl}")
    print("\n[FIRST 300 CHARACTERS]:")
    print(content[:300])
    print("\n[LAST 300 CHARACTERS]:")
    print(content[-300:])
    print("-" * 60)
