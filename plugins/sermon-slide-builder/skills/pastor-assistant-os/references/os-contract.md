# Pastor Assistant OS Contract

## Purpose

The Pastor Assistant OS is a small local operating layer for recurring pastor
work. It does not train a model. It makes approved preferences durable by
loading local rules before a new task.

## Modes

1. **Build** — perform the requested task with the matching domain skill.
2. **Review** — independently compare source, output, and rules.
3. **Fix** — correct the current output and verify the correction.
4. **Learn** — ask whether one generalized lesson should be saved locally.

## Brain loop

1. **Capture in the current task** — notice the pastor's correction without
   copying the chat or sermon into memory.
2. **Verify** — fix the artifact and prove the correction worked.
3. **Compile** — turn the correction into one short, testable general rule.
4. **Approve** — require the exact pastor permission before writing.
5. **Retrieve** — load approved rules at the start of future pastor work.
6. **Operationalize** — apply the rule through the correct build/review skill.
7. **Audit** — keep metadata-only change history and run the doctor check.

This deliberately uses the strongest parts of a larger knowledge brain without
capturing full transcripts or building a broad personal archive.

## Rule precedence

Apply rules in this order:

1. Privacy, safety, rights, authenticity, theological fidelity, and explicit
   approval requirements.
2. The pastor's current explicit instruction.
3. The current sermon source and its exact wording.
4. The current approved PowerPoint/template and requested canvas.
5. Church profile.
6. Approved personal rules.
7. Plugin defaults.

A lower rule never weakens a higher rule. A current pastor instruction may
override a style preference for this task without erasing that preference.

## Memory scopes

- **Current sermon:** keep in the current task only. Character bibles, temporary
  series colors, and one-off choices belong here.
- **This pastor:** save only after `YES, SAVE THIS RULE`.
- **Church-wide:** prepare a proposal only after separate approval. A church
  administrator must review, test, version, and publish it.

These are also the three learning levels: task-only, approved local behavior,
and administrator-reviewed shared behavior. A lesson is not “learned” merely
because it appeared in chat.

## Update boundary

Plugin updates may add better built-in behavior but must never overwrite the
pastor's local profile or approved rules. Local rules may refine defaults but
may not rewrite installed skills or push changes to GitHub.
