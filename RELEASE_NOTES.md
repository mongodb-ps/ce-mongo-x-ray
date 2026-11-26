# mongo-x-ray 2.1.5 — Release Notes

**Scope**: v2.1.2 → 2.1.5 (2026-11-26)
**TL;DR**: two compatibility fixes after the 2.1.4 release — a plugin older than 2.1.4 no longer fails on the missing MongoDB template, and the health check brings back a helper the older gmd imports. 2.1.3 remains broken on PyPI (see below); use 2.1.5.

## Compatibility fixes

- **Older plugins fall back to their `full.html` template**: the default configuration points at `<module>/mongodb.html`, which only ships with plugin releases from 2.1.4 on. A newer core with an older plugin (e.g. `mongo-x-ray-gmd` 2.1.0) failed with `FileNotFoundError`; `select_template()` now warns and renders `<module>/full.html` instead.
- `mongo-x-ray-hc` 2.1.5 restores `colorize_severity`, which `mongo-x-ray-gmd` releases before 2.1.4 import (`ImportError: cannot import name 'colorize_severity'` when only the health check plugin was upgraded).
- ⚠️ **`mongo-x-ray==2.1.3` on PyPI is broken** (its wheel is missing `templates/css/mongodb.css`); 2.1.4 restored the file and 2.1.5 adds these compatibility fixes.

## New Features ✨

- **MongoDB report template** (`<module>/mongodb.html`) for every plugin: a dark report — MongoDB black page, `#112733` panel, `#E8EDEB` text — built from the design system, with the LeafyGreen **SideNav** outline, **Table**, **Badge**, **Tabs**, **Button** (default variant) and **Typography** scale, and the LeafyGreen icons (Copy, Checkmark, Sort, Chevron) inlined as SVG masks. It replaces the two stylesheets the default template fetches from a CDN, so the themed report requests no remote stylesheet and no webfont. The template is now the shipped default (`config.json`).
- **Severity badges**: `mongo_x_ray.shared.severity_badge()` renders HIGH/MEDIUM/LOW/INFO as MongoDB Badges (red / yellow / green / light gray) everywhere a severity is shown, replacing the per-plugin bold coloured text.
- **AI notes**: `mongo_x_ray.shared.ai_note_markdown()` renders the Sparkle label, the note and a **copy button** that copies exactly the note (title excluded); the new shared `post_ai_copy.js` wires it up. The Sparkle glyph is exported as `shared.AI_ICON`.
- **`.env` loading** (`mongo_x_ray.env`): loaded when the package is imported, searching the working directory and its parents, then the package location; values already in the environment (VS Code `envFile`, CI, shell exports) win. Previously the file was only read as a side effect of importing `mongo_x_ray.utils`, so runs started elsewhere — and `AI_MODEL` in particular — silently used defaults.
- **Chart blocks** carry a `chart-container` class with a 16px bottom margin, so stacked charts and the notes below them no longer touch.

## Fixed 🐛

- **Printing**: the report outline is hidden *and* out of the layout on paper (no reserved column); the whole dark theme falls back to the light variant, so the PDF is ink friendly.
- **Outline**: clicking an entry lands the heading at the top and highlights that same entry. The stray `scroll-margin-top` (a leftover from the removed sticky tabs) and gmd's divergent outline implementation are gone.
- **Every labelled report button** (Copy Table, the log Reset controls) is the MongoDB Button default variant; the Copy Table button shows the Copy icon and a Checkmark while copied.

## Changed 🔧

- `item_config` gained `ai_analysis` (`false` disables the AI analysis, `true` opts a test run in); the old log `WEFItem.ai_support` switch was removed.
- `.vscode` launch configurations let `.env` own `LOG_LEVEL`/`ENV`, pin the working directory, and read the same file for the test configurations; `python.envFile` is set so Test Explorer and terminal runs see it too.

## Upgrade Guide (2.1.2 → 2.1.3)

```bash
pip install -U mongo-x-ray mongo-x-ray-hc mongo-x-ray-log mongo-x-ray-ftdc mongo-x-ray-gmd
```

- Upgrade the plugins together with `mongo-x-ray`: the 2.1.3 plugins import helpers added in this core release (`severity_badge`, `ai_note_markdown`, `AI_ICON`) and rely on its stylesheets, so they require `mongo-x-ray>=2.1.3`.
- Reports now default to the MongoDB template. Restore the original look per module with `"template": "<module>/full.html"` in the config file.
