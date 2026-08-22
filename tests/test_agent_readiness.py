#!/usr/bin/env python3
"""Checks for the machine-readable surface of mohammad.page.

Everything here runs against the files in the repo, so it works before a
deploy. `tests/verify_live.sh` covers the parts that only exist once the site
is served (status codes, content types).

    python3 -m unittest discover -s tests -v
"""

import io
import json
import os
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from build_markdown import PAGES, md_name  # noqa: E402

SITE = "https://mohammad.page/"
TRUST_PAGES = ["about.html", "contact.html", "privacy.html"]
MIN_TRUST_CHARS = 500


def read(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def exists(name):
    return os.path.exists(os.path.join(ROOT, name))


class TextOnly(HTMLParser):
    """Visible text: no scripts, styles, or markup."""

    def __init__(self):
        HTMLParser.__init__(self)
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        return " ".join("".join(self.parts).split())


def visible_text(html_source):
    parser = TextOnly()
    parser.feed(html_source)
    return parser.text()


def json_ld_blocks(html_source):
    return re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html_source, re.S)


def local_path_for(url):
    """Map a mohammad.page URL to the repo file that answers it."""
    if not url.startswith(SITE):
        return None
    path = url[len(SITE):].split("#")[0].split("?")[0]
    if path == "":
        return "index.html"
    return path


class TrustAnchorPages(unittest.TestCase):
    """/about, /contact and /privacy are what an agent checks first."""

    def test_pages_exist(self):
        for page in TRUST_PAGES:
            self.assertTrue(exists(page), "%s is missing" % page)

    def test_pages_have_real_content(self):
        for page in TRUST_PAGES:
            body = visible_text(read(page))
            self.assertGreaterEqual(
                len(body), MIN_TRUST_CHARS,
                "%s has %d chars of visible text, needs %d"
                % (page, len(body), MIN_TRUST_CHARS))

    def test_pages_are_indexable_and_canonical(self):
        for page in TRUST_PAGES:
            source = read(page)
            self.assertIn(
                '<link rel="canonical" href="%s%s" />' % (SITE, page), source,
                "%s needs a self-referencing canonical" % page)
            self.assertNotIn("noindex", source,
                             "%s must stay indexable" % page)
            self.assertIn("<title>", source)
            self.assertRegex(source, r'<meta\s+name="description"')

    def test_pages_carry_parseable_structured_data(self):
        expected = {
            "about.html": "AboutPage",
            "contact.html": "ContactPage",
            "privacy.html": "WebPage",
        }
        for page in TRUST_PAGES:
            blocks = json_ld_blocks(read(page))
            self.assertTrue(blocks, "%s has no JSON-LD" % page)
            types = []
            for block in blocks:
                data = json.loads(block)  # raises if the JSON-LD is malformed
                types.append(data.get("@type"))
            self.assertIn(expected[page], types,
                          "%s should declare %s" % (page, expected[page]))

    def test_contact_details_are_consistent(self):
        """Same name, email and city everywhere, or agents can't match them."""
        for page in TRUST_PAGES:
            source = read(page)
            self.assertIn("mohammad jafari", visible_text(source).lower())
        for page in ("about.html", "contact.html"):
            self.assertIn("me@mohammad.page", read(page))
            self.assertIn("toronto", visible_text(read(page)).lower())

    def test_pages_are_reachable_from_the_home_page(self):
        home = read("index.html")
        for page in TRUST_PAGES:
            self.assertIn('href="%s"' % page, home,
                          "%s is not linked from index.html" % page)

    def test_pages_are_in_the_sitemap(self):
        sitemap = read("sitemap.xml")
        for page in TRUST_PAGES:
            self.assertIn("%s%s" % (SITE, page), sitemap,
                          "%s is missing from sitemap.xml" % page)


