#!/usr/bin/env python3
"""Create a local, dependency-free preview of the HTML-only GitHub README.

Run: python3 scripts/preview.py
Then open preview.html directly. No server, Git, API calls or uploads required.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
content = (ROOT / 'README.md').read_text()
# Don't request external statistics until the visitor expands their section.
content = re.sub(r'(<img\b[^>]*?)src="(https://[^"]+)"', r'\1data-remote-src="\2"', content)
shell = (ROOT / 'scripts' / 'preview-template.html').read_text()
output = ROOT / 'preview.html'
output.write_text(shell.replace('<!-- PROFILE_CONTENT -->', content))
print(f'Готово: {output.as_uri()}')
