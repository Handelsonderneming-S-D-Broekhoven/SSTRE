# Roadmap

**Current stage: M0, demonstration build** (0.1.0-preview2). Phase 0 was reviewed by the owner on 2026-11-27. No calendar or budget is approved; effort is estimated per work package in the [backlog](backlog.md).

## Priority order (owner directive, 2026-11-28, binding)

**Demonstration Build → Performance Optimization → PBR & Hex-Tiling → Geometry Enhancement → Native Controller Support → Multicontroller & Split-Screen → Console Ports.**

The directive takes effect once preview2 is completed, validated and committed. Planning and documentation may start at once. CPU-only research, asset processing and tooling may run in parallel with any stage if they do not disturb measurements (GPU lock and quiet mode). The directive's "Phase 1" is stage M1, its "Phase 2" is M2 + M3, and its "Phase 3" is M4 + M5.

| Stage | Objective | Entry criteria | Exit criteria (measurable) | Work packages | Status |
|---|---|---|---|---|---|
| **M0** Demonstration build | Integrated, playable preview: Classic-VK engine, optional RT, local HD layers, reproducibly AI-enhanced textures for the slice levels | sprint-2 pieces available | preview2 assembled locally; TFE `01_Hatshepsut` and TSE `1_0_InTheLastEpisode` and `1_1_Palenque` play in RT, Vulkan and OpenGL, and `1_2_Palenque` does not hang; engine patch series and docs merged after green CI; nothing questionable published (GATE-05) | sprint 2 ([backlog status](backlog.md#phase-1-sprint-status-2026-11-27)) | in progress |
| **M1** RT and engine performance | ≈100 FPS mean with RT, "High" profile and the upscaled pack at 2560×1440 on an RTX 4070, without frame generation | M0 exit; benchmark harness v2 (POC-33) ready | (a) four-way benchmark A/B/C/D on ≥ 3 TFE and ≥ 3 TSE scenes incl. combat, with avg FPS, 1 % low, p50/p95/p99, GPU %, CPU % and VRAM, reported per mode (native, spatial, temporal, frame generation); (b) target met in the agreed mode, **or** the stop rule triggered and the owner has decided on the escalation memo; (c) 0 Vulkan validation errors in RT and raster on the test levels; (d) RTGL1 defects classified and fixed or documented; (e) no image change without an explicit setting (quality guard) | POC-33..46 | not started |
| **M2** PBR and hex-tiling | PBR materials (normal, roughness, metallic, height, emissive), automated classification and QA, compression and packing, quality profiles; realtime stochastic hex-tiling as a generic RTGL1 feature, with baked, hybrid and low-end variants | M1 exit (optimized baseline D recorded) | (a) RD-008 §5 phase-5 criteria a–d; (b) hex-tiling criteria in RD-011 §7; (c) each feature benchmarked alone and combined against D (POC-53); none with disproportionate cost is on by default | POC-47..53 | not started |
| **M3** Geometry enhancement | Less visible angularity of world geometry: normal smoothing, terminator correction, selective subdivision, optional displacement | M2 materials available (displacement needs height maps); techniques 1–2 may overlap M2 | RD-013 §7 criteria; collision, gameplay end state and UVs unchanged; all techniques optional; costs in POC-53 | POC-54..56 | not started |
| **M4** Native controller support | PC fully usable without keyboard and mouse; Xbox, DS4/DualSense and generic pads; Steam Input; Steam Deck | M2/M3 implemented and validated (input design may start earlier, CPU only) | RD-012 §7 items 1–3; Steam Deck validated on hardware | POC-57..60 | not started |
| **M5** Multicontroller and split-screen | Per-player assignment, mixed devices, 4-player split-screen; RT split-screen feasibility | M4 exit | RD-012 §7 item 4 | POC-61..62 | not started |
| **M6** Console ports | **Research only** (ADR-0007): keep RD-009/RD-010 current and the interfaces portable | none | no console build is made; a port would need an IP-holder licence, a platform agreement and counsel answers (RD-007 Q14/Q19) | POC-63 | research |

Cross-cutting rules (details in the [backlog](backlog.md#rules-for-all-stage-m1m5-packages)): no silent quality reductions; profile before optimizing; frame generation never counts toward a target; a diminishing-returns stop rule with escalation to the owner; TFE and TSE both; Vulkan and OpenGL raster keep working alongside optional RT; original gameplay and art direction preserved; licensing, clean-room and publication gates unchanged.

## Foundation phases (Phase 0 plan)

The original phase table stays valid as a list of capabilities. Its order is now governed by the stages above.

| Phase | Objective | Status / where it went |
|---|---|---|
| 0 | Bootstrap and evidence-based research | done (owner-reviewed 2026-11-27) |
| 1 | Engine baseline | builds and TFE/TSE launch done; the performance baseline moves into M1 (POC-35, at 2560×1440) |
| 2 | Asset extraction and mapping | partly done (EXP-007/008/012); continues in parallel (CPU) |
| 3 | AI toolkit prototype | PoC done for the slice (EXP-013); continues in parallel |
| 4 | First full texture build | after M1 has set the VRAM and performance budget; CPU work may run in parallel |
| 5 | PBR integration | = M2 |
| 6 | Rendering and TSE compatibility | RT on TSE done for the slice (EXP-018); full coverage spread over M1–M3 |
| 7 | PC alpha | after M4 (controller support is part of a usable PC build) |
| 8 | Console feasibility and ports | = M6, research only |
| 9 | Public stable release | after counsel clears the binary-distribution blockers (RD-007, RD-010) |

Notes:

- Console work is optional and must not block a viable PC release. Xbox Series X|S, PS5 and Switch/Switch 2 are research targets, not promised ports. See [RD-006](research/RD-006-platforms.md), [RD-009](research/RD-009-ps5-homebrew.md) and [RD-010](research/RD-010-homebrew-distribution.md).
- Future games are outside the current delivery scope.
- Gate criteria for the foundation phases are in [RD-008](research/RD-008-testing-release.md) §5. Proposed ADRs for the new stages are listed in the [backlog](backlog.md#proposed-adrs-for-the-leadowner).
