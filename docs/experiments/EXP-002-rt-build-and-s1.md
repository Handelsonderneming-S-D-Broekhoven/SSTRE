# EXP-002: Serious-Engine-RT + RTGL1 build and rendering spike S1

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | POC-01, POC-22 |
| Status | partial: build and TFE RT run pass; validation, OpenGL, demo, 1440p and TSE criteria fail or are not tested |
| Environment | Windows 11 Pro 22631; NVIDIA RTX 4070 12 GB, driver 616.64; desktop 3440×1440 at 125 % scaling (2752×1152 logical); VS 2022 17.5 (MSVC 14.35.32215, v143, **no MFC**); CMake 4.4.4; Ninja 1.13.2; Vulkan SDK 1.4.363.0 (shaderc v2026.4); WinFlexBison 2.5.25 (bison 3.8.2, flex 2.6.4); Python 3.10.11 |
| Inputs | sultim-t/Serious-Engine-RT `0e7f223c19a28014b60d900878c28831db522120` (local `upstream/rt-main`, tag v1.5); sultim-t/RayTracedGL1 tag `v1.1.0` = `b1eb3d8ca3fe75f6f4dda16a53aeb99ea613aead`; Steam *Serious Sam Classic: The First Encounter* (user-owned, copied, unmodified) |

