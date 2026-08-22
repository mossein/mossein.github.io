# mohammad.page

The source of [mohammad.page](https://mohammad.page/) — a hand-written static
site served by GitHub Pages. No framework, no build step for the HTML: the
pages are the source.

## Layout

| what | where |
| --- | --- |
| pages | `*.html` at the repo root |
| styles | `styles.css` |
| nav, theme switch, scroll effects | `nav.js` |
| markdown twins of every page | `*.md`, generated |
| agent-facing indexes | `llms.txt`, `llms-full.txt`, `agents.md` |
| crawler files | `robots.txt`, `sitemap.xml`, `feed.xml` |
| optional edge layer | `edge/` |
| checks | `tests/` |

## Editing a page

Edit the HTML, then regenerate the markdown twins:

```
python3 scripts/build_markdown.py
```

Every page has a `.md` sibling (`/about.html` -> `/about.md`) so agents can read
the content without parsing HTML. The twins are generated from the HTML, so
they never drift — but they do go stale if you forget to rerun the script. CI
fails on stale twins, and so does `scripts/build_markdown.py --check`.

New page? Add it to `PAGES` in `scripts/build_markdown.py`, to `sitemap.xml`,
and to the right section of `llms.txt`.

## Checks

```
python3 scripts/build_markdown.py --check   # twins match the html
python3 -m unittest discover -s tests -v    # structure, llms.txt, 404, schema
node --test                                 # edge negotiation logic
```

Against a running site:

```
python3 tests/serve_local.py 8000 &         # emulates GitHub Pages routing
tests/verify_live.sh http://127.0.0.1:8000
tests/verify_live.sh                        # or the deployed site
```

CI runs the first three on every push (`.github/workflows/agent-readiness.yml`).

## Agent readiness

The site is built to be read by agents as well as people:

- **Markdown twins** at `/<page>.md`, advertised from each page with
  `<link rel="alternate" type="text/markdown">`.
- **`/llms.txt`** ([llmstxt.org](https://llmstxt.org)) — what the site holds,
  when to use it, and what it is not for.
- **`/agents.md`** — the long form: when to use, when not to, how to fetch,
  how to cite.
- **`/llms-full.txt`** — every page in one request.
- **Real 404s** with a markdown recovery body pointing at the above.
- **One schema.org entity** — every page's `Person` markup resolves to
  `https://mohammad.page/#person`.

`Accept: text/markdown` negotiation and `Vary: Accept` are the one piece that
cannot live here: GitHub Pages is a file host and never sees the request's
`Accept` header. `edge/` holds a ready-to-deploy Cloudflare Worker that adds
it in front of the origin — see [`edge/README.md`](edge/README.md).
