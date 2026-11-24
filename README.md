# Nowzen

Nowzen is an unofficial Telegram client for iOS.

<img src="assets/branding/voidgram/VoidGram-icon.svg" width="128" alt="Nowzen logo">

## Features

- **Custom App Icon & Colorways**: Built-in in-app icon switcher (`Settings → Nowzen → Appearance / App Icon`) with 16 color variants including dark, blue, light, liquid glass, emerald, crimson, mono, aurora, sunset, retro, gold, and cyan.
- **Ghost Mode**: Per-account controls for read receipts, online status, typing/recording indicators, and upload progress (`Settings → Privacy and Security → Nowzen · Ghost Mode`).
- **Message History**: Local edit/deletion ledger, formatting and reaction snapshots, and reversible local message hiding.
- **Plugins**: JavaScript, Python, and native plugin support.
- **Music Player & Lyrics**: Synchronized lyrics, track recognition, and 120 Hz animations.
- **Appearance & Interface**: Custom bubble skins, chat colors, MessageShot, and tab bar customization.

## Cloud Builds (GitHub Actions)

Every push to `main` automatically runs **Nowzen iOS Build & Release** (`.github/workflows/build.yml`):
- Applies the native port patches onto the pinned `Telegram-iOS` commit (`upstream.json`).
- Uses `actions/cache` for the Bazel disk cache (`nowzen-bazel-*`) so subsequent builds reuse compiled artifacts and run significantly faster.
- Builds `release_arm64` `.ipa` and TrollStore `.tipa` packages and publishes a new versioned GitHub Release (`v1.0.<run_number>`).

Configure `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` in **Repository Settings → Secrets and variables → Actions** for Telegram login support.

## Local macOS Preparation

```sh
git clone https://github.com/TelegramMessenger/Telegram-iOS.git telegram
git -C telegram checkout fb0e62ba8a147f0821da6aa63c09da7d79a10111
python3 ci/prepare.py telegram
```

## License & Attribution

Based on [Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS). Preserve upstream notices and comply with applicable licenses before distributing binaries.
