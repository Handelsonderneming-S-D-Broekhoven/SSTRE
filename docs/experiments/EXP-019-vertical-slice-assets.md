# EXP-019: Vertical-slice asset integration (slice v0): engine settings, Vulkan pool budget, level scope, overlay packaging

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | Sprint 2 track VS-A (vertical slice, assets); ADR-0009 consequences 1–3; EXP-016 follow-ups ("platform profile that sets the texture cvars", "AssetCompiler support for `TEX_32BIT`", Vulkan pool) |
| Status | STATUS-LINE |
| Environment | Windows 11 Pro 10.0.22631, Intel Core i5-11600K, NVIDIA RTX 4070 12 GB, driver 616.64 (Vulkan 1.4.351). Python 3.10.11 venv `G:\sstre-tmp\assets\venv` (numpy 2.2.6, Pillow 12.3.0, jsonschema 4.26.0, pytest 9.2.0, reuse 5.0.2). Compressonator CLI 4.6.0 (as in EXP-002/EXP-013). KTX-Software `ktx` 4.4.2 as a black-box validator only (EXP-014) |
| Inputs | Selection records and texture set 1 of EXP-012; the local HD image plugin output (EXP-012); AI1 layer-6 packs (AI-PACKS-LINE); the owner's Steam Classic TFE and TSE installs (read-only). Test runtimes: data copied from E1's TFE runtime (EXP-009) and E4's TSE runtime (EXP-016); binaries copied from track VS-E's integrated build (SSTRE-Engine local `sprint2/integration`: Classic-VK + RT transplant (TFE) + `FilterBitmap` fix + upload log + master-server switch). No asset paths, hashes or images are published here (GATE-05) |
| Code | SSTRE-AssetCompiler `feature/slice-packaging` (local, not pushed); umbrella `sprint2/exp-019` (two schema changes + this report) |

## Goal and success criteria

1. AssetCompiler:
   - `TEX_32BIT` on replacements by default;
   - platform profiles with an engine-settings section that the packager emits as an SSTRE settings script, with the original `GLSettings` scripts untouched;
   - the Vulkan texture pool as a planner constraint;
   - a deterministic `package` command: plan plus inputs → runtime overlay with a provenance manifest.
2. Owner scope (updated during the sprint): the first build covers the first campaign level of TFE (`01_Hatshepsut`) and of TSE (`1_0_InTheLastEpisode` and `1_1_Palenque`) completely.
   - One overlay per game.
   - Plan restricted to the textures of those levels.
   - HD Quality and HD Material Maps where the selection records pick them; HD Artwork and HD Interface off.
   - AI profile `conservative`; platform profile `pc-default`.
3. Rebuild twice and show the outputs are byte-identical; install into private runtime copies. Verify in the engine that the settings script is active, uploads are full size, and textures load without errors. Capture paired Classic vs slice screenshots (local only) when the GPU queue allows.
4. Record the effective configuration and per-asset provenance (local); report aggregates here.

## Design (what was built)

### `TEX_32BIT` (flag bit 1)

- `make_replacement()` and `sstre-ac tex-replace` set flag bit 1 on every replacement by default.
- `--no-32bit` (`force_32bit=False`) keeps the original flags exactly.
- `tex-encode` keeps the sidecar flags, so originals still re-encode byte-identically, unless `--32bit` is given.
- The flag's meaning comes from EXP-016 [DOC: EXP-016 §5]. No engine source was read for this experiment, so the AssetCompiler stays clean-room.

### Engine settings in platform profiles

Platform profiles gain an optional `engineSettings` section: an ordered list of console variables and the script path (default `Scripts/SSTRE/TextureProfile.ini`). The script is written with CRLF line ends, is deterministic, and ends with an `Echo` line so its execution is visible in the log.

| Profile | Console variables | Planner consequence |
|---|---|---|
| `pc-default` | `sam_iVideoSetup=3`, `tex_iNormalSize=11`, `tex_iNormalQuality=22` (EXP-016 recommendation) | `maxPixels` 4 194 304 (2048² upload area); was 8 388 608 |
| `pc-low-memory` | `sam_iVideoSetup=3`, `tex_iNormalSize=10`, `tex_iNormalQuality=22` | `maxPixels` 1 048 576 (1024²); was 4 194 304 |
| `legacy-constrained` | none (hypothetical profile) | unchanged |

