#!/usr/bin/env python3
"""Import the public GitHub contribution calendar without an API token.

Usage: python3 scripts/update-activity.py [downloaded-contributions.html]
Without a file, downloads the public calendar. Saves aggregate dates/counts
only: no email, repository names, commit messages or private repository data.
"""
from datetime import date, timedelta
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://github.com/users/PetkaKahin/contributions'


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days, self.counts = {}, {}
        self.tip, self.text = None, ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'td' and attrs.get('data-date'):
            self.days[attrs['id']] = {'date': attrs['data-date'], 'level': int(attrs['data-level'])}
        if tag == 'tool-tip' and attrs.get('for', '').startswith('contribution-day'):
            self.tip, self.text = attrs['for'], ''

    def handle_data(self, data):
        if self.tip:
            self.text += data

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tip:
            match = re.match(r'(No|[\d,]+) contributions?', self.text.strip())
            if not match:
                raise ValueError(f'Unexpected contribution tooltip: {self.text!r}')
            self.counts[self.tip] = 0 if match[1] == 'No' else int(match[1].replace(',', ''))
            self.tip = None


if len(sys.argv) > 2:
    raise SystemExit(__doc__)
if len(sys.argv) == 2:
    html = Path(sys.argv[1]).read_text()
else:
    request = Request(SOURCE, headers={'User-Agent': 'GitHub-profile-activity', 'Accept-Language': 'en-US'})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode('utf-8')

calendar = Calendar()
calendar.feed(html)
if not calendar.days or calendar.days.keys() != calendar.counts.keys():
    raise ValueError('Incomplete calendar; existing activity.json was not changed.')
days = sorted(({**day, 'count': calendar.counts[key]} for key, day in calendar.days.items()), key=lambda day: day['date'])
end = date.fromisoformat(days[-1]['date'])
start = end - timedelta(days=364)
days = [day for day in days if date.fromisoformat(day['date']) >= start]
assert len(days) == 365 and len({day['date'] for day in days}) == 365, 'Expected 365 unique calendar days'
assert all(date.fromisoformat(day['date']) == start+timedelta(days=i) for i, day in enumerate(days)), 'Calendar contains gaps'
assert all(0 <= day['level'] <= 4 and day['count'] >= 0 for day in days), 'Invalid calendar values'
output = {'source': SOURCE, 'from': days[0]['date'], 'to': days[-1]['date'], 'days': days}
(ROOT/'activity.json').write_text(json.dumps(output, indent=2, ensure_ascii=False)+'\n')
print(f'Imported {len(days)} days, {sum(day["count"] for day in days)} contributions; {days[0]["date"]} — {days[-1]["date"]}.')
