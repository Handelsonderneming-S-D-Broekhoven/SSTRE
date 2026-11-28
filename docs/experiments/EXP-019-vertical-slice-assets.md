# EXP-019: Vertical-slice asset integration (slice v1): engine settings, Vulkan pool budget, level scope, overlay packaging

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | Sprint 2 track VS-A (vertical slice, assets); ADR-0009 consequences 1–3; EXP-016 follow-ups ("platform profile that sets the texture cvars", "AssetCompiler support for `TEX_32BIT`", Vulkan pool) |
| Status | Completed for slice v1 (both games packaged deterministically; in-engine pairs on the integrated VS-E build). Re-run on a newer VS-E build is up to the lead |
| Environment | Windows 11 Pro 10.0.22631, Intel Core i5-11600K, NVIDIA RTX 4070 12 GB, driver 616.64 (Vulkan 1.4.351). Python 3.10.11 venv `G:\sstre-tmp\assets\venv` (numpy 2.2.6, Pillow 12.3.0, jsonschema 4.26.0, pytest 9.2.0, reuse 5.0.2). Compressonator CLI 4.6.0 (as in EXP-002/EXP-013). KTX-Software `ktx` 4.4.2 as a black-box validator only (EXP-014) |
| Inputs | Selection records and texture set 1 of EXP-012; the local HD image plugin output (EXP-012); AI1 layer-6 packs: the level-1 packs `classic-tfe-level1` and `classic-tse-level1` (version 0.1.0, profile `conservative`, EXP-013; local only). Slice v0 used only AI1's earlier seven-asset run; the owner's Steam Classic TFE and TSE installs (read-only). Test runtimes: data copied from E1's TFE runtime (EXP-009) and E4's TSE runtime (EXP-016); binaries copied from track VS-E's integrated build (SSTRE-Engine local `sprint2/integration`: Classic-VK + RT transplant (TFE) + `FilterBitmap` fix + upload log + master-server switch). No asset paths, hashes or images are published here (GATE-05) |
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
3. **Configurations** `cfg\slice-v0-{tfe,tse}.json` (slice v0, AI1 set 1) and `cfg\slice-v1-{tfe,tse}.json` (slice v1, the AI1 level-1 pack of the game; v0 stays reproducible):
   - `layers` at their defaults: Classic Base, HD Quality and HD Material Maps on; HD Artwork and HD Interface off;
   - `ai-enhancement.qualityProfile = conservative` with the AI packs;
   - `platformProfile = pc-default`.
4. **Pipeline** `scripts\build-slice.sh`, started only after `gpu-lock.ps1 wait-quiet` returned 0. For each game:
   - `sstre-ac level-scope <install> --edition classic_tfe|classic_tse --level <world file>…`;
   - `plan --config … --selection <records> --assets <set 1 READY.json> --scope scope\<game>.json`, run twice, then `cmp`;
   - `package --plan … --classic-root … --hd-images … --pack-dir … --bc-encoder compressonatorcli --out slice-vN\<game>`, run twice into `slice-vN` and `slice-vN-rerun`, then `diff -r` (`SLICE=slice-v1`, `PACKDIRS_<game>` = the level-1 pack directory);
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

- AssetCompiler `feature/slice-packaging`: 187 passed with `SSTRE_SCHEMAS_DIR` pointing at this branch's schemas (180 passed + 7 skipped without). `validate_repo.py`: 0 errors, 0 warnings in both repositories. `reuse lint`: compliant in both.
- Slice v1 needed no AssetCompiler change; the tests above cover the code that built it.

### Level scope and plans

| Item | TFE (`01_Hatshepsut`) | TSE (`1_0_InTheLastEpisode` + `1_1_Palenque`) |
|---|---|---|
| World dictionary names / textures named | 348 / 183 | 243 + 531 names; 121 + 258 textures → 345 unique |
| Textures with a selection record | 74 | 155 |
| Fallback categories (largest groups) | architecture 45, technical 35 (incl. editor markers), enemy 32, sky 24 | architecture 101, enemy 69, props 55, technical 43 |
| Supplying layer | Classic Base 182, HD Quality 1 | Classic Base 343, HD Quality 2 |
| HD Material Maps | 2 assets (2 normal, 2 gloss) | 4 assets (4 normal, 4 gloss) |
| HD Artwork / HD Interface | 7 / 0 candidates `disabled` | 17 / 0 candidates `disabled` |
| AI (`conservative`), slice v1 | applied 132, awaiting 5, not eligible 41, platform-capped 4, source-sufficient 1; 0 rejected | applied 260, awaiting 18, not eligible 56, platform-capped 10, source-sufficient 1; 0 rejected |
| AI, slice v0 (for comparison) | applied 2, awaiting 135 | applied 0, awaiting 278 |
| Vulkan pool (RGBA8, mips; all scoped textures resident; budget 536 870 912 B) | 203 685 876 B (37.9 %), 0 halvings, nothing reduced | 454 020 956 B (84.6 %), 0 halvings, nothing reduced |
| Determinism | run 1 = run 2 (byte-identical), one `planHash` per game | same |

