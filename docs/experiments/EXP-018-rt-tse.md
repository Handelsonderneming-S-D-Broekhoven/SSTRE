# EXP-018: Ray-tracing backend on TSE in Classic-VK (EXP-005 milestone M2) and a data-driven per-level RT table

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | POC-29 follow-up (EXP-005 M2: WP4, WP7 part, WP10 part; conditional C1) |
| Status | **partial** (M2 port met). TSE runs the RT backend on Windows with raster as the default and RTGL1 optional. The per-level table is data-driven and the TFE values are migrated. **Not done:** artistic tuning of the 13 TSE worlds (placeholders only), CMake/Linux, play sessions longer than 35 s, menu navigation to "Ray Tracing" (RT was selected through `sam_iGfxAPI`) |
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

The four RT-free TSE runs log no RT init. Totals: session A 13 runs, session B 15 runs (6 TSE without RTGL1, 6 TFE, 1 TFE validation, 1 TSE long run, plus the 2 sync steps). **0 crashes, 0 hangs.**

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

- **`d9f86637` stays in the branch base** (TFE `Graphics.cpp`), because `sprint2/rt-tse` was branched from `sprint2/rt-transplant` as instructed. It is not replayed onto TSE. The TSE tree therefore has the *unfixed* FilterBitmap; E4's fix applies to both trees, which is the integration track's job.
- **CustomInfo changes also touch the TFE tree** (`d1ddb552`), so the RT layer stays identical in both trees. TFE behaviour depends on `Scripts/RT/WorldTuning.txt` being present in the runtime. The sync script copies it, and the game-root template contains it.
- **GATE-05 note for the lead:** the committed `WorldTuning.txt` files contain game texture paths. They are the same 68 paths that are already in Serious-Engine-RT's public `CustomInfo.cpp`, moved from code into data, plus level names. TSE-specific paths are kept local only. Please review before export.
- **Menu:** the "Ray Tracing" entry is applied [SRC `SamTSE/Sources/SeriousSam/Menu.cpp`, `0a90724b`] but was not clicked through; RT was selected with `sam_iGfxAPI=2`.
- **Tooling:**
  - The agent shell again collapsed `\\` in inline heredocs, which caused one failed Python run. The scripts were then moved into files under `G:\sstre-tmp\e5\scripts`.
  - The first write of `CustomInfo.h` used CRLF on an LF file. It was converted back before the commit (verified with `file`).
  - A relative-glob `rm` was refused by the safety check. The E1 override files were moved, not deleted.
- **Interruption:** the agent run was paused by an API usage limit after the first TSE build (about 00:55). Wall-clock times below may contain part of that pause.

## Effort measurement vs EXP-005 M2

Wall-clock time of this AI-agent run, from `G:\sstre-tmp\e5\logs\timelog.txt` and commit times. Lock waiting is excluded. These are **not** person-days.

| WP (EXP-005) | M2 estimate (pd low/likely/high) | Measured | Output |
|---|---|---|---|
| WP4 replay onto TSE | 1 / 2 / 4 | **≈ 3 min** of patching (00:42 → 00:46), 7 commits, plus **12 min** to the first linked build (scripts, RTGL1 copy, 167 s build) | 0 conflict regions, 3 files by hand, 0 compile errors |
| C1 data-driven `CustomInfo` (conditional) | 3 / 5 / 8 | ≈ 10–20 min (design, about 400 lines of loader, constructor rewrite, generators, count check). Bounded by the 00:55 pause | 2 commits, 28 keys, TFE migration verified |
| WP7 TSE content (13 worlds plus texture lists) | 8 / 15 / 30 | **Not done**: placeholders only (≈ 2 min). One artefact identified | 13 placeholder sections |
| WP10 (part) validation | — | ≈ 10 min of locked runs (A) plus session B; about 25 min of queue waiting | 2 + 13 + 14 runs |

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
