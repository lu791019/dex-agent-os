
# Slack GIF Creator - Flexible Toolkit

A toolkit for creating animated GIFs optimized for Slack. Provides validators for Slack's constraints, composable animation primitives, and optional helper utilities.

## Slack's Requirements

**Message GIFs:** Max ~2MB, 480x480, 15-20 FPS, 128-256 colors, 2-5s duration.

**Emoji GIFs:** Max 64KB (strict), 128x128, 10-12 FPS, 32-48 colors, 1-2s duration. Limit to 10-15 frames, avoid gradients, keep designs simple.

## Core Validators

```python
from core.validators import validate_gif, is_slack_ready

all_pass, results = validate_gif('emoji.gif', is_emoji=True)

if is_slack_ready('emoji.gif', is_emoji=True):
    print("Ready to upload!")
```

## Philosophy

1. **Understand the creative vision** — What should happen? What's the mood?
2. **Design the animation** — Break into phases (anticipation, action, reaction)
3. **Apply primitives as needed** — Shake, bounce, move, effects — mix freely
4. **Validate constraints** — Check file size, especially for emoji GIFs
5. **Iterate if needed** — Reduce frames/colors if over size limits

## Dependencies

```bash
pip install pillow imageio numpy
```

## Reference Files

- **`references/animation-primitives.md`** — All animation building blocks: shake, bounce, spin, pulse, fade, zoom, explode, wiggle, slide, flip, morph, move, kaleidoscope, and composing patterns. Load when creating GIF animations.
- **`references/helpers-optimization.md`** — GIF Builder, text rendering, color palettes, visual effects, easing functions, frame composition, optimization strategies, and example patterns. Load when assembling and optimizing GIFs.
