#!/usr/bin/env python3
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except Exception as e:  # pragma: no cover
    genai = None
    types = None
    _IMPORT_ERROR = e


def _text_part(text: str):
    fn = getattr(types.Part, "from_text", None)
    if callable(fn):
        return fn(text)
    return types.Part(text=text)


def _generate_image_response(*, client, model: str, prompt: str, image_part):
    attempts = []

    try:
        attempts.append([_text_part(prompt), image_part])
    except Exception:
        pass

    try:
        content_cls = getattr(types, "Content", None)
        if content_cls is not None:
            attempts.append([content_cls(role="user", parts=[_text_part(prompt), image_part])])
    except Exception:
        pass

    attempts.append([prompt, image_part])

    last_error: Exception | None = None
    for contents in attempts:
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
            )
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All Gemini request encodings failed. Last error: {last_error}") from last_error


def _extract_first_image_bytes(resp) -> bytes:
    parts = getattr(resp, "parts", None)
    if parts is None and getattr(resp, "candidates", None):
        try:
            parts = resp.candidates[0].content.parts
        except Exception:
            parts = None

    if not parts:
        raise RuntimeError(f"No parts returned. Response: {resp}")

    for part in parts:
        inline = getattr(part, "inline_data", None)
        if inline is None:
            inline = getattr(part, "inlineData", None)
        if inline is None:
            continue

        data = getattr(inline, "data", None)
        if data is None:
            continue
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return base64.b64decode(data)

    raise RuntimeError(f"No image inline_data found. Response: {resp}")


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_template_path(*, repo_root: Path, prompt_json: dict, override: str | None) -> Path:
    if override:
        p = Path(override)
        return p if p.is_absolute() else (repo_root / p)

    candidate = prompt_json.get("template_image")
    if isinstance(candidate, str) and candidate.strip():
        p = Path(candidate)
        resolved = p if p.is_absolute() else (repo_root / p)
        if resolved.exists():
            return resolved

    fallback = repo_root / "templates" / "clean_template.png"
    return fallback


def _mime_type_for_path(p: Path) -> str:
    ext = p.suffix.lower()
    if ext == ".png":
        return "image/png"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"


def _count_stat_circles(value: object) -> tuple[int, int] | None:
    if not isinstance(value, str):
        return None
    filled = value.count("●")
    empty = value.count("○")
    if filled == 0 and empty == 0:
        return None
    return (filled, empty)


def _build_prompt(*, base_prompt: str, content_substitutions: dict) -> str:
    base_prompt = base_prompt.replace("bottom right", "bottom-right")
    base_prompt = base_prompt.replace("diamond", "rhombus")

    stats = content_substitutions.get("stats") if isinstance(content_substitutions.get("stats"), dict) else {}
    lore = _count_stat_circles(stats.get("LORE"))
    context = _count_stat_circles(stats.get("CONTEXT"))
    complexity = _count_stat_circles(stats.get("COMPLEXITY"))

    def _pip_instruction(name: str, filled_empty: tuple[int, int] | None) -> str | None:
        if not filled_empty:
            return None
        filled, _empty = filled_empty
        filled = max(0, min(5, int(filled)))
        filled_idxs = list(range(1, filled + 1))
        empty_idxs = list(range(filled + 1, 6))
        return (
            f"- {name}: fill circles {filled_idxs} and leave circles {empty_idxs} empty (circles are indexed 1..5 left-to-right)"
        )

    stat_lines = []
    for item in (
        _pip_instruction("LORE", lore),
        _pip_instruction("CONTEXT", context),
        _pip_instruction("COMPLEXITY", complexity),
    ):
        if item:
            stat_lines.append(item)
    stat_block = "\n".join(stat_lines) if stat_lines else "- Use the existing 5 circles under each stat label; fill based on the provided values."

    contract = (
        "RENDERING CONTRACT (follow exactly):\n"
        "- Do NOT redesign the card. Keep layout, borders, panels, spacing, alignment, and ornamentation identical to the template.\n"
        "- Do NOT introduce new UI elements. Edit ONLY the placeholder text and the artwork inside the art panel.\n"
        "- Output must contain ONLY the card. Do not add any surrounding text, captions, watermarks, or labels outside the card border.\n"
        "- Prioritize legibility. Do not output warped, garbled, scribbly, or low-resolution text.\n"
        "- Do not add extra headings, duplicate headings, or new panels not present in the template.\n"
        "- STAT CIRCLES: Do NOT draw new circles. Use the existing circle slots on the template.\n"
        "  - Keep circle positions, sizes, stroke widths, and spacing unchanged.\n"
        "  - To indicate filled vs empty, change only the fill of the existing circles.\n"
        f"{stat_block}\n"
        "- Text must be copied EXACTLY from the provided values (case, punctuation, quotes, ellipses, diacritics).\n"
        "  - Do not add brackets around values unless the brackets are part of the value itself.\n"
        "  - Do not translate, paraphrase, or substitute lookalike characters.\n"
        "- Greek and Hebrew must be rendered exactly as provided (preserve diacritics; Hebrew right-to-left).\n"
        "- Return only the finished card image.\n"
    )

    return (
        f"{base_prompt}\n\n"
        "---\n"
        f"{contract}\n"
        "CONTENT_SUBSTITUTIONS_JSON (authoritative):\n"
        f"{json.dumps(content_substitutions, ensure_ascii=False, indent=2)}\n"
    )


