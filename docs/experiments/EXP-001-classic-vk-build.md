# EXP-001: Classic-VK baseline build (Windows x64 + Linux x64, TFE + TSE) and platform spike S2

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | POC-02, POC-16, POC-23 |
| Status | **partial**: builds and Windows runtime pass. Linux graphical runtime, Steam Deck, the 5-minute demo and the KTX2 test were not run |
| Environment | Windows 11 Pro 22631, Intel Core i5-11600K, 32 GB RAM, NVIDIA RTX 4070 12 GB, driver 616.64 (Vulkan 1.4.351, OpenGL 4.6.0), display 3440×1440. VS 2022 17.5.1 / MSBuild 17.5.0 / MSVC 14.35.32215 (toolset v143), Windows SDK 10.0.22000.0, Vulkan SDK 1.4.363.0, WinFlexBison 2.5.25 (bison 3.8.2, flex 2.6.4). Docker 20.10.23 with `ubuntu:22.04@sha256:b000e69a50ff940390233025e7a337fb8469b509e2334fa4d018ac30f3e18cdb` (gcc 11.4.0, cmake 3.22.1, bison 3.8.2, flex 2.6.4) |
| Inputs | tx00100xt/SeriousSamClassic-VK `510d36f901cbe883c56b155b53717e4efdeb6522` (local branch `upstream/classic-vk-main`). Windows build branch `phase1/cvk-build` (local only). User-owned Steam editions: Serious Sam Classic The First Encounter and The Second Encounter |

Build instructions derived from this experiment: [SSTRE-Engine `docs/sstre/build-classic-vk.md`](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-Engine/blob/phase1/validation/docs/sstre/build-classic-vk.md) (local, not yet pushed).

## Goal and success criteria

1. Compile Classic-VK for Windows x64 and Linux x64, for both TFE and TSE (RD-001 S1, RD-006 S2.1 build half).
2. Launch TFE and TSE with user-owned Classic data, reach the main menu and load at least 3 campaign levels each, with Vulkan and with OpenGL (RD-001 S2/S3).
3. Measure startup and, if a built-in facility exists, frame time.
4. Evaluate RD-006 S2.1–S2.6 and the Classic-VK-relevant RD-001 criteria (S1, S2, S3, S8 Classic-VK half, S9).

## Procedure (exact, reproducible)

All work happened in a git worktree (`local-work/engine/cvk`, branch `phase1/cvk-build` from `upstream/classic-vk-main`). Scripts: `local-work/engine/cvk-scripts/` (`build-win.ps1`, `build-linux.sh`, `run-game.ps1`, `run-matrix.ps1`, `linux-ded-smoke.sh`). Logs: `local-work/cvk-logs/`. None of this is in a repository.

### Upstream procedure [DOC]

- `README.md` at `510d36f`, "Windows": install the Vulkan SDK ≥ 1.3.204.1 and VS 2015 or later, "open the solution in the Sources folder, select Release x64 … and compile it". "Linux": `cmake ..; make; make install`, with the apt packages listed there.
- `.github/workflows/cibuild.yml`: `build-ubuntu-x64` runs on `ubuntu-22.04` with `cmake -B build-x64 -DCMAKE_BUILD_TYPE=Release; make; make install`, after `sed`-replacing `-march=native` with `-mtune=generic`. `build-windows-x64` runs `msbuild /m /p:Configuration=Release /p:Platform=x64 SamTFE.sln` (and `SamTSE.sln`) on `windows-2019` with `setup-msbuild vs-version 14.0`. It installs neither flex nor bison, so the committed `Tools.Win32/Bison.exe`/`Flex.exe` are used through `ExecutablePath` [SRC `SamTFE/Sources/DecodeReport/DecodeReport.vcxproj:103` and other projects].

### Windows

