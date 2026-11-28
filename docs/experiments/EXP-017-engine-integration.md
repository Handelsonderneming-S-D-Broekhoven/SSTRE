# EXP-017: Integrated Classic-VK engine line and its `classic-vk` patch series

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | Sprint 2 track VS-E (vertical slice, engine integration); POC-27 follow-up (per-path context), POC-29/30/32, E3/E4 fixes, E5 TSE ray tracing (EXP-005 M2, EXP-018) |
| Status | **complete for 0.1.0-preview2**: E1, E3, E4, E5 (incl. the TSE haze fix and the two `1_2_Palenque` RT fixes) integrated, built, tested, exported. Open: the `1_2_Palenque` RT spawn cave renders black (E5 tuning issue, R3) |
| Environment | Windows 11 Pro 10.0.22631, Intel i5-11600K, RTX 4070 12 GB, driver 616.64. VS 2022 17.5 / MSVC 14.35.32215 (v143), Windows SDK 10.0.22000.0, WinFlexBison 2.5.25 (trusted copy), Vulkan SDK 1.4.363.0, Git 2.55.0.windows.3, Python 3.10.11. Linux: Docker 20.10.23, `ubuntu:22.04@sha256:b000e69a50ff940390233025e7a337fb8469b509e2334fa4d018ac30f3e18cdb` (gcc 11.4.0, CMake 3.22.1, Bison 3.8.2, Flex 2.6.4), runtime/audit image `sstre-e2-netaudit:local` (EXP-010) |
| Inputs | SSTRE-Engine local branches `sprint2/no-master-server` (`f7c3605f` = `phase1/cvk-build` + POC-32), `sprint2/tex4096-crash` (E4), `sprint2/rt-transplant` (E1), `sprint2/bench-fixes` (E3, head `b7c7e998`), `sprint2/rt-tse` (E5, head `958b2bd5`). RTGL1 clean-room build of `sprint2/ktx2-cleanroom` `0eb4c4a` (EXP-009, DLL SHA-256 prefix `42bdd141`). Owner's Steam *Serious Sam Classic* TFE and TSE data, copied into private runtimes |

