"""Verify the generated static site without third-party dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links, self.ids, self.h1 = [], [], 0
        self.copy_count = 0
        self.code_count = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag in {"script", "link"}:
            value = attrs.get("src") or attrs.get("href")
            if value:
                self.links.append(value)
        if tag == "pre":
            self.code_count += 1
        if tag == "button" and "copy-button" in attrs.get("class", ""):
            self.copy_count += 1


def main():
    errors = []
    chapters = json.loads((ROOT / "chapters.json").read_text())
    pages = {p.resolve(): Page(p.read_text()) for p in SITE.rglob("*.html")}
    for path, page in pages.items():
        relative = path.relative_to(ROOT)
        if page.h1 != 1:
            errors.append(f"{relative}: expected one h1, found {page.h1}")
        if len(page.ids) != len(set(page.ids)):
            errors.append(f"{relative}: duplicate IDs")
        if page.copy_count != page.code_count:
            errors.append(f"{relative}: missing copy controls")
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                if url.scheme not in {"https", "http", "mailto"}:
                    errors.append(f"{relative}: unsafe URL {href}")
                continue
            if url.path.startswith("/"):
                errors.append(f"{relative}: root-relative link breaks project Pages: {href}")
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.exists():
                errors.append(f"{relative}: missing target {href}")
            elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                errors.append(f"{relative}: missing anchor {href}")

    banned = {
        "personal absolute path": re.compile(r"/(?:Users|var/folders|private/var/folders)/"),
        "email address": re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
        "literal account/message UUID": re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I),
        "credential pattern": re.compile(r"\b(?:gsk_|lsv2_|github_pat_|ghp_|sk-proj-)[A-Za-z0-9_-]{12,}"),
    }
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", "__pycache__"} for part in path.parts):
            continue
        if path == Path(__file__).resolve():
            continue
        if path.name.startswith(".env") or path.suffix in {".db", ".sqlite"}:
            errors.append(f"Private runtime file present: {path.name}")
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for label, pattern in banned.items():
            if pattern.search(text):
                errors.append(f"{path.relative_to(ROOT)}: {label}")
    for chapter in chapters:
        path = ROOT / "chapters" / f'{chapter["slug"]}.md'
        text = path.read_text()
        for heading in ("## What it is and why it matters", "## Interview questions", "## References"):
            if heading not in text:
                errors.append(f"{path.name}: missing {heading}")
        if chapter["status"] not in {"Read", "Planned"}:
            errors.append(f"{path.name}: unexpected status")

    before = {p: p.stat().st_mtime_ns for p in SITE.rglob("*") if p.is_file()}
    result = subprocess.run([sys.executable, str(ROOT / "build.py")], capture_output=True, text=True, check=True)
    after = {p: p.stat().st_mtime_ns for p in SITE.rglob("*") if p.is_file()}
    if before != after:
        errors.append("An unchanged second build rewrote output files")
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print(f"PASS: {len(chapters)} chapter sources; {len(pages)} HTML pages; local links/anchors; unique IDs; code-copy coverage; privacy scan; incremental build.")
    print(result.stdout.strip())


if __name__ == "__main__":
    main()
