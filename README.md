# Mousa Analyzing Memory

A static Volatility 3 plugin reference for memory forensics: 155 plugins across Windows
and Linux, mapped to a 10-phase (Windows) and 9-phase (Linux) analysis workflow, with a
runnable example command for every plugin.

Every plugin name and flag was verified by running `vol.py <plugin> -h` against
Volatility 3 stable **v2.28** (verified 2026-08-28). Plugin sets differ between
versions -- check your own `vol -h` output if something here doesn't match your install.

Live site: `https://theonlymosmos.github.io/Mousa-Analyzing-Memory/`

## Source of truth

[`Volatility3_Memory_Analysis_Reference.xlsx`](Volatility3_Memory_Analysis_Reference.xlsx)
in the repo root is the source of truth for every row on the site. It is not
paraphrased, summarised, merged, or edited -- if something in it looks wrong, that's a
workbook issue, not a site bug. Download it directly if you want the raw data.

## How the site is built

Two committed stages, so the site is reproducible, reviewable, and never hand-edited:

```
python3 tools/extract.py   # openpyxl reads the workbook, writes data/reference.json
                            # asserts row counts per sheet, fails loudly on mismatch
python3 tools/build.py     # reads data/reference.json, writes static HTML into docs/
```

`data/reference.json` is committed so a data change is visible in a diff without
opening a spreadsheet. `docs/` is the GitHub Pages source (Settings -> Pages -> branch
`main`, folder `/docs`). A GitHub Action re-runs both scripts on every push and fails
the build if `docs/` doesn't match what the workbook produces, so the published site
can't drift from the source.

No Node, no bundler, no CSS framework, no CDN. Vanilla HTML, one CSS file, one small
JS file, self-hosted fonts. Everything works with JavaScript disabled; JS only adds
the filter box, phase toggles, copy buttons, and deep-link highlighting.

To validate a local build against the definition-of-done checks (row counts, plugin
diff, broken anchors, banned words/emoji):

```
python3 tools/validate.py
```

## License

The build scripts (`tools/`) and site code (`docs/style.css`, `docs/script.js`,
page templates) are MIT -- see [LICENSE](LICENSE).

The reference content itself (plugin descriptions, workflow phases, triage notes,
translation table) is **CC BY 4.0**, credit Mousa Mohamed.

This project is not affiliated with or endorsed by the Volatility Foundation.
Volatility 3 is the subject of this reference, licensed under the GPL / Volatility
Software License -- see https://github.com/volatilityfoundation/volatility3.
