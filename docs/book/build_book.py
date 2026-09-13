"""Build the Saqqa field manual: docs/book/*.md -> one HTML file (print-ready) -> PDF.

    python docs/book/build_book.py          -> docs/book/out/Saqqa_Field_Manual.html + .pdf

Every number the chapters cite from the prototype comes from docs/book_evidence.json (written by the evidence
extractor from runs/*.json and the events table), substituted at build time as {{stats.calls_total}} etc., so the
book cannot drift from the logged runs. Chapter files are plain Markdown, one per chapter, in filename order.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import markdown

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

EVIDENCE = json.load(open(ROOT / "docs" / "book_evidence.json", encoding="utf-8"))
EVENT = json.load(open(ROOT / "docs" / "book_evidence_event.json", encoding="utf-8"))


def lookup(path: str):
    cur: object = {"stats": EVIDENCE["stats"], "calls": EVIDENCE["calls"], "runs": {r["id"]: r for r in EVIDENCE["runs"]}, "event": EVENT}
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part, f"⟨missing {path}⟩")
        elif isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        else:
            return f"⟨missing {path}⟩"
    return cur


def substitute(text: str) -> str:
    def rep(m):
        v = lookup(m.group(1).strip())
        if isinstance(v, (dict, list)):
            return "```json\n" + json.dumps(v, indent=1, ensure_ascii=False) + "\n```"
        return str(v)
    return re.sub(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}", rep, text)


CSS = """
@page { size: A4; margin: 22mm 20mm 24mm 20mm; }
:root { --ink:#14171C; --mute:#5E656E; --rule:#D8D4CC; --blue:#0E6BA8; --alert:#B4462A; --green:#2F6B4F; --paper:#FFFFFF; }
html { font-size: 11.2pt; }
body { margin: 0; color: var(--ink); background: var(--paper); font-family: "Source Serif 4", Georgia, "Times New Roman", serif; line-height: 1.5; }
.page { max-width: 760px; margin: 0 auto; padding: 48px 24px 96px; }
h1, h2, h3, h4 { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-weight: 500; line-height: 1.2; letter-spacing: -.01em; }
h1 { font-size: 30pt; margin: 0 0 6px; font-weight: 300; }
h2 { font-size: 19pt; margin: 42px 0 12px; padding-top: 10px; border-top: 1px solid var(--ink); page-break-before: always; }
h2:first-of-type { page-break-before: auto; }
h3 { font-size: 13.5pt; margin: 26px 0 8px; }
h4 { font-size: 11pt; margin: 18px 0 6px; color: var(--mute); text-transform: uppercase; letter-spacing: .08em; }
p { margin: 0 0 11px; text-wrap: pretty; }
ul, ol { margin: 0 0 12px 22px; padding: 0; }
li { margin-bottom: 4px; }
code, pre { font-family: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace; font-size: 9pt; }
code { background: #F3F1EC; padding: 1px 4px; border-radius: 3px; }
pre { background: #F3F1EC; padding: 12px 14px; overflow-x: auto; border-left: 3px solid var(--rule); white-space: pre-wrap; word-break: break-word; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; font-size: 9.5pt; margin: 10px 0 16px; page-break-inside: auto; }
th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid var(--rule); }
th { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-weight: 500; font-size: 8.5pt; text-transform: uppercase; letter-spacing: .08em; color: var(--mute); }
tr { page-break-inside: avoid; }
blockquote { margin: 14px 0; padding: 8px 16px; border-left: 3px solid var(--blue); color: var(--ink); background: #F7F6F2; }
blockquote p { margin: 0; }
.kicker { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9pt; letter-spacing: .14em; text-transform: uppercase; color: var(--mute); }
.subtitle { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 13pt; color: var(--mute); margin: 0 0 30px; font-weight: 300; }
.callout { border: 1px solid var(--rule); padding: 12px 16px; margin: 14px 0; background: #FBFAF7; }
.callout.warn { border-color: var(--alert); }
.callout.ok { border-color: var(--green); }
.callout > :first-child { margin-top: 0; } .callout > :last-child { margin-bottom: 0; }
.toc { columns: 2; column-gap: 32px; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10pt; }
.toc a { color: var(--ink); text-decoration: none; }
a { color: var(--blue); }
hr { border: 0; border-top: 1px solid var(--rule); margin: 24px 0; }
strong { font-weight: 600; }
.small { font-size: 9pt; color: var(--mute); }
@media print { .page { padding: 0; max-width: none; } a { color: inherit; } }
"""


def main() -> None:
    chapters = sorted(p for p in HERE.glob("[0-9][0-9]_*.md"))
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list", "md_in_html"], extension_configs={"toc": {"toc_depth": "2-3"}})
    bodies, toc_items = [], []
    for p in chapters:
        text = substitute(p.read_text(encoding="utf-8"))
        html = md.convert(text)
        md.reset()
        m = re.search(r"^## (.+)$", text, re.M)
        if m:
            toc_items.append(m.group(1))
        bodies.append(html)
    stats = EVIDENCE["stats"]
    toc = "<div class='toc'><ol>" + "".join(f"<li>{t}</li>" for t in toc_items) + "</ol></div>"
    front = (f"<p class='kicker'>Saqqa · field manual · built {stats['generated']} from commit {stats['commit']}</p>"
             f"<h1>Paid on a Signature</h1><p class='subtitle'>The Saqqa field manual: what we built, what it proves, where it breaks, and how to defend it in a room.</p>{toc}")
    page = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Paid on a Signature · Saqqa field manual</title>"
            f"<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap'>"
            f"<style>{CSS}</style></head><body><div class='page'>{front}{''.join(bodies)}</div></body></html>")
    out_html = OUT / "Saqqa_Field_Manual.html"
    out_html.write_text(page, encoding="utf-8")
    print("HTML ->", out_html, f"({out_html.stat().st_size / 1024:.0f} KB, {len(chapters)} chapters)")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.goto(out_html.resolve().as_uri(), wait_until="networkidle")
            pg.wait_for_timeout(800)
            pg.pdf(path=str(OUT / "Saqqa_Field_Manual.pdf"), format="A4", print_background=True,
                   margin={"top": "22mm", "bottom": "24mm", "left": "20mm", "right": "20mm"},
                   display_header_footer=True, header_template="<span></span>",
                   footer_template="<div style='width:100%;font:8px Helvetica,Arial,sans-serif;color:#7C838C;padding:0 20mm;display:flex;justify-content:space-between'><span>Saqqa · Paid on a Signature</span><span class='pageNumber'></span></div>")
            b.close()
        print("PDF  ->", OUT / "Saqqa_Field_Manual.pdf", f"({(OUT / 'Saqqa_Field_Manual.pdf').stat().st_size / 1024:.0f} KB)")
    except Exception as exc:  # noqa: BLE001
        print("PDF skipped:", exc)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
