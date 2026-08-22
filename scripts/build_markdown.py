#!/usr/bin/env python3
"""Generate the markdown twin of every content page.

The site is static on github pages, which can't negotiate on `Accept`, so the
markdown an agent wants has to exist at a real url. Each page gets a `.md`
sibling (`/about.html` -> `/about.md`), advertised from the html with
`<link rel="alternate" type="text/markdown">` and listed in llms.txt. The same
files are concatenated into llms-full.txt.

Run from the repo root:

    python3 scripts/build_markdown.py          # write the .md files
    python3 scripts/build_markdown.py --check  # fail if anything is stale
"""

import argparse
import html
import io
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin

SITE = "https://mohammad.page/"

# the pages worth handing an agent. 404.html and the blog-post-N.html redirect
# stubs are deliberately out: neither has content to read.
PAGES = [
    "index.html",
    "about.html",
    "contact.html",
    "privacy.html",
    "blog.html",
    "now.html",
    "links.html",
    "spotify.html",
    "photos.html",
    "studio.html",
    "das-man.html",
    "making-software-is-so-easy-i-stopped-doing-it.html",
    "i-havent-coded-in-3-months.html",
    "the-ai-hangover.html",
    "always-be-building.html",
    "delete-more-code.html",
    "llms-in-production.html",
    "retellio-insight-podcasts.html",
    "ai-in-b2b-customer-research.html",
]

SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "template"}
BLOCK_TAGS = {"p", "div", "section", "article", "li", "ul", "ol", "h1", "h2",
              "h3", "h4", "h5", "h6", "blockquote", "pre", "footer", "nav",
              "figure", "figcaption", "main", "header", "tr"}
HEADINGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####",
            "h6": "######"}


class MainExtractor(HTMLParser):
    """Pull the innerHTML of the first <main> out of a page."""

    def __init__(self):
        HTMLParser.__init__(self)
        self.depth = 0
        self.parts = []
        self.done = False

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        if tag == "main" and self.depth == 0:
            self.depth = 1
            return
        if self.depth:
            if tag == "main":
                self.depth += 1
            self.parts.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        if self.depth and not self.done:
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.done or not self.depth:
            return
        if tag == "main":
            self.depth -= 1
            if self.depth == 0:
                self.done = True
            return
        self.parts.append("</%s>" % tag)

    def handle_data(self, data):
        if self.depth and not self.done:
            self.parts.append(data)

    def handle_entityref(self, name):
        if self.depth and not self.done:
            self.parts.append("&%s;" % name)

    def handle_charref(self, name):
        if self.depth and not self.done:
            self.parts.append("&#%s;" % name)


class Markdownifier(HTMLParser):
    """A converter for exactly the markup this site uses — nothing more."""

    def __init__(self, base_url):
        HTMLParser.__init__(self)
        self.base_url = base_url
        self.out = []
        self.skip = 0
        self.list_stack = []
        self.link_href = None
        self.link_text = []
        self.pending_marker = False

    # -- helpers ---------------------------------------------------------
    def emit(self, text):
        if self.link_href is not None:
            self.link_text.append(text)
        else:
            self.out.append(text)

    def newblock(self):
        self.emit("\n\n")

    def absolute(self, url):
        if not url:
            return ""
        return urljoin(self.base_url, url)

    # -- parser callbacks ------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag in SKIP_TAGS or "email-hint" in classes:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "span" and "dates" in classes:
            # the role and date spans are adjacent with no whitespace between
            # them in the html; markdown needs a visible separator
            self.emit(" — ")
        if tag in BLOCK_TAGS and tag != "li":
            self.pending_marker = False
        if tag in HEADINGS:
            self.newblock()
            self.emit(HEADINGS[tag] + " ")
        elif tag in ("p", "div", "section", "article", "blockquote", "figure"):
            self.newblock()
            if tag == "blockquote":
                self.emit("> ")
        elif tag in ("ul", "ol"):
            self.list_stack.append(tag)
            self.newblock()
        elif tag == "li":
            self.emit("\n")
            marker = "- " if (not self.list_stack or self.list_stack[-1] == "ul") else "1. "
            self.emit("  " * max(0, len(self.list_stack) - 1) + marker)
            self.pending_marker = True
            return
        elif tag == "br":
            self.emit("\n")
        elif tag in ("em", "i"):
            self.emit("*")
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag == "code":
            self.emit("`")
        elif tag == "a":
            self.link_href = self.absolute(a.get("href", ""))
            self.link_text = []
        elif tag == "img":
            alt = a.get("alt", "")
            src = self.absolute(a.get("src", ""))
            # the lazy-load placeholders are inline base64; the real file is
            # what an agent should see, so drop data: urls entirely
            if src and not src.startswith("data:"):
                self.emit("![%s](%s)" % (alt, src))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in ("br", "img") and tag not in SKIP_TAGS:
            self.handle_endtag(tag)
        elif tag in SKIP_TAGS:
            self.skip = max(0, self.skip - 1)

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS or (tag == "span" and self.skip):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in HEADINGS or tag in ("p", "div", "section", "article",
                                      "blockquote", "figure"):
            self.newblock()
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.newblock()
        elif tag in ("em", "i"):
            self.emit("*")
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag == "code":
            self.emit("`")
        elif tag == "a" and self.link_href is not None:
            text = "".join(self.link_text).strip()
            href = self.link_href
            self.link_href = None
            self.link_text = []
            if text and href:
                self.out.append("[%s](%s)" % (text, href))
            elif text:
                self.out.append(text)

    def handle_data(self, data):
        if self.skip:
            return
        if self.pending_marker:
            if not data.strip():
                return
            data = data.lstrip()
            self.pending_marker = False
        self.emit(data)

    def handle_entityref(self, name):
        if not self.skip:
            self.emit(html.unescape("&%s;" % name))

    def handle_charref(self, name):
        if not self.skip:
            self.emit(html.unescape("&#%s;" % name))

    def result(self):
        return "".join(self.out)


