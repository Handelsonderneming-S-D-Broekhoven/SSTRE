# EXP-025: Rendering audit, comparison harness and regression scene set (M0.1, POC-89, POC-90)

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | POC-89 (defect register and regression scene set), POC-90 (comparison harness, fixed exposure, checkpoints, debug views) |
| Status | **complete for M0.1 research stage**: harness in use by other tracks, 20-checkpoint scene set (8 TFE, 12 TSE; 7 + 9 levels), register RDF-001..021. Open items in §8 |
| Environment | Windows 11 Pro 22631, i5-11600K, RTX 4070 12 GB, windowed 1600×900, VSync off |
| Inputs | Reference build 0.1.0-preview2 = SSTRE-Engine `sprint2/integration` @ `7eeed884` (copied, never modified). Classic-VK reference raster = the Phase-1 Classic-VK runtimes. Game data: the owner's Steam TFE and TSE (no asset names in this report, GATE-05) |

## 1. Goal and success criteria

1. A reproducible harness that renders the **same level, camera and simulation state** in up to 7 configurations (directive §8) plus a "corrected" build of another track, and produces a side-by-side local contact sheet with simple image metrics.
2. Fixed exposure for diagnostics and debug views where the engine exposes them.
3. A sweep beyond the three showcase levels (at least 4 TFE and 4 TSE levels) over the scene types of directive §8, every visible defect filed in [`rendering-defects.md`](../rendering-defects.md) with a harness checkpoint as its regression test.

## 2. Harness (POC-90)

Local script `G:\sstre-tmp\r1\harness\r1-compare.ps1` (usage in its header and in the R1 status file). Not published: it references local runtimes and game data only.

### 2.1 Configurations

| Id | Meaning | Runtime | `sam_iGfxAPI` |
|---|---|---|---|
| `cvk` | Classic-VK reference raster, original textures | copy of the Phase-1 Classic-VK runtime | 1 |
| `vk-orig` / `vk-enh` | SSTRE Vulkan raster, original / enhanced textures | copies of preview2 `*-Classic` / `*` | 1 |
| `gl-orig` / `gl-enh` | SSTRE OpenGL, original / enhanced | same | 0 |
| `rt-orig` / `rt-enh` | SSTRE RT (RTGL1), original / enhanced | same | 2 |
| `fix` | "corrected" build of another track: its `Bin` (and optional data overlay) on a cached copy of the orig or enh runtime | `runtime-fix-<name>-<game>-<base>` | `-FixApi`, default 2 |

Each configuration starts through preview2's own launcher script (`Scripts\SSTRE\Launch-<API>.ini`, so the enhanced runtimes get the SSTRE texture profile), then the harness settings.

### 2.2 Deterministic camera checkpoint, no input

- **Position and view:** the player spawns at the coop marker *Player Start - N* (`cht_iGoToMarker=N` in the start script) [SRC `EntitiesMP/Player.es:5250-5256`]. Its orientation is the marker's. Marker lists were extracted locally from the level files. A missing marker crashes the game (null entity at `Player.es:5255`) [SRC], so the harness only uses listed markers. Marker 0 = the level start (levels that start in NETRICSA need `-Esc`; marker spawns never start in NETRICSA [SRC `Player.es:5353`]).
- **Simulation state:** `cmd_cmdOnTick` (engine shell command executed once per game tick, `cmd_tmTick` = game time) [SRC `Engine/Network/SessionState.cpp:1019-1024`] freezes the world at game time *T* with `gam_fRealTimeFactor=0.0` [SRC `Server.cpp:741`; the lerp factor clamps to 0, `SessionState.cpp:1506-1514`]. Demos freeze with `dem_fSyncRate=-1.0` (`DEMOSYNC_STOP`, `Network.cpp:1969`). Enemies, particles and the weapon animation are therefore identical in all renderers, independent of load time. RT keeps accumulating on the frozen frame, which removes denoiser noise from the comparison.
- The shell needs float literals for FLOAT comparisons (`cmd_tmTick>=3` is a type mismatch, `>=3.0` works) [EXP].
- God mode and invisibility on; FOV 90; HUD and FPS counter on (HUD is itself a checked scene type); console overlay off (`con_iLastLines=0`).
- The mouse is parked in the bottom-right screen corner before each launch, so no pointer motion reaches the game.
- Capture: `PrintWindow` of the client area at fixed wall-clock times after launch (default 45 s and 55 s; the last one is used). Engine screenshots cannot be used in Vulkan/RT (RDF-007).

