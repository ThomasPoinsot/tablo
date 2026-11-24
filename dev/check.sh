#!/usr/bin/env bash
# Vérifications de Tablo : syntaxe JS, décodeur vocal, captures d'écran multi-tailles.
# Usage : dev/check.sh [dossier_sortie]   (par défaut /tmp/tablo-test)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-/tmp/tablo-test}"
mkdir -p "$OUT"

echo "== Syntaxe JS"
python3 - "$ROOT/tablo.html" "$OUT" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
for i, js in enumerate(re.findall(r"<script>(.*?)</script>", s, re.S)):
    open(f"{sys.argv[2]}/script{i}.js", "w", encoding="utf-8").write(js)
js = re.findall(r"<script>(.*?)</script>", s, re.S)[-1]
start, end = js.index("const WORDS"), js.index("const voice =")
open(f"{sys.argv[2]}/parser_test.js", "w", encoding="utf-8").write(js[start:end] + r"""
const T = {"56":56,"cinquante-six":56,"vingt et un":21,"soixante-dix-sept":77,"quatre-vingts":80,
  "quatre-vingt-dix-neuf":99,"dix-huit":18,"deux cent cinquante":250,"mille":1000,"1 000":1000,
  "sept fois huit cinquante six":56,"cent":100,"quatorze":14,"trois cent cinquante":350,
  "soixante et onze":71,"heu":null,"neuf":9};
let bad = 0;
for (const [k, v] of Object.entries(T)) { const r = parseFrNumber(k); if (r !== v) { bad++; console.log("ÉCHEC", k, "->", r, "attendu", v); } }
console.log(bad ? bad + " échec(s)" : "décodeur vocal OK");
if (bad) process.exit(1);
""")
PY
for f in "$OUT"/script*.js; do node --check "$f"; done && echo "syntaxe OK"

echo "== Décodeur vocal"
node "$OUT/parser_test.js"

echo "== Captures"
python3 "$ROOT/dev/make_test_pages.py" "$OUT" >/dev/null
CHROME="$(command -v google-chrome || command -v chromium)"
for v in kids menu setup prog game csetup cprog cgame; do
  for w in 375x667 820x1180 1366x768; do
    rm -rf "$OUT/prof_$v$w"
    "$CHROME" --headless=new --disable-gpu --no-sandbox --user-data-dir="$OUT/prof_$v$w" --hide-scrollbars \
      --window-size="${w/x/,}" --virtual-time-budget=3000 --screenshot="$OUT/s_${v}_$w.png" "file://$OUT/v_$v.html" 2>/dev/null &
  done
done
wait
rm -rf "$OUT"/prof_*
ls "$OUT"/s_*.png
