# Repository registry

Status: Phase 0. Observed state recorded 2026-11-27 from local clones and the
GitHub API (all repositories public, owner `Handelsonderneming-S-D-Broekhoven`).
Do not substitute a guessed ITEagle organization.

## Repositories

| Repository | Role | Intended license | Observed state (2026-11-27) |
|---|---|---|---|
| [SSTRE](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE) | Umbrella: documentation, research dossiers, ADRs, cross-repo contracts (`schemas/`), release pins, later the user-facing builder and packaging | Proposed GPL-3.0-only for original code, subject to dependency audit | `main` @ `a8c73d2`, one commit ("Initial commit"), 2-line README, no license |
| [SSTRE-Engine](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-Engine) | Engine fork: rendering, game compatibility, runtime, platform ports | Preserve upstream licenses and notices; never relicense | `main` @ `d17edbb`, one commit, README only. **Not a GitHub fork and contains no upstream history yet**; base engine pending ADR-005 |
| [SSTRE-AssetCompiler](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-AssetCompiler) | Serious Sam-specific discovery, extraction, normalization, HD-to-Classic mapping, runtime format conversion, compilation and packaging | Proposed GPL-3.0-only for independent original code, subject to dependency audit | Empty repository, zero commits, no default branch |
| [SSTRE-Manifests](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-Manifests) | Declarative data: defaults, material profiles, mappings, per-game recipes, curated overrides, generated lock manifests | Proposed GPL-3.0-only for original contributions; suitability for data under review | `main` @ `13d52c1`, one commit, README only, no license |
| [Remaster-Toolkit](https://github.com/Handelsonderneming-S-D-Broekhoven/Remaster-Toolkit) | Game-agnostic texture processing, workflow execution, QA, caching, material generation, later curation tools | Proposed GPL-3.0-only for independent original code, subject to dependency audit | `main` @ `c0cfd64`, one commit, README only ("ITEagle Remaster-toolkit"), no license |

Licensing for all repositories: pending owner confirmation — proposed GPL-3.0
(see `docs/research/RD-007-licensing.md`). Nothing in this table is a legal
conclusion.

## Bootstrap branches

Phase 0 scaffolding is prepared locally on branch `phase0/bootstrap` in each
repository. Nothing is pushed until the owner approves.

## Interfaces between repositories

See [architecture/cross-repo-contracts.md](./architecture/cross-repo-contracts.md)
for dependency direction, file and CLI interfaces, schema ownership and the
version-pinning proposal.

## Upstream engine candidates (reference only, not dependencies yet)

| Upstream | Role in research |
|---|---|
| https://github.com/sultim-t/Serious-Engine-RT | Primary engine candidate (ray tracing) |
| https://github.com/tx00100xt/SeriousSamClassic-VK | Alternative foundation (Vulkan, Linux/Windows) |
| https://github.com/Croteam-official/Serious-Engine | Original source release |
| https://github.com/sultim-t/Serious-Engine-Vk | Vulkan port preceding the RT fork |
| https://github.com/sultim-t/RayTracedGL1 | Ray tracing library used by the RT fork |

The evaluation and exact commits examined are recorded in
`docs/research/RD-001-engine-baseline.md`; the decision in ADR-005.