### 2.3 Diagnostics

- `-FixedExposure X`: RT only, sets `srt_fTonemappingMinLogLuminance = srt_fTonemappingMaxLogLuminance = X` at freeze time, i.e. after the per-world tuning that `CustomInfo` applies at world load [SRC `CustomInfo.cpp:134`], so exposure no longer adapts.
- `-DebugMode`: `lightonly` (`wld_bRenderTextures=0`: raster shows the shadowmap lighting only — the reference for RD-016), `noshadowmaps`, `noparticles`, `nofog`, `nomodels`, `wire`, `rtgradients`, `rtmotion` (RTGL1 debug views) [SRC `Engine/Graphics/GfxLibrary.cpp:1347-1364`, `Raytracing/SSRT.cpp:52-53`].
- Per tile: mean RGB and luma, fraction of near-black (luma < 8) and clipped (> 250) pixels, luma delta vs `cvk`; watchdog result; RTGL1 and validation error counts from the log.
- Rules: GPU lock per invocation (owner configurable), estimated hold checked against 30 min; game watchdog (rule 1c) per run.

### 2.4 Harness validation [EXP]

- **Determinism:** `tse-corr-2_1m3`, `tse-out-1_3m10`: Classic-VK reference and SSTRE Vulkan orig give **identical** metrics (luma 33.9 / 111.6, same RGB means); the weapon pose, enemies and particles match across all raster configurations. The freeze works in all three APIs.
- **Failure found and fixed:** the first smoke runs used `cmd_tmTick>=3` (INDEX literal) and the shell answered *Type mismatch*, so nothing froze; float literals fixed it. In one run of `tse-vol-2_4m1` (`vk-orig`) the camera was pitched down: when the window got focus, the engine re-centred the parked cursor and took the jump as mouse look. Since 19:15 the harness sets `inp_fMouseSensitivity=0.0`; that capture is marked *invalidated* in the ledger.
- **Fixed exposure** works only for RT. Interiors that RT leaves unlit stay black at a fixed exposure as well, so the problem is missing light rather than exposure (RDF-001).
- **Robustness:** across 65 runs before the ledger hook, the watchdog reported no hang or freeze, RTGL1 reported 0 errors and the validation layer reported 0 errors (the validation layer is off: `srt_bDebugValidation=0`). The window often did not have focus at capture time. That does not affect `PrintWindow` captures, but the inactive-window FPS limit applies, so the FPS overlay is not a benchmark.
- **Cost:** about 50 s per configuration run. A 7-configuration checkpoint takes about 6 min of GPU time, and a research pair (`vk-enh` + `rt-enh`) takes about 2 min.

## 3. Regression scene set (POC-89)

20 checkpoints (local file `scenes.csv`, level + coop marker + freeze time 3 s). They were picked from a raster survey of 37 marker views over 7 TFE and 9 TSE levels. None uses manually placed lights. Showcase levels appear only where an earlier report needs a re-check (`1_1` start).

| Id | Campaign / level | Scene types |
|---|---|---|
| `tse-out-1_3m10` | TSE 1_3_Teotihuacan | bright outdoors, sky/clouds, alpha-tested foliage, paving mips, sun flare |
| `tse-dark-1_3m20` | TSE 1_3_Teotihuacan | dark red interior, item models |
| `tse-corr-2_1m3` | TSE 2_1_Ziggurrat | torch-lit corridor, animated flame, weapon |
| `tse-room-2_2m1` | TSE 2_2_Persepolis | room, reflective floor, wall lights |
| `tse-part-2_2m20` | TSE 2_2_Persepolis | interior, item sparkle particles |
| `tse-vol-2_4m1` | TSE 2_4_TowerOfBabylon | room lit through openings, translucent light shafts |
| `tse-night-3_1m1` | TSE 3_1_GothicCastle | night sky + moon, lit windows (emissive), wet ground |
| `tse-cave-3_1m20` | TSE 3_1_GothicCastle | cave, torches |
| `tse-snow-3_2m1` | TSE 3_2_LandOfDamned | bright snow, sky, smoke particles |
| `tse-cave-3_2m18` | TSE 3_2_LandOfDamned | red cave, emissive |
| `tse-haze-3_3m5` | TSE 3_3_CorridorOfDeath | haze/fog corridor, light beam, sky |
| `tse-sky-1_1m0` | TSE 1_1_Palenque | level start under water, refracted sky (RDF-004/009/010) |
| `tfe-corr-03m8` | TFE 03_TombOfRamses | dark stair corridor |
| `tfe-room-04m6` | TFE 04_ValleyOfTheKings | room with wall torches |
| `tfe-out-06m2` | TFE 06_Oasis | bright outdoors, sky, palms, grass |
| `tfe-hall-06m5` | TFE 06_Oasis | large hall lit through openings |
| `tfe-water-09m5` | TFE 09_Sewers | under water, enemy model |
| `tfe-fog-10m6` | TFE 10_Metropolis | sunlit long view, distance haze |
| `tfe-night-12m1` | TFE 12_Karnak | night colonnade, star sky, torches |
| `tfe-dusk-15m5` | TFE 15_TheGreatPyramid | sunset sky, emissive, pickup particles |

