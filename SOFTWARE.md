# Software Decisions

This file is for the setup assistant and the repository owner. It is not a
pastor-facing lesson.

## Required

### ChatGPT desktop

Required for the intended local setup, Plugins Directory, file access, and the
Work or Codex surface. The pastor signs in with their own account. Do not create
shared passwords or ask the pastor to reveal credentials.

Approved source: `learn.chatgpt.com/docs/app` or a download link reached from
that official OpenAI page. Show the domain before asking permission.

### Pastor Assistant Agent OS plugin

Required. It is included under `plugins/sermon-slide-builder/` and listed in
`.agents/plugins/marketplace.json`. The technical folder name stays stable so
existing installations can update safely.

### Private local Pastor Assistant OS folder

Required for approved corrections to carry into future chats. It is created
only after explicit permission under the Mac Application Support folder or the
Windows Local AppData folder. It is outside the plugin, outside the release,
and outside GitHub so an update cannot overwrite it.

### Image generation

Required on the pastor's ChatGPT account. This is an account capability, not a
Java or local software package. If it is unavailable, check account or workspace
settings instead of installing an unofficial image tool.

### Editable presentation creation

Required in ChatGPT Work or Codex for end-to-end `.pptx` creation. The plugin
provides the workflow and guardrails; the host provides the presentation tools.

### Microsoft PowerPoint

Required when the church expects editable `.pptx` delivery and native final
review. Do not purchase a license automatically. If it is missing or unlicensed,
pause for the church's Microsoft 365 administrator.

Approved source: `microsoft.com/microsoft-365/powerpoint`, the Microsoft Store,
or the church's managed Microsoft 365 installer. Do not use third-party download
sites.

### Internet

Required for ChatGPT, plugin distribution, current-source research, and AI image
generation.

## Conditional

### Python 3

The sermon helpers and deterministic Pastor Assistant OS manager use only
Python's standard library. No `pip` install is needed. Python is not required
for the Markdown brain itself: when the host has no Python launcher, the agent
uses the bundled workspace template and local file tools. Request a system
Python only when a separate helper or file conversion truly requires it.

Approved source when it is truly required: `python.org/downloads` or the
computer's church-managed software catalog.

### LibreOffice

Conditional fallback for reading legacy `.doc` sermon notes outside macOS or
for preliminary rendering when PowerPoint is unavailable. Prefer converting the
note to `.docx` and using PowerPoint instead.

Approved source when it is truly required: `libreoffice.org/download` or the
computer's church-managed software catalog.

### Poppler `pdftotext`

Conditional only when a PDF sermon note must be parsed locally. Prefer the
original `.docx` sermon note.

Official project information: `poppler.freedesktop.org`. There is no simple
official Windows installer intended for novice users, so prefer the original
`.docx` or a trusted church-managed conversion rather than an arbitrary download.

### Microsoft Word

Conditional when the pastor requests an editable audience handout and wants
native Word review. It is not required for image-only PowerPoint work.

### Church template fonts

Conditional for an exact match to an existing deck. Licensed fonts must come
from the church or its template. The setup assistant may verify them but must
not download paid fonts from unapproved sources.

### Git

Optional for maintainers who want updates through cloning. Pastors can use the
GitHub ZIP route and do not need Git. Git is required for the repository owner
when running the public release builder because the builder verifies the exact
clean commit, release tag, and GitHub origin before packaging.

## Not required

- Java
- Node.js or npm
- an OpenAI API key
- a database
- a local web server
- a third-party memory server

Do not install any of these for this workflow unless the repository changes and
a new, verified dependency is documented here.

## Download rule

Before any software change, the setup assistant must display the exact official
domain, the one item being installed, whether administrator approval is needed,
and the exact permission phrase. A search-result page or third-party mirror is
not an approved source.
