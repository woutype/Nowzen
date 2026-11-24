"""Generate all Nowzen 3D crystal 'N' icon assets for iOS, previews, welcome screen, and AltStore."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent.parent
BRANDING = Path(__file__).resolve().parent
PREVIEWS = BRANDING.parent / "previews"
CLASSIC = BRANDING / "classic"
WELCOME = ROOT / "assets" / "welcome"
ALTSTORE = ROOT / "altstore"

# Exact subpixel-extracted 3D crystal 'N' geometry in 1024x1024 reference space
CX_ORIG = (240.93 + 764.87) / 2.0
CY_ORIG = (248.14 + 757.55) / 2.0
W_ORIG = 764.87 - 240.93

FACETS = [
    # (polygon_points, shade_role: 0=bright, 1=light, 2=mid)
    ([(240.93, 248.14), (547.85, 386.59), (506.50, 534.30)], 0),
    ([(547.85, 386.59), (715.18, 757.55), (506.50, 534.30)], 1),
    ([(567.10, 375.53), (764.87, 248.23), (614.00, 427.00)], 0),
    ([(764.87, 248.23), (674.79, 494.55), (614.00, 427.00)], 1),
    ([(567.10, 375.53), (614.00, 427.00), (674.79, 494.55), (650.32, 561.46)], 2),
    ([(338.79, 409.04), (370.30, 526.10), (241.63, 689.89)], 1),
    ([(241.63, 689.89), (370.30, 526.10), (425.09, 560.75)], 0),
    ([(338.79, 409.04), (425.09, 560.75), (370.30, 526.10)], 2),
]


def hex_rgba(h, alpha=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def hex_rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def render_bg(size, bg):
    if bg is None:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if isinstance(bg, tuple):
        c0 = np.array(hex_rgb(bg[0]), dtype=float)
        c1 = np.array(hex_rgb(bg[1]), dtype=float)
        t = np.linspace(0.0, 1.0, size)[:, None, None]
        arr = (c0 * (1.0 - t) + c1 * t).clip(0, 255).astype(np.uint8)
        arr = np.broadcast_to(arr, (size, size, 3)).copy()
        return Image.fromarray(arr, "RGB").convert("RGBA")
    return Image.new("RGBA", (size, size), hex_rgba(bg))


def render_icon(size, bg, palette, scale=0.68, ss=4, overrides=None):
    """Render anti-aliased Nowzen crystal N at `size`x`size`."""
    S = size * ss
    img = render_bg(S, bg)
    k = (S * scale) / W_ORIG

    def pt(x, y):
        return ((x - CX_ORIG) * k + S / 2.0, (y - CY_ORIG) * k + S / 2.0)

    draw = ImageDraw.Draw(img)
    colors = [hex_rgba(c) if isinstance(c, str) else c for c in palette]
    for idx, (poly, role) in enumerate(FACETS):
        fill = colors[role]
        if overrides and idx in overrides:
            c = overrides[idx]
            fill = hex_rgba(c) if isinstance(c, str) else c
        draw.polygon([pt(x, y) for x, y in poly], fill=fill)
    return img.resize((size, size), Image.LANCZOS)


def render_svg(size, bg, palette, scale=0.68):
    k = (size * scale) / W_ORIG
    tx = size / 2.0 - CX_ORIG * k
    ty = size / 2.0 - CY_ORIG * k
    defs = ""
    rect = ""
    if isinstance(bg, tuple):
        defs = (
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{bg[0]}"/>'
            f'<stop offset="1" stop-color="{bg[1]}"/>'
            f'</linearGradient></defs>'
        )
        rect = f'<rect width="{size}" height="{size}" fill="url(#g)"/>'
    elif isinstance(bg, str):
        rect = f'<rect width="{size}" height="{size}" fill="{bg}"/>'
    paths = []
    for poly, role in FACETS:
        d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in poly) + " Z"
        paths.append(f'<path d="{d}" fill="{palette[role]}"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'{defs}{rect}<g transform="translate({tx:.3f} {ty:.3f}) scale({k:.5f})">{"".join(paths)}</g></svg>'
    )


def main():
    CLASSIC.mkdir(parents=True, exist_ok=True)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    WELCOME.mkdir(parents=True, exist_ok=True)

    full = {
        "Brand": (("#141416", "#050506"), ("#FFFFFF", "#D6D7DC", "#B9BCC5")),
        "Blue": (("#2B4C9B", "#0A1636"), ("#FFFFFF", "#C9DAFF", "#97B4F2")),
        "Graphite": (("#F4F4F6", "#CFCFD6"), ("#16161A", "#3A3A44", "#5B5B68")),
    }
    manifest = []
    for name, (bg, pal) in full.items():
        out_path = BRANDING / f"{name}.png"
        render_icon(1254, bg, pal, scale=0.68).convert("RGB").save(out_path, optimize=True)
        prev_path = PREVIEWS / f"{name}.png"
        Image.open(out_path).resize((300, 300), Image.LANCZOS).save(prev_path, optimize=True)
        manifest.append({
            "name": name,
            "original_dimensions": [1254, 1254],
            "preview_dimensions": [300, 300],
            "original_bytes": out_path.stat().st_size,
            "preview_bytes": prev_path.stat().st_size,
            "source_sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
        })
    (PREVIEWS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    glass = {
        "GlassBlue": ("#2B4C9B", "#0A1636"),
        "GlassGraphite": ("#38383E", "#0B0B0D"),
    }
    for name, bg in glass.items():
        render_bg(1024, bg).convert("RGB").save(BRANDING / f"{name}-Background.png", optimize=True)
        render_icon(1024, None, ("#FFFFFF", "#E2E4EC", "#C2C6D4"), scale=0.68).save(
            BRANDING / f"{name}-Logo.png", optimize=True
        )
        render_icon(256, bg, ("#FFFFFF", "#E2E4EC", "#C2C6D4"), scale=0.68).convert("RGB").save(
            BRANDING / f"{name}-Preview.png", optimize=True
        )

    classic_styles = {
        "Default": (("#2B2242", "#1A142B"), ("#FFFFFF", "#E3DAFF", "#BBA8FF"), None),
        "Alt": (("#9C7CFF", "#6E46EB"), ("#FFFFFF", "#EDE6FF", "#D5C5FF"), None),
        "Discord": (("#5865F2", "#3B45C4"), ("#FFFFFF", "#DFE3FF", "#BEC6FF"), None),
        "Spotify": ("#121214", ("#24F06D", "#1DB954", "#14873D"), None),
        "Extera": (("#E53935", "#AE1C19"), ("#FFFFFF", "#FFD5D4", "#FFABA8"), None),
        "Nothing": ("#F4F4F4", ("#121212", "#323236", "#54545A"), {2: "#D71921", 3: "#B51219", 4: "#8F0D13"}),
        "Bard": ("#FFFFFF", ("#4285F4", "#8B6CD9", "#E57350"), {2: "#9B72CB", 3: "#D96570", 4: "#F28B54"}),
        "Yaplus": (("#26152B", "#140A18"), ("#FF6B4A", "#E0309A", "#8B4BFF"), None),
        "Win95": ("#008080", ("#FFFFFF", "#C8C8C8", "#787878"), None),
        "MeiMei": (("#141416", "#070708"), ("#FFE28A", "#F2B838", "#BD8214"), None),
        "Extera2": (("#0B2A36", "#05151C"), ("#9CFBFF", "#29D3E6", "#0E98AD"), None),
    }

    for name, (bg, pal, overrides) in classic_styles.items():
        img = render_icon(1024, bg, pal, scale=0.68, overrides=overrides).convert("RGB")
        if name == "Win95":
            img = img.resize((64, 64), Image.BOX).resize((1024, 1024), Image.NEAREST)
        out = CLASSIC / f"{name}.png"
        img.save(out, optimize=True)
        img.resize((300, 300), Image.LANCZOS).save(CLASSIC / f"{name}-Preview.png", optimize=True)

    # Mark & SVG exports + Welcome logo + AltStore icon
    render_icon(1254, None, ("#FFFFFF", "#D6D7DC", "#B9BCC5"), scale=0.80).save(
        BRANDING / "VoidGram-mark.png", optimize=True
    )
    (BRANDING / "VoidGram-mark.svg").write_text(
        render_svg(1024, None, ("#FFFFFF", "#D6D7DC", "#B9BCC5"), scale=0.80)
    )
    (BRANDING / "VoidGram-icon.svg").write_text(
        render_svg(1024, ("#141416", "#050506"), ("#FFFFFF", "#D6D7DC", "#B9BCC5"), scale=0.68)
    )
    render_icon(480, None, ("#FFFFFF", "#D6D7DC", "#B9BCC5"), scale=0.80).save(
        WELCOME / "VoidGramWelcomeLogo@3x.png", optimize=True
    )
    Image.open(BRANDING / "Brand.png").resize((512, 512), Image.LANCZOS).save(
        ALTSTORE / "icon.png", optimize=True
    )
    print("Generated all Nowzen icon assets successfully.")


if __name__ == "__main__":
    main()
