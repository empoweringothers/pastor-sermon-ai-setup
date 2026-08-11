---
name: create-sermon-slides
description: Create or update image-rich PowerPoint sermon decks and optional Word audience handouts from pasted sermon text, Word/text/PDF notes, or an existing PPTX, including notes that use SL/Sl or Slide labels. Use when converting a pastor's notes into an editable 16:9, 32:9, or exact-template PPTX; researching authentic historic/place visuals; generating consistent biblical imagery; leaving pastor-supplied media placeholders; following a church template; preserving wording and theology; or auditing a deck against its source.
---

# Create Sermon Slides

Turn pasted or attached sermon material into editable, sourced presentation
files while treating the pastor's wording as the authority. Interpret `SL` and
`Slide` as slide-boundary labels, not as sermon content.

Set `SKILL_DIR` to the absolute path of this skill before running its scripts.
The helper scripts require Python 3.9 or newer and use only the standard
library. They do not require Java, Node.js, `python-pptx`, or `python-docx`.

Before resolving sermon inputs, invoke `$pastor-assistant-os` and load the
applicable approved church and pastor rules from the private local OS. If the OS
is unavailable, continue with this skill's built-in rules and disclose that
personal learning was not loaded. Never copy local memory into the sermon deck,
speaker notes, source log, public repository, or delivery folder.

## Read the Relevant References

- Read `references/wording-fidelity.md` for every create, edit, or audit task.
- Read `references/image-research-policy.md` before finding or generating any
  visual.
- Read `references/biblical-photorealistic-image-set.md` before planning or
  generating any biblical scene or biblical character.
- Read `references/church-style-profile.md` before choosing a canvas, template,
  fonts, colors, or Scripture default for a new church.
- Read `references/vf-service-deck-patterns.md` when the pastor supplies a VF
  service deck, requests the VF layout, or has no nearer approved same-series
  deck.

## Non-Negotiable Rules

1. Treat case-insensitive `SL`, `Sl`, `sl`, `Slide`, `SL-`, `Slide:`, `SL –`,
   parenthesized forms such as `(SL – theme slide)`, and an occasional mistyped
   numeric prefix such as `3Sl` as slide boundaries.
2. Map one cue to one slide by default. Split a cue only when verbatim Scripture
   or a long list cannot remain readable. Do not merge, reorder, or omit cues
   without explicit approval.
3. Preserve the pastor's visible wording, theology, Bible translation,
   emphasis, outline numbering, quotations, and intended sequence. Do not
   "improve" the sermon.
4. Use prose around a cue to understand the visual and the speaking context.
   Do not silently turn surrounding sermon prose into new slide copy.
5. Put production directions such as `(pic of lake)` or `Video` in the build
   plan, not on screen. The only new on-slide production label allowed is a
   tracked, editable, draft-only `IMAGE NEEDED` placeholder created because the
   pastor will supply an asset later.
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
    point and first-level lettered subpoint routed to AI illustration. Do not
    add AI images for headings routed to authentic, provided, or placeholder
    media, or for numbered nested points, bullets, applications, introductions,
    conclusions, or Scripture-continuation slides unless the pastor explicitly
    requests one.
13. Keep every recurring biblical character visually consistent within the
    sermon. Create a sermon-specific continuity record first, approve the
    character's first required image as the visual anchor, and use that anchor
    for every later scene. Peter must look like the same Peter throughout.
14. Generated artwork contains no sermon text, Scripture, labels, captions,
    letters, numbers, logos, borders, signatures, or watermarks.
15. Accept sermon wording pasted directly into chat; do not require the pastor
    to convert or re-upload it merely so a helper script can read it.
16. Resolve the output canvas before sourcing or generating visuals. A supplied
    PPTX's exact size is authoritative; otherwise ask for `16:9`, `32:9`, or the
    exact dimensions of another special screen. Never assume every ultrawide
    screen is exactly 32:9.
17. Honor explicit media directions safely: use an authentic sourced image for
    `real`, `actual`, `historic photo`, or `location photo`; use AI only when the
    cue requests an illustration/reconstruction or the subject is illustrative;
    and use a draft placeholder when the pastor says they will supply the image.
18. Treat a proposed, possible, or traditional biblical location as uncertain.
    Use an authentic present-day photograph when requested. If the slide itself
    identifies the site, preserve the pastor's wording and add an approved,
    editable qualifier beside the media—such as `Traditional site`, `Proposed
    site`, or `Possible site — identification disputed`—as well as the full
    evidence and uncertainty in notes and the handoff. Never put the qualifier
    inside the photograph or silently promote a debated site to proven. Showing
    a photograph as that debated site counts as identifying it even when the
    visible sermon heading does not name the location.
