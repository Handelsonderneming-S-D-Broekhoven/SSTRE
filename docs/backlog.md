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

## Rough totals (for planning only)

Sum of ranges for POC-01..21 (Agent G draft): approximately **50–114 pd**; POC-22..25 add **10–23 pd**, for a total of about **60–137 pd** (IDs are stable labels, not priority order). With 2–3 parallel contributors and the dependencies above, the critical path is roughly POC-01/02 → POC-13/14 → POC-17 → POC-19 → POC-21 for engine, and POC-03 → POC-06 → POC-07 → POC-08/09 → POC-10 → POC-11 → POC-12 for assets. Re-estimate after POC-01/02 and POC-07, the two highest-uncertainty items.
