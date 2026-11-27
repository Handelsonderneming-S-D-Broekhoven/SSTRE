# EXP-006: CI activation across the five repositories

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | POC-04 (schema examples + negative tests), POC-05 (minimal CI) |
| Status | partial: all checks written and run locally; not yet run on GitHub (nothing pushed); engine allowlist needs a validator pin bump |
| Environment | Windows 11 Pro 10.0.22631, Git Bash; Python 3.10.11 (`local-work\venv`: jsonschema 4.26.0, referencing 0.37.0, reuse 5.0.2, PyYAML 6.0.4); `local-work\ci-agent\venv`: pytest 8.4.2, jsonschema 4.26.0. CI targets `ubuntu-24.04` + Python 3.12, not reproduced locally. `act` not installed, not used. |
| Inputs | All five repositories on branch `phase1/validation`; umbrella `HEAD` = `230ab5e1dbfeb5b04501fb6f2f29fbe407e85d1a`; SSTRE-Engine local branches `upstream/classic-vk-main` (510d36f) and `upstream/rt-main` (0e7f223), read through throwaway clones only |

## Goal and success criteria

1. Every umbrella schema has synthetic `examples`, plus positive/negative test documents. Valid documents must pass and invalid ones must fail in CI (POC-04).
2. CI runs in all five repositories: link check, schema check, game-data leak scan, and REUSE where applicable. Actions are pinned by full SHA and run with `contents: read` (POC-05).
3. The leak scan fails on a planted `.tex`/`.dem`/`.sav` file or a >1 MB binary (POC-05 "done when").
4. A DCO check exists as a proposal and does not block anything yet.

## Procedure (exact, reproducible)

```sh
PY=L:/claude-ws/SSTRE/local-work/venv/Scripts/python.exe
# umbrella
$PY scripts/validate_repo.py
$PY -m reuse lint
# siblings with the new validator, and with the validator pinned at 230ab5e
# (git show 230ab5e:scripts/validate_repo.py > <scratch>/validate_repo.py)
$PY scripts/validate_repo.py --root ../<repo>
(cd ../<repo> && $PY -m reuse lint)        # not SSTRE-Engine
# engine against future upstream content (throwaway local clones in scratch)
git clone --single-branch --branch upstream/<b> ../SSTRE-Engine <scratch>/eng-<b>
$PY scripts/validate_repo.py --root <scratch>/eng-<b> --skip-schemas [--forbidden-allowlist <engine>/.github/workflows/sstre-forbidden-allowlist.txt]
# leak-scan control: copy of the umbrella, git init, planted files force-added
# AssetCompiler tests as CI runs them
PYTHONPATH=src SSTRE_SCHEMAS_DIR=<schemas dir> <ci-agent venv>/python -m pytest -p no:cacheprovider
# YAML: yaml.safe_load on every workflow + regex check that each `uses:` ends in @<40-hex>
```

Action tags were checked with `gh api repos/<owner>/<repo>/git/ref/tags/<tag>`: `actions/checkout` v7.0.1 → `3d3c42e5aac5ba805825da76410c181273ba90b1`, and `actions/setup-python` v7.1.0 → `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`. Both are commit objects and both are the latest releases.

## CI checks that now exist

| Repo | Workflow | Jobs | Trigger |
|---|---|---|---|
| SSTRE | `docs-and-schemas.yml` | `validate` (schemas, schema tests, links, leak scan), `reuse` (`reuse==5.0.2`, `reuse lint`) | push `main`, PR, dispatch |
| SSTRE | `dco-proposal.yml` | `dco`: every non-merge commit in `base..HEAD` needs a `Signed-off-by` matching the author e-mail | **dispatch only (proposal, not required)** |
| SSTRE-AssetCompiler | `sstre-checks.yml` | `validate`, `reuse`, `pytest` (only if `tests/` exists; pytest 8.4.2, Python 3.12, `PYTHONPATH=src`, `SSTRE_SCHEMAS_DIR` = umbrella `schemas/` at the same pinned commit) | push `main`, PR, dispatch |
| SSTRE-Manifests, Remaster-Toolkit | `sstre-checks.yml` | `validate`, `reuse` | push `main`, PR, dispatch |
| SSTRE-Engine | `sstre-checks.yml` | `validate` only (`--skip-schemas`); no REUSE, because the upstream import is not REUSE-compliant | push `main`, PR, dispatch |

Sibling workflows check out the umbrella at `SSTRE_UMBRELLA_COMMIT: 230ab5e1dbfeb5b04501fb6f2f29fbe407e85d1a` (sparse `scripts/`, or `schemas/` for pytest). They then run `validate_repo.py --root repo`.

Validator changes (`scripts/validate_repo.py`, still stdlib + jsonschema only):

