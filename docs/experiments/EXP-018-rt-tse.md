# EXP-018: Ray-tracing backend on TSE in Classic-VK (EXP-005 milestone M2) and a data-driven per-level RT table

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | POC-29 follow-up (EXP-005 M2: WP4, WP7 part, WP10 part; conditional C1) |
| Status | **partial** (M2 port met). TSE runs the RT backend on Windows with raster as the default and RTGL1 optional. The per-level table is data-driven and the TFE values are migrated. **Not done:** artistic tuning of the 13 TSE worlds (placeholders only), CMake/Linux, active play (the longest RT run is a 160 s idle view), the Palenque culling probe, menu navigation to "Ray Tracing" (RT was selected through `sam_iGfxAPI`) |
| Environment | Windows 11 Pro 22631, i5-11600K, RTX 4070 12 GB, driver 616.64. VS 2022 17.5 (v143), Windows SDK 10.0.22000.0, Vulkan SDK 1.4.363.0 (validation layer), WinFlexBison 2.5.25. `/p:UseOfMfc=false` |
| Inputs | SSTRE-Engine `sprint2/rt-transplant` @ `005bd78c` (E1, EXP-009). RTGL1: E1's clean-room build (`sprint2/rtgl1-sstre` = `0eb4c4a`), DLL SHA-256 prefix `42bdd141`, copied with its 45 SPIR-V shaders into `G:\sstre-tmp\e5\rtgl1`. Game data: the owner's Steam *Serious Sam Classic: The Second Encounter* and *The First Encounter*, copied |

## How to reproduce (local paths; nothing is published)

- Worktree `G:\sstre-tmp\e5\wt-engine` on `sprint2/rt-tse`, checked out with `core.autocrlf=false`, as in EXP-009.
- Build: `powershell -File G:\sstre-tmp\e5\scripts\build-win.ps1 -Game TSE|TFE -Tag <t>`. It runs MSBuild `SamT?E.sln`, Release x64, with `RTGL1_SDK_PATH` and `RTGL1_LIB_PATH` set to `G:\sstre-tmp\e5\rtgl1`. TSE targets: Ecc, Engine, EntitiesMP, GameMP, Shaders, SeriousSam, ogg/vorbis, amp11lib.
- TSE runtime: `sh G:\sstre-tmp\e5\scripts\assemble-runtime-tse.sh` writes `G:\sstre-tmp\e5\runtime-tse`. It combines the Classic-VK `SamTSE` game-root template (minus `Sources`, `Tools.Win32`, `Bin` and `Mods`) with the owner's Steam TSE `*.gro` and `Help`. `Mods/` is excluded both from the template and from Steam, because it is third-party content.
- TFE runtime: `G:\sstre-tmp\e5\runtime-tfe`, a copy of E1's `runtime-tfe`. E1's synthetic weapon `.ktx2` override was moved out to `G:\sstre-tmp\e5\quarantine-e1-overrides`, so the TFE runs use no overrides. E1's runtime was not modified.
- Binaries: `powershell -File G:\sstre-tmp\e5\scripts\sync-bin.ps1 -Game TSE|TFE -Rtgl cleanroom|none`. It also copies `Scripts\RT\WorldTuning.txt`.
- Runs: `G:\sstre-tmp\e5\scripts\run-game.ps1`, E1's harness with the runtime and output paths changed. It captures the window only, records foreground state, always kills the game, and reports validation and RTGL1 error counts per run. Sessions: `session-a.ps1` and `session-b.ps1`, each run through `gpu-lock.ps1 run -Owner E5`.
- Command line: `SeriousSam.exe +script Scripts\sstre_run.ini +level Levels\LevelsMP\<world>.wld`, with `sam_iGfxAPI` = 0 (OpenGL), 1 (Vulkan) or 2 (RT); `sam_bFullScreen=0`; 1920×1080; `srt_bVSync=0`; `srt_bDebugValidation=0` except in the validation runs; master server set to 127.0.0.1; `cht_bGod=1; cht_bInvisible=1` for level runs. ESC is posted at 16 s to close NETRICSA, and captures are taken at 22 s and 32 s.

## Goal and success criteria

1. Apply the RT engine hooks to `SamTSE`. Port the entity hooks to `EntitiesMP`. Make RT selectable in the TSE exe and menu, keep raster as the default, and keep RTGL1 delay-loaded and optional exactly as for TFE.
2. Per-level RT tuning: make the hard-coded TFE tables data-driven if that is cheap, otherwise add TSE entries. Document what tuning means and which values are placeholders.
3. Tests under the GPU lock:
   - TSE menu and 3 campaign levels in RT, Vulkan and OpenGL;
   - RTGL1-absent fallback;
   - validation-layer error count;
   - TFE regression in all three APIs.
   Record focus loss and input interference.
4. Measure effort per work package against EXP-005's M2 estimates.

## Procedure

