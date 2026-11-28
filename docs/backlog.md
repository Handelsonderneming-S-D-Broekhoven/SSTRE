# SSTRE POC backlog

> **Status: draft, reconciled by the lead with RD-001..007 and ADR-0005..0007 on 2026-11-27.** Drafted by Agent G (QA/release). Nothing here is implemented. Priorities, owners and estimates are proposals awaiting owner approval.

Expands the plan's §8 "First POC backlog". Each item lists the open decision(s) from plan §3 it informs (1 engine, 2 editions/HD mapping, 3 AI models, 4 determinism, 5 PBR/metadata representation, 6 backends/packaging, 7 consoles, 8 GUI/CLI/CI/release format). QA gate definitions referenced below are in [RD-008](./research/RD-008-testing-release.md).

## Estimation assumptions

- One person-day (pd) = ~6 focused hours by a contributor already familiar with C++/CMake and Python.
- Reference PC with a ray-tracing-capable GPU is available; user-owned Steam Classic + HD installs available locally (Phase 0 lead inspection). GOG editions are **not** available — anything GOG-specific is out of these estimates.
- Ranges cover "works roughly as documented" (low) to "requires patching build files or reverse-engineering" (high). They exclude review/approval wait time. They are not commitments; re-estimate after POC-01/02.
- No game data in CI; local-only steps produce aggregate reports (numbers + hashes) only.

## Priority 0 — foundations (can start immediately, parallel)

| ID | Goal | Owner repo | Depends on | Deliverable | Done when (measurable) | Effort (pd) | Informs |
|---|---|---|---|---|---|---|---|
| POC-01 | Build RT candidate (Serious-Engine-RT @ `0e7f223`, with RTGL1 `v1.1.0` @ `b1eb3d8` — the revision RD-001/RD-005 *infer*, since it is unpinned upstream) unmodified, Windows x64 | SSTRE-Engine (notes in `docs/sstre/`) | RD-001; owner approval to build untrusted upstream in an isolated environment; Vulkan SDK + `glslc` installed (absent on the host) | Build log + exact commit + toolchain versions + failure list | Two clean builds from pinned commit by documented steps; binaries launch to main menu with TFE Classic data, or failure documented with root cause | 2–6 | 1, 6 |
| POC-02 | Build the proposed main-line candidate (SeriousSamClassic-VK @ `510d36f`) unmodified, Windows + Linux (ADR-0005) | SSTRE-Engine | RD-001; CMake installed; MSVC v140 solutions retargeted to v143 (only v142/v143 are installed) | As POC-01, both OSes | Same criteria as POC-01 per OS | 2–6 | 1, 6 |
| POC-03 | Local edition inventory and detection | SSTRE-AssetCompiler | RD-002 | Edition detection spec + aggregate report (archive names, SHA-256, counts) | Each local install (TFE/TSE Classic, TFE/TSE HD, Fusion) identified by top-level archive hashes; report contains no proprietary file listings | 1–3 | 2 |
| POC-04 | Cross-repo schemas v0 (inventory, recipe, lock/provenance, qa-report, release-pins) | SSTRE (`schemas/`) | RD-002, RD-004 | JSON Schemas + positive/negative examples (synthetic) | All examples validate/fail as expected in CI; reviewed by AssetCompiler/Toolkit owners | 3–6 | 5, 8 |
| POC-05 | Minimal CI: Markdown/link lint, schema validation, game-data leak scan | SSTRE (+ copy to other repos) | POC-04 (partial), Agent F scaffold | Workflow files, pinned actions, `.gitignore` patterns | CI green on all 5 repos; leak scan fails on a planted `.tex`/`.dem`/`.sav`/>1 MB binary in a test branch | 1–3 | 8 |

## Priority 1 — engine baseline and harness

