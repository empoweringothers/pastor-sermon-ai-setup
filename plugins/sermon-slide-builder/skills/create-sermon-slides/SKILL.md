---
name: create-sermon-slides
description: Create or update image-rich PowerPoint sermon decks and optional Word audience handouts from Word, text, or PDF sermon notes, especially notes that use SL/Sl as slide cues. Use when converting a pastor's notes into PPTX, researching or generating sermon visuals, following a supplied church template, preserving a pastor's wording and theology, or auditing sermon materials against source notes.
---

# Create Sermon Slides

Turn sermon notes into editable, sourced presentation files while treating the
pastor's wording as the authority. Interpret `SL` as "slide," not as sermon
content.

Set `SKILL_DIR` to the absolute path of this skill before running its scripts.
The helper scripts require Python 3.9 or newer and use only the standard
library. They do not require Java, Node.js, `python-pptx`, or `python-docx`.

## Read the Relevant References

- Read `references/wording-fidelity.md` for every create, edit, or audit task.
- Read `references/image-research-policy.md` before finding or generating any
  visual.
- Read `references/biblical-photorealistic-image-set.md` before planning or
  generating any biblical scene or biblical character.
- Read `references/church-style-profile.md` before choosing a canvas, template,
  fonts, colors, or Scripture default for a new church.

## Non-Negotiable Rules

1. Treat case-insensitive `SL`, `Sl`, `sl`, `SL-`, `SL –`, parenthesized forms
   such as `(SL – theme slide)`, and an occasional mistyped numeric prefix such
   as `3Sl` as slide boundaries.
2. Map one cue to one slide by default. Split a cue only when verbatim Scripture
   or a long list cannot remain readable. Do not merge, reorder, or omit cues
   without explicit approval.
3. Preserve the pastor's visible wording, theology, Bible translation,
   emphasis, outline numbering, quotations, and intended sequence. Do not
   "improve" the sermon.
4. Use prose around a cue to understand the visual and the speaking context.
   Do not silently turn surrounding sermon prose into new slide copy.
5. Put production directions such as `(pic of lake)` or `Video` in the build
   plan, not on screen, unless the source deck intentionally displays a
   placeholder.
6. Use authentic sourced photographs for real people, real news, actual events,
   identifiable places, products, screenshots, or documentary claims. Never
   present an AI-generated image as news or historical evidence.
7. Use realistic AI-generated imagery only for conceptual, metaphorical,
   biblical, or clearly illustrative scenes. Record it as an AI-generated
   illustration in the source notes.
8. Keep the pastor and identifiable church members as authentic source pixels.
   Do not generate, face-swap, beautify, or reshape their likenesses.
   AI may create a separate background without changing the person.
9. Never overwrite the sermon note, the reference deck, or any PowerPoint that
   is open. A nearby `~$filename.pptx` means the file is locked; copy it to a
   work directory and leave the live file untouched.
10. Use a recent pastor-approved sermon PowerPoint as the layout authority when
    one is supplied. Reuse its slide geometry, spacing, type scale, and separate
    text and image regions.
11. Never place sermon words on top of a photograph or AI-generated image. Keep
    text and pictures in separate frames. A slide may be image-only or text-only
    when the pastor's approved examples establish that pattern.
12. For a photorealistic biblical image set, generate one image for each main
    point and first-level lettered subpoint only. Do not add images for numbered
    nested points, bullets, applications, introductions, conclusions, or
    Scripture-continuation slides unless the pastor explicitly requests one.
13. Keep every recurring biblical character visually consistent within the
    sermon. Create a sermon-specific continuity record first, approve the
    character's first required image as the visual anchor, and use that anchor
    for every later scene. Peter must look like the same Peter throughout.
14. Generated artwork contains no sermon text, Scripture, labels, captions,
    letters, numbers, logos, borders, signatures, or watermarks.

## Workflow

### 1. Resolve the Inputs

Obtain:

- The authoritative sermon note.
- The intended service/date and AM/PM context.
- A same-series starter deck or a recent approved sermon deck.
- The delivery format: existing ultrawide, `HD`/16:9, or both.

Prefer explicitly supplied files. Do not search email, cloud drives, shared
church storage, or other private locations unless the pastor asks and the host
has authorized read access. Never send, move, label, delete, or share private
church material during a search.

