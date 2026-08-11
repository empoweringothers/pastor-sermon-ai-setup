---
name: learn-pastor-corrections
description: Fix a pastor-reported mistake, decide whether the correction is one-time or reusable, and save a sanitized personal rule to the Pastor Assistant OS only after explicit approval. Use when the pastor says a result is wrong, asks to remember a preference, says “next time,” repeats a prior correction, or wants the assistant to improve future sermon work.
---

# Learn Pastor Corrections

Turn a useful correction into safer future behavior without pretending to
retrain the model or silently editing the public plugin.

Read [references/promotion-policy.md](references/promotion-policy.md) before
proposing or saving a rule.

## Correction loop

1. Restate the concrete problem in one short sentence.
2. Fix the current deliverable first when the task authorizes changes.
3. Verify the fix with `$review-pastor-work` or a focused equivalent check.
4. Decide whether the correction is:

   - `current sermon only`;
   - `personal future rule`; or
   - `possible church-wide rule`.

5. For a one-time choice, stop after the fix. Do not save it.
6. For a reusable preference, write one generalized rule without sermon text,
   names, images, private facts, or file paths.
7. Check the proposed rule against existing approved rules and the plugin's
   safety rules. Narrow or reject a conflicting rule.
8. Show exactly this single decision:

   ```text
   SAVE FOR NEXT TIME?
   Rule: <one plain-language rule>
   Scope: This pastor only

   Reply exactly: YES, SAVE THIS RULE
   Or reply: NO
   ```

9. If the answer is not exact, do not write memory.
10. After the exact answer, invoke `$pastor-assistant-os` and use its local OS
    script:

    ```text
    remember --category <category> --rule <rule> --reason <generalized reason> --consent "YES, SAVE THIS RULE" --json
    ```

11. Run `doctor --json`, then confirm the rule ID and that it is local to this
    pastor's computer.

An absent or unhealthy local OS is never a reason to delay the current fix.
Finish and verify the correction first. Then, if the pastor wants the rule
remembered, route to `$pastor-assistant-os` for permissioned setup before asking
the separate save question.

## Church-wide improvement

Never edit the installed skill or public repository automatically. A correction
may become a church-wide proposal after either:

- the same approved problem occurs at least twice; or
- one occurrence creates a privacy, factual, theological-fidelity, or
  production-use risk.

Ask separately for `YES, PREPARE CHURCH RULE PROPOSAL`. The script may then
create a local proposal file for the church administrator. Creating a proposal
does not approve, publish, commit, push, or install it.

## Forgetting a rule

Show the exact rule and ask for `YES, FORGET THIS RULE`. Retire it through the
script only after that answer. Keep the local audit entry; remove it from the
compiled approved rules used for future work.
