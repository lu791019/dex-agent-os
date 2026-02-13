
# PPTX creation, editing, and analysis

## Overview

A .pptx file is a ZIP archive containing XML files and resources. Different tools and workflows are available for different tasks.

## Reading and Analyzing Content

**Text extraction:**
```bash
python -m markitdown path-to-file.pptx
```

**Raw XML access** (for comments, speaker notes, layouts, animations, formatting):
```bash
python ooxml/scripts/unpack.py <office_file> <output_dir>
```

Key file structures: `ppt/presentation.xml`, `ppt/slides/slide{N}.xml`, `ppt/notesSlides/`, `ppt/comments/`, `ppt/slideLayouts/`, `ppt/slideMasters/`, `ppt/theme/`, `ppt/media/`.

**Typography/color extraction**: Read `ppt/theme/theme1.xml` for `<a:clrScheme>` and `<a:fontScheme>`, examine slide XML for `<a:rPr>`, grep for `<a:solidFill>` and `<a:srgbClr>`.

## Creating New (Without Template)

Use **html2pptx** workflow:
1. **READ**: [`html2pptx.md`](html2pptx.md) completely
2. Create HTML files per slide (720pt x 405pt for 16:9). Rasterize gradients/icons as PNG first.
3. Run JS using [`html2pptx.js`](scripts/html2pptx.js) to convert and save
4. **Validate**: `python scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4` — inspect for text cutoff, overlap, positioning, contrast issues

Load `references/design-guidelines.md` for color palettes and visual design patterns.

## Editing Existing

1. **READ**: [`ooxml.md`](ooxml.md) completely
2. Unpack: `python ooxml/scripts/unpack.py <file> <dir>`
3. Edit XML files
4. Validate: `python ooxml/scripts/validate.py <dir> --original <file>`
5. Pack: `python ooxml/scripts/pack.py <dir> <file>`

## Creating New (With Template)

Load `references/template-workflow.md` for the full 7-step process covering: template analysis, inventory, outline, rearranging, text extraction, replacement JSON, and applying replacements.

## Thumbnail Grids

```bash
python scripts/thumbnail.py template.pptx [output_prefix] [--cols 4]
```

## Slide to Image Conversion

```bash
soffice --headless --convert-to pdf template.pptx
pdftoppm -jpeg -r 150 template.pdf slide
```

## Code Style

Write concise code. Avoid verbose variable names, redundant operations, and unnecessary print statements.

## Dependencies

markitdown, pptxgenjs, playwright, react-icons, sharp, LibreOffice, Poppler, defusedxml.

## Reference Files

- **`references/design-guidelines.md`** — Design principles, 18 color palettes, visual details (geometry, borders, typography, charts, layouts, backgrounds), layout tips. Load when creating presentations from scratch.
- **`references/template-workflow.md`** — Full 7-step template-based creation: extract, analyze, outline, rearrange, inventory, replacement JSON, apply. Load when creating presentations from templates.
