# EXP-009: RT transplant spike into Classic-VK (TFE, Windows x64) and KTX2 reader render test

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | POC-29 (RT transplant spike), POC-30 (clean-room KTX2 reader render test) |
| Status | **partial** (M1 core met) — TFE RT transplant builds and runs with raster as default and RT selectable at runtime; RTGL1 is optional at runtime. Not done: CMake/Linux build of the RT code, DLSS/FSR menus, TSE, 10-minute play, frame-time benchmark |
| Environment | Windows 11 Pro 22631, Intel i5-11600K, RTX 4070 12 GB, driver 616.64 (Vulkan 1.4.351), desktop 3440×1440 @125 %. VS 2022 17.5 (MSVC 14.35.32215, v143), Windows SDK 10.0.22000.0, Vulkan SDK 1.4.363.0, CMake 4.4.4, Ninja 1.13.2, WinFlexBison 2.5.25. No MFC (`/p:UseOfMfc=false`) |
| Inputs | Engine: SSTRE-Engine `phase1/cvk-build` (`ba0c12e8` = Classic-VK `510d36f` + 6 Windows build commits). RT source: local `upstream/rt-main` = Serious-Engine-RT `0e7f223c`, fork point `77a955ba`, RT-only patch from EXP-005 probe (b). RTGL1: `phase1/rtgl1-v1.1.0-sdk1.4` (`4bcf13e`) and track K's `sprint2/ktx2-cleanroom` (`0eb4c4a`). Game data: owner's Steam *Serious Sam Classic: The First Encounter*, copied |

## How to launch the transplant build (for the benchmark and AI tracks)

All paths are local; nothing is published. Hold the GPU lock (`G:\sstre-tmp\gpu-lock.ps1`) for every run.

