---
name: gen-image-compare
description: Generate the same prompt across up to three OpenRouter image models in parallel (Nano Banana Pro / google/gemini-3-pro-image, Nano Banana 2 / google/gemini-3.1-flash-image, and OpenAI's gpt-5.4-image-2), crop each to an exact WxH resolution, and stitch a labeled side-by-side comparison montage. Use this skill whenever the user wants to compare image-generation models, "generate with 3 models", "try multiple models", "see which model is best" for an image, asks for a model bake-off / comparison sheet, or says "gen-image-compare" — even if they don't name the models. If the user wants only 1 or 2 images, ask which model(s) to use and pass them through.
---

# gen-image-compare

Run one prompt through multiple OpenRouter image models at once and compare the results. Wraps `generate.py`, which fires the models in parallel, center crop-to-fills each output to the exact requested `WxH` (the models never return precise pixel sizes), and builds a labeled montage.

**Models** (slug → id): `gemini-3-pro` → `google/gemini-3-pro-image` (priciest, highest quality) · `gemini-3.1-flash` → `google/gemini-3.1-flash-image` (cheapest, fast) · `gpt-5.4-image-2` → `openai/gpt-5.4-image-2`.

## How to run

1. Collect inputs (ask only for what's missing):
   - **prompt** — what the image should show.
   - **resolution** — `WxH` in pixels. If unspecified, infer from intent and state your choice:
     - X/Twitter header → `1500x500` · OG / social preview → `1200x630` · Blog hero → `1600x900` · Square / generic → `1024x1024`.

2. **Decide how many / which models.** Default is **all three**. If the user asked for **1 or 2** images and didn't name the models, ask which of `gemini-3-pro` / `gemini-3.1-flash` / `gpt-5.4-image-2` they want, then pass them via `--models` (comma-separated). With a single model the montage is skipped automatically.

3. **Optional design doc.** If the user provides or points to a design doc (a `design.md` or any markdown/text file describing palette, typography, layout, branding, or style), pass it via `--design <path>` — its contents are injected into the prompt for **every** model so they all follow the same guidelines. If a `design.md` exists in the working directory and the user is doing design/brand work, offer to include it rather than assuming. Omit `--design` entirely when there's no design doc.

4. Run the script (use `$CLAUDE_PLUGIN_ROOT` when installed as a plugin; otherwise the local path):
   ```bash
   python3 "$CLAUDE_PLUGIN_ROOT/skills/gen-image-compare/generate.py" \
     --prompt "your prompt here" \
     --size 1200x630
   # subset example:
   #   --models gemini-3.1-flash,gpt-5.4-image-2
   # with a design doc:
   #   --design ./design.md
   # other dir: --out-dir ~/Desktop
   ```

5. Parse the script output (per-model `STATUS` / `SAVED` / `COST`, plus `DESIGN_DOC`, `MONTAGE`, and `TOTAL_COST`). Report each model's saved path and cost, **always state the `TOTAL_COST` at the end**, note the design doc if one was applied, then surface every saved image **and** the montage inline with the **SendUserFile** tool.

## Notes

- **API key sourcing order:** `$OPENROUTER_API_KEY` → `~/.config/openrouter/key` → `--api-key`. If none is found the script exits with a message. In that case, ask the user for their key and offer to save it: `mkdir -p ~/.config/openrouter && printf '%s' "<key>" > ~/.config/openrouter/key && chmod 600 ~/.config/openrouter/key`. Never echo the key back.
- **Partial failure is tolerated:** if one model errors, the others still save; report which failed and why. The script only errors out if *all* models fail.
- **Design doc:** `--design` accepts any text/markdown file, not just one literally named `design.md`. Its full contents are sent to every model, so very long docs add some token cost. If the path is missing or empty the script exits with a clear error before any API call.
- **Cost:** Pro is the most expensive, Flash the cheapest — mention this if the user is cost-sensitive or running all three repeatedly.
- For text-in-image (logos, taglines), warn that the models approximate text; verify spelling after generation.
- Requires Pillow (`PIL`) and Python 3.