HUD and weapon are visible in every checkpoint. Menus are covered by UI1 (POC-87). Decals, normals and shadows are compared implicitly; no checkpoint isolates them (see §8).

## 4. Results

Metrics are `mean luma / fraction of near-black pixels` of the frozen frame (1600×900 window, HUD included). Full 7-configuration runs were made for three TSE checkpoints, before owner directive #26. After the directive, the research sweep used `vk-enh` (raster reference with the same textures) and `rt-enh`.

### 4.1 Full matrix (7 configurations) [EXP]

| Checkpoint | cvk | vk-orig | vk-enh | gl-orig | gl-enh | rt-orig | rt-enh |
|---|---|---|---|---|---|---|---|
| `tse-out-1_3m10` | 111.6 / .003 | 111.6 / .003 | 111.0 / .003 | 115.2 / .003 | 113.2 / .003 | 141.9 / .006 | 136.5 / .013 |
| `tse-corr-2_1m3` | 33.9 / .063 | 33.9 / .063 | 34.3 / .056 | 34.7 / .062 | 33.2 / .074 | 1.8 / .974 | 1.7 / .974 |
| `tse-vol-2_4m1` | 39.4 / .311 | invalid¹ | 44.7 / .240 | 43.6 / .250 | 42.5 / .265 | 10.7 / .882 | 10.3 / .910 |

¹ Camera pitched by the mouse re-centre (§2.4). Re-run in §4.3.

- Raster configurations agree with each other (Classic-VK = SSTRE Vulkan exactly; OpenGL within ±4 luma, from the lens-flare/corona glow that only OpenGL draws: RDF-012). Enhanced vs original textures change luma by < 1.5 in all raster pairs. RT orig vs enh differ by ≤ 5.4. **No defect in this set depends on the texture pack**, so the defects are engine/RTGL1 defects, not asset-processing defects.
- RT vs raster: interiors lose 70–95 % of their brightness (RDF-001), the light shafts of `2_4` become opaque white boxes (RDF-002), outdoors are about 25 % brighter (RDF-013), and the first-person weapon is framed differently (RDF-011).

### 4.2 Research sweep, TSE (`vk-enh` / `rt-enh`) [EXP]

| Checkpoint | vk-enh | rt-enh | Visible differences |
|---|---|---|---|
| `tse-dark-1_3m20` | 21.6 / .191 | 23.7 / .334 | the red light colour of the room is lost; items dark (RDF-001) |
| `tse-room-2_2m1` | 47.4 / .103 | 3.9 / .874 | room black, only reflections visible (RDF-001) |
| `tse-part-2_2m20` | 36.8 / .080 | 1.5 / .978 | black; only sparkle particles visible (RDF-001); particles themselves present |
| `tse-night-3_1m1` | 51.4 / .007 | 43.4 / .094 | moonlight OK; lit windows/torches add no light; bluer (RDF-001) |
| `tse-cave-3_1m20` | 45.8 / .179 | 1.1 / .991 | black (RDF-001) |
| `tse-snow-3_2m1` | 98.4 / .005 | 161.7 / .002 | overbright snow (RDF-013) |
| `tse-cave-3_2m18` | 32.0 / .050 | 3.5 / .881 | black except an emissive rock (RDF-001) |
| `tse-haze-3_3m5` | 85.6 / .002 | 61.6 / .129 | haze missing (RDF-006); the blue light beam at the corridor end missing (isolation in §4.3) |
| `tse-sky-1_1m0` | 31.7 / .108 | 54.8 / .024 | no under-water tint (RDF-010), streaks in the refracted sky (RDF-004) |