class MarkdownTwins(unittest.TestCase):
    """Every page an agent might read exists as markdown at a stable URL."""

    def test_every_page_has_a_twin(self):
        for page in PAGES:
            self.assertTrue(exists(md_name(page)),
                            "%s has no markdown twin" % page)

    def test_twins_are_up_to_date(self):
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "build_markdown.py"),
             "--check"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(
            result.returncode, 0,
            "markdown twins are stale:\n%s" % (result.stderr or result.stdout))

    def test_html_advertises_its_twin(self):
        for page in PAGES:
            expected = ('<link rel="alternate" type="text/markdown" '
                        'href="%s%s" />' % (SITE, md_name(page)))
            self.assertIn(expected, read(page),
                          "%s does not advertise %s" % (page, md_name(page)))

    def test_twins_open_with_a_heading_and_a_source_line(self):
        for page in PAGES:
            twin = read(md_name(page))
            self.assertTrue(twin.startswith("# "),
                            "%s should open with an H1" % md_name(page))
            self.assertIn("Source: ", twin,
                          "%s should name its HTML source" % md_name(page))

    def test_full_text_bundle_covers_every_page(self):
        full = read("llms-full.txt")
        for page in PAGES:
            first_line = read(md_name(page)).splitlines()[0]
            self.assertIn(first_line, full,
                          "llms-full.txt is missing %s" % md_name(page))

    def test_nojekyll_keeps_markdown_served_verbatim(self):
        """Without this, GitHub Pages may hand .md files to Jekyll."""
        self.assertTrue(exists(".nojekyll"))


class LlmsTxt(unittest.TestCase):
    """llms.txt follows llmstxt.org and says when to use the site."""

    def setUp(self):
        self.source = read("llms.txt")
        self.lines = self.source.splitlines()

    def test_starts_with_an_h1_then_a_blockquote_summary(self):
        self.assertTrue(self.lines[0].startswith("# "),
                        "llms.txt must open with a single H1")
        summary = [ln for ln in self.lines[1:8] if ln.startswith("> ")]
        self.assertTrue(summary, "llms.txt needs a blockquote summary")
        self.assertGreater(len(summary[0]), 80,
                           "the summary should actually describe the site")

    def test_has_exactly_one_h1(self):
        h1s = [ln for ln in self.lines if re.match(r"^# [^#]", ln)]
        self.assertEqual(len(h1s), 1, "llms.txt must have exactly one H1")

    def test_sections_are_h2(self):
        for line in self.lines:
            if line.startswith("#"):
                self.assertRegex(
                    line, r"^(# |## )",
                    "only H1 and H2 headings belong in llms.txt: %r" % line)

    def test_names_when_to_use_the_site(self):
        lowered = self.source.lower()
        self.assertIn("## when to use this", lowered,
                      "llms.txt needs a when-to-use section")
        self.assertIn("poor fits", lowered,
                      "when-to-use should say what the site is not for")

    def test_link_lines_are_well_formed(self):
        pattern = re.compile(r"^- \[[^\]]+\]\([^)]+\)(: .+)?$")
        for line in self.lines:
            if line.startswith("- ["):
                self.assertRegex(
                    line, pattern,
                    "link list entries are `- [name](url): notes`: %r" % line)

    def test_every_linked_file_exists(self):
        for _, url in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", self.source):
            local = local_path_for(url)
            if local is None:
                continue
            self.assertTrue(exists(local),
                            "llms.txt links %s, which does not exist" % url)

    def test_lists_every_markdown_twin(self):
        for page in PAGES:
            self.assertIn("%s%s" % (SITE, md_name(page)), self.source,
                          "llms.txt does not list %s" % md_name(page))

    def test_explains_how_to_fetch_markdown(self):
        lowered = self.source.lower()
        self.assertIn("llms-full.txt", lowered)
        self.assertIn(".md", lowered)