| ID | Goal | Owner repo | Depends on | Deliverable | Done when (measurable) | Effort (pd) | Informs |
|---|---|---|---|---|---|---|---|
| POC-13 | Performance/VRAM capture protocol | SSTRE (docs) + SSTRE-Engine | POC-01 or POC-02 | Capture script/instructions (SE1 `dem_bProfile`, PresentMon, MangoHud), report template | 5 repeated runs of one demo produce parsed p50/p99/peak VRAM; run-to-run variance reported; regression threshold derived | 2–4 | 1, 4, 6 |
| POC-14 | Demo record/playback determinism in candidate fork(s) | SSTRE-Engine | POC-01/02 | Report: Classic-recorded demo in fork; fork-recorded demo replayed 5× | End-state (position/health/score/time) identical in 5/5 replays of fork-recorded demos; Classic-demo result recorded pass/fail with cause | 2–5 | 1, 4 |
| POC-15 | Savegame compatibility probe | SSTRE-Engine | POC-01/02 | Report per edition | Classic save → fork load result recorded per candidate; fork save/load round trip works | 1–2 | 1 |
| POC-16 | TSE launch spike on each candidate | SSTRE-Engine | POC-01/02 | Report | TSE Classic reaches main menu + loads 3 levels, or blockers documented | 2–5 | 1, 6 |
| POC-17 | Engine baseline capture (Phase 1 gate) | SSTRE-Engine + SSTRE | POC-13, POC-14 | Baseline report: ≥3 demos per campaign attempted, perf + VRAM, local screenshots (not committed) | Phase 1 gate (RD-008 §5) criteria a–e satisfied and linked | 2–4 | 1 |

## Priority 1 — assets and toolkit

| ID | Goal | Owner repo | Depends on | Deliverable | Done when (measurable) | Effort (pd) | Informs |
|---|---|---|---|---|---|---|---|
| POC-06 | Select 50-texture test matrix | SSTRE-Manifests (IDs/metadata only) | POC-03, RD-002 | Matrix of stable asset IDs + class tags (architecture, terrain, vegetation, enemies, weapons, UI, alpha, normal, technical masks, animated, tileable) | 50 entries; every class has ≥3 items; committed data contains only IDs/metadata, no pixels | 1–2 | 2, 3 |
| POC-07 | `.tex` read + round-trip locally | SSTRE-AssetCompiler | POC-03, RD-002, ADR-0006 boundary: either a clean-room reader built from a written format spec, or a separate GPL-2.0-only helper process | Reader + round-trip test (local data) | All 50 matrix items decode; `.tex → intermediate → .tex` byte-identical or field-level diff explained | 4–10 | 2, 5 |
| POC-08 | HD-to-Classic mapping on matrix + one level import | SSTRE-AssetCompiler + Manifests | POC-06, POC-07 | Mapping table (matched/ambiguous/unmatched) + level load report | Every matrix item classified; one representative level loads with mapped assets or documented Classic fallback | 4–10 | 2 |
| POC-09 | SR vs controlled diffusion benchmark | Remaster-Toolkit | POC-06, RD-003 | Benchmark report: GPU time, VRAM, metrics, seams, human audit | All 50 processed by ≥2 SR and ≥1 diffusion workflow; per-asset time/VRAM recorded; blind 2-reviewer audit done | 5–12 | 3 |
| POC-10 | QA checker v0 + threshold calibration | Remaster-Toolkit | POC-04, POC-09 | Checker (dims, alpha, seams, SSIM/LPIPS/DISTS, color, provenance, forbidden-diffusion) + synthetic unit tests + calibration report | Synthetic suite in CI passes; on matrix, per-class thresholds chosen with reviewer κ and checker-vs-human agreement reported | 5–10 | 3, 5 |
| POC-11 | Fallback ladder + failure isolation | Remaster-Toolkit | POC-10 | Ladder implementation + fault-injection test | N injected failures (timeout/OOM/check fail) → build completes, N reported with reason codes, assets fall to expected level | 2–4 | 3, 8 |
| POC-12 | Double build + incremental invalidation + resume | Remaster-Toolkit | POC-04, POC-11, RD-004 | Test suite (synthetic in CI; matrix locally) + report | Reference env: hash-match rate per stage reported vs RD-004 target; all 7 invalidation mutations (RD-008 §7.3) recompute exactly expected set; resumed build hashes = uninterrupted | 4–8 | 4, 8 |
| POC-18 | Synthetic `.tex` fixture writer (future, gated) | SSTRE-AssetCompiler | POC-07, RD-007 ruling | Procedural fixture generator + golden tests | Generated fixtures cover TDAT/FRMS/ANIM variants; reader passes them in CI; local real files still pass | 3–6 | 5, 8 |

## Priority 1 — rendering, platform and HD-format spikes (added by lead from RD-002/005/006)