### 2. Extract the Slide Cues

Run:

```bash
python3 "$SKILL_DIR/scripts/extract_slide_cues.py" "<sermon-note.docx>" \
  --out "<work-dir>/slide-cues.json"
```

PowerShell equivalent:

```powershell
py -3 "$env:SKILL_DIR\scripts\extract_slide_cues.py" "<sermon-note.docx>" `
  --out "<work-dir>\slide-cues.json"
```

Review every cue in order. The script includes nearby paragraphs only as
context. Treat `visible_text_candidate` as source material, not permission to
rewrite it.

Create a build record for every output slide:

- source cue and paragraph number;
- exact visible copy;
- production direction;
- outline level, generated-image eligibility, and the scope reason or recorded
  pastor override;
- visual type (`actual`, `AI illustration`, `provided`, or `none`);
- recurring character IDs and life-stage continuity phase;
- source URL/file or generation record;
- any approved copy change;
- mapped source slide/layout.

### 3. Choose the PowerPoint Route

Use the host's native PowerPoint/presentation capability. In Codex, use the
Presentations workflow and follow its template-following and QA requirements.

- When a starter/reference PPTX exists, duplicate suitable source slides and
  edit inherited elements. Preserve its master, layouts, dimensions, fonts,
  backgrounds, footer marks, and safe zones.
- Preserve a supplied church deck's exact canvas. When no template exists, ask
  whether the church uses ordinary 16:9 or a special sanctuary screen; default
  to 16:9 only after confirming there is no special screen.
- When no reference deck exists, build a simple sermon-specific visual system:
  a dedicated text region beside a dedicated image region, very large readable
  type, restrained accents, and a small consistent series/title mark.
- When topical imagery is requested and the reference deck permits a split
  composition, use a consistent text-left, picture-right layout on content
  slides. Reserve full-width or text-only treatment for a supplied series
  opener, a cue that explicitly calls for it, or a user-directed exception.
- Never use a photograph or generated image as a background behind sermon text.
  For full-width art, make the slide image-only or place text on a separate
  solid-color panel that does not overlap the image.
- Produce `.pptx` first. Import the verified PPTX into Google Slides only when
  the user requests a native Google Slides copy.

### 4. Research and Create Visuals

Classify the requested visual before acquiring it.

For a biblical image set, first create `biblical-image-plan.md` and
`character-continuity.md` as defined in
`references/biblical-photorealistic-image-set.md`. Plan all eligible headings,
but generate only one image at a time in sermon order; do not parallel-generate
scenes that share a recurring character. Before a recurring
character appears again, approve the first required image containing that
character and use it as a reference input when supported. If reference inputs
are unavailable, repeat the complete continuity description and reject any
identity drift before proceeding.

- Search only pastor-approved church folders for church members, ministry
  events, or supplied photos.
- Browse current primary or official sources for news, public figures, current
  statistics, recent events, and exact quotations.
- Prefer official, public-domain, Creative Commons, or clearly licensed raster
  images. Record the creator/source, URL, date accessed, and license/usage
  context.
- Generate a true-to-life illustration only when the subject is illustrative.
  Specify the dedicated image-frame ratio, crop, subject placement, lighting,
  lens language, historical details, continuity anchors, and "no text/no logos"
  in the image prompt. Compose for the image frame, not for text inside the art.
- Do not generate lookalike photographs of an identifiable current event,
  public figure, church member, or congregation.

### 5. Author the Deck

- Keep cue wording verbatim by default; remove only the `SL` marker and genuine
  production instructions.
- Use one clear idea and usually one dominant visual per slide.
- Keep the sermon cue in the text-safe area and the topical image in the
  image-safe area established by the church profile. When no profile exists,
  use a consistent text-left, image-right content layout. Do not alternate sides
  merely for variety.
- Match the arrangement of the pastor's recent approved sermon examples before
  inventing a layout. Do not copy old sermon wording or imagery—copy only the
  approved layout system.
- Preserve the source template's font sizes. Do not shrink text merely to force
  it into a frame.
- Split long Scripture across consecutive slides without changing words or
  verse order.
- When the cue supplies only a reference and full Scripture is required, ask
  for the church's default translation if the note or template does not already
  establish one. Never guess the translation.
- Keep images sharp at full-stage size and crop for the actual frame.
- Place each generated biblical image only in its dedicated image frame. Do not
  use the artwork as a background behind the sermon wording.
- Add a `[Sources]` block to speaker notes for each researched claim and asset.
  Mark generated work as `[AI-generated illustration]`.
- Keep videos as supplied media when available. Otherwise create an intentional
  placeholder/still and identify the missing media in the handoff.

### 6. Build a Companion Word Handout When Requested

Use the Documents workflow and recent approved weekly handouts as formatting
references. Do not treat the full speaker manuscript as the audience-handout
template simply because its filename contains `handout`.

- Match the nearest pastor-approved weekly handout for page size, margins,
  typography, paragraph density, indentation, emphasis, numbering, page count,
  and blank density. If none exists, ask before choosing a format.
- Condense by omitting paragraphs, not by paraphrasing Pastor's retained words.
- Remove `SL` cues, production directions, and cue highlighting from the audience
  copy.
- Use only a few purposeful blanks on major outline terms and central takeaways.
  Match the recent weekly density; when no closer example exists, use about 8–12
  blanks across a four-page handout. Never turn most sentences into blanks.
- Preserve Scripture wording and visible emphasis. Do not silently repair source
  citations or theology.
- Produce an editable `.docx`. Do not create InDesign output unless the user asks
  for it explicitly.

### 7. Validate

Render and inspect every slide at full size. Fix clipping, poor crops, unresolved
placeholders, low contrast, blurry media, and accidental template changes.

Prefer a native PowerPoint render/export for final QA. If the host has no
presentation renderer, export a working copy to PDF in desktop PowerPoint. When
PowerPoint is unavailable, use LibreOffice headless export only as a preliminary
fallback, render the PDF pages to images, and inspect each page plus a contact
sheet. Treat font equivalence as unverified until the deck is opened or exported
on a machine with the required fonts. Compare every referenced font against the
installed fonts and flag substitutions or reflow; never shrink text merely to
hide a missing-font problem.

Run the host presentation overflow/fidelity checks, then run:

```bash
python3 "$SKILL_DIR/scripts/audit_slide_fidelity.py" \
  "<sermon-note.docx>" "<final-deck.pptx>" \
  --out "<work-dir>/fidelity-report.json"
