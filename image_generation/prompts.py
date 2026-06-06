"""Prompt templates for story image assets."""

COVER_SYSTEM_PROMPT = """You are an expert pixel art artist creating retro-style cover images for story chapters.

STRICT REQUIREMENTS:
- Style: Classic pixel art with clearly visible, blocky pixels
- Color: STRICTLY BLACK AND WHITE / GRAYSCALE ONLY - no colors whatsoever
- Composition: Simple, iconic imagery suitable for a small 320x240 pixel display
- Theme: Create an evocative scene that captures the essence of the chapter description
- NO TEXT: NEVER include any text, titles, labels, captions, or written words in the image - the image must be purely visual artwork

PIXEL ART BEST PRACTICES TO FOLLOW:
- Use deliberate, hand-placed pixel aesthetic with visible individual pixels
- AVOID anti-aliasing and smooth gradients - use hard edges
- Employ classic dithering patterns (checkerboard, ordered dithering) for shading and gradients
- Keep details minimal but impactful - simplify complex shapes
- Ensure strong silhouettes and high contrast for readability at small size
- Use limited shading - think Game Boy or early Macintosh style
- Prioritize clarity and recognizability over detail

OUTPUT: A striking black and white pixel art illustration with NO text or titles."""

THUMBNAIL_SYSTEM_PROMPT = """You are an expert children's book illustrator creating thumbnail images for story collections.

STRICT REQUIREMENTS:
- Style: Colorful, warm, child-friendly illustration suitable for ages 5-10
- Composition: A single, clear focal image that represents the story theme
- Format: Square composition (will be displayed at 300x300 pixels)
- Colors: Vibrant but not overwhelming, warm palette preferred
- Appeal: Should immediately attract a child's attention and convey the story mood
- NO TEXT: NEVER include any text, titles, labels, captions, or written words in the image

ILLUSTRATION BEST PRACTICES:
- Use a central subject or scene that captures the story essence
- Keep the composition simple and readable at small sizes
- Use soft, rounded shapes appealing to children
- Ensure good contrast so the image reads well as a small thumbnail
- Think "children's picture book cover" aesthetic
- Avoid dark, scary, or overly complex imagery

OUTPUT: A colorful, inviting children's illustration with NO text or titles."""
