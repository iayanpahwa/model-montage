# gen-image-compare

A Claude Code skill that takes **one prompt** and **one resolution**, fires it at up to **three OpenRouter image models in parallel**, crop-to-fills each result to the exact resolution, and stitches a labeled **side-by-side comparison montage** — so you can see which model renders your prompt best in a single run.

| Slug | Model | Notes |
|------|-------|-------|
| `gemini-3-pro` | `google/gemini-3-pro-image` (Nano Banana Pro) | Highest quality, priciest |
| `gemini-3.1-flash` | `google/gemini-3.1-flash-image` (Nano Banana 2) | Fast, cheapest |
| `gpt-5.4-image-2` | `openai/gpt-5.4-image-2` | OpenAI's image model |

## Prerequisites

- Python 3
- [Pillow](https://pypi.org/project/pillow/): `pip install pillow`
- An [OpenRouter](https://openrouter.ai/) API key

Set the key one of these ways (checked in this order):

```bash
export OPENROUTER_API_KEY=sk-or-...
# or
mkdir -p ~/.config/openrouter && printf '%s' "sk-or-..." > ~/.config/openrouter/key && chmod 600 ~/.config/openrouter/key
# or pass --api-key on the command line
```

## Install in Claude Code

```text
/plugin marketplace add iayanpahwa/ai-image-gen
/plugin install gen-image-compare@ai-image-gen
```

Then just ask: *"compare image models for a poster of a red fox in snow at 1200x630"*.

## Manual install (or other agents)

The skill is self-contained — copy the folder into your agent's skills directory:

```bash
cp -r skills/gen-image-compare ~/.claude/skills/
```

`SKILL.md` + `generate.py` have no dependencies beyond Python 3 and Pillow.

## Usage (script directly)

```bash
# all three models, OG resolution
python3 skills/gen-image-compare/generate.py \
  --prompt "a red fox sitting in fresh snow, cinematic lighting" --size 1200x630

# a single model (no montage)
python3 skills/gen-image-compare/generate.py \
  --prompt "..." --size 1024x1024 --models gemini-3.1-flash

# two models, save elsewhere
python3 skills/gen-image-compare/generate.py \
  --prompt "..." --models gemini-3-pro,gpt-5.4-image-2 --out-dir ~/Desktop
```

Output files land in the current directory (or `--out-dir`):

- `image_<slug>_<WxH>_<timestamp>.png` per model
- `compare_<WxH>_<timestamp>.png` — the montage (only when 2+ models succeed)

If one model fails, the others still save and the failure is reported. Image text is approximate — verify spelling on logos/taglines.

## License

MIT
