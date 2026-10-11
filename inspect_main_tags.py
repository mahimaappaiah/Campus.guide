import urllib.request
import re
import html
from html.parser import HTMLParser

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

class MainTagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.main_depth = 0
        self.text_parts = []
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
                self.text_parts.append(f"\n\n{'#' * int(tag[1])} ")
            elif tag in ['p', 'div', 'tr']:
                self.text_parts.append("\n")
            elif tag == 'li':
                self.text_parts.append("\n- ")
            elif tag in ['td', 'th']:
                self.text_parts.append(" | ")

    def handle_endtag(self, tag):
        if tag in self.ignore_tags:
            self.ignore_depth = max(0, self.ignore_depth - 1)
            
        if self.in_main:
            if self.ignore_depth == 0 and tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'tr']:
                self.text_parts.append("\n")
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
                self.text_parts.append(t + " ")

urls = {
    "hostel": "https://mccblr.edu.in/infrastructure/hostel/",
    "results_revaluation": "https://mccblr.edu.in/examination-centre/results-revaluation/",
    "library": "https://mccblr.edu.in/infrastructure/library/",
    "attendance": "https://mccblr.edu.in/examination-centre/attendance/",
    "cia": "https://mccblr.edu.in/examination-centre/cia/",
    "ese": "https://mccblr.edu.in/examination-centre/ese/",
    "promotion": "https://mccblr.edu.in/examination-centre/promotion-awards/"
}

for name, u in urls.items():
    req = urllib.request.Request(u, headers=headers)
    raw = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
    parser = MainTagParser()
    parser.feed(raw)
    extracted = "".join(parser.text_parts)
    extracted = re.sub(r'[ \t]+', ' ', extracted)
    extracted = re.sub(r'\n\s*\n\s*\n+', '\n\n', extracted).strip()
    
    lines = [l.strip() for l in extracted.splitlines() if l.strip()]
    print(f"\n==================== {name} ({len(extracted)} chars, {len(lines)} lines) ====================")
    print("\n".join(lines[:15]))
    if len(lines) > 15:
        print("...")
        print("\n".join(lines[-5:]))
