"""
verify_corpus.py - Complete automated verification script for the RAG portfolio corpus.

Outputs raw data and verification metrics to console and writes verification_report.txt.
"""

import os
import sys
import io
import re
import urllib.request
import subprocess
from pathlib import Path
import pypdf

# Ensure clean UTF-8 console output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
REPORT_PATH = BASE_DIR / "verification_report.txt"

PDF_SOURCES = {
    "code_of_conduct.md": "https://mccblr.edu.in/wp-content/uploads/2026/08/Code-of-Conduct-Students-2026-27.pdf",
    "grievance_redressal_policy.md": "https://mccblr.edu.in/wp-content/uploads/2026/01/Grievance-Policy-2024.pdf",
    "anti_drug_policy.md": "https://mccblr.edu.in/wp-content/uploads/2026/01/Anti-Drug-Cell.pdf"
}

WEB_SOURCES = {
    "attendance_regulations.md": ("https://mccblr.edu.in/examination-centre/attendance/", "# Attendance"),
    "continuous_internal_assessment.md": ("https://mccblr.edu.in/examination-centre/cia/", "# Continuous Internal Assessment"),
    "end_semester_examinations.md": ("https://mccblr.edu.in/examination-centre/ese/", "# End Semester Examination"),
    "results_and_revaluation.md": ("https://mccblr.edu.in/examination-centre/results-revaluation/", "# Results & Revaluation"),
    "promotion_and_awards.md": ("https://mccblr.edu.in/examination-centre/promotion-awards/", "# Promotion & Awards"),
    "library_guidelines.md": ("https://mccblr.edu.in/infrastructure/library/", "# Library"),
    "hostel_regulations.md": ("https://mccblr.edu.in/infrastructure/hostel/", "# Mother Mary Memorial Hostel")
}


