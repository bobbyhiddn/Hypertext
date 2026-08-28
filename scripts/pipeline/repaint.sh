#!/usr/bin/env bash
# repaint.sh SLUG... - repaint only the illustration (per card.json ART_PROMPT) via image-only revise, then fixed elements, gate, grade.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
set -a; . ./.env; set +a
PY=${HYPERTEXT_PY:-python3}; HX=${HYPERTEXT_HX:-hypertext}
for slug in "$@"; do
  CD=series/2026-Q1/cards/$slug
  echo "=== REPAINT $slug ==="
  art=$($PY -c "import json; print(json.load(open('$CD/card.json'))['content']['ART_PROMPT'])")
  corr="Repaint ONLY the illustration inside the art window as a luminous full-color cinematic oil painting with impressionistic brushwork, deep shadowed background, one radiant golden light source, rich saturated blues and golds - no sepia, no monochrome, no engraving or line art - depicting: $art. Keep the frame, header, stats, ability, verses, language panels, trivia, and footer exactly as rendered, pixel for pixel."
  ok=0
  for t in 1 2 3; do
    timeout 900 $PY -m hypertext.pipeline.daily --phase revise --card-dir $CD --image-only --revision "$corr" >/dev/null 2>&1 || true
    $HX fixed-elements --card-dir $CD >/dev/null 2>&1 || true
    $HX visual-gate --card-dir $CD >/dev/null 2>&1 || { echo "$slug p$t: gate fail"; continue; }
    out=$(timeout 900 $PY -m hypertext.pipeline.daily --phase grade --card-dir $CD --style-series series/2026-Q1 2>&1)
    echo "$slug p$t: $(echo "$out" | grep -o 'Final Score: [0-9]*' | head -1)"
    if echo "$out" | grep -q 'Status: PASS'; then echo "$slug: REPAINT PASS (p$t)"; ok=1; break; fi
  done
  [ "$ok" = "1" ] || echo "$slug: REPAINT EXHAUSTED"
done
echo "REPAINT DONE"
