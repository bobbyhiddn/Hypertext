#!/usr/bin/env python3
import os

POST_TEMPLATE = """# Hypertext — {word}

![{word} card]({image_rel_path})

## Word
**{word}** — {gloss}

## Old Testament
> {ot_ref} — “{ot_snip}”

## New Testament
> {nt_ref} — “{nt_snip}”

## Trivia
{trivia}

"""


def bullet_lines(items):
    return "\n".join([f"- {x}" for x in items])


def render_post(
    out_path: str,
    *,
    word: str,
    gloss: str,
    ot_ref: str,
    ot_snip: str,
    nt_ref: str,
    nt_snip: str,
    trivia_items: list[str],
    image_rel_path: str,
):
    content = POST_TEMPLATE.format(
        word=word,
        gloss=gloss,
        ot_ref=ot_ref,
        ot_snip=ot_snip,
        nt_ref=nt_ref,
        nt_snip=nt_snip,
        trivia=bullet_lines(trivia_items),
        image_rel_path=image_rel_path,
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    pass
