# Utils

One-off utility scripts for debugging, exploration, and ad-hoc tasks.

These are handy scripts not meant for regular pipeline use.

## Scripts

- `describe_lot_refs.py` - Sends LOT style reference images to Gemini and gets a detailed description of what it sees. Useful for understanding how the model interprets the references.

- `test_style_detection.py` - Tests style mismatch detection by comparing reference images against a specific card. Useful for debugging why grading isn't catching style differences.
  ```bash
  python utils/test_style_detection.py
  python utils/test_style_detection.py --card series/2026-Q1/lots/05-scroll/outputs/lot_1024x1536.png
  ```
