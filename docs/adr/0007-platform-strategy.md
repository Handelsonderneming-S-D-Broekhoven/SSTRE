# ADR-0007: Platform strategy

- **Status:** split.
  - *Accepted:* PC-first development; PC-side asset generation; no AI inference on any runtime platform.
  - *Proposed:* platform tiers, graphics backends and texture formats below.
- **Date:** 2026-11-27
- **Deciders:** project owner (project plan v0.1 §3); lead architect proposes
- **Evidence:** [RD-005 rendering](../research/RD-005-rendering.md), [RD-006 platforms](../research/RD-006-platforms.md), [RD-007 licensing](../research/RD-007-licensing.md)

## Context

The plan fixes a PC-first direction and treats consoles as research targets, not promised ports. The Phase 0 research (RD-005/RD-006, desk research, nothing built) observed the following:

- RayTracedGL1 needs `VK_KHR_ray_tracing_pipeline`. It provides **no raster fallback** for world geometry; it rasterizes only overlays, HUD and sky.
- Serious-Engine-RT, as published, is Windows-only. The Vulkan raster renderers in Serious-Engine-Vk and SeriousSamClassic-VK emulate the original fixed-function pipeline.
- MoltenVK exposes no ray-tracing extensions. Xbox Series X|S runtime graphics are D3D12-only. PS5 and Switch/Switch 2 use proprietary, NDA-gated APIs.
- Every console distribution path observed needs a platform developer agreement *and* a license from the rights holder for the Serious Sam IP. The project has neither. Whether NDA-covered platform layers can coexist with GPL obligations is unresolved (RD-007).

## Decision

**Accepted now:**

1. Development, asset generation and the reference environment are on PC (Windows first, Linux second).
2. Runtime platforms consume pre-built, platform-specific assets. No runtime platform runs AI inference.
3. Console work must not block a viable PC release.

**Proposed (pending Phase 1 spikes S1/S2 in RD-005/RD-006 and owner confirmation):**

| Tier | Platform | Runtime path | Status |
|---|---|---|---|
| 1 | Windows x64 | Vulkan; RT backend (RTGL1-class) optional on capable GPUs; non-RT raster baseline | proposed |
| 1 | Linux x64 | Vulkan raster baseline; RT is research (needs a Linux build of the RT backend) | proposed |
| 2 | Steam Deck (Linux/Proton) | Vulkan raster baseline; RT performance is research | proposed |
| 3 | macOS | raster only via MoltenVK; RT blocked | research |
| — | Xbox Series X\|S, PS5, Switch, Switch 2 | blocked until an IP-holder license *and* a platform developer agreement exist | blocked |
| — | PS Vita | homebrew only; not pursued | blocked / low priority |

- PC runtime textures: KTX2 with BCn payloads, as proposed. DDS is acceptable where an upstream path needs it. ASTC is relevant only if mobile or Switch-class targets are ever unblocked.
- Shader toolchain: GLSL → SPIR-V, matching the upstream renderers. No cross-compilation layer is added until a target requires one.

## Alternatives considered

| Alternative | Why not (yet) chosen |
|---|---|
| RT-only renderer | Excludes non-RT GPUs, macOS and likely the Steam Deck; RTGL1 has no raster fallback |
| Raster-only, no RT | Contradicts the project's ray-tracing target |
| Early console work | No authorization path; GPL/NDA conflict unresolved; diverts effort from PC |

## Consequences

- The engine decision ([ADR-0005](0005-engine-foundation.md)) must keep a raster path. A PBR-capable raster renderer is new work, because the existing Vulkan raster paths are fixed-function emulations (RD-005).
- The asset compiler must support at least two runtime profiles: RT with PBR maps, and raster.
- Revisit this ADR when rights-holder licensing changes, or when spikes S1/S2 report.

## Acceptance criteria for the proposed parts

- Spike S2 (RD-006) meets criteria S2.1–S2.6 on Windows and Linux.
- The owner confirms that a raster baseline is acceptable alongside optional RT.
- The owner decides whether to approach the rights holder about licensing (a prerequisite for any console work).
