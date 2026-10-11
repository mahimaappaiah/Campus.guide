"""
rebuild_corpus_strict.py - Deterministic, verbatim extraction of official Mount Carmel College policies.

Extracts main content using strict HTML <main> container parsing and verbatim PDF text extraction.
Moves excluded documents to docs_excluded/ and updates SOURCES.md and .gitignore.
"""

import os
import io
import re
import urllib.request
import html
from html.parser import HTMLParser
from pathlib import Path
import pypdf

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
EXCLUDED_DIR = BASE_DIR / "docs_excluded"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
EXCLUDED_DIR.mkdir(parents=True, exist_ok=True)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}


def extract_pdf_verbatim(url: str) -> tuple[str, int, int]:
    req = urllib.request.Request(url, headers=headers)
    data = urllib.request.urlopen(req, timeout=30).read()
    reader = pypdf.PdfReader(io.BytesIO(data))
    total_pages = len(reader.pages)
    pages_with_text = 0
    text_chunks = []
    
    for i, page in enumerate(reader.pages):
        t = page.extract_text() or ""
        t = t.replace('\uf0b7', '- ').replace('\uf0d8', '- ').replace('\u2022', '- ')
        t = t.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
        t = t.replace('\ufffd', '')
        if t.strip():
            pages_with_text += 1
            text_chunks.append(f"### Section / Page {i+1}\n\n{t.strip()}")
            
    return "\n\n".join(text_chunks), total_pages, pages_with_text


class StrictMainParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.main_depth = 0
        self.tokens = []
        self.ignore_tags = {'script', 'style', 'noscript', 'svg', 'iframe'}
        self.ignore_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.in_main = True
            self.main_depth += 1
        elif self.in_main:
            self.main_depth += 1
            
        if tag in self.ignore_tags:
            self.ignore_depth += 1
            
        if self.in_main and self.ignore_depth == 0:
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                self.tokens.append(f"\n\n{'#' * int(tag[1])} ")
            elif tag in ['p', 'div', 'tr']:
                self.tokens.append("\n")
            elif tag == 'li':
                self.tokens.append("\n- ")
            elif tag in ['td', 'th']:
                self.tokens.append(" | ")

    def handle_endtag(self, tag):
        if tag in self.ignore_tags:
            self.ignore_depth = max(0, self.ignore_depth - 1)
            
        if self.in_main:
            if self.ignore_depth == 0 and tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'tr']:
                self.tokens.append("\n")
            if tag == 'main':
                self.main_depth -= 1
                if self.main_depth <= 0:
                    self.in_main = False
            else:
                self.main_depth -= 1

    def handle_data(self, data):
        if self.in_main and self.ignore_depth == 0:
            t = html.unescape(data).strip()
            if t:
                self.tokens.append(t + " ")


def extract_web_main_verbatim(url: str) -> str:
    req = urllib.request.Request(url, headers=headers)
    raw = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', errors='ignore')
    parser = StrictMainParser()
    parser.feed(raw)
    raw_text = "".join(parser.tokens)
    raw_text = re.sub(r'[ \t]+', ' ', raw_text)
    raw_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', raw_text).strip()
    
    # Clean special characters without touching markdown headings
    raw_text = raw_text.replace('\uf0b7', '- ').replace('\uf0d8', '- ').replace('\u2022', '- ')
    raw_text = raw_text.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    
    lines = [l.strip() for l in raw_text.splitlines() if l.strip() and l.strip() != '-']
    return "\n\n".join(lines)


# ------------------------------------------------------------------------------
# 1. INCLUDED POLICY DOCUMENTS
# ------------------------------------------------------------------------------
INCLUDED_DOCS = [
    {
        "filename": "code_of_conduct.md",
        "title": "Mount Carmel College - Student Code of Conduct and Dress Code Guidelines",
        "type": "PDF",
        "url": "https://mccblr.edu.in/wp-content/uploads/2026/08/Code-of-Conduct-Students-2026-27.pdf"
    },
    {
        "filename": "grievance_redressal_policy.md",
        "title": "Mount Carmel College - Grievance Redressal Mechanism Policy",
        "type": "PDF",
        "url": "https://mccblr.edu.in/wp-content/uploads/2026/01/Grievance-Policy-2024.pdf"
    },
    {
        "filename": "attendance_regulations.md",
        "title": "Mount Carmel College - Attendance Policy and Examination Eligibility",
        "type": "WEB",
        "url": "https://mccblr.edu.in/examination-centre/attendance/"
    },
    {
        "filename": "continuous_internal_assessment.md",
        "title": "Mount Carmel College - Continuous Internal Assessment (CIA) Regulations",
        "type": "WEB",
        "url": "https://mccblr.edu.in/examination-centre/cia/"
    },
    {
        "filename": "end_semester_examinations.md",
        "title": "Mount Carmel College - End Semester Examination (ESE) Regulations and Minimum Pass Marks",
        "type": "WEB",
        "url": "https://mccblr.edu.in/examination-centre/ese/"
    },
    {
        "filename": "results_and_revaluation.md",
        "title": "Mount Carmel College - Results, Photocopy, Revaluation & Challenge Valuation Rules",
        "type": "WEB",
        "url": "https://mccblr.edu.in/examination-centre/results-revaluation/"
    },
    {
        "filename": "promotion_and_awards.md",
        "title": "Mount Carmel College - Academic Promotion Criteria and Graduation Awards",
        "type": "WEB",
        "url": "https://mccblr.edu.in/examination-centre/promotion-awards/"
    }
]