### Overlays (`slice-v1\tfe`, `slice-v1\tse`; `slice-v0` kept unchanged)

| Item | TFE | TSE |
|---|---|---|
| Assets packaged (v1) | 133: 132 AI (from Classic pixels, layer 6), 1 HD Quality | 262: 260 AI, 2 HD Quality |
| Files (v1) | 272: 133 loose `.tex`; 133 BC7 albedo, 2 BC5 `_n` and 2 BC4 `_rme` `.ktx2`; settings script; manifest | 534: 262 `.tex`; 262 BC7, 4 BC5 and 4 BC4 `.ktx2`; script; manifest |
| Size (v1) | 158 MiB | 359 MiB |
| Largest raster output | 1024 px (within the 2048² upload limit) | 1024 px |
| Slice v0 (for comparison) | 4 assets / 12 files | 5 assets / 16 files |
| Packaging time per run (Compressonator BC7) | 195 s; rerun 186 s | 391 s; rerun 403 s |
| Determinism | plans: run 1 = run 2; `slice-v1` = `slice-v1-rerun` (`diff -r` identical) | same |
| `ktx validate` 4.4.2 | 137 of 137 pass | 270 of 270 pass |

- **AI awaiting in TFE (5):**
  - 2 editor marker textures, which AI1 excluded on purpose;
  - 3 that AI1 classes as effects/technical while the scope's fallback category says enemy or items.
- **AI awaiting in TSE (18):**
  - 10 with the same class disagreement (AI1: effects/technical; scope fallback: enemy, props, items, architecture);
  - 4 procedural textures without pixels;
  - 3 named in the world dictionary but not loaded by either level at runtime;
  - 1 sky whose selected source is HD Quality. An SR result made from Classic pixels would not match the plan's source.
- The class disagreement is accepted for the slice; those textures stay Classic. It is a question of the path-based fallback categories, not a pack defect.
- AI1's packs also contain BC5 normal maps for some assets. The packager takes only the albedo entries of AI packs, so these were not used. The RT `_n`/`_rme` maps in the overlays come from HD Material Maps only.

### In-engine

**Settings script and upload size** (Vulkan raster, VS-E build, slice runtime, settings script via `include`):
- The log contains `SSTRE: engine settings pc-default applied.`
- The synthetic 4096² probe in `12_Karnak` logged `4096x4096 px, 1 mip(s) skipped, uploaded as 2048x2048 (area limit 4194304 px, max dimension 8192, tex_iNormalSize=11)`. EXP-016 measured `uploaded as 512x512` with the shipped settings.
- The effective upload area is therefore 2048². Every slice texture (≤ 1024²) uploads at full size.
- The run reached `started.` and stayed responsive. No texture, KTX2 or pool errors were logged.

