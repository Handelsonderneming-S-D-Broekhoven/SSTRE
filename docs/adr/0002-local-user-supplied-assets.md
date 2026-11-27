# ADR-0002: Game data is supplied locally by the user and never distributed by the project

- **Status:** accepted as *project policy*. This is **not** a legal clearance; see open questions in [RD-007](../research/RD-007-licensing.md).
- **Date:** 2026-11-27
- **Deciders:** project owner (project plan v0.1 §1, §3), lead architect
- **Evidence:** [RD-002 HD assets](../research/RD-002-hd-assets.md), [RD-007 licensing](../research/RD-007-licensing.md)

## Context

Serious Sam: The First Encounter and The Second Encounter (Classic and HD editions) are commercial products. Croteam's 2016 GPL release of the Serious Engine 1 source covers the engine source code, not the game content. The project is independent of Croteam and Devolver Digital.

## Decision

1. Users supply their own legally acquired installations (for example Steam or GOG). SSTRE tools detect and validate them locally.
2. No repository, CI job, release, issue attachment or Git LFS store may contain original game assets, extracted assets, generated derivatives of game assets (including AI-upscaled textures and screenshots of restricted content), proprietary SDKs, secrets or model weights.
3. Manifests may contain *metadata* about assets (stable IDs, archive-relative virtual paths, hashes, dimensions, recipe parameters). **Owner decision, 2026-11-27:** game asset identifiers, paths and hashes may be used locally. They are published only after their provenance has been confirmed and the applicable restrictions have been reviewed (backlog GATE-05).
4. Asset builds run on the user's machine. The project distributes only tooling, recipes and engine code.
5. CI uses synthetic or properly licensed fixtures only.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Distribute pre-built remastered texture packs | Derivatives of copyrighted assets; requires rights-holder permission the project does not have |
| Download game data automatically from third parties | Unauthorized distribution; prohibited |
| Ship only diffs/patches of assets | Still derivative content; legally unclear, so treated like the option above until counsel says otherwise |

## Consequences

- The user-side builder (umbrella) is a core deliverable, not an afterthought, and it requires reproducible local builds (see [ADR-0003](0003-dev-release-separation-locked-recipes.md)).
- Repository `.gitignore` files and the validation script block common game-data extensions.
- Testing that needs real game data runs only on developer machines. Evidence from those runs is shared as numbers and text, not as restricted images.
- Local processing alone does not establish permission to distribute anything; any distribution question goes to the owner and counsel.