**Mechanism.**
- The shipped `Scripts/Game_startup.ini` describes itself as "executed each time SeriousSam is started" [DOC: comment in the shipped file]. Using it would mean writing a shipped file, so it was not used.
- A profile cannot name a `Scripts/GLSettings/` path; both the AssetCompiler and the schema check this.
- [EXP] A lone `+script Scripts\SSTRE\TextureProfile.ini` executes the script, and so does `include "Scripts\SSTRE\TextureProfile.ini";` inside another `+script` file. Both log `SSTRE: engine settings pc-default applied.`
- [EXP] With two `+script` arguments, only the last one runs: the log shows the full command line but executes only the second file.
- Recommended activation: the lone `+script`, or `include` from a launcher or harness script. The generated script's header and `INSTALL.txt` say so.

**Consistency rule.** `tex_iNormalSize` = N caps every upload at 4^N pixels (EXP-016 §5). The profile's `maxPixels` must therefore not exceed 4^N; otherwise the plan would ship pixels that the runtime discards at load time. The AssetCompiler rejects such a profile.

**Caveat.** The variables are persistent. After one clean exit they stay in the runtime's `PersistentSymbols.ini`. `INSTALL.txt` describes how to return to the shipped settings.

### Vulkan texture pool as a planner constraint

- Profiles gain `additionalBudgets`. Both PC profiles record `vulkan-texture-pool`:
  - 536 870 912 bytes (256·256·4·4/3 × 512 × 3; EXP-016 [SRC, by E4]);
  - every format counted as RGBA8, mips included;
  - `scope: per-game`, because one runtime loads one game;
  - policy `reduce-largest`.
- Pending (not yet produced) AI targets are reduced before sizes that exist.
- Two planner defects appeared as soon as the pool applied to a real plan; see Deviations.

### Per-level asset scope

