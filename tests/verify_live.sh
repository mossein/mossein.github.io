#!/usr/bin/env bash
# Verify the deployed site's public endpoints and machine-readable files.
#
#   tests/verify_live.sh                       # against https://mohammad.page
#   tests/verify_live.sh https://other.host    # against somewhere else
#
# Exits non-zero if any required endpoint is wrong. The Accept-negotiation
# section is reported but not enforced: GitHub Pages cannot negotiate, so it
# only passes once the Cloudflare worker in edge/ is deployed (see
# edge/README.md).

set -u

BASE="${1:-https://mohammad.page}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAILED=0
CURL=(curl -sS --max-time 20 --location --write-out '%{http_code} %{content_type}')

pass() { printf '  ok    %s\n' "$1"; }
fail() { printf '  FAIL  %s\n' "$1"; FAILED=$((FAILED + 1)); }
note() { printf '  note  %s\n' "$1"; }

status_of() { curl -sS --max-time 20 -o /dev/null -w '%{http_code}' "$1"; }
ctype_of()  { curl -sS --max-time 20 -o /dev/null -w '%{content_type}' "$1"; }

expect_status() { # url expected label
  local got
  got="$(status_of "$1")"
  if [ "$got" = "$2" ]; then pass "$3 -> $got"; else fail "$3 -> $got (want $2)"; fi
}

echo "verifying $BASE"

echo
echo "1. agent-friendly 404s"
expect_status "$BASE/some-path-that-does-not-exist" 404 "missing path"
expect_status "$BASE/another/missing/one" 404 "missing nested path"
body="$(curl -sS --max-time 20 "$BASE/some-path-that-does-not-exist")"
for marker in "llms.txt" "sitemap.xml" "agents.md" "## 404"; do
  case "$body" in
    *"$marker"*) pass "404 body mentions $marker" ;;
    *)           fail "404 body is missing $marker" ;;
  esac
done
expect_status "$BASE/404.md" 200 "404.md"

echo
echo "2. markdown twins and content type"
while IFS= read -r md; do
  url="$BASE/$md"
  got="$(status_of "$url")"
  ct="$(ctype_of "$url")"
  if [ "$got" != "200" ]; then
    fail "$md -> $got"
  elif case "$ct" in text/markdown*|text/plain*) false ;; *) true ;; esac; then
    fail "$md served as $ct (want text/markdown or text/plain)"
  else
    pass "$md -> 200 $ct"
  fi
done < <(cd "$ROOT" && ls *.md)

echo
echo "3. Accept: text/markdown negotiation (acceptmarkdown.com)"
neg_ct="$(curl -sS --max-time 20 -o /dev/null -w '%{content_type}' \
  -H 'Accept: text/markdown' "$BASE/about")"
neg_vary="$(curl -sS --max-time 20 -o /dev/null -D - \
  -H 'Accept: text/markdown' "$BASE/about" | tr 'A-Z' 'a-z' \
  | awk -F': ' '/^vary:/ {print $2}' | tr -d '\r')"
case "$neg_ct" in
  text/markdown*) pass "Accept: text/markdown -> $neg_ct" ;;
  *) note "Accept: text/markdown -> $neg_ct (static host cannot negotiate; deploy edge/)" ;;
esac
case "$neg_vary" in
  *accept,*|*accept) pass "Vary: $neg_vary" ;;
  *) note "Vary: ${neg_vary:-<none>} (needs the edge worker; see edge/README.md)" ;;
esac
note "meanwhile agents are told to fetch the .md URL directly (llms.txt, agents.md)"

echo
echo "4. trust anchor pages"
for page in about contact privacy; do
  expect_status "$BASE/$page" 200 "/$page"
  expect_status "$BASE/$page.html" 200 "/$page.html"
  chars="$(curl -sS --max-time 20 "$BASE/$page.md" | tr -d '[:space:]' | wc -c | tr -d ' ')"
  if [ "$chars" -ge 500 ]; then
    pass "/$page.md has $chars chars"
  else
    fail "/$page.md has only $chars chars (want 500+)"
  fi
done

echo
echo "5. machine-readable entry points"
for file in llms.txt llms-full.txt agents.md robots.txt sitemap.xml feed.xml; do
  expect_status "$BASE/$file" 200 "/$file"
done
curl -sS --max-time 20 "$BASE/llms.txt" | head -1 | grep -q '^# ' \
  && pass "llms.txt opens with an H1" || fail "llms.txt does not open with an H1"
curl -sS --max-time 20 "$BASE/llms.txt" | grep -qi '^## when to use this' \
  && pass "llms.txt has a when-to-use section" \
  || fail "llms.txt has no when-to-use section"

echo
if [ "$FAILED" -eq 0 ]; then
  echo "all required checks passed"
else
  echo "$FAILED check(s) failed"
fi
exit "$FAILED"
