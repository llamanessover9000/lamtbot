import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Los_Angeles")  # what "midnight" means for date reminders

UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
TOKEN_RE = re.compile(
    r"(\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|[smhdw])(?![a-z])\s*",
    re.IGNORECASE,
)

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
DATE_RE = re.compile(
    r"^([a-z]{3})[a-z]*\.?\s+(\d{1,2})(?!\d)(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?\s*(.*)$",
    re.IGNORECASE | re.DOTALL,
)

def parse_duration(text):
    pos, total = 0, 0
    while True:
        m = TOKEN_RE.match(text, pos)
        if not m:
            break
        total += int(m.group(1)) * UNIT_SECONDS[m.group(2)[0].lower()]
        pos = m.end()
    if pos == 0:
        return None
    return total, text[pos:].strip()

def parse_when(text, now):
    text = text.strip()

    result = parse_duration(text)
    if result:
        seconds, rest = result
        return now + timedelta(seconds=seconds), rest

    m = DATE_RE.match(text)
    if m and m.group(1).lower() in MONTHS:
        month = MONTHS[m.group(1).lower()]
        day = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else now.year
        try:
            when = datetime(year, month, day, tzinfo=TZ)  # midnight
        except ValueError:
            return None
        if when <= now and not m.group(3):
            when = when.replace(year=year + 1)  # "jan 20" in November means next January
        return when, m.group(4).strip()

    return None