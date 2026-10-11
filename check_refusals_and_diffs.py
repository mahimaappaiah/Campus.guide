import sys
from pathlib import Path

# 1. Q14 inspection
print("=== Q14 PDF EXTRACTION AROUND EMAIL (grievance_redressal_policy.md) ===")
lines = Path("docs/grievance_redressal_policy.md").read_text(encoding="utf-8").splitlines()
for i in range(45, 60):
    if i < len(lines):
        print(f"{i+1:03d}: {lines[i]}")

print("\nOCR Artifact Note on grievance_redressal_policy.md:")
print("- Page 1 header shows 'mails@mccbir.edu.in' ('bir' instead of 'blr' due to glyph OCR scanning).")
print("- Page 1 body mentions '1CC' instead of 'ICC'.")
print("- Page 2 contact listing correctly extracts: '1. Students Grievance Redressal Committee: grievancestudents@mccblr.edu.in'")

# 2. Grep for replacement refusal terms
print("\n=== GREP FOR ADVERSARIAL REFUSAL TERMS IN docs/ ===")
terms = ["refund", "cancellation", "swimming", "gym", "pool", "tuition fee", "hostel mess", "borrow"]
for term in terms:
    matches = []
    for f in sorted(Path("docs").glob("*.md")):
        if f.name == "SOURCES.md": continue
        flines = f.read_text(encoding="utf-8").splitlines()
        for idx, l in enumerate(flines, 1):
            if term in l.lower():
                matches.append((f.name, idx, l.strip()))
    print(f"Grep for '{term}': {len(matches)} matches found.")
    for m in matches:
        print(f"  [{m[0]}:{m[1]}] {m[2]}")
