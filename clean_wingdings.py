import os
from pathlib import Path

for root_dir in [Path("./docs"), Path("./docs_excluded")]:
    if not root_dir.exists(): continue
    for f in root_dir.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        # Replace private use Wingdings glyphs
        text = text.replace('\uf076', '- ')
        text = text.replace('\uf0b7', '- ')
        text = text.replace('\uf0d8', '- ')
        text = text.replace('\u2022', '- ')
        text = text.replace('\u2013', '-')
        text = text.replace('\u2014', '-')
        text = text.replace('\ufffd', '')
        f.write_text(text, encoding="utf-8")

print("Cleaned wingdings/private use characters.")
