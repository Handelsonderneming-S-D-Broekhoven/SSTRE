# RD-014: Ray-tracing and engine performance optimization

| Field | Value |
|---|---|
| Dossier | RD-014 |
| Author | Track DOC-R (roadmap/planning), 2026-11-28 |
| Date | 2026-11-28 |
| Status | **Draft.** Desk research and source reading only. No new measurement was made for this dossier. Numbers come from EXP-011 (E3 track, POC-28) and are labelled [EXP]. |
| Feeds | Proposed ADR "performance target and measurement policy" ([backlog](../backlog.md#proposed-adrs-for-the-leadowner)); backlog POC-33..46 |
| Related | [RD-005 rendering](./RD-005-rendering.md), [RD-008 testing/release](./RD-008-testing-release.md) §8.4, [RD-007 licensing](./RD-007-licensing.md) §5.3, [EXP-018 RT on TSE](../experiments/EXP-018-rt-tse.md), [roadmap](../roadmap.md) |

## 1. Question and scope

The owner directive of 2026-11-28 makes performance the first stage after the demonstration build (0.1.0-preview2). The target is **about 100 FPS on an NVIDIA RTX 4070, ray tracing on, high settings, upscaled texture pack loaded, 2560×1440 output**. Frame generation never counts toward it.

This dossier answers:

1. What has to be measured, with which tools, so that the four-way comparison (original Serious-Engine-RT, SSTRE RT with original assets, SSTRE RT with the upscaled pack, optimized SSTRE RT with the upscaled pack) is reproducible?
2. Where is the frame time likely to go, and which hypotheses should profiling test first?
3. What rules keep optimization honest: no silent quality loss, and a stop rule against diminishing returns?

Out of scope: PBR, hex-tiling and geometry cost (RD-011, RD-013; they reuse this protocol), and console performance.

## 2. Evidence

| ID | Source | Revision / date |
|---|---|---|
| P1 | EXP-011 draft (E3 track, local branch `sprint2/exp-011`, not yet merged) and the E3 status file: harness, validity rules, two valid baselines | 2026-11-27/28 |
| P2 | [EXP-018](../experiments/EXP-018-rt-tse.md) R4: validation-layer findings on TSE (45 errors / 6 VUIDs) and TFE (35 / 5) | 2026-11-28 |
| P3 | RTGL1 `v1.1.0` (`b1eb3d8`) and the SSTRE clean-room branch `sprint2/rtgl1-sstre` (local RTGL1 clone, contains `v1.1.0` plus the KTX2-reader commits) | as listed |
| P4 | Serious-Engine-RT `0e7f223`, `Sources/Engine/Raytracing/` | as listed |
| P5 | PresentMon README, metric definitions incl. `FrameType` ("rendered by the application or interpolated by a driver/SDK"): https://github.com/GameTechDev/PresentMon (fetched 2026-11-28, via search mirror) | 2.x |
| P6 | NVIDIA Linux driver README, "NVIDIA Smooth Motion": an implicit Vulkan layer `VK_LAYER_NV_present` that injects frames, RTX 40 series and newer: https://download.nvidia.com/XFree86/Linux-x86_64/595.58.03/README/nvpresent.html (search snippet; the Windows driver ships the feature as well, per press: https://www.tomshardware.com/pc-components/gpu-drivers/nvidias-new-driver-update-finally-brings-smooth-motion-to-rtx-40-series-gpus-works-like-amds-fluid-motion-frames-and-claims-to-double-your-fps-with-a-single-click-in-any-game) | 2025–2026 |
| P7 | RenderDoc ray-tracing support page, https://renderdoc.org/docs/behind_scenes/raytracing.html, and v1.36/v1.43 release notes (mirrors; NVIDIA RT-pipeline capture depends on driver support) | not verified against the official changelog |
| P8 | Hardware of the reference PC, confirmed by the lead with `nvidia-smi`/CIM on 2026-11-28 and recorded in EXP-011: NVIDIA GeForce RTX 4070 12 GB (driver 616.64), Intel Core i5-11600K (6 cores / 12 threads), 32 GB RAM, Windows 11 Pro 22631, display 3440×1440 at 144 Hz with 125 % scaling | 2026-11-28 |

## 3. Observed facts

### 3.1 What exists already

- [EXP] P1: the POC-28 harness (SSTRE-Engine `tools/benchmark/`, local branch `feature/poc-28-benchmarks`) plays a demo through a `+demo` option, captures PresentMon 2.6.0, `nvidia-smi` (VRAM, GPU utilization, clocks, power), per-process WDDM dedicated memory, machine and per-process CPU, foreground window and last input. It invalidates runs on focus loss, user input, foreign GPU clients or > 10 % foreign CPU load. Batches run under `gpu-lock.ps1 run -Quiet`. Analysis gives p50/p95/p99 frame time, mean FPS, CV and a regression threshold.
- [EXP] P1, **1920×1080 windowed**, demo `auto-demo0002` ("Dunes", TFE), original assets:

| Config | Valid runs | Mean FPS (CV) | p50 / p95 / p99 ms | VRAM peak MiB (GPU / process) |
|---|---|---|---|---|
| Serious-Engine-RT, RT | 4/5 | 113.0 (1.5 %) | 8.56 / 12.38 / 14.79 | 2049 / 1357 |
| Serious-Engine-RT, Vulkan raster | 5/5 | 1233.5 (2.0 %) | 0.66 / 1.49 / 2.07 | 980 / 274 |

- These are **not** 2560×1440 numbers. The new reference needs every baseline to be measured again (lead, 2026-11-28).
- [EXP] P1: the transplant (SSTRE RT on Classic-VK) and the Classic-VK raster configurations were built but not measured in the final protocol.
- [EXP] P2: with `srt_bDebugValidation=1`, TSE logs 45 errors over 6 VUIDs and TFE 35 errors over 5 VUIDs. The layer's per-message limit (10) caps four of the counts, so the real number of occurrences is higher. A TSE-only error is overlapping regions in one `vkCmdCopyBuffer` (`VUID-vkCmdCopyBuffer-pRegions-12482`). The others concern sampler `mipmapMode` in trace/dispatch, an AS build input (`pInfos-10126`), a non-acquired swapchain image and a signal semaphore in `vkQueueSubmit`.
- [EXP] E5 status: TSE `1_2_Palenque` in RT floods `RG_CANT_UPDATE_TRANSFORM` (movable brush parts whose unique ID RTGL1 does not know), then exits or hangs. Whether the defect is in SSTRE or RTGL1 is open.

### 3.2 Renderer facts that shape the hypotheses

- [SRC] P3: RTGL1 v1.1.0 is a path tracer with an A-SVGF denoiser (RD-005 §3.2). Upscalers are FSR 1.0 (spatial) and optional DLSS (temporal, `RG_RENDER_UPSCALE_TECHNIQUE_NVIDIA_DLSS` in `Include/RTGL1/RTGL1.h:1101` of `sprint2/rtgl1-sstre`). **The build has no temporal upscaler other than DLSS.** DLSS-enabled builds must not be distributed (RD-007 §5.3, Q3).
- [SRC] P3: acceleration-structure builds set `ALLOW_UPDATE` only for updateable BLAS (`Source/ASBuilder.cpp:90-105`). Static geometry is submitted once per scene (`rgStartNewScene` … `rgSubmitStaticGeometries`); movable brushes are `RG_GEOMETRY_TYPE_STATIC_MOVABLE` with per-frame transform updates (E5 status, `SceneBrushes.cpp:57-271`).
- [SRC] P4: models and particles are uploaded as dynamic geometry every frame (`Scene.cpp:272` passes model normals per upload). SKA models and terrain are not ray traced in the RT fork (RD-005 §3.3).
- [SRC] P3: texture sampling in hit shaders uses ray-cone derivatives and `textureGrad` (`Source/Shaders/RayCone.h:85-122`). The cost of sampling scales with texture size and format: uncompressed RGBA8 4096² textures cost 64 MiB each before mips.
- [SRC] RTGL1 `hl1` (`2457acc`) adds a light grid and ReSTIR/ReSTIR GI (RD-005 §3.2). Those are the upstream answers to light-sampling cost, but `hl1` is API-incompatible with v1.1.0.
- [DOC] P6: on RTX 40 GPUs the driver can inject generated frames into a Vulkan application through an implicit layer, without the application knowing. A harness that does not check for it can report frame-generated FPS by accident.
- [DOC] P5: PresentMon reports per frame whether it was application-rendered or interpolated (`FrameType`), and reports GPU-busy time, which separates GPU-bound from CPU/present-bound frames.

## 4. Assumptions and unknowns

- A1 [ASM]: path-tracing cost scales roughly with pixel count. 2560×1440 has 1.78× the pixels of 1920×1080, so the RT fork's 113 FPS at 1080p suggests **about 60–75 FPS native at 1440p** on "Dunes". Verify with POC-35. If it holds, 100 FPS native needs about 1.4–1.6× speed-up, or a temporal upscaler.
- A2 [ASM]: the upscaled pack raises VRAM and texture bandwidth (more and larger textures), not ray count. Its cost should show up as cache misses and VRAM pressure, not as AS cost. On a 12 GB card, uncompressed overrides could exceed the budget. Verify with per-config VRAM and with BCn vs RGBA8 runs.
- A3 [ASM]: at ~100 FPS (10 ms) the CPU side matters on a 6-core i5-11600K. SE1's game loop is single-threaded, and per-frame dynamic uploads (models, particles, HUD) run on that thread. Verify by GPU-busy vs frame time and per-thread CPU sampling.
- A4 [ASM]: combat scenes (many models, particles, dynamic lights) cost more than the "Dunes" demo. The current baseline under-represents them.
- U1: what "high graphical settings" means for each config. RTGL1 options (bounces, denoiser, resolution mode) and SE1 options differ between the RT fork and SSTRE. A named profile must fix them (POC-33).
- U2: whether the 100 FPS target may be met with a temporal upscaler, or must be native. The directive requires reporting them separately; it does not say which one satisfies the target. **Owner question.**
- U3: whether Nsight Graphics GPU Trace works on this RTGL1 build (likely; vendor tool) and whether RenderDoc can capture its RT pipelines on driver 616.64 (P7, unverified).

## 5. Measurement design (input to POC-33..35)

| Item | Decision |
|---|---|
| Output | 2560×1440, exclusive fullscreen or borderless at 2560×1440. A decorated 2560×1440 window does not fit the 1440-pixel-high display (P8); record the mode. |
| Render modes, reported separately | **N** native; **S** spatial upscaling (FSR 1.0); **T** temporal upscaling (DLSS local-only, or a future FSR 2+/source-built); **FG** any frame generation. N and T are separate result tables; FG is never in the target table. |
| FG guard | Before each run, record the driver frame-generation setting and the loaded implicit Vulkan layers; mark a run invalid if `VK_LAYER_NV_present` (or an equivalent) is active in N/S/T runs, or if PresentMon reports any non-application `FrameType`. |
| Metrics | Mean FPS; **1 % low** = 1000 / mean of the slowest 1 % frame times; p50/p95/p99 frame time; GPU % (`nvidia-smi utilization.gpu`, plus PresentMon GPU-busy share); CPU % (machine, game process, busiest thread); VRAM (GPU total and per-process dedicated, peak and mean). |
| Runs | 1 warm-up + 5 measured per scene × config × mode; cold shader-cache run recorded separately (RD-008 §8.4). |
| Scenes | ≥ 3 per game, including ≥ 1 combat-heavy per game (POC-34). The original RT fork has RT only for TFE, so the four-way comparison is complete for TFE; TSE has configs B–D only. |
| Quality guard | Fixed frame captures at demo checkpoints; perceptual difference (e.g. FLIP) against the reference config, numbers only in the report (images stay local). |
| Isolation | `gpu-lock.ps1 run -Quiet`, watchdog, focus/input checks (existing harness). |

## 6. Hypotheses to profile (one per directive item)

Each row becomes work only when the profile shows it matters (§8 stop rule). "Probe" is the first measurement.

| # | Area | Hypothesis | Probe |
|---|---|---|---|
| H1 | BLAS/TLAS build, caching, updates | Dynamic models are rebuilt as new BLAS every frame instead of refitted or instanced; movable brushes force updates | Nsight GPU Trace: AS-build time per frame; count of builds vs updates |
| H2 | Static vs dynamic geometry | Geometry that never moves is classified dynamic (or the reverse), so it is re-uploaded | Per-frame upload byte counter in the RT layer |
| H3 | Vulkan sync and pipeline stalls | Full-pipeline barriers or a CPU wait on the previous frame's fence serialize CPU and GPU | GPU idle gaps in Nsight Systems; fence wait time |
| H4 | CPU-side rendering overhead | Scene traversal and RT upload on the game thread take a large share of 10 ms on the i5-11600K | CPU-busy vs GPU-busy from PresentMon; sampling profiler on the game thread |
| H5 | Shader execution and traversal | Divergent any-hit shaders (alpha-tested foliage, layered materials) dominate traversal | Nsight shader profiler per ray-gen pass |
| H6 | Redundant uploads | Textures or geometry are re-uploaded after scene changes or each frame | Upload counters; RTGL1 staging-buffer traffic |
| H7 | Texture caching, compression, VRAM | Upscaled overrides are uncompressed or not BCn, raising VRAM and bandwidth | VRAM per config; pack format census (aggregate counts only) |
| H8 | Denoising | A-SVGF passes cost a fixed several ms at 1440p | Per-pass GPU time |
| H9 | Light sampling and needless rays | All lights are sampled per pixel; shadow rays for lights that cannot contribute | Ray counts per pass; light count per frame |
| H10 | DLSS/FSR | FSR 1.0 is spatial; a temporal upscaler at "Quality" would cut ray work by ~2.25× pixels | N vs S vs T runs |
| H11 | Multithreading | Upload preparation could run off the game thread | Thread timeline |
| H12 | Frame pacing | p99 spikes come from shader compilation, AS rebuilds after load, or present-mode interaction | p99/1 % low vs mean; spike correlation with events |

## 7. Tools

| Tool | Use | Licence / note |
|---|---|---|
| PresentMon 2.6.0 (pinned, in use) | frame times, frame type, GPU busy | MIT (EXP-011) |
| `nvidia-smi`, WDDM counters | VRAM, utilization | NVIDIA driver tool / Windows |
| Nsight Systems / Nsight Graphics | CPU-GPU timeline, GPU Trace, RT shader profiling, AS inspection | proprietary, free; local only, never a CI dependency (RD-008 §8.4) |
| RenderDoc | frame inspection; RT pipeline capture on NVIDIA only with driver support (P7) | MIT; verify on 616.64 |
| Vulkan validation layers (SDK 1.4.363.0) | correctness, with the duplicate-message limit disabled for counting | Khronos, Apache-2.0 (tool use only) |
| Engine counters (to add) | upload bytes, BLAS builds/updates, ray counts, `VK_EXT_memory_budget` | SSTRE patches |

## 8. Rules

1. **No silent quality reductions.** Any change that alters the image beyond the quality-guard threshold (§5) must be an explicit setting, off by default unless the owner approves, and listed in a settings registry with its measured cost and benefit.
2. **Profile first.** No optimization work package starts without a profile that attributes its share of the frame time.
3. **Stop rule.** Stop optimizing and escalate to the owner when either (a) two consecutive optimization work packages each gain less than the larger of 3 % mean FPS or the measured regression threshold on the scene set, or (b) the Phase-1 effort budget is spent (proposed 25 pd, owner to confirm), and the target is not met. The escalation memo names the architectural limits found, the remaining gap per scene and mode, and realistic alternatives (temporal upscaling as the default for the target, an RTGL1 revision change, reduced-cost RT presets as explicit settings, a lower reference resolution).
4. **Frame generation** is reported, never counted.

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 100 FPS native at 1440p not reachable on RTGL1 v1.1.0 | medium [ASM] | high | stop rule; temporal-upscaler path; RTGL1 revision study (POC-42) |
| DLSS is the only temporal upscaler and cannot be distributed | high | medium | source-built FSR 2+ (MIT) evaluation; report T results per upscaler |
| Driver frame generation contaminates numbers | low | high | FG guard (§5) |
| Benchmark noise from other tracks | medium | medium | quiet mode, contention checks (existing) |
| Optimizations change the image | medium | high | quality guard, settings registry |
| Demo playback is not deterministic for combat | medium | medium | POC-14 replay checks; end-state comparison |

## 10. Recommendation

Reuse the POC-28 harness; extend it for 1440p, render-mode tagging, 1 % lows, the FG guard and per-thread CPU. Re-measure all baselines at 1440p before any optimization. Profile two scenes per game with Nsight, rank H1–H12 by measured share, and run optimization packages only in that order, each with a before/after benchmark and quality check. Treat the Vulkan validation clean-up and the RTGL1 defects as Phase 1 work: they can hide synchronization costs and invalidate measurements.

## 11. Decision dependencies

- Owner: whether temporal upscaling may satisfy the target (U2); the meaning of "high settings" (U1); the Phase-1 budget for the stop rule.
- Proposed ADR on performance target and measurement policy.
- RD-007 Q3 for any DLSS distribution (local measurement only meanwhile).

## 12. Next steps

POC-33 (harness v2) → POC-34 (scene set) → POC-35 (four-way baseline) → POC-36 (profiling) → POC-37..42 by measured priority, with POC-43..45 (validation, RTGL1 defects, quality guard) in parallel → POC-46 (optimized run D and final report). See the [backlog](../backlog.md#stage-m1--ray-tracing-and-engine-performance-directive-phase-1).
