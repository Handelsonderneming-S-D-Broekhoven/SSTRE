# ADR-0007: Platform strategy

- **Status:** accepted in part by the owner on 2026-11-27.
  - *Accepted:* PC-first development and Windows + Linux as the initial implementation targets. Steam Deck support is desirable. Conventional rasterization is the **mandatory baseline**, and ray and path tracing are **optional** backends. Console support is a strategic research objective, not a committed release feature.
  - *Still proposed:* the specific backends and texture formats, pending spikes S1/S2.
- **Date:** 2026-11-27
- **Deciders:** project owner
- **Evidence:** [RD-005 rendering](../research/RD-005-rendering.md), [RD-006 platforms](../research/RD-006-platforms.md), [RD-007 licensing](../research/RD-007-licensing.md)

## Context

The plan fixes a PC-first direction and treats consoles as research targets, not promised ports. The Phase 0 research (RD-005/RD-006, desk research, nothing built) observed the following:

- RayTracedGL1 needs `VK_KHR_ray_tracing_pipeline`. It provides **no raster fallback** for world geometry; it rasterizes only overlays, HUD and sky.
- Serious-Engine-RT, as published, is Windows-only. The Vulkan raster renderers in Serious-Engine-Vk and SeriousSamClassic-VK emulate the original fixed-function pipeline.
- MoltenVK exposes no ray-tracing extensions. Xbox Series X|S runtime graphics are D3D12-only. PS5 and Switch/Switch 2 use proprietary, NDA-gated APIs.
- Every console distribution path observed needs a platform developer agreement *and* a license from the rights holder for the Serious Sam IP. The project has neither. Whether NDA-covered platform layers can coexist with GPL obligations is unresolved (RD-007).

## Decision

**Accepted now:**

1. Development, asset generation and the reference environment are on PC. Windows and Linux are the initial implementation targets.
2. Runtime platforms consume pre-built, platform-specific assets. No runtime platform runs AI inference.
3. Console work must not block a viable PC release.

**Platform tiers (accepted by the owner, 2026-11-27):**

| Tier | Platform | Runtime path | Status |
|---|---|---|---|
| 1 | Windows x64 | mandatory raster baseline; optional RT/PT backend (RTGL1-class) on capable GPUs | initial target |
| 1 | Linux x64 | mandatory raster baseline; RT is research (needs a Linux build of the RT backend) | initial target |
| 2 | Steam Deck (Linux/Proton) | raster baseline; RT performance is research | desirable |
| 3 | macOS | raster only via MoltenVK; RT blocked | research |
| — | Xbox Series X\|S, PS5, Switch, Switch 2 | blocked until an IP-holder license *and* a platform developer agreement exist | blocked |
| — | PS Vita | homebrew only; not pursued | blocked / low priority |

- PC runtime textures (still proposed): BCn payloads. The container is open: KTX2 is a candidate only if no Apache-2.0 code is needed in the GPLv2 runtime. Otherwise the GPLv3 AssetCompiler converts KTX2 to a format with a GPLv2-compatible loader, such as DDS or an SE1-native container (Phase 1 investigation, ADR-0006). DDS is acceptable where an upstream path needs it. ASTC is relevant only if mobile or Switch-class targets are ever unblocked.
- Shader toolchain: GLSL → SPIR-V, matching the upstream renderers. No cross-compilation layer is added until a target requires one.

## Console questions are four separate questions

Per owner direction, these are never conflated. Each one has its own status in [RD-006](../research/RD-006-platforms.md):

| Question | What it asks | Current status |
|---|---|---|
| Technical homebrew feasibility | Can the engine run on the hardware via community toolchains, without official SDKs? | research; legality varies by jurisdiction and platform (RD-007) |
| Official platform distribution | Can a title be published on the platform's store? | needs a publisher/developer agreement and platform certification; not available to the project |
| Platform SDK licensing | Can NDA-covered SDK code coexist with GPL obligations? | unresolved legal question (RD-007) |
| Game IP licensing | Does the rights holder of *Serious Sam* license the use of the IP on that platform? | not requested; prerequisite for any official distribution |

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
