# EXP-019: Vertical-slice asset integration (slice v0): engine settings, Vulkan pool budget, overlay packaging

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | Sprint 2 track VS-A (vertical slice, assets); ADR-0009 consequences 1–3; EXP-016 follow-ups ("platform profile that sets the texture cvars", "AssetCompiler support for `TEX_32BIT`", Vulkan pool) |
| Status | IN-ENGINE-STATUS |
| Environment | Windows 11 Pro 10.0.22631, Intel Core i5-11600K, NVIDIA RTX 4070 12 GB, driver 616.64 (Vulkan 1.4.351). Python 3.10.11 venv `G:\sstre-tmp\assets\venv` (numpy 2.2.6, Pillow 12.3.0, jsonschema 4.26.0, pytest 9.2.0, reuse 5.0.2). Compressonator CLI 4.6.0 (as in EXP-002/EXP-013). KTX-Software `ktx` 4.4.2 as a black-box validator only (EXP-014) |
| Inputs | Selection records and texture set 1 of EXP-012; the local HD image plugin output (EXP-012); AI1's layer-6 pack `ai1-runp` (EXP-013 §7, the latest pack available at packaging time); the owner's Steam Classic TFE install (read-only). Runtime data: a copy of E1's `runtime-tfe` (EXP-009); binaries: a copy of track VS-E's integrated TFE build (SSTRE-Engine local `sprint2/integration`: Classic-VK + RT transplant + `FilterBitmap` fix + upload log + master-server switch). No asset paths, hashes or images are published here (GATE-05) |
| Code | SSTRE-AssetCompiler `feature/slice-packaging` (local, not pushed); umbrella `sprint2/exp-019` (schema change + this report) |

## Goal and success criteria

1. AssetCompiler: `TEX_32BIT` on replacements by default; platform profiles with an engine-settings section that the packager emits as an SSTRE settings script (original `GLSettings` scripts untouched); the 537 MB Vulkan texture pool as a planner constraint; a deterministic `package` command (plan + inputs → runtime overlay with a provenance manifest).
2. Assemble slice v0 locally with the ADR-0009 defaults plus AI profile `conservative` on `pc-default`, install it into a private runtime copy, run TFE level 01 and a level that shows set-1 assets in Vulkan raster and RT with the settings script active, verify full-size uploads in the console log, and capture paired Classic vs slice screenshots (local only).
3. Record the effective configuration and the per-asset provenance (local), and report aggregates here.

## Design (what was built)

### `TEX_32BIT` (flag bit 1)

`make_replacement()` and `sstre-ac tex-replace` set flag bit 1 on every replacement by default (`--no-32bit` / `force_32bit=False` keeps the original flags exactly). `tex-encode` keeps the sidecar flags, so originals still re-encode byte-identically, unless `--32bit` is given. The flag's meaning comes from EXP-016 [DOC: EXP-016 §5]; the AssetCompiler stays clean-room (no engine source was read for this experiment).

### Engine settings in platform profiles

Platform profiles gain an optional `engineSettings` section: an ordered list of console variables and the script path (default `Scripts/SSTRE/TextureProfile.ini`).

| Profile | Console variables | Planner consequence |
|---|---|---|
| `pc-default` | `sam_iVideoSetup=3`, `tex_iNormalSize=11`, `tex_iNormalQuality=22` (EXP-016 recommendation) | `maxPixels` 4 194 304 (2048² upload area); was 8 388 608 |
| `pc-low-memory` | `sam_iVideoSetup=3`, `tex_iNormalSize=10`, `tex_iNormalQuality=22` | `maxPixels` 1 048 576 (1024²); was 4 194 304 |
| `legacy-constrained` | none (hypothetical profile) | unchanged |

