# Image Research and Generation Policy

Choose the visual route by what the image is claiming to be.

| Subject | Required route | Notes |
|---|---|---|
| Current news or recent event | Authentic photograph from an official or reputable source | Verify event, date, people, and caption. Never generate. |
| Identifiable public figure | Authentic licensed/official photograph | Verify identity. Never generate a lookalike. |
| Church member, missionary, or local ministry event | Provided photo or approved church-drive asset | Do not guess identity from the web. |
| Historical event used as evidence | Authentic archive/public-domain image when available | A reconstruction must be labeled illustration. |
| Place, building, object, product, map, document, or screenshot | Authentic current/archival image | Do not fabricate evidence, logos, documents, or UI. |
| Proposed, possible, or traditional biblical/historical site | Authentic current or archival location photograph | State the uncertainty in notes/handoff. If the slide identifies the site, use an approved editable qualifier beside the media; never label a debated site as proven. |
| Pastor-owned or ministry image not yet supplied | Dedicated draft placeholder | Do not search for a lookalike or generate a substitute. |
| Biblical scene or historical reconstruction | Realistic AI illustration is allowed | Label as AI-generated illustration; avoid claiming documentary accuracy. |
| Abstract idea, metaphor, mood, or title graphic | Realistic AI illustration is allowed | Keep it visually believable but clearly illustrative in notes. |
| Scripture, outline, quotation, or list | Usually no image or a restrained supporting visual | The words remain primary. |

## Research

- Browse the web for current events, news, public figures, current statistics,
  recent quotations, and facts that may have changed.
- Use Google, Bing, or another image search only to discover candidates. Open
  the original source page before using an image; a search-result thumbnail is
  neither the authoritative source nor proof of usage rights.
- Prefer primary and official sources. Use reputable reporting when the primary
  source does not supply a usable photograph or sufficient context.
- Verify that a photograph depicts the exact named person/event and not a
  similar scene.
- Save the direct page URL, creator/agency if available, published/event date,
  access date, and license or usage context.
- Use an asset only when its license, a church-owned media subscription, or
  explicit permission covers the intended in-room presentation, recording,
  livestream, and later replay. Official or reputable provenance does not by
  itself grant display or streaming rights. Do not treat "found on Google" as a
  usage right.
- Use a screenshot only when the screenshot itself is evidence and the context
  is visible enough to understand it.
- For a debated biblical location, distinguish `traditional site`, `proposed
  site`, `possible site`, and `archaeologically established place`. Preserve
  the pastor's wording on the slide. When the slide itself identifies the site,
  add a small editable qualifier beside the media only after the pastor supplies
  or approves it—for example `Traditional site`, `Proposed site`, or `Possible
  site — identification disputed`. Keep that label in the PowerPoint layout,
  never burned into the photograph. Record the fuller evidence and uncertainty
  in speaker notes and flag an overconfident claim for review. Presenting the
  photograph as the site counts as an identification even when the visible
  sermon heading does not name the location.

## Conflicting Visual Directions

Do not resolve mixed routes by keyword precedence. If one cue matches more than
one of these routes, record `conflict_review` and ask one short question before
searching, generating, or editing:

- authentic sourced evidence;
- AI-generated illustration or reconstruction;
- a pastor-provided asset already attached;
- a pastor-supplied asset that is still missing and needs a placeholder.

Examples that require clarification include `Use a real archival photo; make an
AI image only if unavailable` and `AI edit of my church photo`. The second may
also trigger the real-person privacy rule. Keep the slide pending until the
pastor chooses a safe route.

## Pastor-Supplied Image Placeholders

Use a placeholder when the cue says the pastor will add the image, when an
identifiable church image has not been supplied, or when the requested authentic
image cannot be used with clear rights.

- Put one neutral solid placeholder shape inside the final dedicated image
  frame; never put it behind sermon text.
- Use the short draft label `IMAGE NEEDED: <description>` so it cannot be
  mistaken for completed media.
- Add a speaker-note block with the required owner/source, subject, desired crop,
  orientation, and deadline when known.
- Add the same item to the delivery media-needed list.
- Keep the placeholder editable and easy to replace without moving the sermon
  text or rebuilding the slide.
- Name the deck as a draft and do not call it service-ready until all required
  placeholders are resolved or the pastor explicitly accepts a text-only slide.

Use this speaker-note form:

```text
[Media needed]
- Required image: <plain description>
- Expected owner/source: <pastor/church/archive/other>
- Frame and crop: <ratio, orientation, subject placement>
- Status: awaiting pastor-supplied asset
[/Media needed]
```

## AI Image Generation

Generate only illustrative material. Use prompts that specify:

- "true-to-life editorial photograph" or "cinematic documentary-style
  illustration";
- era, location, clothing, architecture, and material details;
- plausible natural lighting and a real camera/lens description;
- the exact slide ratio or crop;
- subject placement and crop safety for the dedicated image frame;
- no lettering, captions, watermarks, UI, or logos;
- no resemblance to a named living person unless the user supplied an image and
  explicitly requested an allowed edit.

For the pastor or an identifiable church member, do not generate or alter the
face or body. Keep the approved subject layer in its original pixels. If a new
setting is needed, generate only a clean background and composite the authentic
subject without generative fill touching the person.

For a special ultrawide church screen, use the exact template ratio, request a
very wide composition, and keep important faces and objects away from far edges
and physical screen seams.

For recurring biblical characters, read
`biblical-photorealistic-image-set.md`, create a continuity record for the
current sermon, and reuse the first approved sermon image as a visual reference
for later scenes. Character continuity is per sermon unless the pastor asks to
carry it into another sermon or series.

## Provenance in Speaker Notes

Use a block like:

```text
[Sources]
- Photo: <creator/source>, <direct page URL>, accessed <YYYY-MM-DD>, <license/usage context>
- Claim: <primary source>, <direct URL>, accessed <YYYY-MM-DD>
- Site status: <proposed/traditional/possible/established>, <supporting source and URL>
- [AI-generated illustration]: <tool/model if known>, prompt record <file or short identifier>
[/Sources]
```

For each AI-generated illustration, retain the generation tool/model when
known, date, complete prompt or prompt-file ID, reference-image and character
continuity IDs, crop/edit history, and any historical research sources used to
ground the reconstruction.

Do not put a source URL visibly on the slide unless the pastor's note or the
presentation context calls for it.

## Final Visual Checks

- Inspect the full-resolution crop, not only a thumbnail.
- Reject blurry, stretched, watermarked, misidentified, or contextually false
  images.
- Reconcile every draft placeholder with the media-needed list and confirm it
  occupies the final image frame without overlapping sermon text.
- Confirm every visible label for a debated site is editable, outside the
  photograph, and consistent with the source notes.
- Confirm every `conflict_review` item has a recorded pastor decision.
- Check that text remains readable on the stage background.
- Confirm that an AI illustration cannot reasonably be mistaken for a real
  news photograph without the source notes.