All scripts, logs, screenshots and runtimes are local under `G:\sstre-tmp\vse\` (`scripts\`, `logs\`, `runs\`, `linux\`, `runtime-tfe\`, `runtime-tse\`). Nothing was pushed. Level, demo and archive names appear below; asset paths and hashes stay local (GATE-05).

## Goal and success criteria

1. One linear integration branch `sprint2/integration` with the original commits of E4, E1 (without its superseded `FilterBitmap` fix `d9f86637`), E3 and E5, on top of `phase1/cvk-build` + POC-32.
2. Windows x64 Release builds of TFE and TSE (both with the runtime-optional RT backend), Linux x64 builds of both (raster only) in the pinned container.
3. Runtime tests under the GPU lock: TFE and TSE menu + level in Vulkan, OpenGL and RT; RTGL1-absent fallback; a 4096-wide synthetic texture loads; demos play to completion; the RT menu options load through the `Include:` line; no master-server traffic; TSE RT lights distant geometry (haze fix) and runs `1_2_Palenque` (E5 fixes) without RTGL1 errors.
4. The `classic-vk` series exported from that branch, `check` clean **without `--allow-flagged`** (flagged files with minimal context and a lead review entry), `verify` round trip with equal tree hash, committed on SSTRE-Engine `feature/integrated-series`.

## Procedure (exact, reproducible)

1. **Branch.** `git -C …\SSTRE-Engine worktree add G:\sstre-tmp\vse\wt-engine -b sprint2/integration sprint2/no-master-server` (all git calls with `-c core.autocrlf=false`). Cherry-picks, in order: `15c567c0 3a4d07cc` (E4), `2f9251dc 7c0fcf50 e62b6fcc 1fd1cd9f 7d80a7d7 750b1047 005bd78c` (E1, **`d9f86637` skipped**), `9c8c06b9 b7c7e998` (E3), then E5's `sprint2/rt-tse` commits above `005bd78c` (R1). No `(cherry picked from …)` lines; the mapping is the R1 table. `git diff sprint2/tex4096-crash HEAD -- '*/Graphics/Graphics.cpp'` is empty: only E4's `FilterBitmap` fix is present.
2. **Credit.** Every RT port commit carries one message paragraph naming the secondary upstream and its author ("Ported code: Serious-Engine-RT (…, GPL-2.0-only) by Sultim Tsyrendashiev; original copyright notices kept."). Trees, authors and author dates are unchanged.
3. **VS-E adaptations, folded into the original commits:** the RT menu options live in the new SSTRE files `SamT?E/SSTRE/Menu/RenderingOptionsRT.cfg`; the retail `Scripts/Menu/RenderingOptions.cfg` gets one `Include: TFNM SSTRE\Menu\RenderingOptionsRT.cfg` line (new `Include:` keyword in `SeriousSam/VarList.cpp`). The RT world tuning tables moved from `Scripts/RT/` to `SamT?E/SSTRE/RT/WorldTuning.txt` (loader paths in `CustomInfoTuning.cpp`). Linux: `SE1_RAYTRACING` (1 for MSVC x64 Vulkan builds, 0 for CMake), stubs for the `CGfxLibrary` RT entry points and `RT_Particle_*` hooks, `#if SE1_RAYTRACING` around the blocks that use SSRT types; TFE in `4e642c39`, TSE in `c8fcfbf8`.
4. **Publication rule for the TSE tuning table (lead decision):** it may contain only level names and texture paths that also appear in the public TFE table. Check after every E5 data change: `comm -23` of the sorted `.tex` lines of the TSE file vs the TFE file must be empty. At `c1537cfd`: **empty** (57 lines in each file).
5. **Windows build.** `scripts\build-win.ps1` (EXP-001/EXP-016 procedure): `MSBuild SamT?E.sln /m /t:Ecc;Engine;Entities(MP);Game(MP);Shaders;SeriousSam;libogg;libvorbis;libvorbisfile;amp11lib /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=v143 /p:WindowsTargetPlatformVersion=10.0.22000.0 /p:UseOfMfc=false /p:RTGL1_SDK_PATH=<copy of RTGL1 Include> /p:RTGL1_LIB_PATH=<clean-room build>`, trusted win_flex/win_bison first on `PATH`, `TEMP` on G:. `scripts\build-all.ps1` runs TFE, TSE and the Linux build, each after `gpu-lock.ps1 wait-quiet`.
6. **Linux build.** `git archive HEAD` → the EXP-001 container script unchanged (`cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build && cmake --install`, TFE + TSE), clean container. The apt step needs the network; nothing is run there.
7. **Runtimes.** `scripts\assemble.ps1 [-BinOnly]`: robocopy of the Phase-1 runtimes `local-work\runtime\cvk-t?e` (Steam data) without `Bin`, logs and persistent settings, plus our `Bin`, the branch's `Scripts\Menu\RenderingOptions.cfg`, `Controls\00-Default.ctl` and `SSTRE\` tree, and for both games the RT data of EXP-009 (45 SPIR-V, blue noise, water normal map) and the clean-room `RayTracedGL1.dll`.
8. **Runtime tests.** `scripts\session.ps1` (matrix; `-Only <regex>`, `-KeyStart <s>`) and `scripts\session-tse-rt.ps1 -Part A|B|C`, each in its own hold through `gpu-lock.ps1 run -Owner VSE`, every hold ≤ 30 min (`scripts\sessions-p2.ps1`: four holds; VS-A held the lock in between). Harness `scripts\run-game.ps1`: windowed 1600×900, single player, `ser_bEnumeration=0`, `srt_bVSync=0; srt_bDebugValidation=0`, master-server cvars at their compiled-in defaults, PrintWindow captures with focus state, `Get-NetTCPConnection`/`Get-NetUDPEndpoint` of the game process at each capture, process always killed; **game watchdog** (`G:\sstre-tmp\lib\watchdog-start.ps1`, lead rule 1c: hung ≥ 20 s, flat-colour frame ≥ 15 s, RTGL1 error flood, 20 s grace) on every run. Error counts per run: lines `RTGL1 error` (release-build logging of failed RTGL1 calls) and validation-error lines in the copied `SeriousSam.log`. Synthetic 4096² texture: E4's `probe\gen.py` (own checker pattern, AssetCompiler `tex-replace`), removed again after the runs. Demos: `+demo Demos\auto-demo000N.dem` with `dem_bProfile=1; dem_iProfileRate=5; dem_strPostExec="DumpDemoProfile(); Quit();"` (EXP-011). TSE level runs press ESC at 18 s (NETRICSA) and capture at 24/32 s (`1_2`: also at 90/180 s, 190 s in total).
9. **Linux runtime / network.** `linux\netaudit\run*.sh`: E2's `ded-netaudit.sh` in `sstre-e2-netaudit:local` with `--network none`, TFE `01_Hatshepsut` and TSE `1_0_InTheLastEpisode` (at `7b8d0e1f`; the later commits change only RT code and data, which the Linux build does not compile).
10. **Series.** In `G:\sstre-tmp\vse\wt-engine-pub` (`feature/integrated-series` from SSTRE-Engine `main` `f9f96f75`), `SSTRE_UPSTREAM_CACHE=G:\sstre-tmp\vse\upstream-cache`:
    ```sh
    python tools/sstre_patches.py export classic-vk --from sprint2/integration --source-repo G:/sstre-tmp/vse/wt-engine \
           --validator <umbrella>/scripts/validate_repo.py --max-patch-kib 1280 --verify     # --flagged-context 1 is the default
    python tools/sstre_patches.py check --max-patch-kib 1280 --validator <umbrella>/scripts/validate_repo.py   # no --allow-flagged
    ```
