import urllib.request
import re
from html.parser import HTMLParser
import os
from pathlib import Path

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

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
    html_content = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
    
    # Check container classes or ids
    containers = re.findall(r'<div[^>]+class=[\"\']([^\"\']*(?:entry-content|elementor-widget-container|post-content|main-content)[^\"\']*)[\"\'][^>]*>', html_content)
    print(f"\nURL: {name} ({u})")
    print("Found container classes:", set(containers))
    
    # Check if entry-content or elementor-widget-theme-post-content exists
    match = re.search(r'<div[^>]+class=[\"\'][^\"\']*entry-content[^\"\']*[\"\'][^>]*>(.*?)</div>', html_content, re.DOTALL | re.I)
    if match:
        print(f"  entry-content length: {len(match.group(1))} chars")
    else:
        # Check elementor main
        match_el = re.search(r'<main[^>]*>(.*?)</main>', html_content, re.DOTALL | re.I)
        if match_el:
            print(f"  <main> tag length: {len(match_el.group(1))} chars")
