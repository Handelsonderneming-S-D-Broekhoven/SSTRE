# ADR-0005: Engine foundation

- **Status:** accepted as the **provisional implementation direction** (owner, 2026-11-27). The final engine selection still depends on successful compilation, source-level analysis and the rendering feasibility spike (acceptance criteria below). Until they are met, this ADR may be revised.
- **Date:** 2026-11-27 (proposed and provisionally accepted)
- **Deciders:** project owner
- **Evidence:** [RD-001 engine baseline](../research/RD-001-engine-baseline.md), [RD-005 rendering](../research/RD-005-rendering.md), [RD-006 platforms](../research/RD-006-platforms.md), [RD-007 licensing](../research/RD-007-licensing.md)

## Context

The plan names sultim-t/Serious-Engine-RT as the preferred engine candidate and tx00100xt/SeriousSamClassic-VK as the alternative (plan §3, open decision 1). Phase 0 source inspection found the following. Nothing was built; revisions are listed in RD-001.

| Aspect | Serious-Engine-RT (`0e7f223`, v1.5, 2022-04-20) | SeriousSamClassic-VK (`510d36f`, 2026-01) |
|---|---|---|
| Lineage | git descendant of Croteam `b408e88` via Serious-Engine-Vk | no shared git history with Croteam; squashed import |
| Activity | dormant since 2022; unreleased `dev` branch | active; CI green across 12 jobs |
| Build | MSVC v143, Windows x64 only | CMake (Unix), MSVC solutions (Windows); many OS/arch targets |
| TFE / TSE | RT enabled **only for TFE** (`SE1_RAYTRACING` in the TFE project); TFE level and texture tables hard-coded | separate TFE and TSE trees |
| RT | RTGL1 v1.1.0-era API (unpinned, `RTGL1_SDK_PATH`); about 10k lines in `Engine/Raytracing/`; SKA models and terrain not ray-traced | no RT (vestigial `GAT_RT` comment) |
| Raster | OpenGL/Vulkan paths still compiled; working state **unverified** | Vulkan + OpenGL fixed-function paths |
| PBR overrides | `.ktx2` + `_n`/`_rme` by virtual path | none |

RTGL1 itself has no raster fallback for world geometry (RD-005). [ADR-0007](0007-platform-strategy.md) proposes keeping a non-RT path on every tier.

## Decision (provisional)

**Use SeriousSamClassic-VK as the primary engine baseline. Use Serious-Engine-RT as a secondary upstream and as the source of rendering functionality, ported as an optional rendering backend** ("Classic-VK-first, RT optional"). Support for both TFE and TSE is preserved.

- Import Serious-Engine-RT **unmodified** into SSTRE-Engine as a reference branch. It is the source for the RT port and for the PBR-override mechanism.
- Import Classic-VK's history as the primary main line.
- Both upstream histories are imported locally as `upstream/classic-vk-main` and `upstream/rt-main`, with commit history and attribution preserved. **Before these branches are published**, the questionable headers, binary files and game-data archives are audited ([ADR-0006](0006-licensing-boundaries.md)). Public availability upstream is not taken as proof of redistribution rights.
- Both imports are non-destructive and use namespaced branches. See [the import procedure](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-Engine/blob/phase0/bootstrap/docs/sstre/upstream-import-procedure.md); the branch is local and not yet pushed.

## Alternatives considered

| Alternative | Pros | Cons | Status |
|---|---|---|---|
| **RT-first** (Serious-Engine-RT as the main line) | RT and PBR overrides already work for TFE; closest to the visual target | Windows-only; TFE-only RT; dormant; unpinned RTGL1; raster fallback unverified; TSE work large | defensible only if the port proves very costly *and* RT's raster path works |
| **Classic-VK-first, RT optional** | active upstream; cross-platform; TFE+TSE; matches the ADR-0007 raster baseline | the RT port is substantial; Classic-VK has no git ancestry from Croteam (provenance tracked via CHANGELOG) | **proposed** |
| Croteam official / Serious-Engine-Vk | original lineage | outdated toolchains; no RT; superseded by both of the above | reference only |
| New engine | — | contradicts the "reuse existing work" requirement | rejected |

## Consequences

- Phase 1 must build *both* candidates unmodified on the reference PC (POC-01/02 in the [backlog](../backlog.md)).
- The RT backend port, including TSE and SKA/terrain coverage, becomes a major work package, sized after the spikes.
- The PBR override convention (`.ktx2`, `_n`, `_rme`) becomes an input contract for SSTRE-AssetCompiler, pending this ADR's acceptance.

## Acceptance criteria

1. Both candidates build from documented, pinned revisions on the reference PC. Failures are recorded with exact errors.
2. Classic-VK launches TFE and TSE with user-owned Classic data. The RT fork launches TFE.
3. RD-001 criteria S1–S8 and RD-005 spike S1 are measured and reported, including a sized estimate for porting the RT backend.
4. RD-007 confirms no license blocker in either base (for example, the unlicensed `Entities/*.es` files in the RT fork and the bundled `.gro` data).
5. ~~The owner approves the decision and the history-import option.~~ Done for the provisional direction and the local import (2026-11-27). Publishing the upstream branches still requires the audit in item 4.
