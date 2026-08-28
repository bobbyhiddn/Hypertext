#!/usr/bin/env bash
# batch_run.sh WORD:TYPE:RARITY ... - queue, plan (driver daemon answers), validate, census, self-heal render; one card at a time in order.
# Run driver_daemon.py against a designs module first so the plan prompts are answered.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
set -a; . ./.env; set +a
PY=${HYPERTEXT_PY:-python3}
SPOOL=${HYPERTEXT_TEXT_DRIVER_DIR:?set HYPERTEXT_TEXT_DRIVER_DIR to the driver spool directory}
for spec in "$@"; do
  IFS=: read -r WORD TYPE RARITY <<< "$spec"
  echo "=== BATCH $WORD ($TYPE $RARITY) ==="
  $PY - "$WORD" "$TYPE" "$RARITY" <<'PYEOF'
import sys, yaml
w, t, r = sys.argv[1:4]
p = 'series/2026-Q1/deck/queue.yml'; q = yaml.safe_load(open(p))
if not any(e.get('word') == w for e in q):
    q.append({'word': w, 'card_type': t, 'rarity': r}); yaml.safe_dump(q, open(p, 'w'), sort_keys=False)
print(f"queue: {w} at #{len(q):03d}")
PYEOF
  HYPERTEXT_TEXT_DRIVER_DIR=$SPOOL timeout 1800 $PY -m hypertext.pipeline.daily --phase plan --series series/2026-Q1 --auto > /tmp/plan-$WORD.log 2>&1 || { echo "$WORD: PLAN FAILED"; tail -3 /tmp/plan-$WORD.log; continue; }
  CD=$(ls -dt series/2026-Q1/cards/*/ | head -1); CD=${CD%/}
  echo "$WORD: planned $CD"
  $PY -m hypertext.cards.validate "$PWD/$CD/card.json" 2>&1 | tail -1
  $PY - "$TYPE" "$RARITY" <<'PYEOF'
import json, sys
t, r = sys.argv[1:3]
p = 'schema/babel_template_matrix.json'; m = json.load(open(p))
for c in m['valid_combinations']:
    if c['type'] == t and c['rarity'] == r:
        c['card_count'] += 1; print(f"census {t}/{r} -> {c['card_count']}")
json.dump(m, open(p, 'w'), indent=2); open(p, 'a').write('\n')
PYEOF
  REGEN=1 scripts/pipeline/selfheal.sh "$(basename $CD)"
done
echo "BATCH DONE"
