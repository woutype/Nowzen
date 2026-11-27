#!/usr/bin/env python3
"""Apply the native port patches only to their pinned upstream source tree."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from port_sources import missing_port_sources
from nowzen_enhancements import apply_nowzen_enhancements

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
source = args.source.resolve()
pin = json.loads((root / "upstream.json").read_text())
actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
if actual != pin["commit"]:
    raise SystemExit("Upstream commit differs from upstream.json; refusing to apply a mismatched patch")
patches = [
    root / "patches" / "voidgram-ghost-mode.patch",
    root / "patches" / "voidgram-custom-features.patch",
    root / "patches" / "voidgram-followup-features.patch",
    root / "patches" / "voidgram-developer-badges.patch",
    root / "patches" / "voidgram-interface-controls.patch",
    root / "patches" / "voidgram-badge-alignment.patch",
    root / "patches" / "voidgram-haptics-material.patch",
    root / "patches" / "voidgram-attachment-menu-motion.patch",
    root / "patches" / "voidgram-lyrics-word-sync.patch",
    root / "patches" / "voidgram-formatting-toolbar-layout.patch",
    root / "patches" / "voidgram-fixed-leading-badges.patch",
    root / "patches" / "voidgram-plugin-dialogs-keyboard.patch",
    root / "patches" / "voidgram-music-reference.patch",
    root / "patches" / "voidgram-peer-search.patch",
    root / "patches" / "voidgram-player-toolbar-refinements.patch",
    root / "patches" / "voidgram-music-inline-queue.patch",
    root / "patches" / "voidgram-fixed-player-fades.patch",
    root / "patches" / "voidgram-expanded-lyrics.patch",
    root / "patches" / "voidgram-big-update.patch",
    root / "patches" / "voidgram-settings-optimization.patch",
    root / "patches" / "voidgram-port-fixes.patch",
    root / "patches" / "voidgram-server-badges.patch",
    root / "patches" / "voidgram-blur-glass-corners.patch",
    root / "patches" / "voidgram-feature-gate.patch",
    root / "patches" / "voidgram-badge-desk-cosmetics.patch",
    root / "patches" / "voidgram-offer-black-hole-delete.patch",
    root / "patches" / "voidgram-offer-important-posts.patch",
    root / "patches" / "voidgram-offer-multi-reply.patch",
    root / "patches" / "voidgram-offer-voice-transcript.patch",
    root / "patches" / "voidgram-offer-visual-quote.patch",
    root / "patches" / "voidgram-offer-quick-sticker.patch",
    root / "patches" / "voidgram-offer-time-capsule.patch",
    root / "patches" / "voidgram-offer-postbox-allowlist.patch",
    root / "patches" / "voidgram-fixes-1106.patch",
    root / "patches" / "voidgram-gift-market.patch",
    root / "patches" / "voidgram-bot-chat-list.patch",
    root / "patches" / "voidgram-gift-actions.patch",
    root / "patches" / "voidgram-classic-media-bubbles.patch",
    root / "patches" / "voidgram-bubble-skins.patch",
    root / "patches" / "voidgram-video-download-background.patch",
    root / "patches" / "voidgram-welcome-wallpapers-glow.patch",
    root / "patches" / "voidgram-swipe-actions.patch",
    root / "patches" / "voidgram-avatar-frames-rating.patch",
    root / "patches" / "voidgram-name-styles.patch",
    root / "patches" / "voidgram-hide-classic-design.patch",
    root / "patches" / "voidgram-tabbar-reveal.patch",
    root / "patches" / "voidgram-fixes-1115.patch",
    root / "patches" / "voidgram-reorder.patch",
    root / "patches" / "voidgram-features-1119.patch",
    root / "patches" / "voidgram-features-1120.patch",
]
for patch in patches:
    subprocess.run(["git", "apply", "--recount", "--check", str(patch)], cwd=source, check=True)
    subprocess.run(["git", "apply", "--recount", str(patch)], cwd=source, check=True)

# The largest in-app logo is 100 pt (AyuSettingsHeaderItem); the icon picker is
# at most 72 pt. Ship 300 px previews for 3x screens instead of decoding 1254 px
# launcher artwork in these rows. Icon Composer keeps its full-size originals.
for name in ("Brand", "Blue", "Graphite"):
    preview = root / "assets/branding/previews" / (name + ".png")
    image_set = source / "submodules/TelegramUI/Images.xcassets/AyuGram" / (name + ".imageset")
    shutil.copy2(preview, image_set / "AyuGram.png")
    contents_path = image_set / "Contents.json"
    contents = json.loads(contents_path.read_text())
    contents["images"][0]["scale"] = "3x"
    contents_path.write_text(json.dumps(contents, indent=2) + "\n")

# VoidGram artwork replaces the launcher icons the patches ship: the full-bleed
# Icon Composer layers and the glass icons' backdrop and glass logo.
voidgram = root / "assets/branding/voidgram"
icons = source / "Telegram/Telegram-iOS"
for name, folder in (("Brand", "Telegram"), ("Blue", "AyuBlue"), ("Graphite", "AyuGraphite")):
    shutil.copy2(voidgram / (name + ".png"), icons / (folder + ".icon") / "Assets" / "AyuGram.png")
for name in ("GlassBlue", "GlassGraphite"):
    for layer in ("Background", "Logo"):
        shutil.copy2(voidgram / f"{name}-{layer}.png", icons / f"Ayu{name}.icon" / "Assets" / f"{layer}.png")
    shutil.copy2(voidgram / f"{name}-Preview.png", source / "submodules/TelegramUI/Images.xcassets/AyuGram" / f"{name}.imageset" / "AyuGram.png")

# The classic styles, redrawn with the VoidGram mark (assets/branding/voidgram/styles.py), and
# the MeiMei mascot in the Chibi slot. Each is one full-bleed layer on its own background colour;
# the picker shows a 300 px preview. Chibi2 is gone.
classic_fills = {
    "Default": "#2B2242", "Alt": "#9C7CFF", "Discord": "#5865F2", "Spotify": "#121212",
    "Extera": "#E53935", "Nothing": "#F4F4F4", "Bard": "#FFFFFF", "Yaplus": "#26152B",
    "Win95": "#008080", "Chibi": "#141416", "Extera2": "#0B2A36",
}
classic_art = {"Chibi": "MeiMei"}
shutil.rmtree(icons / "AyuOriginalChibi2.icon")
shutil.rmtree(source / "submodules/TelegramUI/Images.xcassets/AyuGram/OriginalChibi2.imageset")
for name, fill in classic_fills.items():
    art = classic_art.get(name, name)
    bundle = icons / f"AyuOriginal{name}.icon"
    for old in (bundle / "Assets").iterdir():
        old.unlink()
    shutil.copy2(voidgram / "classic" / f"{art}.png", bundle / "Assets" / "Nowzen.png")
    icon = json.loads((bundle / "icon.json").read_text())
    red, green, blue = (int(fill[i:i + 2], 16) / 255 for i in (1, 3, 5))
    icon["fill"] = {"solid": f"extended-srgb:{red:.5f},{green:.5f},{blue:.5f},1.00000"}
    for group in icon["groups"]:
        for layer in group["layers"]:
            layer["image-name"] = "Nowzen.png"
            layer["name"] = f"Nowzen {art}"
            layer.pop("position", None)
    (bundle / "icon.json").write_text(json.dumps(icon, indent=2) + "\n")

    image_set = source / "submodules/TelegramUI/Images.xcassets/AyuGram" / f"Original{name}.imageset"
    for old in image_set.iterdir():
        old.unlink()
    shutil.copy2(voidgram / "classic" / f"{art}-Preview.png", image_set / "Nowzen.png")
    contents = {"images": [{"idiom": "universal", "filename": "Nowzen.png", "scale": "3x"}], "info": {"author": "xcode", "version": 1}}
    (image_set / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")

# iOS caches each alternate icon's flat rendering by its name.
(icons / "AyuOriginalChibi.icon").rename(icons / "AyuMeiMei.icon")

for badge_name in ("ExteraBadge", "ExteraDeveloperBadge"):
    badge_src = root / "assets" / "branding" / f"{badge_name}.imageset"
    if badge_src.is_dir():
        badge_dst = source / "submodules" / "TelegramUI" / "Images.xcassets" / "AyuGram" / f"{badge_name}.imageset"
        badge_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(badge_src, badge_dst, dirs_exist_ok=True)

app_badge_src = root / "assets" / "branding" / "AppBadge@3x.png"
if app_badge_src.is_file():
    app_badge_dst = source / "submodules" / "TelegramUI" / "Images.xcassets" / "Components" / "AppBadge.imageset" / "AppBadge@3x.png"
    app_badge_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(app_badge_src, app_badge_dst)

# TelegramUIResources includes Resources/**/* in the application bundle.
font_src = root / "assets" / "fonts" / "YSMusic-HeadlineBold.ttf"
font_dst = source / "submodules" / "TelegramUI" / "Resources" / font_src.name
font_dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(font_src, font_dst)

# Bubble skins (AyuBubbleSkin.swift): the gold frame's 9-slice and ornaments and the grey
# skin's pattern tile, loaded from the bundle by name.
for bubble_asset in sorted((root / "assets" / "bubbles").glob("VoidGramBubble*@3x.png")):
    shutil.copy2(bubble_asset, source / "submodules" / "TelegramUI" / "Resources" / bubble_asset.name)
# The first screen's logo and the wallpapers offered in Themes, colours & badges.
shutil.copy2(root / "assets" / "welcome" / "NowzenWelcomeLogo@3x.png", source / "submodules" / "TelegramUI" / "Resources" / "NowzenWelcomeLogo@3x.png")
for wallpaper in sorted((root / "assets" / "wallpapers").glob("NowzenWallpaper*.jpg")):
    shutil.copy2(wallpaper, source / "submodules" / "TelegramUI" / "Resources" / wallpaper.name)


def apply_nowzen_branding(src: Path):
    """Remove author credits/ads/easter-eggs and rebrand VoidGram -> Nowzen."""
    import re

    # 1. Remove easter-egg Swift files
    for rel in (
        "submodules/SettingsUI/Sources/AyuEblanButton.swift",
        "submodules/SettingsUI/Sources/AyuNatsukinMusic.swift",
    ):
        (src / rel).unlink(missing_ok=True)

    # 2. Clean AyuSettingsController.swift (remove AyuNatsukinMusicButton block)
    settings_ctrl = src / "submodules/SettingsUI/Sources/AyuSettingsController.swift"
    if settings_ctrl.is_file():
        text = settings_ctrl.read_text(encoding="utf-8")
        text = re.sub(
            r"\n\s*// Easter egg:.*?controller\.didDisappear = \{ _ in\n\s*music\.stop\(\)\n\s*\}",
            "",
            text,
            flags=re.S,
        )
        settings_ctrl.write_text(text, encoding="utf-8")

    # 3. Clean AyuGramSettingsController.swift (remove CREDITS, author/channel links, and AyuEblan pull easter egg)
    main_ctrl = src / "submodules/SettingsUI/Sources/AyuGramSettingsController.swift"
    if main_ctrl.is_file():
        text = main_ctrl.read_text(encoding="utf-8")
        # Remove LINKS section entries (channel/group) and CREDITS section entries
        text = re.sub(
            r'\n\s*\.header\(6, 70, AyuStrings\.links\.text\(ru\)\),\n\s*link\(6, \.channel[^\n]*\n\s*link\(6, \.sourceCode[^\n]*\n\s*link\(6, \.officialGroup[^\n]*',
            '\n            .header(6, 70, AyuStrings.links.text(ru)),\n            link(6, .sourceCode, AyuStrings.sourceCode.text(ru), "GitHub")',
            text,
        )
        text = re.sub(
            r'\n\s*entries\.append\(contentsOf:\s*\[\s*\n\s*\.header\(8, 90, ru \? "КТО ДЕЛАЛ" : "CREDITS"\),.*?\]\)',
            "",
            text,
            flags=re.S,
        )
        # Update sourceCode URL to woutype/Nowzen
        text = text.replace("https://github.com/neosay-dev/VoidGram", "https://github.com/woutype/Nowzen")
        # Remove AyuEblanPullButton block
        text = re.sub(
            r"\n\s*// The first pull brings out the search field;.*?(?=\n\s*controller\.contentOffsetChanged)",
            "",
            text,
            flags=re.S,
        )
        text = re.sub(
            r"\n\s*var eblanArmed = false\n\s*controller\.beganInteractiveDragging = \{[^}]*\}",
            "",
            text,
            flags=re.S,
        )
        text = re.sub(
            r"\n\s*guard let controller, case let \.known\(value\) = offset else \{ return \}.*?eblan\.update\(pull: eblanArmed \? -value : 0\.0\)",
            "",
            text,
            flags=re.S,
        )
        text = text.replace(
            "controller.contentOffsetChanged = { [weak controller] offset, _ in",
            "controller.contentOffsetChanged = { offset, _ in",
        )
        main_ctrl.write_text(text, encoding="utf-8")

    # Fix jagged profile section corner artifacts with continuous CALayer mask
    section_container = src / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenItemSectionContainerNode.swift"
    if section_container.is_file():
        stext = section_container.read_text(encoding="utf-8")
        old_mask_block = """        if clipsCorners && hasCorners {
            let radius: CGFloat = 26.0
            let panel = CGRect(x: 0.0, y: contentWithBackgroundOffset, width: width, height: max(0.0, contentWithBackgroundHeight - contentWithBackgroundOffset))
            let path = UIBezierPath(rect: CGRect(x: 0.0, y: -1000.0, width: width, height: 1000.0 + panel.minY))
            if panel.height / 2.0 <= radius {
                // A one-row section is a full pill. UIBezierPath's rounded rect is a different, wider shape at
                // this radius, and the row's own corners showed as dark slivers beside it (My Profile in Settings):
                // true half-circles cut them.
                path.append(UIBezierPath(cgPath: CGPath(roundedRect: panel, cornerWidth: panel.height / 2.0, cornerHeight: panel.height / 2.0, transform: nil)))
            } else {
                path.append(UIBezierPath(roundedRect: panel, cornerRadius: radius))
            }
            path.append(UIBezierPath(rect: CGRect(x: 0.0, y: panel.maxY, width: width, height: max(0.0, contentHeight - panel.maxY) + 1000.0)))
            let mask = (self.itemContainerNode.layer.mask as? CAShapeLayer) ?? CAShapeLayer()
            mask.path = path.cgPath
            self.itemContainerNode.layer.mask = mask
            self.backgroundNode.cornerRadius = min(radius, panel.height / 2.0)
            if #available(iOS 13.0, *) {
                self.backgroundNode.layer.cornerCurve = panel.height / 2.0 <= radius ? .circular : .continuous
            }
        }"""
        new_mask_block = """        if clipsCorners && hasCorners {
            let radius: CGFloat = 26.0
            let panel = CGRect(x: 0.0, y: contentWithBackgroundOffset, width: width, height: max(0.0, contentWithBackgroundHeight - contentWithBackgroundOffset))
            let clampedRadius = min(radius, panel.height / 2.0)
            let maskRoot: CALayer
            if let existing = self.itemContainerNode.layer.mask, existing.sublayers?.count == 3 {
                maskRoot = existing
            } else {
                maskRoot = CALayer()
                for _ in 0 ..< 3 {
                    let sub = CALayer()
                    sub.backgroundColor = UIColor.black.cgColor
                    maskRoot.addSublayer(sub)
                }
                self.itemContainerNode.layer.mask = maskRoot
            }
            if let subs = maskRoot.sublayers, subs.count == 3 {
                subs[0].frame = CGRect(x: 0.0, y: -1000.0, width: width, height: 1000.0 + panel.minY)
                subs[1].frame = panel
                subs[1].cornerRadius = clampedRadius
                if #available(iOS 13.0, *) {
                    subs[1].cornerCurve = .continuous
                }
                subs[2].frame = CGRect(x: 0.0, y: panel.maxY, width: width, height: max(0.0, contentHeight - panel.maxY) + 1000.0)
            }
            self.backgroundNode.cornerRadius = clampedRadius
            if #available(iOS 13.0, *) {
                self.backgroundNode.layer.cornerCurve = .continuous
            }
        }"""
        if old_mask_block in stext:
            stext = stext.replace(old_mask_block, new_mask_block)
            section_container.write_text(stext, encoding="utf-8")

    # 4. Update AyuAppIconCatalog.swift with all 16 Nowzen colorways
    catalog = src / "submodules/TelegramPresentationData/Sources/AyuAppIconCatalog.swift"
    if catalog.is_file():
        catalog.write_text(
            '''import Foundation

public struct AyuAppIconPreset {
    public let name: String?
    public let assetName: String
    public let title: String
    public let russianTitle: String
}

public enum AyuAppIconCatalog {
    public static let presets: [AyuAppIconPreset] = [
        AyuAppIconPreset(name: nil, assetName: "AyuGram/Brand", title: "Nowzen", russianTitle: "Nowzen"),
        AyuAppIconPreset(name: "AyuBlue", assetName: "AyuGram/Blue", title: "Nowzen Blue", russianTitle: "Nowzen · синий"),
        AyuAppIconPreset(name: "AyuGraphite", assetName: "AyuGram/Graphite", title: "Nowzen Light", russianTitle: "Nowzen · светлый"),
        AyuAppIconPreset(name: "AyuGlassBlue", assetName: "AyuGram/GlassBlue", title: "Glass Blue", russianTitle: "Стекло · синий"),
        AyuAppIconPreset(name: "AyuGlassGraphite", assetName: "AyuGram/GlassGraphite", title: "Glass Graphite", russianTitle: "Стекло · графит"),
        AyuAppIconPreset(name: "AyuOriginalDefault", assetName: "AyuGram/OriginalDefault", title: "Nowzen Violet", russianTitle: "Nowzen · фиолетовый"),
        AyuAppIconPreset(name: "AyuOriginalAlt", assetName: "AyuGram/OriginalAlt", title: "Nowzen Lavender", russianTitle: "Nowzen · лаванда"),
        AyuAppIconPreset(name: "AyuOriginalDiscord", assetName: "AyuGram/OriginalDiscord", title: "Nowzen Indigo", russianTitle: "Nowzen · индиго"),
        AyuAppIconPreset(name: "AyuOriginalSpotify", assetName: "AyuGram/OriginalSpotify", title: "Nowzen Emerald", russianTitle: "Nowzen · изумруд"),
        AyuAppIconPreset(name: "AyuOriginalExtera", assetName: "AyuGram/OriginalExtera", title: "Nowzen Crimson", russianTitle: "Nowzen · алый"),
        AyuAppIconPreset(name: "AyuOriginalNothing", assetName: "AyuGram/OriginalNothing", title: "Nowzen Mono", russianTitle: "Nowzen · моно"),
        AyuAppIconPreset(name: "AyuOriginalBard", assetName: "AyuGram/OriginalBard", title: "Nowzen Aurora", russianTitle: "Nowzen · аврора"),
        AyuAppIconPreset(name: "AyuOriginalYaplus", assetName: "AyuGram/OriginalYaplus", title: "Nowzen Sunset", russianTitle: "Nowzen · закат"),
        AyuAppIconPreset(name: "AyuOriginalWin95", assetName: "AyuGram/OriginalWin95", title: "Nowzen Retro", russianTitle: "Nowzen · ретро"),
        AyuAppIconPreset(name: "AyuMeiMei", assetName: "AyuGram/OriginalChibi", title: "Nowzen Gold", russianTitle: "Nowzen · золото"),
        AyuAppIconPreset(name: "AyuOriginalExtera2", assetName: "AyuGram/OriginalExtera2", title: "Nowzen Cyan", russianTitle: "Nowzen · циан"),
    ]
}
''',
            encoding="utf-8",
        )

    # 5. Rebrand Telegram/BUILD and all modified Swift sources: VoidGram -> Nowzen
    build_file = src / "Telegram/BUILD"
    if build_file.is_file():
        btext = build_file.read_text(encoding="utf-8")
        btext = btext.replace("VoidGram", "Nowzen")
        build_file.write_text(btext, encoding="utf-8")

    changed = set()
    for args in (["diff", "--name-only", "-z", "HEAD"], ["ls-files", "--others", "--exclude-standard", "-z"]):
        out = subprocess.check_output(["git", *args], cwd=src)
        changed.update(p.decode("utf-8") for p in out.split(b"\0") if p.endswith(b".swift"))

    for rel in sorted(changed):
        fpath = src / rel
        if not fpath.is_file():
            continue
        t = fpath.read_text(encoding="utf-8")
        updated = (
            t.replace("https://github.com/neosay-dev/VoidGram", "https://github.com/woutype/Nowzen")
            .replace("VoidGramWelcomeLogo", "NowzenWelcomeLogo")
            .replace("VoidGramWallpaper", "NowzenWallpaper")
            .replace("VoidGram", "Nowzen")
            .replace("VOIDGRAM", "NOWZEN")
        )
        if updated != t:
            fpath.write_text(updated, encoding="utf-8")


apply_nowzen_enhancements(source)
apply_nowzen_branding(source)

missing = missing_port_sources(source)
if missing:
    raise SystemExit("Port patch is missing required native source files:\n" + "\n".join(missing))
print("Applied native Nowzen changes to " + actual)