| ID | Goal | Owner repo | Depends on | Deliverable | Done when (measurable) | Effort (pd) | Informs |
|---|---|---|---|---|---|---|---|
| POC-22 | Rendering spike S1: RT fork's raster paths, PBR override path (`.ktx2`, `_n`/`_rme`), RTGL1 revision confirmation | SSTRE-Engine | POC-01 | Report against RD-005 criteria S1.1–S1.7 | Every S1 criterion recorded as pass/fail with evidence; RTGL1 revision confirmed or refuted | 3–6 | 1, 5, 6 |
| POC-23 | Platform spike S2: Classic-VK Vulkan raster on Windows + Linux (+ Steam Deck if available) | SSTRE-Engine | POC-02 | Report against RD-006 criteria S2.1–S2.6 | Every S2 criterion recorded; Linux result included | 2–5 | 6, 7 |
| POC-24 | RT-backend port sizing: RD-001 criteria S1–S8, TSE + SKA/terrain coverage gap | SSTRE-Engine + SSTRE | POC-22, POC-23 | Sized estimate + risk list feeding ADR-0005 | Estimate with an explicit range and assumptions; ADR-0005 can move to accepted or be revised | 2–4 | 1 |
| POC-25 | HD `CTSEMETA` texture header experiment (RD-002 E-B1), local only | SSTRE-AssetCompiler | POC-03; owner go-ahead after RD-007 Q6 position (reverse engineering HD formats) | Aggregate report: decoded dimensions/pixel formats for HD textures matched in RD-002 | ≥ 90% of path-matched HD textures decode to known dimensions/format, or blocker documented | 3–8 | 2 |
| POC-27 | Patch-series tooling for ADR-0008: fetch the pinned upstreams, verify SHAs, `git am` the series, enforce the patch content rules (no binaries or game data; flag patches touching EXP-004 items); export the local build branches as `patches/<upstream>/` | SSTRE-Engine (+ umbrella validator) | ADR-0008, EXP-001/002 build commits | Script + CI job + first exported series | Clean checkout → fetch → apply reproduces the local build branch tree byte-for-byte (tree hash equal); a planted binary or game-data patch fails CI | 2–4 | 1, 8 |

## Owner and legal gates (not engineering effort)

| ID | Decision | Source | Blocks |
|---|---|---|---|
| GATE-01 | ~~SPDX identifier per repo; copyright-holder wording; DCO vs CLA~~ **Decided 2026-11-27** (ADR-0006) | ADR-0006 | — |
| GATE-02 | **Decided 2026-11-27:** upstream histories stay local; SSTRE-Engine publishes only own patches against pinned upstream commits (ADR-0008, provisional). Audit done (EXP-004) | ADR-0005, ADR-0006, ADR-0008 | — |
| GATE-03 | Counsel review of RD-007 Q1 (Apache-2.0 KTX in RTGL1), Q3 (DLSS), Q4 (entity-code provenance), Q6 (local conversion under the EULA/SSA, HD reverse engineering), Q12 (trademark/project name) | RD-007 §16 | any binary release; POC-25 |
| GATE-04 | Whether to approach the rights holder (Croteam/Devolver) for a license. Consoles stay a research objective (owner, 2026-11-27) | RD-006, ADR-0007 | official console distribution |
| GATE-05 | Publishing per-asset identifiers, paths and hashes. Owner: local use allowed; publish only after provenance and restrictions are reviewed | ADR-0002, RD-002, RD-007 | committing POC-03/POC-06 output publicly |

## Priority 2 — integration and decision

| ID | Goal | Owner repo | Depends on | Deliverable | Done when (measurable) | Effort (pd) | Informs |
|---|---|---|---|---|---|---|---|
| POC-19 | Baseline vs remastered in-engine comparison (local) | SSTRE-Engine + AssetCompiler | POC-08, POC-11, POC-17 | Local screenshots (not committed), perf/VRAM delta report | Same demo checkpoints captured both ways; p99 and peak VRAM delta reported; FLIP/SSIM numbers only in report | 2–4 | 3, 6 |
| POC-20 | Compatibility matrix first real entries | SSTRE (`docs/compatibility.md`) | POC-17 | Updated matrix | Only rows with linked reports leave `untested` | 0.5–1 | 2, 6 |
| POC-21 | Go/no-go recommendation | SSTRE | POC-01..25 | Decision memo + ADR updates (ADR-005, ADR-007) | Recommends engine base, asset source strategy, model choices, next sprint with re-estimated effort; owner reviewed | 2–3 | 1, 2, 3, 6, 8 |

## Phase 1 sprint status (2026-11-27)

