import ssl
from urllib.request import Request, urlopen
from urllib.error import URLError
from html.parser import HTMLParser

def fetch_document(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=30, context=ssl.create_default_context()) as r:
            return r.read().decode("utf-8", errors="replace")
    except URLError:
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
            with urlopen(request, timeout=30, context=ctx) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception:
            with urlopen(request, timeout=30, context=ssl._create_unverified_context()) as r:
                return r.read().decode("utf-8", errors="replace")

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self._row = []
        self._in_td = False
    def handle_starttag(self, tag, attrs):
        if tag == "tr": self._row = []
        elif tag in ("td", "th"): self._in_td = True
    def handle_endtag(self, tag):
        if tag == "tr" and self._row: self.rows.append(self._row)
        elif tag in ("td", "th"): self._in_td = False
    def handle_data(self, data):
        if self._in_td: self._row.append(data.strip())

def main():
    url = input("Enter published Google Doc URL: ").strip()
    doc = fetch_document(url)
    parser = TableParser(); parser.feed(doc)
    rows = parser.rows
    coords = []
    for row in rows[1:] if rows and 'x' in rows[0][0].lower() else rows:
        if len(row) < 3: continue
        try:
            x = int(row[0]); y = int(row[2]); ch = row[1] if row[1] else ' '
        except Exception: continue
        coords.append((x, y, ch))
    if not coords:
        print("No valid coordinates found."); return
    max_x = max(x for x, _, _ in coords)
    max_y = max(y for _, y, _ in coords)
    grid = [[' ' for _ in range(max_x + 1)] for _ in range(max_y + 1)]
    for x, y, ch in coords:
        if 0 <= x <= max_x and 0 <= y <= max_y:
            grid[max_y - y][x] = ch[0] if ch else ' '
    for row in grid:
        print(''.join(row))

if __name__ == "__main__":
    main()
