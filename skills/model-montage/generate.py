#!/usr/bin/env python3
"""Generate the same prompt across multiple OpenRouter image models in parallel,
crop-to-fill each result to an exact resolution, and (optionally) stitch a labeled
side-by-side comparison montage.

Usage:
    python3 generate.py --prompt "..." --size 1200x630
    python3 generate.py --prompt "..." --size 1024x1024 --models gemini-3.1-flash
    python3 generate.py --prompt "..." --models gemini-3-pro,gpt-5.4-image-2

Default models: all three (gemini-3-pro, gemini-3.1-flash, gpt-5.4-image-2).
Images are saved to the current directory unless --out-dir is given.
"""

import argparse
import base64
import datetime
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from math import gcd

# slug (used in filenames / labels) -> OpenRouter model id
MODELS = {
    "gemini-3-pro": "google/gemini-3-pro-image",
    "gemini-3.1-flash": "google/gemini-3.1-flash-image",
    "gpt-5.4-image-2": "openai/gpt-5.4-image-2",
}
# reverse lookup so users can also pass the long id to --models
ID_TO_SLUG = {v: k for k, v in MODELS.items()}


def parse_size(s):
    try:
        w, h = s.lower().split("x")
        return int(w), int(h)
    except Exception:
        sys.exit(f"Bad --size {s!r}; expected WxH like 1200x630")


def aspect_hint(w, h):
    g = gcd(w, h)
    return f"{w // g}:{h // g} aspect ratio ({w}x{h} pixels)"


def resolve_models(arg):
    """Map --models (slugs or long ids, comma-separated) to [(slug, id), ...]."""
    if not arg:
        return [(slug, mid) for slug, mid in MODELS.items()]
    out = []
    for token in [t.strip() for t in arg.split(",") if t.strip()]:
        if token in MODELS:
            out.append((token, MODELS[token]))
        elif token in ID_TO_SLUG:
            out.append((ID_TO_SLUG[token], token))
        else:
            sys.exit(
                f"Unknown model {token!r}. Choose from: {', '.join(MODELS)} "
                f"(or the long ids {', '.join(MODELS.values())})."
            )
    return out


def resolve_api_key(cli_key):
    if cli_key:
        return cli_key
    env = os.environ.get("OPENROUTER_API_KEY")
    if env:
        return env
    keyfile = os.path.expanduser("~/.config/openrouter/key")
    if os.path.isfile(keyfile):
        with open(keyfile) as f:
            k = f.read().strip()
        if k:
            return k
    sys.exit(
        "No OpenRouter API key found. Set $OPENROUTER_API_KEY, write the key to "
        "~/.config/openrouter/key, or pass --api-key."
    )


def generate_one(slug, model_id, prompt, w, h, api_key, out_dir, ts, design_text=None):
    """Call one model, crop-to-fill to WxH, save. Returns a result dict."""
    design_block = ""
    if design_text:
        design_block = (
            "Strictly follow the design guidelines below - treat them as authoritative for "
            "layout, color palette, typography, spacing, visual style, and branding:\n"
            "--- BEGIN DESIGN GUIDELINES ---\n"
            f"{design_text}\n"
            "--- END DESIGN GUIDELINES ---\n\n"
        )
    full_prompt = (
        f"{prompt}\n\n"
        f"{design_block}"
        f"Compose this as a {aspect_hint(w, h)} image. Fill the entire frame edge to edge; "
        f"do not add borders, letterboxing, or padding."
    )
    payload = json.dumps(
        {"model": model_id, "messages": [{"role": "user", "content": full_prompt}]}
    ).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        body = getattr(e, "read", lambda: b"")()
        return {"slug": slug, "status": "failed", "error": f"{e} {body[:300]!r}"}

    msg = data.get("choices", [{}])[0].get("message", {})
    images = msg.get("images")
    if not images:
        return {
            "slug": slug,
            "status": "failed",
            "error": f"no image in response (content={msg.get('content')!r})",
        }

    try:
        raw = base64.b64decode(images[0]["image_url"]["url"].split(",", 1)[1])
        from PIL import Image, ImageOps

        img = Image.open(BytesIO(raw)).convert("RGB")
        fitted = ImageOps.fit(img, (w, h), method=Image.LANCZOS, centering=(0.5, 0.5))
        path = os.path.join(out_dir, f"image_{slug}_{w}x{h}_{ts}.png")
        fitted.save(path, "PNG")
    except Exception as e:
        return {"slug": slug, "status": "failed", "error": f"decode/save failed: {e}"}

    return {
        "slug": slug,
        "status": "ok",
        "path": path,
        "cost": data.get("usage", {}).get("cost"),
    }


