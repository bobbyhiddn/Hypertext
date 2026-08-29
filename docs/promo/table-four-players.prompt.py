"""Generate the four-player table illustration with real cards as style references.

Not a card, so it deliberately does not go through the card image contract (which pins
2:3 / 2K for faces). Marketing art: landscape, real card faces shown as references so the
painted cards on the table match the printed ones.
"""
import os, sys, pathlib
from google import genai
from google.genai import types

S = pathlib.Path("/tmp/claude-1000/-home-cap-Code-Hypertext/51dcdd88-c49d-4b61-a082-0bfa42d56523/scratchpad/tableart")
REFS = [
    ("a Word Card face, GLORIOUS rarity", "series/2026-Q1/cards/024-covenant/outputs/card_1024x1536.png"),
    ("a Word Card face, COMMON rarity",   "series/2026-Q1/cards/016-good/outputs/card_1024x1536.png"),
    ("a Word Card face, RARE rarity",     "series/2026-Q1/cards/089-priest/outputs/card_1024x1536.png"),
    ("the card BACK, navy and gold",      "templates/card_back.png"),
    ("a LOT card face (a recipe card)",   "series/2026-Q1/lots/faces/02-pentateuch.png"),
    ("the LOT card back, green and silver", "templates/lots/Lot_Back.png"),
]

PROMPT = """A luminous cinematic oil painting, impressionistic brushwork, of a four-player
card game in progress, seen from a high three-quarter angle looking down across a dark
walnut table. Rich saturated blues and golds, deep shadowed edges, one warm light source
above the table.

ABSOLUTELY NO FACES AND NO PEOPLE ABOVE THE WRIST. Show only hands and forearms entering
the frame from the four table edges - four pairs of hands, cuffs and sleeves visible, no
heads, no torsos, no faces anywhere in the image.

ON THE TABLE, arranged clearly:
- CENTRE: a face-down draw pile of cards showing the NAVY AND GOLD card back from the
  reference images (this is the Tower), and beside it a face-up discard pile of Word Cards.
- Beside those, one LOT card face-up - a landscape-oriented recipe card matching the LOT
  reference image.
- FOUR PLAYER SEATS, one at each edge: each has a small fan of Word Cards held in one hand,
  a LOT card face-up on the table in front of them, and a few small gold coin-like tokens.
- One player at the near edge is in the act of PLAYING a card - their hand is lowering a
  single Word Card face-up onto the table, mid-motion, the card catching the light.
- One seat has three Word Cards laid out face-up in a neat row on the table in front of it,
  like a completed set.

THE CARDS must look exactly like the reference card images: tall portrait cards with an
ornate navy and gold border, a parchment interior, a small painted illustration panel near
the top, and dark text blocks below. Painted, not photographic. Card text may be suggested
with soft illegible marks rather than real letters.

Warm, absorbed, quiet - the feel of a serious game between friends. No text overlays, no
title, no logo, no watermark, no UI."""

def main(n=3):
    key = os.environ.get("GEMINI_API_KEY")
    if not key: raise SystemExit("GEMINI_API_KEY not set")
    client = genai.Client(api_key=key)
    contents = []
    for label, path in REFS:
        b = pathlib.Path(path).read_bytes()
        contents.append(types.Part.from_text(text=f"REFERENCE: {label}"))
        contents.append(types.Part.from_bytes(data=b, mime_type="image/png"))
    contents.append(types.Part.from_text(text=PROMPT))
    cfg = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="4:3", image_size="2K"),
    )
    for i in range(1, n + 1):
        r = client.models.generate_content(model="gemini-3.1-flash-image", contents=contents, config=cfg)
        saved = False
        for part in r.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                out = S / f"table-{i}.png"
                out.write_bytes(part.inline_data.data)
                print(f"  saved {out.name} ({len(part.inline_data.data)//1024} KB)")
                saved = True
        if not saved: print(f"  attempt {i}: no image returned")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
