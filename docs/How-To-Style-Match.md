# Nano Banana Multi-Image Reference Specification

## Overview

Nano Banana (Gemini 2.5 Flash Image / Gemini 3 Pro Image) supports multi-image input for composition, style transfer, and template-based generation. This spec covers reference image usage patterns for consistent, repeatable outputs.

---

## Model Capabilities

| Model | Max Reference Images | Resolution | Notes |
|-------|---------------------|------------|-------|
| Gemini 2.5 Flash Image | 6 | 1K default | Fast, good for iteration |
| Gemini 3 Pro Preview | 14 | 1K, 2K, 4K | Up to 6 objects + 5 humans |

---

## Reference Image Roles

When providing multiple images, explicitly label each image's role in your prompt:

### Core Role Types

| Role | Purpose | Example Label |
|------|---------|---------------|
| **Template** | Structural layout, composition, placement zones | "Image A is the template showing layout structure" |
| **Style** | Visual aesthetic, color palette, texture, finish | "Image B defines the target visual style" |
| **Subject** | Primary content/character to preserve identity | "Image C contains the subject to include" |
| **Background** | Environment, scene, backdrop | "Image D is the background environment" |
| **Lighting** | Light direction, temperature, shadow reference | "Use lighting from Image E" |

---

## Prompt Structure Pattern

```
[IMAGE INVENTORY]
Image A is [role]: [brief description of what it provides]
Image B is [role]: [brief description of what it provides]

[GENERATION INTENT]
Generate/Create [output description].

[PRESERVATION RULES]
- Keep [element] from Image [X]
- Match [element] from Image [Y]
- Preserve [specific detail]

[STYLE DIRECTIVES]
Apply [style/aesthetic] from [source].
Use [color/lighting/texture] treatment.

[TECHNICAL SPECS]
[Aspect ratio], [resolution], [camera/lens if relevant]

[NEGATIVE CONSTRAINTS]
No [unwanted elements], avoid [artifacts to prevent].
```

---

## Card Generation Template

### Two-Image Pattern: Template + Completed Example

```
IMAGE ROLES:
- Image A: Blank card template showing structure, borders, and text zones
- Image B: Completed example card demonstrating target style, coloring, and finish

TASK:
Generate a new card using the structural layout from Image A.
Apply the visual style, color treatment, shading, and artistic finish from Image B.

CARD CONTENT:
- Title: [Card Title]
- Artwork Subject: [Description of central artwork]
- Card Type/Category: [Type indicator]
- Text Content: [Any body text or stats]

PRESERVATION:
- Maintain exact border structure and proportions from template
- Match color palette and lighting style from example
- Keep text zones positioned as shown in template

STYLE:
- [Art style]: [e.g., "illustrated fantasy art", "watercolor biblical", "icon-style"]
- Color temperature: [warm/cool/neutral]
- Texture: [smooth/painterly/textured]

OUTPUT:
[Aspect ratio, e.g., 2:3 portrait], high detail, print-ready quality

AVOID:
- Text rendering errors
- Border distortion
- Style drift from example
```

---

## Multi-Image Combination Patterns

### Pattern 1: Template + Style Reference
```
Image A (template): Card frame and layout structure
Image B (style): Completed card showing desired finish

"Create a new card. Use the structural layout from Image A. 
Apply the artistic style, coloring, and finish from Image B.
Subject: [new subject description]"
```

### Pattern 2: Template + Style + Subject
```
Image A (template): Card frame structure
Image B (style): Art style reference
Image C (subject): Character/object to feature

"Generate a card using layout from A, art style from B, 
featuring the subject from C adapted to match the style."
```

### Pattern 3: Template + Multiple Style Aspects
```
Image A (template): Structure
Image B (color palette): Color reference
Image C (texture): Surface/finish reference
Image D (composition example): How elements arrange

"Create card with structure from A, colors from B, 
texture treatment from C, element arrangement inspired by D."
```