- Runtime: `G:\sstre-tmp\engine\runtime-tfe` (Classic-VK game-root template + copies of the owner's Steam TFE `*.gro`, `Levels`, `Help`, `Demos`; RT data in `OverridenTextures\`, RTGL1 SPIR-V in `Shaders\`). Rebuild it with `G:\sstre-tmp\engine\scripts\assemble-runtime.sh`.
- Build: `powershell -File G:\sstre-tmp\engine\scripts\build-win.ps1 -Tag <name>` (MSBuild `SamTFE.sln`, Release x64, properties `RTGL1_SDK_PATH` = RTGL1 source root, `RTGL1_LIB_PATH` = directory with `RayTracedGL1.lib`). RTGL1: `G:\sstre-tmp\engine\scripts\build-rtgl1.bat <src> <builddir>` (Ninja, RelWithDebInfo, DLSS OFF, then `GenerateShaders.py`).
- Refresh binaries in the runtime: `powershell -File G:\sstre-tmp\engine\scripts\sync-bin.ps1 -Rtgl cleanroom|libktx|none`. `Bin\RayTracedGL1.dll` is **optional**: without it the build runs raster only and "Ray Tracing" is hidden in the menu.
- Select the API with `sam_iGfxAPI` (persistent) or in a `+script` file: `0` = OpenGL, `1` = Vulkan raster (default), `2` = ray tracing. In the menu: Options → Video → Graphics API → "Ray Tracing".
- Command line (working directory `Bin`): `SeriousSam.exe +script Scripts\sstre_run.ini [+level Levels\01_Hatshepsut.wld]`, with e.g. `sam_iGfxAPI=2; sam_bFullScreen=0; sam_iScreenSizeI=1920; sam_iScreenSizeJ=1080; hud_iStats=1; srt_bVSync=0; ser_bEnumeration=0; ga_strServer="127.0.0.1"; ga_strMSLegacy="127.0.0.1";`. RT validation: `srt_bDebugValidation=1;`.
- Harness used here: `G:\sstre-tmp\engine\scripts\run-game.ps1 -Api 0|1|2 [-Level …] -ShotAt … -EscAt … -Total …` (window-only capture, records foreground state, always kills the game), launched through `gpu-lock.ps1 run` (or the earlier `locked.ps1`, which runs only after a confirmed ACQUIRED).
- Overrides: RT reads `OverridenTextures\Compressed\<texture path without .tex>{,_n,_rme}.ktx2`; all APIs read loose `.tex` files in the game root (EXP-012). Both can be present at the same time (see R6).
- Caveat: RT window captures are stale while the window is occluded or not in the foreground (flip-model swapchain, R4). The harness brings the window to the front, so the owner's keyboard and mouse can reach it.

## Goal and success criteria

1. Port the Serious-Engine-RT backend into Classic-VK for TFE on Windows x64 (EXP-005 milestone M1). Conventional raster stays the default; RT is a runtime-selectable graphics API.
2. Vulkan and OpenGL raster keep working, including when RTGL1 is absent.
3. TFE main menu plus 3 campaign levels in Vulkan raster, OpenGL raster and RT, and the same for raster with RTGL1 absent. Count validation errors for RT.
4. Integrate track K's clean-room KTX2 reader into RTGL1. Show that blue-noise-dependent RT effects and a synthetic KTX2 override render the same with libktx and with the clean-room reader.
5. Measure effort against EXP-005's M1 sub-estimates (conflicts, LOC, time) so the estimate can be recalibrated.

## Procedure (exact, reproducible)

1. **Worktrees** (2026-11-27):
   - `git -C repos\SSTRE-Engine worktree add G:\sstre-tmp\engine\wt-transplant -b sprint2/rt-transplant phase1/cvk-build`, re-checked out with `core.autocrlf=false` so that git's LF patches apply like for like (no config changed).
   - `git -C upstream\sultim-t_RayTracedGL1 worktree add G:\sstre-tmp\engine\wt-rtgl1 -b sprint2/rtgl1-sstre phase1/rtgl1-v1.1.0-sdk1.4`, later fast-forwarded to `sprint2/ktx2-cleanroom`.
   - Umbrella `G:\sstre-tmp\engine\wt-umbrella` on `sprint2/exp-009`.
   - The Phase 1 reader (`phase1/no-ktx`) was not read or used.
2. **Baseline:** an unmodified `phase1/cvk-build` build (`build-win.ps1 -Tag baseline`, targets Ecc, Engine, Entities, Game, Shaders, SeriousSam, ogg/vorbis, amp11lib) passed in 180 s. Its binaries are kept in `G:\sstre-tmp\engine\bin-baseline`.
3. **RTGL1:** `build-rtgl1.bat` for `build\rtgl1-libktx` (`4bcf13e`, stock libktx) and for `build\rtgl1-cleanroom` (`0eb4c4a`). Both have DLSS OFF. Shaders come from `GenerateShaders.py -r` into `wt-rtgl1\Build` (45 `.spv`). Track K changed no shaders, so one SPIR-V set serves both builds.
4. **Transplant (WP2):** `git apply --3way local-work\port\rt_only_SamTFE.patch` (EXP-005 probe b). Conflict regions were resolved per region with a logging helper (`scripts\resolve.py`, log `logs\conflicts.tsv`). The compile was then iterated until clean. Compiler errors for the renamed union members were fixed by exact error column (`scripts\fix_members.py`).
5. **Runtime-optional RT (WP5):** delay-loaded `RayTracedGL1.dll` plus the `RTGL1Loader` probe, and non-fatal RT adapter enumeration (see R2).
6. **UI (WP3, minimal):** a "Ray Tracing" entry in Classic-VK's graphics-API trigger, plus the RT section of `RenderingOptions.cfg`.
7. **Runtime:** `assemble-runtime.sh` and `sync-bin.ps1` (see the launch section). Every game run went through the GPU lock. Session A+B+C ran in one hold (2026-11-27 23:53:58 to 2026-11-28 00:22:36, 28.6 min); session D ran in a later hold. All runs: 1920×1080 window, `srt_bVSync=0`, `hud_iStats=1`, master server 127.0.0.1, single player.
8. **Image metrics:** `scripts\imgstats.ps1` (System.Drawing). It reports the mean RGB of the client area, and between two captures the mean absolute difference (MAD, 0–255), PSNR and the share of pixels differing by more than 8.

## Results ([EXP] unless labelled otherwise)

### R1. Transplant and build

| Item | Measured |
|---|---|
| RT-only patch apply onto `ba0c12e8` (TFE) | Same as EXP-005: 26 files added, 15 clean, 8 conflicted |
| Editor files (EngineGui, Modeler/WorldEditor `DlgPreferences`) | Reverted. MFC is not installed and the editors are out of M1 scope, so Modeler's 2 regions were not resolved |
| Conflict regions resolved | **39** in 7 files: DrawPort 16, SeriousSam.cpp 6, GfxLibrary.cpp 5, Texture 5, GfxLibrary.h 3, Gfx_wrapper 3, RenderModel_View 1. Choice: 16 ours (2 with a follow-up GAT_RT edit), 6 theirs, 17 hand-merged. Commit `7c0fcf50`'s message says "41"; the correct count for the engine files is 33, plus 6 in SeriousSam.cpp (`7d80a7d7`) |
| Silent semantic conflicts (applied cleanly, broke the build) | 2 in DrawPort.cpp: duplicate `eAPI` in `Fill(COLOR)`, and the HUD quad `ptex` that Classic-VK had commented out |
| Point adaptations not predicted by EXP-005 R3 | (a) Classic-VK `Vertex.h` uses **named union members** (`GFXColor.ub.r`, `.ul.abgr`, `GFXTexCoord.st.s`, `.uv.u`): 42 sites. (b) PCH include name `<Engine/StdH.h>`. (c) `Console.h` is not in the Classic-VK PCH. (d) `RG_USE_SURFACE_WIN32` define. (e) Flashlight declarations dropped by the hunk filter (`ctl_bFlashlight`, `hud_bShowFlashlightHint`). (f) Adapter RT probe was a `FatalError` on non-RT GPUs |
| Point adaptations predicted by R3 | World pointer → `CShell::Get/SetCurrentWorld` (2 sites); `std::size` → `ARRAYCOUNT`. The Win32 surface needed **no** change: on Windows Classic-VK's `_hwndMain` is a native `HWND` [SRC `SeriousSam/MainWindow.cpp:257-283`] |
| Full build after transplant | Exit 0, 0 errors (`logs\msbuild-rt10.log`, 163 s; incremental later builds 6–100 s) |
| Diff vs `phase1/cvk-build` (10 commits) | 51 files, **+11,922 / −98** lines. RT layer files (verbatim plus adaptations): 28 files, +10,804. Hooks, glue and SSTRE code ≈ +1,120 / −98 |
| RTGL1 clean-room build | `[66/66]` linked. EXP-003 guard `check_rtgl1_build.py`: **PASS** (libktx build: FAIL, 15 KTX-Software objects). `KTXorientation` string in DLL: 0 (libktx build: 1). DLL 1,470,976 B vs 2,058,240 B |

### R2. Runtime-optional RT

- `Engine.dll` links `RayTracedGL1.lib` with `/DELAYLOAD:RayTracedGL1.dll`. `RTGL1_IsAvailable()` does a `LoadLibrary` and then binds all imports with `__HrLoadAllImportsForDll` under SEH. It is called once from `InitAPIs`; if it fails, `GAT_RT` has 0 adapters [SRC `Engine/Raytracing/RTGL1Loader.cpp`, `Engine/Graphics/Adapter.cpp`].
- A failed `rgCreateInstance` leaves `SSRTMain` uninitialized, and `InitDriver_RayTracing` then returns FALSE [SRC `Gfx_RayTracing.cpp`, `SSRT.cpp`].
- The display-mode recovery list now tries Vulkan raster first, then OpenGL.
- [EXP] With `RayTracedGL1.dll` removed (session C), `sam_iGfxAPI=2` logs `Ray tracing unavailable: RayTracedGL1.dll not found` → `Cannot start ray tracing` → `Trying recovery mode 0...` → `Vulkan context created`. The menu and `01_Hatshepsut` then run in Vulkan raster. Recovery uses the 640×480 recovery resolution.
- RTGL1 errors were silently dropped in Release (`RG_CHECKERROR` was an ASSERT). They are now logged, rate-limited (`005bd78c`). No RTGL1 API errors appeared in any run.

### R3. Test matrix (sessions A and C, 2026-11-27/28)

Each run: start, screenshots at 12 s (menu) or 20 s and 32 s (level), then kill. "OK" = the process was still running and responding at the end, and for levels the log shows `started.`. No crash and no hang in any of the 22 runs (A: 12, C: 10).

| Build / API | Menu | 01_Hatshepsut | 02_SandCanyon | 03_TombOfRamses |
|---|---|---|---|---|
| RTGL1 present, **RT** | OK, menu rendered (title-bar FPS ≈ 470–550) | OK, intro cutscene path-traced with RTGL1 lens flares | OK (level start shows NETRICSA) | OK (NETRICSA) |
| RTGL1 present, **Vulkan raster** | OK | OK | OK | OK |
| RTGL1 present, **OpenGL raster** | OK | OK, textured (unlike the RT fork's OpenGL, EXP-002) | OK | OK |
| RTGL1 **absent**, Vulkan raster | OK | OK | OK | OK |
| RTGL1 absent, OpenGL raster | OK | OK | OK | OK |
| RTGL1 absent, RT requested | OK, falls back to Vulkan raster (R2) | OK, Vulkan raster | — | — |

- Vulkan vs OpenGL on the same NETRICSA frames: MAD 1.5–2.3, PSNR 33.7–35.6 dB.
- Raster with RTGL1 present vs absent: MAD 1.3–3.2. The residual comes from animated backgrounds, not from the RT code.
- Gameplay in RT on `08_Suburbs`: path-traced world and HUD. HUD FPS **≈ 102** with the player alive (session D) and 74.9 in a death-cam view (session B), at 1080p, **validation layer on** (see R5). Vulkan raster, same view: 142.7–143.9 (vsync-capped, ASM). These are indicative single readings for the benchmark track, not measurements.
- Levels 2 and 3 open NETRICSA at start. Posting ESC opens the game menu on levels that show no NETRICSA, so the A matrix shows load success, not gameplay views, for those levels.

### R4. Failure found and fixed in the harness, not in the engine

The first RT runs showed only the green mode-switch fill (menu) or the loading screen (level), although the game logged progress. The same runs worked once the game window was in the foreground. Vulkan raster windows capture correctly in the background. [ASM] `PrintWindow` returns stale content for RTGL1's flip-model swapchain while the window is occluded. The harness now brings the window to the front before each capture.

One diagnostic variant (rendering GAT_RT on the parent window instead of Classic-VK's child canvas) **hung** after RT init. It was reverted and is not in the branch.

### R5. Validation layer (RT, `08_Suburbs`, `srt_bDebugValidation=1`, Vulkan SDK 1.4.363 layer)

**35 error messages, 5 distinct VUIDs:**

| VUID | Count |
|---|---|
| `VUID-vkCmdTraceRaysKHR-mipmapMode-04770` | 10 (limit) |
| `VUID-vkCmdDispatch-mipmapMode-04770` | 10 (limit) |
| `VUID-vkCmdBuildAccelerationStructuresKHR-pInfos-10126` | 10 (limit) |
| `UNASSIGNED-non-acquired-swapchain-image-used` | 3 |
| `VUID-vkQueueSubmit-pSignalSemaphores-00067` | 2 |

Plus 1 warning (`AllocateDescriptorSets-WrongType`). This is **exactly the set EXP-002 measured for the unmodified RT fork**, so the transplant adds no validation errors. All five are RTGL1 v1.1.0 issues.

**Persistent-cvar caveat:** `srt_bDebugValidation` is a persistent cvar. After the first diagnostic validation run (22:07) it stayed on, so **every** RT run in sessions A, B and D ran with the validation layer. Each of these runs logged the same 35 errors and 5 VUIDs, with both RTGL1 builds. The RT FPS readings below therefore include validation overhead. The harness now sets `srt_bDebugValidation=0`, and the runtime's `PersistentSymbols.ini` was reset to 0 (and `sam_iGfxAPI` to 1).

### R6. POC-30: libktx vs clean-room KTX2 reader (session D, 2026-11-28 00:33–00:41)

**Setup:**

- Scene: `08_Suburbs` with `cht_bGod=1; cht_bInvisible=1` (the player stays alive and enemies ignore him) and one ESC at 16 s to close NETRICSA. Captures at 22 s and 30 s.
- Synthetic TommyGun override `Body{,_n,_rme}.ktx2`: BC7/BC5, from EXP-002's SSTRE generator.
- Blue noise `BlueNoise_LDR_RGBA_128.ktx2`, 128 layers, which drives RTGL1's stochastic shadow/GI sampling.
- Two runs per reader. Same engine binaries, same SPIR-V; only `RayTracedGL1.dll` differs (clean-room `42bdd141…`, libktx `055cdd12…`, SHA-256 prefixes of our own builds).
- Metric on rows 90–1119 of the window, which excludes the title bar and the top console band (validation text).

| Pair | 22 s: MAD / PSNR / px > 8 | 30 s: MAD / PSNR / px > 8 |
|---|---|---|
| clean-room run 1 vs run 2 (same reader) | 0.28 / 36.9 dB / 0.67 % | 1.59 / 27.7 dB / 4.59 % |
| libktx run 1 vs run 2 (same reader) | 0.20 / 40.9 dB / 0.55 % | 0.53 / 33.0 dB / 1.19 % |
| clean-room 1 vs libktx 1 | 0.29 / 37.2 dB / 0.69 % | 1.70 / 27.4 dB / 4.72 % |
| clean-room 2 vs libktx 2 | 0.28 / 37.4 dB / 0.70 % | 0.60 / 32.6 dB / 1.38 % |
| clean-room 1 vs libktx 2 | 0.18 / 38.5 dB / 0.36 % | 1.64 / 27.5 dB / 4.62 % |
| clean-room 2 vs libktx 1 | 0.20 / 37.5 dB / 0.36 % | 0.55 / 32.5 dB / 1.21 % |

- **Result:** cross-reader differences are within run-to-run noise. At 22 s every pair is at MAD 0.18–0.29. At 30 s, clean-room run 1 is the outlier against **all** other runs, including its own reader (≈ 1.6); the other three agree at 0.5–0.6. That points to timing, not to the reader.
- On a full-frame metric, the first-pass difference sat entirely in the top tile row (console text present or absent). In every other tile the per-tile mean luminance difference was 0.0 ± 0.2.
- The synthetic override (magenta/cyan checker, yellow band, emissive grid glow) is visible on the first-person weapon in all four runs. The blue-noise-dependent path-traced lighting is visually and numerically identical.
- **POC-30 render test: pass** for this scene. Limits: one scene, two runs per reader, window captures (not a frame-exact readback).
- HUD FPS with validation on: ≈ 102 (both readers). Vulkan raster, same view: 143.9 (vsync-capped, ASM).

### R7. Loose `.tex` (raster override) and `.ktx2` (RT override) coexist

- A loose `Models\Weapons\TommyGun\Body.tex` in the game root (the owner's own archive texture of another weapon, used as a stand-in, local only) and the synthetic `.ktx2` override were present at the same time. Same scene and captures as R6.

| Run | Weapon shows | Lower-half metric |
|---|---|---|
| Vulkan raster | loose `.tex` (green skin) | — |
| OpenGL raster | loose `.tex` | vs Vulkan: MAD 1.63 |
| RT, `.ktx2` present | synthetic `.ktx2` checker | vs the R6 run without the loose `.tex`: MAD 0.44 (same) |
| RT, `.ktx2` removed | loose `.tex` | vs `.ktx2` present: MAD 12.6 (different) |

- **Confirmed for the vertical slice:** raster uses the loose `.tex`; RT uses `.ktx2` when present and otherwise falls back to the loaded `.tex` (also the loose one).

## Branches and commits (local, not pushed)

SSTRE-Engine `sprint2/rt-transplant` (base `ba0c12e8` = `phase1/cvk-build`), 8 commits, head `005bd78c`:

| Commit | Subject |
|---|---|
| `2f9251dc` | rt(engine): import the ray-tracing layer from Serious-Engine-RT (TFE) |
| `7c0fcf50` | rt(engine): port the GAT_RT hooks into the Classic-VK graphics/render code |
| `e62b6fcc` | rt(engine): make ray tracing runtime-optional (delay-loaded RTGL1, no fatal probe) |
| `1fd1cd9f` | rt(entities): port the TFE RT entity hooks (flashlight, HUD, weapon render) |
| `7d80a7d7` | rt(game): select GAT_RT at runtime in the game exe, raster stays default |
| `750b1047` | rt(menu): offer "Ray Tracing" as a graphics API and add the RT rendering options |
| `d9f86637` | fix(gfx): FilterBitmap row buffer overflow for textures wider than 2048 |
| `005bd78c` | rt(engine): log failed RTGL1 calls in release builds |

RTGL1 `sprint2/rtgl1-sstre` = `0eb4c4a`: a fast-forward to track K's `sprint2/ktx2-cleanroom` on top of `4bcf13e`. No E1 commits were needed, because the build is configured from the command line (DLSS OFF).

## Deviations, modifications and failures

- **Scope cuts (documented, not done):**
  - Windows vcxproj only; the CMake/Linux build does not compile the RT files yet. Linux `RTGL1_IsAvailable()` returns FALSE.
  - No DLSS/FSR or render-scale menus.
  - No `SE1_RAYTRACING`-style build-time switch: x64 builds always contain the RT code, but it is runtime-optional.
  - Editors untouched.
  - TSE untouched.
  - No 10-minute play sessions.
- **Raster behaviour changes (all deliberate, RT-related):**
  - Display-mode recovery now tries Vulkan before OpenGL.
  - The menu API list has a third entry when RT is available.
  - The RT-only `BodyRemoveItem()` per tick in `Player.es` is guarded to GAT_RT.
- **Extra fix:** `d9f86637` enlarges the `FilterBitmap` temp row buffer `aulRows[2048]` (overflow for textures wider than 2048) [SRC `Engine/Graphics/Graphics.cpp:1225,1377`]. It is a plausible root cause of EXP-012's 4096×4096 crash. It was not verified at runtime here, because the investigation moved to track E4 by lead decision.
- **Lock incidents:**
  - (1) 21:48: a hung diagnostic game (CPU idle) kept running for about 4 minutes after my harness released the lock. Another track's GPU job had already acquired it. The harness now kills the game in `finally`.
  - (2) Lock starvation from about 22:12 to 23:54: other holders re-acquired within 15 ms to 2 s of releasing. Fixed by the lead's FIFO queue.
  - No game ran unlocked otherwise. An acquire that timed out was stopped before it could launch (22:47).
- **Focus and input:** the owner's cursor visibly hovered menu items in 3 captures ("DEMO", "HIGH SCORES" highlighted). One shot recorded the window without focus. No keystrokes are known to have reached a level run.
- **Tooling notes:**
  - The agent shell collapsed `\\` in inline scripts, which split 5 `CPrintF("…\n")` literals. They were caught and fixed before the first build.
  - A `sed` edit stripped CRLF from `Engine.vcxproj`. It was restored and the local commit rewritten before anything else built on it.

## Effort measurement vs EXP-005 M1

Wall-clock times of this agent run, from `G:\sstre-tmp\engine\logs\timelog.txt`. They are **not** person-days: the executor is an AI agent. Lock waiting is excluded.

| WP (EXP-005) | EXP-005 M1 estimate (pd low/likely/high) | Measured here | Output |
|---|---|---|---|
| WP0 RTGL1 pin/build | 1 / 2 / 4 | ≈ 7 min (both variants; the recipe was known from EXP-002/003) | 2 DLLs + 45 SPIR-V |
| WP1 build integration (Windows vcxproj only) | 2 / 4 / 7 | inside WP2's 20 min | Engine.vcxproj +37/−5 |
| WP2 engine transplant (TFE) | 5 / 8 / 13 | **20 min** (21:13 → 21:33, apply to first full link) | 39 regions, 2 silent conflicts, 42 member renames, 8 point adaptations; +11.8k lines |
| WP3 game exe + UI (minimal) | 3 / 5 / 7 | 4 min (+ exe runtime checks inside WP2) | +10 Menu.cpp, +162 cfg, +68/−21 SeriousSam.cpp |
| WP5 runtime optionality (Windows) | 3 / 5 / 9 | inside WP2 | +117 new loader lines, ≈ +60 glue |
| WP10 (part) runtime validation | — | 35 min diagnosis (R4) + about 45 min of locked test runs | 22 (A, C) + 10 (B) + 8 (D) runs |

- **Recalibration [ASM]:** the mechanical part (P1/P2) went much faster than the assumptions: about 0.5 min per conflict region against P1 = 10–30 min, and about 10k lines per hour against P2 = 1.5–4k lines per day. The time went into runtime behaviour that the patch statistics do not show: the capture/foreground issue, the lock, test design. EXP-005's R3 API check missed the named-union `Vertex.h` divergence (42 sites) and the PCH name.
- **For human-executed planning:** keep WP2 at its low end (5 pd) at most. Move effort to WP5/WP10 (runtime fallback, validation, input-isolated testing), and keep WP6 (Linux) and WP7 (TSE content) as the dominant unknowns.

## Interpretation ([SRC]/[DOC]/[ASM] clearly labelled)

- [EXP] EXP-005's central claim holds: the RT layer transplants almost unchanged into Classic-VK. The resulting single binary runs TFE in Vulkan raster, OpenGL raster and RT. It degrades cleanly to raster when RTGL1 is missing.
- [EXP] Classic-VK's OpenGL path survives the transplant. The RT fork's OpenGL defect (EXP-002) does not appear here. That supports Classic-VK-first (ADR-0005).
- [ASM] The remaining M1 work is mostly product work (menus, render scale, input-isolated tests, CMake), not porting risk.

## Impact on ADRs, dossiers and backlog

- **ADR-0005:** the transplant spike's acceptance item is met for TFE on Windows (evidence above). The provisional direction is strengthened.
- **ADR-0007:** RT is optional at runtime on Windows ([EXP], R2). Build-time optionality (CMake option) and Linux are still open.
- **Backlog, suggested items:**
  - CMake/Linux build of the RT code with a dlopen loader (EXP-005 WP6);
  - DLSS-free RT menu items (render scale, FSR 1);
  - harness support for NETRICSA/menu-aware gameplay captures;
  - runtime verification of `d9f86637` by E4;
  - RTGL1 VUID cleanup (also needed in any RTGL1 upgrade).

## Open questions

1. Should x64 builds always contain the RT code (runtime-optional, current state), or should there also be a build-time switch for raster-only builds (Linux packages without RTGL1)?
2. Display-mode recovery now prefers Vulkan over OpenGL. Is that acceptable as the Classic-VK default?