1. [SRC] All 128 vcxproj configurations specify `v140` and SDK `10.0.14393.0`. Neither is installed. Override on the command line with `/p:PlatformToolset=v143 /p:WindowsTargetPlatformVersion=10.0.22000.0`.
2. Build with `build-win.ps1`. It sets `VULKAN_SDK=C:\VulkanSDK\1.4.363.0` and puts the trusted WinFlexBison directory first on `PATH`:
   ```
   MSBuild.exe SamTFE\Sources\SamTFE.sln /m /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=v143
     /p:WindowsTargetPlatformVersion=10.0.22000.0 /p:UseOfMfc=false
     /t:Ecc:Rebuild;Engine:Rebuild;Entities:Rebuild;Game:Rebuild;Shaders:Rebuild;SeriousSam:Rebuild;DedicatedServer:Rebuild;libogg:Rebuild;libvorbis:Rebuild;libvorbisfile:Rebuild;amp11lib:Rebuild
   ```
   TSE is the same with `SamTSE.sln`, `EntitiesMP` and `GameMP`.
3. Runtime directories `local-work/runtime/cvk-tfe` and `cvk-tse`, following README "Running": the upstream game-root template (`SamT?E/` minus `Sources`, `Tools.Win32` and `Bin`; it includes upstream `SE1_10b.gro` and `ModEXT.txt`) plus, copied from the Steam installs, all `*.gro` and `Help/` (TFE also `Levels/`) plus our built `*.exe`/`*.dll` in `Bin/`. For the demo test, the Steam `Demos/` were copied over the upstream template demos (the upstream TFE demo files differ from the Steam ones). The Steam installs were only read.
4. `run-game.ps1` writes `Scripts\sstre_run.ini`. The `+script` file runs before the video mode is set [SRC `SamTFE/Sources/SeriousSam/SeriousSam.cpp:811-851`]. The script sets `sam_iGfxAPI` (1 = Vulkan, 0 = OpenGL), `sam_bFullScreen=0`, `sam_iScreenSizeI/J=1280/720`, and for menu runs `sam_bAutoPlayDemos=0`. The harness starts `Bin\SeriousSam.exe +script Scripts\sstre_run.ini [+level <wld>]`, polls `SeriousSam.log` for a marker, takes a window-only screenshot with `PrintWindow`, then force-kills the process at 20 s (menu) or 30 s (level). `run-matrix.ps1` runs 2 games × 2 APIs × (menu + 3 levels) = 16 runs.

### Linux

1. `git -c core.autocrlf=false archive 510d36f… > src.tar`, which is **unmodified** upstream.
2. `docker run --rm -v src.tar:/in/src.tar:ro -v build-linux.sh:/in/build.sh:ro -v out:/out ubuntu@sha256:b000e69a… sh /in/build.sh`. The script installs the upstream README/CI package list plus `nasm`, `ninja-build` and `git`, records `dpkg -l`, extracts the tarball inside the container (CMake writes generated sources into the source tree, so a read-only source mount is not possible), then runs `cmake -B /work/build -DCMAKE_BUILD_TYPE=Release && cmake --build -j && cmake --install`. It copies `SamT?E/Bin` to `/out`.
3. Repeat into a second output directory and compare the SHA-256 of every output file (S9).
4. Linux runtime smoke without a GPU: `linux-ded-smoke.sh` copies the runtime data and our Linux `Bin/` into the container, writes a `Scripts/Dedicated/SSTRE/{init,1_begin,1_end}.ini` config that names one level, and runs `timeout 45 ./DedicatedServer SSTRE`.

## Results ([EXP] unless labelled otherwise)

### Builds

| Build | Result | Time | Warnings | Evidence |
|---|---|---|---|---|
| Windows x64 Release, TFE runtime targets (clean rebuild) | **pass**, exit 0, 0 errors | 150 s | 187 (C4267 ×150, C4244 ×112, C4996 ×40, …) | `cvk-logs/msbuild-SamTFE-Release-x64-runtime-rebuild.log` |
| Windows x64 Release, TSE runtime targets (clean rebuild) | **pass**, exit 0, 0 errors | 82 s | 187 | `cvk-logs/msbuild-SamTSE-Release-x64-runtime-rebuild.log` |
| Windows x64 Release, full `SamTFE.sln` `Build`, without `/p:UseOfMfc=false` | **fail**: `MSB8041` "MFC libraries are required" in DecodeReport, Depend, EngineGUI, Entities, MakeFONT, RCon (dependents not attempted) | n/a | n/a | `cvk-logs/msbuild-SamTFE-Release-x64-Build.log` |
| Linux x64 Release, TFE + TSE (`cmake` default targets), unmodified `510d36f` | **pass** | 62 s (run 1), 67 s (run 2) | 43 lines with `warning:` (bison conflict notes, `-Wsign-compare`, …) | `engine/cvk-linux/out/cmake-build.log`, `dpkg-l.txt` |
| Windows Debug, Win32, XPLUS variants | not attempted | | | |