---

## Best Practices

### DO:
- **Label images explicitly** - "Image A is...", "Image B provides..."
- **Prioritize preservation** - State what MUST stay the same first
- **Be specific about style elements** - Colors, lighting, texture, line quality
- **Use hierarchical instructions** - Structure → Style → Content → Constraints
- **Iterate in conversation** - Refine with follow-up prompts in same session

### DON'T:
- Assume the model knows which image is which without labels
- Overload with conflicting style references
- Mix aspect ratios without specifying which to use
- Leave ambiguity about what to preserve vs. what to generate fresh

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Style not transferring | Weak style labeling | Explicitly describe style elements to extract |
| Template structure lost | Style override | Add "Preserve exact layout structure from template" |
| Inconsistent outputs | Ambiguous roles | Strengthen role labels and preservation rules |
| Wrong aspect ratio | Mixed input ratios | Specify output ratio; use template ratio as anchor |
| Text rendering issues | Model limitation | Minimize text; add to template, not generation |
| Color drift | Palette not anchored | Reference specific colors: "Match the deep blue (#1a3a5c) from Image B" |

---

## API Usage (Python Example)

```python
import google.generativeai as genai
from PIL import Image
import base64

# Configure
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-2.0-flash-exp')  # or gemini-2.5-flash

# Load reference images
template_img = Image.open("card_template.png")
style_img = Image.open("completed_example.png")

# Multi-image prompt
prompt = """
IMAGE ROLES:
- Image 1: Card template showing structure and layout
- Image 2: Completed card example showing target style

TASK:
Generate a new card using structural layout from Image 1.
Apply visual style, coloring, and finish from Image 2.

CARD CONTENT:
- Title: "CHESED"
- Artwork: Ancient Hebrew shepherd extending hand to help fallen traveler
- Type: Hebrew Word Card

PRESERVATION:
- Exact border structure from template
- Color palette from example
- Text zone positions from template

OUTPUT: 2:3 portrait, print quality
AVOID: Text errors, border distortion
"""

response = model.generate_content([prompt, template_img, style_img])

# Handle response
if response.candidates[0].content.parts:
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'inline_data'):
            # Save generated image
            img_data = base64.b64decode(part.inline_data.data)
            with open("generated_card.png", "wb") as f:
                f.write(img_data)
```

---

## Hypertext Card Pipeline Integration

For automated card generation with consistent style:

```python
def generate_card(word_data: dict, template_path: str, style_ref_path: str) -> bytes:
    """
    Generate a Hypertext card using template + style reference.
    
    Args:
        word_data: Dict with 'hebrew', 'english', 'definition', 'artwork_prompt'
        template_path: Path to blank card template
        style_ref_path: Path to completed example card
    
    Returns:
        Generated image bytes
    """
    prompt = f"""
    IMAGE ROLES:
    - Image 1: Card template (structure, borders, text zones)
    - Image 2: Style reference (coloring, finish, artistic treatment)
    
    GENERATE: Hypertext biblical word study card
    
    CONTENT:
    - Hebrew Word: {word_data['hebrew']}
    - English: {word_data['english']}
    - Artwork: {word_data['artwork_prompt']}
    
    STYLE MATCHING:
    - Match exact color palette from Image 2
    - Apply same artistic finish and texture
    - Use consistent lighting treatment
    - Preserve border styling from both references
    
    STRUCTURE:
    - Layout from Image 1
    - Proportions from Image 1
    - Text positioning from Image 1
    
    OUTPUT: 2:3 portrait, 1024px width minimum
    AVOID: Text rendering in artwork area, border artifacts
    """
    
    template = Image.open(template_path)
    style_ref = Image.open(style_ref_path)
    
    response = model.generate_content([prompt, template, style_ref])
    return extract_image_from_response(response)
```

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2025-12-28 | Initial spec for multi-image reference usage |