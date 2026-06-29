# model-montage

Generate **one prompt** at **one resolution** across **up to three image models at once** - Google's Nano Banana Pro & Nano Banana 2 and OpenAI's GPT-5.4 Image 2 - via [OpenRouter](https://openrouter.ai/). Every result is crop-to-filled to your exact pixel size, and a labeled **side-by-side comparison montage** is stitched automatically so you can pick the best model for the job in a single run.

Optionally pass a **design doc** (`design.md`) and its guidelines are injected into the prompt for *every* model, so they all follow the same palette, typography, layout, and branding.

| Slug | OpenRouter model | Notes |
|------|------------------|-------|
| `gemini-3-pro` | `google/gemini-3-pro-image` (Nano Banana Pro) | Highest quality, priciest |
| `gemini-3.1-flash` | `google/gemini-3.1-flash-image` (Nano Banana 2) | Fast, cheapest |
| `gpt-5.4-image-2` | `openai/gpt-5.4-image-2` | OpenAI's image model |

---

## Examples

**One prompt, three models, side by side.** Prompt: *"a red fox sitting in fresh snow, cinematic lighting"* at `1200x630`. Each panel is labeled with the model and its cost:

![3-model comparison](assets/example-3-model-comparison.png)

**With a design doc, every model follows the same brand.** Prompt: *"a fox mascot logo"* at `1024x1024` with a `design.md` specifying a deep-navy + warm-gold flat-vector style - all three obey it:

![design-guided comparison](assets/example-design-doc-comparison.png)

See [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md) for a full run across all cases (single/2/3 models, design doc, and error handling) with costs.

---

## What it's good for

Anywhere you'd otherwise guess which model to use - generate once, compare, ship the best:

- **Blog cover images** - hero/header art at your exact `1600x900`.
- **YouTube / video thumbnails** - eye-catching `1280x720` frames, three takes at once.
- **Social / OG preview images** - `1200x630` link cards and `1500x500` X headers.
- **App store & marketing screenshots / promo art** at fixed dimensions.
- **Logos, mascots & brand art** - pair with a `design.md` so every model stays on-brand.
- **Ad creatives & A/B variants** - get distinct directions in one pass to test.
- **Product mockups, icons, and spot illustrations** for docs and decks.
- **Model evaluation** - a quick, repeatable bake-off when you're deciding which image model to standardize on.

---

## Table of contents

- [What it's good for](#what-its-good-for)
- [Prerequisites](#prerequisites)
- [Set your OpenRouter API key](#set-your-openrouter-api-key)
- [Install - pick your path](#install--pick-your-path)
  - [A. Claude Code plugin from GitHub](#a-claude-code-plugin-from-github-recommended)
  - [B. Claude Code plugin from a local clone](#b-claude-code-plugin-from-a-local-clone)
  - [C. Manual skill install (Claude Code or any SKILL.md agent)](#c-manual-skill-install-claude-code-or-any-skillmd-agent)
  - [D. No agent - just run the script](#d-no-agent--just-run-the-script)
- [Using it inside Claude Code](#using-it-inside-claude-code)
- [Command-line reference](#command-line-reference)
- [Output files](#output-files)
- [Design-doc guided generation](#design-doc-guided-generation)
- [Updating & uninstalling](#updating--uninstalling)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Prerequisites

- **Python 3** (3.8+)
- **[Pillow](https://pypi.org/project/pillow/)** - `pip install pillow` (or `pip3 install pillow`)
- An **OpenRouter API key** - create one at <https://openrouter.ai/keys>

No other dependencies: the script uses only the Python standard library plus Pillow.

## Set your OpenRouter API key

The script looks for the key in this order - **environment variable → key file → `--api-key` flag**. Set it up any one way:

```bash
# 1) Environment variable (add to ~/.zshrc or ~/.bashrc to persist)
export OPENROUTER_API_KEY="sk-or-..."

# 2) Key file (read if the env var is unset)
mkdir -p ~/.config/openrouter
printf '%s' "sk-or-..." > ~/.config/openrouter/key
chmod 600 ~/.config/openrouter/key

# 3) Per-run flag (overrides both of the above)
#    ... generate.py --api-key "sk-or-..." ...
```

---

## Install - pick your path

### A. Claude Code plugin from GitHub (recommended)

This repo is its own plugin **marketplace**, so installation is two commands inside Claude Code:

```text
/plugin marketplace add iayanpahwa/model-montage
/plugin install model-montage@model-montage
/reload-plugins
```

Verify with `/plugin` - you should see `model-montage@model-montage` enabled. Done - now just talk to it (see [Using it inside Claude Code](#using-it-inside-claude-code)).

### B. Claude Code plugin from a local clone

Useful for hacking on the skill or installing offline:

```bash
git clone https://github.com/iayanpahwa/model-montage.git
```

```text
/plugin marketplace add /absolute/path/to/model-montage
/plugin install model-montage@model-montage
/reload-plugins
```

Edits to the cloned files take effect after `/reload-plugins`.

### C. Manual skill install (Claude Code or any SKILL.md agent)

The skill is self-contained - a `SKILL.md` plus one Python script. Copy the folder into your agent's skills directory:

```bash
# Claude Code (user-level skills)
mkdir -p ~/.claude/skills
cp -r model-montage/skills/model-montage ~/.claude/skills/
```

It loads on the next session (or `/reload-plugins`). The same folder works in **any agent that follows the `SKILL.md` convention** - drop `skills/model-montage/` into that tool's skills location. The instructions in `SKILL.md` are plain Markdown and reference only `generate.py`, so there's nothing tool-specific to port.

### D. No agent - just run the script

`generate.py` is a standalone CLI; you don't need Claude Code at all:

```bash
git clone https://github.com/iayanpahwa/model-montage.git
cd model-montage
pip install pillow
export OPENROUTER_API_KEY="sk-or-..."

python3 skills/model-montage/generate.py \
  --prompt "a red fox sitting in fresh snow, cinematic lighting" \
  --size 1200x630
```

---

## Using it inside Claude Code

Once installed, just ask in plain language - the skill triggers on phrasing like *compare image models*, *generate with all 3 models*, *try multiple models*, or *model-montage*:

- `compare image models for a poster of a red fox in snow at 1200x630`
- `generate this with all three models: a neon cyberpunk alley, 1600x900`
- `model-montage a serene mountain lake at 1024x1024, follow design.md`

Behavior:

- **No resolution given?** It infers a sensible one and tells you (X header → `1500x500`, OG image → `1200x630`, blog hero → `1600x900`, square → `1024x1024`).
- **Want only 1 or 2 images?** Say so and it asks which model(s) to use, then runs only those.
- **Have a `design.md`?** Mention it (or it may offer to use one it finds in the folder) and the guidelines go to every model.

It reports each model's saved path and cost, then shows the images and the montage inline.

---

## Command-line reference

```text
python3 skills/model-montage/generate.py --prompt PROMPT [options]

--prompt PROMPT     (required) what the image should show
--size WxH          pixel size, e.g. 1200x630   (default: 1024x1024)
--models LIST       comma-separated slugs OR full OpenRouter ids
                    (default: all three). e.g. gemini-3.1-flash
                    or gemini-3-pro,gpt-5.4-image-2
--design PATH       a design doc (any .md/.txt) sent to every model
--out-dir DIR       where to save (default: current directory)
--api-key KEY       override $OPENROUTER_API_KEY / key file
--no-montage        skip the comparison sheet
```

### Examples

```bash
# All three models, OG resolution (default behavior)
python3 skills/model-montage/generate.py \
  --prompt "a red fox in fresh snow, cinematic" --size 1200x630

# A single model - no montage is produced
python3 skills/model-montage/generate.py \
  --prompt "a single ripe lemon on a white plate" --size 1024x1024 \
  --models gemini-3.1-flash

# Two specific models, saved to the Desktop
python3 skills/model-montage/generate.py \
  --prompt "minimalist mountain logo" --size 800x800 \
  --models gemini-3-pro,gpt-5.4-image-2 --out-dir ~/Desktop

# Brand-guided: every model follows design.md
python3 skills/model-montage/generate.py \
  --prompt "a fox mascot logo" --size 1024x1024 --design ./design.md
```

---

## Output files

Written to the current directory (or `--out-dir`):

| File | When |
|------|------|
| `image_<slug>_<WxH>_<timestamp>.png` | one per model, exactly `WxH` |
| `compare_<WxH>_<timestamp>.png` | the labeled montage - only when **2+** models succeed |

The script prints a parseable summary: per-model `MODEL` / `STATUS` / `SAVED` / `COST`, then `RESOLUTION`, `DESIGN_DOC`, `MONTAGE`, and `TOTAL_COST`.

**Partial failures are tolerated:** if one model errors, the others still save and the failure is reported. The script only exits non-zero if *every* model fails.

> Text inside generated images is approximate - verify spelling on logos and taglines.

---

## Design-doc guided generation

Pass any Markdown/text file via `--design`. Its full contents are inserted into the prompt for **every** selected model, framed as authoritative guidelines for layout, palette, typography, spacing, style, and branding. Example `design.md`:

```markdown
# Brand design guidelines
- Palette: deep navy (#0B1F3A) background with warm gold (#E5B567) accents only.
- Style: flat minimalist vector illustration. No photorealism, no gradients.
- Composition: single centered subject, generous negative space.
- Mood: premium, calm, modern.
```

Notes:
- Any file path works (it need not literally be named `design.md`).
- Longer docs add some token cost since they're sent to each model.
- A missing or empty design file is reported clearly *before* any API call is made.

---

## Updating & uninstalling

```text
# Update to the latest published version
/plugin marketplace update model-montage
/plugin install model-montage@model-montage
/reload-plugins

# Remove it
/plugin uninstall model-montage@model-montage
/plugin marketplace remove model-montage
```

Manual install: delete `~/.claude/skills/model-montage/`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `No OpenRouter API key found` | Set the key - see [Set your OpenRouter API key](#set-your-openrouter-api-key). |
| `ModuleNotFoundError: No module named 'PIL'` | `pip install pillow` (use the same Python you run the script with). |
| Skill doesn't trigger after install | Run `/reload-plugins`; confirm it's enabled in `/plugin`. |
| `Design doc not found` / `is empty` | Check the `--design` path; the file must exist and be non-empty. |
| One model fails but others save | Expected - read the `ERROR:` line for that model; the run still succeeds. |
| Output isn't exactly your size | It is - the model's raw output is center crop-to-filled to `WxH` with Pillow. |

---

## License

[MIT](LICENSE) © Ayan Pahwa