Generated parsers and scanners show that the trusted tools were used. `Engine/Base/Parser.cpp` begins "A Bison parser, made by GNU Bison 3.8.2", and `SCANNER.CPP` defines `YY_FLEX_MINOR_VERSION 6`. The bundled `Tools.Win32` executables were never invoked: the projects now call `win_bison`/`win_flex`, names that do not exist in `Tools.Win32`.

Windows outputs per game: `SeriousSam.exe`, `DedicatedServer.exe`, `Ecc.exe`, `Engine.dll`, `Entities(MP).dll`, `Game(MP).dll`, `Shaders.dll`, `amp11lib.dll`, `libogg.dll`, `libvorbis.dll`, `libvorbisfile.dll`. Linux outputs per game: `SeriousSam`, `DedicatedServer`, `MakeFONT`, `TEXConv`, `libEngine(MP).so`, `libEntities(MP).so`, `libGame(MP).so`, `libShaders(MP).so`, `libamp11lib.so`.

Key Linux package versions (`dpkg -l`, 2026-11-27): bison 2:3.8.2+dfsg-1ubuntu0.22.04.1, cmake 3.22.1-1ubuntu1.22.04.2, flex 2.6.4-8build2, gcc/g++ 4:11.2.0-1ubuntu1 (gcc-11 11.4.0-1ubuntu1~22.04.3), libsdl2-dev 2.0.20+dfsg-2ubuntu1.22.04.2, libvulkan-dev/libvulkan1 1.3.204.1-2, libvorbis-dev 1.3.7-1build2, libogg-dev 1.3.5-0ubuntu3, libxxhash-dev 0.8.1-1, zlib1g-dev 1:1.2.11.dfsg-2ubuntu9.2, nasm 2.15.05-1, make 4.3-4.1build1.

**Reproducibility (S9, Linux):** two clean container builds produced the same 20-file list with **byte-identical SHA-256 for every file** (`out/sha256-bins.txt` = `out2/sha256-bins.txt`). Both builds used the same image, the same paths and the same apt snapshot day. Windows reproducibility was not tested.

### Windows runtime (our own builds, Steam data)

All 16 runs used 1280×720 windowed mode. Every process was still running and `Responding=True` at the time limit, then killed by the harness (no crash, no exit). Renderer strings from the log: Vulkan "NVIDIA GeForce RTX 4070, 1.4.351", OpenGL "NVIDIA GeForce RTX 4070/PCIe/SSE2, 4.6.0 NVIDIA 616.64".

| Game | API | Main menu | Level 1 | Level 2 | Level 3 |
|---|---|---|---|---|---|
| TFE | Vulkan | reached (screenshot) | `01_Hatshepsut` started, 7.99 s | `02_SandCanyon` 3.90 s | `03_TombOfRamses` 3.62 s |
| TFE | OpenGL | reached | `01_Hatshepsut` 3.39 s | `02_SandCanyon` 2.98 s | `03_TombOfRamses` 2.92 s |
| TSE | Vulkan | reached | `1_0_InTheLastEpisode` 5.45 s | `1_1_Palenque` 6.54 s | `1_2_Palenque` 5.10 s |
| TSE | OpenGL | reached | `1_0_InTheLastEpisode` 3.34 s | `1_1_Palenque` 5.14 s | `1_2_Palenque` 5.22 s |

