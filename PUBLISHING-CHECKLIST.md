# Publishing Checklist

This page is for the person who publishes the GitHub repository.

- Create an immutable GitHub release tag; never distribute setup from a mutable
  branch.
- Make the tagged release publicly readable, or send the verified release ZIP
  directly. A private URL may be unreadable in the pastor's first chat.
- Choose and add the license you intend to grant before public distribution.
- Do not add real sermon notes, church-member photos, private drive paths,
  passwords, API keys, or licensed church templates.
- Run `python3 scripts/check_environment.py --json`.
- Run `python3 scripts/prepare_plugin.py --check`.
- Build the pastor release ZIP and its external paste message only after the
  final commit SHA and release URL are known.
- Run:

  ```bash
  python3 scripts/build_release.py \
    --release-url "https://github.com/OWNER/REPO/releases/tag/v0.1.0" \
    --commit "FULL_40_CHARACTER_COMMIT_SHA" \
    --out "release"
```

The builder safely excludes the chosen output folder when it is inside the
repository, so rebuilding cannot place an earlier ZIP inside the new ZIP.

- Confirm the generated paste message contains no `{{...}}` placeholders.
- Confirm the release ZIP SHA-256 in the paste message matches the uploaded ZIP.
- Run the plugin and skill validators listed in `TESTING.md`.
- Test the pastor paste message from a fresh ChatGPT conversation.
- Test the complete setup on one Mac and one Windows computer before broad use.
- Confirm that the assistant gives only one action and waits for `DONE` every
  time.