19. If one cue requests conflicting visual routes—such as a real archival photo
    and an AI substitute, or an AI edit of a church photograph—stop on that cue
    and ask one short clarification question. Do not silently choose a route.
20. Apply this precedence: safety, privacy, rights, uncertainty disclosure, and
    non-overwrite rules; then the pastor's current explicit instruction; then
    the designated sermon source for wording; then a content-bearing PPTX; then
    the reference/template PPTX for layout; then the church profile; then
    applicable approved personal rules; then plugin defaults. A personal rule
    may refine a preference but never weaken a higher rule.

## Workflow

### 1. Resolve the Inputs

Obtain:

- The authoritative sermon source: pasted chat text, an attached note, an
  existing PowerPoint, or a note plus a PowerPoint.
- The intended service/date and AM/PM context.
- A same-series starter deck or a recent approved sermon deck.
- The delivery format: uploaded deck's exact size, `16:9`, `32:9`, another
  exact special-screen size, or separate outputs for more than one canvas.

Choose the mode from the supplied material:

- **Pasted sermon text or note only:** create a new deck from the labeled cues.
- **Sermon plus PPTX:** use the sermon for wording and the PPTX for approved
  layout, master, dimensions, and series styling. Always duplicate the PPTX to
  a safe working copy; never edit the supplied source in place.
- **PPTX plus requested changes:** revise a safe working copy and preserve its
  editable structure; do not flatten the deck into pictures.
- **PPTX only with no requested changes:** ask what outcome is wanted. Do not
  invent a sermon or replace its wording.

Prefer explicitly supplied files. Do not search email, cloud drives, shared
church storage, or other private locations unless the pastor asks and the host
has authorized read access. Never send, move, label, delete, or share private
church material during a search.

### 2. Extract the Slide Cues

For sermon text pasted directly into chat, review it in place and apply the same
marker rules as the helper. Record the chat paragraph or line for each cue. Do
not make the pastor save a `.txt` file first. If no `SL` or `Slide` labels exist,
ask how slide boundaries should be chosen rather than turning every sermon
paragraph into a slide.

For an attached `.docx`, `.txt`, `.md`, legacy `.doc`, or text-based PDF, run:

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

For an attached PPTX, inspect its slide size, layouts, masters, text, notes,
media, and editable object structure. Treat it as the output deck when the
pastor asks for edits, or as visual precedent when paired with a new sermon.

Create a build record for every output slide:

- source cue and paragraph number;
- exact visible copy;
- production direction;
- outline level, generated-image eligibility, and the scope reason or recorded
  pastor override;
- visual type (`actual`, `AI illustration`, `provided`, `placeholder`, or
  `none`);
- explicit visual-route hint (`authentic_sourced_image`, `ai_illustration`,
  `pastor_provided_asset`, `pastor_supplied_placeholder`, `automatic`, or
  `conflict_review`), the reason, and whether clarification is required;
- site-identification status (`established`, `traditional`, `proposed`,
  `possible`, `disputed`, `unknown`, or `not_applicable`) and any approved
  visible uncertainty label;
- placeholder description, expected source, and status (`needed`, `received`,
  `replaced`, `waived`, or `not_applicable`);
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
- Preserve a supplied church deck's exact canvas even when it is only
  approximately 32:9. When no template exists, ask whether the church uses
  ordinary 16:9, exact 32:9, or another special sanctuary screen; default to
  16:9 only after confirming there is no special screen.
- Read the dimensions inside the PPTX. Never infer the canvas from filename
  labels such as `HD`, `UW`, `wide`, or `32x9`.
- For a new exact 32:9 deck without a template, use a true 32:9 slide size such
  as 16 by 4.5 inches. For 16:9 and 32:9 delivery, build separate PPTX files and
  recompose each visual; do not stretch or blindly crop one deck into the other.
- When no reference deck exists, build a simple sermon-specific visual system:
  a dedicated text region beside a dedicated image region, very large readable
  type, restrained accents, and a small consistent series/title mark.
- When topical imagery is requested and the reference deck permits a split
  composition, use a consistent text-left, picture-right layout on content
  slides. Reserve full-width or text-only treatment for a supplied series
  opener, a cue that explicitly calls for it, or a user-directed exception.
- For a VF service deck, follow `references/vf-service-deck-patterns.md`: copy
  the approved rhythm, geometry, spacing, typography, and separate picture
  frames, never the old sermon wording or legacy character depictions.