1. **Replay (WP4).** Each of E1's commits was exported with `git format-patch -1`. The paths were rewritten with `SamTFE/`→`SamTSE/` and `Entities/`→`EntitiesMP/`, then applied with `git apply --3way`. E1's `d9f86637` (FilterBitmap) was **not** replayed, because track E4 supersedes it. It remains in the base branch for the TFE tree only (see Deviations).
2. **Entity hooks.** HUD and Player hunks that did not apply were placed by hand at the equivalent TSE anchors.
3. **Data-driven table (C1, cheap variant).** New `Engine/Raytracing/CustomInfoTuning.cpp`, plus a constructor rewrite in `CustomInfo.cpp`. The TFE table was generated from the original C++ by `G:\sstre-tmp\e5\scripts\gen_tuning_tfe.py` and the TSE table by `gen_tuning_tse.py`.
4. **Builds:** TSE and TFE trees, Release x64.
5. **Locked runs:**
   - S0 smoke: 2 runs, 01:05.
   - Session A (TSE, RTGL1 present): 13 runs, 01:10:53 to about 01:21.
   - Session B (TSE with RTGL1 absent, then TFE regression): 14 runs.
6. **Image metrics:** E1's `imgstats.ps1` (MAD, PSNR, share of pixels with a difference > 8). It is called read-only from E1's script directory.

## Results ([EXP] unless labelled otherwise)

### R1. Port onto the TSE tree

| E1 commit (TFE) | Onto SamTSE | Conflicts |
|---|---|---|
| `2f9251dc` RT layer import (26 new files, +10.7k lines) | applied | 0 |
| `7c0fcf50` GAT_RT hooks (14 files: DrawPort, GfxLibrary, Gfx_wrapper, Texture, RenderModel*, Render, ShadowMap, Particles, Benchmark, Network) | applied **cleanly** | **0** regions (EXP-005 R4 predicted 41 for an apply against unmodified TSE; E1's resolutions carry over, because the touched files are identical between the trees) |
| `e62b6fcc` runtime optionality | Adapter.cpp and the loader applied cleanly. **`Engine.vcxproj` did not apply**: TSE's `PreprocessorDefinitions` lack `FIRST_ENCOUNTER`, so the context differs. The 6 edits were re-applied by a script | 1 file by hand |
| `7d80a7d7` game exe, `750b1047` menu and `RenderingOptions.cfg`, `005bd78c` RTGL1 error logging | applied cleanly | 0 |
| `1fd1cd9f` entity hooks → `EntitiesMP` | `PlayerWeapons.es` applied cleanly. `Player.es` and `Common/HUD.cpp`: the 3-way merge produced two large spurious conflict regions, because TSE's shell declarations use `(void *)` casts and declare more controls. The 5 hunks were placed by hand at the same logical anchors; the logic is unchanged | 2 files by hand |

- **The first TSE build after the replay linked on the first attempt:** exit 0, 0 errors, 167 s for the 10 targets. No compile fix was needed. The RT layer does not depend on `FIRST_ENCOUNTER` and refers to no TFE entity class beyond `"Player"` [SRC `Raytracing/RTLights.cpp:59`; grep for `FIRST_ENCOUNTER` in `Raytracing/` returns 0 hits].
- **Port-surface difference against EXP-005 R4(c).** R4(c) predicted 6 of 15 entity hunks rejected. Measured: 2 files hand-placed, 5 hunks; no hunk needed a logic change.
- **Extra fix for TSE: flashlight binding.** Classic-VK TSE's default controls bind F to Down/Duck, so RT's "Flashlight" button was added to `Controls/00-Default.ctl` on **L** (`bf625709`). The TFE tree has no flashlight binding either. That gap is inherited from E1 and not fixed here.
- **Not ported (UX-only, same as for TFE):** Eyeman invisibility shading and WeaponPositions/FOV tweaks.

### R2. Data-driven per-level RT tuning

- **Before [SRC `CustomInfo.cpp` @ `005bd78c`]:** 15 TFE worlds were hard-coded as an `EWorld` enum. They fed:
  - 4 tables (illumination, world parameters, World Base brushes to ignore, directional lights to ignore);
  - 17 texture-path arrays;
  - 10 `switch (eCurrentWorld)` blocks (ignored or masked polygons and sectors, cutscene lights, animated sun, flashlight hint, light threshold, water extinction, sky type, haze, reflect-water, haze-ignored sectors).
  A world without an entry got generic defaults and the console warning "LEVEL THAT WAS NOT MODIFIED FOR RAY TRACING".
- **After:** `Scripts/RT/WorldTuning.txt` (plus an optional `WorldTuning.local.txt`) is read through the engine file system at level start, so it also works from `.gro` archives. The format has three section types:
  - `[defaults]`;
  - `[world <WorldFileName>]` with `key = value` lines (28 keys; list keys are repeatable);
  - `[textures <category>]`, one path per line.
  Unknown keys or sections are reported on the console. A missing file falls back to the generic defaults with a console note.
- **Still in code:** the position-dependent or game-state-dependent hooks, keyed by the TFE world name. They never match TSE worlds:
  - Great Pyramid sky and boss animation, Metropolis-on-Serious lighting, Moon Mountains reflections;
  - cull masks per camera position (`GetCullMask`), ray length, Sand Canyon and Luxor light special cases.
- **TFE migration:** 15 worlds, 224 keys and 68 texture paths in 17 classes, generated mechanically from the original source. An independent count check of every list against the original matches:

  | List | Count |
  |---|---|
  | Ignored polygons | 75 |
  | Ignored sectors | 4 |
  | Ignored ranges | 10 |
  | Masked polygons | 10 |
  | Masked sectors | 8 |
  | Masked ranges | 7 |
  | Cutscene lights | 23 |

  Order-sensitive overrides keep their original order: Metropolis-on-Serious and Great Pyramid are applied after the table.
- **TSE table:** a `[world …]` section for each of the 13 campaign worlds (`1_0_InTheLastEpisode` … `3_3_CorridorOfDeath`). All have `tuned = 0`, and an explicit `[defaults]` restates RT's generic values. **Every TSE world value is a placeholder [ASM].** The TFE texture class lists are reused: 54 of the 68 TFE paths exist in the TSE data (aggregate scan of the owner's `.gro` files). Absent paths are harmless, because a lookup simply misses, as in the original code.
- **Runtime check:** each TSE RT level logs `RT tuning: Scripts\RT\WorldTuning.txt: 15 values applied for '<world>'` (14 defaults plus `tuned`), followed by the expected warning.
- **What "tuning" means** is documented in the TSE file header:
  - illumination;
  - `culling_max_sector_depth`;
  - polygon, sector and World Base suppression, with indices from the level editor;
  - cutscene lights, sun animation, flashlight, haze, sky type, water;
  - texture classes.
