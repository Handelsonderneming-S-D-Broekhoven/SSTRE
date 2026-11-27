# ADR-0008: Distribute SSTRE-Engine as own patches against pinned upstream commits

- **Status:** accepted, **provisional** (owner decision, 2026-11-27). This is the official distribution strategy for SSTRE-Engine until it is revised. It is project policy, not legal clearance.
- **Date:** 2026-11-27
- **Deciders:** project owner
- **Evidence:** [EXP-004 upstream publication audit](../experiments/EXP-004-upstream-publication-audit.md) (option 5), [ADR-0005](0005-engine-foundation.md), [ADR-0006](0006-licensing-boundaries.md), [RD-007](../research/RD-007-licensing.md) §16

## Context

EXP-004 audited the full history of both engine upstreams imported locally: `upstream/classic-vk-main` (tx00100xt/SeriousSamClassic-VK @ `510d36f`) and `upstream/rt-main` (sultim-t/Serious-Engine-RT @ `0e7f223`).

- Publishing a branch publishes **every blob reachable from it**. A later removal commit does not undo this.
- Both histories contain items rated high risk:
  - game-data archives identical to retail content (`SE1_10.gro`, `SE1_10b.gro`);
  - demo recordings identical to retail files;
  - TFE `Entities` sources of unclear license.
- They also contain items rated medium risk:
  - `DSOUND.H` (Microsoft, "All Rights Reserved");
  - the LightWave SDK headers;
  - assets with no stated provenance.
- ADR-0006 forbids both publishing material of unclear status and rewriting history. A filtered history (option 3) would change nearly every commit ID and would need an ADR-0006 amendment.

## Decision

SSTRE-Engine **publishes only SSTRE's own changes, as a patch series per upstream, against pinned upstream commits.** No upstream history or upstream blobs are pushed to the SSTRE-Engine repository.

1. **Upstream lock.** SSTRE-Engine contains `upstream.lock.json` (schema: umbrella `schemas/engine-upstream-lock.schema.json`). For each upstream it lists the canonical repository URL, the full 40-hex commit SHA, its role (`primary` or `secondary`), and the patch-series directory.
2. **Patch series.** Patches live in `patches/<upstream-name>/NNNN-<slug>.patch`. They are generated with `git format-patch` from a local branch on top of the pinned commit, so authorship, dates and messages are preserved, and they are applied in order with the SSTRE patch tool (`tools/sstre_patches.py apply` in SSTRE-Engine). Plain `git am` is not enough, because deletions are exported with `--irreversible-delete` so that deleted third-party files are never reproduced (see amendment A1). Each patch contains only changes authored by SSTRE contributors, except for the documented exceptions in amendment A1.
3. **Users and CI fetch upstream from its original host** at the pinned SHA. Then they verify the commit SHA and apply the series. SSTRE redistributes no upstream content beyond the context lines inside patches.
4. **Patch content rules**, enforced by review and, later, by CI:
   - No binary patches. No patch may add, modify or rename game data, demos, screenshots, prebuilt binaries or proprietary SDK files.
   - A patch that touches files flagged in EXP-004 (for example `Entities/**`, `DSOUND.H`, LightWave SDK headers) needs explicit review, because its context lines reproduce excerpts of that file. Prefer `--unified=1` context for such files, or avoid touching them.
   - SSTRE changes to engine files are `GPL-2.0-only` with the notice `Copyright © 2026 Handelsonderneming S.D. Broekhoven, trading as ITEagle Europe`. Upstream notices are never removed.
5. **Local development** continues on local branches based on `upstream/*`. The local pre-push hook stays in place and keeps refusing any ref that contains upstream history.
6. **Upgrading the upstream pin** is a reviewed PR that updates `upstream.lock.json` and rebases the patch series. The audit is re-run on the new upstream range.

## Not covered by this ADR: binary distribution

Distributing engine **binaries** would trigger the GPL obligation to provide the complete corresponding source, and that includes the upstream source the binary was built from. Patch-only publication therefore **does not** unblock binary releases. The rule in ADR-0006 stays: no engine binaries until the licensing blockers (RD-007 Q1, Q3, Q4) are resolved. Any future binary release must also show that its build inputs exclude the questionable files, or that their redistribution has been cleared.

## Alternatives considered

| Option (EXP-004) | Outcome |
|---|---|
| 1. Publish upstream branches as-is | rejected: distributes high-risk blobs |
| 2. Publish with a later removal commit | rejected: the blobs remain in history |
| 3. Filtered-history import branch | not chosen: rewrites ~99% of commit IDs and strips commit signatures; needs an ADR-0006 amendment |
| 4. Keep everything local | remains the fallback for anything not suitable as a patch |
| **5. Own patches against pinned upstream** | **chosen (provisional)** |

## Consequences

- **Upstream dependency.** SSTRE-Engine depends on the upstream repositories staying available. Mitigation: record a [Software Heritage](https://www.softwareheritage.org/) SWHID for each pinned commit in the lock file, once archived (to be checked), and keep local mirrors. Mirrors stay unpublished.
- **New tooling:** a small, documented script that clones the upstreams, verifies the SHAs and applies the series. It must also check patches against the content rules in item 4. This is backlog item POC-27.
- **Fork model.** The repository no longer follows a "GitHub fork" model. The history-import procedure in SSTRE-Engine `docs/sstre/upstream-import-procedure.md` is superseded for publication purposes.
- **Release pins.** The umbrella `release-pins.json` refers to the SSTRE-Engine commit. The upstream pins are carried by `upstream.lock.json`.
- **Revisit** if a rights holder clarifies the status of the flagged files, or if the owner amends ADR-0006 to allow a filtered history.

## Amendment A1 (2026-11-27, lead, within the approved licensing boundaries)

Added after the first real exports (EXP-010).

1. **Deletions are exported without content.** `git format-patch --irreversible-delete` is used, and `check` rejects any patch that carries the removed content of a deleted file. `apply` rebuilds such deletions from the pinned upstream file and refuses if that file does not match. This keeps the deletion of `Source/KTX` (Apache-2.0) from republishing its source.
2. **Documented exceptions to "SSTRE-authored only"**, allowed if recorded in the series README and in THIRD_PARTY_NOTICES:
   - **(a) Backports of commits from the same upstream project.** The original author and date are kept, and the upstream commit is referenced. Example: the RTGL1 shader fix that backports upstream `a2ad71e`.
   - **(b) Vendored third-party code** under a GPL-2.0-only-compatible licence, with its licence header intact and an upstream source digest recorded. Example: the zstd 1.5.7 single-file decompressor (BSD-3-Clause OR GPL-2.0) in the `rtgl1` series.
   - **(c) Regenerated build artefacts of upstream sources** (for example Bison/Flex output from upstream grammars), when the upstream tree already tracks the generated files. Follow-up: make the build regenerate them, so the patches can drop them.
3. **Size limit:** the CI patch size limit is 1,280 KiB per patch, which fits exception (b). Larger patches need lead review.
