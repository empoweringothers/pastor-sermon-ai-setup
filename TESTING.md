# Maintainer Testing

Run these checks before publishing a release.

## Read-only environment report

```bash
python3 scripts/check_environment.py --json
```

## Installer dry check

```bash
python3 scripts/prepare_plugin.py --check
```

## Safe installer test in a temporary home

```bash
TEST_HOME="$(mktemp -d)"
python3 scripts/prepare_plugin.py --prepare --home "$TEST_HOME"
python3 scripts/prepare_plugin.py --check --home "$TEST_HOME"
```

The temporary test does not touch the real personal marketplace.

## Sermon helper tests

```bash
python3 -m unittest discover \
  plugins/sermon-slide-builder/skills/create-sermon-slides/tests
```

## Setup repository tests

```bash
python3 -m unittest discover tests
```

The included GitHub Actions workflow runs both test suites on macOS and Windows.

## Dependency-free package validation

```bash
python3 scripts/validate_package.py
```

When developing inside ChatGPT/Codex, also run the current built-in
`plugin-creator` and `skill-creator` validators before tagging a release. Those
validators live in the active host runtime, so this repository does not hardcode
a private machine path to them.

## Release source gate

```bash
python3 scripts/check_publish_ready.py
```

The source gate intentionally fails until the repository owner chooses and adds
a public-distribution license.

Finally, test installation from the Plugins Directory, restart ChatGPT desktop,
and verify the plugin in a new chat using the exact request in Phase 7 of
`SETUP-ASSISTANT.md`.
