# RD-008 — Testing, QA gates and release strategy

| Field | Value |
|---|---|
| Dossier | RD-008 |
| Author | Agent G (QA/release researcher), Phase 0 |
| Date | 2026-11-27 |
| Status | **Draft / proposal.** Nothing in this dossier is implemented. Thresholds are placeholders to be calibrated by POC measurements. |
| Related | [RD-003 AI pipeline](./RD-003-ai-pipeline.md), [RD-004 reproducibility](./RD-004-reproducibility.md), [RD-001 engine baseline](./RD-001-engine-baseline.md), [RD-007 licensing](./RD-007-licensing.md), [backlog](../backlog.md), [compatibility](../compatibility.md) |

## 1. Question and scope

How will SSTRE know that things work, phase by phase, without proprietary game data in source control or CI? Specifically:

1. Acceptance gates per roadmap phase 0–9 (plan §8): measurable exit criteria and who/what verifies them.
2. Per-texture automated asset QA, the fallback ladder, failure reporting, and an honest definition of the "95% automated acceptance" metric.
3. Reproducibility checks (double build, equivalence, incremental invalidation) — conceptual; the mechanism and tolerances are owned by [RD-004](./RD-004-reproducibility.md).
4. Gameplay/performance regression for an SE1-based engine: demo record/playback, determinism caveats, screenshots, frame-time/VRAM capture, co-op, savegames.
5. Testing without game data: synthetic fixtures, schema and golden-file tests.
6. A release compatibility matrix template.
7. Release format, versioning, contents and signing.

Out of scope: choosing the engine (RD-001), choosing models (RD-003), legal clearance (RD-007), CI implementation (Agent F / open decision 8).

## 2. Evidence

