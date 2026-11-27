# EXP-005: Effort estimate for porting the Serious-Engine-RT backend into SeriousSamClassic-VK

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | POC-24 |
| Status | **complete (source analysis + patch-apply measurements). Nothing was built or run.** Build results from the parallel build agent can move the numbers; see §7. |
| Environment | Windows 11 Pro 10.0.22631, git 2.55.0.windows.3, Python 3.10.11 (`local-work\venv`). No compiler was invoked. |
| Inputs | SSTRE-Engine local branches `upstream/rt-main` = `0e7f223c` (RT v1.5) and `upstream/classic-vk-main` = `510d36f9`. RT fork point `77a955ba` (Serious-Engine-Vk lineage, per RD-001) and Croteam `b408e88`, both present in the same repo. RTGL1 clone `upstream/sultim-t_RayTracedGL1` at tag `v1.1.0` = `b1eb3d8`. Local Steam Classic TFE/TSE installs, read-only and aggregate counts only. |
| Scratch | `local-work\port\` (scripts `probe.py`, `filter_patch.py`, `scan_worlds.py`, `count_levels.py`; outputs `probe_files.tsv`, `rt_*_numstat.tsv`, `rt_code_*.patch`, `rt_only_*.patch`, `conflict_*.txt`). The worktree `local-work\port\cvk` is on the throwaway branch `phase1/port-probe` (= `510d36f9`, **no commits, reset to clean** after every probe). The upstream branches were not modified. |

## Goal and success criteria

The goal is an evidence-based person-day estimate for porting RT's ray-tracing backend into Classic-VK, for **TFE and TSE**. Conventional raster stays the mandatory baseline, and RT is optional at build time and at runtime (ADR-0005, ADR-0007).

The estimate passes if:

- every work package traces back to a measured line count, conflict count or source finding;
- every productivity figure is stated as an assumption;
- [SRC], [EXP] and [ASM] are kept apart.

## Procedure (exact, reproducible)

All commands run from `L:\claude-ws\SSTRE\repos\SSTRE-Engine` unless noted otherwise.

1. **Measure the delta [EXP].**
   - `git diff --numstat 77a955ba upstream/rt-main` and `git diff --numstat b408e88 upstream/rt-main` produce `rt_vs_fork_numstat.tsv` and `rt_vs_croteam_numstat.tsv`.
   - `group.awk` sorts the files into subsystems.
2. **Classify per file [EXP]** with `probe.py`. For each of the 113 changed code files (`*.cpp/h/inl/es`) under `Sources/`, it:
   - counts the hunks of the fork-point→RT diff, and the hunks that contain RT markers (`GAT_RT|SSRT|SE1_RAYTRACING|srt_|RTGL|rg*()|Raytracing|…`);
   - checks whether the file exists at `SamTFE/Sources/<f>` and `SamTSE/Sources/<f>` in Classic-VK;
   - measures how far Classic-VK is from the fork-point version and from the RT version (`git diff --no-index --numstat -w`);
   - runs a per-file 3-way merge (`git merge-file --diff3`, with base = fork point, ours = Classic-VK, theirs = RT) and counts the conflict regions.
3. **Apply the patches [EXP].** In the worktree (checked out with `-c core.autocrlf=false`, so line endings are LF as in git), with the path prefix rewritten `Sources/` → `SamTFE/Sources/` (and `SamTSE/Sources/`):
   - **(a) Full code patch.** All 105 code files that exist in Classic-VK or are new: `git -c core.autocrlf=false apply --3way --whitespace=nowarn rt_code_<T>.patch`.
   - **(b) RT-only patch** (`filter_patch.py`):
     - whole files for the RT core and the pure hook files;
     - only the RT-marked hunks for mixed files (GfxLibrary, Texture, Adapter, DrawPort, Network, SeriousSam.cpp, HUD, Player, PlayerWeapons);
     - x64/asm-port, Vulkan-raster and UX-only files dropped.

     The result is 144 hunks, +11,710/−129 lines, sha256 prefix `bd69a3b02564bb92`. Conflict regions are counted with `grep -c '^<<<<<<<'`. The worktree is then `reset --hard` and cleaned.
   - **(c) Cross-tree entity patch.** The TFE `Entities` hunks for Player, PlayerWeapons, Eyeman and HUD, rewritten onto `SamTSE/Sources/EntitiesMP`, applied with `git apply --reject`.
4. **Check API compatibility [EXP].** Every identifier used by the new RT files that is defined elsewhere in RT's engine (1,976 identifiers, of which 295 are SE1-style `xx_Name` members) was looked up in Classic-VK `SamTFE/Sources/Engine`. The method is `comm` over sorted token lists.
5. **Check content usage [EXP].** `scan_worlds.py` scans every `.wld` (loose files and inside `.gro`) of the Steam Classic TSE and TFE installs for entity-class strings. It prints aggregate counts only.
   - Sanity check: `WorldBase.ecl` was found in 80 of 80 TSE worlds.
   - `count_levels.py` counts the numbered campaign-style worlds. The method reproduces the 15 TFE worlds in RT's `CustomInfo::EWorld`.

## Results

### R1. Size of the RT delta [EXP]

The RT delta from fork point `77a955ba` to `0e7f223c` covers 166 files, +20,708/−3,346 lines (of which `Sources/` is 143 files, +20,051/−1,240). The table groups it by subsystem.

| Group | Files | +/− | Nature ([SRC]: commit subjects, hunk markers) |
|---|---|---|---|
| `Engine/Raytracing/` (new) | 23 | +10,119/−0 | SSRT layer. `CustomInfo.cpp` alone is 1,997 lines |
| `Gfx_RayTracing.cpp`, `Gfx_wrapper_Raytracing.cpp` (new) | 2 | +390/−0 | `gfx*` function-pointer backend for `GAT_RT` |
| Graphics, other (GfxLibrary, DrawPort, Texture, Adapter, Color, Graphics.cpp…) | 22 | +1,393/−459 | Mixed: RT hooks and x64/asm conversions |
| `Graphics/Vulkan/` | 8 | +237/−25 | Raster fixes, already in Classic-VK (R3) |
| `Rendering/` | 3 | +160/−2 | `RenderView` hand-off to SSRT (`Render.cpp:960`) |
| Models, Light, BSP | 7 | +1,004/−131 | `LayerMixer.cpp` +690 is the x64 asm→C conversion. `RenderModel*.cpp` holds hooks. `RTModelNormalsFix.cpp` is dead code (`return;` at line 74) |
| Engine, other (Base, Math, Sound, Network) | 23 | +365/−166 | Mostly x64 (`e4b9664`, `2be6c82`, `0b5cece`…). Network.cpp also has RT scene-reset hooks |
| TFE `Entities` | 5 | +189/−135 | Flashlight, weapon-render guard, HUD and FOV tweaks |
| `GameMP` | 3 | +38/−86 | TFE branding and colours (UX, not RT) |
| `SeriousSam` (exe, menus) | 12 | +777/−122 | RT video options, DLSS/FSR menus, borderless window |
| Editors | 5 | +46/−4 | API-select dialogs |
| `Scripts/menu/RenderingOptions.cfg` | 1 | +250/−84 | Menu script |
| Build (`*.vcxproj/.sln/.filters/.user`) | 30 | +5,333/−110 | MSVC v143 x64, RTGL1 include, lib and DLL copy |
| Non-source (docs, PNG, `OverridenTextures/*.ktx2`, controls) | 22 | +407/−2,022 | Includes the KTX2 blue-noise file and the water normal map |

- Of the 113 changed code files (+14,718/−1,130), hunks carrying RT markers account for **+11,993/−108**. The remaining ≈2.7k lines are mostly the x64 port and UX changes.
- RT compared with Croteam `b408e88` adds, on top of the above, the Vk-era Vulkan backend (35 files, +5,175) and the TFE `Entities` import (136 files, +64,061). Classic-VK already has both.

### R2. Lineage and similarity: Classic-VK's Vulkan code is derived from the RT tree [EXP]/[SRC]

- **Vulkan directory.** Classic-VK `SamTFE/Sources/Engine/Graphics/Vulkan/` is **closer to RT** than to the fork point:
  - vs RT: 18 files, +224/−34 (`-w`, CR ignored);
  - vs fork point `77a955ba`: 19 files, +460/−58.

  RT-era files such as `SvkMatrix.cpp`, `SvkQueries.cpp` and `SvkTextures.cpp` differ from RT by only 2 lines each, against 29–146 lines from the fork point (`probe_files.tsv`).
- **`GfxLibrary.h`.** The 3-way merge (R4) leaves exactly the RT lines that Classic-VK **commented out**: `//GAT_RT = 2` at `GfxLibrary.h:77`, and the `HasAPI(GAT_RT)` line at `:312`. These are the only `GAT_RT`/`SSRT`/`Raytracing` traces in Classic-VK `SamTFE/Sources`.
- **Conclusion.** Classic-VK took RT's Vulkan raster code and removed the RT bits. The RT layer's host interfaces are therefore largely intact.

### R3. API compatibility of the RT layer with the Classic-VK engine [EXP]

- **Identifiers.** Of the 1,976 identifiers that the new RT files (`Raytracing/*`, the two `Gfx_*Raytracing` files and `RTModelNormalsFix.cpp`) share with RT's engine, every one exists in Classic-VK `SamTFE/Sources/Engine` except:
  - identifiers that RT's own hook hunks introduce (`gl_SSRT`, `ssrt_*`, `SSRT::C*Info`, `RT_Particle_*`, `*_RayTracing`);
  - **one real divergence:** the 64-bit current-world pointer. RT uses `CShell::GetUINT64("pwoCurrentWorld64_0/1")` (`Raytracing/Utils.cpp:24`). Classic-VK has `CShell::GetCurrentWorld()` (`Base/Shell.h:77`).
- **Includes.** All 69 `#include`s resolve, apart from the new RT headers and `RTGL1/RTGL1.h`.
- **Texture fields.** `Texture.h:69-70` (`td_ulObject` and `td_pulObjects`) is identical in both trees.
- **Platform-specific code.** Only `SSRT.cpp:321-325` (`HWND`, `GetModuleHandle`, Win32 surface) [SRC].
- **C++17.** `std::size` at `RTLights.cpp:559,561` is C++17, and Classic-VK builds with `CMAKE_CXX_STANDARD 14` (`SamTFE/Sources/CMakeLists.txt:5`) [SRC].
- **Game exe.** `SeriousSam/GUI/Menus/MenuActions.cpp:19` includes `RTGL1/RTGL1.h`, so the game exe depends on the RTGL1 header [SRC].

### R4. Patch-apply measurements onto Classic-VK [EXP]

| Probe | Tree | Files A / M clean / conflicted | Conflict regions | Lines inside conflicts |
|---|---|---|---|---|
| (a) full code patch (105 files, 388 hunks) | SamTFE | 26 / 17 / **50** | **202** | not counted |
| (a) | SamTSE | 26 / 17 / 50 | 203 | not counted |
| (b) RT-only patch (49 files, 144 hunks) | SamTFE | 26 / 15 / **8** | **41** | **571** |
| (b) | SamTSE | 26 / 15 / 8 | 41 | (identical) |
| plain `git apply --check`, full patch | TFE / TSE | 64 / 63 files fail without 3-way | — | — |
| (c) TFE entity hunks → TSE `EntitiesMP` | SamTSE | Eyeman and PlayerWeapons clean; Player 2 of 5 hunks rejected, HUD 4 of 6 rejected | 6 of 15 hunks rejected | — |

Conflicts in probe (b), TFE, as regions/lines:

| File | Regions | Lines |
|---|---|---|
| `DrawPort.cpp` | 16 | 212 |
| `SeriousSam.cpp` | 6 | 97 |
| `Texture.cpp` | 5 | 88 |
| `GfxLibrary.cpp` | 5 | 109 |
| `Gfx_wrapper.cpp` | 3 | 40 |
| `GfxLibrary.h` | 3 | 16 |
| `Modeler/DlgPreferences.cpp` | 2 | 7 |
| `RenderModel_View.cpp` | 1 | 2 |

- **Nature of the conflicts.** The `DrawPort.cpp` regions inspected are mostly mechanical. Classic-VK replaced the per-API `ASSERT(eAPI==…)` blocks with `ASSERT(GfxValidApi(eAPI))`, and RT adds `if (eAPI==GAT_RT) return;` next to them.
- **Clean hook files.** These apply cleanly in both trees:
  - `Render.cpp` and `Render_internal.h`
  - `RenderModel.cpp` and `Model.cpp`
  - `ShadowMap.cpp` and `DrawPort_Particles.cpp`
  - `Adapter.cpp` (RT hunks only) and `Network.cpp` (RT hunks only)
  - `Benchmark.cpp` and the EngineGui dialogs
  - TFE `Player.es`, `PlayerWeapons.es` and `Eyeman.es`
- **The x64 port must not be carried over.**
  - Most of the 202 regions in probe (a) come from RT's x64/asm hunks, for example `LayerMixer.cpp` (26), `SoundMixer.cpp` (12), `BSP.cpp` (10) and `Color.*` (10).
  - Classic-VK already has its own portable paths (`USE_PORTABLE_C`/`PLATFORM_64BIT` style guards, with 4–15 hits per file in LayerMixer, Color.h, Functions.h, SoundMixer and Graphics.cpp) [SRC].
  - So a selective port (probe b) is the right method. Taking whole files (probe a) would cost about 5× more conflict work.

### R5. TFE and TSE trees in Classic-VK [EXP]

- **Engine files touched by probe (b).** These are identical between `SamTFE` and `SamTSE` (`-w`), except `Adapter.cpp`, which differs by 10 lines.
- **Whole engine tree.** Apart from the vendored VMA, the two engine trees differ in 12 files and 138 changed lines.
- **Game exe.** `SeriousSam/Menu.cpp` (6,517 lines) and `SeriousSam/SeriousSam.cpp` are identical between the two trees.
- **Effect on effort.** TSE engine and UI work is mostly a replay of the TFE work.

### R6. UI layout gap [SRC]

- RT's menus live in `SeriousSam/GUI/Menus/*` (the post-2016 Croteam split). Classic-VK uses the older monolithic `SeriousSam/Menu.cpp`, `MenuGadgets.cpp` and `MenuPrinting.cpp`, so 8 RT menu files have **no counterpart**.
- RT-marked lines in those 8 files: 469 (MenuActions 352, MVideoOptions 57, MOptions 28, MenuStuff 21, MMain 6, MSinglePlayer 5).
- `SE1_RAYTRACING` is a **compile-time** switch in the game exe only (`SeriousSam.cpp` and the menus; defined in `SeriousSamTFE.vcxproj:193,300`). It removes some raster options under `#ifndef SE1_RAYTRACING`. For "raster mandatory, RT optional" those removals must become runtime checks.
- Classic-VK already has a runtime API switch, `APIToSwitch`/`sam_iGfxAPI` at `Menu.cpp:2070-2176`. It recreates the SDL window per API, which is the slot to extend.

### R7. TSE content needs [EXP]

| Measure | TSE (Steam Classic) | TFE |
|---|---|---|
| `.wld` total | 80 | 59 |
| Numbered campaign-style worlds | **13** | 15 (= RT `CustomInfo::EWorld` entries) |
| Worlds referencing `Terrain.ecl` | **0** | 0 |
| Worlds referencing `ModelHolder3.ecl` or `GruntSka.ecl` (SKA) | **0** | 0 |
| Worlds referencing `EnvironmentParticlesHolder.ecl` (rain/snow) | 7 | 0 |

- **SKA and terrain.** The shipped TSE worlds do not instantiate the terrain or SKA entity classes (string scan). The RT layer's missing SKA/terrain support (RD-005 §3.3) is therefore **not a blocker for the TSE campaign**, only for mods and user levels.
- **Caveat [ASM].** This is a string scan, not a runtime check. An entity could reach SKA through other classes. A runtime screenshot diff (RD-005 S1.4) would confirm it.
- **Rain and snow.** These are drawn through the generic `Particle_*` DrawPort API that RT hooks (`DrawPort_Particles.cpp`, 10 RT hunks) [SRC]. Whether they look right under RT is untested [ASM].

### R8. KTX and RTGL1 dependency surface [SRC]

- **KTX.** In RTGL1 `b1eb3d8`, KTX is used through `ImageLoader.cpp` (184 lines, 26 KTX references). It is also referenced in `ImageLoader.h`, `TextureOverrides.cpp:261-262` (forces `.ktx2`) and a TODO in `CubemapManager.cpp`. The vendored libktx is `Source/KTX/` (73 files).
  - `ImageLoader` also loads the blue-noise file (`BlueNoise.cpp:58-60`). That file ships in RT as `OverridenTextures/BlueNoise_LDR_RGBA_128.ktx2`.
  - So removing libktx means changing one RTGL1 loader class and converting two runtime files. It is a dependency for the owner's direction, not part of this port.
- **Linux build.** RTGL1 `v1.1.0` already contains the Linux compile fixes (`cf5d95e` is an ancestor of `b1eb3d8`). It offers `RG_WITH_SURFACE_XLIB/XCB/WAYLAND`. Its instance takes native surface infos only (`RgInstanceCreateInfo`: "exactly one of these surface create infos"), so on Linux the engine has to pass X11 or Wayland handles taken from SDL.
- **Linking.** RT links `RayTracedGL1.lib` directly (RD-001). A binary built with RT therefore will not start without the DLL, unless RTGL1 is loaded at runtime instead.
- **Runtime API calls.** RT uses 22 distinct `rg*` entry points, so a loader table would be small.

## Deviations, modifications and failures

- **No build.** No compile was attempted, as the brief requires. Compile errors on MSVC v143 or GCC are therefore **not measured**, only bounded by R3.
- **Line endings.** The first worktree checkout used `core.autocrlf=true` (CRLF on disk). It was re-checked-out with `-c core.autocrlf=false` so that git's LF patches compare like with like. No config file was changed.
- **Marker heuristic.** The RT-marker classification is a heuristic and misses some RT-support hunks, for example `Render_internal.h` and the de-static changes in `RenderModel_View.cpp`. Those files were therefore included whole in probe (b). The per-file call is in `filter_patch.py`.
- **Untested omission.** Dropping RT's x64 hunks assumes the RT layer does not rely on them. R3 found only the world-pointer case [ASM].
- A first `count_levels.py` heredoc had a quoting error and was rewritten. No effect on results.

## Interpretation and estimate

### Classification per hunk group

| Group | Classification | Evidence |
|---|---|---|
| `Engine/Raytracing/*` and the 2 `Gfx_*Raytracing` files (10,509 lines) | **Applies cleanly, then minor adaptation** | R4: added without conflict. R3: API-identical except the world pointer, the Win32 surface and `std::size` |
| Render, model, particle and shadow-map hooks | **Applies cleanly** | R4 |
| GfxLibrary, Gfx_wrapper, Texture, DrawPort hooks | **Needs adaptation** (mechanical) | R4: 29 regions, 449 lines |
| x64/asm hunks (≈40 files) | **Not ported.** Classic-VK has its own solution | R4(a), R1 |
| Vulkan raster fixes | **Already in Classic-VK** | R2 |
| TFE entity hooks | Applies cleanly (TFE). TSE: 9 of 15 hunks apply cross-tree, 6 need manual work | R4(c) |
| Menus and RT video options | **Must be rewritten** into `Menu.cpp`, with the compile-time `#ifndef SE1_RAYTRACING` turned into runtime checks | R6 |
| `SeriousSam.cpp` | Needs adaptation | R4: 6 regions |
| Build (CMake + vcxproj, 2 trees) | **Must be rewritten**. Classic-VK's `USE_SYSTEM_VULKAN`→`SE1_VULKAN` option is the pattern | `CMakeLists.txt:14,83-135,1218-1243` |
| `CustomInfo` tables | Applies, but the content is TFE-only. **TSE tables missing** | R7, `CustomInfo.h:31-48` |
| SKA and terrain in RT | **Missing** in RT. Not needed for the TSE campaign | R7, RD-005 §3.3 |
| UX-only changes (GameMP branding, borderless window, HUD defaults) | Optional, not ported by default | R1 commit subjects |

### Productivity assumptions [ASM]

These are planning assumptions for one engineer who knows SE1 and Vulkan. They are not measured, and §7 says how to calibrate them.

| ID | Assumption |
|---|---|
| P1 | Mechanical conflict region: 10–30 min (patterns like ASSERT→`GfxValidApi`) |
| P2 | Transplanting code that already exists and is API-compatible (review, compile fixes, wiring): 1,500–4,000 lines/day |
| P3 | New engine code (design, write, debug): 60–150 lines/day |
| P4 | Re-implementing UI code into a different structure: 100–250 lines/day |
| P5 | Per-level RT tuning (lights, materials, ignored polygons, as in TFE `CustomInfo`), including playtesting: 0.5–2 days per level |

### Estimate table (person-days)

| WP | Work package | Evidence | Low | Likely | High | Key assumptions and risks |
|---|---|---|---|---|---|---|
| WP0 | Pin, vendor and build RTGL1 `v1.1.0` (Windows) | RD-001/RD-005 inferred pair; no pin in RT HEAD | 1 | 2 | 4 | Depends on the build agent's S4 result. High if `b1eb3d8` does not match RT's API (fallback `7a88e38`) |
| WP1 | Build integration: CMake option (off by default) and vcxproj, both trees; RTGL1 find, link and shaders | R1 build group (+5,333 RT vcxproj lines, not reusable); Classic-VK option pattern | 2 | 4 | 7 | Classic-VK vcxproj is v140 and needs retargeting (RD-001) |
| WP2 | Engine transplant, TFE tree: 26 new files; 15 clean; 41 regions/571 lines; ≈5 point adaptations | R3, R4(b) | 5 | 8 | 13 | 41 × P1 = 0.9–2.6 d. 10,649 lines at P2 = 2.7–7.1 d. Adaptations 1–3 d |
| WP3 | Game exe and UI, TFE: RT video, DLSS and FSR options into `Menu.cpp`; `RenderingOptions.cfg` merge; entity hooks | R6 (469 lines at P4 = 1.9–4.7 d); cfg (Classic-VK differs from the fork point by 313 diff lines); entity hooks clean | 3 | 5 | 7 | The RTGL1 header must leave the exe (`MenuActions.cpp:19`) |
| WP4 | Replay onto the TSE tree | R5 (identical files), R4(c) (6 rejected hunks) | 1 | 2 | 4 | Cheaper still if the trees are unified first (separate decision) |
| WP5 | Runtime and build-time optionality: guard the 44 `gl_SSRT`/`SSRT::` sites; load RTGL1 at runtime (22 entry points); RT capability probe with fallback to VK/GL; SDL window flags per API | R3, R8; RT already falls back to VK (`aead590a`) | 3 | 5 | 9 | About 300–600 new lines at P3. A non-RT GPU starting an RT build is unverified (RT #19) |
| WP6 | Linux RT path: RTGL1 on GCC; SDL→Xlib/XCB/Wayland surface; GCC fixes in about 10.6k MSVC-only lines; packaging; native-Linux RT test | R8; RT never built on Linux | 4 | 7 | 14 | Largest unknown. WSLg is not representative. Needs a native Linux box with an RT GPU |
| WP7 | TSE RT content: `CustomInfo` for 13 campaign worlds; TSE texture class lists (water, fire, glass, alpha, emission…; TFE has 71 `.tex` entries over 1,229 TFE textures) | R7 at P5 (6.5–26 d), plus texture lists 2–5 d | 8 | 15 | 30 | Subjective quality bar. The owner should set "acceptable" per level |
| WP10 | Regression and validation: raster unchanged in both games (hooks are `GAT_RT`-guarded [SRC]); RT smoke test per game; Windows and Linux | R4 hook list | 3 | 5 | 8 | Test matrix of 2 games × 2 OS × 3 APIs |
| **Total, core** | **TFE + TSE, Windows + Linux, raster mandatory, RT optional** | | **30** | **53** | **96** | |

Milestone subtotals (low/likely/high):

| Milestone | Work packages | Low | Likely | High |
|---|---|---|---|---|
| M1: TFE RT on Classic-VK, Windows | WP0, WP1, WP2, WP3, WP5, plus part of WP10 | 16 | 27 | 45 |
| M2: TSE | WP4, WP7, plus part of WP10 | 10 | 19 | 37 |
| M3: Linux RT | WP6 | 4 | 7 | 14 |

**Conditional packages, not in the total:**

| WP | Package | Low | Likely | High | Notes |
|---|---|---|---|---|---|
| C1 | Data-driven `CustomInfo` (manifest instead of hard-coded `EWorld`/`.tex` tables) | 3 | 5 | 8 | Recommended before WP7. Could shrink WP7's high end |
| C2 | Replace libktx in RTGL1 with a GPLv2-compatible loader (e.g. DDS BC7/BC5); convert the blue-noise and water files; matching AssetCompiler output | 2 | 4 | 7 | Owner direction (ADR-0007). Contained to `ImageLoader` (R8) |
| C3 | SKA models in RT (exporter analogous to `RTModels.cpp`, 1,210 lines; SKA skinning in `Ska/RMRender.cpp`, 2,619 lines) | 6 | 10 | 16 | Not needed for the shipped TSE campaign (R7). Mods only |
| C4 | Terrain in RT (`Terrain/TerrainRender.cpp`, 1,412 lines) | 4 | 7 | 12 | Same as C3 |
| C5 | Upgrading to RTGL1 `hl1` API | — | — | — | Not estimated. A rewrite of the ≈8.9k-line layer (RD-005 §3.1) |

**Confidence [ASM].**

- **Low to medium overall.** The totals are about −45% to +80% around "likely".
- **The mechanical part is well measured.** WP2 and WP4 rest on conflict counts and API checks.
- **WP6 and WP7 dominate the uncertainty.**
  - WP6 depends on unmeasured GCC behaviour and Linux RT hardware.
  - WP7 is artistic tuning without an agreed quality bar.
- **Compared with RD-001's hypothesis.** RD-001 expected "the same order as the original RT layer", which took 291 commits over about 17 months. The measurements point much lower, because the layer transplants almost unchanged (R3, R4).

## Impact on ADRs, dossiers and backlog

- **ADR-0005.** The "Classic-VK-first, RT optional" direction is supported. The port is a transplant (most of the core applies cleanly), not a redesign. Classic-VK's own Vulkan code came from the RT tree (R2). The RT-first alternative's main argument ("port disproportionately costly") is weakened by these measurements, but not yet confirmed by a build.
- **ADR-0007.** RT can be made optional at build time (a CMake option, following the Vulkan pattern) and at runtime (load RTGL1 at runtime plus API fallback). This needs WP5, and RT as shipped does not do it.
- **RD-005.** SKA and terrain gaps move from "high risk for TSE" to "mods only" for the shipped TSE campaign (R7, a string-scan [EXP]).
- **Backlog.**
  - POC-24 can be closed with this estimate.
  - Suggested new items: a TFE-tree port spike (WP2 only, time-boxed to 8 days, to calibrate P1 and P2); C1 data-driven `CustomInfo`; a decision on unifying the TFE/TSE engine trees before WP4.

## Open questions (for owner and lead)

1. What quality bar should TSE RT meet (WP7)? Per-level tuning parity with TFE, or "works, untuned"? The answer swings the total by up to about 25 days.
2. Should the TFE and TSE engine trees be unified before the port? The touched files are already identical (R5).
3. RTGL1: stay on `v1.1.0` and accept forking it for C2 (KTX) and Linux packaging, or plan C5 later?
4. Linux RT validation needs native Linux hardware with an RT-capable GPU. Is there any?
5. Should RT's UX changes (GameMP branding, borderless window, HUD defaults) be ported? Default proposed: no.
6. Calibration: run a time-boxed WP2 spike on the throwaway `phase1/port-probe` branch once the build agent confirms that Classic-VK and RTGL1 build. Then re-derive P1 and P2.