No run hung, froze or flooded RTGL1 errors (watchdog ok, RTGL1 errors 0 in every run).

### 4.2b Research sweep, TFE (`vk-enh` / `rt-enh`) [EXP]

TFE worlds have Serious-Engine-RT's per-world tuning (migrated tables), TSE worlds only generic defaults. That difference shows:

| Checkpoint | vk-enh | rt-enh | Visible differences |
|---|---|---|---|
| `tfe-corr-03m8` | 27.0 / .234 | 15.1 / .531 | darker, but readable (RDF-001, milder); flashlight hint text (RDF-020) |
| `tfe-room-04m6` | 69.7 / .015 | 84.2 / .027 | lit correctly by the torches; flashlight hint (RDF-020) |
| `tfe-out-06m2` | 110.7 / .001 | 160.0 / .000 | overbright (RDF-013); **weapon drawn with a magenta/cyan checker texture (RDF-019)** |
| `tfe-hall-06m5` | 55.7 / .022 | 28.2 / .208 | half as bright, bluish (RDF-001/013 calibration); checker weapon (RDF-019) |
| `tfe-water-09m5` | 29.9 / .142 | 14.1 / .823 | green under-water tint gone, scene black except the enemy (RDF-010 in TFE too); checker weapon |
| `tfe-fog-10m6` | 123.2 / .001 | 143.3 / .007 | brighter (RDF-013) |
| `tfe-night-12m1` | 32.7 / .203 | 39.8 / .097 | comparable |
| `tfe-dusk-15m5` | 85.4 / .003 | 72.4 / .039 | comparable; sparkle particles present |

The checker weapon is not a renderer defect. The preview2 TFE runtimes ship three synthetic test override files for that weapon from the EXP-009 tests. They are byte-identical to the files E5 quarantined, and the VS-A runtime templates contain them too (RDF-019; file names local only).

### 4.3 Isolation runs