11. **Release binaries.** `scripts\make-release-bin.ps1` → `G:\sstre-tmp\vse\release-bin\` with `manifest.json`.

## Results ([EXP] unless labelled otherwise)

### R1. Integrated commit list (`sprint2/integration`, local, not pushed)

Base `f7c3605f` = `sprint2/no-master-server` (Classic-VK `510d36f9` + 6 build commits `d4c43f15 9cb83850 bbf04b04 4677963f 4206e38f ba0c12e8` + POC-32 `f7c3605f`). On top, linear, 27 commits; all applied without conflicts:

| # | Commit | Source commit (track) | Subject |
|---|---|---|---|
| 8 | `f1a01161` | `15c567c0` (E4) | fix(gfx): stop FilterBitmap row buffer overflow on textures wider than 2048 px |
| 9 | `0312e6ff` | `3a4d07cc` (E4) | feat(gfx): allow tex_iNormalSize 12 and report oversized texture uploads |
| 10 | `700ecdb1` | `2f9251dc` (E1) | rt(engine): import the ray-tracing layer from Serious-Engine-RT (TFE) |
| 11 | `a2b72060` | `7c0fcf50` (E1) | rt(engine): port the GAT_RT hooks into the Classic-VK graphics/render code |
| 12 | `90df5107` | `e62b6fcc` (E1) | rt(engine): make ray tracing runtime-optional (delay-loaded RTGL1, no fatal probe) |
| 13 | `15a340b0` | `1fd1cd9f` (E1) | rt(entities): port the TFE RT entity hooks (flashlight, HUD, weapon render) |
| 14 | `715a104e` | `7d80a7d7` (E1) | rt(game): select GAT_RT at runtime in the game exe, raster stays default |
| 15 | `ecb6e50f` | `750b1047` (E1) + VS-E | rt(menu): offer "Ray Tracing" as a graphics API and add the RT rendering options |
| — | *(skipped)* | `d9f86637` (E1) | fix(gfx): FilterBitmap row buffer overflow … (superseded by E4's `15c567c0`) |
| 16 | `851e2a5c` | `005bd78c` (E1) | rt(engine): log failed RTGL1 calls in release builds |
| 17 | `2546b3ce` | `9c8c06b9` (E3) | feat(bench): add +demo command-line option for benchmark playback |
| 18 | `25323971` | `b7c7e998` (E3) | fix(game): finish demo playback cleanly (profile report, post-exec) |
| 19 | `4e642c39` | new (VS-E) | build(linux): compile TFE without the ray-tracing layer (SE1_RAYTRACING=0) |
| 20 | `10078a73` | `adc4f40c` (E5) | rt(engine,tse): import the ray-tracing layer into the TSE engine tree |
| 21 | `41ac9d02` | `2b0cfa04` (E5) | rt(engine,tse): port the GAT_RT hooks into the TSE graphics/render code |
| 22 | `b61c3ccf` | `d2ef76d1` (E5) | rt(engine,tse): make ray tracing runtime-optional in the TSE engine |
| 23 | `1d0c8dc6` | `c7d53e1e` (E5) | rt(game,tse): select GAT_RT at runtime in the TSE game exe |
| 24 | `ba5b9b38` | `0a90724b` (E5) + VS-E | rt(menu,tse): offer "Ray Tracing" as a graphics API in the TSE menu |
| 25 | `5cdad742` | `d9e505d1` (E5) | rt(engine,tse): log failed RTGL1 calls in release builds (TSE) |
| 26 | `0dcde5eb` | `61668251` (E5) | rt(entities,tse): port the RT entity hooks to EntitiesMP |
| 27 | `5de4bf94` | `bf625709` (E5) | rt(controls,tse): bind the RT flashlight in the default TSE controls |
| 28 | `fda08eb6` | `938ba5ab` (E5) + VS-E | rt(engine,tse): load per-world RT tuning from SSTRE/RT/WorldTuning.txt |
| 29 | `771588e1` | `d1ddb552` (E5) + VS-E | rt(engine,tfe): use the runtime RT tuning table in the TFE tree too |
| 30 | `c8fcfbf8` | new (VS-E) | build(linux): compile TSE without the ray-tracing layer (SE1_RAYTRACING=0) |
| 31 | `7b8d0e1f` | `f71bd2cc` (E5) + VS-E | rt(data,tse): explicit RT entries for the showcase worlds 1_0 and 1_1 |
| 32 | `804448a8` | `4e1053be` (E5) | rt(data,tse): disable RT "haze" by default; fixes darkness beyond ~20 m (path mapped to `SamTSE/SSTRE/RT/WorldTuning.txt`) |
| 33 | `67faf472` | `1c59be04` (E5) | rt(tse,tfe): batch brush polygons per entity; respect RTGL1 static capacity |
| 34 | `c1537cfd` | `958b2bd5` (E5) | rt(tse,tfe): don't build RT particles outside the RT particle pass |

Head **`c1537cfd4574971da3f2903e363eb9ee606279a3`**, tree **`3d2a6261a59c2db2a958fed67d3d2ee60f278798`**. "+ VS-E" = adaptation folded in (procedure step 3). Authorship and author dates are preserved; there is no Signed-off-by anywhere. `67faf472` and `c1537cfd` touch the same RT-layer paths in both trees as on `sprint2/rt-tse`, so no path mapping was needed. [SRC, E5/EXP-018] `67faf472`: RTGL1 holds at most 4096 static BLAS geometries and silently drops the rest. The brush exporter cut a geometry at every material change, so `1_2_Palenque` produced 5127 parts; it now produces 1405. `c1537cfd` fixes a null-scene crash in `RTParticles.cpp` caused by TSE first-person chainsaw particles.

### R2. Builds (at `c1537cfd`)

| Build | Result |
|---|---|
| Windows x64 Release TFE, runtime targets, RT | **pass**, exit 0, 104 s (incremental) |
| Windows x64 Release TSE, runtime targets, RT | **pass**, exit 0, 68 s (incremental) |
| Linux x64 TFE + TSE, clean container (EXP-001 script) | **pass**, rc 0, 165 s wall, the same 20 output files as EXP-001/EXP-010 (`SE1_RAYTRACING=0`) |
| String checks (at `7b8d0e1f`, unaffected since) | `sam.ostap.eu`: 0 in TFE/TSE `Engine.dll`, `libEngine.so`, `libEngineMP.so`; "master server disabled at compile time" present in all four |

Earlier history: the first Linux build after E1's transplant failed (`SSRTObjects.h:20: fatal error: RTGL1/RTGL1.h: No such file or directory`); `4e642c39` fixed it. E5's TSE port got the same fix in `c8fcfbf8`.

### R3. Runtime matrix (Windows, `c1537cfd`, 2026-11-28 14:22–15:17, seven lock holds of 2–13 min)

"OK" means the process was alive and `Responding` at the end, the menu rendered (or, for levels, `  started.` is in the log), and the window captures exist. **The game window was in the foreground in every capture. All 43 run logs have 0 RTGL1 errors and 0 validation errors.** Sockets: 0 TCP connections and 0 UDP endpoints at every sampling point (all runs, single player).

Matrix (`session.ps1`; levels TFE `01_Hatshepsut`, TSE `1_1_Palenque`):

| Runs | Result |
|---|---|
| T01–T04 TFE menu/level Vulkan, OpenGL | 4/4 OK |
| T05/T06 TFE menu/level RT | OK / OK |
| T07–T09 TFE: RT requested with RTGL1 absent (raster fallback), Vulkan level | 3/3 OK |
| T10 TFE demo `auto-demo0002` | ran to completion, quit by itself at 56 s (exit code 1, see deviations) |
| T11–T14 TFE TechTest with a synthetic 4096² texture (Vulkan default, Vulkan/OpenGL HD settings, RT) | 4/4 OK |
| S01–S04 TSE menu/level Vulkan, OpenGL | 4/4 OK |
| S05 TSE demo `auto-demo0002` | ran to completion, quit by itself at 86 s |
| S06 TSE 4096² Vulkan HD | OK |
| S07–S10 TSE RT menu, RT level, RT with RTGL1 absent, RT 4096² | 4/4 OK |
| M01–M04 menu navigation to the rendering options | **inconclusive**, tried twice (the second time with keys at 18 s). In all four runs, including the Vulkan run M03, the capture shows the *Choose level* screen instead of the rendering options. [ASM] The mouse pointer rests over the game window, and its hover selection (*Mods* is highlighted in the T05 menu capture) disturbs the keyboard navigation. This is not an engine change: no commit after `7b8d0e1f`, where M01–M04 passed, touches menu code |

Watchdog: `WATCHDOG=ok` in all 28 matrix runs and the 4 menu re-runs.

TSE RT re-test (`session-tse-rt.ps1`):

| Run | API | Result | RTGL1 / validation errors | Watchdog |
|---|---|---|---|---|
| R01 / R02 `1_1_Palenque` | RT / Vulkan | OK / OK | 0 / 0 | ok |
| R03 / R04 `2_1_Ziggurrat` | RT / Vulkan | OK / OK | 0 / 0 | ok |
| R05 `auto-demo0001` (*Valley of the Jaguar*, `1_2_Palenque`) | RT | **ran to completion**: 13537 frames in 139.7 s, 96.9 FPS average, quit by itself at 144 s | 0 / 0 | ok |
| R06 `1_2_Palenque` level start | RT | renders (HUD visible, ~100 FPS, responsive), but the 3D view at the spawn cave is **black** from ~22 s; the watchdog **KILLED** it at 38.7 s: flat colour #000000 ≥ 15 s | 0 / 0 | **KILLED** |
| R11 = R06 plus the flashlight key (L), with `SSTRE_WATCHDOG_ARGS=-UniformSec 200` for this run only | RT | alive and `Responding` for the full 190 s, `  started.`, ~105 FPS; the 3D view stays black in all four captures (24/32/90/180 s), and the weapon is not visible either. [ASM] The posted L key does not reach the game's input, so the flashlight stayed off | 0 / 0 | ok (uniform frame logged, no kill) |
| R07 `auto-demo0001` | Vulkan | ran to completion (143.8 FPS avg), quit by itself at 145 s | 0 / 0 | ok |
| R08 `1_2_Palenque` level, 190 s | Vulkan | OK (cave lit, dim) | 0 / 0 | ok |
| R09 `auto-demo0001` | OpenGL | ran to completion (169.2 FPS avg), quit by itself at 145 s | 0 / 0 | ok |
| R10 `1_2_Palenque` level, 190 s | OpenGL | OK | 0 / 0 | ok |

- **Haze fix [EXP]:** in RT the distant geometry is lit. The R05 capture at 90 s (open valley, with pyramids and hills several hundred metres away) shows full daylight to the horizon. The `2_1_Ziggurrat` RT and Vulkan captures at 32 s match in brightness, and the `1_1_Palenque` RT capture (start under water) shows the lit surface and vegetation above. Before `804448a8`, everything beyond ~20 m was dark (EXP-018 A1).
- **1_2 RT fixes [EXP]:** the full `1_2_Palenque` demo plays in RT with 0 RTGL1 errors. Before `67faf472` it ended in an `RG_CANT_UPDATE_TRANSFORM` flood and then an exit or hang (EXP-018).
- **Watchdog kill R06:** per lead rule 1c this counts as a reproduced flat-colour freeze. However, the game was alive and drew the HUD at ~100 FPS, and R11 ran the full 190 s. [ASM] This is E5's open issue "1_2 cave spawn is black in RT (unlit, also with the pre-fix engine; flashlight shows the geometry)", i.e. a tuning problem, not a hang. The demo starts elsewhere and is not affected.
- RT frame rate in the `2_1_Ziggurrat` capture: 15.8 FPS (Vulkan: 143.9); `1_1_Palenque`: 74.6 FPS. These are single readings, not a benchmark.

### R4. Master-server traffic

- **Windows clients** (all runs above, master cvars at compiled-in defaults, single player): 0 TCP connections and 0 UDP endpoints at every sampling point. This is not a packet capture; a single-player client opens no sockets.
- **Linux dedicated servers** (E2 harness, `--network none`, 40 s, TFE `01_Hatshepsut`, TSE `1_0_InTheLastEpisode`, at `7b8d0e1f`): the log shows "GameAgent: master server disabled at compile time (SSTRE_MASTER_SERVER=0), LAN queries only" and `  started.`; 0 captured packets, 0 DNS packets, 0 heartbeat lines, and `ostap` appears 0 times in strace. With `--network none` and no host-name entry, the server's lookup of its own host name tries the unreachable resolver [SRC: `CommunicationInterface.cpp:376-384`]. With `--hostname sstre-ded --add-host sstre-ded:127.0.0.1`: 0 non-loopback connect/send calls for both games.

### R5. Patch series and tooling

- **Tool** (SSTRE-Engine `418eeea3`, `191a1bbb`): `export --flagged-context N` (default 1) and `--path-context GLOB=N`, plus the per-patch review list `patches/classic-vk/REVIEWED-FLAGGED.json` (patch SHA-256, paths, reviewer, date, rationale). Without `--allow-flagged`, `check` accepts a flagged section only if a matching review entry exists; any change to the patch invalidates the entry.
- **Export** from `c1537cfd`: **34 patches** (`0001…0034`). 0001–0031 are byte-identical to the previous export (from `7b8d0e1f`). New: 0032 (haze default, 4.2 KiB), 0033 (brush batching, 35 KiB), 0034 (RT particles, 6.2 KiB). The largest patch is 0010 (RT layer import, TFE).
- **verify** (round trip on a fresh apply at `510d36f9`): the applied tree **`3d2a6261a59c2db2a958fed67d3d2ee60f278798`** equals `sprint2/integration^{tree}`. Applied head: `87969168ee6c9d77f58382b87c94c2277191b4e3`. The series contains no deletions.
- **check without `--allow-flagged`** (`--max-patch-kib 1280`, umbrella validator lists): `patches/` has 48 patches (all series), **0 errors** and 67 warnings. The warnings cover new RT files without an SPDX tag (they keep Sultim Tsyrendashiev's original GPL-2.0 notice by design), the six reviewed flagged sections, and vendored third-party files in other series. 0032–0034 produce no warning and touch no EXP-004 flagged path (`Engine/Raytracing/*` and `SSTRE/RT/*`), so they need no new review.

**Flagged patches (EXP-004):** exported with 1 line of context; the lead reviewed all of them on 2026-11-28.

| Patch | File | Flag | Change |
|---|---|---|---|
| 0013 | `SamTFE/Sources/Entities/Common/HUD.cpp` | H6 | RT hooks |
| 0013 | `SamTFE/Sources/Entities/Player.es` | H6 | flashlight toggle, RT-only `BodyRemoveItem()` |
| 0013 | `SamTFE/Sources/Entities/PlayerWeapons.es` | H6 | first-person weapon render flag |
| 0015 | `SamTFE/Scripts/Menu/RenderingOptions.cfg` | G4 | one `Include:` line; RT options in the new SSTRE file `SamTFE/SSTRE/Menu/RenderingOptionsRT.cfg` |
| 0024 | `SamTSE/Scripts/Menu/RenderingOptions.cfg` | G4 | one `Include:` line (`SamTSE/SSTRE/Menu/RenderingOptionsRT.cfg`) |
| 0027 | `SamTSE/Controls/00-Default.ctl` | G4 | +7 lines: "Flashlight" button on L (the controls parser has no include) |

The tuning tables are SSTRE files under `SSTRE/RT/`, not under the flagged retail `Scripts/` tree. This replaces the plan in the previous version of this report.

### R6. SSTRE-Engine branch `feature/integrated-series` (from `main` `f9f96f75`, local, not pushed)

| Commit | Content |
|---|---|
| `418eeea3` | feat(tools): per-path context for exported patches (tool, tests, docs) |
| `eacd7f44` | feat(patches): integrated classic-vk series v1; README (provenance, flagged list); `THIRD_PARTY_NOTICES.md` row for the code ported from Serious-Engine-RT |
| `191a1bbb` | feat(tools): per-patch review list for EXP-004 flagged files |
| `d0fa5559` | feat(patches): 0015 keeps the RT menu options out of the retail script; review list |
| `e7486eef` | feat(patches): classic-vk series with the TSE ray-tracing port (E5), 31 patches |
| `9fe05505` | docs(patches): lead reviews of 0013/0015/0024/0027 |
| **`ecb285c5`** | feat(patches): classic-vk 0032–0034 (TSE RT haze default, 1_2 RT fixes); README table |

The branch contains neither `upstream/classic-vk-main` nor `upstream/rt-main`, only patches, docs and tools.

### R7. Local release binary set (0.1.0-preview2)

`G:\sstre-tmp\vse\release-bin\`: 142 files + `manifest.json` (name "SSTRE Classic-VK integrated engine 0.1.0-preview2", commit `c1537cfd`, tree, toolchain, SHA-256 per file). It holds the Windows `SamTFE/` and `SamTSE/` game-root overlays (`Bin` incl. the clean-room `RayTracedGL1.dll`, `Scripts/Menu/RenderingOptions.cfg`, `Controls/00-Default.ctl`, `SSTRE/` incl. the haze-0 TSE tuning table, 45 SPIR-V, blue-noise texture) and the Linux `Bin` sets. Local disk only (ADR-0006); not distributed.

## Deviations, modifications and failures

- **R06 watchdog kill** (flat black frame at the `1_2_Palenque` RT spawn cave), see R3. The re-run R11 raised the uniform-frame limit for that run only; the watchdog stayed active for hang and error-flood detection.
- **M01–M04 inconclusive** (menu navigation disturbed, see R3). The `Include:` path is covered by the pass at `7b8d0e1f` and has not changed since.
- The `1_2` demo runs last 140 s (the length of the recorded demo), not 3 min; the demo runs to its end in all three APIs. The `1_2` level runs in RT, Vulkan and OpenGL last 190 s.
- **Demo exit code 1** after the scripted `Quit()` in both games. [ASM] On Windows the engine's normal quit path returns 1; the log shows an orderly shutdown.
- **Persistent cvars:** `tex_iNormalSize=12` and the custom video setup from T12/T13 persist into T14. `sam_iGfxAPI` is set in every run.
- Known issue (lead-accepted): in Vulkan mode the RT options are listed in the rendering-options menu (disabled, not hidden).
- Not done: 10-minute play sessions; a validation-layer run on the integrated build (`srt_bDebugValidation=0` in all runs; EXP-009 R5 covers the same RT code); RT on Linux (EXP-005 WP6).

## Interpretation

- [EXP] The five sprint-2 engine lines (E1 RT transplant, E2 master-server switch, E3 demo playback, E4 texture fix, E5 TSE RT) combine without conflicts. One Windows binary set runs TFE and TSE in Vulkan, OpenGL and RT, falls back to raster without RTGL1, survives 4096-wide textures and plays demos to the end in all three APIs, with 0 RTGL1 errors in 43 runs.
- [EXP] E5's haze default fixes the far-field darkness in TSE RT, and the brush batching makes `1_2_Palenque` playable in RT. Its spawn cave is still unlit in RT (tuning).
- [EXP] The published series reproduces the integration tree exactly from the public pin. The vertical-slice engine is fully described by 34 SSTRE patches, and CI's `check` passes without `--allow-flagged`.

## Impact on ADRs, dossiers and backlog

- ADR-0008 item 4: `--flagged-context 1` is the tool default; flagged sections pass CI only with a per-patch lead review entry.
- ADR-0007 / EXP-009 open question 1: the build-time switch `SE1_RAYTRACING` (0 for CMake builds) exists in both trees; Windows x64 keeps RT runtime-optional.
- Backlog: VS-E engine integration is done for 0.1.0-preview2. Follow-ups: `1_2_Palenque` RT spawn lighting (E5); RTGL1 should report dropped uploads (RTGL1 tree); fix the M01–M04 harness (park the pointer outside the window) and the in-game key injection (flashlight); RT on Linux (WP6).

## Open questions

None at owner level.