Reproducible instructions: SSTRE-Engine [`docs/sstre/build-rt.md`](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-Engine/blob/phase1/validation/docs/sstre/build-rt.md) (local, not pushed). Logs: `local-work/rt-logs/`. Scripts: `local-work/rt-tools/`. Screenshots: `G:\sstre-tmp\rt\shots\` (local only, never committed).

**Location change.** Disk L: ran out of space during this experiment (ENOSPC, see Deviations). From 2026-11-27 ~20:20, all new large outputs go to `G:\sstre-tmp\rt\` (owner-approved temporary area): screenshots, KTX test files, the TSE probe worktree, and TEMP/TMP for builds. The existing worktrees (`local-work/engine/rt`, `local-work/engine/rtgl1-v1.1.0`) and the runtime (`local-work/runtime/rt-tfe`) stayed on L:.

## Goal and success criteria

1. Build RTGL1 and SE-RT for Windows x64, and confirm or refute that RTGL1 `v1.1.0` is the matching revision (RD-001 §3.2, RD-005 §3.1).
2. Launch TFE with RT. Test whether the raster backends (`GAT_VK`, `GAT_OGL`) still work in the same binary.
3. Test the KTX2 PBR override path (`OverridenTextures/Compressed`, `_n`, `_rme`) with a synthetic texture.
4. Evaluate RD-005 S1.1–S1.7 and RD-001 S4–S8.

## Procedure (exact, reproducible)

1. Worktrees (all commands run on 2026-11-27):
   - `git -C repos/SSTRE-Engine worktree add local-work/engine/rt -b phase1/rt-build upstream/rt-main`
   - `git -C upstream/sultim-t_RayTracedGL1 worktree add local-work/engine/rtgl1-v1.1.0 v1.1.0` (the tag was already present)
2. RTGL1, in a VS x64 developer prompt (`rt-tools/build-rtgl1.bat`): `cmake -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DRG_WITH_SURFACE_WIN32=ON -DRG_WITH_NVIDIA_DLSS=OFF -DRG_WITH_EXAMPLES=OFF`, then `cmake --build`. Shaders: `python -I Source/Shaders/GenerateShaders.py -r` with `C:\VulkanSDK\1.4.363.0\Bin` on PATH.
3. SE-RT (`rt-tools/build-sert.bat`): `msbuild Sources\AllTFE.sln /m "/t:Ecc;Engine;Entities;Game;SeriousSamTFE;libogg;libvorbis;libvorbisfile;Shaders" /p:Configuration=Release /p:Platform=x64 -p:UseOfMfc=false`, with `RTGL1_SDK_PATH=<rtgl1 worktree>` and WinFlexBison first on PATH. The final evidence is a clean rebuild after `git clean -xdf Sources Bin`.
4. Runtime `local-work/runtime/rt-tfe` (`rt-tools/assemble-runtime.sh`). It holds the build outputs, the RTGL1 `*.spv`, the engine-repo data (`SE1_10.gro`, `Data`, `Scripts`, …, `OverridenTextures/BlueNoise…ktx2`, `WaterNormal_n.ktx2`) and copies of the Steam files named in the SE-RT v1.5 release notes (`Levels/` and six `.gro`) plus `Demos/`. `TFE_RT_Textures.zip` was **not** downloaded.
5. Launch (`rt-tools/run-se.ps1`): `Bin\SeriousSamTFE.exe +script Scripts\sstre_lvl_api<N>.ini +level Levels\<level>.wld`. The script sets `sam_iGfxAPI` (2 = RT, 1 = Vulkan raster, 0 = OpenGL), a 1920×1080 window, `hud_iStats=1`, and for RT `srt_bVSync=0`.
   - The script closes NETRICSA at level start by posting `WM_KEYDOWN VK_ESCAPE` to the game window only.
   - Window images come from `PrintWindow(PW_RENDERFULLCONTENT)`, which captures only the game window. One earlier attempt with desktop capture (`CopyFromScreen`) picked up other windows; those images were deleted immediately.
   - The game is closed with `WM_CLOSE`, and `SeriousSamTFE.log` is copied to `rt-logs/<tag>.log`.
6. Override test.
   - `rt-tools/gen_synthetic_tex.py` (stdlib only, our own procedural pattern) writes a 512² albedo (magenta/cyan checker + yellow diagonal band), `_n` (sinusoidal ripple) and `_rme` (R roughness, G metallic, B emissive grid).
   - Each PNG is encoded with Compressonator CLI **4.6.0**: `compressonatorcli -fd BC7|BC5 -miplevels 20 in.png out.ktx2`, the same formats as RTGL1 `Tools/CreateKTX2.py`.
   - Tool provenance: `compressonatorcli-4.6.0-win64.zip` from the GPUOpen-Tools/compressonator GitHub release V4.6.0. SHA-256 `6fb42c9b7de0bd0f626bea8a17975a343f3cde7a5ef57a754582eb59b18543d5` equals the GitHub-published digest. `compressonatorcli.exe` has a valid Authenticode signature from Advanced Micro Devices. License: MIT (`license/license.txt`).
   - The three `.ktx2` files go under `OverridenTextures/Compressed/<dir of one first-person weapon model texture>/<name>{,_n,_rme}.ktx2`. The exact asset path is kept locally only in `rt-logs/override-target.LOCAL.txt` (GATE-05).
7. Validation: `srt_bDebugValidation=1` (RTGL1 `enableValidationLayer`; layer from Vulkan SDK 1.4.363.0).

## Results ([EXP] unless labelled otherwise)

### Build

| Item | Result |
|---|---|
| RTGL1 v1.1.0 configure + compile | [EXP] Exit 0. 79/79 Ninja steps, only a `NOMINMAX` redefinition warning (C4005). CMake 4.4.4 needed no policy override; the Vulkan 1.4.363 headers compiled without change |
| RTGL1 shaders, unmodified | [EXP] **8 of 45 fail** with glslc from SDK 1.4.363: `ShaderCommonGLSLFunc.h:70: error: 'return' : sampler or image cannot be used as return type when generating SPIR-V` (RtRaygen*, RtAlphaTest, RsRasterizer*, …) |
| RTGL1 shaders after `4bcf13e` | [EXP] 45/45 `.spv`, "> Done." |
| SE-RT first build attempt | [EXP] Failed in sequence: flex skeleton ("bad line in skeleton file"), C1010 PCH in `SCANNER.CPP`, C1083 `unistd.h`, C2732 `yywrap`, Ecc "memory exhausted" at `Entities/Player.es(5589)`, MSB8041 (MFC required) for `Entities`, RC1015 `afxres.h`, and DedicatedServer C1083 `EntitiesMP/Global.h` |
| SE-RT clean rebuild (final) | [EXP] **exit 0, 139 s**. 222 distinct warning lines (590× C4267, 56× C4244, 22× C4477 …). Outputs: `SeriousSamTFE.exe`, `Engine.dll`, `Entities.dll`, `Game.dll`, `Shaders.dll`, `Ecc.exe`, ogg/vorbis DLLs, `RayTracedGL1.dll` |
| RTGL1 revision | [EXP] SE-RT `0e7f223` compiles, links and runs against `b1eb3d8` headers and library: **hypothesis confirmed as compatible**. [SRC] `b1eb3d8` (2022-04-20 00:25 +0100) is the last RTGL1 commit dated before SE-RT `0e7f223` (2022-04-20 20:24 +0100); the next RTGL1 commits (`75aea8f` onward) are dated 2022-04-23 or later. The fallback `7a88e38` was not needed |

### Runtime (1920×1080 window, RT defaults except `srt_bVSync=0`)

| Run (log in `rt-logs/`) | Result |
|---|---|
| `rt_seq` (no level) | [EXP] "Vulkan ray tracing context created: (NVIDIA, NVIDIA GeForce RTX 4070, 1.4)". Main menu rendered ("RAY TRACED", "1920x1080xdesktop (Vulkan Ray Tracing)") |
| `rt_01_Hatshepsut` | [EXP] Level loaded. The intro cutscene renders with RTGL1 lens flares; HUD 476 FPS (cutscene; engine cap `sam_iMaxFPSActive=500`). Clean stop |
| `rt_08_Suburbs_play` | [EXP] Level loaded; path-traced gameplay view at spawn; **HUD 93 FPS** |
| `rt_13_Luxor_play` | [EXP] Level loaded; interior gameplay; **HUD 65 FPS** (minigun firing; see input caveat) |
| `vk_08_Suburbs_play` (`sam_iGfxAPI=1`) | [EXP] "Vulkan context created". Same level renders correctly in Vulkan raster; HUD 144 FPS. [ASM] 144 is a vsync/refresh limit; raster vsync was not disabled |
| `ogl_08_Suburbs_play` (`sam_iGfxAPI=0`) | [EXP] "OpenGL context created … 4.6.0 NVIDIA 616.64". The level runs, but **brush geometry is untextured grey and the sky is white**. Models, terrain floor and HUD weapon are textured. Cause not investigated |
| `rt_08_Suburbs_validation` | [EXP] Error-severity messages: 5 distinct VUIDs. `VUID-vkCmdTraceRaysKHR-mipmapMode-04770` and `VUID-vkCmdDispatch-mipmapMode-04770` (each hit the 10-message limit), `VUID-vkCmdBuildAccelerationStructuresKHR-pInfos-10126` (AS size too small; 10× limit), `UNASSIGNED-non-acquired-swapchain-image-used` (3), `VUID-vkQueueSubmit-pSignalSemaphores-00067` (2). [ASM] The 2026 layer is far stricter than 2022-era layers |
| `rt_08_Suburbs_1440` (2560×1440 window) | [EXP] Runs and renders, but the window exceeds the 2752×1152 logical desktop. The top of the client area (with the FPS counter) is off-screen, so **no 1440p measurement** |
| `rt_demo2` | [EXP] `PlayDemo("auto-demo0002")` → "Cannot play demo: Cannot open file `…\demos\<garbage>.dem`". Workaround `dem_bPlay=1; dem_bPlayByName=1;` + `+level Demos\auto-demo0002.dem` → black screen; the process exited after 37.5 s (exit code 1) with no error in the log and no Windows Application-log event |
| Crashes | [EXP] None. Every level run ended with "stopping game … Renderer buffers cleared". Exit code is 1 on every `WM_CLOSE`, including clean ones |

Frame-time method: SE1 HUD FPS counter (`hud_iStats=1`, averaged over the last frames, `GameMP/Game.cpp:1855–1880`), read from window captures at fixed times after launch. These are single readings, not p50/p99. VRAM was not measured. 93 FPS ≈ 10.8 ms and 65 FPS ≈ 15.4 ms per frame.

### PBR override test

| Run | Result |
|---|---|
| `rt_08_Suburbs_override` (RT) | [EXP] The first-person weapon shows the synthetic magenta/cyan checker and yellow band, and the `_rme` emissive grid lines glow (bloom halo). The control run without overrides shows the original texture. **The override is used.** HUD FPS unchanged (93) |
| `vk_08_Suburbs_override` (Vulkan raster, same files present) | [EXP] Original texture; the override is ignored (consistent with RD-001 §3.6) |
| KTX2 files | [EXP] Valid KTX2 magic. `vkFormat` 145 (BC7_UNORM) for albedo/`_rme`, 141 (BC5_UNORM) for `_n`; 512², 10 mip levels, no supercompression. SHA-256 (our own synthetic files): albedo `5b3140ff…a74e`, `_n` `81c1027c…dfa2`, `_rme` `73036f8e…1ca1` |
| Log evidence | [SRC] RTGL1 v1.1.0 `TextureOverrides.cpp` does not log loaded overrides, so the evidence is visual only. Visible effect of `_n` not isolated |

### Other observations

- [EXP] The log shows garbled strings ("Assumed engine directory: �]4", "Vendor: ntel", "Saved game: <garbage>").
  - [SRC] `Engine/Base/Shell.h:28` redefines `NEXTARGUMENT` to read from `&pArgs` on x64. 22× C4477 show `CTString` passed by value to `%s` varargs.
  - [ASM] Both are x64-port defects. The first breaks shell functions with `CTString` arguments (`PlayDemo`); the second garbles the log.
- [EXP] Without `+level`, two runs ended up in a Hatshepsut single-player game ~20 s after start, and in `rt_13_Luxor_play` the player fired the minigun. The game window takes focus on launch, so the user's real keyboard/mouse input reaches it. Gameplay in these runs is therefore **not scripted or reproducible**. Level loads via `+level` are unaffected.
- [EXP] The engine-data files the release notes leave out (`Scripts/Game_startup.ini`, `Data/Var/*.var`, `Scripts/GLSettings/GLSettings.lst`, `Data/SeriousSam.gms`) are reported missing in the log, without visible effect.

## Criteria evaluation

| ID | Criterion | Result | Evidence |
|---|---|---|---|
| S1.1 | Unmodified build succeeds (or every edit listed) | **pass with edits**: 7 SE-RT build commits + 1 RTGL1 shader commit, all build-only, listed below | Build table |
| S1.2 | TFE RT run, 2 levels × 5 min demo, no crash, no validation errors at error severity | **fail**: 3 levels load without crash, but there are 5 error-severity VUIDs, demo playback fails, and continuous 5-minute play was not run (longest RT session ~95 s) | Runtime table |
| S1.3 | Raster fallback in the same binary | **pass for `GAT_VK`**; **fail for `GAT_OGL`** (brushes untextured, sky white) | `vk_`/`ogl_08_Suburbs_play` |
| S1.4 | TSE coverage | **not tested**: TSE cannot be built in the RT fork (see S7) | — |
| S1.5 | 10/10 overrides load, 0 on effect textures | **partial**: 1/1 override (albedo + `_rme` visibly applied, `_n` not isolated); the effect-texture exclusion was not tested | Override table |
| S1.6 | Colour space ΔE2000 ≤ 3 | **not tested** | — |
| S1.7 | Frame time p50/p99 + VRAM per mode | **partial**: single HUD FPS readings only (RT 93 / 65 at 1080p; VK 144, likely vsync-limited); no p50/p99, VRAM or OpenGL figure | Runtime table |
| RD-001 S4 | RT TFE builds, exact SHA/SDK/toolset recorded | **pass** (with build commits) | Build table |
| RD-001 S5 | `01_Hatshepsut` RT, frame time at 1080p and 1440p, 10 min without crash | **partial**: loads and renders (intro only in captures); 1080p reading on other levels; 1440p not measured; 10 min not run | Runtime table |
| RD-001 S6 | OpenGL and Vulkan raster render the same level | **partial**: Vulkan yes; OpenGL defective | Runtime table |
| RD-001 S7 | RT TSE status | **fail (not buildable as-is)**: [EXP] `Sources/All.sln` defines only `Debug/Release/Template|Win32`, so msbuild `Release|x64` fails with MSB4126. [EXP] The TSE projects `SeriousSam`, `EntitiesMP` and `GameMP` have 0 `Release|x64` configurations and 0 `SE1_RAYTRACING` defines (probe worktree at `phase1/rt-build`, `rt-logs/sert-all-tse-build.log`). [SRC] RTGL1 needs a 64-bit build | — |
| RD-001 S8 | RT KTX2 override visible | **pass** (RT half; the Classic-VK half belongs to EXP-001) | Override table |

## Deviations, modifications and failures

Build modifications. Each is a separate local commit; messages end with `Co-Authored-By`; nothing is pushed.

| Repo / branch | Commit | Change |
|---|---|---|
| SSTRE-Engine `phase1/rt-build` | `33e8b255` | `bison`/`flex` → `win_bison`/`win_flex` (Ecc, Engine, SeriousSkaStudio vcxproj). This avoids the untrusted `Tools.Win32/Bison.exe`/`Flex.exe` |
| | `46ce9ace` | drop `-S Flex.skl`/`-S smcFlex.skl` |
| | `cc74881f` | `%top{}` PCH include in `Engine/Base/Scanner.l`, `Engine/Ska/smcScan.l` |
| | `4b464aa2` | `win_flex --wincompat` for the Engine scanners |
| | `e6ac425b` | `#define YY_SKIP_YYWRAP` in the same `%top` blocks |
| | `47e4eff1` | `#define YYINITDEPTH 1000` in `Ecc/Parser.y` (value from Classic-VK) |
| | `4d18ac11` | `winres.h` instead of `afxres.h` in `SeriousSam.rc`, `DedicatedServer.rc` |
| RTGL1 `phase1/rtgl1-v1.1.0-sdk1.4` | `4bcf13e` | `getTexture()` → macro; backport of upstream `a2ad71e` |

Other deviations and failures:

- **Command-line property:** `-p:UseOfMfc=false`, because MFC is not installed on the reference PC, contrary to the Phase 1 toolchain table, which lists MFC. Only ATL headers and libs exist under `atlmfc/`.
- **Failed attempt (recorded):** after the YYINITDEPTH change, a stale `Bin\Ecc.exe` (Ecc's copy step did not re-run) made the error persist. A temporary `YYINITDEPTH 10000` commit was made and then dropped from the local branch before the final build. The final value is 1000, verified by the clean rebuild.
- **Environment failure (ENOSPC on L:):** the first Compressonator download failed with "not enough space on the disk". The Luxor screenshots of the first RT level pass were written truncated (0 B and 576 KiB). After the outputs moved, the download was redone (on C: scratchpad; the tool was later switched to 4.6.0) and Luxor was re-run (`rt_13_Luxor_play`). Object files of the RT build were deleted to free space; `Bin` was kept.
- **Tool choice:** Compressonator 4.5.52 was downloaded first but rejected: it is unsigned and GitHub has no digest for it. It was deleted.
- `DedicatedServer` dropped from the TFE target list (it needs TSE `EntitiesMP`).

## Interpretation ([SRC]/[DOC]/[ASM] clearly labelled)

- [EXP] The RT fork can be rebuilt reproducibly today with modern tools. Only small build-system edits are needed plus one RTGL1 shader fix that upstream itself made later. Unpinned RTGL1 is not a blocker: `v1.1.0` works.
- [EXP] Within the same binary, Vulkan raster is a working non-RT path for TFE. OpenGL is not usable as-is.
  - [ASM] Raster needs no RT hardware, because `GAT_VK` does not create the RTGL1 instance (only the RT path calls `rgCreateInstance`). This was not tested on a non-RT GPU.
- [EXP] The KTX2 override path works end to end with SSTRE-generated BC7/BC5 KTX2 and touches only the RT path. This supports the ADR-0005 contract `.ktx2` + `_n`/`_rme`. Per the owner decision on Apache-2.0 KTX code, it also confirms that the KTX dependency sits in RTGL1 (`Source/KTX`, libktx subset), not in the SE engine.
- [EXP] Validation errors with SDK 1.4.363 (AS build size, sampler filter features, swapchain image use) are technical debt for any RT backend port. [ASM] The AS-size error may matter on other drivers.
- [SRC]/[EXP] The x64 varargs defects (`NEXTARGUMENT`, `CTString` to `%s`) affect any engine based on this x64 port and should be checked in Classic-VK as well.

## Impact on ADRs, dossiers and backlog

- RD-001 §5 / RD-005 §3.1 and A1: RTGL1 `v1.1.0` is confirmed compatible (with a shader fix for new SDKs). U2 is answered: Vulkan raster works, OpenGL is broken.
- RD-001 S7 / RD-005 S1.4: TSE in the RT fork requires an x64 port of the TSE projects first. This adds to the ADR-0005 "RT backend port incl. TSE" work package.
- ADR-0005 acceptance criterion 2 ("RT fork launches TFE") is met. Criterion 3 is partially met; S1.2, S1.6 and S1.7 remain open.
- Phase 1 toolchain table: MFC is listed but not installed.
- Backlog suggestions:
  - Scripted, input-isolated benchmark: fix demo playback or add a frame-time dump. This needs code changes.
  - Rerun validation, VRAM and p50/p99 with PresentMon or similar.
  - Effect-texture override exclusion test.
  - Colour-space S1.6 test.

## Open questions

1. Should MFC (v143 x64) be installed so that the tools and the unmodified `UseOfMfc` settings can be built, or is `UseOfMfc=false` acceptable for game-only builds?
2. Is a frame-time instrumentation patch (per-frame dump) acceptable as a local commit, to get p50/p99 without third-party tools? Or should a pinned PresentMon release be installed?
3. Benchmarks need an input-isolated session (separate desktop/VM or user away), because the game window receives the user's real input.
4. Should the OpenGL defect in the RT fork be investigated, or should OpenGL be dropped as a target for the RT lineage (Vulkan raster is the fallback)?
