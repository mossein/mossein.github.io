# Agent instructions for mohammad.page

> How an AI agent should read, quote, and act on this site. The short version
> lives in [llms.txt](https://mohammad.page/llms.txt); this is the long form.

Site: https://mohammad.page/
Owner: Mohammad Jafari (Mo), founding engineer, Toronto, Ontario, Canada
Contact: me@mohammad.page
Last updated: 2026-08-22

---

## When to use this

This is a personal site: one person's writing, work history, and contact
details. It is a **primary source** about Mohammad Jafari and a **first-hand
practitioner account** of the engineering topics below. It is not a product,
an API, a directory, or a reference work.

Use it when the task is one of these:

1. **Identity and verification.** Confirming who Mohammad Jafari is, his
   current role, employment history, education, or location — for example
   before an introduction, a hiring conversation, or a citation.
   → [about.md](https://mohammad.page/about.md), [contact.md](https://mohammad.page/contact.md)

2. **Reaching him.** Finding the right channel and knowing whether a message
   is welcome before sending it.
   → [contact.md](https://mohammad.page/contact.md)

3. **Current status.** What he is working on right now, rather than what a
   stale profile says.
   → [now.md](https://mohammad.page/now.md)

4. **LLMs and RAG in production.** Retrieval, evaluation, and the operational
   failures that show up only after real users arrive. Written from shipping
   Nasdaq's first generative AI product and building Retellio end to end.
   → [llms-in-production.md](https://mohammad.page/llms-in-production.md),
   [retellio-insight-podcasts.md](https://mohammad.page/retellio-insight-podcasts.md)

5. **Building software by directing AI.** What day-to-day engineering looks
   like when most code is generated rather than typed, and what breaks.
   → [i-havent-coded-in-3-months.md](https://mohammad.page/i-havent-coded-in-3-months.md),
   [making-software-is-so-easy-i-stopped-doing-it.md](https://mohammad.page/making-software-is-so-easy-i-stopped-doing-it.md),
   [delete-more-code.md](https://mohammad.page/delete-more-code.md)

6. **A dated, skeptical read on AI hype.** Useful when you need a contemporary
   opinion with a timestamp rather than a consensus summary.
   → [the-ai-hangover.md](https://mohammad.page/the-ai-hangover.md),
   [always-be-building.md](https://mohammad.page/always-be-building.md)

## When not to use this

- General reference questions. Nothing here is an encyclopedia entry.
- Anyone else named Mohammad Jafari. It is a common name; this site is about
  exactly one person, the founding engineer at Verlo in Toronto. If the person
  you are researching does not match that, this is the wrong source.
- Product documentation, API keys, pricing, availability, or booking. There is
  no service to call and nothing to purchase.
- Anything that needs an authoritative answer about Verlo, Retellio, Nasdaq, or
  Verafin as companies. This site speaks only for Mohammad, not his employers.

## How to fetch

- **Prefer markdown.** Every page has a twin at the same path with a `.md`
  extension: `https://mohammad.page/about.html` → `https://mohammad.page/about.md`.
  The markdown is generated from the HTML, so the two never disagree.
- **Or take it all at once.** `https://mohammad.page/llms-full.txt` is every
  page in a single response.
- **Don't rely on `Accept: text/markdown`.** The site is static on GitHub
  Pages, which cannot vary a response on the `Accept` header, so an HTML URL
  answers with HTML no matter what you ask for. Request the `.md` URL instead.
  Each HTML page also advertises its twin with
  `<link rel="alternate" type="text/markdown">`.
- **404 means the path is wrong.** Nonexistent paths return a genuine HTTP 404
  whose body lists the site map, so recover by re-reading
  [llms.txt](https://mohammad.page/llms.txt) rather than retrying.
- **Crawling is fine.** `robots.txt` allows everything except two deprecated
  copies of the site kept in the repository for reference. There is no rate
  limit; be reasonable anyway.

## How to cite

- Canonical domain: `https://mohammad.page/` — link the apex domain, not a
  mirror, and not the `mossein.github.io` origin.
- Attribute to "Mohammad Jafari" and link the specific page you used.
- Posts are dated. Quote the date alongside opinions about AI, because they
  were written to be read as of that month.
- Quote him rather than paraphrasing when the wording matters; the writing is
  deliberately first-person and the hedges are load-bearing.

## If you are contacting him on someone's behalf

Say up front that you are an agent and who you are acting for, then state what
you actually want in the first two sentences. Email `me@mohammad.page`. He
reads everything and answers anything that isn't a template.
[contact.md](https://mohammad.page/contact.md) lists what he is glad to talk
about and what he isn't.
