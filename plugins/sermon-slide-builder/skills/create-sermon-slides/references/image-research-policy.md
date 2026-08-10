# Image Research and Generation Policy

Choose the visual route by what the image is claiming to be.

| Subject | Required route | Notes |
|---|---|---|
| Current news or recent event | Authentic photograph from an official or reputable source | Verify event, date, people, and caption. Never generate. |
| Identifiable public figure | Authentic licensed/official photograph | Verify identity. Never generate a lookalike. |
| Church member, missionary, or local ministry event | Provided photo or approved church-drive asset | Do not guess identity from the web. |
| Historical event used as evidence | Authentic archive/public-domain image when available | A reconstruction must be labeled illustration. |
| Place, building, object, product, map, document, or screenshot | Authentic current/archival image | Do not fabricate evidence, logos, documents, or UI. |
| Biblical scene or historical reconstruction | Realistic AI illustration is allowed | Label as AI-generated illustration; avoid claiming documentary accuracy. |
| Abstract idea, metaphor, mood, or title graphic | Realistic AI illustration is allowed | Keep it visually believable but clearly illustrative in notes. |
| Scripture, outline, quotation, or list | Usually no image or a restrained supporting visual | The words remain primary. |

## Research

- Browse the web for current events, news, public figures, current statistics,
  recent quotations, and facts that may have changed.
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
- Check that text remains readable on the stage background.
- Confirm that an AI illustration cannot reasonably be mistaken for a real
  news photograph without the source notes.
