---
name: review-pastor-work
description: Independently review sermon PowerPoints, AI images, handouts, and related pastor deliverables against their source material, built-in workflow rules, and approved Pastor Assistant OS preferences. Use before final delivery, after a pastor says a result is wrong or inconsistent, or when checking whether a correction really fixed the problem.
---

# Review Pastor Work

Find specific problems before the pastor uses the deliverable. Review is not
permission to rewrite sermon content or save a future rule.

Read [references/review-rubric.md](references/review-rubric.md) completely for
the artifact being reviewed.

## Review contract

1. Read the authoritative source, the produced artifact, and only the approved
   personal rules that apply.
2. Prefer a fresh reviewer subagent when available. Give it the raw artifact,
   source, and rubric—not the builder's conclusions or intended answer.
3. If a fresh reviewer is unavailable, start a separate review pass and do not
   rely on the builder's completion claim.
4. Inspect, render, or open the native file when the host supports it. A file's
   existence is not proof that it works.
5. Classify each finding as `blocker`, `fix before use`, or `suggestion`.
6. Support every finding with a slide number, cue, image identifier, or other
   concrete location.
7. Fix confirmed blockers and required defects when the current task authorizes
   building or revision. Preserve originals and edit a duplicate.
8. Re-run the affected checks after the fix.
9. Do not record memory. If the pastor wants a future preference saved, invoke
   `$learn-pastor-corrections` after the current artifact is fixed.

## Required review output

Return a short result with:

- `Ready` or `Not ready`;
- required fixes and exact locations;
- checks that passed;
- any unresolved item needing one pastor decision.

Ask only one decision at a time. Do not hide a known defect behind a general
statement such as “looks good.”
