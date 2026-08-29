#!/usr/bin/env bash
# selfheal.sh SLUG... - render loop: rebuild -> visual gate -> voted grade -> single-defect image-only fix, up to 6 attempts per card.
# REGEN=1 regenerates prompt.txt on the first attempt (required after descriptor changes).
# Requires: .env with GEMINI_API_KEY, HYPERTEXT_PY (python with the package installed), HYPERTEXT_HX (hypertext CLI).
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
set -a; . ./.env; set +a
PY=${HYPERTEXT_PY:-python3}; HX=${HYPERTEXT_HX:-hypertext}
command -v "$HX" >/dev/null 2>&1 || { echo "HYPERTEXT_HX is not an executable hypertext CLI: $HX (every gate would fail as 'pip fail')" >&2; exit 2; }
for slug in "$@"; do
  CD=series/2026-Q1/cards/$slug
  echo "=== CARD $slug ==="
  for a in 1 2 3 4 5 6; do
    RP=""; [ "$a" = "1" ] && [ "${REGEN:-0}" = "1" ] && RP="--regen-prompt"
    timeout 900 $PY -m hypertext.pipeline.daily --phase rebuild --card-dir $CD $RP >/dev/null 2>&1 || true
    $HX fixed-elements --card-dir $CD >/dev/null 2>&1 || true
    $HX visual-gate --card-dir $CD >/dev/null 2>&1 || { echo "$slug a$a: pip fail"; continue; }
    out=$(timeout 900 $PY -m hypertext.pipeline.daily --phase grade --card-dir $CD --style-series series/2026-Q1 2>&1)
    score=$(echo "$out" | grep -o 'Final Score: [0-9]*' | head -1)
    mkdir -p $CD/outputs/grades; cp $CD/grade.txt $CD/outputs/grades/a$a.txt 2>/dev/null   # keep every attempt's verdict; grade.txt is overwritten
    echo "$slug a$a: pips ok, $score"
    if echo "$out" | grep -q 'Status: PASS'; then echo "$slug: FULL PASS (a$a)"; break; fi
    corr=$(grep -A2 'Corrections Needed' $CD/grade.txt 2>/dev/null | sed -n 2p | sed 's/^ *- *//')
    n=$(grep -A6 'Corrections Needed' $CD/grade.txt 2>/dev/null | grep -c '^ *-')
    # Fix-mode for a single correction at score >= 90, or - at any score - when
    # the single correction is the figure rule (an art-panel repaint fixes it;
    # a full re-render just rolls the dice on the same subject again).
    figure=0; echo "$corr" | grep -qi "no figure faces the viewer" && figure=1
    if [ "$n" = "1" ] && [ -n "$corr" ] && { [ "${score#Final Score: }" -ge 90 ] 2>/dev/null || [ "$figure" = "1" ]; }; then
      echo "$slug a$a: single defect, fix-mode: $corr"
      timeout 900 $PY -m hypertext.pipeline.daily --phase revise --card-dir $CD --image-only --revision "Visual fix only, change nothing except this single correction: $corr Keep every other pixel, panel, and text exactly as rendered." >/dev/null 2>&1 || true
      $HX fixed-elements --card-dir $CD >/dev/null 2>&1 || true
      $HX visual-gate --card-dir $CD >/dev/null 2>&1 || { echo "$slug a$a: post-fix pip fail"; continue; }
      out=$(timeout 900 $PY -m hypertext.pipeline.daily --phase grade --card-dir $CD --style-series series/2026-Q1 2>&1)
      cp $CD/grade.txt $CD/outputs/grades/a$a-fix.txt 2>/dev/null
      echo "$slug a$a-fix: $(echo "$out" | grep -o 'Final Score: [0-9]*' | head -1)"
      if echo "$out" | grep -q 'Status: PASS'; then echo "$slug: FULL PASS (a$a+fix)"; break; fi
    fi
  done
done
echo "SELFHEAL DONE"