- **Showcase worlds (lead request):** `1_0_InTheLastEpisode` and `1_1_Palenque` have explicit, conservative entries (`f71bd2cc`):
  - culling depth 8, the top of TFE's range, which favours complete geometry over speed;
  - the default light threshold (2), haze on, geometry sky;
  - no flashlight hint, because the template's player control profiles lack the new L binding.
  The observed state and the Palenque artefact are written into the table as comments. Both stay at `tuned = 0` [ASM: these are not play-tested values]. All keys in both tables were checked offline against the loader's key set: 0 unknown keys.
- **Local-only overlay (GATE-05):** a file-name heuristic found TSE water/fire candidates (2/0). They are written to the runtime's `WorldTuning.local.txt` only, unreviewed, and not committed.

### R3. Test matrix

All runs are OK: the process was still running and responding at the end, and levels logged `started.`. No crash and no hang.

| Build / API | Menu | 1_0_InTheLastEpisode | 1_1_Palenque | 2_1_Ziggurrat |
|---|---|---|---|---|
| TSE, RTGL1 present, **RT** | OK, RT context created | OK (load; ESC opened the game menu, because the level has an intro and no NETRICSA) | OK, path-traced gameplay view, HUD and weapon. HUD ≈ 58 FPS | OK, gameplay view ≈ 41 FPS |
| TSE, RTGL1 present, **Vulkan** | OK | OK | OK, ≈ 144 FPS | OK |
| TSE, RTGL1 present, **OpenGL** | OK | OK | OK, ≈ 390 FPS | OK |

| TSE, RTGL1 **absent**, Vulkan | OK | — | OK | — |
| TSE, RTGL1 absent, OpenGL | OK | — | OK | — |
| TSE, RTGL1 absent, **RT requested** | OK, log: `Ray tracing unavailable: RayTracedGL1.dll not found` → `Cannot start ray tracing` → `Trying recovery mode 0...` → `Vulkan context created` | — | OK, falls back to Vulkan raster | — |
| **TSE RT, long run** | — | — | — | OK, **160 s** in RT. Captures at 30/60/90/120/150 s are all live (weapon idle animation changes, HUD ≈ 44 FPS at 150 s). Idle view, god mode, no movement input |
| **TFE regression**, RT | OK | — | — | `01_Hatshepsut` OK. Log: `RT tuning: Scripts\RT\WorldTuning.txt: 17 values applied for '01_Hatshepsut'`, no "not modified" warning, so the migrated table is used |
| TFE regression, Vulkan | OK | — | — | `01_Hatshepsut` OK |
| TFE regression, OpenGL | OK | — | — | `01_Hatshepsut` OK |

The four RT-free TSE runs log no RT init. Totals: session A 13 runs, session B 14 runs (6 TSE without RTGL1, 6 TFE, 1 TFE validation, 1 TSE long run). **0 crashes, 0 hangs.**

