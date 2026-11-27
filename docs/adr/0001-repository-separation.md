# ADR-0001: Separate repositories for umbrella, engine, asset compiler, manifests and generic toolkit

- **Status:** accepted
- **Date:** 2026-11-27
- **Deciders:** project owner (via project plan v0.1 §2–§4), lead architect
- **Evidence:** [project plan §2, §4](../project-plan.md); [repository registry](../repository-registry.md); [RD-007 licensing](../research/RD-007-licensing.md); [cross-repo contracts](../architecture/cross-repo-contracts.md)

## Context

The project combines components with different licensing constraints, release cadences and reuse potential:

- an engine derived from Croteam's Serious Engine 1, released under GPL-2.0 (the exact grant is audited in RD-007),
- independently written, game-specific asset tooling,
- declarative per-game data (recipes, mappings, locks),
- a game-agnostic texture/material processing toolkit that should be reusable for other remasters,
- an umbrella for documentation, release pins and user-facing builder UX.

GPL-2.0-only and GPL-3.0-only code cannot be combined into one derivative executable. Putting both into one monorepo with a shared build would make accidental coupling easy and the licensing boundary hard to audit.

## Decision

Keep five repositories under the `Handelsonderneming-S-D-Broekhoven` GitHub organization, with these roles and this dependency direction:

| Repository | Role | May depend on |
|---|---|---|
| SSTRE | umbrella: docs, ADRs, schemas (contract proposals), release pins, builder UX | all (by pinned revision, not by code import) |
| SSTRE-Engine | engine fork, rendering, runtime, platform ports | nothing in the other four at build or run time; consumes compiled asset files only |
| SSTRE-AssetCompiler | Serious Sam-specific discovery, extraction, mapping, conversion, packaging | Remaster-Toolkit (as a separate tool/library), Manifests (as data) |
| SSTRE-Manifests | declarative recipes, mappings, locks, overrides | schemas only; contains no executable code by default |
| Remaster-Toolkit | game-agnostic processing, QA, caching, material generation | nothing Serious Sam-specific |

Engine and independent tools communicate **only through files and documented CLI interfaces** in separate processes. Cross-repo contracts live as JSON Schema proposals in the umbrella `schemas/` directory until they stabilize.

## Alternatives considered

| Alternative | Pros | Cons | Status |
|---|---|---|---|
| Monorepo | single checkout, atomic cross-cutting changes | mixes GPL-2.0-only and GPL-3.0 code; licensing boundary harder to audit; toolkit reuse harder | rejected |
| Engine + one "tools" repo | fewer repos | game-specific and generic code mixed; toolkit not reusable | rejected |
| Git submodules everywhere | exact pins | submodule UX friction; still possible later for release pins | deferred to [cross-repo contracts](../architecture/cross-repo-contracts.md) |

## Consequences

- Each repository carries its own LICENSE and notices (see [ADR-0006](0006-licensing-boundaries.md)).
- Cross-repo changes require coordinated PRs and a release-pin update in the umbrella.
- The Remaster-Toolkit must be reviewed for Serious Sam-specific leakage (names, formats, paths).
- The engine must not link to or embed Python, ComfyUI or any inference runtime.
