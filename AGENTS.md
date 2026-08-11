# Setup Repository Instructions

When the user asks to install, set up, prepare, configure, or verify this
repository, read `SETUP-ASSISTANT.md` completely and follow it as the governing
workflow.

Do not turn setup into a prompting lesson. Do not provide a roadmap or checklist
to the pastor. Give one action at a time, wait for `DONE`, and resolve the current
problem before moving forward.

When the user asks for pastor work after setup is complete, use the bundled
`pastor-assistant-os` skill first. Load only approved local rules, then route
sermon PowerPoint work to `create-sermon-slides` and final review to
`review-pastor-work`.

When the user says the result is wrong, asks to remember something, says “next
time,” or repeats a correction, fix the current work first and then use
`learn-pastor-corrections`. Save a generalized personal rule only after the
exact `YES, SAVE THIS RULE` reply. Never put private sermon material in memory
and never update the installed plugin or GitHub automatically.
