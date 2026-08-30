#!/usr/bin/env python3
"""Read data/reference.json, write static HTML into docs/.

No templating framework -- small f-string helpers. Every page shares the
same shell (skip link, mobile topbar, desktop phase spine, footer) so the
only real work per page is the content block.
"""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "data" / "reference.json"
DOCS = ROOT / "docs"

VERIFIED_VERSION = "2.28"
VERIFIED_DATE = "2026-08-28"
CREDIT_NAME = "Mousa Mohamed"
REPO_URL = "https://github.com/theonlymosmos/Mousa-Analyzing-Memory"
XLSX_NAME = "Volatility3_Memory_Analysis_Reference.xlsx"

PAGES = [
    ("index.html", "Overview"),
    ("windows.html", "Windows"),
    ("linux.html", "Linux"),
    ("workflow.html", "Workflow"),
    ("framework.html", "Framework"),
    ("triage.html", "Triage"),
    ("translation.html", "Vol2 -> Vol3"),
    ("notes.html", "Notes & legend"),
]

_seen_ids_per_page = {}


def esc(s):
    return html.escape(str(s), quote=True)


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text


def unique_id(page, base):
    seen = _seen_ids_per_page.setdefault(page, {})
    n = seen.get(base, 0) + 1
    seen[base] = n
    return base if n == 1 else f"{base}-{n}"


def page_nav(active_page):
    items = []
    for href, label in PAGES:
        current = ' aria-current="page"' if href == active_page else ""
        items.append(f'<a href="{href}"{current}>{esc(label)}</a>')
    return "\n      ".join(items)


def page_select(active_page):
    opts = []
    for href, label in PAGES:
        selected = " selected" if href == active_page else ""
        opts.append(f'<option value="{href}"{selected}>{esc(label)}</option>')
    return "\n        ".join(opts)


def phase_spine(phases, active_page):
    if not phases:
        return ""
    items = []
    for p in phases:
        slug = slugify(p["name"])
        items.append(f'<li><a href="#{slug}">{esc(p["name"])}</a></li>')
    return f'<ul class="phase-list">\n        {"".join(items)}\n      </ul>'


def render_shell(title, dek_html, body_html, active_page, phases=None):
    spine_phases = phase_spine(phases, active_page) if phases else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Volatility 3 reference</title>
<meta name="description" content="{esc(dek_html)}">
<link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>

<header class="topbar">
  <a class="brand" href="index.html">vol3-reference</a>
  <select id="page-select" aria-label="Go to page">
        {page_select(active_page)}
  </select>
</header>

<div class="shell">
  <aside class="spine">
    <a class="brand" href="index.html">vol3-reference</a>
    <span class="subbrand">Volatility 3 · verified v{VERIFIED_VERSION}</span>
    <nav class="pages" aria-label="Sections">
      {page_nav(active_page)}
    </nav>
    {spine_phases}
  </aside>

  <main id="main">
    <h1>{esc(title)}</h1>
    <p class="dek">{dek_html}</p>
    {body_html}
    <footer class="page-footer">
      <p>Reference content verified against Volatility 3 stable v{VERIFIED_VERSION} ({VERIFIED_DATE}), CC BY 4.0, {esc(CREDIT_NAME)}.
      Not affiliated with or endorsed by the Volatility Foundation. Source: <a href="{esc(XLSX_NAME)}">{esc(XLSX_NAME)}</a> ·
      <a href="{REPO_URL}">{REPO_URL.replace('https://', '')}</a></p>
    </footer>
  </main>
</div>