- [EXP, black-box observation of the owner's world files] A `.wld` contains `DICT` chunks: `DICT`, int32 count, then count × (`DFNM`, int32 length, name), then `DEND`. This is the same `DFNM` record as in `.tex` files.
  - The level-1 world files have two such chunks: brush textures, then entity resources (textures, models, classes, sounds).
- `sstre-ac level-scope` collects the `.tex` names of every complete chunk that exist in the install's archives. For each texture it records:
  - header facts: size, firstMip, alpha mode, frames, file hash;
  - a path-based fallback category, used only for assets without a selection record.
- `plan --scope` plans exactly the union of the given scopes. Several levels of one game are deduplicated by asset ID. The scope is recorded in `effectiveConfig.assetScope` (new optional schema field).
- [ASM] The scope is a lower bound. Textures that entity classes load by name from code, and textures that models name internally, are not in the world dictionary.

### `sstre-ac package`

**Inputs and checks.**
- Inputs: a plan, `--classic-root EDITION=ROOT`, `--hd-images`, `--pack-dir` and an optional `--bc-encoder`.
- The packager re-checks the `planHash`, the Classic file hash of every packaged asset, the AI and override output hashes, and the HD source hashes against the plan. It refuses on any mismatch.
- Assets of other games are ignored and counted.

**Output** (relative to the game root):
- **Raster:** a loose v4 `.tex` with the Classic mex and `TEX_32BIT`, at the planned size fitted to Classic × 2^k with k ≤ firstMip.
- **RT:** `OverridenTextures/Compressed/<path>{,_n,_rme}.ktx2`, the layout from EXP-002/EXP-009.
  - `_n` holds X/Y/Z in R/G/B. The two-channel layout of the HD normal maps (X in alpha, Y in green, R = B) is detected and expanded.
  - `_rme` holds R = 1 − gloss, G = metallic 0, B = emission 0 [ASM: conversion choice].
  - Maps are never upscaled beyond their real size.
- **Engine settings:** the settings script.
- **Provenance:** `SSTRE/package-manifest.json` with plan and profile hashes, the options, the encoder identity, per-asset inputs with hashes, every output with its processing steps, the file list with SHA-256, and a `packageHash`.

**What is written.**
- Only assets whose albedo is not the Classic original, or that gain material maps. Classic assets stay in the archives.
- Assets with a Classic albedo and HD maps also get an RT albedo `.ktx2` made from the Classic image [ASM: whether RTGL1 needs it for the maps was not tested].

**Encoding.**
- BCn through Compressonator 4.6.0 (`-fd BC7|BC5|BC4 -miplevels 20`); the result is checked for vkFormat and size.
- Without an encoder, a clean-room KTX 2.0 writer (written from the Khronos specification) produces RGBA8 with a box-filtered mip chain. Its synthetic outputs pass `ktx validate` 4.4.2.
- Not packaged: multi-frame and effect textures. AO and height maps have no RT slot.

## Procedure (exact, reproducible; all local under `G:\sstre-tmp\vsa\`)

1. **Worktrees.**
   - `git -C …\SSTRE-AssetCompiler worktree add G:\sstre-tmp\vsa\wt-ac -b feature/slice-packaging origin/main`;
   - umbrella `G:\sstre-tmp\vsa\wt-umbrella` on `sprint2/exp-019` from `origin/main`.
2. **Tests.**
   - `python -m pytest -p no:cacheprovider`, with and without `SSTRE_SCHEMAS_DIR=<wt-umbrella>/schemas`;
   - `scripts/validate_repo.py --root .` in both repositories;
   - `reuse lint` in both.
3. **Configurations** `cfg\slice-v0-{tfe,tse}.json`:
   - `layers` at their defaults: Classic Base, HD Quality and HD Material Maps on; HD Artwork and HD Interface off;
   - `ai-enhancement.qualityProfile = conservative` with the AI packs;
   - `platformProfile = pc-default`.
4. **Pipeline** `scripts\build-slice.sh`, started only after `gpu-lock.ps1 wait-quiet` returned 0. For each game:
   - `sstre-ac level-scope <install> --edition classic_tfe|classic_tse --level <world file>…`;
   - `plan --config … --selection <records> --assets <set 1 READY.json> --scope scope\<game>.json`, run twice, then `cmp`;
   - `package --plan … --classic-root … --hd-images … --pack-dir … --bc-encoder compressonatorcli --out slice-v0\<game>`, run twice into `slice-v0` and `slice-v0-rerun`, then `diff -r`;
   - `ktx validate` on every `.ktx2`, then `SHA256SUMS`.
5. **Runtimes** `scripts\make-runtimes.sh`, after `wait-quiet`:
   - `runtime-classic` and `runtime-slice` (TFE), `runtime-tse-classic` and `runtime-tse-slice`;
   - each copies the source runtime's data with `Bin\` replaced by VS-E's build. TFE also gets the clean-room `RayTracedGL1.dll`; the integrated TSE build has no RT layer;
   - the overlay goes into the `*-slice` copies only. The source runtimes were not modified.
6. **Upload probe** `scripts\make_probe.py <game>`:
   - our own synthetic 4096² pattern, written with `make_replacement` over the header of one level texture that is not in the overlay and whose firstMip allows 4096 px;
   - it is placed temporarily as a loose file during a run;
   - the VS-E build logs every texture wider than 2048 px with its uploaded size (EXP-016 `3a4d07cc`). The slice textures themselves are ≤ 1024 px and are not logged.
7. **In-engine runs** `scripts\run-vsa.ps1`, derived from E1's harness:
   - 1920×1080 window, master server 127.0.0.1, single player, `cht_bGod`/`cht_bInvisible`, ESC at 15 s;
   - window-only captures; the foreground state is recorded;
   - the log is scanned for the settings `Echo`, for upload lines, and for texture/KTX2/pool errors;
   - each batch runs through `gpu-lock.ps1 run -Owner VSA`.

## Results ([EXP] unless labelled otherwise)

### Tests

TESTS-RESULT

### Level scope and plans

| Item | TFE (`01_Hatshepsut`) | TSE (`1_0_InTheLastEpisode` + `1_1_Palenque`) |
|---|---|---|
| World dictionary names / textures named | 348 / 183 | 243 + 531 names; 121 + 258 textures → 345 unique |
| Textures with a selection record | 74 | 155 |
| Fallback categories (largest groups) | architecture 45, technical 35 (incl. editor markers), enemy 32, sky 24 | architecture 101, enemy 69, props 55, technical 43 |
| Supplying layer | Classic Base 182, HD Quality 1 | Classic Base 343, HD Quality 2 |
| HD Material Maps | 2 assets (2 normal, 2 gloss) | 4 assets (4 normal, 4 gloss) |
| HD Artwork / HD Interface | 7 / 0 candidates `disabled` | 17 / 0 candidates `disabled` |
| AI (`conservative`) | PLAN-AI-TFE | PLAN-AI-TSE |
| Vulkan pool (RGBA8, mips; all scoped textures resident) | POOL-TFE | POOL-TSE |
| Determinism | run 1 = run 2 (byte-identical), one `planHash` per game | same |

### Overlays (`slice-v0\tfe`, `slice-v0\tse`)

PACKAGE-TABLE

### In-engine

**Settings script and upload size** (Vulkan raster, VS-E build, slice runtime, settings script via `include`):
- The log contains `SSTRE: engine settings pc-default applied.`
- The synthetic 4096² probe in `12_Karnak` logged `4096x4096 px, 1 mip(s) skipped, uploaded as 2048x2048 (area limit 4194304 px, max dimension 8192, tex_iNormalSize=11)`. EXP-016 measured `uploaded as 512x512` with the shipped settings.
- The effective upload area is therefore 2048². Every slice texture (≤ 1024²) uploads at full size.
- The run reached `started.` and stayed responsive. No texture, KTX2 or pool errors were logged.

VERIFY-RUNS

CAPTURE-MATRIX

## Deviations, modifications and failures

- **Scope change.** The owner changed the scope mid-sprint from "set 1 + all records" to the first campaign level per game (TSE: two levels). Neither the set-1 assets outside those levels nor the earlier set-1 overlay are part of the deliverable any more. The earlier full-record plan, kept as an intermediate result, showed the pool constraint at scale:
  - with `conservative` over all TFE records: 965 MB counted with every pending ×2 target, against 285 MB for what exists now;
  - 271 of 971 pending targets (TFE and TSE together) would be dropped by the pool budget.
  - With the per-level scope, both games fit without any reduction.
- **Budget order defect (fixed, `33ed2d7`).** The first full-record plan cut 5 of the 7 produced AI outputs back to Classic size.
  - Cause: the pool budget halved the largest asset first, whether or not its size existed yet. Hundreds of not-yet-produced ×2 targets kept their planned size.
  - `docs/asset-layers.md` already said pending AI targets are reduced first; the code did not do so. It does now.
- **Map size defect (fixed, `4c43b6d`).** Halving a pending AI albedo target also halved the asset's existing material maps.
- **Map upscale (fixed, `3aacc0d`).** The packager upscaled a 128² HD map to the 256² the plan assumed (`pxAssumed`). It now keeps the real size and records the step.
- **EXP-015 numbers change.** A re-run of EXP-015's configurations would give different `pc-low-memory` numbers, because of the 1024² cap, the pool budget and the reduction order. EXP-015 itself is unchanged.
- **CI pin.** AssetCompiler CI validates against the pinned umbrella commit `189da0c`. Its schemas lack `engineSettings`, `additionalBudgets` and `assetScope`, so the schema tests fail in CI until the pin includes this branch's schema commits.
- **Load protocol.**
  - The first plan and package runs (about 00:50–01:00) ran before the lead's `wait-quiet` protocol. They were CPU-only (Python plus Compressonator) and may coincide with the foreign load the lead observed.
  - Every later CPU-heavy step ran after `wait-quiet`. Every game window ran under `gpu-lock.ps1 run`.
  - One locked session was interrupted by the owner's pause (02:2x). The game had already exited, and the lock was released manually with `release -Owner VSA`. The interrupted Classic control probe left its synthetic probe file in the Classic test runtime; it was removed.
- **VS-E binaries changed during the experiment** (rebuilt at 01:12, `sprint2/integration` HEAD moved). The runtimes were recreated from the new build, and both slice runtimes contain the upload log. The recorded binary hashes are in the local effective-configuration file.
- DEVIATIONS-RUNS

## Interpretation

INTERPRETATION

## Impact on ADRs, dossiers and backlog

- **ADR-0009 rule 5** (platform profiles): profiles now also carry the runtime engine settings and several memory budgets. Suggested clarification: a profile's size limits must be consistent with the upload limit of the settings it emits.
- **EXP-016 open questions.**
  - Q1, for the slice: keep the shipped `GLSettings` scripts and ship a separate profile script activated by `+script`/`include`. The owner may still prefer a default.
  - Q2 is implemented: `TEX_32BIT` is the default for replacements.
- **Backlog:**
  - bump the AssetCompiler CI umbrella pin after merging `sprint2/exp-019`;
  - a launcher integration of the settings script for players;
  - map sizes in the HD plugin sidecars, which removes `pxAssumed`;
  - complete level scopes (textures loaded by entity classes);
  - RTGL1 behaviour for `_n`/`_rme` without an albedo override;
  - a larger or chained Vulkan pool before a full-game AI build.

## Open questions

OPEN-QUESTIONS
