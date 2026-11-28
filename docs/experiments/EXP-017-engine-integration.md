# EXP-017: Integrated Classic-VK engine line and its `classic-vk` patch series

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | Sprint 2 track VS-E (vertical slice, engine integration); POC-27 follow-up (per-path context), POC-29/30/32, E3/E4 fixes |
| Status | **complete for the pre-E5 scope**. TSE ray tracing (track E5, `sprint2/rt-tse`) is not integrated yet; the rebase plan is below |
| Environment | Windows 11 Pro 10.0.22631, Intel i5-11600K, RTX 4070 12 GB, driver 616.64. VS 2022 17.5 / MSVC 14.35.32215 (v143), Windows SDK 10.0.22000.0, WinFlexBison 2.5.25 (trusted copy), Vulkan SDK 1.4.363.0, Git 2.55.0.windows.3, Python 3.10.11. Linux: Docker 20.10.23, `ubuntu:22.04@sha256:b000e69a50ff940390233025e7a337fb8469b509e2334fa4d018ac30f3e18cdb` (gcc 11.4.0, CMake 3.22.1, Bison 3.8.2, Flex 2.6.4), runtime/audit image `sstre-e2-netaudit:local` (EXP-010) |
| Inputs | SSTRE-Engine local branches `sprint2/no-master-server` (`f7c3605f` = `phase1/cvk-build` + POC-32), `sprint2/tex4096-crash` (E4), `sprint2/rt-transplant` (E1), `sprint2/bench-fixes` (E3, head `b7c7e998`, no newer commits at integration time). RTGL1 clean-room build of `sprint2/ktx2-cleanroom` `0eb4c4a` (EXP-009, DLL SHA-256 prefix `42bdd141`). Owner's Steam *Serious Sam Classic* TFE and TSE data, copied into private runtimes |

