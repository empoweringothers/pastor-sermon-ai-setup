# Biblical Photorealistic Image Set

Use this reference when a sermon needs generated biblical scenes. The goal is a
cohesive set of reverent, true-to-life cinematic illustrations that feels like
one carefully produced biblical film—not unrelated pieces of artwork.

## Contents

- Image scope and planning
- Per-sermon character continuity and recurring defaults
- Visual language and historical grounding
- Canvas and placement
- Sequential generation and review

## Image scope

Generate exactly one new image for each:

- main sermon point;
- first-level lettered subpoint such as `A`, `B`, or `C`.

Do not generate a new image for:

- numbered nested subpoints such as `1`, `2`, or `3`;
- bullets, supporting illustrations, or applications;
- an introduction or conclusion unless the pastor explicitly requests it;
- extra slides created only to continue a long Scripture passage.

This rule governs generated imagery, not slide count. Preserve every requested
slide cue and the pastor's exact outline. A non-image slide may use the approved
deck's text-only treatment. If the sermon note explicitly requests a visual
outside this default scope, pause and ask before expanding the image set.

## Plan before generating

Create a `biblical-image-plan.md` in the working folder. For every main point and
first-level subpoint, record:

- exact sermon heading and outline level;
- primary biblical event or theological truth;
- book, passage, era, place, and scene evidence from the sermon;
- recurring characters and their continuity IDs;
- dedicated image-frame ratio and intended crop;
- scene, composition, lighting, emotional tone, and historical details;
- prompt and generated asset identifier;
- approval or revision status.

Do not invent a biblical event merely to make a dramatic picture. When the
heading teaches a theological truth without naming a specific event, use a
restrained, biblically suitable metaphor or environment and record that it is an
illustration.

## Per-sermon character continuity

Create `character-continuity.md` before generating the first scene. Continuity
is scoped to the current sermon unless the pastor explicitly asks to carry a
character into another sermon or series.

Give every recurring named character a stable ID and record:

- name and life stage for this scene;
- approximate age and regional appearance;
- face shape, complexion, eye color, hair, beard, and distinguishing features;
- height, build, posture, and normal expression;
- clothing layers, fabric, color, wear, head covering, footwear, and props;
- first approved image or other visual reference asset;
- allowed story-driven changes, such as age, dirt, injury, or different attire.

The same character must retain the same identity across all images in that
sermon. Peter must look like the same Peter; Abraham must look like the same
Abraham. Clothing may change only when the passage or timeline calls for it,
while face, build, and other identity anchors remain stable.

For each recurring character:

1. Write the continuity specification before the first generation.
2. Generate the first required sermon image containing that character.
3. Review and approve the character appearance in that image before generating
   a later scene with the character.
4. Use the approved image as a reference input whenever the image tool supports
   references. Also repeat the stable continuity description in the prompt.
5. If reference inputs are unavailable, repeat the complete continuity block
   verbatim and compare each result with the approved anchor before accepting it.
6. Reject and revise face, age, build, hair, beard, costume, or prop drift before
   moving to the next image.

Do not add a separate character portrait to the deliverable image count unless
the pastor requests one. The first eligible sermon image becomes the visual
anchor. Never imitate a recognizable actor or living person's likeness.

When a character appears at different ages, define named phases such as
`Moses-young`, `Moses-adult`, and `Moses-older`. Preserve identifiable facial and
physical traits across the phases while changing age and story-appropriate
clothing.

## Recurring character defaults

Use these only when the sermon and pastor do not establish a closer direction.

### Abraham

- elderly man with a weathered tan complexion and white beard;
- earth-toned woven robes and wrapped head covering;
- gentle, strong, reverent expression.

### Moses

- `Moses-young`: dark-haired, educated Egyptian prince in historically grounded
  royal linen clothing;
- `Moses-adult`: rugged shepherd with sun-weathered skin and practical woven
  clothing;
