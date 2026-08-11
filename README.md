# Pastor Assistant Agent OS — Computer Setup

This repository prepares a pastor's computer to use the Pastor Assistant Agent
OS plugin in ChatGPT and Codex.

It is **not** the prompting lesson, image lesson, or sermon-writing course.
Those can begin only after this setup is verified.

## What the pastor receives

The pastor pastes one short message into ChatGPT. The setup assistant then:

- checks whether the computer is a Mac or Windows PC;
- confirms the ChatGPT desktop app and the pastor's own account;
- checks PowerPoint and the plugin system;
- confirms the account can create images and editable presentation files;
- checks the included helper tools;
- asks explicit permission, then installs only what is missing and truly required;
- installs the Pastor Assistant Agent OS plugin;
- creates a private local learning workspace only after permission;
- verifies the plugin in a new chat.

The assistant gives **one question, permission request, or action at a time**.
It waits for `DONE` after an action and requires a clear answer for a question or
permission. If anything goes wrong, it stays on that step until the issue is
resolved.

## What is actually required

| Item | Needed? | Why |
|---|---:|---|
| ChatGPT desktop app | Yes | Runs Chat, Work, Codex, and plugins |
| Church-approved ChatGPT account | Yes | Each pastor signs in to their own approved account; no shared password |
| Pastor Assistant Agent OS plugin | Yes | Adds the sermon builder, reviewer, and approved-correction workflow |
| Private local OS folder | Yes | Keeps approved pastor preferences outside GitHub and outside the replaceable plugin |
| Image generation in ChatGPT | Yes | Creates sermon illustrations inside the guided workflow |
| Presentation creation in Work/Codex | Yes | Produces the editable `.pptx` file |
| Microsoft PowerPoint | Yes for PowerPoint delivery | Opens, edits, presents, and performs final visual review |
| Internet connection | Yes | ChatGPT, plugin download, research, and image generation |
| Java | No | Nothing in this repository uses Java |
| Node.js | No | Nothing in this repository uses Node.js |
| Git | No for the download route | Helpful for updates, but not required for a pastor |
| Python packages | No | The included helper scripts use Python's standard library only |

Pastors do not need to install Python for the brain. When ChatGPT/Codex already
provides Python, the private learning tool uses its standard library. When it
does not, the agent uses the bundled Markdown templates and local file tools.
Python may still be requested for an optional helper or unusual file conversion
only after that separate need is proven. LibreOffice and `pdftotext` remain
conditional fallbacks for old `.doc` files or PDF sermon notes.

## How the assistant improves

The plugin does not retrain ChatGPT and it never rewrites itself. It uses a safe
local loop:

1. Build the current work.
2. Review it independently.
3. Fix a confirmed mistake.
4. Ask whether one generalized correction should be saved.
5. Save it locally only after `YES, SAVE THIS RULE`.
6. Load approved rules before the next pastor task.

The local folder uses the Mac Application Support or Windows Local AppData
location. It stores generalized rules—not sermons, images, names, counseling
details, prayer requests, credentials, URLs, or private file paths. Repeated
lessons may become a local church-rule proposal, but only an administrator can
review and publish a shared plugin update.

## Give this to a pastor

1. Publish this source folder in a GitHub repository.
2. Choose a license and create an immutable tagged release.
3. Use the release builder to produce a pastor ZIP, checksum, and completed
   paste message pinned to that release and commit.
4. Send the generated paste message and release ZIP to the pastor. Tell the
   pastor to paste the plain-text message first and not unzip, run, or open the
   launcher until ChatGPT verifies the release.

The pastor may start in ordinary ChatGPT. If that chat cannot inspect or change
the local computer, the assistant will guide the pastor into the desktop app's
Work or Codex surface, one action at a time.

After release verification, the pastor may use the visual setup launcher. It uses a Mac System
Settings-style design on macOS and a Windows Settings-style design on Windows,
while reserving VF colors for church-branded elements. Its help box packages the
current question for the pastor's own ChatGPT account; it does not use an API key
or a second AI bill.

## Source repository contents

This owner repository includes publishing and test files that the release
builder intentionally removes from the pastor ZIP. The builder replaces this
README with `RELEASE-README.md` in the distributed folder.

- `SETUP-ASSISTANT.md` — the strict one-step-at-a-time setup protocol
- `index.html` and `setup-ui/` — the VF-branded Mac/Windows setup launcher
- `PASTE-INTO-CHATGPT.txt` — the only message the pastor needs to paste
- `AGENTS.md` — makes the same protocol active when the folder is opened in Codex
- `scripts/check_environment.py` — read-only Mac/Windows readiness check
- `scripts/prepare_plugin.py` — safe personal marketplace preparation, removal,
  and restore with recovery bundles
- `scripts/verify_release.py` — verifies every distributed file before setup
- `scripts/build_release.py` — builds the pastor ZIP, checksum, and paste message
- `.agents/plugins/marketplace.json` — repository plugin marketplace
- `plugins/sermon-slide-builder/` — the installable Pastor Assistant Agent OS
  plugin, including build, review, and approved-correction skills
- `SOFTWARE.md` — exact required and conditional software
- `SOURCES.md` — current official ChatGPT and plugin documentation
- `PUBLISHING-CHECKLIST.md` — owner-only steps before sharing the link
- `RELEASE-README.md` — the start page placed in the pastor release ZIP

## Important limitation

A GitHub URL cannot silently change a computer from a normal web chat. ChatGPT
can coach the setup from any supported chat, but it needs the desktop app's Work
or Codex access to inspect files or perform local setup actions. The protocol
handles that handoff without showing the pastor a long checklist.

This is a ChatGPT/Codex workflow plugin, not a PowerPoint add-in or a background
self-training model. It creates and checks editable `.pptx` files; PowerPoint
remains the program used to open and present them.

When the plugin later builds a deck, a recent pastor-approved sermon PowerPoint
is the layout authority. Sermon words stay in a separate text region and images
stay in a separate image frame—never text over an image.

For safety, pastors should receive a tagged release message generated after the
release ZIP is built. Do not give them a mutable `main` branch URL and ask an AI
to execute it.
