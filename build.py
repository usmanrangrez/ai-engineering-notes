"""Build the notes site using only the Python standard library.

Supports headings, paragraphs, lists, tables, fenced code blocks, blockquotes,
interactive visuals (::: visual id | caption), recall accordions (::: question),
and semantic study callouts (::: concept / mental-model / warning / tip).
No untrusted HTML is executed.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site"
DATE = "2026-11-28"
PLAYLIST = "https://www.youtube.com/playlist?list=PLkz_y24mlSJZ9SFlc9O4Q4Grli5SQDbrB"

CALLOUT_META = {
    "concept": ("Core Concept", "callout-concept"),
    "mental-model": ("Mental Model", "callout-mental"),
    "warning": ("Critical Rule / Gotcha", "callout-warning"),
    "tip": ("Engineering Rule", "callout-tip"),
}


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
            out.append(
                f'<div class="code-block" data-lang="{esc(language.lower())}">'
                f'<div class="code-toolbar"><span class="code-lang">{esc(language)}</span>'
                f'<button class="copy-button" type="button" aria-label="Copy {esc(language)} code">Copy</button></div>'
                f'<pre><code class="lang-{esc(language.lower())}">{esc(chr(10).join(code))}</code></pre></div>'
            )
            i += 1
            continue
        if line.startswith("::: visual "):
            spec = line[len("::: visual "):].strip()
            parts = spec.split("|", 1)
            vid = re.sub(r"[^a-z0-9-]+", "", parts[0].strip().lower())
            caption = parts[1].strip() if len(parts) > 1 else ""
            out.append(
                f'<section class="visual-box" data-visual="{esc(vid)}" aria-label="{esc(caption or vid)}">'
                f'<p class="visual-fallback">Interactive visual: {esc(caption or vid)} (enable JavaScript to interact).</p>'
                f'</section>'
            )
            i += 1
            continue
        callout_match = re.match(r"^::: (concept|mental-model|warning|tip)\s*(.*)$", line)
        if callout_match:
            kind, title = callout_match[1], callout_match[2].strip()
            label, css_cls = CALLOUT_META[kind]
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                body.append(lines[i])
                i += 1
            rendered, _ = markdown("\n".join(body))
            heading_html = f'<div class="callout-head"><span class="callout-pill">{esc(label)}</span>' + (f'<strong>{inline(title)}</strong>' if title else '') + '</div>'
            out.append(f'<aside class="callout {css_cls}">{heading_html}<div class="callout-body">{rendered}</div></aside>')
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
            out.append(f'<details class="question"><summary><span>{inline(title)}</span><span class="q-chevron" aria-hidden="true">+</span></summary><div class="question-body">{rendered}</div></details>')
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
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1]):
            rows = [line]
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = lambda row: [c.strip() for c in row.strip().strip("|").split("|")]
            out.append(
                '<div class="table-scroll" role="region" aria-label="Reference table" tabindex="0">'
                '<table><thead><tr>'
                + ''.join(f'<th scope="col">{inline(c)}</th>' for c in cells(rows[0]))
                + '</tr></thead><tbody>'
            )
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


def read_minutes(source):
    words = len(re.findall(r"\b\w+\b", source))
    return max(2, math.ceil(words / 210))


def layout(title, body, chapters, *, current=None, toc=None):
    prefix = "../" if current else ""
    nav_groups = []
    last_group = None
    for c in chapters:
        if c["group"] != last_group:
            nav_groups.append(f'<div class="nav-group">{esc(c["group"])}</div>')
            last_group = c["group"]
        active = "active" if current and c["slug"] == current["slug"] else ""
        aria = ' aria-current="page"' if active else ""
        dot_cls = "dot-read" if c["status"] == "Read" else "dot-planned"
        nav_groups.append(
            f'<a class="chapter-link {active}" data-slug="{esc(c["slug"])}" href="{chapter_link(c, prefix)}"{aria}>'
            f'<span class="chapter-number">{c["number"]:02}</span>'
            f'<span class="chapter-title-text">{esc(c["title"])}</span>'
            f'<span class="nav-dot {dot_cls}" title="{esc(c["status"])}" aria-hidden="true"></span></a>'
        )
    nav = "".join(nav_groups)
    toc_html = "".join(f'<a href="#{slug}" data-toc="{slug}">{esc(label)}</a>' for slug, label in (toc or []))
    right = f'<aside class="page-toc" aria-label="On this page"><p>On this page</p><nav>{toc_html}</nav></aside>' if toc else ""
    progress_bar = '<div class="read-progress" aria-hidden="true"><div id="read-progress-fill"></div></div>' if current else ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="Interactive AI Engineering Study Handbook: Python, LangGraph, Tools, RAG, Persistence, Streaming, Human-in-the-Loop, and LangSmith with first-principles theory and live lab receipts."><title>{esc(title)} · AI Engineering Handbook</title><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet"><script>try{{document.documentElement.dataset.theme=localStorage.getItem('ai-notes-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}}catch(e){{}}</script><link rel="stylesheet" href="{prefix}assets/style.css"><script defer src="{prefix}assets/site.js"></script><script defer src="{prefix}assets/visuals.js"></script></head>
<body><a class="skip-link" href="#main">Skip to content</a>{progress_bar}<header class="topbar"><a class="brand" href="{prefix}index.html"><span class="brand-mark" aria-hidden="true">AI</span><span><strong>AI Engineering</strong><small>Interactive Study Handbook</small></span></a><nav class="topnav" aria-label="Primary"><a href="{prefix}index.html">Handbook</a><a href="{prefix}start.html">Start here</a><a href="{prefix}roadmap.html">Roadmap</a><a href="https://github.com/usmanrangrez/ai-engineering-notes">GitHub</a></nav><div class="top-actions"><button id="theme-toggle" class="theme-button" type="button" aria-label="Switch color theme">Dark</button><button id="menu-toggle" class="menu-button" type="button" aria-expanded="false" aria-controls="chapter-nav">Chapters</button></div></header>
<div class="shell"><aside class="sidebar" id="chapter-nav"><div class="sidebar-intro"><div class="study-mini"><span>Your study progress</span><strong id="sidebar-studied">0 studied</strong></div><div class="study-bar"><div id="sidebar-studied-fill"></div></div></div><nav aria-label="Chapters">{nav}</nav><div class="sidebar-foot"><span>Next milestone</span><a href="{prefix}chapters/25-integrated-support-agent.html">Resume Project (FastAPI + React)</a></div></aside><main id="main" class="{"chapter-main" if current else "index-main"}">{body}</main>{right}</div><footer class="site-footer"><span>Interactive AI Engineering Study Handbook · First-principles theory, visual walkthroughs, and real lab receipts.</span><a href="{prefix}about.html">Evidence &amp; editorial policy</a></footer><p id="copy-status" class="sr-only" role="status" aria-live="polite"></p></body></html>'''


def build():
    chapters = json.loads((ROOT / "chapters.json").read_text())
    changed = 0
    OUT.mkdir(exist_ok=True)
    for asset in (ROOT / "assets").iterdir():
        if asset.is_file():
            changed += write_if_changed(OUT / "assets" / asset.name, asset.read_text())
    for example in (ROOT / "examples").glob("*"):
        if example.is_file() and example.suffix in {".py", ".md"}:
            changed += write_if_changed(OUT / "examples" / example.name, example.read_text())

    meta = {}
    for c in chapters:
        src = (ROOT / "chapters" / f'{c["slug"]}.md').read_text()
        meta[c["slug"]] = {
            "source": src,
            "mins": read_minutes(src),
            "visuals": src.count("::: visual "),
        }

    read_count = sum(c["status"] == "Read" for c in chapters)
    visual_count = sum(1 for c in chapters if meta[c["slug"]]["visuals"] > 0)

    cards = []
    for c in chapters:
        m = meta[c["slug"]]
        has_v = m["visuals"] > 0
        v_badge = f'<span class="badge-visual">{m["visuals"]} interactive visual{"s" if m["visuals"] > 1 else ""}</span>' if has_v else ""
        status_label = "Ready to study" if c["status"] == "Read" else "Planned"
        cards.append(
            f'<li class="chapter-row" data-status="{c["status"]}" data-visual="{"yes" if has_v else "no"}" data-slug="{esc(c["slug"])}" data-search="{esc((c["title"] + " " + c["group"] + " " + c["summary"]).lower())}">'
            f'<a class="chapter-card" href="{chapter_link(c)}">'
            f'<div class="card-top"><span class="row-number">CH {c["number"]:02}</span><span class="card-group">{esc(c["group"])}</span><span class="status {c["status"].lower()}">{status_label}</span></div>'
            f'<strong class="card-title">{esc(c["title"])}</strong>'
            f'<p class="card-summary">{esc(c["summary"])}</p>'
            f'<div class="card-foot"><span class="card-mins">{m["mins"]} min read</span>{v_badge}<span class="studied-pill" hidden>Studied</span></div>'
            f'</a>'
            f'<div class="row-course"><a href="{esc(c["course_url"])}">{esc(c["course_label"])}</a></div></li>'
        )

    body = f'''<section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">AI Engineering Study Handbook · LangGraph · RAG · Agents</p>
        <h1>Master the theory.<br>See the data move.</h1>
        <p class="lede">Deep first-principles explanations, interactive visual walkthroughs, annotated Python code, and verified live receipts—built to actually study from and prepare for AI engineering roles.</p>
        <div class="hero-actions">
          <a class="btn-primary" href="chapters/23-rag-in-langgraph.html">Study RAG in LangGraph</a>
          <a class="btn-secondary" href="chapters/24-human-in-loop.html">Study Human-in-the-Loop</a>
          <a class="btn-ghost" href="roadmap.html">View full syllabus</a>
        </div>
      </div>
      <div class="hero-stats">
        <div class="stat-card"><span class="stat-num">{read_count}</span><span class="stat-label">Study chapters ready</span></div>
        <div class="stat-card"><span class="stat-num">{visual_count}</span><span class="stat-label">Chapters with interactive visuals</span></div>
        <div class="stat-card"><span class="stat-num">13 / 18</span><span class="stat-label">Core syllabus topics complete</span></div>
        <div class="stat-card stat-study"><span class="stat-num" id="home-studied-count">0 / {read_count}</span><span class="stat-label">Marked studied by you</span></div>
      </div>
    </section>
    <section class="next-lesson">
      <div>
        <span class="pill-next">Current Checkpoint · Updated {DATE}</span>
        <h2>Chatbot Parts 1–9 complete — Resume Project (FastAPI + React) is next.</h2>
        <p>Tool Calling, ReAct, RAG, Persistence, Streaming, and Human-in-the-Loop are all verified with live runs and interactive visuals.</p>
      </div>
      <a class="btn-primary" href="chapters/24-human-in-loop.html">Review Chapter 24</a>
    </section>
    <section class="chapter-index" aria-labelledby="chapter-heading">
      <div class="section-heading">
        <div>
          <h2 id="chapter-heading">Study Curriculum</h2>
          <p id="results-count" class="result-count" aria-live="polite">{len(chapters)} chapters</p>
        </div>
        <div class="index-tools">
          <div class="filter-buttons" role="group" aria-label="Filter chapters">
            <button type="button" data-filter="All" aria-pressed="true">All ({len(chapters)})</button>
            <button type="button" data-filter="Read" aria-pressed="false">Ready ({read_count})</button>
            <button type="button" data-filter="Visual" aria-pressed="false">Interactive Visuals ({visual_count})</button>
            <button type="button" data-filter="Planned" aria-pressed="false">Planned ({len(chapters)-read_count})</button>
          </div>
          <label class="search-label"><span class="sr-only">Search chapters</span><input id="chapter-search" type="search" placeholder="Search concepts, tools, RAG, HITL..." autocomplete="off"></label>
        </div>
      </div>
      <ol class="chapter-grid">{''.join(cards)}</ol>
      <p id="empty-results" hidden>No chapters match that filter. Try another keyword or choose All.</p>
    </section>'''

    changed += write_if_changed(OUT / "index.html", layout("Study Curriculum", body, chapters))

    for i, c in enumerate(chapters):
        m = meta[c["slug"]]
        rendered, toc = markdown(m["source"])
        course = f'<a href="{esc(c["course_url"])}">{esc(c["course_label"])}</a>'
        status_note = '<aside class="callout callout-warning"><div class="callout-head"><span class="callout-pill">Planned Chapter</span><strong>Outline only — no completed lab claimed yet</strong></div><div class="callout-body"><p>This outline will be replaced with deep theory, visuals, and verified receipts after the lesson.</p></div></aside>' if c["status"] == "Planned" else ''
        prev = f'<a class="pn-card" href="{chapters[i-1]["slug"]}.html"><span>← Previous</span><strong>{esc(chapters[i-1]["title"])}</strong></a>' if i else '<a class="pn-card" href="../index.html"><span>← Back</span><strong>Study Curriculum</strong></a>'
        nxt = f'<a class="pn-card pn-next" href="{chapters[i+1]["slug"]}.html"><span>Next →</span><strong>{esc(chapters[i+1]["title"])}</strong></a>' if i + 1 < len(chapters) else '<a class="pn-card pn-next" href="../roadmap.html"><span>Next →</span><strong>Full Roadmap</strong></a>'
        mobile_toc = '<details class="inline-toc"><summary>In this chapter</summary><nav aria-label="Lesson sections">' + ''.join(f'<a href="#{slug}">{esc(label)}</a>' for slug, label in toc) + '</nav></details>'
        v_pill = f'<span class="badge-visual">{m["visuals"]} interactive visual{"s" if m["visuals"] > 1 else ""}</span>' if m["visuals"] > 0 else ""
        study_btn = f'<button type="button" class="study-toggle" data-study-slug="{esc(c["slug"])}">Mark as studied</button>' if c["status"] == "Read" else ""
        body = (
            f'<div class="breadcrumbs"><a href="../index.html">Handbook</a><span>/</span><span>Chapter {c["number"]:02}</span><span>/</span><span>{esc(c["group"])}</span></div>'
            f'<header class="chapter-header">'
            f'<div class="chapter-badges"><span class="status {c["status"].lower()}">{"Ready to study" if c["status"] == "Read" else "Planned"}</span><span class="meta-chip">{m["mins"]} min read</span>{v_pill}</div>'
            f'<h1>{esc(c["title"])}</h1>'
            f'<p class="lede">{esc(c["summary"])}</p>'
            f'<div class="chapter-bar"><div class="course-link">{course}</div>{study_btn}</div>'
            f'</header>{status_note}{mobile_toc}<article>{rendered}</article>'
            f'<div class="chapter-finish"><div><p class="checked">Last verified: <time datetime="{DATE}">{DATE}</time>. Live learner outputs are preserved separately from conceptual diagrams.</p></div>{study_btn}</div>'
            f'<nav class="prev-next" aria-label="Chapter navigation">{prev}{nxt}</nav>'
        )
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