- **Mechanism.** The script is activated with `+script` on the command line. That is the mechanism EXP-016 already used to set these variables (its custom-settings runs C3–C5) [DOC: EXP-016 §4], and the one E1's launch instructions use (EXP-009). The shipped `Scripts/Game_startup.ini` says it is "executed each time SeriousSam is started" [DOC: comment in the shipped file], but writing it would modify a shipped file, so it was not used. A profile cannot name a `Scripts/GLSettings/` path (checked by the AssetCompiler and by the schema). SETTINGS-MECHANISM-RESULT
- **Consistency rule.** `tex_iNormalSize` = N caps every upload at 4^N pixels (EXP-016 §5), so the profile's `maxPixels` must not exceed 4^N. Otherwise the plan would ship pixels that the runtime discards at load time. The AssetCompiler rejects such a profile.
- **Caveat.** The variables are persistent: once set, they stay in the runtime's `PersistentSymbols.ini` after a clean exit.

### Vulkan texture pool as a planner constraint

Profiles gain `additionalBudgets`. Both PC profiles record `vulkan-texture-pool`: 536 870 912 bytes (256·256·4·4/3 × 512 × 3, EXP-016 [SRC via EXP-016]), every format counted as RGBA8, mips included, `scope: per-game` (one runtime loads one game), policy `reduce-largest`. The count covers all planned assets of a game, so it is an upper bound for a single level.

Two planner defects showed up as soon as the pool applied to a real plan. Both were fixed (see Deviations).

### `sstre-ac package`

- **Inputs.** A plan plus local inputs: `--classic-root EDITION=ROOT`, `--hd-images`, `--pack-dir`, and an optional `--bc-encoder`. The packager re-checks the `planHash`, the Classic file hash of every packaged asset, the AI and override output hashes, and the HD source hashes against the plan. It refuses on any mismatch.
- **Output** (relative to the game root):
  - a loose v4 `.tex` for raster, with the Classic mex and `TEX_32BIT`, at the planned size fitted to Classic × 2^k with k ≤ firstMip;
  - `OverridenTextures/Compressed/<path>{,_n,_rme}.ktx2` for RT (the layout from EXP-002/EXP-009). `_n` holds X/Y/Z in R/G/B; the two-channel layout of the HD normal maps (X in alpha, Y in green) is detected and expanded. `_rme` holds R = 1 − gloss, G = metallic 0, B = emission 0 [ASM: conversion choice; see Open questions];
  - the settings script;
  - `SSTRE/package-manifest.json`: plan and profile hashes, options, encoder identity, per-asset inputs with hashes, every output with its processing steps, the file list with SHA-256, and a `packageHash`.
- **What is written.** Only assets whose albedo is not the Classic original, or that gain material maps, are written; Classic assets stay in the archives. Assets with Classic albedo and HD maps get an RT albedo `.ktx2` from the Classic image, so that the `_n`/`_rme` files have a base [ASM: whether RTGL1 needs the albedo file for the maps was not tested].
- **Encoding.** BCn goes through Compressonator 4.6.0 (`-fd BC7|BC5|BC4 -miplevels 20`), and the result is checked (vkFormat, size). Without an encoder, a clean-room KTX 2.0 writer (written from the Khronos specification) writes RGBA8 with a box-filtered mip chain. Its synthetic outputs pass `ktx validate` 4.4.2.
- **Scope.** Multi-frame and effect textures are not packaged. AO and height maps have no RT slot.

## Procedure (exact, reproducible; all local under `G:\sstre-tmp\vsa\`)