def run_verification():
    output = []
    
    def log(msg=""):
        output.append(str(msg))
        try:
            print(msg)
        except Exception:
            print(str(msg).encode('ascii', errors='backslashreplace').decode('ascii'))

    log("=" * 80)
    log("MOUNT CARMEL COLLEGE RAG CORPUS VERIFICATION REPORT")
    log("=" * 80)

    # --------------------------------------------------------------------------
    # 1. FILE METRICS & PEEK (EVERY FILE IN docs/ INCLUDING SOURCES.md)
    # --------------------------------------------------------------------------
    all_files = sorted(list(DOCS_DIR.glob("*.md")) + list(DOCS_DIR.glob("*.txt")))
    
    log("\n" + "#" * 80)
    log("SECTION 1: DOCUMENT METRICS, PREVIEWS, AND BOILERPLATE ANALYSIS")
    log("#" * 80)

    for doc_file in all_files:
        filename = doc_file.name
        content = doc_file.read_text(encoding="utf-8")
        char_count = len(content)
        lines = content.splitlines()
        line_count = len(lines)
        
        first_400 = content[:400]
        last_400 = content[-400:] if len(content) >= 400 else content

        # Boilerplate check: lines < 4 words or containing common web navigation words
        boilerplate_keywords = ["home", "menu", "login", "contact", "copyright", "skip to content", "gallery & media"]
        boilerplate_lines = []
        for l in lines:
            stripped = l.strip()
            if not stripped or stripped.startswith("#"):
                continue
            words = stripped.split()
            if len(words) < 4 or any(kw in stripped.lower() for kw in boilerplate_keywords):
                boilerplate_lines.append(stripped)

        log(f"\n--- FILE: {filename} ---")
        log(f"Character Count: {char_count}")
        log(f"Line Count:      {line_count}")
        log(f"Boilerplate Line Candidates (count: {len(boilerplate_lines)}):")
        for bl in boilerplate_lines[:10]:
            log(f"  * {bl}")

        log("\n[FIRST 400 CHARACTERS]:")
        log(first_400)
        log("\n[LAST 400 CHARACTERS]:")
        log(last_400)
        log("-" * 60)

    # --------------------------------------------------------------------------
    # 2. PDF PAGE EXTRACTION AUDIT
    # --------------------------------------------------------------------------
    log("\n" + "#" * 80)
    log("SECTION 2: PDF-SOURCED DOCUMENTS PAGE COUNT AUDIT")
    log("#" * 80)

    headers = {'User-Agent': 'Mozilla/5.0'}
    for doc_name, pdf_url in PDF_SOURCES.items():
        try:
            req = urllib.request.Request(pdf_url, headers=headers)
            pdf_bytes = urllib.request.urlopen(req, timeout=20).read()
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            total_pages = len(reader.pages)
            pages_with_text = 0
            for p in reader.pages:
                t = p.extract_text() or ""
                if t.strip():
                    pages_with_text += 1
            log(f"File: {doc_name:<35} | Total PDF Pages: {total_pages} | Pages with Text: {pages_with_text} | URL: {pdf_url}")
        except Exception as e:
            log(f"File: {doc_name:<35} | ERROR checking PDF: {e}")

    # --------------------------------------------------------------------------
    # 3. KEY NUMERICAL STRINGS AUDIT ("75%", "80%", "40%", "25%", "5 working days")
    # --------------------------------------------------------------------------
    log("\n" + "#" * 80)
    log("SECTION 3: KEY NUMERICAL STRINGS AUDIT IN docs/*.md")
    log("#" * 80)

    target_strings = ["75%", "80%", "40%", "25%", "5 working days"]
    matches_found = []

    for doc_file in sorted(DOCS_DIR.glob("*.md")):
        if doc_file.name == "SOURCES.md":
            continue
        lines = doc_file.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            for ts in target_strings:
                if ts.lower() in line.lower():
                    matches_found.append((doc_file.name, idx, ts, line.strip()))

    log(f"Total Matches Found: {len(matches_found)}")
    for filename, line_no, target, text in matches_found:
        log(f"[{filename}:{line_no}] (Matched '{target}'): {text}")

    # --------------------------------------------------------------------------
    # 4. LIVE WEB PAGE RE-FETCH AND CHARACTER COUNT COMPARISON
    # --------------------------------------------------------------------------
    log("\n" + "#" * 80)
    log("SECTION 4: LIVE WEB PAGE RE-FETCH & CHARACTER COMPARISON")
    log("#" * 80)

    from html.parser import HTMLParser
    class SimpleParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.lines = []
            self.ignore = False
        def handle_starttag(self, tag, attrs):
            if tag in ['script', 'style', 'nav', 'header', 'footer', 'noscript', 'svg']:
                self.ignore = True
            elif tag in ['p', 'div', 'tr', 'h1', 'h2', 'h3', 'h4', 'li']:
                self.lines.append("\n")
        def handle_endtag(self, tag):
            if tag in ['script', 'style', 'nav', 'header', 'footer', 'noscript', 'svg']:
                self.ignore = False
        def handle_data(self, data):
            if not self.ignore:
                s = data.strip()
                if s:
                    self.lines.append(s + " ")

    for doc_name, (web_url, start_kw) in WEB_SOURCES.items():
        try:
            req = urllib.request.Request(web_url, headers=headers)
            raw_html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
            parser = SimpleParser()
            parser.feed(raw_html)
            text = "".join(parser.lines)
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            idx = text.find(start_kw)
            if idx != -1:
                text = text[idx:]
            
            saved_content = (DOCS_DIR / doc_name).read_text(encoding="utf-8")
            live_len = len(text.strip())
            saved_len = len(saved_content.strip())
            
            log(f"\n--- Web Source: {doc_name} ---")
            log(f"Live URL:             {web_url}")
            log(f"Live Clean Content Len: {live_len} chars")
            log(f"Saved File Char Len:    {saved_len} chars")
            log(f"First 300 Chars of Live Extracted Content:")
            log(text.strip()[:300])
        except Exception as e:
            log(f"\n--- Web Source: {doc_name} --- ERROR: {e}")

    # --------------------------------------------------------------------------
    # 5. PRINT .gitignore, requirements.txt, AND DIRECTORY LISTING
    # --------------------------------------------------------------------------
    log("\n" + "#" * 80)
    log("SECTION 5: PROJECT CONFIGURATION & DIRECTORY LISTING")
    log("#" * 80)

    log("\n[.gitignore CONTENTS]:")
    gitignore_path = BASE_DIR / ".gitignore"
    log(gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else "FILE NOT FOUND")

    log("\n[requirements.txt CONTENTS]:")
    req_path = BASE_DIR / "requirements.txt"
    log(req_path.read_text(encoding="utf-8") if req_path.exists() else "FILE NOT FOUND")

    log("\n[docs/ DIRECTORY LISTING & SIZES]:")
    for f in sorted(DOCS_DIR.glob("*")):
        log(f"{f.name:<40} | {f.stat().st_size:>8} bytes | {len(f.read_text(encoding='utf-8')):>8} chars")

    # --------------------------------------------------------------------------
    # 6. CONFIRM LOADER SKIPS SOURCES.MD AND README FILES
    # --------------------------------------------------------------------------
    log("\n" + "#" * 80)
    log("SECTION 6: INGEST.PY LOADER FILTER VERIFICATION")
    log("#" * 80)
    
    ingest_code = (BASE_DIR / "ingest.py").read_text(encoding="utf-8")
    lines = ingest_code.splitlines()
    filter_block = []
    for i, l in enumerate(lines, start=1):
        if "sources.md" in l.lower() or "readme" in l.lower():
            filter_block.append((i, l))

    log("Exact code lines in ingest.py filtering out SOURCES.md and README files:")
    for line_no, code_line in filter_block:
        log(f"  Line {line_no:02d}: {code_line}")

    # --------------------------------------------------------------------------
    # 7. RUN PYTEST
    # --------------------------------------------------------------------------
    log("\n" + "#" * 80)
    log("SECTION 7: PYTEST TEST SUITE EXECUTION")
    log("#" * 80)

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True
        )
        log(proc.stdout)
        if proc.stderr:
            log("[STDERR]:\n" + proc.stderr)
    except Exception as e:
        log(f"Pytest run error: {e}")

    # --------------------------------------------------------------------------
    # 8. RUN INGEST.PY
    # --------------------------------------------------------------------------
    log("\n" + "#" * 80)
    log("SECTION 8: INGEST.PY EXECUTION")
    log("#" * 80)

    try:
        proc = subprocess.run(
            [sys.executable, "ingest.py"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True
        )
        log(proc.stdout)
        if proc.stderr:
            log("[STDERR]:\n" + proc.stderr)
    except Exception as e:
        log(f"Ingest run error: {e}")

    # --------------------------------------------------------------------------
    # 9. RUN ASK.PY ON THE 3 MANDATORY TEST QUESTIONS
    # --------------------------------------------------------------------------
    log("\n" + "#" * 80)
    log("SECTION 9: SAMPLE TEST QUESTIONS EXECUTION (ask.py)")
    log("#" * 80)

    test_queries = [
        "What is the minimum attendance required to appear for exams?",
        "What is the dress code policy?",
        "What is the capital of France?"
    ]

    from ask import answer_query

    for q in test_queries:
        log(f"\n>>> QUESTION: {q}")
        res = answer_query(q)
        log(f"\n[FULL ANSWER]:\n{res['answer']}")
        log("\n[RETRIEVED CHUNKS & SOURCES]:")
        for idx, chunk in enumerate(res.get("retrieved_chunks", []), start=1):
            src = chunk.get("source", "unknown")
            snippet = chunk.get("content", "")[:200].replace("\n", " ").strip()
            log(f"  Chunk {idx} [Source: {src}] -> First 200 chars: {snippet}")
        log("-" * 60)

    # Save to verification_report.txt
    full_report_text = "\n".join(output)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(full_report_text)
    
    print(f"\nVerification report written to: {REPORT_PATH}")


if __name__ == "__main__":
    run_verification()