```

PowerShell equivalent:

```powershell
py -3 "$env:SKILL_DIR\scripts\audit_slide_fidelity.py" `
  "<sermon-note.docx>" "<final-deck.pptx>" `
  --out "<work-dir>\fidelity-report.json"
```

Manually review every result whose status is not `strong`. In particular,
`source-context-additions-review` means the deck added words found in the sermon
body but not in the `SL` cue; those additions still need a recorded approval.
A visual-only cue can legitimately have little text, but it still needs the
intended image.
Confirm that every actual-news/event image is authentic and every AI image is
identified in notes.
For a biblical image set, inspect a contact sheet for face, age, build, hair,
beard, costume, prop, lighting, color-grade, and historical-detail drift. Reject
later scenes in which Peter or any recurring character no longer matches the
approved sermon-specific anchor.
Confirm that the eligible-heading count equals the generated-image count, and
that no excluded outline level received new artwork without a recorded pastor
override. Confirm every generated image matches its actual PowerPoint image
frame and that no PowerPoint text shape overlaps the artwork.

For a companion handout, render every DOCX page and inspect it at full size.
Confirm the expected page count, the intended blank count, visible underscore
lengths, no residual `SL` cues/highlights, no clipping, and no accidental blank
pages. Record an answer key in the work log or handoff, not inside the audience
handout unless requested.

Review AI-authored captions, research summaries, and handoff text for accuracy.
Do not run a prose-rewriting pass over the pastor's verbatim slide copy or
Scripture.

## Delivery Contract

Deliver:

- the editable `.pptx`;
- the editable `.docx` handout when requested;
- an optional Google Slides link only when requested;
- a concise list of researched sources and AI-generated illustrations;
- the biblical image plan, character-continuity record, and prompt/asset log
  when biblical images were generated;
- any unresolved media placeholders;
- the fidelity audit result and every intentional wording change.

Do not claim the deck is complete when a cue, image, citation, or review flag is
still unresolved.