- Level times run from process start until `  started.` first appears in `SeriousSam.log` (log polled every 100 ms). They are upper bounds because the log is buffered. The first Vulkan run includes cold caches.
- Time to renderer context created (menu runs): TFE 3.26 s (Vulkan) / 2.21 s (OpenGL), TSE 2.68 s / 2.30 s. Screenshots show the TFE and TSE main menus.
- Level screenshots show rendered geometry in all 12 runs. Vulkan and OpenGL screenshots of the same level have nearly identical mean luminance (for example TFE level 2: 45.9 vs 46.1), which suggests the two backends render the same scene. Screenshots stay in `local-work/cvk-logs/runs/`.
- Log errors are the same in every run and benign: missing first-run files (`PersistentSymbols.ini`, `SeriousSam.gms`, `DefaultMod.txt`), `ImmWraper.dll` (iFeel), EAX query failures, `Initial.ini(88): 'gfx_fProbeRatio' is not declared`, and joystick `error 0x000000a5`. No level-specific errors.
- Cosmetic bug: several strings in the Windows log are truncated to one character (CPU vendor "ntel", sound devices "H", "M", display "C"). This looks like an ANSI/Unicode mismatch in the `UNICODE` build. The Linux log prints "GenuineIntel" [ASM: Windows-only `printf("%s", wchar)`-style bug, unverified].
- These are smoke loads (30 s idle in the level), not 10 minutes of play. RD-001 S2's "10 minutes of play without a crash" was **not** measured.
- Another agent's RT build (`runtime/rt-tfe`) was running on the same GPU during these runs, so timings are indicative only.

### Frame time

**Not measured.** The built-in facility exists: `dem_bProfile`, `DumpDemoProfile()` and `dem_strPostExec` [SRC `SamTFE/Sources/GameMP/Game.cpp:166-168, 497-530, 1261-1263, 2782`]. Three attempts to use it produced no profile:

1. `PlayDemo("auto-demo0001")` in the `+script`: the demo started, then the menu initialization stopped it.
2. Auto-play (`dem_bProfile=1; dem_strPostExec="DumpDemoProfile(); Quit();"`, 300 s, Vulkan): the intro and then the auto-play loop rendered for the full 300 s (process responsive, screenshot shows a rendered level), but no `Temp\DemoProfile.lst` was written. [ASM] Either the post-exec does not fire in the auto-play loop, or the demo had not finished.
3. Skipping the intro via `sam_strIntroLevel` with a non-existent path: the auto-play loop tried to start that path and stopped.

No frame-time numbers are reported. A reliable method (a dedicated demo-launch command-line option, or a small harness patch) is future work. Stability side result [EXP]: TFE on Vulkan ran 300 s and 280 s without crashing or hanging.

### Linux runtime

- **Graphical client: not tested on Linux hardware.** WSL2/WSLg was not tried because of time and disk constraints.
- [EXP] Headless smoke test of our Linux `DedicatedServer` in Docker (no GPU, no sound): the first TFE campaign level and the first TSE campaign level (exact world paths kept locally, GATE-05) each reached `started.` / "ALL OK: Dedicated server is now running!" and ran until the 45 s timeout (exit 124). A later run with `--network none` loaded TFE `02_SandCanyon` the same way. This exercises Linux engine, entities and world loading on Steam data, but not rendering. Logs: `cvk-logs/ded-*.log`.
- Steam Deck: **not available, untested.**

### Outbound network contact (incident and mitigation)

- [EXP] Two Linux `DedicatedServer` runs on Docker's default bridge network (TFE level 01, TSE level 1_0) logged `Send heartbeat` twice each (start and `statechanged`). The configured master server is `sam.ostap.eu` (`ga_strServer` / `ga_strMSLegacy` defaults [SRC `SamTFE/Sources/Engine/GameAgent/GameAgent.cpp:182-184`]; the Croteam host is commented out). [ASM] These UDP heartbeats probably left the host, because the container had outbound connectivity. Setting `ser_bEnumeration=0` did **not** stop the heartbeat in the TSE run.
- [EXP] The 16 Windows runs were single-player (`network is off` in every log, no `Send heartbeat` lines). During the Windows demo run, `Get-NetTCPConnection`/`Get-NetUDPEndpoint` for the game process showed 0 TCP connections and 0 UDP endpoints in 5 samples over 15 s.
- Mitigation now in the scripts: Linux runtime tests run with `--network none`, in a local image (`sstre-cvk-rt:local`, `FROM` the pinned digest, runtime libraries pre-installed). The verification run still logs "Send heartbeat", but the container has no route. All test scripts also set `ser_bEnumeration=0; ga_strServer="127.0.0.1"; ga_strMSLegacy="127.0.0.1";`. Windows tests stay single-player.