def build_montage(results, w, h, out_dir, ts):
    ok = [r for r in results if r["status"] == "ok"]
    if len(ok) < 2:
        return None
    from PIL import Image, ImageDraw, ImageFont

    panel_w = min(w, 640)
    panel_h = max(1, round(h * panel_w / w))
    strip = 32
    font = ImageFont.load_default()
    canvas = Image.new("RGB", (panel_w * len(ok), panel_h + strip), "white")
    draw = ImageDraw.Draw(canvas)
    for i, r in enumerate(ok):
        im = (
            Image.open(r["path"])
            .convert("RGB")
            .resize((panel_w, panel_h), Image.LANCZOS)
        )
        x = i * panel_w
        canvas.paste(im, (x, strip))
        label = r["slug"]
        if r.get("cost") is not None:
            label += f"  ${r['cost']}"
        draw.rectangle([x, 0, x + panel_w, strip], fill="black")
        draw.text((x + 6, 9), label, fill="white", font=font)
    path = os.path.join(out_dir, f"compare_{w}x{h}_{ts}.png")
    canvas.save(path, "PNG")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--size", default="1024x1024", help="WxH, e.g. 1200x630")
    ap.add_argument(
        "--models",
        default=None,
        help="comma-separated slugs or ids; default is all three",
    )
    ap.add_argument("--out-dir", default=None, help="output dir (default: cwd)")
    ap.add_argument("--api-key", default=None, help="override $OPENROUTER_API_KEY")
    ap.add_argument("--no-montage", action="store_true", help="skip comparison sheet")
    ap.add_argument(
        "--design",
        default=None,
        help="path to a design doc (e.g. design.md); its contents are sent to every model",
    )
    args = ap.parse_args()

    w, h = parse_size(args.size)
    models = resolve_models(args.models)
    api_key = resolve_api_key(args.api_key)
    out_dir = os.path.abspath(os.path.expanduser(args.out_dir or os.getcwd()))
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    design_text = None
    if args.design:
        design_path = os.path.abspath(os.path.expanduser(args.design))
        if not os.path.isfile(design_path):
            sys.exit(f"Design doc not found: {design_path}")
        with open(design_path, encoding="utf-8") as f:
            design_text = f.read().strip()
        if not design_text:
            sys.exit(f"Design doc is empty: {design_path}")

    with ThreadPoolExecutor(max_workers=len(models)) as ex:
        futures = [
            ex.submit(
                generate_one,
                slug,
                mid,
                args.prompt,
                w,
                h,
                api_key,
                out_dir,
                ts,
                design_text,
            )
            for slug, mid in models
        ]
        results = [f.result() for f in futures]

    # keep output ordered the same as the requested models
    order = {slug: i for i, (slug, _) in enumerate(models)}
    results.sort(key=lambda r: order.get(r["slug"], 0))

    montage = None
    if not args.no_montage:
        montage = build_montage(results, w, h, out_dir, ts)

    total = 0.0
    for r in results:
        print(f"MODEL: {r['slug']}")
        print(f"STATUS: {r['status']}")
        if r["status"] == "ok":
            print(f"SAVED: {r['path']}")
            print(f"COST: {r.get('cost')}")
            if isinstance(r.get("cost"), (int, float)):
                total += r["cost"]
        else:
            print(f"ERROR: {r['error']}")
        print("---")

    print(f"RESOLUTION: {w}x{h} (center crop-to-fill applied)")
    print(f"DESIGN_DOC: {design_path if design_text else '(none)'}")
    print(f"MONTAGE: {montage if montage else '(skipped)'}")
    print(f"TOTAL_COST: {total}")

    if not any(r["status"] == "ok" for r in results):
        sys.exit("All models failed.")


if __name__ == "__main__":
    main()