class AgentInstructions(unittest.TestCase):
    """agents.md is the long-form when-to-use guidance."""

    def setUp(self):
        self.source = read("agents.md")

    def test_exists_with_substance(self):
        self.assertGreater(len(self.source), MIN_TRUST_CHARS)

    def test_has_a_when_to_use_section(self):
        self.assertIn("## When to use this", self.source)
        self.assertIn("## When not to use this", self.source)

    def test_says_how_to_fetch_and_cite(self):
        self.assertIn("## How to fetch", self.source)
        self.assertIn("## How to cite", self.source)
        self.assertIn("llms-full.txt", self.source)

    def test_is_linked_from_llms_txt(self):
        self.assertIn("%sagents.md" % SITE, read("llms.txt"))

    def test_every_linked_file_exists(self):
        for _, url in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", self.source):
            local = local_path_for(url)
            if local is None:
                continue
            self.assertTrue(exists(local),
                            "agents.md links %s, which does not exist" % url)


class NotFoundPage(unittest.TestCase):
    """A 404 an agent can recover from without guessing."""

    def setUp(self):
        self.source = read("404.html")

    def test_recovery_block_is_present(self):
        self.assertIn('id="agent-recovery"', self.source)

    def test_recovery_block_is_markdown(self):
        block = re.search(r'id="agent-recovery"[^>]*>(.*?)</pre>',
                          self.source, re.S).group(1)
        self.assertIn("## 404", block, "the block should read as markdown")
        links = re.findall(r"^- \[([^\]]+)\]\(([^)]+)\)", block, re.M)
        self.assertGreaterEqual(len(links), 5,
                                "point agents at more than one place")

    def test_recovery_block_points_at_the_machine_readable_entry_points(self):
        block = re.search(r'id="agent-recovery"[^>]*>(.*?)</pre>',
                          self.source, re.S).group(1)
        for target in ("llms.txt", "sitemap.xml", "agents.md",
                       "llms-full.txt"):
            self.assertIn(target, block,
                          "the 404 body should mention %s" % target)

    def test_recovery_links_resolve(self):
        block = re.search(r'id="agent-recovery"[^>]*>(.*?)</pre>',
                          self.source, re.S).group(1)
        for _, url in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", block):
            local = local_path_for(url)
            if local is None:
                continue
            self.assertTrue(exists(local),
                            "the 404 body links %s, which does not exist" % url)

    def test_markdown_form_of_the_404_matches_the_html(self):
        md = read("404.md")
        block = re.search(r'id="agent-recovery"[^>]*>(.*?)</pre>',
                          self.source, re.S).group(1)
        html_links = set(re.findall(r"\[([^\]]+)\]\(([^)]+)\)", block))
        md_links = set(re.findall(r"\[([^\]]+)\]\(([^)]+)\)", md))
        self.assertTrue(
            html_links.issubset(md_links),
            "404.md is missing links the 404 page offers: %s"
            % sorted(html_links - md_links))

    def test_stays_out_of_the_index(self):
        self.assertIn('content="noindex, nofollow"', self.source)

    def test_visual_page_is_untouched(self):
        """The snake game and the human-facing copy still ship."""
        self.assertIn('id="snake"', self.source)
        self.assertIn("page not found", self.source)


class CrawlerEntryPoints(unittest.TestCase):

    def test_robots_allows_crawling_and_points_at_the_indexes(self):
        robots = read("robots.txt")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: %ssitemap.xml" % SITE, robots)
        self.assertIn("%sllms.txt" % SITE, robots)

    def test_sitemap_is_valid_and_every_url_resolves(self):
        tree = ET.fromstring(read("sitemap.xml"))
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        locs = [el.text for el in tree.iter(ns + "loc")]
        self.assertTrue(locs)
        for loc in locs:
            local = local_path_for(loc)
            self.assertIsNotNone(local, "%s is off-domain" % loc)
            self.assertTrue(exists(local),
                            "sitemap lists %s, which does not exist" % loc)

    def test_structured_data_parses_on_every_page(self):
        for page in PAGES + ["404.html"]:
            for block in json_ld_blocks(read(page)):
                try:
                    json.loads(block)
                except ValueError as exc:
                    self.fail("invalid JSON-LD in %s: %s" % (page, exc))


if __name__ == "__main__":
    unittest.main(verbosity=2)