**Slice v1 repeat** (session 4, same VS-E build as the runtimes had before; runtimes rebuilt with their existing `Bin\`):
- Slice probe: `uploaded as 2048x2048 (area limit 4194304 px, …, tex_iNormalSize=11)`, settings `Echo` present.
- Classic control probe (no settings script): `3 mip(s) skipped, uploaded as 512x512 (area limit 262144 px, …, tex_iNormalSize=9)`. The slice therefore uploads 16× the area of the shipped settings for large textures.
- The largest slice-v1 raster output is 1024 px, so no slice texture is downscaled at upload. No upload line names a slice texture.

**Run summary** (24 locked runs in three lock acquisitions of 8.9, 5.0 and 7.9 min; Vulkan raster = `sam_iGfxAPI=1`, RT = 2):

| Item | Result |
|---|---|
| Runs that reached `started.` and stayed responsive | 24 / 24 |
| Game watchdog | `WATCHDOG=ok` in 24 / 24; no kill, no freeze reproduced |
| Settings `Echo` | in every slice run, in no Classic run |
| Texture, KTX2, Vulkan pool or RTGL1 errors | 0 in every run |
| Warning lines, Classic vs slice of the same level and API | identical sets in every pair (joystick, EAX, missing mod files and the harness's own two script lines) |
| Foreground at every capture | yes, in every run (no focus loss recorded) |
| TSE ray tracing | not run: the integrated TSE build has no RT layer |

The engine log has no line per loaded override, so "loaded without errors" means "no error line", not a positive load count. In RT the overlay is visibly in use (see below).

**Captures** (window-only, 1920×1080, local only). Metrics from `scripts\pair_metrics.py` on the frame without the title bar: mean absolute difference (MAD, 0–255), PSNR, and the share of pixels whose largest channel difference exceeds 8.

| Pair (level, API, capture) | What is on screen | MAD | PSNR (dB) | px > 8 | Mean luma Classic / slice |
|---|---|---|---|---|---|
| TFE `01_Hatshepsut`, Vulkan, 115 s | level (arrival cinematic) | 15.4 | 18.3 | 44 % | 130.4 / 130.9 |
| TFE `01_Hatshepsut`, RT, 115 s | level (arrival cinematic) | 11.5 | 20.8 | 41 % | 136.7 / 136.3 |
| TSE `1_0_InTheLastEpisode`, Vulkan, 32 s | level (intro camera) | 7.0 | 26.5 | 31 % | 27.6 / 28.1 |
| TSE `1_1_Palenque`, Vulkan, 32 s | level (player view) | 8.5 | 22.9 | 49 % | 32.0 / 32.9 |

- Mean luminance stays within 1 level of 255 in every level pair, so the AI layer does not shift brightness or colour balance. The large pixel shares come from texture detail (the purpose of the layer), plus small camera and timing differences in the cinematics; they are not an error measure.
- **Visual inspection** of the pairs above and of every other capture: no wrong mapping, no missing or black textures, no alpha errors (alpha-tested foliage and decals look like Classic), no visible tiling seams.
- The slice is visibly sharper on walls, rock and terrain. On some distant mountain and cloud textures in TFE the SR output looks posterised (flat regions with hard edges), in raster and RT alike. That is a quality observation for the AI profile, not a packaging defect.
- In RT the slice frames show the AI textures as well, so RTGL1 uses the `OverridenTextures` KTX2 files. The frame rates of the pair are comparable (about 250 FPS in both RT runs; the raster runs are capped at about 144 FPS).
- The TFE text crawl and the menus are animated. Pairs captured on them (session 4 and part of session 5) are kept locally but say nothing about textures.

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
- **Capture timing.** Session 4 used batch-s2's single ESC at 15 s. In TFE `01_Hatshepsut` and TSE `1_0` that ESC opened the game menu, so all their captures showed the menu. In TSE `1_1` it closed Netricsa and the captures show the level. Session 5 used two ESCs (15 s and 17 s): TSE `1_0` then shows the level, TSE `1_1` the menu. TFE opens with a text crawl that is still running at 90 s, so session 6 captured TFE at 60, 90 and 115 s. The table above uses the one valid pair per level.
- **Configurations.** Slice v1 uses new files `cfg\slice-v1-{tfe,tse}.json`, so `slice-v0` stays reproducible from its own configuration. Slice v1 lists only the level-1 pack of each game. The earlier seven-asset pack is not used.
- **Runtimes.** VS-E's build tree had moved on (02:21) since the runtimes were made (01:4x). `make-runtimes.sh` gained `KEEP_BIN=1`, which keeps each runtime's existing `Bin\`. Slice v1 was therefore tested on the same VS-E binaries as the slice-v0 probes. A run on a newer VS-E build is a separate step.
- The overlay's `INSTALL.txt` still names "slice v0" in its title line; the content applies to v1 unchanged.

## Interpretation

- The packaging path scales from a handful of assets to complete level sets: 133 (TFE) and 262 (TSE) assets, each rebuilt byte-identically, each `.ktx2` valid, within the planner's Vulkan pool estimate, and without any upload downscale at the `pc-default` settings.
- The pool estimate did not change between slice v0 and slice v1, because pending AI targets were already counted at their planned size. TSE uses 85 % of the pool with one level pair resident; a full TSE episode with AI ×2 targets would exceed it. That supports the backlog item for a larger or chained pool before full-game AI builds.
- The in-engine evidence is negative evidence (no error, no freeze, no visible defect) plus visual confirmation that both the raster and the RT path show the AI textures. It is not a quality judgement of the AI layer, apart from the posterisation noted above.

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

- Owner: is the visible SR posterisation on distant terrain and cloud textures acceptable for the slice, or should those categories move to the conventional resample (L1) in the conservative profile?
- Owner: the 10 TSE and 3 TFE textures whose category AI1 and the scope classify differently stay Classic. Should a later pass resolve this with explicit selection records?
