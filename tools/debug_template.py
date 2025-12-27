#!/usr/bin/env python3
"""
Debug script to ask Gemini what it sees in the style reference image.
"""
import os
import sys
from gemini_text import generate_text_with_grounding
# We need to send the image to Gemini Vision model (e.g. gemini-1.5-flash) to describe it.
# But gemini_text.py uses text-only model by default? No, 1.5-flash is multimodal.
# However, gemini_text.py implementation only accepts text prompts.

# I'll use gemini_style.py imports to send an image + prompt to describe it.
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("google-genai not installed")
    sys.exit(1)

def describe_image(image_path: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set")
        return

    client = genai.Client(api_key=api_key)
    
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    # Create image part
    if hasattr(types.Part, "from_bytes"):
        image_part = types.Part.from_bytes(data=img_bytes, mime_type="image/png")
    else:
        # Fallback
        image_part = types.Part(inline_data={"mime_type": "image/png", "data": img_bytes})

    prompt = "Describe the top-right corner of this card template. Is there a Rarity Icon (diamond/shape)? Is there text? Describe exactly what is in that corner."

    response = client.models.generate_content(
        model="gemini-3-pro-preview",
        contents=[image_part, prompt]
    )
    
    print(f"Analysis of {image_path}:")
    print(response.text)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        describe_image(sys.argv[1])
    else:
        describe_image("tools/clean_template_final.png")