- Treat a reference deck as style evidence, not automatic proof of quality.
  Correct inherited clipping, stretched pictures, collisions, missing source
  notes, and identity drift before delivery.
- Never use a photograph or generated image as a background behind sermon text.
  For full-width art, make the slide image-only or place text on a separate
  solid-color panel that does not overlap the image.
- Produce `.pptx` first. Import the verified PPTX into Google Slides only when
  the user requests a native Google Slides copy.

### 4. Research and Create Visuals

Classify the requested visual before acquiring it.

Use the cue's explicit direction when safe. Search may discover a candidate,
but never treat a Google or Bing result thumbnail as the source or usage right.
Open the original official, archive, museum, archaeology, tourism, news, or
licensed-media page; verify what the image actually shows; and record the
direct page, creator, date, and usage context.

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
- For an identifiable historical or biblical place, prefer an authentic
  present-day or archival photograph when the pastor requests a real image.
  For examples such as a possible tomb location, distinguish a proposed or
  traditional site from a proven location. If the slide makes the identification
  claim, use an approved editable qualifier beside the image and record fuller
  context in speaker notes and the handoff.
- Prefer official, public-domain, Creative Commons, or clearly licensed raster
  images. Record the creator/source, URL, date accessed, and license/usage
  context.
- When the pastor must supply a photo, or no suitable rights-cleared authentic
  image is available, place a draft-only neutral placeholder shape in the
  dedicated image frame. Label it briefly `IMAGE NEEDED: <description>`, add a
  `[Media needed]` note with the source/owner and crop request, and list it in
  the handoff. Never replace it with fabricated evidence or call the deck
  service-ready while it remains unresolved.
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
- Keep every unresolved image placeholder inside the same dedicated image frame
  the final asset will use, so the pastor can replace it without rebuilding the
  slide. A placeholder is a solid editing aid, not text over a photograph.
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

Render and inspect every slide at full size. Fix clipping, poor crops, low
contrast, blurry media, accidental template changes, and every untracked or
unintended placeholder. A tracked `IMAGE NEEDED` placeholder may remain only in
a clearly named draft and must reconcile to the media-needed list.

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
Confirm that the headings planned and approved for AI generation equal the
generated-image count. An eligible heading routed to authentic, provided, or
placeholder media is excluded from that AI count. Confirm that no excluded
outline level received new artwork without a recorded pastor override. Confirm
every generated image matches its actual PowerPoint image frame and that no
PowerPoint text shape overlaps the artwork.
Confirm that every visual-route conflict was resolved by the pastor and that no
AI-generated substitute was used for an authentic evidence request or missing
pastor-owned photograph.
Confirm the PPTX canvas exactly matches the selected 16:9, 32:9, or uploaded
template dimensions. If both canvases were requested, validate each deck and
its independently composed image crops.
Reconcile every `IMAGE NEEDED` placeholder with the media-needed list. Deliver
a placeholder-bearing deck as a clearly named draft, never as the final
service-ready file.

For a companion handout, render every DOCX page and inspect it at full size.
Confirm the expected page count, the intended blank count, visible underscore
lengths, no residual `SL` cues/highlights, no clipping, and no accidental blank
pages. Record an answer key in the work log or handoff, not inside the audience
handout unless requested.

Review AI-authored captions, research summaries, and handoff text for accuracy.
Do not run a prose-rewriting pass over the pastor's verbatim slide copy or
Scripture.

Invoke `$review-pastor-work` for an independent final pass using the sermon
source, finished artifacts, this skill's rules, and only the approved personal
rules that apply. Fix every confirmed blocker or required defect, then re-run
the affected checks. A builder's completion claim is not its own review.

## Delivery Contract

Deliver:

- the editable `.pptx`;
- the editable `.docx` handout when requested;
- an optional Google Slides link only when requested;
- a concise list of researched sources and AI-generated illustrations;
- the biblical image plan, character-continuity record, and prompt/asset log
  when biblical images were generated;
- any unresolved media placeholders;
- a media-needed list naming the slide, required asset, owner/source, intended
  crop, and whether the deck is still a draft;
- the fidelity audit result and every intentional wording change.

Do not claim the deck is complete when a cue, image, citation, or review flag is
still unresolved.

If the pastor reports a miss, fix and verify the current deck first. Then invoke
`$learn-pastor-corrections` to decide whether the correction is one-time or a
reusable personal rule. Never save a rule without the exact approval required
by that skill, and never carry a sermon-specific character bible into another
sermon merely because it existed in the last project.
