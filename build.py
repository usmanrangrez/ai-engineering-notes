"""Build the notes site using only the Python standard library.

The Markdown subset is intentionally small: headings, paragraphs, lists, tables,
fenced code, blockquotes, and ::: question blocks. No untrusted HTML is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site"
DATE = "2026-11-22"
PLAYLIST = "https://www.youtube.com/playlist?list=PLkz_y24mlSJZ9SFlc9O4Q4Grli5SQDbrB"


def esc(value):
    return html.escape(str(value), quote=True)


def inline(text):
    tokens = []

    def hold(value):
        tokens.append(value)
        return f"\x00{len(tokens)-1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: hold(f"<code>{esc(m[1])}</code>"), text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: hold(f'<a href="{esc(m[2])}">{esc(m[1])}</a>')
        if re.match(r"^(https?://|[\w./#-]+$)", m[2]) else esc(m[1]),
        text,
    )
    text = esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m[1])], text)


def markdown(source):
    lines = source.splitlines()
    out, toc, slugs = [], [], {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            language = line[3:].strip() or "text"
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            out.append(f'<div class="code-block"><div class="code-toolbar"><span>{esc(language)}</span><button class="copy-button" type="button" aria-label="Copy {esc(language)} code">Copy</button></div><pre><code>{esc(chr(10).join(code))}</code></pre></div>')
            i += 1
            continue
        if line.startswith("::: question "):
            title = line[len("::: question "):]
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                body.append(lines[i])
                i += 1
            rendered, _ = markdown("\n".join(body))
            out.append(f'<details class="question"><summary>{inline(title)}</summary><div>{rendered}</div></details>')
            i += 1
            continue
        heading = re.match(r"^(#{1,4}) (.+)$", line)
        if heading:
            level, title = len(heading[1]), heading[2]
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            count = slugs.get(slug, 0)
            slugs[slug] = count + 1
            slug += f"-{count}" if count else ""
            out.append(f'<h{level} id="{slug}">{inline(title)}</h{level}>')
            if level == 2:
                toc.append((slug, title))
            i += 1
            continue
        if line.startswith("|") and i+1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i+1]):
            rows = [line]
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = lambda row: [c.strip() for c in row.strip().strip("|").split("|")]
            out.append('<div class="table-scroll" role="region" aria-label="Reference table" tabindex="0"><table><thead><tr>' + ''.join(f'<th scope="col">{inline(c)}</th>' for c in cells(rows[0])) + '</tr></thead><tbody>')
            for row in rows[1:]:
                out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in cells(row)) + '</tr>')
            out.append('</tbody></table></div>')
            continue
        if re.match(r"^[-*] ", line) or re.match(r"^\d+\. ", line):
            ordered = bool(re.match(r"^\d+\. ", line))
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>")
            pattern = r"^\d+\. " if ordered else r"^[-*] "
            while i < len(lines) and re.match(pattern, lines[i]):
                out.append(f'<li>{inline(re.sub(pattern, "", lines[i]))}</li>')
                i += 1
            out.append(f"</{tag}>")
            continue
        if line.startswith("> "):
            quote = []
            while i < len(lines) and lines[i].startswith("> "):
                quote.append(lines[i][2:])
                i += 1
            out.append(f'<aside class="note">{inline(" ".join(quote))}</aside>')
            continue
        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4} |```|:::|\| |> |[-*] |\d+\. )", lines[i]):
            paragraph.append(lines[i])
            i += 1
        out.append(f'<p>{inline(" ".join(paragraph))}</p>')
    return "\n".join(out), toc


def write_if_changed(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return 0
    path.write_text(content, encoding="utf-8")
    return 1


def chapter_link(chapter, prefix=""):
    return f'{prefix}chapters/{chapter["slug"]}.html'


def layout(title, body, chapters, *, current=None, toc=None):
    prefix = "../" if current else ""
    nav = ''.join(f'<a class="chapter-link {"active" if current and c["slug"] == current["slug"] else ""}" href="{chapter_link(c, prefix)}" {"aria-current=page" if current and c["slug"] == current["slug"] else ""}><span class="chapter-number">{c["number"]:02}</span><span>{esc(c["title"])}</span><span class="nav-status">{c["status"]}</span></a>' for c in chapters)
    toc_html = ''.join(f'<a href="#{slug}">{esc(label)}</a>' for slug, label in (toc or []))
    right = f'<aside class="page-toc" aria-label="On this page"><p>On this page</p>{toc_html}</aside>' if toc else ''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="Hands-on AI engineering notes: LangGraph workflows, persistence, streaming and LangSmith, with real lab receipts."><title>{esc(title)} · AI Engineering Notes</title><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;450;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet"><script>try{{document.documentElement.dataset.theme=localStorage.getItem('ai-notes-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}}catch(e){{}}</script><link rel="stylesheet" href="{prefix}assets/style.css"><script defer src="{prefix}assets/site.js"></script></head>
<body><a class="skip-link" href="#main">Skip to content</a><header class="topbar"><a class="brand" href="{prefix}index.html"><span class="brand-mark" aria-hidden="true">a/</span><span>AI Engineering<br><strong>Notes</strong></span></a><nav class="topnav" aria-label="Primary"><a href="{prefix}start.html">Start here</a><a href="{prefix}index.html">Chapters</a><a href="{prefix}roadmap.html">Roadmap</a><a href="https://github.com/usmanrangrez/ai-engineering-notes">Source</a></nav><button id="theme-toggle" class="theme-button" type="button" aria-label="Switch color theme">Dark mode</button><button id="menu-toggle" class="menu-button" type="button" aria-expanded="false" aria-controls="chapter-nav">Chapters</button></header>
<div class="shell"><aside class="sidebar" id="chapter-nav"><div class="sidebar-intro"><a href="{prefix}start.html">New reader? Start here</a><p>LangGraph track<br>Bappy + guided labs</p></div><nav aria-label="Chapters">{nav}</nav><div class="sidebar-foot">Next course addition<br><a href="{prefix}chapters/21-tool-calling.html">Tool calling in LangGraph</a></div></aside><main id="main" class="{"chapter-main" if current else "index-main"}">{body}</main>{right}</div><footer class="site-footer"><span>Written with AI help. Original labs were run by hand by the learner; new offline examples were verified by the notes author. Planned work is labeled.</span><a href="{prefix}about.html">Evidence &amp; editorial policy</a></footer><p id="copy-status" class="sr-only" role="status" aria-live="polite"></p></body></html>'''


def build():
    chapters = json.loads((ROOT / "chapters.json").read_text())
    changed = 0
    OUT.mkdir(exist_ok=True)
    for asset in (ROOT / "assets").iterdir():
        changed += write_if_changed(OUT / "assets" / asset.name, asset.read_text())
    for example in (ROOT / "examples").glob("*"):
        if example.is_file() and example.suffix in {".py", ".md"}:
            changed += write_if_changed(OUT / "examples" / example.name, example.read_text())
    read_count = sum(c["status"] == "Read" for c in chapters)
    rows = []
    for c in chapters:
        rows.append(f'<li class="chapter-row" data-status="{c["status"]}" data-search="{esc((c["title"]+" "+c["group"]+" "+c["summary"]).lower())}"><a href="{chapter_link(c)}"><span class="row-number">{c["number"]:02}</span><span class="row-copy"><strong>{esc(c["title"])}</strong><span>{esc(c["summary"])}</span></span><span class="status {c["status"].lower()}">{c["status"]}</span></a><div class="row-course"><a href="{esc(c["course_url"])}">{esc(c["course_label"])}</a></div></li>')
    body = f'''<section class="intro"><p class="eyebrow">A practical course, built from real learning</p><h1>Learn the concepts.<br>Build the system.</h1><p class="lede">Learn AI engineering from the beginning: clear definitions, small code walkthroughs, runnable labs, and real debugging evidence. Python, LangGraph, and LangSmith first.</p><div class="intro-meta"><span>{read_count} teaching chapters</span><span>11 of 18 original topics complete</span><span>Updated {DATE}</span></div></section><section class="reader-start"><p class="eyebrow">Your first visit</p><h2>Start with the explanation. Then run it.</h2><p>Each available chapter teaches the mechanism before the code, includes exercises with self-check answers, and preserves the original lab evidence.</p><a href="start.html">Start here: setup and reading guide</a><a href="chapters/01-async-python.html">Begin chapter 1</a></section><section class="next-lesson"><div><p>Original learner’s course checkpoint</p><h2>Tool calling is next.</h2><span>LangSmith tracing is complete. Evaluation experiments remain planned.</span></div><a class="text-action" href="chapters/21-tool-calling.html">See the next chapter</a></section><section class="chapter-index" aria-labelledby="chapter-heading"><div class="section-heading"><h2 id="chapter-heading">The notebook</h2><a href="roadmap.html">View learning order</a></div><div class="index-tools"><div class="filter-buttons" role="group" aria-label="Filter chapters"><button type="button" data-filter="All" aria-pressed="true">All</button><button type="button" data-filter="Read" aria-pressed="false">Read</button><button type="button" data-filter="Planned" aria-pressed="false">Planned</button></div><label class="search-label"><span class="sr-only">Search chapters</span><input id="chapter-search" type="search" placeholder="Search the notebook" autocomplete="off"></label></div><p id="results-count" class="result-count" aria-live="polite">{len(chapters)} chapters</p><ol class="chapter-list">{''.join(rows)}</ol><p id="empty-results" hidden>No chapters match. Try another search or choose All.</p></section>'''
    changed += write_if_changed(OUT / "index.html", layout("Chapters", body, chapters))
    for i, c in enumerate(chapters):
        source = (ROOT / "chapters" / f'{c["slug"]}.md').read_text()
        rendered, toc = markdown(source)
        course = f'<a href="{esc(c["course_url"])}">{esc(c["course_label"])}</a>'
        status_note = '<p class="planned-notice">Planned chapter. No completed lab or verified output is claimed. The outline will be replaced with notes after the lesson.</p>' if c["status"] == "Planned" else ''
        prev = f'<a href="{chapters[i-1]["slug"]}.html"><span>Previous</span>{esc(chapters[i-1]["title"])}</a>' if i else '<a href="../index.html"><span>Previous</span>Chapter index</a>'
        nxt = f'<a href="{chapters[i+1]["slug"]}.html"><span>Next</span>{esc(chapters[i+1]["title"])}</a>' if i+1 < len(chapters) else '<a href="../roadmap.html"><span>Next</span>Review the roadmap</a>'
        mobile_toc = '<details class="inline-toc"><summary>In this lesson</summary><nav aria-label="Lesson sections">' + ''.join(f'<a href="#{slug}">{esc(label)}</a>' for slug, label in toc) + '</nav></details>'
        reader_note = '<p class="reader-note">First time here? <a href="../start.html">Set up and learn how to use these lessons.</a> Read marks the original course record, not your personal progress.</p>' if c["status"] == "Read" else ''
        body = f'<div class="breadcrumbs"><a href="../index.html">Notebook</a><span>/</span><span>Chapter {c["number"]:02}</span></div><header class="chapter-header"><p class="eyebrow">{esc(c["group"])}</p><h1>{esc(c["title"])}</h1><p class="lede">{esc(c["summary"])}</p><div class="chapter-meta"><span class="status {c["status"].lower()}">{c["status"]}</span><span>{esc(c["coverage"])}</span></div><p class="course-link">{course}</p></header>{status_note}{reader_note}{mobile_toc}<article>{rendered}</article><p class="checked">Facts last checked: <time datetime="{DATE}">{DATE}</time>. Historical outputs are receipts, not promises of identical future results.</p><nav class="prev-next" aria-label="Chapter navigation">{prev}{nxt}</nav>'
        changed += write_if_changed(OUT / "chapters" / f'{c["slug"]}.html', layout(c["title"], body, chapters, current=c, toc=toc))
    for name, title in (("roadmap", "Learning roadmap"), ("about", "Evidence & editorial policy"), ("start", "Start here")):
        rendered, _ = markdown((ROOT / f"{name.upper()}.md").read_text())
        changed += write_if_changed(OUT / f"{name}.html", layout(title, f'<div class="standalone"><article>{rendered}</article></div>', chapters))
    changed += write_if_changed(OUT / ".nojekyll", "")
    print(f"Built {len(chapters)} chapters ({read_count} Read / {len(chapters)-read_count} Planned); {changed} files changed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build()