| ID | Status | Result / evidence |
|---|---|---|
| POC-01 | **done** | RT + RTGL1 v1.1.0 build and run TFE (EXP-002) |
| POC-02 | **done (partial)** | Classic-VK Windows and Linux builds; Windows TFE/TSE runtime; Linux graphical client untested (EXP-001) |
| POC-03 | **done** | `sstre-ac detect` / `inventory`; 5/5 installs exact; 69 tests (EXP-007) |
| POC-04 | **done** | synthetic examples and negative tests for all schemas (EXP-006) |
| POC-05 | **done** | CI active in all five repos (validator, REUSE, pytest) and green on GitHub (EXP-006) |
| POC-13 | **open** | demo profiler gave no output; needs a scripted demo plus PresentMon or a dump patch |
| POC-14 | **blocked (RT)** / open (CVK) | RT `PlayDemo` x64 varargs defect (EXP-002) |
| POC-16 | **done (CVK)** / fail (RT) | CVK loads TSE levels; RT TSE has no RT build (EXP-001/002) |
| POC-22 | **done (partial)** | S1.1 pass, S1.2 fail, S1.3 Vulkan pass / OpenGL fail, override pass (EXP-002) |
| POC-23 | **partial** | Windows raster pass; Linux graphical and Steam Deck untested (EXP-001) |
| POC-24 | **done** | 30/53/96 pd (EXP-005) |
| POC-25 | **done** | HD `.tex` decode 99.9%; verifier 20/21; verified HD sources TFE 395, TSE 364 (EXP-008) |
| POC-26 (audit) | **done** | EXP-004; owner chose patch distribution (ADR-0008) |

### Proposed next sprint (requires owner approval)

| ID | Goal | Effort (pd) |
|---|---|---|
| POC-27 | Patch-series tooling; export the CVK and RT build commits as `patches/` | 2–4 |
| POC-28 | Frame-time/VRAM baseline: scripted demo, PresentMon (pinned), input-isolated session, CVK + RT | 2–4 |
| POC-29 | Time-boxed transplant spike: RT backend for TFE/Windows into Classic-VK, raster default, RT selectable | ~8 (time-box) |
| POC-30 | Integrate the libktx-free KTX2 reader in the spike build and confirm that rendering matches | 1–2 |
| POC-31 | Linux graphical run on real GPU hardware (and Steam Deck if available) | 1–3, needs hardware |
| POC-32 | Compile-time disable of the master-server heartbeat in SSTRE builds | 0.5 |
| POC-06/07 | 50-asset matrix selection (local) and `.tex` round-trip, using EXP-007/008 tooling | 3–8 |

## Rough totals (for planning only)

Sum of ranges for POC-01..21 (Agent G draft): approximately **50–114 pd**; POC-22..25 add **10–23 pd**, for a total of about **60–137 pd** (IDs are stable labels, not priority order). With 2–3 parallel contributors and the dependencies above, the critical path is roughly POC-01/02 → POC-13/14 → POC-17 → POC-19 → POC-21 for engine, and POC-03 → POC-06 → POC-07 → POC-08/09 → POC-10 → POC-11 → POC-12 for assets. Re-estimate after POC-01/02 and POC-07, the two highest-uncertainty items.

## Post-demonstration work packages (owner directive 2026-11-28)