- **Vulkan vs OpenGL on the same frames:**

  | Level | MAD | PSNR | Pixels > 8 |
  |---|---|---|---|
  | 2_1_Ziggurrat | 1.2 | 33.5–34.5 dB | 0.7 % |
  | 1_0_InTheLastEpisode (menu frame) | 2.4–2.6 | — | 3–4 % |
  | 1_1_Palenque | 7.4–9.7 | — | — |

  The larger Palenque difference comes from animated foliage and sky and from weapon bob (visual check of the two frames).
- **RT vs Vulkan:** MAD 28–35 on gameplay frames, which is expected for a different renderer.
- **First observed TSE RT tuning artefact:**
  - What: in `1_1_Palenque` RT shows sky where raster draws the distant hillside and trees.
  - Why [ASM]: background geometry or World Base handling that TFE solved per level.
  - It is a concrete first target for WP7.
- **FPS:** single HUD readings, indicative only. RT ran with the validation layer off.

### R4. Validation layer (RT, `1_1_Palenque`, `srt_bDebugValidation=1`)

**45 errors, 6 distinct VUIDs**, plus 1 warning:

| VUID | Count | Also in TFE (EXP-002/009)? |
|---|---|---|
| `VUID-vkCmdTraceRaysKHR-mipmapMode-04770` | 10 (limit) | yes |
| `VUID-vkCmdDispatch-mipmapMode-04770` | 10 (limit) | yes |
| `VUID-vkCmdBuildAccelerationStructuresKHR-pInfos-10126` | 10 (limit) | yes |
| **`VUID-vkCmdCopyBuffer-pRegions-12482`** | 10 (limit) | **new** |
| `UNASSIGNED-non-acquired-swapchain-image-used` | 3 | yes |
| `VUID-vkQueueSubmit-pSignalSemaphores-00067` | 2 | yes |

- The new error is overlapping destination regions in a single `vkCmdCopyBuffer`: identical 216-byte ranges, which is a write-after-write hazard.
- In RT mode the engine issues no Vulkan calls itself; all Vulkan work goes through RTGL1. So this is an RTGL1 v1.1.0 upload path triggered by TSE content [ASM].
- **The TFE control confirms it is TSE-specific.** The same build on TFE `08_Suburbs` (session B, `srt_bDebugValidation=1`) logs **35 errors, 5 VUIDs**, exactly EXP-009's set, and no `vkCmdCopyBuffer` error.
- No RTGL1 API errors (`RTGL1 error …`) were logged in any run.

### R5. Focus and input

- Every capture recorded the game window in the foreground (`FOCUS=…:True`).
- The owner's mouse cursor highlighted a menu item in at least 2 captures ("MODS" in the S0 menu and "HIGH SCORES" in the 1_0 game menu).
- No keystrokes are known to have reached a level run.
- The S0 smoke ran concurrently with this track's own TFE build (CPU load), so its timings are not usable. No timing claims are made from it.

## Deviations, modifications and failures

- **Palenque culling-depth probe not run.** The planned probe (session C, `G:\sstre-tmp\e5\scripts\session-c.ps1`: depth 16 and 32 on Palenque, plus 1_0 intro captures in RT vs Vulkan) would have waited behind four lock holders.
  - The first attempt's lock job never took a queue ticket and was stopped. The second was cancelled while queued, and nothing ran.
  - The lead asked for a report as soon as the definition of done held, so the probe is a follow-up.

- **`d9f86637` stays in the branch base** (TFE `Graphics.cpp`), because `sprint2/rt-tse` was branched from `sprint2/rt-transplant` as instructed. It is not replayed onto TSE. The TSE tree therefore has the *unfixed* FilterBitmap; E4's fix applies to both trees, which is the integration track's job.
- **CustomInfo changes also touch the TFE tree** (`d1ddb552`), so the RT layer stays identical in both trees. TFE behaviour depends on `Scripts/RT/WorldTuning.txt` being present in the runtime. The sync script copies it, and the game-root template contains it.
- **GATE-05 note for the lead:** the committed `WorldTuning.txt` files contain game texture paths. They are the same 68 paths that are already in Serious-Engine-RT's public `CustomInfo.cpp`, moved from code into data, plus level names. TSE-specific paths are kept local only. Please review before export.
- **Menu:** the "Ray Tracing" entry is applied [SRC `SamTSE/Sources/SeriousSam/Menu.cpp`, `0a90724b`] but was not clicked through; RT was selected with `sam_iGfxAPI=2`.
- **Tooling:**
  - The agent shell again collapsed `\\` in inline heredocs, which caused one failed Python run. The scripts were then moved into files under `G:\sstre-tmp\e5\scripts`.
  - The first write of `CustomInfo.h` used CRLF on an LF file. It was converted back before the commit (verified with `file`).
  - A relative-glob `rm` was refused by the safety check. The E1 override files were moved, not deleted.
- **Interruption:** the agent run was paused by an API usage limit after the first TSE build (about 00:55). Wall-clock times below may contain part of that pause.

## Branches and commits (local, not pushed)

