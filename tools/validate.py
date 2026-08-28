#!/usr/bin/env python3
"""Definition-of-done checks: row counts, plugin diff, anchors, banned words/emoji."""
import json
import re
import sys
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
data = json.loads((ROOT / "data" / "reference.json").read_text(encoding="utf-8"))

ok = True


def report(label, passed, detail=""):
    global ok
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail else ""))
    if not passed:
        ok = False


# 1. row counts in generated HTML
win_html = (DOCS / "windows.html").read_text(encoding="utf-8")
lin_html = (DOCS / "linux.html").read_text(encoding="utf-8")
win_rows = win_html.count('class="row"')
lin_rows = lin_html.count('class="row"')
report("windows.html row count == 96", win_rows == 96, f"found {win_rows}")
report("linux.html row count == 59", lin_rows == 59, f"found {lin_rows}")

fw_html = (DOCS / "framework.html").read_text(encoding="utf-8")
fw_rows = fw_html.count("<tr id=")
report("framework.html row count == 10", fw_rows == 10, f"found {fw_rows}")

tg_html = (DOCS / "triage.html").read_text(encoding="utf-8")
tg_rows = len(re.findall(r"<tr><td>", tg_html))
report("triage.html row count == 24", tg_rows == 24, f"found {tg_rows}")

tr_html = (DOCS / "translation.html").read_text(encoding="utf-8")
tr_rows = tr_html.count("<code>")  # 2 <code> per row (v2, v3)
# 77 workbook rows = 70 data rows + 7 section-header rows (see extract.py); both are
# asserted in extract.py against the workbook itself, so here we check the 70 data rows.
report("translation.html data row count == 70 (of 77 workbook rows, 7 are section headers)", tr_rows // 2 == 70, f"found {tr_rows // 2}")
tr_sections = len(data["translation"])
report("translation.html section count == 7", tr_sections == 7, f"found {tr_sections}")

nt_html = (DOCS / "notes.html").read_text(encoding="utf-8")
nt_rows = nt_html.count("<td><code>")
report("notes.html usage-note row count == 16", nt_rows == 16, f"found {nt_rows}")
legend_rows = nt_html.count("border-left:1rem solid")
report("notes.html legend row count == 10", legend_rows == 10, f"found {legend_rows}")

wf_html = (DOCS / "workflow.html").read_text(encoding="utf-8")
wf_rows = wf_html.count("<tr><td>")
report("workflow.html total row count == 19 (10 win + 9 linux)", wf_rows == 19, f"found {wf_rows}")


# 2. plugin diff: every plugin name from workbook appears in the rendered pages
def plugin_ids_in_page(text):
    return set(re.findall(r'<a class="plugin" href="#([^"]+)">', text))


workbook_win_plugins = {r["plugin"] for r in data["windows"]["rows"]}
workbook_lin_plugins = {r["plugin"] for r in data["linux"]["rows"]}
rendered_win = {re.sub(r"-\d+$", "", i) if i not in workbook_win_plugins else i for i in plugin_ids_in_page(win_html)}
rendered_lin = {re.sub(r"-\d+$", "", i) if i not in workbook_lin_plugins else i for i in plugin_ids_in_page(lin_html)}

# exact count-based diff: every workbook row's plugin text must appear as literal text somewhere on its page
missing_win = [p for p in workbook_win_plugins if f">{p}</a>" not in win_html]
missing_lin = [p for p in workbook_lin_plugins if f">{p}</a>" not in lin_html]
report("every windows plugin name renders on windows.html", not missing_win, f"missing: {missing_win}")
report("every linux plugin name renders on linux.html", not missing_lin, f"missing: {missing_lin}")

workbook_fw_plugins = {r["plugin"] for r in data["framework"]}
missing_fw = [p for p in workbook_fw_plugins if f">{p}</a>" not in fw_html]
report("every framework plugin name renders on framework.html", not missing_fw, f"missing: {missing_fw}")


# 3. no broken internal anchors: crawl every href="#..." / href="page.html#..." and verify target id exists
class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.hrefs.append(attrs["href"])


page_ids = {}
page_hrefs = {}
for f in DOCS.glob("*.html"):
    p = LinkParser()
    p.feed(f.read_text(encoding="utf-8"))
    page_ids[f.name] = p.ids
    page_hrefs[f.name] = p.hrefs

broken = []
for page, hrefs in page_hrefs.items():
    for href in hrefs:
        if href.startswith("http") or href.startswith("mailto:"):
            continue
        if "#" not in href:
            target_page = href
            frag = None
        else:
            target_page, frag = href.split("#", 1)
        target_page = target_page or page
        if target_page.endswith(".xlsx"):
            continue
        if target_page not in page_ids:
            broken.append((page, href, "unknown page"))
            continue
        if frag and frag not in page_ids[target_page]:
            broken.append((page, href, "missing id"))

report("no broken internal anchors", not broken, f"{len(broken)} broken: {broken[:10]}")


# 4. banned words + emoji
BANNED_WORDS = [
    "comprehensive", "powerful", "seamless", "one-stop", "dive in", "unlock", "elevate",
    "built with ❤", "built with love", "powered by",
]
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001F0FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "]"
)

banned_hits = []
emoji_hits = []
for f in list(DOCS.glob("*.html")) + [DOCS / "style.css", DOCS / "script.js"]:
    text = f.read_text(encoding="utf-8")
    low = text.lower()
    for w in BANNED_WORDS:
        if w in low:
            banned_hits.append((f.name, w))
    for m in EMOJI_RE.finditer(text):
        emoji_hits.append((f.name, m.group()))

report("zero banned marketing words", not banned_hits, f"{banned_hits}")
report("zero emoji", not emoji_hits, f"{emoji_hits}")

print()
sys.exit(0 if ok else 1)