## RD-006 spike S2 criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| S2.1 | Raster build on Windows and Linux, documented steps, 5-minute demo without crash | **Partial.** Builds pass on both platforms and the steps are documented. Windows TFE/TSE run without crash in all 16 smoke runs plus the demo run (see Frame time). The **5-minute scripted demo was not run** (no S1 demo script exists yet), and nothing graphical was run on Linux | above |
| S2.2 | Deck raster at 1280×800, p99 frame time | **Not tested** (no Deck, no Linux GPU host) | — |
| S2.3 | `VK_KHR_ray_tracing_pipeline` probe per device | **Windows/RTX 4070: present.** Classic-VK's own device enumeration in `SeriousSam.log` lists `VK_KHR_ray_tracing_pipeline`, `VK_KHR_acceleration_structure` and `VK_KHR_ray_query` among 289 device extensions (driver 616.64). Not done with `vulkaninfo`. No other devices tested | `cvk-logs/runs/tfe-vk-menu.log` |
| S2.4 | SE-RT under Proton or native Linux | **Not tested** (out of scope for Classic-VK; RT agent) | — |
| S2.5 | macOS / MoltenVK | **Not tested** (optional; no hardware) | — |
| S2.6 | KTX2 BC7/BC5 override identical on all PC targets | **Not tested.** Classic-VK has no KTX2 loader [SRC per RD-001 §3.4]. Needs the AssetCompiler path and an override mechanism first | — |

## RD-001 criteria relevant to Classic-VK