- `Moses-older`: long white beard, humble robes, wooden shepherd staff, and wise
  expression.

### Pharaoh

- nemes headdress, linen robes, and historically grounded Egyptian jewelry;
- regal, hardened expression in a throne room with appropriate Egyptian
  architecture and hieroglyphic detail;
- never fantasy armor or a recognizable film actor.

For Peter, Jesus, Paul, and every other recurring person, create the same kind
of sermon-specific continuity record before first use. Use plausible regional
features and avoid generic celebrity casting.

## Visual language

Every accepted image should be:

- ultra-photorealistic and cinematic;
- historically grounded, presentation-quality, and suitable for a large screen;
- naturally color graded with realistic HDR-like tonal range;
- rich in believable depth, fabric, skin, anatomy, shadow, and atmosphere;
- composed with a strong foreground subject, readable middle ground, expansive
  background, leading lines, natural framing, and appropriate scale;
- emotionally reverent, hopeful, strong, and restrained rather than theatrical.

Use natural sunrise, sunset, morning light, torchlight, campfire light,
moonlight, window light, or plausible volumetric sunlight. Suggest providence
through natural light when appropriate. Do not add halos, magical glows, fantasy
effects, or exaggerated supernatural light unless the passage explicitly calls
for a visible phenomenon.

The image must contain no Scripture, title, label, caption, letters, numbers,
logo, watermark, signature, decorative frame, or fabricated readable writing.
All sermon text stays in the PowerPoint's separate text region.

## Historical grounding

Use era-appropriate natural woven fabrics, head coverings, footwear, tools,
weapons, household items, and construction methods. Avoid medieval European
robes, fantasy costumes, modern fabrics, modern objects, Gothic buildings,
medieval castles, and anachronistic architecture.

Match the location named in Scripture or the sermon:

- **Egypt:** Nile, papyrus, mudbrick buildings, appropriate temples, obelisks,
  palms, stone monuments, and desert horizons;
- **Canaan:** rolling rocky hills, oak or olive trees where plausible, grazing
  animals, tents, wells, and ancient paths;
- **Midian:** rugged mountains, dry riverbeds, desert shrubs, shepherd camps,
  and open wilderness;
- **Wilderness:** sandstone, sparse vegetation, tents, livestock, campfires,
  and broad skies;
- **New Testament Judea and Galilee:** historically appropriate villages,
  roads, hills, lakeshore settings, clothing, and Roman-period elements only
  where the passage supports them.

Do not claim archaeological certainty. Record every generated scene as an
`[AI-generated illustration]`, not as a documentary photograph of a biblical
event.

## Canvas and placement

- Preserve the exact aspect ratio and image frame from the pastor-approved
  PowerPoint.
- If there is no approved deck, template, or special sanctuary screen, default
  the image to 16:9.
- Recompose separately for a special ultrawide church screen; do not crop a
  16:9 scene blindly.
- Compose for the dedicated image frame. Do not reserve an area for sermon text
  inside the artwork and never place PowerPoint text over the generated image.
- Keep important faces, hands, and story details away from crop boundaries and
  physical screen seams.

## Sequential generation and review

Generate one image at a time in sermon order. Do not begin the next eligible
heading until the current image has been reviewed and either accepted or
revised.

For each result, check:

- it illustrates the exact sermon heading without changing the theology;
- recurring characters match their approved anchor and continuity record;
- era, place, clothing, architecture, props, and geography are plausible;
- faces, hands, anatomy, fabric, light, and shadows look natural;
- the crop works in the dedicated PowerPoint image frame;
- no modern object, fake text, watermark, logo, border, fantasy effect, or
  recognizable actor appears;
- color grade, lens language, lighting, and realism match the rest of the set.

At the end, inspect a contact sheet of the full image set specifically for
character drift and visual discontinuity. Beauty alone is not a pass: the image
must be faithful to the sermon, consistent with the series, and usable in the
approved slide layout.