- Schemas are the top-level `schemas/*.json` files, handled generically. A new schema such as `game-edition-report.schema.json` is picked up with no code change.
- New: `schemas/tests/<name>/{valid,invalid}/*.json` documents are validated against `schemas/<name>.schema.json`. A test directory with no matching schema, a stray entry, a valid document that fails or an invalid document that passes is an error.
- Leak scan: added `.dem` and `.sav`. A binary file (NUL byte in the first 8 KiB) larger than `--max-binary-mb` (default 1) is now an error.
- New flags: `--forbidden-allowlist FILE` (fnmatch globs, for preserved upstream files only) and `--skip-forbidden`.

## Results ([EXP], 2026-11-27)

- **Umbrella validator:** `schemas: checked 5 schema(s), 5 inline example(s)` · `schema-tests: 2 valid and 23 invalid document(s) checked; no negative tests yet for: game-edition-report` · `markdown: checked 31 file(s), 182 relative link(s)` · `forbidden-files: checked 73 file(s)` · `result: 0 error(s), 0 warning(s)`. Before this change the result was 3 "no 'examples'" warnings. Each of the 23 invalid documents yields exactly one validation error, so each fails for its intended reason.
- **REUSE:** umbrella, AssetCompiler, Manifests and Toolkit all report "compliant with version 3.3". AssetCompiler and Toolkit also print `'README.md' holds an SPDX expression that cannot be parsed, skipping the file`. The cause is prose after an `SPDX-License-Identifier` mention in the README. It is a warning, not a failure.
- **Siblings, pinned 230ab5e validator (what CI runs today):** AssetCompiler, Manifests, Toolkit and Engine each give `0 error(s), 0 warning(s)`. The new validator gives the same result on all four.
- **Engine vs. future upstream:** `upstream/classic-vk-main` gives 43 errors without the allowlist and 0 with it (33 files exempted). `upstream/rt-main` gives 9 errors without it and 0 with it (8 exempted). The markdown check passes on both (2 files, 0 relative links).
- **Leak-scan control** (copy of the umbrella with planted files): errors fired for `planted.tex`, `planted.dem`, `planted.sav` and `planted.bin` (1 MiB + 1 NUL bytes). A 6 MiB text file gave only a warning. The schema-test controls also fired: a valid document in `invalid/`, an invalid one in `valid/`, a broken JSON file and an orphan `tests/no-such-schema/` were all reported. Result: 8 errors, exit 1. A probe with a synthetic `game-edition-report` schema plus a negative test was handled generically.
- **DCO script:** on the umbrella, `BASE=main` reported `checked 3 commit(s) in origin/main..HEAD, 3 without matching sign-off` with exit 1, as expected because the commits are not signed off. A synthetic repository with one `git commit -s` commit gave exit 0.
- **AssetCompiler pytest** (another agent's work in progress, snapshot): 68 passed with the umbrella working-tree schemas. With the schemas from 230ab5e (what CI would fetch): 65 passed, 3 skipped (`game-edition-report.schema.json` is absent there).
- **YAML:** all 6 workflow files parse. Every `uses:` is pinned to a 40-hex SHA, and every workflow sets `permissions: {contents: read}`.

## Deviations, modifications and failures

- **Not run on GitHub.** Nothing was pushed, and Linux/Python 3.12 behaviour is [ASM].
- **Validator pin lag:** the siblings pin 230ab5e, which predates `--forbidden-allowlist`, schema tests and the `.dem`/`.sav`/binary rules. The engine workflow therefore runs without its allowlist for now (`SSTRE_VALIDATOR_ARGS: ""`). That is correct today because the branch has no upstream files. It would fail after an upstream merge unless the pin is bumped first.
- The engine allowlist lives at `.github/workflows/sstre-forbidden-allowlist.txt`, because writes were limited to `.github/workflows/`. GitHub ignores non-YAML files there.

## Interpretation

- [ASM] `actions/checkout` with a public `repository:` and a SHA `ref` works with the default token, because all five repositories are public (`gh repo list`).
- [ASM] pytest via `PYTHONPATH=src` matches an installed package for these tests. It avoids an unpinned `setuptools` download during build isolation.

## Impact on ADRs, dossiers and backlog

- POC-04: examples and negative tests exist for 4 of 5 schemas. `game-edition-report` still needs negative tests from its owner. QA-report, mapping and package-manifest schemas do not exist yet.
- POC-05: green locally on all 5 repositories. The "done when" leak criteria are met in the local control, but CI on GitHub is still unverified.

## Open questions

1. Lead: after committing the umbrella changes, bump `SSTRE_UMBRELLA_COMMIT` in the four sibling workflows. In the engine workflow, also set `SSTRE_VALIDATOR_ARGS` to `--forbidden-allowlist .github/workflows/sstre-forbidden-allowlist.txt`.
2. Owner: the engine allowlist names upstream file paths, including the upstream-distributed `SE1_10b.gro` and `SE1_10.gro`. Is naming these upstream repository paths acceptable under the GATE-05 policy, or should coarser globs be used?
3. Owner: how to handle the unsigned existing commits before `dco-proposal.yml` gains a `pull_request` trigger and becomes required.
4. Owner: workflow files in SSTRE-Manifests fall under its default `CC-BY-SA-4.0` annotation. Should `.github/**` be CC0-1.0 there?