> **Status: draft, written by track DOC-R on 2026-11-28 for lead review.** The owner directive of 2026-11-28 (binding; kept in the lead's records) sets the order **Demonstration Build → Performance Optimization → PBR & Hex-Tiling → Geometry Enhancement → Native Controller Support → Multicontroller & Split-Screen → Console Ports**. Stages and gates are in the [roadmap](roadmap.md). Packages start when their stage starts. CPU-only research, tooling and asset work may run earlier if it does not disturb benchmarks (quiet mode). Effort ranges are proposals, not commitments.

Columns: **Track** is the suggested owning track. **GPU lock** says whether the package needs `gpu-lock.ps1 run` (game window or GPU job) and whether benchmark runs need `-Quiet`. Acceptance numbers are measured on the reference PC unless stated.

**Reference PC** (lead, `nvidia-smi`/CIM, 2026-11-28; also in EXP-011): NVIDIA GeForce RTX 4070 12 GB, driver 616.64; Intel Core i5-11600K (6 cores / 12 threads); 32 GB RAM; Windows 11 Pro 22631; display 3440×1440 @ 144 Hz, 125 % scaling. At ~100 FPS the 6-core CPU may make CPU-side overhead relevant ([RD-014](research/RD-014-rt-performance.md) A3).

### Rules for all stage M1–M5 packages

1. **No silent quality reductions.** A change that alters the image beyond the quality-guard threshold (POC-45) ships only as an explicit, documented graphical setting with measured cost and benefit. Defaults change only with owner approval.
2. **Profile first.** An optimization package starts only when a profile (POC-36) attributes a measurable share of frame time to its area.
3. **Frame generation never counts.** Results are reported per render mode: **N** native, **S** spatial upscaling (FSR 1.0), **T** temporal upscaling, **FG** frame generation. FG results are reported separately and never toward the target.
4. **Diminishing-returns stop rule.** Stop stage-M1 optimization and escalate to the owner when (a) two consecutive optimization packages each gain less than max(3 % mean FPS, the measured regression threshold) on the scene set, or (b) the stage budget (proposed 25 pd, owner to confirm) is spent, while the target is still missed. The escalation memo (POC-46) lists the architectural limits found, the remaining gap per scene and mode, and realistic alternatives.
5. **Every graphical feature in M2/M3 is benchmarked alone and combined** against the optimized M1 baseline (POC-53). A feature with disproportionate cost is optimized, applied selectively or replaced before it may be on by default.
6. TFE and TSE both. Vulkan and OpenGL raster keep working (regression run in every package that touches the engine).

### Stage M1 — Ray tracing and engine performance (directive Phase 1)

Target: **≈100 FPS mean, RT on, "High" profile, upscaled texture pack, 2560×1440, RTX 4070**, frame generation excluded. Dossier: [RD-014](research/RD-014-rt-performance.md). Reuse the POC-28 harness (SSTRE-Engine `tools/benchmark/`, E3 track); no new harness.

Configurations of the four-way comparison:

| Label | Engine | Assets |
|---|---|---|
| A | original Serious-Engine-RT (`phase1/rt-build` + bench fixes). **TFE only**: the fork has no TSE RT | original |
| B | current SSTRE RT (Classic-VK + RT backend, preview2 state) | original |
| C | current SSTRE RT | upscaled pack (the preview2 asset overlay, identified by its local manifest hash) |
| D | optimized SSTRE RT (end of M1) | upscaled pack |

| ID | Goal | Track | Inputs | Depends on | GPU lock | Acceptance (measurable) | Effort (pd) |
|---|---|---|---|---|---|---|---|
| POC-33 | Benchmark harness v2: 2560×1440 (fullscreen or borderless; a decorated window does not fit the 1440-px display), render-mode tag N/S/T/FG, 1 % low, per-thread CPU, GPU-busy share, FG guard (driver FG setting and implicit Vulkan layers such as `VK_LAYER_NV_present` recorded; PresentMon `FrameType` checked), named "High" settings profile per config | PERF-BENCH | POC-28 harness, EXP-011 | preview2 committed | yes; `-Quiet` for test runs | harness emits avg FPS, 1 % low, p50/p95/p99, GPU %, CPU % (machine, process, busiest thread), VRAM peak and mean (GPU and process) per run; a run with any non-application frame or an active FG layer in N/S/T is invalid; 5 runs of one RT config give CV ≤ 3 % | 2–4 |
| POC-34 | Benchmark scene set: ≥ 3 scenes per game, ≥ 1 combat-heavy per game (many active enemies, projectiles, particles), plus the shipped demos ("Dunes", "The Elephant Atrium") and preview2 slice levels; locally recorded demos stay local | PERF-BENCH | POC-14 (demo determinism), slice levels | POC-33 | yes | each scene plays to the end 5/5 times in B and C with identical end state (position, health, score); scene list with level names and duration in the EXP report; upscaled-pack coverage of every C/D scene stated (extend the pack or choose covered scenes) | 2–4 |
| POC-35 | Baseline at 1440p: A, B, C × scenes × modes N and S (+T where a local temporal upscaler exists); raster reference (Classic-VK Vulkan + OpenGL) for regression. Supersedes the 1080p EXP-011 baselines | PERF-BENCH | POC-33, POC-34 | POC-33, POC-34 | yes, `-Quiet` | new EXP report with one table per game and mode; ≥ 5 valid runs per cell; regression threshold per cell derived from run-to-run variance (RD-008 §8.4) | 2–3 |
| POC-36 | Profiling campaign: CPU/GPU timeline and per-pass GPU cost (Nsight Systems/Graphics; RenderDoc where RT capture works) on 2 scenes per game in C | PERF-RT | POC-35 | POC-35 | yes | ≥ 90 % of mean frame time attributed to named passes or CPU phases per scene; RD-014 §6 hypotheses H1–H12 ranked by measured share; CPU- vs GPU-bound verdict per scene | 3–5 |
| POC-37 | BLAS/TLAS construction, caching and updates; static vs dynamic geometry classification (incl. movable brushes) | PERF-RT | RD-014 H1/H2 | POC-36 shows ≥ 5 % share | yes | before/after on the scene set with gain per scene; no image change beyond the guard; 0 new validation errors | 3–8 |
| POC-38 | Redundant geometry and texture uploads; texture caching, BCn compression of the upscaled pack, VRAM management | PERF-RT (+ VS-A for the pack format) | RD-014 H6/H7 | POC-36 | yes | upload bytes per frame and VRAM before/after; peak VRAM in C ≤ 10 GiB on the 12 GB card [ASM budget]; compression changes the image only within the guard, otherwise it is a texture-quality setting | 3–6 |
| POC-39 | Shader execution and ray traversal; light sampling and unnecessary rays; denoiser cost | PERF-RT | RD-014 H5/H8/H9 | POC-36 | yes | per-pass GPU time before/after; any change in ray counts, bounces or denoiser quality that changes the image is an explicit setting | 4–8 |
| POC-40 | CPU-side rendering overhead, multithreading, Vulkan synchronization and pipeline stalls, frame pacing | PERF-RT | RD-014 H3/H4/H11/H12 | POC-36 | yes | CPU frame time and GPU idle gaps before/after; p99 and 1 % low improve or stay within threshold; gameplay end state unchanged | 4–8 |
| POC-41 | Upscalers: characterize FSR 1.0 and DLSS (local only, RD-007 Q3); evaluate a source-built temporal upscaler (FSR 2+, MIT) as an explicit setting | PERF-RT | RD-005 §3.2, RD-007 §5.3 | POC-35 | yes | N/S/T table with quality-guard numbers per mode; temporal upscaler built from pinned source, or a documented blocker; no DLSS in any distributed artefact | 3–6 |
| POC-42 | RTGL1 revision study: v1.1.0 (current clean-room fork) vs `hl1` (light grid, ReSTIR): cost/benefit and port effort; desk work plus a small spike | PERF-RT | RD-005, EXP-005 | POC-36 | short spike only | sized estimate with a range; recommendation memo feeding the proposed RTGL1-baseline ADR | 2–4 |
| POC-43 | Vulkan validation clean-up: TSE 45 errors / 6 VUIDs, TFE 35 / 5 (EXP-018 R4; counts capped by the layer's message limit) | PERF-VAL | EXP-009, EXP-018 | none (may start in the M0 tail) | yes | with the duplicate-message limit disabled: 0 validation errors over 3 min on 2 TFE and 3 TSE levels, in RT and in Vulkan raster; fixes as SSTRE patches (ADR-0008) | 3–6 |
| POC-44 | Upstream RTGL1 defects: `vkCmdCopyBuffer` region overlap (TSE), the `RG_CANT_UPDATE_TRANSFORM` flood on `1_2_Palenque` if RTGL1-side, sampler and AS-build VUIDs; draft upstream issues | PERF-VAL | E5 status, EXP-018 | POC-43 | yes | each defect classified SSTRE-side or RTGL1-side with a minimal repro; fixed in the SSTRE RTGL1 fork or documented; upstream issue drafts ready for owner approval (nothing is posted without it) | 2–5 |
| POC-45 | Quality guard and settings registry: deterministic capture at demo checkpoints in RT (the Vulkan screen grab is grey today, EXP-011 issue 8, so add a read-back), perceptual metric (e.g. FLIP) and threshold; a registry of every quality/performance setting | PERF-VAL | RD-008 §8.3 | POC-33 | yes | same build twice gives a metric below the noise floor; the registry lists each setting with default, cost and image delta; CI checks the registry format (synthetic data) | 2–4 |
| POC-46 | Run D and stage report: four-way table, target verdict per mode, stop-rule evaluation, memo on architectural limits and alternatives | PERF-BENCH (+ lead) | all M1 packages | M1 packages done or stop rule hit | yes, `-Quiet` | EXP report with A/B/C/D per scene and mode; explicit pass/fail of the 100 FPS target in N and in T; memo reviewed by the lead; owner decision recorded | 1–2 |

### Stage M2 — PBR and hex-tiling (directive Phase 2)

Dossiers: [RD-005](research/RD-005-rendering.md) §6, [RD-003](research/RD-003-ai-pipeline.md), [RD-011](research/RD-011-hex-tiling.md). Extend RTGL1's existing material path before adding new infrastructure.

| ID | Goal | Track | Inputs | Depends on | GPU lock | Acceptance (measurable) | Effort (pd) |
|---|---|---|---|---|---|---|---|
| POC-47 | Material data contract: map set (albedo, normal, roughness, metallic, emissive, height), channel packing (RME/ORM), BCn per channel type, **constant-value detection** (no map when a constant represents the material within tolerance), quality profiles | PBR (AssetCompiler + Toolkit) | RD-005 §6, ADR-0009 | M1 baseline | no (CPU) | schema and synthetic fixtures in CI; on the 50-asset matrix, the share of maps replaced by constants is reported; packing round-trip error within tolerance | 3–6 |
| POC-48 | Automated material classification and per-class generation recipes; automated QA and fallback (constant, original, skip) | PBR (Toolkit) | RD-003, POC-10/11 | POC-47 | GPU jobs under the lock | deterministic reruns give equal hashes on the reference environment; every matrix item ends accepted or with a reason-coded fallback; agreement with a human audit sample reported | 5–10 |
| POC-49 | In-engine PBR integration in RTGL1 (normal, roughness, metallic, emissive; height only as an input for POC-56, because RTGL1 has no height maps) and quality profiles | PBR (engine) | POC-47, POC-48 | POC-48 | yes | each channel toggles independently on representative surfaces (RD-008 §5 phase 5 a–d); cost vs the M1 baseline via POC-53 | 4–8 |
| POC-50 | Realtime hex-tiling as a generic, default-off RTGL1 material feature (shared hit-info code, ray-cone gradients, tangent-space normal rotation) | HEX | RD-011 | POC-49 (material records) | yes | RD-011 §7 items 1–2: identical transform across maps, normal error < 1° on fixtures, no mip popping in the distance sweep, 0 new validation errors | 4–8 |
| POC-51 | AssetCompiler eligibility classification and exclusions (text, signage, directional art, decals, UI, animated/effect, alpha cut-outs, atlases), with curated overrides | HEX (AssetCompiler) | RD-011 §3.3 | POC-47 | no | 0 false positives on the hand-labelled exclusion set; ≥ 80 % recall on the hand-labelled eligible set | 2–4 |
| POC-52 | Offline-baked, hybrid and low-end hex-tiling variants (raster and Deck profiles) | HEX | RD-011 §5 | POC-50, POC-51 | GPU jobs under the lock | variants built deterministically; VRAM per variant reported | 3–6 |
| POC-53 | Feature cost matrix: every M2/M3 feature alone and combined vs the optimized M1 baseline (mean FPS, 1 % low, p99, VRAM; modes N and T) | PERF-BENCH | POC-33 harness | POC-46 | yes, `-Quiet` | table per feature and combination; features above an owner-set cost limit are flagged and not on by default | 1–2 per round |

### Stage M3 — Geometry enhancement (directive Phase 2)

Dossier: [RD-013](research/RD-013-geometry-enhancement.md). Render-only: collision, sectors, portals and gameplay use the original data.

| ID | Goal | Track | Inputs | Depends on | GPU lock | Acceptance (measurable) | Effort (pd) |
|---|---|---|---|---|---|---|---|
| POC-54 | Vertex normal smoothing for brush geometry in the RT layer (crease angle, material and sector boundaries, per-surface opt-out), as a setting | GEO | RD-013 §3 | M1 baseline | yes | RD-013 §7 item 1: identical demo end state 5/5, load-time increase < 5 %, frame time within threshold | 2–4 |
| POC-55 | Shadow terminator correction as a generic RTGL1 option | GEO | RD-013 G3/G4 | POC-54 | yes | no terminator band on fixtures at 3 light angles; 0 new validation errors; cost reported (POC-53) | 2–4 |
| POC-56 | Selective offline subdivision with constrained smoothing; optional displacement from PBR height maps (AssetCompiler, render-only meshes, local outputs) | GEO (AssetCompiler + engine) | RD-013 §5, POC-49 | POC-54, POC-55 | yes | boundary vertices bit-identical; UV error 0 at original vertices; gameplay end state identical; triangles, BLAS memory and frame time reported per scene | 5–10 |

### Stage M4 — Native controller support (directive Phase 3)

Dossier: [RD-012](research/RD-012-input-local-multiplayer.md). Single-player first. The PC version must become fully usable without keyboard and mouse.

| ID | Goal | Track | Inputs | Depends on | GPU lock | Acceptance (measurable) | Effort (pd) |
|---|---|---|---|---|---|---|---|
| POC-57 | Input-abstraction design and SDL3 spike (pinned source, input only, Windows + Linux, Classic-VK) with licence check | INPUT | RD-012 §5, §7 | M3 done (the CPU-only design may start earlier) | short game runs | RD-012 §7 item 1; design note and a proposed ADR draft | 3–5 |
| POC-58 | Gamepad backend and action maps: Xbox, DS4, DualSense, generic USB/Bluetooth; analog move/look; bindings, sensitivity, deadzones; persistence; hot-plug; automatic device switching; rumble | INPUT | POC-57 | POC-57 | short game runs | RD-012 §7 item 2 checklist passes on Windows with 3 pad families and 1 generic pad; original controls files still work | 5–10 |
| POC-59 | Full controller menu navigation and dynamic button prompts (own or permissively licensed glyphs) | INPUT | POC-58 | POC-58 | short game runs | every menu reachable and usable, from start to in-game options, with a pad only; prompts follow the last active device; glyph licence recorded | 4–8 |
| POC-60 | Steam Input and Steam Deck validation (no Steamworks SDK in the engine) | INPUT | RD-006 Tier 2, POC-31 | POC-58, POC-59; Deck hardware | on the Deck | via Steam Input on Windows the checklist passes; on the Deck one level is played start to end without keyboard; result entered in the compatibility matrix | 1–3, needs hardware |

### Stage M5 — Multicontroller and split-screen

| ID | Goal | Track | Inputs | Depends on | GPU lock | Acceptance (measurable) | Effort (pd) |
|---|---|---|---|---|---|---|---|
| POC-61 | Multiple independent controllers, per-player assignment, mixed keyboard/mouse and pads, 4-player raster split-screen regression | INPUT | RD-012 §3.1 (SE1 already has `SSC_PLAY1..4`) | POC-58 | yes | 4 pads drive 4 players; the mixed setup works; raster 4-player split-screen ≥ 60 FPS on the reference PC | 3–6 |
| POC-62 | Ray-traced split-screen feasibility (RTGL1 draws one view per frame) | PERF-RT | RD-012 U2 | POC-61, M1 | yes | report with measured cost for 2 and 4 views, or the blocker; recommendation: RT split-screen as an explicit option, or not offered | 2–4 |

### Stage M6 — Console ports (research only)

ADR-0007: consoles remain a research objective. Nothing here builds for or runs on a console.

| ID | Goal | Track | Inputs | Depends on | GPU lock | Acceptance (measurable) | Effort (pd) |
|---|---|---|---|---|---|---|---|
| POC-63 | Keep [RD-009](research/RD-009-ps5-homebrew.md) and [RD-010](research/RD-010-homebrew-distribution.md) current; portability review of the input and render interfaces for future authorized adapters; distribution checklist for engine-only packages | DOC-R | RD-006, RD-007 Q14/Q18/Q19 | none | no | dossiers reviewed at least every 6 months; no proprietary SDK, stub, exploit or firmware-derived material in any repository (leak scan and review); checklist reviewed by the lead | 0.5–1 per update |

### Proposed ADRs for the lead/owner

This track does not edit ADRs. Proposed new ADRs and amendments:

| Proposal | Content | Evidence |
|---|---|---|
| ADR-0010 Performance target and measurement policy | definition of the 100 FPS target (hardware, 1440p, "High" profile, upscaled pack); N/S/T/FG separation, FG never counts; whether T may satisfy the target; no silent quality reductions; settings registry; stop rule and budget | RD-014 |
| ADR-0011 RTGL1 baseline and fork policy | stay on the v1.1.0 clean-room fork or move to `hl1`; generic features (hex-tiling, terminator fix) as self-contained RTGL1 patches; rules for upstream contributions | RD-005, RD-011, RD-014, POC-42 |
| ADR-0012 Input abstraction | SDL3 (zlib) as the PC backend behind an engine-owned, platform-neutral interface; WinMM path replaced; compatibility layer for original controls; no Steamworks SDK in the GPL engine | RD-012 |
| ADR-0013 Material/PBR data contract (or an ADR-0009 amendment) | map set, packing, constant values, quality profiles, hex-tiling eligibility fields | RD-005 §6, RD-011 |
| ADR-0014 Render-only geometry | render meshes may differ from collision; collision, portals and sectors always use original data; all geometry enhancement optional | RD-013 |
| ADR-0007 amendment | record the stage order M0–M6; reaffirm console research only and "homebrew not pursued" pending RD-007 Q19 | RD-009, RD-010 |