def tidy(text):
    """Collapse the whitespace html let us be sloppy about."""
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).rstrip()
        # a list marker or blockquote arrow with nothing after it is noise
        if line.strip() in ("-", "1.", ">", "*", "**"):
            line = ""
        lines.append(line.lstrip() if line.startswith(" ") else line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def meta(source, name):
    m = re.search(
        r'<meta\s+name="%s"\s*\n?\s*content="([^"]*)"' % re.escape(name),
        source, re.S)
    return " ".join(html.unescape(m.group(1)).split()) if m else ""


def title_of(source):
    m = re.search(r"<title>(.*?)</title>", source, re.S)
    return " ".join(html.unescape(m.group(1)).split()) if m else ""


def page_url(page):
    return SITE if page == "index.html" else SITE + page


def render(page, source):
    extractor = MainExtractor()
    extractor.feed(source)
    inner = "".join(extractor.parts)
    if not inner.strip():
        raise SystemExit("no <main> found in %s" % page)

    conv = Markdownifier(page_url(page))
    conv.feed(inner)
    body = tidy(conv.result())
    # the document already opens with the page title, so a leading <h1>
    # would just say it twice
    body = re.sub(r"\A# [^\n]*\n+", "", body)

    title = title_of(source) or page
    description = meta(source, "description")

    header = ["# %s" % title, ""]
    if description:
        header += ["> %s" % description, ""]
    header += [
        "Source: %s" % page_url(page),
        "",
        "---",
        "",
        "",
    ]
    return "\n".join(header) + body


def md_name(page):
    return page[:-len(".html")] + ".md"


def build(root):
    written = {}
    for page in PAGES:
        path = os.path.join(root, page)
        if not os.path.exists(path):
            raise SystemExit("missing page: %s" % page)
        source = io.open(path, encoding="utf-8").read()
        written[md_name(page)] = render(page, source)

    # llms-full.txt is every page in one fetch, for agents that would rather
    # take the whole site than walk it link by link
    full = [
        "# Mohammad Jafari — mohammad.page (full text)",
        "",
        "> Every page of mohammad.page concatenated as markdown, generated by",
        "> scripts/build_markdown.py. Individual pages live at the same path",
        "> with a .md extension, e.g. https://mohammad.page/about.md",
        "",
    ]
    for page in PAGES:
        full.append("")
        full.append("=" * 72)
        full.append("")
        full.append(written[md_name(page)].rstrip())
        full.append("")
    written["llms-full.txt"] = "\n".join(full).strip() + "\n"
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if any generated file is stale")
    ap.add_argument("--root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    args = ap.parse_args()

    written = build(args.root)
    stale = []
    for name, content in sorted(written.items()):
        path = os.path.join(args.root, name)
        current = io.open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if current == content:
            continue
        if args.check:
            stale.append(name)
        else:
            io.open(path, "w", encoding="utf-8").write(content)
            print("wrote %s (%d bytes)" % (name, len(content.encode("utf-8"))))

    if args.check:
        if stale:
            sys.stderr.write(
                "stale markdown twins: %s\nrun: python3 scripts/build_markdown.py\n"
                % ", ".join(stale))
            return 1
        print("all %d generated files are up to date" % len(written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