Expanded configurations only where a found defect needed isolating (directive #26):

| Question | Runs | Result |
|---|---|---|
| RDF-012: does `gfx_iLensFlareQuality=3` bring back the flare in Vulkan? | `tse-out-1_3m10` `vk-orig` + Extra | no: identical frame (luma 111.6); the setting is not the cause |
| RDF-021: is the missing beam an asset or renderer effect? | `tse-haze-3_3m5` `cvk`, `rt-orig` | beam in Classic-VK, missing in RT orig and enh: renderer |
| RDF-004/010: do the original textures change the refracted sky? | `tse-sky-1_1m0` `cvk`, `rt-orig` | streaks and missing water tint with original textures too: engine |
| RDF-002 harness re-run | `tse-vol-2_4m1-rerun` `vk-orig` | camera correct after the mouse fix; light shafts as in Classic-VK |
| RDF-019: does the TFE Classic runtime show the checker weapon too? | `tfe-out-06m2-iso` `rt-orig` | skipped: the byte-identity of the files (both TFE runtimes) already answers it; R1's TFE runtimes were quarantined afterwards (lead procedure), so later TFE RT runs carry revision `preview2@7eeed884+q-exp009` |

### 4.4 Performance observations (for E3/M1, not measurements)

The HUD FPS counter in the frozen frames shows what to expect; it is not a benchmark, since the window often lacks focus.
- RT at 1600×900: 25 FPS outdoors (`tse-out-1_3m10`), 37 FPS at night (`3_1`), 56–115 FPS in the dark interiors. Unlit interiors are cheap, so RD-016 lighting fixes will cost frame time; measure each fix.
- Vulkan raster reports about 144 FPS everywhere, while OpenGL reports 430–720 FPS. Vulkan defaults to `VK_PRESENT_MODE_FIFO_KHR` (`gfx_vk_iPresentMode = 0`, `Engine/Graphics/Vulkan/SvkUtils.cpp:416-421`), so it is vsync-limited by design. Vulkan raster benchmarks must set `gfx_vk_iPresentMode=2` (immediate) [SRC].

## 5. Defects filed

[`rendering-defects.md`](../rendering-defects.md) now has RDF-001..021. R1 added RDF-010..013 and RDF-019..021 from the sweep, and RDF-014..018 from lead relays (owner issues #28/#31, UI1). R1 also supplied root causes or [SRC] pointers for the seed entries RDF-002/004/006/007/009. The lead approved the owners on 2026-11-28.

| Severity | Count | Ids |
|---|---|---|
| S1 | 1 | 001 |
| S2 | 7 | 002, 003, 006, 011, 014, 016, 019 |
| S3 | 9 | 004, 005, 010, 012, 013, 015 (provisional), 017, 020, 021 |
| S4 | 3 | 007, 008, 018 |
| not a defect | 1 | 009 (wont-fix) |

| Owner | Ids |
|---|---|
| LIGHT | 001, 013 |
| FXT | 002, 003, 006, 010, 012, 021 |
| FXP | 005 |
| WPN | 011, 014, 015, 016 |
| UI1 | 008, 017, 018 |
| Integration | 019 |
| engine-other | 004 (proposal), 007, 020 |

Engine vs asset: all defects are engine/RTGL1 defects except RDF-019, a packaging defect. Every defect seen in both texture packs reproduces with original and enhanced textures alike (§4.1, §4.3), so none of them is an asset-processing defect.

## 6. Interpretation

- **The RT layer drops whole categories of SE1 information instead of translating them** [SRC]. Static invisible lights (RDF-001, LIGHT's inventory: 1249 dropped in `1_2`) are dropped, and so are fog/haze parameters (RDF-006/010: only a boolean "in haze" survives, mapped to water), polygon colour and translucency of brushes (RDF-002: translucent becomes alpha-tested, colour ignored), the weapon projection (RDF-011: computed, never used) and screen read-back (RDF-007). Each is a single code location with a universal fix; none needs per-level data.
- **TFE suffers less than TSE** because Serious-Engine-RT's TFE tables partly compensate per world. A universal fix must close the gap for TSE without double-counting in TFE (RD-016 rule).
- **Raster is consistent:** Classic-VK and SSTRE Vulkan are pixel-identical at the same frozen frame. OpenGL differs only by flares/coronas, which the Vulkan back-end loses (RDF-012, inherited from Classic-VK).
- **The enhanced textures introduced no visible defect** in 20 checkpoints. The only asset-side finding is a stray test file in packaging (RDF-019).

## 7. Impact on dossiers, ADRs and backlog

- RD-016: R1's interior checkpoints (`tse-corr-2_1m3`, `tse-room-2_2m1`, `tse-cave-3_1m20`, `tse-cave-3_2m18`, `tfe-corr-03m8`) are the regression set for P3-1..P3-3; LIGHT can run them with `-Configs cvk,rt-enh,fix -More @{FixBin=...; FixRev=...}`.
- RD-017 / ADR-0016: RDF-002/021 (translucent and additive classes) and RDF-006/010 (fog/haze as RT medium/compositing) belong in the semantic classification.
- POC-92 (Preview3 assembly): add a packaging gate against stray override files (RDF-019).
- E3 / M1: Vulkan raster benchmarks need `gfx_vk_iPresentMode=2` (§4.4); RT interiors will get slower once lit.
- Testing policy: the harness writes every run to the ledger and reuses earlier captures (`-Reuse`); the 20 checkpoints are the M0.1 regression scene set.

## 8. Not done / open questions

- **Coverage** (directive #26). Executed:
  - 21 full-matrix runs before the directive;
  - 34 research-pair runs (17 checkpoints × 2);
  - 37 survey runs (raster);
  - 6 isolation runs (2 more skipped, see §4.3);
  - 7 smoke runs.

  Invalidated: smoke1/2 (the freeze command failed), the `vk-orig` run of `tse-vol-2_4m1` (mouse) and the 3 TFE RT captures with the tommygun (RDF-019 test override), recorded as ledger entries that reference the invalidated run ids. Reused: none yet; the ledger hook exists since 19:20. Skipped: the full 7-configuration matrix on the 17 sweep checkpoints, which is reserved for the Preview3 candidate. Deferred: demos as checkpoints (the harness supports `-Demo`; no demo checkpoint is in the set yet), a community level (licensing not checked), decal and normal-map close-ups, menus (UI1).
- RDF-004 needs an A/B build: sky cubemap size and depth write of blended sky layers.
- RDF-012 needs a Vulkan query trace.
- RDF-015 (chainsaw) symptoms are still unknown.
- Owner-level: none.