<script src="script.js"></script>
</body>
</html>
"""


def command_block(page, base_id, command):
    cmd_id = f"cmd-{unique_id(page, 'cmd-' + slugify(command))}"
    return (
        f'<div class="cmd-wrap">'
        f'<code class="command" id="{cmd_id}">{esc(command)}</code>'
        f'<button class="copy-btn" type="button" data-copy-target="{cmd_id}">Copy</button>'
        f"</div>"
    )


def classification_row(page, row):
    plugin = row["plugin"]
    row_id = unique_id(page, plugin)
    phase_key = slugify(row["phase"])
    return f"""<div class="row" id="{esc(row_id)}" data-phase-key="{esc(phase_key)}">
        <div class="step">{row['step']:02d}</div>
        <div class="col-main">
          <a class="plugin" href="#{esc(row_id)}">{esc(plugin)}</a>
          <p class="purpose">{esc(row['purpose'])}</p>
          <p class="desc">{esc(row['description'])}</p>
        </div>
        {command_block(page, row_id, row['command'])}
      </div>"""


def build_classification_page(page, section, os_label):
    phases = section["phases"]
    rows_by_phase = {}
    for row in section["rows"]:
        rows_by_phase.setdefault(row["phase"], []).append(row)

    toggles = "\n      ".join(
        f'<button class="phase-toggle" type="button" aria-pressed="false" '
        f'data-phase="{slugify(p["name"])}">{esc(p["name"])}</button>'
        for p in phases
    )

    sections_html = []
    for p in phases:
        slug = slugify(p["name"])
        rows = rows_by_phase.get(p["name"], [])
        rows_html = "\n      ".join(classification_row(page, r) for r in rows)
        sections_html.append(
            f"""<section class="phase-section" id="{slug}">
      <h2>{esc(p['name'])} <span class="phase-count">{len(rows)} plugins</span></h2>
      <div class="rows">
      {rows_html}
      </div>
    </section>"""
        )

    body = f"""<div class="filter-bar">
      <div class="filter-row">
        <input id="filter-input" type="text" placeholder="Filter {os_label} plugins ( / to focus, Esc to clear )" autocomplete="off">
        <span id="filter-count"></span>
      </div>
      <div class="phase-toggles" role="group" aria-label="Filter by phase">
      {toggles}
      </div>
    </div>
    {"".join(sections_html)}"""

    dek = (
        f"All {len(section['rows'])} {os_label} plugins from the workbook, grouped by the "
        f"{len(phases)}-phase analysis workflow, with a runnable example command for each."
    )
    return render_shell(f"{os_label} plugins", dek, body, page, phases=phases)


def build_index(data):
    win_count = len(data["windows"]["rows"])
    lin_count = len(data["linux"]["rows"])
    fw_count = len(data["framework"])
    tr_count = sum(len(s["rows"]) for s in data["translation"])
    tg_count = len(data["triage"])

    links = [
        ("windows.html", "Windows plugins", f"{win_count} plugins across {len(data['windows']['phases'])} phases"),
        ("linux.html", "Linux plugins", f"{lin_count} plugins across {len(data['linux']['phases'])} phases"),
        ("workflow.html", "Workflow summary", "Windows and Linux analysis sequence, phase by phase"),
        ("framework.html", "Framework plugins", f"{fw_count} OS-independent plugins"),
        ("triage.html", "Triage & gotchas", f"{tg_count} indicators, false positives, and pitfalls"),
        ("translation.html", "Vol2 -> Vol3 translation", f"{tr_count} command mappings across 7 areas"),
        ("notes.html", "Usage notes & legend", "Syntax, flags, and the phase colour legend"),
    ]
    links_html = "\n      ".join(
        f'<li><a href="{href}"><span class="link-title">{esc(title)}</span>'
        f'<span class="link-desc">{esc(desc)}</span></a></li>'
        for href, title, desc in links
    )

    body = f"""<p>This is a Volatility 3 plugin reference built from a working memory-forensics
    workflow: {win_count} Windows plugins and {lin_count} Linux plugins, mapped to the analysis phase
    each one belongs to, with the flags and an example command for each.</p>

    <div class="verify-box">
      <p><strong>Verified against Volatility 3 stable v{VERIFIED_VERSION}</strong> ({VERIFIED_DATE}).
      Every plugin name and flag in this reference was checked by running <code>vol.py &lt;plugin&gt; -h</code>
      against that release. Plugin sets change between versions -- check your own <code>vol -h</code> output
      if something here does not match what you have installed.</p>
    </div>

    <h2>Get Volatility 3 running</h2>
    <div class="cmd-wrap"><code class="command" id="cmd-install">pip install volatility3</code>
    <button class="copy-btn" type="button" data-copy-target="cmd-install">Copy</button></div>
    <div class="cmd-wrap"><code class="command" id="cmd-run">vol -f memory.raw windows.info</code>
    <button class="copy-btn" type="button" data-copy-target="cmd-run">Copy</button></div>
    <p>See <a href="notes.html">usage notes &amp; legend</a> for symbol tables, output formats,
    and the rest of the flags that apply across every plugin.</p>

    <h2>Where to go</h2>
    <ul class="index-links">
      {links_html}
    </ul>

    <h2>Source</h2>
    <p>Every row on this site comes from <a href="{esc(XLSX_NAME)}">{esc(XLSX_NAME)}</a>, kept in the
    repository root. The spreadsheet is the source of truth -- download it directly if you want the
    raw data.</p>"""

    dek = "A Volatility 3 plugin reference for memory forensics, verified against a real install."
    return render_shell("Volatility 3 memory analysis reference", dek, body, "index.html")


def build_workflow(data):
    def table(rows, caption):
        body_rows = []
        for r in rows:
            plugins = ", ".join(f"<code>{esc(p)}</code>" for p in r["plugins"])
            body_rows.append(
                f"<tr><td>{esc(r['phase_num'])}</td><td>{esc(r['stage'])}</td>"
                f"<td>{plugins}</td><td>{esc(r['objectives'])}</td></tr>"
            )
        return f"""<table>
      <caption>{esc(caption)}</caption>
      <thead><tr><th>Phase</th><th>Stage</th><th>Associated plugins</th><th>Key objectives</th></tr></thead>
      <tbody>
      {"".join(body_rows)}
      </tbody>
    </table>"""

    body = f"""<h2 id="windows-workflow">Windows workflow</h2>
    {table(data['windows_workflow'], f"{len(data['windows_workflow'])} phases")}
    <h2 id="linux-workflow">Linux workflow</h2>
    {table(data['linux_workflow'], f"{len(data['linux_workflow'])} phases")}"""

    dek = "The recommended execution sequence for Windows and Linux memory images, phase by phase."
    return render_shell("Analysis workflow", dek, body, "workflow.html")


def build_framework(data):
    rows = []
    for r in data["framework"]:
        row_id = unique_id("framework.html", r["plugin"])
        rows.append(
            f"""<tr id="{esc(row_id)}">
        <td><a class="plugin" href="#{esc(row_id)}">{esc(r['plugin'])}</a></td>
        <td>{esc(r['applies_to'])}</td>
        <td>{esc(r['description'])}</td>
        <td>{command_block('framework.html', row_id, r['command'])}</td>
      </tr>"""
        )
    body = f"""<table>
      <thead><tr><th>Plugin</th><th>Applies to</th><th>Description</th><th>Command</th></tr></thead>
      <tbody>
      {"".join(rows)}
      </tbody>
    </table>"""
    dek = f"{len(data['framework'])} plugins that work against any image type, regardless of OS."
    return render_shell("Framework & cross-OS plugins", dek, body, "framework.html")


def build_triage(data):
    rows = []
    for r in data["triage"]:
        rows.append(
            f"<tr><td>{esc(r['area'])}</td><td>{esc(r['look_for'])}</td><td>{esc(r['why'])}</td></tr>"
        )
    body = f"""<table>
      <thead><tr><th>Area</th><th>What to look for</th><th>Why it matters / pitfall</th></tr></thead>
      <tbody>
      {"".join(rows)}
      </tbody>
    </table>"""
    dek = "Reading the output is the hard half. What each result means, and where it will mislead you."
    return render_shell("Triage indicators & gotchas", dek, body, "triage.html")


def build_translation(data):
    sections = []
    for s in data["translation"]:
        rows = "\n      ".join(
            f"<tr><td><code>{esc(r['v2'])}</code></td><td><code>{esc(r['v3'])}</code></td>"
            f"<td>{esc(r['notes'])}</td></tr>"
            for r in s["rows"]
        )
        slug = slugify(s["section"])
        sections.append(
            f"""<h2 id="{slug}">{esc(s['section'])}</h2>
    <table>
      <thead><tr><th>Volatility 2</th><th>Volatility 3</th><th>Notes &amp; differences</th></tr></thead>
      <tbody>
      {rows}
      </tbody>
    </table>"""
        )
    total = sum(len(s["rows"]) for s in data["translation"])
    body = "\n    ".join(sections)
    dek = (
        f"What each Volatility 2 command became in Volatility 3, and what has no replacement. "
        f"{total} commands across {len(data['translation'])} areas, for reading older writeups."
    )
    return render_shell("Volatility 2 to 3 translation", dek, body, "translation.html")


def build_notes(data):
    rows = "\n      ".join(
        f"<tr><td>{esc(r['topic'])}</td><td><code>{esc(r['flag'])}</code></td><td>{esc(r['notes'])}</td></tr>"
        for r in data["notes"]
    )
    legend_rows = []
    for i, leg in enumerate(data["legend"]):
        phase_name = data["windows"]["phases"][i]["name"] if i < len(data["windows"]["phases"]) else leg["phase"]
        legend_rows.append(
            f'<tr><td style="border-left:1rem solid {esc(leg["color"])}; padding-left:0.6rem">'
            f'{esc(leg["phase"])}</td><td>{esc(phase_name)}</td></tr>'
        )
    body = f"""<h2 id="usage-notes">Usage notes</h2>
    <table>
      <thead><tr><th>Topic</th><th>Flag / syntax</th><th>Notes</th></tr></thead>
      <tbody>
      {rows}
      </tbody>
    </table>

    <h2 id="legend">Legend -- phase colour bands</h2>
    <p>Each analysis phase carries one colour across the classification and workflow pages, shown here
    as a left rule rather than a filled row.</p>
    <table>
      <thead><tr><th>Phase</th><th>Name</th></tr></thead>
      <tbody>
      {"".join(legend_rows)}
      </tbody>
    </table>"""
    dek = f"{len(data['notes'])} usage notes and the phase colour legend used across the other pages."
    return render_shell("Usage notes & legend", dek, body, "notes.html")


def main():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    xlsx_src = ROOT / XLSX_NAME
    xlsx_dst = DOCS / XLSX_NAME
    if xlsx_src.exists():
        shutil.copyfile(xlsx_src, xlsx_dst)

    pages = {
        "index.html": build_index(data),
        "windows.html": build_classification_page("windows.html", data["windows"], "Windows"),
        "linux.html": build_classification_page("linux.html", data["linux"], "Linux"),
        "workflow.html": build_workflow(data),
        "framework.html": build_framework(data),
        "triage.html": build_triage(data),
        "translation.html": build_translation(data),
        "notes.html": build_notes(data),
    }

    for name, html_out in pages.items():
        (DOCS / name).write_text(html_out, encoding="utf-8")

    total_bytes = 0
    for p in DOCS.rglob("*"):
        if p.is_file():
            total_bytes += p.stat().st_size

    print("Build OK:")
    for name in pages:
        print(f"  wrote docs/{name} ({(DOCS / name).stat().st_size} bytes)")
    print(f"  total docs/ size: {total_bytes} bytes ({total_bytes / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
