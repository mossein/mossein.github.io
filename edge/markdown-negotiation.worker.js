/**
 * Accept: text/markdown negotiation for mohammad.page (acceptmarkdown.com).
 *
 * The site itself is static on GitHub Pages, which serves files and nothing
 * else: it cannot read the request's Accept header and it cannot add a Vary
 * header. So negotiation has to happen in front of the origin. Put this worker
 * on the zone and it does three things and no more:
 *
 *   1. serves the pre-built markdown twin (/about.html -> /about.md) when the
 *      client prefers text/markdown,
 *   2. sets `Vary: Accept` on every negotiable response, so a cache can never
 *      hand the HTML variant to an agent that asked for markdown,
 *   3. answers 406 when the client accepts neither markdown nor HTML.
 *
 * Everything else — assets, redirects, status codes — passes through
 * untouched. A missing twin falls back to HTML rather than 404ing.
 *
 * See edge/README.md for deployment. This file is inert until deployed.
 */

const MARKDOWN = "text/markdown";
const HTML = "text/html";

/**
 * Quality value the Accept header assigns to one media type, honouring
 * `type/*` and `*​/*` wildcards. RFC 9110 §12.5.1: the most specific match
 * wins, an absent Accept means everything is acceptable, and q=0 means
 * "not acceptable".
 *
 * @param {string|null} header raw Accept header
 * @param {string} mediaType e.g. "text/markdown"
 * @returns {number} q in [0, 1]
 */
export function qualityFor(header, mediaType) {
  if (header === null || header === undefined || header.trim() === "") {
    return 1;
  }
  const [type, subtype] = mediaType.split("/");
  // specificity: exact type beats type/*, which beats */*
  let best = { specificity: -1, q: 0 };

  for (const part of header.split(",")) {
    const segments = part.trim().split(";");
    const range = segments.shift().trim().toLowerCase();
    if (!range) continue;

    let q = 1;
    for (const segment of segments) {
      const [name, value] = segment.split("=");
      if (name && name.trim().toLowerCase() === "q") {
        const parsed = parseFloat(value);
        q = Number.isNaN(parsed) ? 1 : Math.min(Math.max(parsed, 0), 1);
      }
    }

    let specificity;
    if (range === type + "/" + subtype) specificity = 2;
    else if (range === type + "/*") specificity = 1;
    else if (range === "*/*") specificity = 0;
    else continue;

    if (specificity > best.specificity) {
      best = { specificity, q };
    }
  }
  return best.q;
}

/**
 * @param {string|null} header raw Accept header
 * @returns {"markdown"|"html"|"none"} what to serve
 */
export function negotiate(header) {
  const md = qualityFor(header, MARKDOWN);
  const html = qualityFor(header, HTML);
  if (md === 0 && html === 0) return "none";
  // ties go to HTML: browsers send */* and must keep getting the real page
  return md > html ? "markdown" : "html";
}

/**
 * Map a document path to its markdown twin. Returns null for anything that
 * isn't a document (assets, feeds, the markdown files themselves).
 *
 * @param {string} pathname
 * @returns {string|null}
 */
export function markdownTwin(pathname) {
  if (pathname === "/" || pathname === "") return "/index.md";
  if (pathname.endsWith("/")) return pathname + "index.md";
  if (pathname.endsWith(".html")) return pathname.slice(0, -".html".length) + ".md";
  // extensionless paths are the same documents; GitHub Pages serves both
  if (!/\.[a-z0-9]+$/i.test(pathname)) return pathname + ".md";
  return null;
}

function withVary(response) {
  const headers = new Headers(response.headers);
  const existing = headers.get("Vary");
  const values = existing ? existing.split(",").map((v) => v.trim()) : [];
  if (!values.some((v) => v.toLowerCase() === "accept")) {
    values.push("Accept");
  }
  headers.set("Vary", values.join(", "));
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers
  });
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const twin = markdownTwin(url.pathname);

    // not a document: leave assets, images and feeds exactly as they are
    if (twin === null) {
      return fetch(request);
    }

    const accept = request.headers.get("Accept");
    const choice = negotiate(accept);

    if (choice === "none") {
      return withVary(
        new Response(
          "406 Not Acceptable\n\n" +
            "This URL can be served as text/html or text/markdown.\n" +
            "See https://mohammad.page/llms.txt\n",
          {
            status: 406,
            headers: { "Content-Type": "text/plain; charset=utf-8" }
          }
        )
      );
    }

    if (choice === "markdown") {
      const mdUrl = new URL(url.toString());
      mdUrl.pathname = twin;
      const md = await fetch(new Request(mdUrl.toString(), {
        method: request.method,
        headers: request.headers
      }));
      if (md.ok) {
        const headers = new Headers(md.headers);
        headers.set("Content-Type", "text/markdown; charset=utf-8");
        headers.set("Content-Location", twin);
        return withVary(new Response(md.body, { status: md.status, headers }));
      }
      // no twin for this path — fall through to HTML rather than invent a 404
    }

    return withVary(await fetch(request));
  }
};
