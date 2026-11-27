# EXP-009: RT transplant spike into Classic-VK (TFE, Windows x64) and KTX2 reader render test

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | POC-29 (RT transplant spike), POC-30 (clean-room KTX2 reader render test) |
| Status | **in progress** — preliminary: launch instructions only; results follow |
| Environment | Windows 11 Pro 22631, RTX 4070 12 GB, driver 616.64; VS 2022 17.5 (v143), Windows SDK 10.0.22000.0, Vulkan SDK 1.4.363.0, CMake 4.4.4, Ninja 1.13.2, WinFlexBison 2.5.25 |
| Inputs | Engine: SSTRE-Engine local branch `sprint2/rt-transplant` (base `phase1/cvk-build` = Classic-VK `510d36f` + 6 build commits; RT code from Serious-Engine-RT `0e7f223`). RTGL1: local branch `sprint2/rtgl1-sstre` (= v1.1.0 + SDK shader fix + track K clean-room KTX2 reader `0eb4c4a`) |

## How to launch the transplant build (for the benchmark and AI tracks)

All paths are local; nothing is published. Hold the GPU lock (`G:\sstre-tmp\gpu-lock.ps1`) for every run.

- Runtime: `G:\sstre-tmp\engine\runtime-tfe` (Classic-VK game-root template + copies of the owner's Steam TFE `*.gro`, `Levels`, `Help`, `Demos`; RT data in `OverridenTextures\`, RTGL1 SPIR-V in `Shaders\`).
- Binaries: `Bin\SeriousSam.exe` (+ `Engine.dll` …). `Bin\RayTracedGL1.dll` is **optional**; without it the build runs raster only and "Ray Tracing" is hidden in the menu.
- Refresh binaries: `powershell -File G:\sstre-tmp\engine\scripts\sync-bin.ps1 -Rtgl cleanroom|libktx|none`.
- Select the API with `sam_iGfxAPI` in a `+script` file: `0` = OpenGL, `1` = Vulkan raster (default), `2` = ray tracing. Example:
  `Bin\SeriousSam.exe +script Scripts\sstre_run.ini +level Levels\01_Hatshepsut.wld` (working directory `Bin`), with `sstre_run.ini` containing e.g. `sam_iGfxAPI=2; sam_bFullScreen=0; sam_iScreenSizeI=1920; sam_iScreenSizeJ=1080; hud_iStats=1; srt_bVSync=0; ser_bEnumeration=0; ga_strServer="127.0.0.1"; ga_strMSLegacy="127.0.0.1";`
- Harness used here: `G:\sstre-tmp\engine\scripts\run-game.ps1 -Api 0|1|2 [-Level …] -ShotAt … -Total …` (window-only capture, records foreground state, always kills the game).
- KTX2 PBR overrides (RT only): `OverridenTextures\Compressed\<texture path without .tex>{,_n,_rme}.ktx2`. Loose high-res `.tex` files in the game root (raster override, EXP-012) are read by all APIs.
- Caveat: RT window captures are stale when the window is occluded/not foreground (flip-model swapchain); the harness brings the window to the front, so the owner's keyboard/mouse can reach it.