# ------------------------------------------------------------------------------
# 2. EXCLUDED DOCUMENTS
# ------------------------------------------------------------------------------
EXCLUDED_DOCS = [
    {
        "filename": "anti_drug_policy.md",
        "title": "Mount Carmel College - Anti-Drug and Substance Abuse Policy",
        "type": "PDF",
        "url": "https://mccblr.edu.in/wp-content/uploads/2026/01/Anti-Drug-Cell.pdf",
        "reason": "Only 2 of 6 PDF pages contain extractable text; remaining pages are raster images."
    },
    {
        "filename": "hostel_regulations.md",
        "title": "Mount Carmel College - Mother Mary Memorial Hostel Disclaimer",
        "type": "WEB",
        "url": "https://mccblr.edu.in/infrastructure/hostel/",
        "reason": "Public webpage only contains a 3-line disclaimer on third-party accommodations and an apply link, without substantive rules."
    },
    {
        "filename": "library_guidelines.md",
        "title": "Mount Carmel College - Library Information & Collections",
        "type": "WEB",
        "url": "https://mccblr.edu.in/infrastructure/library/",
        "reason": "Public webpage contains inventory counts, e-resource catalogs, and staff names, without borrowing limits, loan durations, or fine rules."
    }
]


def rebuild():
    # Clear out any stale files in docs/
    for existing in DOCS_DIR.glob("*.md"):
        existing.unlink()

    sources_table = [
        "# Official Document Sources\n",
        "All active policy documents in `docs/` are verbatim text extracted directly from official, publicly accessible pages and PDFs published by **Mount Carmel College (Autonomous), Bengaluru** (`mccblr.edu.in`).\n",
        "| # | Document Filename | Official Title | Source Type | Official Public URL | Retrieval Date |",
        "|---|-------------------|----------------|-------------|---------------------|----------------|"
    ]

    for idx, doc in enumerate(INCLUDED_DOCS, start=1):
        print(f"Extracting active doc [{idx}/{len(INCLUDED_DOCS)}]: {doc['filename']}...")
        if doc['type'] == 'PDF':
            body, total_p, text_p = extract_pdf_verbatim(doc['url'])
        else:
            body = extract_web_main_verbatim(doc['url'])
            
        content = f"# {doc['title']}\n\n**Source URL:** {doc['url']}\n**Retrieval Date:** 2026-10-10\n\n{body}\n"
        (DOCS_DIR / doc['filename']).write_text(content, encoding="utf-8")
        sources_table.append(f"| {idx} | `{doc['filename']}` | {doc['title']} | {doc['type']} | [{doc['url']}]({doc['url']}) | 2026-10-10 |")

    # Write clean SOURCES.md without any summary claims
    (DOCS_DIR / "SOURCES.md").write_text("\n".join(sources_table) + "\n", encoding="utf-8")

    # Process and write excluded docs
    for idx, doc in enumerate(EXCLUDED_DOCS, start=1):
        print(f"Extracting excluded doc [{idx}/{len(EXCLUDED_DOCS)}]: {doc['filename']}...")
        if doc['type'] == 'PDF':
            body, total_p, text_p = extract_pdf_verbatim(doc['url'])
        else:
            body = extract_web_main_verbatim(doc['url'])
            
        content = (
            f"# [EXCLUDED] {doc['title']}\n\n"
            f"**Source URL:** {doc['url']}\n"
            f"**Retrieval Date:** 2026-10-10\n"
            f"**Reason for Exclusion:** {doc['reason']}\n\n"
            f"{body}\n"
        )
        (EXCLUDED_DIR / doc['filename']).write_text(content, encoding="utf-8")

    # Update .gitignore
    gitignore_content = """# Python bytecode & cache
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/

# Environment and secrets
.env
.venv/
env/
venv/

# Vector database storage
chroma_db/
*.db
*.sqlite3

# Document corpus (downloadable via rebuild_corpus_strict.py)
docs/*.md
!docs/SOURCES.md
docs_excluded/

# IDE / OS specific
.idea/
.vscode/
.DS_Store
Thumbs.db
"""
    (BASE_DIR / ".gitignore").write_text(gitignore_content, encoding="utf-8")
    print("\nRebuild complete.")


if __name__ == "__main__":
    rebuild()