1. Worktrees: `git -C …\SSTRE-AssetCompiler worktree add G:\sstre-tmp\vsa\wt-ac -b feature/slice-packaging origin/main`; umbrella `G:\sstre-tmp\vsa\wt-umbrella` on `sprint2/exp-019` from `origin/main`.
2. Tests: `python -m pytest -p no:cacheprovider` with and without `SSTRE_SCHEMAS_DIR=<wt-umbrella>/schemas`; `scripts/validate_repo.py --root .` in both repositories; `reuse lint` in both.
3. Configuration `cfg\slice-v0.json`: `layers` defaults (Classic Base, HD Quality, HD Material Maps on; HD Artwork and HD Interface off), `ai-enhancement.qualityProfile = conservative` with pack `ai1-runp`, `platformProfile = pc-default`. `sstre-ac validate-config --verify-files` reported OK.
4. Plan, twice: `sstre-ac plan --config cfg\slice-v0.json --selection <records> --assets <set 1 READY.json> --out plan\slice-v0.run{1,2}.json`, then `cmp`.
5. Package, twice (`scripts\package-slice.sh`, started only after `gpu-lock.ps1 wait-quiet` returned 0): `sstre-ac package --plan … --classic-root classic_tfe=<Steam TFE> --hd-images <HD plugin out> --pack-dir <ai1-runp> --bc-encoder <compressonatorcli> --out slice-v0 | slice-v0-rerun`, then `diff -r` and `ktx validate` on every `.ktx2`.
6. Runtimes (`scripts\make-runtimes.sh`, after `wait-quiet`): `runtime-classic` and `runtime-slice` are copies of E1's `runtime-tfe` whose `Bin\` is replaced by the VS-E build plus the clean-room `RayTracedGL1.dll` (identical SHA-256 in both places). Both use the same engine binary. The overlay is copied into `runtime-slice` only. E1's files were not modified.
7. Upload probe (`scripts\make_probe.py`): our own synthetic 4096² pattern, written with `make_replacement` over the header of one Karnak wall texture whose firstMip allows 4096², and placed temporarily in each runtime. The VS-E build logs every texture wider than 2048 px with its uploaded size (EXP-016 `3a4d07cc`). The slice textures themselves are ≤ 1024 px, so they are not logged; the probe shows which area limit is in effect.
8. In-engine runs (`scripts\run-vsa.ps1`, derived from E1's harness: 1920×1080 window, master server 127.0.0.1, single player, `cht_bGod`/`cht_bInvisible`, ESC at 15 s, window-only captures at 22 s and 32 s, foreground recorded), each batch through `gpu-lock.ps1 run -Owner VSA`. Classic runs use the shipped settings; slice runs activate the settings script. Image metrics (`scripts\pair_metrics.py`): MAD, PSNR and the share of pixels differing by more than 8, over the frame without the title bar.

## Results ([EXP] unless labelled otherwise)

### Tests

TESTS-RESULT

### Plan (1376 assets, TFE + TSE records; set 1 facts)

| Item | Value |
|---|---|
| Supplying layer | Classic Base 1362, HD Quality 14 (TFE: 655 / 5) |
| HD Material Maps | 27 assets / 46 maps in total; TFE: 6 assets (5 normal, 5 gloss) |
| HD Artwork / HD Interface | `disabled` for 149 / 2 candidates (no opt-in) |
| AI (`conservative`) | 7 applied (all 7 `ai1-runp` entries), 700 awaiting output, 385 not eligible, 12 source already sufficient, 272 platform-capped (271 by the Vulkan pool budget, 1 by the firstMip cap) |
| Vulkan pool, TFE | 965 MB counted with every pending AI target → 537 MB after 146 halvings of pending targets; **285 MB for what exists now** (Classic + HD + the 7 AI outputs, RGBA8 with mips, all TFE assets) |
| Vulkan pool, TSE | 921 MB → 536 MB (125 halvings); 281 MB existing |
| Main raster budget (2 GiB, report) | within budget |
| Determinism | run 1 and run 2 byte-identical; one `planHash` |

[EXP/ASM] Even counted as an upper bound (every TFE texture resident at once), the slice fits the pool with room to spare. The `conservative` profile applied to all of TFE would not fit at full planned size: the pool budget drops 271 of 971 pending ×2 targets (28 %, TFE and TSE together) back to the source size. On Classic-VK, a full-scale AI build therefore needs either a larger or chained pool (EXP-016 backlog item) or a per-level count.

### Package (slice v0, TFE)

| Item | Value |
|---|---|
| Assets packaged | 17: 7 AI outputs, 5 HD Quality albedos, 5 Classic albedos that gain HD maps |
| Files | 40: 12 raster `.tex`, 17 RT albedo `.ktx2` (BC7), 5 `_n` (BC5), 5 `_rme` (BC4), the settings script, the manifest; about 24.7 MB |
| Raster sizes | AI: 3 × 1024², 1 × 1024×512, 3 × 512²; HD: 512², 512², 256², 256², 256×512. All have `TEX_32BIT` and the Classic mex |
| Map handling | 5 normal maps detected as the two-channel layout and expanded. One asset's HD maps are 128², below the 256² the plan assumed (`pxAssumed`); they were kept at 128² after the fix (Deviations) |
| Skipped | none |
| Validation | `ktx validate` passes for 27/27 `.ktx2` |
| Determinism | two runs into separate directories: `diff -r` identical, same `packageHash`; about 35–55 s per run (Compressonator dominates) |
| Effective configuration and per-asset provenance | recorded locally in `slice-v0-effective.local.json` and the package manifest |

### In-engine (Vulkan raster and RT)

IN-ENGINE-RESULT

## Deviations, modifications and failures

- **Budget order defect (fixed, `33ed2d7`).** The first slice plan cut 5 of the 7 produced AI outputs back to Classic size. The pool budget halved the largest asset first, whether or not its size existed yet. Hundreds of not-yet-produced ×2 targets kept their planned size, while the real 1024² outputs were the largest single items. `docs/asset-layers.md` already stated that pending AI targets are reduced first; the code did not do so. Now pending targets are reduced first, then existing sizes.
- **Map size defect (fixed, `4c43b6d`).** When the budget halved a pending AI albedo target, it also halved the existing material maps of that asset.
- **Map upscale (fixed, `3aacc0d`).** The packager upscaled a 128² HD map to the 256² the plan assumed. It now keeps the smaller real size and records the step.
- **EXP-015 numbers change.** Because of the new limits and these fixes, a re-run of EXP-015's configurations would give different `pc-low-memory` numbers (1024² cap instead of 2048², pool budget, a different reduction order). EXP-015 itself is unchanged.
- **CI pin.** AssetCompiler CI validates against the pinned umbrella commit `189da0c`. Its `platform-profile` schema lacks `engineSettings`/`additionalBudgets`, so `test_builtin_data_matches_schemas` will fail in CI until the pin is bumped to a commit that contains `4675c78`.
- **Load protocol.** The first packaging and plan runs (about 00:50–01:00) ran before the lead's `wait-quiet` protocol was announced. They were CPU-only (Python + Compressonator, no GPU), but they may coincide with the foreign CPU load the lead observed. Every later CPU-heavy step ran after `wait-quiet`, and every game window ran under `gpu-lock.ps1 run`.
- DEVIATIONS-RUNS

## Interpretation

INTERPRETATION

## Impact on ADRs, dossiers and backlog

- **ADR-0009 rule 5** (platform profiles): profiles now also carry the runtime engine settings and several memory budgets. Suggest a clarification that a profile's size limits must be consistent with the upload limit of the settings it emits.
- **EXP-016 open questions:** Q1 answered for SSTRE builds: keep the shipped `GLSettings` scripts and ship a separate profile script activated by `+script` (owner may still prefer a default). Q2 implemented: `TEX_32BIT` is the default for replacements.
- **Backlog:** bump the AssetCompiler CI umbrella pin (after merging `sprint2/exp-019`); a per-level texture residency count for the pool budget; map sizes in the HD plugin sidecars (removes `pxAssumed`); a launcher or `Game_startup` integration of the settings script for players; RTGL1 behaviour for `_n`/`_rme` without an albedo override.

## Open questions

OPEN-QUESTIONS