| ID | Result | Notes |
|---|---|---|
| S1 (TFE and TSE Release x64 build, exit 0, toolset override only) | **Pass with deviations.** Exit 0 for both, but **not** "zero source modifications": 6 build commits were needed (below), plus `/p:UseOfMfc=false` and runtime-only targets because MFC is not installed. Linux needs zero modifications | |
| S2 (TFE main menu, `01_Hatshepsut` in Vulkan and OpenGL, 10 min play, startup log) | **Partial.** Menu and `01_Hatshepsut` pass in both APIs, logs saved. The 10-minute play session was not done | |
| S3 (TSE launches, loads `1_0_InTheLastEpisode`; issue #53) | **Pass** for loading (both APIs). Issue #53 was not checked (not investigated in this run) | |
| S8 (Classic-VK half: loose `.tex` override through a mod directory) | **Not tested** | |
| S9 (two clean rebuilds, same file list, hashes) | **Pass on Linux** (identical file list and identical hashes). Windows not tested | |

## Deviations, modifications and failures

Build modifications on local branch `phase1/cvk-build`. Each is a separate commit, attribution preserved, not pushed. All are Windows-only files that the CMake build does not use:

| Commit | Change | Why |
|---|---|---|
| `d4c43f15` | 6 vcxproj files (Ecc, Engine, SeriousSkaStudio × TFE/TSE): `bison`/`flex` → `win_bison`/`win_flex` | The bare names resolve to the untrusted `Tools.Win32/Bison.exe`/`Flex.exe` (first in `ExecutablePath`). The brief forbids them |
| `9cb83850` | Engine.vcxproj: drop `-S Flex.skl` / `-S smcFlex.skl` | [EXP] `win_flex: fatal internal error, bad line in skeleton file`. The skeletons are flex 2.5-era. The CMake build never uses `-S` |
| `bbf04b04` | `win_flex --wincompat` | [EXP] `C1083: Cannot open include file: 'unistd.h'` |
| `4677963f` | Engine.vcxproj: `SCANNER.CPP` gets PCH off and `ForcedIncludeFiles=Engine/StdH.h`. `Smcscan.cpp` gets the same forced include | [EXP] `C1010` (PCH) and missing types. The dropped skeletons injected `#include "Engine/StdH.h"` |
| `4206e38f` | `Engine/Ska/smcScwin.l`: `extern "C" { int syywrap(void); }` | [EXP] `C2732 linkage specification contradicts earlier specification for 'syywrap'` with flex 2.6.4. The Unix `smcScan.l` already does this |
| `ba0c12e8` | `SeriousSam.rc`, `DedicatedServer.rc`: `afxres.h` → `winres.h` | [EXP] `RC1015: cannot open include file 'afxres.h'` (MFC not installed) |

Command-line deviations: `/p:PlatformToolset=v143`, `/p:WindowsTargetPlatformVersion=10.0.22000.0`, `/p:UseOfMfc=false`, and building only runtime targets. [SRC] No runtime source includes MFC headers. `UseOfMfc` only adds `_AFXDLL` and MFC linkage.

Failures and environment issues:

- [EXP] Toolchain: the brief lists MFC as installed, but no `mfc140u.lib` exists in VS 2022 or VS 2019 (BuildTools/Community). `vswhere -requires Microsoft.VisualStudio.Component.VC.ATLMFC` returns nothing. The full solutions (editors and tools) therefore do not build. The lead decided MFC/editors are not needed for Phase 1, so MFC is an optional prerequisite and was not installed.
- [EXP] Linux first attempt failed in `ecc`: `Unrecognized character '' (ASCII 0x0d)`. Cause: `git archive` with Git for Windows' system `core.autocrlf=true` emits CRLF. Fixed with `git -c core.autocrlf=false archive` (not a source change).
- [EXP] **ENOSPC (environment failure, not a code failure):** drive L: filled up (0 GB free) during the second Linux build. That build produced only `apt.log` and was re-run successfully. The same condition caused a screenshot save to fail (GDI+ "generic error"). About 1 GB of our own MSVC intermediate directories (`Sources/*/Release/`) were deleted to recover. As the coordinator instructed, new large outputs from that point went to `G:\sstre-tmp\cvk\` (Docker contexts and Linux dedicated-server logs). The existing worktree, the runtime copies and the small logs stayed on L:.
- [EXP] The first runtime screenshots captured the whole desktop. They were deleted, and the harness switched to window-only `PrintWindow` capture.
- [EXP] The first demo-profiling attempt (`PlayDemo("auto-demo0001")` from the `+script`) started the demo and was then stopped by the menu initialization ("stopping game"). No profile resulted.

## Interpretation ([SRC]/[DOC]/[ASM] clearly labelled)

- Classic-VK at `510d36f` is a viable raster baseline on the reference PC: Windows TFE and TSE run in Vulkan and OpenGL on Steam data, and Linux builds unmodified and reproducibly in a pinned container.
- [ASM] The Windows modifications are all "modern toolchain" fixes (flex 2.6 instead of the bundled 2.5 binary, no MFC). Upstreaming them, or switching the Windows build to CMake, would remove the dependency on the unverified `Tools.Win32` binaries. The upstream CMake has an `MSVC` branch marked "I don't know if this will build with MSVC" [SRC `SamTFE/Sources/CMakeLists.txt:547`]. Not tried.
- [ASM] The bundled `SE1_10b.gro` (105 `.tex` entries under `Textures/` and `TexturesMP/`) and the upstream `Demos/` are data that this layout depends on. They need the ADR-0006 provenance audit before anything is published.

## Impact on ADRs, dossiers and backlog

- ADR-0005 acceptance criterion 1 (Classic-VK half): met with recorded deviations. Criterion 2 (Classic-VK launches TFE and TSE): met on Windows.
- RD-001 §8.1 step 2 is inaccurate: "toolset override only" is not sufficient with flex 2.6 and without MFC. Update it to point to this report.
- RD-006: S2.1 is partial. S2.2, S2.4, S2.5 and S2.6 are open. S2.3 has a Windows/RTX 4070 answer.
- Backlog: POC-02 is done (with deviations). POC-16 is partial (Linux build only). POC-23 is partial.
- Toolchain list in the Phase 1 brief: MFC is **not** installed (optional for editors).

## Open questions

1. Should the SSTRE Windows build move to upstream CMake (if it works with MSVC), or keep patched vcxproj files?
2. A Linux GPU host (Mesa RADV and/or NVIDIA) and a Steam Deck are needed for S2.1 (Linux) and S2.2.
3. A scripted 5-minute demo (the RD-005 S1 demo) is needed to close S2.1 and to produce comparable p99 frame times.
4. Should the GameAgent heartbeat be disabled at build level (for example a compile-time switch) in SSTRE builds, given that `ser_bEnumeration=0` does not stop it on the dedicated server?