SSTRE-Engine `sprint2/rt-tse`, based on `sprint2/rt-transplant` @ `005bd78c`, 11 commits, head `f71bd2cc`:

| Commit | Subject |
|---|---|
| `adc4f40c` | rt(engine,tse): import the ray-tracing layer into the TSE engine tree |
| `2b0cfa04` | rt(engine,tse): port the GAT_RT hooks into the TSE graphics/render code |
| `d2ef76d1` | rt(engine,tse): make ray tracing runtime-optional in the TSE engine |
| `c7d53e1e` | rt(game,tse): select GAT_RT at runtime in the TSE game exe |
| `0a90724b` | rt(menu,tse): offer "Ray Tracing" as a graphics API in the TSE menu |
| `d9e505d1` | rt(engine,tse): log failed RTGL1 calls in release builds (TSE) |
| `61668251` | rt(entities,tse): port the RT entity hooks to EntitiesMP |
| `bf625709` | rt(controls,tse): bind the RT flashlight in the default TSE controls |
| `938ba5ab` | rt(engine,tse): load per-world RT tuning from Scripts/RT/WorldTuning.txt |
| `d1ddb552` | rt(engine,tfe): use the runtime RT tuning table in the TFE tree too |
| `f71bd2cc` | rt(data,tse): explicit RT entries for the showcase worlds 1_0 and 1_1 |

