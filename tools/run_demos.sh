#!/bin/bash
set -e

echo "Running 1/3: Edit Implicit (Template + Contract)"
python tools/demo_card.py --mode edit --prompt-json tools/test_prompt_edit_implicit.json --out tools/demo_edit_implicit.png

echo "Running 2/3: Generate Explicit (Full Description, No Template)"
python tools/demo_card.py --mode generate --prompt-json tools/test_prompt_generate_explicit.json --out tools/demo_generate.png

echo "Running 3/3: Edit Explicit (Template + Manual Prompt)"
python tools/demo_card.py --mode edit --prompt-json tools/test_prompt_edit_explicit.json --out tools/demo_edit_explicit.png

echo "Done! Generated:"
echo "- tools/demo_edit_implicit.png"
echo "- tools/demo_generate.png"
echo "- tools/demo_edit_explicit.png"
