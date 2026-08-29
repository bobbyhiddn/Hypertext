#!/usr/bin/env python3
"""Generate an image from a prompt plus reference images, with retries and a picker.

Usage:
  python generate_image.py --prompt-file p.txt --out-dir art/ --ref a.png:"label" \
      --ref b.png:"label" --aspect 4:3 --attempts 3

Reference images are the point. A prompt describes; a reference SHOWS. When the output
has to match an artifact that already exists - a card, a frame, an icon, a palette - pass
that artifact as a reference and tell the model to copy it. Words like "ornate outline
frame" produced a plain rectangle three times in a row; one reference image fixed it.

Not for Word Cards or Lot faces - those go through the card/lot pipelines, which apply
deterministic stamping and their own gates. This is for everything else: marketing art,
diagrams, box art, promo scenes.
"""
import argparse, os, pathlib, sys

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("pip install google-genai")

DEFAULT_MODEL = "gemini-3.1-flash-image"


def generate(prompt: str, refs: list[tuple[str, str]], out_dir: pathlib.Path,
             attempts: int = 3, aspect: str = "4:3", size: str = "2K",
             model: str = DEFAULT_MODEL, stem: str = "gen") -> list[pathlib.Path]:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY is not set (it lives in .env: set -a; . ./.env; set +a)")
    client = genai.Client(api_key=key)

    contents = []
    for path, label in refs:
        data = pathlib.Path(path).read_bytes()
        mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
        contents.append(types.Part.from_text(text=f"REFERENCE: {label}"))
        contents.append(types.Part.from_bytes(data=data, mime_type=mime))
    contents.append(types.Part.from_text(text=prompt))

    cfg = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=aspect, image_size=size),
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for i in range(1, attempts + 1):
        try:
            r = client.models.generate_content(model=model, contents=contents, config=cfg)
        except Exception as exc:
            print(f"  attempt {i}: request failed: {exc}")
            continue
        got = False
        for part in r.candidates[0].content.parts:
            blob = getattr(part, "inline_data", None)
            if blob and blob.data:
                out = out_dir / f"{stem}-{i}.png"
                out.write_bytes(blob.data)
                print(f"  attempt {i}: {out} ({len(blob.data)//1024} KB)")
                written.append(out)
                got = True
        if not got:
            print(f"  attempt {i}: no image in response")
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", help="file holding the prompt (preferred: prompts get long)")
    ap.add_argument("--prompt", help="inline prompt")
    ap.add_argument("--out-dir", required=True, type=pathlib.Path)
    ap.add_argument("--ref", action="append", default=[],
                    help='reference as PATH:LABEL, repeatable; the label tells the model what it is')
    ap.add_argument("--attempts", type=int, default=3, help="generate N candidates and pick by eye")
    ap.add_argument("--aspect", default="4:3")
    ap.add_argument("--size", default="2K")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--stem", default="gen")
    a = ap.parse_args()

    prompt = pathlib.Path(a.prompt_file).read_text(encoding="utf-8") if a.prompt_file else a.prompt
    if not prompt:
        return ap.error("give --prompt-file or --prompt")
    refs = []
    for r in a.ref:
        path, _, label = r.partition(":")
        refs.append((path, label or pathlib.Path(path).stem))
    out = generate(prompt, refs, a.out_dir, a.attempts, a.aspect, a.size, a.model, a.stem)
    print(f"{len(out)} image(s) in {a.out_dir}")
    return 0 if out else 1


if __name__ == "__main__":
    raise SystemExit(main())
