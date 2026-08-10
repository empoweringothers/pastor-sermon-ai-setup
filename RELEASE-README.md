# Pastor Sermon AI — Verified Setup Folder

This folder contains the computer and plugin setup package. It is not the
prompting or sermon-image lesson.

## Start with the separate setup message

The church setup owner sends `PASTOR-SETUP-MESSAGE.txt` beside the release ZIP.
That plain-text message is the only starting point.

1. Paste the separate message into ChatGPT.
2. Follow the one action ChatGPT gives you.
3. Do not run a script or open `index.html` until ChatGPT verifies the ZIP
   checksum and this folder's integrity file.

If you opened this folder before verification, stop here. Return to the separate
setup message and let ChatGPT verify the release first.

After verification, ChatGPT may ask you to open `index.html`. That optional
launcher uses a Mac System Settings-style view on a Mac and a Windows
Settings-style view on Windows. It can package a setup question for your own
ChatGPT account without an API key. The setup chat remains the authority.

## Included in this release

- `SETUP-ASSISTANT.md` — the one-step-at-a-time setup protocol
- `RELEASE.json` and `FILE-SHA256SUMS.json` — pinned release identity and file
  integrity records
- `index.html` and `setup-ui/` — optional post-verification launcher
- `scripts/verify_release.py` — verifies every included file
- `scripts/check_environment.py` — read-only setup check
- `scripts/prepare_plugin.py` — permissioned plugin-source preparation and
  recovery
- `.agents/plugins/marketplace.json` and `plugins/sermon-slide-builder/` — the
  installable Sermon Slide Builder plugin
- `SOFTWARE.md` and `SOURCES.md` — software boundaries and official sources

Java and Node.js are not required. Python uses only its standard library and is
needed only for the local helper-script route.