All engine evidence is from the read-only upstream clone `<workspace>/upstream/Croteam-official_Serious-Engine` at commit `b408e88a16fd01aa1cfd0e0a999c86c2c1437c9e` (https://github.com/Croteam-official/Serious-Engine), unless noted. Line numbers refer to that commit. Code was read only; nothing was built or executed.

| # | Observation | Location |
|---|---|---|
| E1 | Demo recording is exposed as console commands `StartDemoRecording()` / `StopDemoRecording()` and counter `dem_iRecordedNumber`; auto-named output `Temp\Recorded%02d.dem`. | `Sources/Engine/Network/Network.cpp` L309–318, L732–734, L1839 |
| E2 | Demo file layout: chunk `DEMO`, chunk `MVER` + `_SE_BUILD_MINOR`, then a full `CSessionState::Write_t` snapshot, then the recorded stream, terminated by `DEND`. Playback expects `DEMO`. | `Network.cpp` L1754–1772, L1779–1795, L1321 |
| E3 | `_SE_BUILD_MINOR` is commented "minor versions that are data-compatible, but are not netgame-compatible"; value 10, `_SE_BUILD_MAJOR` 10000. Same values in Serious-Engine-RT (`0e7f223c`) and SeriousSamClassic-VK (`510d36f9`, `SamTFE/Sources/Engine/CurrentVersion.h`). | `Sources/Engine/CurrentVersion.h` L17–18 |
| E4 | Playback speed controls: `dem_tmTimer`, `dem_fSyncRate`, `dem_fRealTimeFactor`; `DEMOSYNC_REALTIME (0.0f)`, `DEMOSYNC_STOP (-1.0f)`. | `Network.cpp` L752–754; `Network.h` L48–49, L180 |
| E5 | Playback by console: `PlayDemo(CTString)` loads `demos\<name>.dem`. Auto-play attract-loop demos `Demos\Auto-*.dem`, toggle `sam_bAutoPlayDemos`. | `Sources/SeriousSam/SeriousSam.cpp` L134–140, L438, L449; `Sources/SeriousSam/LevelInfo.cpp` L244 |
| E6 | Timedemo-like profiling: `dem_bProfile`, `dem_iProfileRate` (fragment seconds, clamped 0–60), `ReportDemoProfile()`, `DumpDemoProfile()` (writes `temp\DemoProfile.lst`), per-frame times collected in `_atmFrameTimes`/`_actTriangles` during playback, report printed when demo finishes (`DemoReportAnalyzedProfile`, `CalcDemoProfile` with "no peaks" averages). | `Sources/GameMP/Game.cpp` L132–137, L174–210, L483, L561–660, L925–931, L986–987, L1296–1301, L2334–2345 |
| E7 | A per-demo `.ini` script (or `Demos\Default.ini`) is `include`d when a demo starts — a hook for setting cvars in reproducible runs. `dem_strPostExec` command string also exists. | `Game.cpp` L930, L1303–1309 |
| E8 | Frame-sequence capture: `dem_iAnimFrame>=0` writes every frame to `ScreenShots\Anim_%05d.tga`. | `Game.cpp` L273, L929, L2383–2400 |
| E9 | Generic profiling: `RecordProfile()`, `DumpProfileToConsole()`, `DumpProfileToFile()`. | `Game.cpp` L254–266, L917–920 |
| E10 | Graphics micro-benchmark `Benchmark()` → `CGfxLibrary::Benchmark` (fill-rate/triangle tests; OpenGL/D3D labelled). | `SeriousSam.cpp` L153–157, L471; `Sources/Engine/Graphics/Benchmark.cpp` L347 |
| E11 | Command-line options include `+level`, `+server`, `+connect host:port`, `+script`, `+goto`, `+game <mod>`, `+logfile`. No `+demo` option observed; demo automation therefore goes through `+script` + console commands. | `Sources/SeriousSam/CmdLine.cpp` L92–142 |
| E12 | Lockstep sync checking: `CSessionState::ChecksumForSync`, `DumpSync_t`; cvars `ser_bReportSyncOK/Bad/Late/Early`, `ser_bPauseOnSyncBad`, `ser_iKickOnSyncBad`, `ser_tmSyncCheckFrequency`, `ser_iSyncCheckBuffer`. Entity randomness is gated by `ses_bAllowRandom` ("Use RND only in entity AI!"). | `Sources/Engine/Network/SessionState.cpp` L71–100, L766–840; `Network.cpp` L768–776 |
| E13 | Savegames: `CGame::SaveGame/LoadGame` → `_pNetwork->Save_t/Load_t`; files `*.sav` (e.g. `QuickSave%06d.sav`) plus thumbnail `<name>Tbn.tex`. Save files carry `BUIV` chunk with `_SE_BUILD_MAJOR`; `CheckVersion_t` decides reinit. | `Game.cpp` L1214–1240, L1343–1366, L2553, L2622; `Network.cpp` L2249–2275 |
| E14 | `.tex` texture format is chunked (`TVER`, `TDAT`, `FRMS`, `ANIM`, `BAST`, `FXBF`/`FXB2`/`FXDT`, `DTLT`); reader and writer exist in engine. | `Sources/Engine/Graphics/Texture.cpp` L697–880 (read), L1021–1107 (write) |
| E15 | Serious-Engine-RT at `0e7f223c` retains the same `dem_*` declarations in `Sources/GameMP/Game.cpp` L132–136 (only declarations re-checked; behaviour under the RT renderer not verified). | upstream clone `sultim-t_Serious-Engine-RT` |

External tools (primary project pages; versions **not** pinned or verified in Phase 0; licenses to be confirmed by RD-007):

- PresentMon — frame-time capture via ETW on Windows: https://github.com/GameTechDev/PresentMon
- MangoHud — Vulkan/OpenGL overlay and CSV frame-time logging on Linux: https://github.com/flightlessmango/MangoHud
- RenderDoc — frame capture/debugging, Vulkan supported: https://github.com/baldurk/renderdoc (ray-tracing capture support must be verified for the RTGL1 path)
- NVIDIA Nsight Graphics / Nsight Systems (proprietary, NVIDIA only): https://developer.nvidia.com/nsight-graphics
- AMD Radeon GPU Profiler / Radeon Memory Visualizer (AMD only): https://gpuopen.com/rgp/ , https://gpuopen.com/rmv/
- Vulkan memory introspection: `VK_EXT_memory_budget` (https://registry.khronos.org/vulkan/specs/latest/man/html/VK_EXT_memory_budget.html)
- Image metrics: SSIM (Wang et al., IEEE TIP 2004); LPIPS https://github.com/richzhang/PerceptualSimilarity ; DISTS https://github.com/dingkeyan93/DISTS ; NVIDIA FLIP https://github.com/NVlabs/flip
- KTX2 validation: Khronos KTX-Software (`ktx validate`) https://github.com/KhronosGroup/KTX-Software
- Release integrity: Sigstore/cosign https://docs.sigstore.dev/ ; SLSA provenance https://slsa.dev/ ; Reproducible Builds https://reproducible-builds.org/

## 3. Observed facts (summary)

- SE1 has a native demo system that snapshots full session state and records the input/message stream, plus a timedemo-style per-frame profiler and per-frame screenshot dump (E1–E8). This is a ready-made regression harness *if* it survives in the chosen fork and renderer (E15 partially confirms for RT; untested).
- Demos are versioned only by `_SE_BUILD_MINOR`; the engine itself declares minor-version changes "not netgame-compatible" (E2, E3). Demos are replays of a lockstep simulation, so any change to entity logic, physics or floating-point behaviour can make old demos desync. There is no explicit "demo desync" detector in playback; the multiplayer sync-check CRC (E12) is the closest existing mechanism.
- Savegames are full network-session serializations guarded by `_SE_BUILD_MAJOR` (E13); compatibility with Classic saves therefore depends on not changing entity class layouts.
- No `+demo` CLI flag exists; headless automation needs `+script` plus console commands (E11). Exit-on-finish behaviour after a profiled demo is not confirmed.
- All five SSTRE repositories contain only a README (Phase 0 lead inspection); there are no tests, CI or fixtures yet.

## 4. Assumptions and unknowns

- A1 (unknown): whether demos recorded with the Steam Classic executables play back in the chosen fork. Must be measured (POC-14).
- A2 (unknown): whether the RT renderer's per-frame cost is attributable via SE1's profiler or only via external tools.
- A3 (assumption): the reference environment for byte-level reproducibility will be one specific Windows or Linux PC with pinned driver; definition is owned by RD-004.
- A4 (unknown): headless/offscreen rendering for CI is not available; all engine runtime tests are assumed local-only on a GPU machine.
- A5 (unknown): metric thresholds (SSIM/LPIPS/DISTS/FLIP, ΔE, histogram distance) have no project-specific calibration yet; any numbers below are starting points only.
- A6 (unknown): GOG edition availability for testing — only Steam installations are present locally.

## 5. Acceptance gates per roadmap phase

"Verifier" means who signs off. "Auto" = scripted check producing a machine-readable report; "Local" = run on a contributor machine with user-owned game data; "Owner" = project owner approval. No gate may be marked passed without a linked report (issue, PR or `docs/reports/…` with commit hashes). Reports for local runs must contain only aggregate numbers and hashes, never game-derived images.

| Phase | Exit criteria (measurable) | Verifier |
|---|---|---|
| 0 Bootstrap | (a) RD-001..008 present in §6 format; (b) ADR-001..007 exist with correct status; (c) all five READMEs state status/scope/licensing; (d) relative links resolve and Markdown/schema lint passes (once tooling exists); (e) backlog has IDs, owners, done-criteria; (f) no game data in any repo (`git ls-files` scan for known extensions `.gro .tex .wld .mdl .dem .sav .ogg .wav`, size >1 MB flagged). | Auto (link/lint) + Lead review + Owner approval of licensing ADR |
| 1 Engine baseline | (a) selected engine builds from a pinned commit with documented, re-run instructions (two clean builds by script); (b) launches TFE Classic data (Steam) to main menu and loads ≥3 named levels on reference PC; (c) baseline demo set (≥3 demos: indoor, outdoor, heavy-combat) recorded and played to completion ≥3 times with profiler output captured; (d) frame-time p50/p99 and peak VRAM recorded per demo with tool + driver versions; (e) TSE launch attempt documented (pass/fail + blockers). | Local + Lead review of report |
| 2 Extraction & mapping | (a) edition detector identifies each local install by top-level archive SHA-256; (b) inventory produced for 100% of texture entries in the 50-asset matrix (RD-002) with schema-valid records; (c) round-trip `.tex → intermediate → .tex` byte-identical or explicitly field-diffed for every matrix item; (d) HD→Classic mapping table: each matrix item classified matched / ambiguous / unmatched, with fallback = Classic; (e) one representative level loads with mapped assets or documented fallback. | Auto (schema, round-trip diff) + Local |
| 3 AI toolkit prototype | (a) 50 matrix textures processed end-to-end, every one ending in an accepted output or a recorded fallback; (b) double build on reference env: hash equality rate reported per stage (target set by RD-004; failures explained); (c) provenance record complete for 100% of outputs (fields of plan §4); (d) cache: unchanged rerun performs 0 recomputations; single-recipe change recomputes only the affected set (§7.3); (e) QA metrics computed and a human audit of all 50 done, producing the first calibration of thresholds. | Auto + human audit (2 reviewers) |
| 4 First full texture build | (a) 100% of in-scope textures (denominator §6.5) have an output or explicit fallback; (b) build completes with individual failures isolated (fault-injection test: N forced failures → build finishes, N reported); (c) resume after kill mid-build produces same output hashes as uninterrupted build (reference env); (d) all "prominent/problem" list items human-reviewed; (e) automated acceptance rate reported with confidence interval from audit sample. | Auto + human audit sample |
| 5 PBR integration | (a) material test map(s) or representative surfaces render with each map channel toggled independently (debug views captured locally); (b) normal-map handedness and color-space checks pass on synthetic fixtures; (c) no regression >X% (calibrated) in baseline demo p99 frame time vs Phase 1 on reference PC; (d) documented statement that generated roughness/normal are inferred, not measured. | Auto (fixtures) + Local + Lead |
| 6 Rendering & TSE | (a) both campaigns: every level loads and the baseline demo set (extended to TSE) completes on each approved backend; (b) RT and raster paths each either implemented or formally deferred by ADR; (c) visual-diff report per backend on demo checkpoints (local only); (d) savegame compatibility result recorded (§8.6). | Local + ADR owner |
| 7 PC alpha | (a) full campaign playthrough of TFE and TSE by ≥2 testers, per-level checklist (start, secrets reachable, end trigger, no softlock); (b) co-op session ≥2 clients over LAN for ≥1 hour, zero sync-bad reports (E12) at default check frequency; (c) performance/memory profile per compatibility-matrix row marked "verified"; (d) user-side builder run from clean machine on Windows and Linux producing a working install; (e) issue templates live. | Testers + Auto logs + Lead |
| 8 Console feasibility | Per platform: authorized toolchain access documented, runtime boots a test scene, distribution path confirmed in writing. A platform lacking any item does not progress. Never blocks PC release. | Owner |
| 9 Public stable | (a) umbrella release-pin manifest references exact commits/tags of all repos; (b) builder reproduces reference-env asset hashes for the release profile (where demonstrated); (c) compatibility matrix updated only with tested entries; (d) notices/THIRD_PARTY complete per RD-007; (e) checksums + signatures published; (f) install instructions validated by someone not on the core team. | Auto + external tester + Owner |

## 6. Asset QA gates

### 6.1 Per-texture automatic checks

Each check emits `pass | warn | fail | n/a` plus measured values into the per-asset QA record (to become a schema under `SSTRE/schemas/`). Checks are ordered cheapest first; a hard fail short-circuits to the fallback ladder.

| Check | Rule | Hard/soft | Notes |
|---|---|---|---|
| Decode/format | Output decodes; channel count and bit depth match target profile | Hard | |
| Dimensions | Output = source × integer scale factor from recipe; power-of-two if source was POT or target format requires it; ≤ profile max size | Hard | SE1 textures are typically POT; confirm from inventory (RD-002). |
| Aspect | Aspect ratio identical to source | Hard | |
| Alpha presence | If source has alpha, output has alpha; if source has no alpha, output alpha absent or fully opaque | Hard | |
| Alpha fidelity | Binary/1-bit masks: downsampled output alpha mask vs source mask IoU ≥ τ_iou; soft alpha: mean abs error at source resolution ≤ τ_a | Hard (binary), soft (graded) | Diffusion must never touch alpha directly (plan §4.5). |
| Seam continuity (tileable only) | Compare pixel strips across wrap boundary vs strips at interior offsets; ratio of boundary gradient energy to interior gradient energy ≤ τ_seam; also check tiled 2×2 render for visible seams with FLIP | Hard | Tileability flag comes from inventory/recipe; auto-detection itself is a heuristic. |
| Structural fidelity | Downsample output to source resolution; SSIM ≥ τ_ssim; LPIPS/DISTS ≤ τ_p | Soft (signals) | Signals only (plan §4.6). Thresholds calibrated per material class. |
| Color drift | Mean ΔE2000 (in linear→Lab, after downsample) ≤ τ_ΔE; per-channel histogram distance (e.g., Earth Mover's or Bhattacharyya) ≤ τ_h; mean luminance shift ≤ τ_L | Soft | Prevents palette/art-direction drift. Color space must be known (RD-003/RD-005). |
| Range/clipping | Fraction of clipped (0/255) pixels not exceeding source fraction + ε | Soft | |
| Text/HUD exclusion | Assets tagged `ui`, `hud`, `font`, `text`, `technical-mask`, `normal`, `lightmap` must have recipe without diffusion; checker fails if provenance shows a diffusion stage | Hard | Tagging from inventory/paths + optional dev-time VLM; release builds never call a VLM. |
| Normal map validity | If normal: vectors near unit length after decode; Z ≥ 0 (tangent space); handedness consistent with profile | Hard | |
| Animated textures | Frame count and frame order preserved; per-frame checks; inter-frame temporal consistency (frame-to-frame LPIPS vs source deltas) | Hard (count) / soft | `.tex` `ANIM`/`FRMS` chunks (E14). |
| Provenance completeness | All required fields of plan §4 present; hashes match files | Hard | |

All τ values start as **uncalibrated placeholders**. Calibration procedure: run Phase 3 matrix, have 2 reviewers label each output accept/reject blind to metrics, choose per-class thresholds that maximize agreement while keeping false-accept rate ≤ target, publish the ROC data (aggregate numbers only).

### 6.2 Fallback ladder

```
L3  SR + controlled diffusion (recipe-permitted classes only)
 │ fail hard check / soft-score below floor / timeout / OOM
L2  SR only (deterministic model or classical upscaler per recipe)
 │ fail
L1  Conservative resample (e.g., Lanczos) of Classic or matched HD source
 │ fail
L0  Original Classic asset, unmodified (always available, always valid)
```

- Each asset records `ladder_start`, `ladder_final`, and the reason codes for each step down.
- Ladder descent is automatic; a curated override can pin any level (plan §4 precedence).
- A curated override must not *raise* above a level that failed a hard check without the checker passing.
- Timeouts and OOM are per-asset; a single failure never aborts the build (Phase 4 gate b).

### 6.3 Failure reporting

- Machine-readable `qa-report.json` per build (schema TBD): per asset ID — source hash, recipe hash, checks with values, ladder path, reason codes, duration, GPU memory peak.
- Human summary: counts per class × ladder level, top-N worst signals, list of hard fails. Contains no images.
- Local-only review gallery (HTML) may embed images and must be written to the user's workspace, never committed; repos' `.gitignore` must exclude it.
- Exit codes: 0 = build complete (fallbacks allowed); 1 = build complete but acceptance below configured floor; 2 = infrastructure failure.

### 6.4 Reason codes (initial set)

`DECODE`, `DIMS`, `ALPHA_MISSING`, `ALPHA_DRIFT`, `SEAM`, `STRUCT_LOW`, `COLOR_DRIFT`, `CLIP`, `DIFFUSION_FORBIDDEN`, `NORMAL_INVALID`, `ANIM_MISMATCH`, `PROVENANCE`, `TIMEOUT`, `OOM`, `OVERRIDE_PINNED`.

### 6.5 The 95% automated acceptance metric — honest measurement

Definition proposal:

- **Denominator** = number of unique texture asset IDs in the selected build profile (game × edition × target profile) **after** deduplication by stable asset ID, **excluding** only assets whose frozen recipe is `passthrough` by policy class (UI fonts, technical masks, lightmaps) — these are reported separately as a count, never silently dropped. Animated textures count once per asset, not per frame. Report the denominator explicitly with every result.
- **Automated acceptance** = asset ended at its recipe's intended ladder level (L3 or L2 as specified), passed all hard checks, had no curated override, and was not rejected in human audit.
- Report three numbers, never just one: (1) *automated-pass rate* (checker-only), (2) *audited acceptance rate* = automated-pass rate × (1 − estimated audit rejection rate), (3) *fallback distribution* (L3/L2/L1/L0 counts).
- **Human audit sampling**: stratified random sample over material class × ladder level, seeded and recorded, minimum n = 200 or the full set if smaller, plus 100% of the "prominent assets" list (which are reported separately because they are not random). Two independent reviewers; disagreements adjudicated by a third. Report Wilson 95% confidence interval for the rejection rate. With n=200 and true rejection 5%, the CI is roughly ±3 points, so "≥95%" can only be claimed if the lower CI bound is met — state this explicitly.
- Reviewers see source and candidate side-by-side at native scale and in-engine where feasible; they are blind to checker outcome.
- Gaming the metric (widening passthrough classes, loosening thresholds after the fact) must be visible: denominator definition and thresholds are versioned in the manifest and diffed in release notes.

## 7. Reproducibility checks

Mechanism, reference environment and tolerances belong to [RD-004](./RD-004-reproducibility.md); this section defines the tests that consume them.

1. **Double build (reference env).** Clean cache, build profile P twice from identical pinned inputs in separate workspaces; compare per-stage output hashes (decoded pixel hash *and* file hash, since container metadata such as timestamps can differ). Pass = 100% hash match for stages RD-004 declares deterministic; any mismatch produces a per-asset diff report (max abs diff, SSIM, FLIP). Byte-level claims only after this passes on ≥2 consecutive days/reboots.
2. **Equivalence (other envs).** Same build on a non-reference GPU/driver: per-asset perceptual and numerical thresholds (from RD-004) on decoded pixels; report distribution, not just pass/fail. Never promise identical bytes.
3. **Incremental invalidation.** Scripted mutations on a synthetic or local workspace, asserting exactly the expected recomputation set:
   - no change → 0 recomputed, outputs identical;
   - change one per-asset recipe → only that asset (and its dependents, e.g. derived PBR maps, mip chains, packages containing it) recomputed;
   - change a material profile → only assets resolving to that profile (respecting override precedence);
   - change a global default shadowed everywhere by overrides → 0 recomputed;
   - change model hash / workflow revision → all assets using it;
   - change only non-semantic manifest formatting (key order, whitespace) → 0 recomputed (proves canonical serialization);
   - corrupt a cache entry → detected by hash, recomputed, reported.
4. **Resume.** Kill the build at random points (seeded); resumed output hashes must equal an uninterrupted build.
5. **Provenance audit.** For a random 5% of outputs, re-derive the cache key from the recorded provenance and confirm it matches.

Tests 3–5 are runnable in CI on synthetic fixtures with CPU-only deterministic stages (stub "models" such as nearest/Lanczos), which validates the cache logic without GPU or game data.

## 8. Gameplay and performance regression

### 8.1 Demo-based harness

- Use the native demo system (E1–E8). Workflow: `+level <world> +script <run.ini>` or console `PlayDemo("<name>")` with `dem_bProfile=1`, `dem_iProfileRate=<n>` and a per-demo `.ini` (E7) that sets fixed resolution, vsync off, frame cap off, fixed renderer settings; collect `DumpDemoProfile()` output (E6).
- Demo files recorded by contributors from their own game are gameplay recordings that reference proprietary levels; treat them as **local-only test data**, not committed to public repos unless RD-007 clears it. Store their SHA-256 and metadata (level name, duration, build) in a committed index.
- Baseline set per campaign: ≥1 indoor, ≥1 large outdoor, ≥1 heavy-combat (many entities, particles), ≥1 transparency/alpha-heavy scene, ≥1 level start (load time).

### 8.2 Deterministic simulation caveats

- Demos replay a lockstep simulation (E2, E12). Any change to entity code, physics, timing, compiler flags affecting floating point (x87 vs SSE, `/fp:fast`), or 32→64-bit ports can cause divergence. Rendering-only changes should not affect simulation, but this is an assumption to verify per fork.
- Upstream marks `_SE_BUILD_MINOR` as netgame-incompatible; SSTRE should bump it deliberately when simulation changes and keep a "demo compatibility" note per release.
- Detection: (a) final player position/health/score and level-end time recorded at demo end and compared against baseline; (b) optional: invoke `ChecksumForSync` (E12) at fixed ticks during playback through a debug cvar (requires engine change — future work); (c) per-frame screenshot sequence (E8) compared at checkpoints.
- If Classic-recorded demos do not play in the fork, record new baseline demos *with the fork at its pinned baseline commit* and treat that as the reference.

### 8.3 Screenshot comparison (local only)

- Capture via `dem_iAnimFrame` (E8) at fixed checkpoint frames, or `bSaveScreenShot` triggers. Compare with FLIP and SSIM against the baseline capture from the same machine/backend.
- Raster backends: expect near-identical results run-to-run; RT backends with stochastic sampling/denoising/temporal accumulation will differ every run — compare with looser thresholds, after accumulation settles, or with a fixed-seed/debug mode if the RT library offers one (to verify in RD-005).
- Results stored as numbers; images stay in the user's workspace and are never committed (plan §8 POC backlog).

### 8.4 Frame-time and VRAM capture

| Need | Windows | Linux | Notes |
|---|---|---|---|
| Frame times (present-to-present, CPU/GPU busy) | PresentMon | MangoHud (`MANGOHUD_CONFIG` CSV logging) | Plus SE1 internal profiler (E6) for engine-side view. |
| Per-pass GPU timing / RT cost | Nsight Graphics/Systems (NVIDIA), RGP (AMD), RenderDoc | RenderDoc, Nsight (NVIDIA), RGP (AMD) | Vendor tools are proprietary; optional, never required by tests. |
| VRAM | `VK_EXT_memory_budget` logged by engine (future engine change), RMV (AMD), Nsight, Task Manager GPU memory as coarse check | `VK_EXT_memory_budget`, MangoHud VRAM | Prefer in-engine logging for vendor-neutral numbers. |
| System RAM | Process peak working set | `/proc/<pid>/status` VmHWM | |

Metrics per demo run: average FPS, p50/p95/p99 frame time, 1% low, max frame time spike, peak VRAM, peak RAM, level load time. Runs: discard first run (shader cache warm-up — but separately measure cold-start shader compilation stutter, especially for Vulkan/RT), then ≥3 measured runs, report median and spread. Record GPU, driver, OS build, resolution, backend, engine commit, manifest/asset build hash. A regression is flagged when median p99 worsens beyond a threshold calibrated from observed run-to-run noise (e.g., > 3× MAD) — not a fixed guess.

### 8.5 Co-op / multiplayer regression

- SE1 supports LAN/Internet co-op via `+server`/`+connect` (E11). Test: host + ≥1 client on the same build over LAN (or two instances on one machine if supported), play scripted session; collect `ser_bReportSyncBad`/`Late`/`Early` logs (E12). Gate: zero sync-bad over the session.
- Cross-version play: clients with different `_SE_BUILD_MINOR` are expected to be incompatible by design (E3); test that the mismatch is reported cleanly rather than silently desyncing.
- Split-screen (`SSC_*` configurations in `Game.cpp`) is a secondary target.
- Mixed backend (RT host, raster client) — should be simulation-neutral; verify.

### 8.6 Savegame compatibility with Classic

- Saves are session serializations (E13); compatibility requires unchanged entity class layout and `_SE_BUILD_MAJOR` handling. Test matrix: Classic save → SSTRE load; SSTRE save → SSTRE load after engine update; SSTRE save → Classic (not required, record result).
- Saves are user data from proprietary game sessions: local only. Committed tests use only saves generated from synthetic test worlds if those ever exist (future).
- Policy proposal: SSTRE guarantees nothing about Classic save compatibility until measured; the compatibility page states the measured result per release.

## 9. Testing without game data

| Layer | What | Runs in CI? |
|---|---|---|
| Schema tests | JSON Schema validation of inventory, recipe, lock manifest, provenance, QA report, release-pin files; positive and negative examples (hand-written, no game data) | Yes |
| Canonicalization tests | Manifest serializer output is byte-stable under key reordering/whitespace; cache-key derivation golden values | Yes |
| Recipe resolution tests | Precedence override > per-asset > profile > global, on synthetic manifests | Yes |
| QA checker unit tests | Synthetic images: checkerboards, gradients, noise, seamless Perlin/tiling patterns (pass) and deliberately broken seams, shifted hues, dropped alpha, wrong dimensions (fail). Generated procedurally from a seed at test time; golden outputs = expected verdicts and metric ranges | Yes (CPU) |
| Pipeline golden files | End-to-end run on synthetic textures with deterministic CPU stand-in stages; golden = output hashes + QA report | Yes |
| Cache/invalidation tests | §7.3 mutations on synthetic workspaces | Yes |
| `.tex` reader/writer fixtures | **Future work.** A synthetic `.tex` writer in AssetCompiler, implemented from a written format specification (RD-002), producing procedurally generated fixtures covering chunk variants (E14: `TVER`, `TDAT`, `FRMS`, `ANIM`, `BAST`, effect chunks). Clean-room status and license of a spec derived from GPL-2.0 engine source (`Texture.cpp`) must be resolved by RD-007 before writing it in a GPL-3.0 repo. Validation against real files happens locally only, recording pass/fail and hashes. | Yes, once it exists |
| Local data tests | Same suites with a `--game-root` option, skipped in CI, producing aggregate reports | No (local) |
| Engine runtime tests | Demo/perf/screenshot harness (§8) | No (local GPU) |

CI policy (consistent with plan §9.6): only checks that exist; pin actions by SHA; least-privilege tokens; no GPU, no game data, no model weights downloaded by default.

## 10. Release compatibility matrix

Template and status vocabulary live in [`../compatibility.md`](../compatibility.md). Status vocabulary: `untested`, `known-broken`, `works-with-issues`, `verified`; an entry may only leave `untested` with a linked test report naming tester, date, all pinned versions and hardware.

## 11. Release format and versioning

### 11.1 Alternatives

| Option | Pros | Cons |
|---|---|---|
| SemVer per repo + umbrella release-pin manifest | Each repo communicates its own API/format breaks (schema changes, CLI changes); umbrella gives one user-facing version | More bookkeeping; SemVer on data repos (Manifests) needs a definition of "breaking" |
| Calendar versioning everywhere | Simple; fits a content project | Hides breaking changes in schemas/CLI |
| Single monotonic umbrella version only | Simplest for users | Sub-repo consumers (Toolkit as generic library) lose meaning |

### 11.2 Recommendation (proposed)

- **Remaster-Toolkit, SSTRE-AssetCompiler**: SemVer (`0.y.z` until interfaces stabilize); MAJOR bump on CLI/schema/cache-key-breaking changes. Cache-key or output-affecting changes must be called out because they invalidate user caches.
- **SSTRE-Manifests**: SemVer where MAJOR = schema-breaking, MINOR = new/changed recipes (changes outputs), PATCH = metadata/doc only (must not change any output hash — testable).
- **SSTRE-Engine**: keep upstream version macros untouched unless simulation changes; tag `sstre-engine-vX.Y.Z` SemVer for SSTRE changes; record upstream base commit in release notes.
- **SSTRE umbrella**: user-facing version (SemVer or `YYYY.MM` — owner decision; open decision 8). Each release ships `release-pins.json` (schema in `SSTRE/schemas/`, future) listing: repo, tag, full commit SHA, schema versions, toolchain versions, model/workflow identifiers + hashes, reference environment ID, expected output-hash manifest per build profile (only where reproducibility is demonstrated).

### 11.3 Contents of a user-side builder release (no game assets)

Includes: engine binaries (built from pinned source, with license texts and source offer/links per GPL obligations — RD-007), builder/AssetCompiler + Toolkit (or install instructions), Manifests at pinned version, `release-pins.json`, model download manifest (URLs + SHA-256 + license; weights fetched by the user only if their license permits and verified before use), THIRD_PARTY notices, compatibility page snapshot, checksums and signatures.

Excludes: any original or extracted game file, any generated derivative asset, demos/saves/screenshots from game data, proprietary SDKs, model weights unless RD-007 explicitly clears redistribution.

### 11.4 Integrity

- `SHA256SUMS` for every release file; signed (Sigstore/cosign keyless via CI identity, or GPG — decide in Phase 9); GitHub artifact attestations / SLSA provenance for binaries built in CI.
- Builder verifies its own inputs (pins, model files) against hashes before running, and refuses mutable aliases (plan §4).
- Engine binary reproducibility (reproducible compilation) is desirable but not a Phase 9 requirement unless demonstrated.

## 12. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Demos desync in fork / after any gameplay change | Loss of the cheapest regression harness | Measure early (POC-14); re-record baselines per pinned engine; end-state comparison; document `_SE_BUILD_MINOR` policy |
| RT nondeterminism makes screenshot diffs noisy | False positives/negatives | Separate thresholds per backend; settle accumulation; rely on frame-time/VRAM and end-state checks |
| Metric thresholds over-fit or are loosened to hit 95% | Misleading quality claims | Versioned thresholds, blind human audit with CI, three-number reporting |
| Test data (demos, saves, screenshots) leaks into public repos | Legal exposure | `.gitignore`, pre-commit scan by extension/size, local-only report generators |
| No headless GPU CI | Runtime regressions caught late | Local reporting protocol with standard report format; optional self-hosted runner decision later (open decision 8) |
| Clean-room `.tex` spec contested | Fixture writer blocked | RD-007 sign-off first; fixtures for intermediate formats (PNG/KTX2) meanwhile |
| Vendor profiling tools licenses | Cannot be required in tests | Use them only as optional diagnostics |

## 13. Proposed experiments and measurable success criteria

| Exp | Description | Success criterion |
|---|---|---|
| X1 (POC-14) | Play a demo recorded with fork baseline 5× on reference PC; compare end-state and profiler output | End-state identical 5/5; profiler output parsed; p99 spread reported |
| X2 (POC-14) | Play Steam Classic-recorded demo in fork | Recorded pass/fail with reason; no expectation |
| X3 (POC-10) | Calibrate QA thresholds on 50-asset matrix with 2 blind reviewers | Per-class thresholds chosen; Cohen's κ between reviewers reported; checker-vs-human agreement ≥ target set before the experiment |
| X4 (POC-08/09) | Double build + §7.3 mutations | Matches RD-004 targets; invalidation sets exact for all 7 mutations |
| X5 (POC-13) | Perf capture repeatability: 5 runs same demo | Run-to-run p99 coefficient of variation measured → regression threshold derived |
| X6 (POC-15) | Classic save → fork load | Result recorded per edition |

## 14. Recommendation

1. Adopt the phase gates in §5 as the roadmap's verifiable exit criteria (lead to merge into `docs/roadmap.md`).
2. Build the QA checker and cache/invalidation tests **first on synthetic data in CI**; treat metric thresholds as calibrated artifacts, versioned in Manifests.
3. Use SE1's native demo + `dem_bProfile` system as the primary gameplay/perf harness, augmented by PresentMon (Windows) and MangoHud (Linux); validate its survival in the chosen fork early.
4. Report automated acceptance as three numbers with explicit denominator and audit CI; never quote "95%" without them.
5. Per-repo SemVer + umbrella `release-pins.json`; signed SHA-256 checksums; no game-derived content in any release or repo.

## 15. Decision dependencies

- Open decision 1 (engine): demo/profiler availability per fork; renderer determinism.
- Open decision 2 (editions/hashes): compatibility matrix rows; edition detector.
- Open decision 3 (AI models): which classes may reach L3; metric calibration.
- Open decision 4 (determinism): §7 thresholds — RD-004.
- Open decision 5 (PBR/metadata representation): normal/alpha/animation checks.
- Open decision 6 (backends/packaging): matrix columns, KTX2/DDS validators.
- Open decision 7 (console): Phase 8 gate only.
- Open decision 8 (CI/release format): CI matrix, self-hosted runner, umbrella version scheme, signing method.

## 16. Next steps

1. Lead reconciles [backlog](../backlog.md) with RD-001..007.
2. Agent F / lead: add schema-validation CI and `.gitignore` patterns for game data, demos, saves, screenshots, review galleries.
3. Define JSON Schemas for `qa-report`, `release-pins`, provenance (coordinate with RD-002/RD-004).
4. Run POC-14 as soon as an engine candidate builds (depends on POC-01/02).
5. Owner: choose umbrella version scheme and signing method before first tagged prerelease.
