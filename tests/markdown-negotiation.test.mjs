// Tests for the Accept: text/markdown negotiation logic in
// edge/markdown-negotiation.worker.js. Pure functions only, so this runs
// without a Cloudflare deployment: node --test tests/

import test from "node:test";
import assert from "node:assert/strict";

import {
  qualityFor,
  negotiate,
  markdownTwin
} from "../edge/markdown-negotiation.worker.js";

test("q-values: exact match beats wildcards", () => {
  const header = "text/markdown;q=0.9, text/*;q=0.5, */*;q=0.1";
  assert.equal(qualityFor(header, "text/markdown"), 0.9);
  // no exact text/html, so text/* applies
  assert.equal(qualityFor(header, "text/html"), 0.5);
  assert.equal(qualityFor(header, "application/pdf"), 0.1);
});

test("q-values: absent or empty Accept accepts everything", () => {
  assert.equal(qualityFor(null, "text/markdown"), 1);
  assert.equal(qualityFor("", "text/html"), 1);
});

test("q-values: missing q defaults to 1 and q=0 means unacceptable", () => {
  assert.equal(qualityFor("text/markdown", "text/markdown"), 1);
  assert.equal(qualityFor("text/html;q=0", "text/html"), 0);
});

test("q-values: unlisted type with no wildcard scores zero", () => {
  assert.equal(qualityFor("text/html", "text/markdown"), 0);
});

test("q-values: whitespace and casing are tolerated", () => {
  assert.equal(qualityFor("  TEXT/Markdown ; Q=0.7 ", "text/markdown"), 0.7);
});

test("negotiate: an explicit markdown request gets markdown", () => {
  assert.equal(negotiate("text/markdown"), "markdown");
  assert.equal(negotiate("text/markdown, text/html;q=0.5"), "markdown");
  assert.equal(negotiate("text/html;q=0.2, text/markdown;q=0.9"), "markdown");
});

test("negotiate: browsers keep getting HTML", () => {
  const chrome =
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif," +
    "image/webp,*/*;q=0.8";
  assert.equal(negotiate(chrome), "html");
  assert.equal(negotiate("*/*"), "html");
  assert.equal(negotiate(null), "html");
});

test("negotiate: a tie goes to HTML", () => {
  assert.equal(negotiate("text/markdown, text/html"), "html");
  assert.equal(negotiate("text/*"), "html");
});

test("negotiate: neither variant acceptable means 406", () => {
  assert.equal(negotiate("application/pdf"), "none");
  assert.equal(negotiate("text/html;q=0, text/markdown;q=0"), "none");
});

test("markdownTwin: documents map to their .md sibling", () => {
  assert.equal(markdownTwin("/"), "/index.md");
  assert.equal(markdownTwin("/about.html"), "/about.md");
  // GitHub Pages serves /about as well as /about.html
  assert.equal(markdownTwin("/about"), "/about.md");
  assert.equal(markdownTwin("/nested/"), "/nested/index.md");
});

test("markdownTwin: assets and feeds are left alone", () => {
  assert.equal(markdownTwin("/styles.css"), null);
  assert.equal(markdownTwin("/nav.js"), null);
  assert.equal(markdownTwin("/og.png"), null);
  assert.equal(markdownTwin("/feed.xml"), null);
  assert.equal(markdownTwin("/sitemap.xml"), null);
  assert.equal(markdownTwin("/about.md"), null);
});