All commits carry the `Co-Authored-By` trailer and no `Signed-off-by`. New files carry the SSTRE GPL-2.0-only notice; upstream and RT author notices are kept. No patches were exported (that is the integration track's job).

## Effort measurement vs EXP-005 M2

Wall-clock time of this AI-agent run, from `G:\sstre-tmp\e5\logs\timelog.txt` and commit times. Lock waiting is excluded. These are **not** person-days.

| WP (EXP-005) | M2 estimate (pd low/likely/high) | Measured | Output |
|---|---|---|---|
| WP4 replay onto TSE | 1 / 2 / 4 | **≈ 3 min** of patching (00:42 → 00:46), 7 commits, plus **12 min** to the first linked build (scripts, RTGL1 copy, 167 s build) | 0 conflict regions, 3 files by hand, 0 compile errors |
| C1 data-driven `CustomInfo` (conditional) | 3 / 5 / 8 | ≈ 10–20 min (design, about 400 lines of loader, constructor rewrite, generators, count check). Bounded by the 00:55 pause | 2 commits, 28 keys, TFE migration verified |
| WP7 TSE content (13 worlds plus texture lists) | 8 / 15 / 30 | **Not done**: placeholders only (≈ 2 min). One artefact identified | 13 placeholder sections |
| WP10 (part) validation | — | about 32 min of locked runs (S0 1 min, A ≈ 11 min, B ≈ 19 min including the 160 s run), plus about 50 min of queue waiting (excluded) | 2 + 13 + 14 runs |

- **Recalibration [ASM]:** WP4 is effectively free once the TFE port exists. The TFE and TSE engine files are identical, so E1's 39 resolutions carry over unchanged. Keep WP4 at ≤ 0.5 pd for human planning. C1's cheap variant (data only, position-dependent hooks kept in code) is well below its estimate.
- **The M2 cost is now almost entirely WP7:** per-level artistic tuning with play-testing, plus finding polygon and sector indices in the editor. It is unchanged by this work, except that it no longer needs engine rebuilds: tuning means editing a text file and reloading the level.

## Interpretation

- [EXP] EXP-005's R5 claim holds in practice. The TSE port is a mechanical replay of the TFE transplant, and RT works for TSE campaign levels with raster as the default.
- [EXP] Untuned TSE levels are playable in RT, but show at least one geometry and background artefact. The "works, untuned" quality bar (EXP-005 open question 1) is met; "tuned parity with TFE" is not.
- [ASM] The new `vkCmdCopyBuffer` VUID suggests that TSE content exercises an RTGL1 path that TFE does not. It is a candidate for the RTGL1 VUID cleanup item.

## Impact on ADRs, dossiers and backlog

- **ADR-0005:** the transplant acceptance now also holds for TSE on Windows.
- **ADR-0007:** RT stays runtime-optional for TSE (see R3 and session B).
- **Backlog, suggested items:**
  - WP7 TSE RT tuning per world, now in data, with an owner-set quality bar;
  - a flashlight binding for TFE;
  - a reload command for the tuning table (currently read at RT scene creation);
  - RTGL1 `vkCmdCopyBuffer` overlap (new VUID);
  - harness support for intro and menu-aware captures;
  - a decision on unifying the TFE and TSE engine trees (the RT layer is now byte-identical in both).

## Open questions

1. What quality bar applies to TSE RT (EXP-005 open question 1)? Placeholders are in place; tuning 13 worlds is the remaining M2 cost.
2. Do the texture paths in the committed tuning tables (already public in the RT upstream source) pass GATE-05 for patch export, or should they move to a local file as well?

## Addendum A1 (2026-11-28): TSE "dark beyond ~20 m" in RT, root cause and fix

**Owner playtest finding:** in TSE under RT, beyond a radius of roughly 20 m around the player everything was pitch dark, so distant enemies and geometry were invisible.

### Root cause

**[SRC] The mechanism:**

1. `RT_CheckViewerInHaze` (`Raytracing/RTModelCulling.cpp:268-300`) marks the camera as "in haze" when it is inside any brush sector whose entity reports SE1 **haze or fog** (`GetHaze(...) || GetFog(...)`).
2. `Scene::IsCameraInHaze` (`Scene.cpp:211-213`) returns that flag only if the world allows haze (`CustomInfo::CanHazeBeApplied`, the tuning key `haze`). This is its only consumer.
3. `SSRT.cpp:652` then sets `typeOfMediaAroundCamera = RG_MEDIA_TYPE_WATER`. The whole frame is rendered as if the camera were under water.
4. RTGL1 attenuates every camera path by `exp(-distance * waterExtinction)` [SRC RTGL1 `Source/Shaders/Media.h:40-52`]. With the default extinction `(0.025, 0.016, 0.011) × water_density_multiplier 5` = 0.125 / 0.08 / 0.055 per metre:

   | Distance | Transmittance (R / G / B) |
   |---|---|
   | 20 m | 8 / 20 / 33 % |
   | 40 m | 0.7 / 4 / 11 % |

   That is a bluish fade to black that matches the reported ~20 m radius.

**Why TFE does not show it [SRC]:** Serious-Engine-RT's TFE tables disable haze on 7 outdoor worlds and keep it on the others only together with `haze_ignored_sectors` lists. The TSE table (R2) inherited RT's generic default, `haze = 1`, for every world, and TSE worlds use sector fog and haze widely.

**Other candidates:**

- [EXP] Missing exports are excluded for the tested views: with `haze = 0` the same geometry appears at full brightness.
- [SRC] Ray length is special-cased only for TFE Luxor (`CustomInfo::GetRayLength`).
- [ASM] Sector culling depth (8, the top of TFE's range) was not varied in this addendum. It cannot cause a distance *darkening*, only missing surfaces.

### Experiments (session D 02:44–02:51, E 03:02–03:08, F 03:13–03:24, 2026-11-28)

Paired captures at fixed views: Vulkan reference, RT with `haze = 1`, RT with `haze = 0`. Haze was toggled through the local tuning overlay. Same build, same position, 24 s after level start.

| View | VK mean RGB | RT haze 1 mean RGB | RT haze 0 mean RGB | haze 1 vs haze 0 |
|---|---|---|---|---|
| `2_1_Ziggurrat` spawn (dry stone hall, far wall about 15–20 m) | 63/61/67 | **70/95/113**: blue cast, far wall dimmed | **120/130/137**: natural colour, far wall lit | MAD 36.5, 95 % of pixels differ |
| `1_1_Palenque` spawn | 14/38/47 | 39/53/58 | 39/53/58 | no change (see below) |
| `1_0_InTheLastEpisode` intro cutscene (session E) | — | — | — | brightness unchanged; the differences come from cutscene timing. The intro camera is not in a fog sector |

| **Demo 3 (`3_1_GothicCastle`, `PlayDemo("auto-demo0003")`), 15 s, identical demo frame (same HUD and score)** | — | **48/51/58: cliffs and castle beyond ≈ 20 m pitch black**, only the near ground and the sky are lit (the reported symptom) | **83/82/81: cliffs, castle and distance fully lit** | MAD 32.1, 69 % of pixels differ |
| Demo 3, 35 s | — | 7/9/9 | 25/24/18 | MAD 14.0 |
| Demo 2 (`2_2_Persepolis`), 15 / 25 / 35 s | — | — | — | MAD 23.6 / 45.8 / 0.4. Brightness is similar, so the camera is mostly outside fog sectors |

- The Vulkan demo frames are not time-aligned with RT: RT loads more slowly, so the same wall-clock second shows a different demo moment. The comparison that counts is RT haze 1 against RT haze 0, which is frame-identical (same RT load time).
- **New failure, not caused by the fix:** demo 1 (`1_2_Palenque`) under RT logs a flood of `RTGL1 error 8 (RG_CANT_UPDATE_TRANSFORM)` and `Can't find static geometry with unique ID=…` [SRC `SceneBrushes.cpp:269`]. RT tries to move brushes it registered as static.
  - With haze 1 the process hung and was killed at 163 s; with haze 0 it exited with code 1 at 15 s.
  - Vulkan plays the same demo normally.
  - This is a follow-up: moving brushes in TSE worlds that the RT exporter treats as static [ASM]. It was not seen in the slice levels' fixed views.

- The **Ziggurrat A/B isolates the cause**: the only change is the `haze` flag, which has one consumer (the water-media switch). `haze = 0` removes the blue cast and the distance darkening.
- **Correction to R3:** the Palenque "RT shows sky where raster shows the hillside" observation is **not** a geometry or culling defect.
  - The player starts **under water** in the pool: bubbles are visible in both raster and RT.
  - Raster draws the scene above the surface without refraction. RT refracts through the water surface, so it shows sky and hanging plants. This is RT behaving physically, not a bug.
  - It also explains why the haze A/B makes no difference at that spot: the camera is genuinely in water there.
- Test-method failures:
  - The `cht_iGoToMarker=2` views respawn the player without NETRICSA, so the scripted ESC opened the game menu. Those 6 captures are unusable.
  - The first demo attempt (session E) used a wrong `PlayDemo` argument; the correct form is the bare name, e.g. `PlayDemo("auto-demo0001")`.

### Fix

- `4e1053be` rt(data,tse): TSE `[defaults]` now sets **`haze = 0`**, and so do the two showcase worlds. It is a generic default, not a per-level hack, and needs no engine change. The TFE tables are unchanged.
- **Consequence [ASM]:** SE1 sector fog and haze are not reproduced in RT at all for TSE. The raster look has distance fog; RT then has none.
  - A proper mapping (SE1 fog/haze colour and distance → an RTGL1 volumetric or extinction parameter with media type "haze" instead of "water") is a follow-up engine item.
  - Per-world opt-in stays possible with `haze = 1` plus `haze_ignored_sectors`, as in TFE.
- **Slice levels:** `1_0_InTheLastEpisode` and `1_1_Palenque` now have explicit entries with `haze = 0`, and the comments record the findings above. Both stay at `tuned = 0` (not play-tested).

### Effort (agent wall-clock)

About 15 min of source analysis and fix, plus about 25 min of locked runs (sessions D, E and F: 33 runs), plus about 45 min of lock queue waiting (excluded).

### Follow-ups (from A1)

1. Map SE1 fog and haze to an RT effect that is not water, for example a light extinction or volumetric term derived from `CHazeParameters` and `CFogParameters`, so TSE regains its distance fog without the darkness.
2. `1_2_Palenque`: `RG_CANT_UPDATE_TRANSFORM` (movable brushes exported as static), then an exit or hang under RT during demo playback.
3. Harness: views from `cht_iGoToMarker` skip NETRICSA, so the scripted ESC must be omitted for them.

## Addendum A2 (2026-11-28): TSE `1_2_Palenque` in RT, transform-update errors and crash, root cause and fix

**Symptom (A1, session F):** demo 1 (`1_2_Palenque`) under RT logged `Can't find static geometry with unique ID=…` / `RTGL1 error 8 (RG_CANT_UPDATE_TRANSFORM)` from `SceneBrushes::SetMovableNewTransform`, then exited or hung. A1's guess "movable brushes exported as static" [ASM] is **wrong**; there were two independent defects.

### Cause 1: RTGL1 geometry capacity exceeded silently [SRC + EXP]

- [SRC] RTGL1 has a fixed capacity of `MAX_BOTTOM_LEVEL_GEOMETRIES_COUNT` = 4096 bottom-level geometries in total (static plus the dynamic geometry of each frame), plus 1 M static vertices and 1 M indexed triangles. `VertexCollector::AddGeometry` returns "no index" beyond that (only an `assert`, compiled out in release); `Scene::Upload` then returns `false`, and `rgUploadGeometry` ignores that and returns `RG_SUCCESS`. The engine therefore recorded IDs that RTGL1 never stored.
- [SRC] The engine's brush exporter (`RTBrushes.cpp`) cut a new geometry at every material-state change between *consecutive* polygons of one sector, and at every sector boundary.
- [EXP] Temporary debug counters in `SceneBrushes::RegisterBrush` (one demo-1 run, removed afterwards): `1_2_Palenque` produced **5127 static brush geometries** (≈ 10 vertices each; 274 movable parts). **Every failing ID was registered after geometry #4096, and no movable part before #4096 failed** (first failure at #4311). Hypothesis (b) "upload rejected silently" confirmed; (a) part-index mismatch and (c) reload ordering ruled out: the part indices of upload and update were identical.
- Consequences beyond the log flood [SRC]: about 1000 static world parts were missing from the RT scene, and no slots were left for dynamic geometry (models, particles).

### Cause 2: null scene in the RT particle path, TSE chainsaw [SRC + EXP]

- [EXP] With cause 1 fixed, demo 1 ran without errors but crashed at 112 s: Windows Application event 1000, `0xc0000005` in `Engine.dll`, offset `0x1922d8`. The linker map resolves it to `RT_GetViewVectors` (`RTParticles.cpp`). The demo's capture at 110 s shows the player using the chainsaw.
- [SRC] TSE's `Player.es` (`RenderHUD`) draws first-person chainsaw particles in the HUD pass (`Particle_PrepareEntity(…, this)` then `RenderChainsawParticles`). Under GAT_RT `Particle_RenderSquare` goes to `RT_Particle_RenderSquare`. `RT_GetViewVectors` checked only `_Particle_penCurrentViewer` before dereferencing `RT_sCurrentScene`, which is set only inside `RT_AddParticlesForEntity` and is null there. TFE has no chainsaw, so it never took this path.
- This is hypothesis (d): the exit/hang was not a consequence of the error flood.

### Fix (SSTRE-Engine `sprint2/rt-tse`)

| Commit | Change |
|---|---|
| `1c59be04` | **Root cause 1:** `RTBrushes.cpp` collects the polygons of all active sectors of a brush entity and groups them by the existing batching key (textures, blending, polygon flags, visibility mask, mirror/warp, media flag), keeping the polygon order inside a group. The grouping is deterministic, so the `brushPartIndex` sequence is identical in the upload, tex-coord and rasterized passes. **Mitigation (in addition):** `SceneBrushes` tracks RTGL1's static budget with RTGL1's own accounting (geometries with 1024 slots reserved for dynamic geometry, vertices, indices). It does not upload parts that would be dropped, never records movable or tex-coord parts that were not uploaded (also on a non-success result), and prints one console line if anything was dropped. |
| `958b2bd5` | **Root cause 2:** `RT_GetViewVectors` also requires the scene; `RT_Particle_RenderSquare/RenderLine/RenderQuad3D` return early without one. Such particles were never flushed anyway, so the visible output is unchanged. |

- Both commits change the **TSE and the TFE tree**: the four RT files were byte-identical in both trees.
- Effect on `1_2_Palenque` [EXP]: **5127 → 1405** static geometries, the same 79 176 indices (no triangle lost), 0 parts dropped by the budget.

### Verification [EXP]

Release x64 builds, clean-room RTGL1, window captures with focus recorded (focus held in every capture), harness watchdog active (no kills). `RTGL1_ERRORS` = count of logged failed RTGL1 calls; validation was off.

| Run | Build | API | Duration | Result | RTGL1 errors |
|---|---|---|---|---|---|
| Demo 1 baseline (debug counters) | pre-fix + counters | RT | hung, 205 s | the error pairs, hang | 18 |
| Demo 1 | `1c59be04` | RT | 60 s | correct rendering, no errors | 0 |
| Demo 1 | `1c59be04` | RT | 112 s | **access violation** (cause 2) | 0 |
| `1_2` level start | `1c59be04` | RT | 100 s | quit with code 1 (normal WinMain return, no crash event); **not reproduced** in two later 195 s runs [ASM: external input, the window had focus] | 0 |
| **Demo 1** | `958b2bd5` | RT | **195 s** (to the end of the run; past the chainsaw) | OK, responsive | **0** |
| **`1_2` level start** | `958b2bd5` | RT | **195 s**, twice | OK, responsive | **0 / 0** |
| `1_1_Palenque` | `958b2bd5` | RT | 70 s | OK; mean RGB 39/52/58 = A1 value | 0 |
| `2_1_Ziggurrat` | `958b2bd5` | RT | 70 s | OK; mean RGB 121/131/138 = A1 haze-0 value | 0 |
| TFE `01_Hatshepsut` | `958b2bd5` (TFE tree) | RT | 70 s | OK; mean RGB as session B | 0 |
| Demo 1 | `958b2bd5` | Vulkan | 195 s | OK | 0 |
| `1_2` level start | `958b2bd5` | Vulkan | 120 s | OK (reference) | 0 |

- **`1_2` spawn is black in RT, not a regression:** the level starts in a cave. Vulkan shows it dimly lit (mean RGB 17/23/16); RT shows a flat near-black frame. With the RT flashlight on, the cave geometry and the weapon appear, and the pre-fix engine (`4e1053be`, swapped in for one run) is equally black (2/1/0). The cave relies on SE1 light that has no RT equivalent; this is per-level tuning work (WP7), not an export defect.
- The flood is gone in both routes; the earlier "hang" with haze 1 and the "exit at 15 s" with haze 0 (A1, session F) were not reproduced with the fixed builds.

### Effort (agent wall-clock)

About 35 min of source analysis, fix and builds (RTGL1 source read to confirm the silent drop), plus about 30 min of locked runs (1 debug, 1 + 6 + 3 + 2 + 5 runs), plus lock-queue waiting (excluded).

### Follow-ups (from A2)

1. RTGL1 (upstream behaviour): `rgUploadGeometry` should return an error when the geometry is dropped. That is a change in the RTGL1 tree, not in the engine; the engine-side budget guard covers it meanwhile.
2. First-person chainsaw particles are not drawn in RT. They would need an RT-side first-person particle path.
3. `1_2_Palenque` (and other cave starts) need RT lighting tuning; together with A1 follow-up 1 (fog/haze mapping) this is WP7 work.
4. The engine-side budget reserves 1024 geometry slots for dynamic geometry; very model-heavy scenes could still exceed RTGL1's shared total per frame. Not observed so far.
