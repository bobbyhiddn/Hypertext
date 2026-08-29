"""Contact sheet of rendered faces for eyeballing a batch: contact_sheet.py OUT.jpg SLUG... (faces at half size, five per row)."""
import sys
from PIL import Image
out, slugs = sys.argv[1], sys.argv[2:]
faces = [Image.open(f"series/2026-Q1/cards/{s}/outputs/card_1024x1536.png").convert("RGB").resize((512, 768)) for s in slugs]
cols = min(5, len(faces)); rows = (len(faces) + cols - 1) // cols
sheet = Image.new("RGB", (512 * cols, 768 * rows), "black")
for i, f in enumerate(faces):
    sheet.paste(f, (512 * (i % cols), 768 * (i // cols)))
sheet.save(out, quality=88); print(out, sheet.size)