All scripts, logs, screenshots and runtimes are local under `G:\sstre-tmp\vse\` (`scripts\`, `logs\`, `runs\`, `linux\`, `runtime-tfe\`, `runtime-tse\`). Nothing was pushed.

## Goal and success criteria

1. One linear integration branch `sprint2/integration` with the original commits of E4, E1 (without its superseded `FilterBitmap` fix `d9f86637`) and E3, on top of `phase1/cvk-build` + POC-32.
2. Windows x64 Release builds of TFE and TSE, Linux x64 builds of both in the pinned container.
3. Runtime tests under the GPU lock: TFE menu + level in Vulkan, OpenGL and RT; TSE menu + level in Vulkan and OpenGL; RTGL1-absent fallback; a 4096-wide synthetic texture loads; a demo plays to completion; no master-server traffic.
4. The `classic-vk` series exported from that branch, `check` clean (flagged files with minimal context and listed), `verify` round trip with equal tree hash, notices updated, committed on SSTRE-Engine `feature/integrated-series`.

## Procedure (exact, reproducible)

1. **Branch.** `git -C …\SSTRE-Engine worktree add G:\sstre-tmp\vse\wt-engine -b sprint2/integration sprint2/no-master-server` (all git calls with `-c core.autocrlf=false`). Then, in this order, `git cherry-pick` of `15c567c0 3a4d07cc` (E4), `2f9251dc 7c0fcf50 e62b6fcc 1fd1cd9f 7d80a7d7 750b1047 005bd78c` (E1, **`d9f86637` skipped**), `9c8c06b9 b7c7e998` (E3). Every pick applied without conflicts. `git diff sprint2/tex4096-crash HEAD -- '*/Graphics/Graphics.cpp'` is empty: only E4's `FilterBitmap` fix is present.
2. **Credit.** The six RT port commits got one message paragraph naming the secondary upstream and its author ("Ported code: Serious-Engine-RT (…, GPL-2.0-only) by Sultim Tsyrendashiev; original copyright notices kept."), applied with `git filter-branch --msg-filter` on `f7c3605f..sprint2/integration`. Trees, authors and dates are unchanged; the E4 commits keep their cherry-pick SHAs. A first attempt wrote CRLF messages (Python text-mode stdout on Windows); it was reset and redone with binary stdout.
3. **Linux fix (new commit).** The first container build failed: `Engine/Raytracing/SSRTObjects.h:20: fatal error: RTGL1/RTGL1.h: No such file or directory` (from `RenderModel.cpp`). E1's RT layer is built only by the Windows vcxproj (EXP-009 scope cut). New commit `c81779ac` adds `SE1_RAYTRACING` (1 for MSVC x64 Vulkan builds, 0 otherwise, set to 0 explicitly in `SamTFE/Sources/CMakeLists.txt`), stubs for the `CGfxLibrary` RT entry points and `RT_Particle_*` hooks in `Gfx_RayTracing.cpp`, and `#if SE1_RAYTRACING` around the blocks that use SSRT types (`DrawPort.cpp` 10 regions, `Render.cpp`, `RenderModel.cpp`, `Gfx_wrapper.cpp`). CMake now also compiles `Gfx_RayTracing.cpp`, `RTGL1Loader.cpp` (returns FALSE off Windows) and `RTModelNormalsFix.cpp` (no RTGL1 dependency, keeps model normals the same as on Windows). +88 lines, Windows unchanged. Iterated with an incremental container (`sstre-vse-build:local`, `FROM` the pinned digest plus the EXP-001 package list and rsync, builds with `--network none`).
4. **Windows build.** `scripts\build-win.ps1` (EXP-001/EXP-016 procedure): `MSBuild SamT?E.sln /m /t:Ecc;Engine;Entities(MP);Game(MP);Shaders;SeriousSam;libogg;libvorbis;libvorbisfile;amp11lib /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=v143 /p:WindowsTargetPlatformVersion=10.0.22000.0 /p:UseOfMfc=false /p:RTGL1_SDK_PATH=<copy of RTGL1 Include> /p:RTGL1_LIB_PATH=<clean-room build>`, trusted win_flex/win_bison first on `PATH`, `TEMP` on G:.
5. **Linux build.** `git archive HEAD` → the EXP-001 container script unchanged (`cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build && cmake --install`, TFE + TSE). The apt step needs the network; nothing is run there.
6. **Runtimes.** `scripts\assemble.ps1`: robocopy of the Phase-1 runtimes `local-work\runtime\cvk-t?e` (Steam data) without `Bin`, logs and persistent settings, plus our `Bin`, the branch's `Scripts\Menu\RenderingOptions.cfg`, and for TFE the RT data of EXP-009 (45 SPIR-V, blue noise, water normal map) and the clean-room `RayTracedGL1.dll`.
7. **Runtime tests.** `scripts\session.ps1` through `gpu-lock.ps1 run -Owner VSE` (one hold). Harness `scripts\run-game.ps1` (derived from E1's): windowed 1600×900, single player, `ser_bEnumeration=0`, `srt_bVSync=0; srt_bDebugValidation=0`, master-server cvars **left at their compiled-in defaults**, PrintWindow captures with focus state, `Get-NetTCPConnection`/`Get-NetUDPEndpoint` of the game process at each capture, process always killed. Synthetic 4096² texture: E4's `probe\gen.py` (own checker pattern, AssetCompiler `tex-replace`, mex kept) on a TechTest floor texture (asset path local, GATE-05), removed again after the runs. Demo: `+demo Demos\auto-demo0002.dem` with `dem_bProfile=1; dem_iProfileRate=5; dem_strPostExec="DumpDemoProfile(); Quit();"` (EXP-011).
8. **Linux runtime / network.** `linux\netaudit\run*.sh`: E2's `ded-netaudit.sh` (tcpdump, `ss`, `strace` of connect/send/bind, 40 s `DedicatedServer`, master cvars at defaults) in `sstre-e2-netaudit:local` with `--network none`, TFE `01_Hatshepsut` and TSE `1_0_InTheLastEpisode`.
9. **Series.** In `G:\sstre-tmp\vse\wt-engine-pub` (`feature/integrated-series` from SSTRE-Engine `main` `f9f96f75`), `SSTRE_UPSTREAM_CACHE=G:\sstre-tmp\vse\upstream-cache`:
   ```sh
   python tools/sstre_patches.py fetch --offline --source classic-vk=<SSTRE-Engine> classic-vk
   python tools/sstre_patches.py export classic-vk --from sprint2/integration --source-repo G:/sstre-tmp/vse/wt-engine \
          --validator <umbrella>/scripts/validate_repo.py --allow-flagged --verify      # --flagged-context 1 is the default
   python tools/sstre_patches.py verify classic-vk --from sprint2/integration --source-repo G:/sstre-tmp/vse/wt-engine
   python tools/sstre_patches.py check --allow-flagged --max-patch-kib 1280 --validator <umbrella>/scripts/validate_repo.py
   SSTRE_UMBRELLA_VALIDATOR=<umbrella>/scripts/validate_repo.py python -m unittest discover -s tools/tests
   python <umbrella>/scripts/validate_repo.py --root . --skip-schemas --forbidden-allowlist .github/workflows/sstre-forbidden-allowlist.txt
   ```

## Results ([EXP] unless labelled otherwise)

### R1. Integrated commit list (`sprint2/integration`, local, not pushed)

Base `f7c3605f` = `sprint2/no-master-server` (Classic-VK `510d36f9` + 6 build commits `d4c43f15 9cb83850 bbf04b04 4677963f 4206e38f ba0c12e8` + POC-32 `f7c3605f`). On top, linear, 12 commits:

| # | Commit | Source commit (track) | Subject |
|---|---|---|---|
| 8 | `f1a01161` | `15c567c0` (E4) | fix(gfx): stop FilterBitmap row buffer overflow on textures wider than 2048 px |
| 9 | `0312e6ff` | `3a4d07cc` (E4) | feat(gfx): allow tex_iNormalSize 12 and report oversized texture uploads |
| 10 | `700ecdb1` | `2f9251dc` (E1) | rt(engine): import the ray-tracing layer from Serious-Engine-RT (TFE) |
| 11 | `a2b72060` | `7c0fcf50` (E1) | rt(engine): port the GAT_RT hooks into the Classic-VK graphics/render code |
| 12 | `90df5107` | `e62b6fcc` (E1) | rt(engine): make ray tracing runtime-optional (delay-loaded RTGL1, no fatal probe) |
| 13 | `15a340b0` | `1fd1cd9f` (E1) | rt(entities): port the TFE RT entity hooks (flashlight, HUD, weapon render) |
| 14 | `715a104e` | `7d80a7d7` (E1) | rt(game): select GAT_RT at runtime in the game exe, raster stays default |
| 15 | `b83869ac` | `750b1047` (E1) | rt(menu): offer "Ray Tracing" as a graphics API and add the RT rendering options |
| — | *(skipped)* | `d9f86637` (E1) | fix(gfx): FilterBitmap row buffer overflow … (superseded by E4's `15c567c0`) |
| 16 | `d744d8dc` | `005bd78c` (E1) | rt(engine): log failed RTGL1 calls in release builds |
| 17 | `5ccfaa2c` | `9c8c06b9` (E3) | feat(bench): add +demo command-line option for benchmark playback |
| 18 | `e4900fb3` | `b7c7e998` (E3) | fix(game): finish demo playback cleanly (profile report, post-exec) |
| 19 | `c81779ac` | new (VS-E) | build(linux): compile TFE without the ray-tracing layer (SE1_RAYTRACING=0) |

Head `c81779ac4f12f4c0e26bf98aba101a83e42604df`, tree `27f3c35f5ee375483b312ac707bc58698171a025`. Authorship and author dates of all picked commits are preserved; the six RT port commits (10–15) carry the credit paragraph (procedure step 2). No Signed-off-by anywhere.

### R2. Builds

| Build | Result |
|---|---|
| Windows x64 Release TFE, runtime targets (first full build) | **pass**, exit 0, 173 s (final incremental after `c81779ac`: 167 s) |
| Windows x64 Release TSE, runtime targets | **pass**, exit 0, 127 s (final: 43 s, TSE tree unchanged by `c81779ac`) |
| Linux x64 TFE + TSE, before `c81779ac` | **fail**: `SSRTObjects.h:20: fatal error: RTGL1/RTGL1.h: No such file or directory` (TFE `RenderModel.cpp`) |
| Linux x64 TFE + TSE, at `c81779ac` (clean container, EXP-001 script) | **pass**, `BUILD_SECONDS=73`, the same 20 output files as EXP-001/EXP-010 |
| String checks | `sam.ostap.eu`: 0 in TFE/TSE `Engine.dll`, `libEngine.so`, `libEngineMP.so`. "master server disabled at compile time" present in all four. TFE `Engine.dll` references `RayTracedGL1.dll`; `libEngine.so` contains the "Ray tracing is not available in this build" stub message; Windows `Engine.dll` does not |

### R3. Runtime matrix (Windows, one GPU-lock hold 01:39:45–01:50:45, 20 runs)

"OK" = process alive and `Responding` at the end, menu rendered or `  started.` in the log for levels, plus a window capture. Levels: TFE `01_Hatshepsut`, TSE `1_1_Palenque`. Every capture was taken with the game window in the foreground (`FOCUS=True` in all 23 captures); no owner input is known to have reached a run.

| Run | API requested → created | Result |
|---|---|---|
| T01 / T02 TFE menu / level | Vulkan → "Vulkan context created" | OK / OK |
| T03 / T04 TFE menu / level | OpenGL → "OpenGL context created" | OK / OK |
| T05 / T06 TFE menu / level | RT → "Vulkan ray tracing context created", "RayTracedGL1.dll loaded" | OK / OK, intro cutscene path-traced with lens flares, HUD ≈ 460 FPS |
| T07 / T08 TFE menu / level, **RTGL1 absent** | RT → "Ray tracing unavailable: RayTracedGL1.dll not found" → "Cannot start ray tracing" → "Trying recovery mode 0..." → Vulkan | OK / OK (raster fallback) |
| T09 TFE level, RTGL1 absent | Vulkan | OK |
| T10 TFE demo `auto-demo0002` | Vulkan | **ran to completion**: "Demo playback: recorded quickload request, ending demo.", "Originally recorded: 7325 frames in 51.2 seconds => 143.1 FPS average.", profile dumped, post-exec `Quit()`: process exited by itself at 55.6 s (exit code 1) |
| T11 TFE TechTest, synthetic **4096×4096** texture, default settings | Vulkan | OK, log: `4096x4096 px, 3 mip(s) skipped, uploaded as 512x512 (… tex_iNormalSize=9)` |
| T12 / T13 same, `sam_iVideoSetup=3; tex_iFiltering=-2; tex_iNormalSize=12` | Vulkan / OpenGL | OK / OK, `0 mip(s) skipped, uploaded as 4096x4096` (max dimension 8192 / 32768) |
| T14 same texture | RT | OK, uploaded as 4096×4096 (persistent `tex_iNormalSize=12` from T12) |
| S01 / S02 TSE menu / level | Vulkan | OK / OK (NETRICSA at level start) |
| S03 / S04 TSE menu / level | OpenGL | OK / OK |
| S05 TSE demo `auto-demo0002` | Vulkan | **ran to completion**: "Originally recorded: 11454 frames in 80.3 seconds => 142.6 FPS average.", self-quit at 86.3 s (exit code 1) |
| S06 TSE TechTest, synthetic 4096² wall texture, HD settings | Vulkan | OK, `uploaded as 4096x4096` |

- The texture runs used the default `tex_iFiltering=-2` of `Initial.ini` in T11 and an explicit `-2` in T12–T14/S06, i.e. the filter path that overflowed before E4's fix (EXP-016). No crash in any run.
- Raster with RTGL1 present and absent behaves identically except for the RT entry; the menu offers "Ray Tracing" only in TFE (TSE has no RT yet).

### R4. Master-server traffic

- **Windows clients** (all 20 runs, master cvars at compiled-in defaults, single player): `Get-NetTCPConnection` and `Get-NetUDPEndpoint` for the game process returned **0 TCP connections and 0 UDP endpoints** at every one of the 23 sampling points (menus, levels, demos). Not a packet capture; a single-player client opens no sockets at all.
- **Linux dedicated servers** (E2 harness, `--network none`, 40 s, TFE `01_Hatshepsut`, TSE `1_0_InTheLastEpisode`): both log "GameAgent: master server disabled at compile time (SSTRE_MASTER_SERVER=0), LAN queries only" and `  started.`; 0 captured packets, 0 DNS packets, 0 heartbeat lines, `ostap` 0 times in strace.
  - First pair: strace showed 2 `connect(…, 192.168.65.7:53) = -1 ENETUNREACH` each. [SRC] This is the server's lookup of its **own host name** (`CommunicationInterface.cpp:376-384`, `gethostname` + `gethostbyname`), not GameAgent: with `--network none` Docker writes no host-name entry to `/etc/hosts`, so glibc falls back to the (unreachable) resolver. E2's runs had the entry and showed no such lookup.
  - Repeated with `--hostname sstre-ded --add-host sstre-ded:127.0.0.1`: **0** non-loopback connect/send calls for both games.

### R5. Patch series and tooling

- **Tool extension** (SSTRE-Engine `418eeea3`): `export --flagged-context N` (default 1) and `--path-context GLOB=N` (repeatable); the tool had only a global `--unified` before. Implementation and safety net: see `docs/sstre/patch-tooling.md` ("Per-path context"). `check` now prints the context of each touched flagged file. Unit tests: **34 tests, all pass** (60.9 s, umbrella validator list comparison enabled), incl. 2 new round-trip tests (flagged file gets 1 line while an ordinary file keeps 3; `--path-context` rule; invalid specs → exit 2).
- **Export** of `sprint2/integration`: 19 patches (`patches/classic-vk/0001…0019`); 0001–0007 byte-identical to the series on `main`. Largest patch 0010 (RT layer import), 343 KiB.
- **check** (with `--allow-flagged --max-patch-kib 1280` and the umbrella validator lists): `patches/`: **33 patches, 0 errors, 37 warnings** (26 of them: new RT files without an SPDX tag; they keep Sultim Tsyrendashiev's original GPL-2.0 notice by design). Without `--allow-flagged`: 4 errors (the flagged sections below).
- **verify** (round trip on a fresh apply at `510d36f9`): applied tree **`27f3c35f5ee375483b312ac707bc58698171a025`** = `sprint2/integration^{tree}` ✔. Reproducible applied HEAD `6ca6b3431d58e108cadc8987475ac0e2081c042a`. No deletions in the series.
- Umbrella `validate_repo.py --skip-schemas --forbidden-allowlist …` on the SSTRE-Engine branch: 0 errors, 0 warnings.

**Flagged patches (EXP-004), for lead review** — all exported with 1 line of context:

| Patch | File | Flag | Change |
|---|---|---|---|
| `0013-rt-entities-port-the-TFE-RT-entity-hooks-flashlight-` | `SamTFE/Sources/Entities/Common/HUD.cpp` | H6 | RT hooks (+19) |
| same | `SamTFE/Sources/Entities/Player.es` | H6 | flashlight toggle, `BodyRemoveItem()` guarded to GAT_RT (+24) |
| same | `SamTFE/Sources/Entities/PlayerWeapons.es` | H6 | first-person weapon render flag (+8/−2) |
| `0015-rt-menu-offer-Ray-Tracing-as-a-graphics-API-and-add-` | `SamTFE/Scripts/Menu/RenderingOptions.cfg` | G4 | RT options section appended (+162; 1 context line) |

### R6. SSTRE-Engine branch `feature/integrated-series` (from `main` `f9f96f75`, local, not pushed)

| Commit | Content |
|---|---|
| `418eeea3` | feat(tools): per-path context for exported patches (tool, tests, docs) |
| `eacd7f44` | feat(patches): integrated classic-vk series; `patches/classic-vk/README.md` (provenance, flagged list); `THIRD_PARTY_NOTICES.md` row for the code ported from Serious-Engine-RT (GPL-2.0-only, Sultim Tsyrendashiev, original notices kept, credited in the commit messages) |

The branch contains neither `upstream/classic-vk-main` nor `upstream/rt-main` (`git merge-base --is-ancestor` false for both); only patches, docs and tools.

### R7. Local release binary set

`G:\sstre-tmp\vse\release-bin\` (89 files, `manifest.json` with commit/tree SHAs, toolchain and SHA-256 per file): Windows `SamTFE/` and `SamTSE/` game-root overlays (`Bin`, `Scripts/Menu/RenderingOptions.cfg`; TFE also clean-room `RayTracedGL1.dll`, 45 SPIR-V, blue-noise texture) and the Linux `Bin` sets. Local disk only (ADR-0006); built from `c81779ac`, i.e. **before** the E5 TSE RT integration.

## Deviations, modifications and failures

- **Linux build failure** of the E1 transplant (R2), fixed by the new commit `c81779ac`. The Linux build is raster-only; RT on Linux remains EXP-005 WP6.
- **Commit messages rewritten** (credit paragraph) after the first export; the tree did not change and the series was re-exported and re-verified. One failed attempt (CRLF messages) was reset before use.
- **Persistent cvars:** `tex_iNormalSize=12` and the custom video setup from T12/T13 persisted into T14 (RT), which is why T14 uploads at full size. `sam_iGfxAPI` was set explicitly in every run.
- **Demo exit code 1** after the scripted `Quit()` in both games. [ASM] The engine's normal quit path returns 1 on Windows; the log shows an orderly shutdown (profile dump, "Renderer buffers cleared"). Not investigated.
- The harness log filter in `session.ps1` printed mostly joystick-probe lines; the logs were evaluated separately (R3). No game was started outside the lock; the session waited behind E3 and VS-A in the FIFO queue.
- Not done: 10-minute play sessions, validation-layer run on the integrated build (EXP-009 R5 is for the same RT code), CI `check` without `--allow-flagged` (see open questions).

## Interpretation

- [EXP] The four sprint-2 engine lines (E1 RT transplant, E2 master-server switch, E3 demo playback, E4 texture fix) combine without textual or functional conflicts: one Windows binary set runs TFE in Vulkan, OpenGL and RT and TSE in Vulkan and OpenGL, falls back to raster without RTGL1, survives 4096-wide textures and plays demos to the end.
- [EXP] The published series reproduces the integration tree exactly from the public pin, so the vertical slice engine is fully described by 19 SSTRE patches.
- [SRC] The integration needed one real fix: the RT layer had no build-time switch, so the CMake build broke. `SE1_RAYTRACING` is that switch; E5's TSE port must use it for `SamTSE` too (below).

## Plan for E5 (`sprint2/rt-tse`)

- `sprint2/rt-tse` currently has 10 commits on top of `sprint2/rt-transplant` (`005bd78c`), `adc4f40c..d1ddb552`.
- Rebase: `git rebase --onto sprint2/integration 005bd78c sprint2/rt-tse` (or cherry-pick `005bd78c..sprint2/rt-tse` onto `sprint2/integration` in the VS-E worktree). This drops nothing of E5 and never re-introduces `d9f86637`, because that commit lies below `005bd78c`. **Dry run [EXP]** in a throw-away detached worktree (removed afterwards): all 10 commits rebase **without conflicts** (59 files changed vs `sprint2/integration`).
- Required follow-ups before export: (1) mirror `c81779ac` for `SamTSE` (`SE1_RAYTRACING` guards and CMake list) so the Linux TSE build keeps compiling; (2) Windows + Linux rebuild, re-run this matrix plus TSE RT; (3) re-export and `verify`.
- [SRC] E5's commits add four more EXP-004 flagged paths: `SamTSE/Controls/00-Default.ctl` (G4), `SamTSE/Scripts/Menu/RenderingOptions.cfg` (G4), `SamTFE/Scripts/RT/WorldTuning.txt` and `SamTSE/Scripts/RT/WorldTuning.txt` (new files under the flagged `Scripts/` tree; additions carry no upstream context). They will need the same review.

## Impact on ADRs, dossiers and backlog

- ADR-0008 item 4: "prefer `--unified=1`" is now the tool default for flagged paths (`--flagged-context 1`).
- ADR-0007 / EXP-009 open question 1: a build-time switch now exists (`SE1_RAYTRACING`, 0 for CMake builds); Windows x64 builds keep RT runtime-optional.
- Backlog: VS-E engine integration done except E5; RT on Linux (WP6) unchanged; the patch CI needs a decision on flagged sections (below).

## Open questions

1. Lead: approve the four flagged sections (R5). CI's `check` runs without `--allow-flagged` and will fail on 0013/0015 until either CI passes `--allow-flagged` or a per-patch review list is added to the tool. Which do you want?
2. Lead/owner: patch 0015 appends 162 lines to the retail-identical `Scripts/Menu/RenderingOptions.cfg` (G4). Alternative: ship the RT options as a new SSTRE script file and add only a one-line include, so the patch touches the flagged file minimally.