def _build_generation_prompt(*, template_description: dict, content_substitutions: dict) -> str:
    desc = json.dumps(template_description, ensure_ascii=False, indent=2)
    subs = json.dumps(content_substitutions, ensure_ascii=False, indent=2)

    return (
        "Generate a high-fidelity trading card image based on the following design system and content.\n\n"
        f"DESIGN SYSTEM (TEMPLATE DESCRIPTION):\n{desc}\n\n"
        "CONTENT TO RENDER (SUBSTITUTIONS):\n"
        "Replace any implied placeholders in the design description with these exact values:\n"
        f"{subs}\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "- Render the card strictly according to the 'DESIGN SYSTEM'.\n"
        "- Fill text fields exactly as provided in the 'CONTENT' block.\n"
        "- Render Hebrew text right-to-left.\n"
        "- Ensure all 5 circles for each stat (LORE/CONTEXT/COMPLEXITY) are visible; fill them according to the symbols (●=filled, ○=empty).\n"
        "- The result must be a single, complete card image with no surrounding background.\n"
    ).replace("diamond", "rhombus")


def generate_card(
    *,
    prompt_json_path: Path,
    template_path: Path,
    out_path: Path,
    model: str,
    max_attempts: int,
    base_delay_s: float,
    prompt_override: str | None,
    mode: str,
) -> None:
    if genai is None or types is None:
        raise RuntimeError(
            "Missing dependency: google-genai. Install it with: pip install google-genai\n"
            f"Import error: {_IMPORT_ERROR}"
        )

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TEXT_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GEMINI_TEXT_API_KEY) env var is not set.")

    prompt_json = _load_json(prompt_json_path)

    instr = prompt_json.get("instructions") if isinstance(prompt_json.get("instructions"), dict) else {}
    content_substitutions = instr.get("content_substitutions") if isinstance(instr.get("content_substitutions"), dict) else {}
    if isinstance(content_substitutions, dict) and "header_right_icon" in content_substitutions:
        v = content_substitutions.get("header_right_icon")
        if isinstance(v, str):
            content_substitutions = dict(content_substitutions)
            content_substitutions["header_right_icon"] = v.replace("diamond", "rhombus")

    prompt = prompt_override
    if not prompt and mode == "edit":
        mp = prompt_json.get("model_prompt")
        if isinstance(mp, str) and mp.strip():
            prompt = mp

    if not prompt and mode == "edit":
        primary = instr.get("primary_directive", "") if isinstance(instr, dict) else ""
        prompt = primary

    image_part = None
    if mode == "edit":
        prompt = _build_prompt(base_prompt=prompt or "", content_substitutions=content_substitutions)
        img_bytes = template_path.read_bytes()
        image_part = types.Part.from_bytes(data=img_bytes, mime_type=_mime_type_for_path(template_path))
    else:
        # mode == "generate"
        tmpl_desc = prompt_json.get("template_description", {})
        if not isinstance(tmpl_desc, dict):
            tmpl_desc = {}
        prompt = _build_generation_prompt(template_description=tmpl_desc, content_substitutions=content_substitutions)

    client = genai.Client(api_key=api_key)

    last_error: Exception | None = None
    resp = None
    for attempt in range(1, max_attempts + 1):
        try:
            if mode == "edit" and image_part:
                resp = _generate_image_response(client=client, model=model, prompt=prompt, image_part=image_part)
            else:
                resp = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
            last_error = None
            break
        except Exception as e:
            if attempt < max_attempts:
                delay = base_delay_s * (2 ** (attempt - 1)) + (0.1 * attempt)
                print(
                    f"Gemini request failed. Retrying in {delay:.1f}s (attempt {attempt}/{max_attempts}).\n{e}",
                    file=sys.stderr,
                )
                time.sleep(delay)
                last_error = e
                continue
            raise

    if last_error is not None or resp is None:
        raise RuntimeError("Gemini request failed after retries.") from last_error

    out_bytes = _extract_first_image_bytes(resp)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out_bytes)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-json", default=str(Path("tools") / "test_prompt.json"))
    parser.add_argument("--template", default=None)
    parser.add_argument("--out", default=str(Path("tools") / "demo_card.png"))
    parser.add_argument("--model", default=os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview"))
    parser.add_argument("--max-attempts", type=int, default=int(os.environ.get("GEMINI_MAX_ATTEMPTS", "6")))
    parser.add_argument("--retry-base-delay-s", type=float, default=float(os.environ.get("GEMINI_RETRY_BASE_DELAY_S", "2")))
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--mode", choices=["edit", "generate"], default="edit")

    args = parser.parse_args()

    prompt_json_path = Path(args.prompt_json)
    if not prompt_json_path.is_absolute():
        prompt_json_path = repo_root / prompt_json_path

    if not prompt_json_path.exists():
        print(f"Prompt JSON not found: {prompt_json_path}", file=sys.stderr)
        return 1

    prompt_json = _load_json(prompt_json_path)

    template_path = Path("placeholder")
    if args.mode == "edit":
        template_path = _resolve_template_path(repo_root=repo_root, prompt_json=prompt_json, override=args.template)
        if not template_path.exists():
            print(f"Template image not found: {template_path}", file=sys.stderr)
            return 1

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = repo_root / out_path

    try:
        generate_card(
            prompt_json_path=prompt_json_path,
            template_path=template_path,
            out_path=out_path,
            model=args.model,
            max_attempts=args.max_attempts,
            base_delay_s=args.retry_base_delay_s,
            prompt_override=args.prompt,
            mode=args.mode,
        )
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
