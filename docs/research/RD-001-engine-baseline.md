# RD-001: Engine baseline: comparison of Serious Engine 1 forks

| Field | Value |
|---|---|
| Dossier | RD-001 |
| Author | Agent A (engine auditor), Phase 0 |
| Date | 2026-11-27 |
| Status | **Draft research, not a decision.** Feeds proposed ADR-005 (engine foundation). |
| Method | Read-only inspection of local clones under `<workspace>/upstream/` using git, grep and Read, plus `gh api` metadata. **Nothing was built or executed.** No upstream scripts, hooks or binaries were run. |
| Related | [RD-005 rendering](./RD-005-rendering.md), [RD-006 platforms](./RD-006-platforms.md), [RD-007 licensing](./RD-007-licensing.md) (deep license audit is Agent E's job), [RD-002 HD assets](./RD-002-hd-assets.md) |

---

## 1. Question and scope

1. Which existing open-source Serious Engine 1 (SE1) codebase should SSTRE-Engine start from? Criteria: buildability, how far it has diverged from upstream, TFE and TSE support, how tightly the renderer is coupled to the rest of the engine, platform reach, and how well it suits later asset injection.
2. Is "Classic-VK first, with RT as an optional backend" a viable alternative to "RT first"?
3. How can upstream history be imported into `SSTRE-Engine` without destroying anything?
4. What exact steps and pass/fail criteria should a Phase 1 build attempt use?

**In scope.** These five repos:

- sultim-t/Serious-Engine-RT ("RT")
- tx00100xt/SeriousSamClassic-VK ("Classic-VK")
- tx00100xt/SeriousSamClassic ("Classic")
- Croteam-official/Serious-Engine ("Croteam")
- sultim-t/Serious-Engine-Vk ("Vk")

sultim-t/RayTracedGL1 ("RTGL1") is covered only where RT binds to it.

**Out of scope.** Builds, runtime tests, the deep license audit (owned by Agent E), and the HD asset format work (owned by Agent B).

---

## 2. Evidence (exact revisions inspected)

| Repo | Local dir | HEAD inspected | Default branch | Other branches |
|---|---|---|---|---|
| [Croteam-official/Serious-Engine](https://github.com/Croteam-official/Serious-Engine) | `upstream/Croteam-official_Serious-Engine` | `b408e88a16fd01aa1cfd0e0a999c86c2c1437c9e` (2017-01-21) | master | none |
| [sultim-t/Serious-Engine-Vk](https://github.com/sultim-t/Serious-Engine-Vk) | `upstream/sultim-t_Serious-Engine-Vk` | `52c0f9c19f6502c91c8569b2f476de2ec02019fd` (2020-10-02) | master | `0.1.2`, `Shaders`, `VMAIntegration` |
| [sultim-t/Serious-Engine-RT](https://github.com/sultim-t/Serious-Engine-RT) | `upstream/sultim-t_Serious-Engine-RT` | `0e7f223c19a28014b60d900878c28831db522120` (2022-04-20; this is also tag `v1.5`) | main | `dev` (`c0527b4`, 2022-10-08, 11 commits ahead), `VMAIntegration` |
| [tx00100xt/SeriousSamClassic-VK](https://github.com/tx00100xt/SeriousSamClassic-VK) | `upstream/tx00100xt_SeriousSamClassic-VK` | `510d36f901cbe883c56b155b53717e4efdeb6522` (2026-01-14) | main | none |
| [tx00100xt/SeriousSamClassic](https://github.com/tx00100xt/SeriousSamClassic) | `upstream/tx00100xt_SeriousSamClassic` | `80b9893e5b74e5a2160eaf63e6d6b3f3981dfbbd` (2026-01-13) | main | none |
| [sultim-t/RayTracedGL1](https://github.com/sultim-t/RayTracedGL1) | `upstream/sultim-t_RayTracedGL1` | `2457acc25df5766e48289205471cc2a07499f7f6` | hl1 | `doom`, `quake`; tags `v1.1.0` (`b1eb3d8`, 2022-04-20) through `v3.0.0-dev` |

GitHub metadata was queried with `gh api repos/<owner>/<repo>` on 2026-11-27:

| Repo | `fork` flag / parent | Last push | Open issues+PRs | GitHub license | Archived |
|---|---|---|---|---|---|
| Croteam | no | 2020-10-31 | 22 | GPL-2.0 | no |
| Vk | no | 2020-10-02 | 2 | GPL-2.0 | no |
| RT | no (not a GitHub fork) | 2022-10-08 | 26 | GPL-2.0 | no |
| Classic-VK | no | 2026-01-14 | 14 | GPL-2.0 | no |
| Classic | no | 2026-01-13 | 16 | GPL-2.0 | no |
| RTGL1 | no | 2023-12-02 | 24 | MIT | no |
| icculus/Serious-Engine (reference) | fork of Croteam | 2023-07-24 | n/a | GPL-2.0 | n/a |
| ptitSeb/Serious-Engine (reference) | fork of icculus | 2025-09-28 | n/a | GPL-2.0 | n/a |

Latest releases:

- **RT:** `v1.5`, 2022-04-20. Assets are `TFE_RT_Bin.zip` only. The textures zip was last shipped with `v1.1`.
- **Classic-VK and Classic:** `1.10.7`, 2025-02-02. Windows, Linux (many architectures), FreeBSD, macOS and AppImage builds.
- **Vk:** `0.1.4`, 2020-06-15. Win32 only.

**CI.** The latest Classic-VK run, [#20977541773](https://github.com/tx00100xt/SeriousSamClassic-VK/actions/runs/20977541773) on `510d36f`, passed all 12 jobs. These include Windows Release Win32 and x64 (`windows-2019`, MSBuild), Ubuntu x64, Alpine, FreeBSD, macOS-14, RPi armv7l/aarch64, mipsel, loongarch64 and AppImage. RT and Vk have no CI.

---

## 3. Observed facts

### 3.1 Fork lineage and divergence

```text
Croteam-official/Serious-Engine (SE 1.10 source drop 2016-03-11 "Uploading full engine sources" 9d8b787; last b408e88 2017-01-21)
 ├── sultim-t/Serious-Engine-Vk  (real git descendant: contains b408e88)
 │     └── fork point 77a955ba (2020-09-23 "Update README.md")
 │           ├── Vk master: +1 commit (52c0f9c "fixed TFE solution")
 │           └── sultim-t/Serious-Engine-RT: +291 commits after 77a955ba (all by S. Tsyrendashiev)
 │                 └── binds RayTracedGL1 (MIT, separate repo/DLL)
 └── icculus/Serious-Engine (GitHub fork) → ptitSeb/Serious-Engine (GitHub fork; Linux/SDL2/CMake port)
       └── tx00100xt/SeriousSamClassic  (NO shared git history: fresh "initial commit" 67d2e93 2022-05-10,
             │                             squashed "Upload sources" c4f9322; old log preserved as text in CHANGELOG.old)
             └── tx00100xt/SeriousSamClassic-VK  (shares 13 commits with Classic; split after d6d609aa 2022-05-15;
                                                  Vulkan renderer ported from the sultim-t lineage per README)
```

Evidence for each link:

- **RT and Vk are true git descendants of Croteam.** `git merge-base --is-ancestor b408e88 HEAD` succeeds in both clones, and both share root commit `d6f53cc` (2016-03-11 "Initial commit"). RT and Vk share 164 commits. Their newest common commit is `77a955ba4c257355228731070f4c196e9e042f26`. Vk HEAD `52c0f9c` is not in RT, but RT's first commit after the fork point, `3bf0612` "fixed TFE solution", has the same message.
- **RT's x64 port.** The RT README says "x64 port is based on https://github.com/rcgordon/Serious-Engine". RT added the x64 platform itself on 2020-11-25 (`5110c26`, `e4b9664`, `2be6c82`). The repo `rcgordon/Serious-Engine` could not be resolved via `gh api` (marked inaccessible).
- **The tx00100xt repos have no git ancestry from Croteam.** Their roots are `67d2e93` / `c4f9322`. `CHANGELOG.old` is byte-identical in both repos and contains 880 lines of `git log` text. It starts at ptitSeb merge `8f1a273` (2021-09-11) and goes back to 2016-03-11. The top authors are ptitSeb (127), Ryan C. Gordon/icculus (98), zcaliptium (41) and Daniel Gibson (37). So the Linux-port provenance is documented only as text, not as git objects.
- **Classic-VK's Vulkan code comes from the sultim-t lineage.** The README says "Vulkan Serious Engine port based on … sultim-t/Serious-Engine-Vk". Hypothesis, supported by evidence: the code was taken from the RT tree rather than from Vk master.
  - `SamTFE/Sources/Engine/Graphics/GfxLibrary.h` contains `//GAT_RT = 2, // Vulkan ray tracing`, commented out.
  - `GAT_RT` was first introduced in RT commit `21429ed` (2021-01-04, "added RTGL to gfx api list") and is absent from Vk.
  - The Classic-VK `Graphics/Vulkan/` directory differs from RT's by 47 deleted lines and from Vk's by 72. Both diffs exclude the vendored VMA headers that Classic-VK added.

Divergence statistics (`git diff --shortstat`; line counts include vendored and generated files unless filtered):

| Comparison | Files | Insertions | Deletions | Notes |
|---|---|---|---|---|
| RT HEAD vs Croteam `b408e88`, `Sources/` | 321 | 96,670 | 1,084 | Includes about 40% new TFE `Sources/Entities/` (game code imported, not engine changes) |
| ↳ `Sources/Engine/Raytracing/` (new) | 23 | 10,119 | 0 | SSRT layer: RTGL1 calls, scene and brush/model/light/particle export, per-level tweaks |
| ↳ `Sources/Engine/Graphics/Vulkan/` (new) | 35 | 5,175 | 0 | Vulkan raster backend from Vk |
| ↳ rest of `Sources/Engine` (code `*.cpp/*.h/*.es` only) | 62 | 6,041 | 703 | Hooks in Render.cpp, RenderModel.cpp, Texture.cpp, DrawPort_Particles.cpp, GfxLibrary, etc. |
| ↳ `Sources/GameMP` + `Sources/SeriousSam` | 26 | 2,426 | 229 | Menus/options for RT |
| RT HEAD vs Vk fork point `77a955ba`, Engine code excluding Raytracing | 64 | 3,544 | 778 | RT-specific changes to core engine |
| Vk vs Croteam, Engine code excluding Vulkan dir | 23 | 2,842 | 58 | Vk is a small change to the core engine |
| Classic-VK `SamTSE/Sources/Engine` vs Croteam `Sources/Engine` (no-index, ignore CR) | 395 | 69,475 | 8,988 | Includes SDL/Unix ports, 2 copies of VMA (~38k lines), 64-bit fixes |
| Classic `SamTSE/Sources/Engine` vs Croteam | 352 | 20,883 | 8,919 | Non-VK Linux port baseline |
| Classic vs Classic-VK, `SamTSE/Sources/Engine` | 64 | 48,712 | 189 | Mostly Vulkan backend plus VMA |
| Classic-VK `SamTFE/Sources/Engine` vs `SamTSE/Sources/Engine` | 13 | 9,187 | 8,862 | Two near-duplicate engine trees. The main difference is the VMA header version, plus small TFE/TSE differences |
| RT `main..dev` | 23 | 2,171 | 405 | Unreleased port to a newer RTGL1 interface. The last commit message reads "update to latest rtgl1 (looks really bad)" |

### 3.2 Build systems, toolchains, platforms, dependencies

| | Croteam | Vk | RT | Classic-VK | Classic |
|---|---|---|---|---|---|
| Build system | MSVC `.sln` (`Sources/All.sln`) | MSVC `.sln` (`All.sln`, `AllTFE.sln`) | MSVC `.sln` (`Sources/All.sln`, `Sources/AllTFE.sln`). RTGL1 is built separately with CMake | CMake (top-level `CMakeLists.txt`, min 3.7) for Unix-likes; MSVC `.sln` (`SamTFE/Sources/SamTFE.sln`, `SamTSE/Sources/SamTSE.sln`) for Windows | Same as Classic-VK |
| Toolset in vcxproj | `v120` (VS2013) | `v120`/`v140` | `v143` (VS2022), Windows SDK 10.0 | `v140` (VS2015). README: "VS 2015 or higher", Vulkan SDK ≥ 1.3.204.1 | `v140` |
| Architectures | Win32 only (0 x64 entries in sln) | Win32 only | x64 required ("64-bit CPU" in README). Win32 configs still exist but point to stale `SolutionDir\RTGL1` paths | x86, x64, arm (armhf/aarch64), ppc64le, riscv64, s390x, mipsel, loongarch64, e2k (release assets) | Same |
| OS | Windows | Windows | **Windows only** (README: "Other OS: Not supported") | Linux, FreeBSD, OpenBSD, NetBSD (OpenGL only), macOS, Windows | Same, plus D3D8/9 Windows variants |
| Graphics APIs | OpenGL; D3D8 behind `SE1_D3D` (off by default) | OpenGL + Vulkan (`SE1_VULKAN`). D3D and VK are mutually exclusive (both use API index 1) | OpenGL, Vulkan raster (`GAT_VK=1`), Vulkan RT via RTGL1 (`GAT_RT=2`). Selection at runtime | OpenGL + Vulkan. OpenGL fallback if Vulkan is missing (`sam_iGfxAPI`). `-DUSE_SYSTEM_VULKAN=FALSE` builds GL-only | OpenGL (+ D3D8/D3D9 on Windows builds) |
| External deps | DirectX8 SDK (optional) | Vulkan SDK | Vulkan SDK (`VULKAN_SDK`), RTGL1 built from source (`RTGL1_SDK_PATH` env var after `591abf7` removed the submodule), Python 3 + `glslc` for shaders, optional NVIDIA DLSS DLL | SDL2 ≥ 2.0.6, zlib, libogg/libvorbis, Vulkan loader/headers ≥ 1.2, flex, bison, nasm (x86 asm), optional xxhash. Windows: bundled `External/SDL2`, libogg, libvorbis | Same minus Vulkan |
| Bundled third-party dirs | `Sources/Engine/zlib`, `Sources/LWSkaExporter/SDK` (NewTek), `Sources/libogg`, `Sources/libvorbis` | same | same, plus RTGL1 (external) | same, plus `amp11lib` (GPL-2), `External/SDL2`, vendored VMA (`vk_mem_alloc.h`, two versions) | same minus VMA |
| Checked-in executables | `Tools.Win32/Bison.exe`, `Flex.exe` | same | same | same, in both `SamTFE/` and `SamTSE/` | same |
| CI | none | none | none | GitHub Actions, 12 jobs, green at HEAD | GitHub Actions, green at HEAD |

RTGL1 binding in RT:

- `Sources/Engine/Engine.vcxproj` includes `$(RTGL1_SDK_PATH)\Include` and links `RayTracedGL1.lib`. A post-build step copies `RayTracedGL1.dll` from `$(RTGL1_SDK_PATH)\Build\x64-Release` (lines ~224–385).
- The last submodule pin, before `591abf7` (2022-04-19), was RTGL1 `7a88e3867db11f669cbb68a5828342865a4e4a86` (2022-02-12), with `branch = Draft`.
- RT `v1.5` (= HEAD `0e7f223`, 2022-04-20) has no pin. Its release notes link "RayTracedGL1-DLSS.zip" from the RTGL1 release `v1.1.0`, and RTGL1 tag `v1.1.0` = `b1eb3d8` is dated 2022-04-20. **Hypothesis:** RT `main` matches RTGL1 `v1.1.0`. A Phase 1 build is needed to confirm.
- At RTGL1 `v1.1.0` (`CMakeLists.txt`):
  - CMake ≥ 3.15, C++17, `find_package(Vulkan)`.
  - Vendored KTX-Software subset (`Source/KTX`).
  - Options `RG_WITH_SURFACE_WIN32/XLIB/XCB/WAYLAND/METAL` and `RG_WITH_NVIDIA_DLSS` (OFF).
  - Shaders are compiled by `Source/Shaders/GenerateShaders.py` using `glslc --target-env=vulkan1.2`.
- RTGL1 itself gained Linux compilation in `cf5d95e` (2022-04-17). That does not make RT Linux-capable: RT uses Win32 surfaces (`RG_USE_SURFACE_WIN32`), MFC tools and the Windows-only Croteam platform layer.

### 3.3 TFE vs TSE support

| | Croteam | Vk | RT | Classic-VK / Classic |
|---|---|---|---|---|
| Game libs present | TSE only: `EntitiesMP`, `GameMP` | `Entities` (TFE, added in `4d17950`, 2020-09-23, "ability to run TFE") + `EntitiesMP` | Same as Vk | Separate full trees: `SamTFE/Sources` (`Entities`, `GameMP` built as TFE) and `SamTSE/Sources` (`EntitiesMP`, `GameMP`) |
| TFE switch | n/a | `SS_THE_FIRST_ENCOUNTER` in `SeriousSamTFE.vcxproj`; TFE solution `AllTFE.sln` | `SS_THE_FIRST_ENCOUNTER` (e.g., `Sources/SeriousSam/SeriousSam.cpp:126`, `Sources/GameMP/CompModels.cpp:21`) | CMake: `-DFIRST_ENCOUNTER=1` when `INTERNAL_NAME=serioussam`, entity dir suffix `MP` for TSE (`SamTFE/Sources/CMakeLists.txt:124–138`). vcxproj: `SE1_VULKAN;FIRST_ENCOUNTER;SS_THE_FIRST_ENCOUNTER` |
| RT on TFE | n/a | n/a | Yes. `SE1_RAYTRACING` is defined only in `SeriousSamTFE.vcxproj` (2 hits). | n/a |
| RT on TSE | n/a | n/a | **No.** `SeriousSam.vcxproj` (TSE) has 0 `SE1_RAYTRACING` defines. `EntitiesMP` was changed in only 2 files (+24/−21). TFE `Entities` were changed for RT in 6 files (+1,310/−139: HUD, WeaponPositions, Player, PlayerWeapons). `Engine/Raytracing/CustomInfo.cpp` hardcodes TFE levels (`EWorld::Hatshepsut`, `SandCanyon`, `Karnak`, …, lines 51–62, ~1,997 lines) and about 70 TFE texture paths. Issue [#22](https://github.com/sultim-t/Serious-Engine-RT/issues/22) quotes the v1.4 notes: "no plans for TSE for the near future". | n/a |
| Mods | Classic `ModEXT.txt`, `Mods/` via `_fnmMod` | same | same | `Mods/` dir per game, mod launch from menu, XPLUS mod build (`-DXPLUS=TRUE`; CI swaps `PlayerWeaponsHD.es`) |
| Open TSE issues | — | — | #22 | Classic-VK [#53](https://github.com/tx00100xt/SeriousSamClassic-VK/issues/53) "Second Encounter won't launch" (GOG, Windows, 0 comments); Classic #29 "SSTSE is just black screen" |

### 3.4 Renderer coupling

The **shared abstraction** in every fork is the SE1 graphics layer:

- `CGfxLibrary` (`Engine/Graphics/GfxLibrary.{h,cpp}`) holds the API enum `GfxAPIType`.
- `Gfx_wrapper.h` declares 46 `gfx*` function pointers. `GFX_SetFunctionPointers()` in `Gfx_wrapper.cpp:853` assigns them for each API.
- Each backend lives in `Gfx_<API>.cpp`, `Gfx_<API>_Textures.cpp` and `Gfx_wrapper_<API>.cpp`.
- The original Croteam renderer is an immediate-mode, polygon-batch design. World rendering (`Engine/Rendering/Render*.cpp`, `RenderModel.cpp`, `DrawPort_*`) pushes vertices and textures through the wrapper.

**Vk / Classic-VK** add a Vulkan backend as one more `gfx*` implementation (`Graphics/Vulkan/Svk*.cpp`). Core-engine edits are small (Vk: +2,842/−58 lines outside the Vulkan dir). The renderer is still a raster API swap and the rendering model is unchanged.

**RT** is more invasive and works at scene level rather than API level:

- `Engine/Rendering/Render.cpp:960` checks `if (_pGfx->gl_eCurrentAPI == GAT_RT)`, builds an `SSRT::CWorldRenderingInfo` and hands the whole world to SSRT. This bypasses the polygon-batch world renderer.
- `RenderModel.cpp` (5 hooks), `DrawPort_Particles.cpp` (5), `Texture.cpp` (4) and `ShadowMap.cpp` redirect geometry, particles and textures to `Engine/Raytracing/*`.
- `GAT_RT` appears 101 times across `Sources/`. `RTGL1/RTGL1.h` is included only in `Engine/Raytracing/` and `SeriousSam/GUI/Menus/MenuActions.cpp`.
- The RT entity and game changes (flashlight, HUD, weapon positions, menus) are TFE-specific.
- **Raster path retained?** Yes in code: `GAT_OGL` and `GAT_VK` remain in the enum, and `Gfx_OpenGL.cpp` and `Gfx_Vulkan.cpp` still compile into `Engine.vcxproj`, with API selection at runtime. Two things are unverified: whether raster still renders correctly in the RT build, and whether a non-RT GPU can even start the RT build.
  - Commit `4425dc8` (2020-10-18) says "removed some code from old rendering system -- restore it after the development".
  - Issue [#19](https://github.com/sultim-t/Serious-Engine-RT/issues/19) "Support for non-RTX fallback" is open.
- **Coupling verdict.** The RT layer is reasonably well contained in `Engine/Raytracing/` (about 10k lines) plus about 100 runtime branch points. In content, though, it is tightly coupled to TFE: level tables, texture lists and entity tweaks.

### 3.5 Licensing (high level only; Agent E owns the deep audit)

- All five engine repos ship a GPL v2 `LICENSE`; GitHub reports `GPL-2.0`.
- Croteam file headers read "under the terms of version 2 of the GNU General Public License" with no "or later" clause. This points to GPL-2.0-only, which Agent E should confirm.
- Sultim's new files (e.g., `Engine/Raytracing/SSRT.cpp`) carry "Copyright (c) 2020-2021 Sultim Tsyrendashiev" and the same version-2 wording.
- RT's TFE `Sources/Entities/*.es` (imported in `4d17950`) **have no license header**; they start directly with the ECC class ID. The Classic tree's TFE entities carry the Croteam GPL header. Where RT's TFE entities came from is not recorded in the commit message (flag for Agent E).
- RTGL1 is **MIT**. It is linked as a DLL. Combining MIT code with GPL-2.0 is generally regarded as compatible, but that is for Agent E to confirm.
- Optional NVIDIA DLSS (`nvngx_dlss.dll`) is proprietary and is not shipped in RT. Users download it separately (v1.5 release notes).
- Third-party directories that are not GPL-2, per the READMEs: zlib, LightWave SDK (NewTek), libogg/libvorbis (Xiph). Classic-VK adds `amp11lib` (GPL-2, `amp11lib/COPYING`), vendored SDL2 (zlib license, presumably) and VMA (MIT, presumably). These are unverified, so Agent E needs to check them.
- Engine resource archive `SE1_10.gro` (83 MB) ships in Croteam, Vk and RT; Classic-VK ships `SE1_10b.gro` (2.7 MB). Their content license is for Agent E.

### 3.6 Content and asset loading (relevant for later injection)

- **`.tex` format** (`Engine/Graphics/Texture.cpp`, Croteam lines 677–800). The file starts with the magic `TVER` and supports version 3 and 4. It contains the chunks `TDAT` (flags, mex width/height, fine-mip count, first mip, frame count), `FRMS` (raw RGB or RGBA frames; v4 stores only the top mip), `ANIM` (texture animations) and others.
- **Effect textures.** `CreateEffectTexture` covers procedural fire and water. These are runtime-generated and **cannot be replaced by static images**.
- **Size limits.** Two different limits apply:
  - **Import into `.tex`.** `Types.h:162` sets `MAX_MEX_LOG2 = 10`, so `MAX_MEX = 1024`. `CTextureData::Create_t` (Texture.cpp:295) throws "At least one of texture dimensions is too large" when a source picture exceeds 1024 px on either axis. This is the in-engine creation path used by the editor and tools. It is unchanged in RT and Classic-VK.
  - **Upload to the raster path.** The user cvar `tex_iNormalSize` (default 9, clamped to 5–11, "log2 of texture area /2 for max texture size allowed") reduces textures at upload. The ceiling is equivalent to 2048×2048. `gl_pixMaxTextureDimension = 8192` is also set (GfxLibrary.cpp:944 Croteam; 1005 RT; 1081 Classic-VK).
  - **Hypothesis:** the v4 on-disk layout (mipmap offset computed with `GetMipmapOffset(15,…)`) can hold larger images if written by an external tool. Whether the engine renders them correctly past these limits is **unknown**. This is a Phase 1/2 experiment.
- **File resolution precedence.** `ExpandFilePath_read` in `Engine/Base/Stream.cpp:1469` resolves files in this order:
  1. mod directory, loose file
  2. mod GRO/zip
  3. base directory, loose file
  4. any GRO/zip
  5. CD path

  This order applies with `fil_bPreferZips=0`; with the cvar set, zips win over loose files. So **loose files placed in a mod directory override archived originals**, which gives a non-invasive injection route for SE1-format (`.tex`) replacements on every fork. GRO-to-GRO override order is not analyzed here (Agent B).
- **RT texture override mechanism** (already implemented):
  - `Engine/Raytracing/TextureUploader.cpp:33` defines `OVERRIDEN_TEXTURE_FILE_EXTENSION ".ktx2"`. Each static material passes `pRelativePath = <tex dir>/<tex name>.ktx2` to `rgCreateStaticMaterial`.
  - `SSRT.cpp:316–355` sets the override root to `<app>/OverridenTextures/Compressed/`. It also sets the postfixes: albedo/alpha `""`, roughness-metallic-emission `"_rme"`, normal `"_n"`.
  - RTGL1 loads the KTX2 files (`Source/TextureOverrides.cpp`, vendored libktx). `RTGL1/Tools/CreateKTX2.py` converts PNG to KTX2 with **compressonatorcli**: BC7 for colour, BC5 for `*_n`.
  - Overrides can be disabled for individual textures (`RTTextures.cpp:66 IsOverrideDisabled`, `RG_MATERIAL_CREATE_DISABLE_OVERRIDE_BIT`).
  - The release asset `TFE_RT_Textures.zip` (v1.1) contained "upscaled textures and PBR textures".
  - Consequence: in RT, high-resolution PBR replacements bypass `.tex` and its 1024/2048 limits. **This works only in the RT path**, not in OpenGL or Vulkan raster.
- **Classic-VK.** No texture override mechanism was found: there are no `.ktx`/`.dds` references in `Engine/Graphics`. HD content (e.g., the XPLUS mod) is delivered as standard SE1 assets inside a mod directory.

---

## 4. Comparison table

| Criterion | RT | Classic-VK | Classic | Vk | Croteam |
|---|---|---|---|---|---|
| Last code activity | 2022-04 (main), 2022-10 (dev) | **2026-01** | 2026-01 | 2020-10 | 2017-01 |
| Maintained | Dormant | **Active**, regular releases | Active | Dormant | Frozen reference |
| Git history back to Croteam | **Yes** (true descendant) | No (squashed 2022, text changelog only) | No | Yes | Root |
| Build system | MSVC v143 `.sln` + CMake for RTGL1 | **CMake** (Unix) + MSVC v140 `.sln` (Win) | CMake + MSVC | MSVC v120/v140 | MSVC v120 |
| CI | none | **12-job matrix, green** | green | none | none |
| 64-bit | x64 only | x86 + x64 + ARM + others | same | Win32 only | Win32 only |
| Windows / Linux | Windows only | **Both** (+BSD, macOS) | Both | Windows | Windows |
| TFE | Yes (RT path) | Yes | Yes | Yes | No (TSE only) |
| TSE | Raster build exists; **RT path not enabled for TSE** | **Yes** (separate tree; one open launch issue on GOG/Windows) | Yes | Yes | Yes |
| Raster path | Code retained (OGL, VK); runtime health unverified | **Vulkan + OpenGL fallback** | OpenGL, D3D8/9 | Vulkan + OpenGL | OpenGL (+D3D8 opt.) |
| Ray/path tracing | **Yes** (RTGL1, DLSS/FSR options) | No | No | No | No |
| HD/PBR texture override | **Yes** (KTX2 BC7/BC5, `_n`, `_rme`) | No (only mod-dir SE1 assets) | No | No | No |
| Core-engine invasiveness | High (scene-level hook, ~100 branch points, ~10k new lines, TFE-specific data) | Moderate (platform port + VK backend; duplicated engine trees) | Moderate | Low | n/a |
| Known runtime issues | AMD/Intel artifacts, Wine black screen, input lag (#5, #19, #24, #25, #30, #36) | Vulkan input lag (#43), missing lens flares/effects (#15, #59) | DX9 issues (#31) | lens flare (#4) | n/a |

---

## 5. Assumptions and unknowns

- **Unknown:** whether RT `main` builds against RTGL1 `v1.1.0` (`b1eb3d8`) without changes. The alternative is the last pinned `7a88e38` or another commit near 2022-04-20.
- **Unknown:** whether RT's OpenGL/Vulkan raster modes still render TFE correctly, and whether TSE (`All.sln`) still compiles and runs in the RT tree.
- **Unknown:** whether the Classic-VK Windows `.sln` builds with toolset v143 when retargeted. The host has v142/v143 installed but no v140. CI runs on `windows-2019`.
- **Unknown:** where RT's TFE entity sources came from and what license they carry (no headers).
- **Unknown:** the effective maximum texture size per backend, both for `.tex` files written by external tools and for RT KTX2 overrides (limited by VRAM and RTGL1).
- **Unknown:** the exact Steam TFE/TSE file set Classic-VK and RT expect, compared with the user's installs (Agent B inventories the editions).
- **Assumption:** Classic-VK's Vulkan backend can host an RT backend because it shares code with RT's Vulkan directory. Not yet demonstrated.
- **Host (observed 2026-11-27, not a build):**
  - Visual Studio 2019 Build Tools / Community 16.11 and VS 2022 Community 17.5.33424.131 are installed. MSVC 14.35.32215 with ATL/MFC. Toolsets v142 and v143 are present; v140 is not.
  - `VULKAN_SDK` is not set. `glslc` and CMake are not on PATH (VS2022 bundles CMake).
  - GPU: NVIDIA GeForce RTX 4070, driver 32.0.16.1664.

---

## 6. Alternatives and tradeoffs

### A. RT-first: fork sultim-t/Serious-Engine-RT

- **Pros:**
  - The only codebase with working path tracing and PBR texture overrides. These are the project's headline features.
  - Full git history back to Croteam.
  - Modern MSVC toolset (v143).
  - The KTX2 override layout maps directly onto the planned AssetCompiler output.
- **Cons:**
  - Dormant since 2022, with no CI.
  - Windows-only and x64-only.
  - The unpinned RTGL1 dependency must be reconstructed. The upstream `dev` branch moved to a newer RTGL1 interface with visible regressions.
  - The RT path is TFE-only: hardcoded level and texture tables, TFE-only entity hooks, and no TSE define.
  - Non-RT GPU support is unclear (#19).
  - Inherits Croteam's Windows-only platform layer, which conflicts with the Linux, console and portability requirements.

### B. Classic-VK-first, with RT as an optional backend (explicit evaluation)

- **Pros:**
  - Actively maintained (2026), with a green 12-job CI matrix.
  - CMake on Unix plus MSVC on Windows, and Linux, BSD, macOS and ARM already working. This is the strongest base for "maintain a viable non-RT path for portability" and for later console research.
  - TFE and TSE both supported, as separate trees.
  - Vulkan raster with OpenGL fallback.
  - Its Vulkan backend shares code with RT's `Graphics/Vulkan/` (the commented-out `GAT_RT` slot is still in `GfxLibrary.h`), so the API-enum and wrapper plumbing for a third backend already exists conceptually.
- **Cons:**
  - No ray tracing and no texture override mechanism. Porting RT means moving about 10k lines of `Engine/Raytracing/` plus about 100 hook points across a tree that has diverged from RT by a 2016-to-2026 Linux port.
  - The RTGL1 interface must be chosen: v1.1.0 to match the RT sources, or a newer version that needs rework.
  - The work has to be done **twice** (in `SamTFE/Sources` and in `SamTSE/Sources`) unless the duplicated engine trees are unified first.
  - No git ancestry from Croteam, so provenance lives only in `CHANGELOG.old`.
  - Windows `.sln` uses v140 and may need retargeting.
  - Open Vulkan visual and latency issues (#15, #43, #59).
- **Feasibility verdict.** Technically plausible and better aligned with the settled requirements: both campaigns, Windows/Linux, a raster fallback, and future platforms. RT becomes a substantial port that must be gated by a time-boxed spike. Expect the effort to be of the same order as the original RT layer, mitigated by being able to copy rather than re-design. This is a hypothesis without measured effort.

### C. Croteam official or Vk as the base

- Clean history and minimal divergence. But no Linux, Win32-only, inactive, and Croteam has no TFE game code. Useful only as **reference and diff baselines**, not as a foundation.

### D. Classic (non-VK) as the base

- Same advantages as Classic-VK, but without Vulkan. Inferior to B unless a Vulkan-free build is needed. Classic-VK can already build GL-only with `-DUSE_SYSTEM_VULKAN=FALSE`.

### E. Dual-track: Classic-VK as main line, RT kept as a reference/spike branch

- Import both histories into SSTRE-Engine (see §9). Phase 1 builds both unmodified. RT stays a read-mostly branch used to (a) prove the RT visuals and KTX2 override pipeline on TFE and (b) harvest code for the backend port into the Classic-VK line.
- Cost: more upstream tracking. Benefit: RT features become available for early asset-pipeline validation without committing the whole project to a Windows-only, TFE-only base.

---

## 7. Risks

| Risk | Likelihood | Impact | Notes / mitigation |
|---|---|---|---|
| RT cannot be rebuilt reproducibly (RTGL1 revision mismatch, missing shader toolchain) | Medium | High for A/E | Try RTGL1 `v1.1.0`, then `7a88e38`. Record the exact SDK version |
| RT raster path is broken, so there is no fallback inside RT | Medium | High for A | Phase 1 test: `sam_iGfxAPI`/menu switch to OpenGL and Vulkan |
| Porting RT to Classic-VK costs far more than estimated (diverged hooks, duplicated trees) | Medium-High | High for B | Time-boxed spike. Unify the engine trees first, or port to the TFE tree only |
| TSE RT content gap (lighting, per-level tables) | High | Medium | Make CustomInfo data-driven (manifest) instead of hardcoded |
| Upstream maintainers inactive (RT) or single-maintainer (Classic-VK) | High / Medium | Medium | Keep our own CI. Upstream fixes only through normal PRs, with owner approval |
| Checked-in `Bison.exe` / `Flex.exe` are untrusted binaries used by the Windows build | Medium | Medium (supply chain) | Replace with a trusted winflexbison download verified by hash, or audit the hash before Phase 1 |
| GitHub `windows-2019` runner deprecation breaks the Classic-VK Windows CI | Unknown | Low-Medium | Our CI should use `windows-2022` with v143 |
| Wrong legal assumption about RT TFE entities without headers, `SE1_10.gro`, LightWave SDK | Unknown | High | Deferred to Agent E / [RD-007](./RD-007-licensing.md) |
| Large blob `SE1_10.gro` (86.6 MB) in RT history | Certain | Low | Under GitHub's 100 MB hard limit. A push will warn (>50 MB) but succeed. Do not use LFS rewriting |

---

## 8. Proposed experiment (Phase 1 build attempt) with measurable success criteria

These steps are **not executed in Phase 0**. They run in a separate local workspace (`<workspace>/local-work/engine-build\`), never in the upstream clones. Game data is only referenced from the read-only Steam installs: copy the required files into a local, git-ignored runtime directory. Record every tool version, commit SHA and console log.

### 8.0 Prerequisites (record exact versions)

- Install the LunarG Vulkan SDK (pick one and record it, e.g., 1.3.2xx), which provides `glslc`.
- CMake ≥ 3.15 (the VS2022-bundled CMake is acceptable).
- Python 3.10 (present).
- VS2022 17.x with "Desktop development with C++" and MFC (present: 17.5, MSVC 14.35).
- compressonatorcli, only for the KTX2 override test.
- Replace or verify `Tools.Win32/Bison.exe` and `Flex.exe`: record their SHA-256, or use winflexbison from a trusted source.

### 8.1 Build Classic-VK (Windows, unmodified source at `510d36f`)

1. Make a fresh copy or clone at `510d36f901cbe883c56b155b53717e4efdeb6522`.
2. Run `msbuild /m /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=v143 SamTFE\Sources\SamTFE.sln`. Repeat for `SamTSE\Sources\SamTSE.sln`. The toolset override is needed because v140 is not installed. Record it as the only deviation.
3. Optional Linux leg (WSL2/VM, Ubuntu 22.04 to match CI):
   ```sh
   apt install build-essential libsdl2-dev cmake libvorbis-dev flex bison git libxxhash-dev libvulkan-dev
   cmake -B build -DCMAKE_BUILD_TYPE=Release
   cmake --build build -j
   ```
4. Runtime setup: copy `Help/`, `Levels/` and the `*.gro` files listed in the README from the user's Steam TFE/TSE installs into the output `SamTFE/`/`SamTSE/` runtime directory.

### 8.2 Build RT (Windows, unmodified source at `0e7f223`, = `v1.5`)

1. Clone RTGL1 at tag `v1.1.0` (`b1eb3d8`). Configure with:
   ```sh
   cmake -B Build/x64-Release -DCMAKE_BUILD_TYPE=Release -DRG_WITH_SURFACE_WIN32=ON
   ```
   Build `RayTracedGL1` with `RG_WITH_NVIDIA_DLSS=OFF`, then run `Source/Shaders/GenerateShaders.py` (uses `glslc`).
2. If step 1 fails to link or compile against RT, retry with `7a88e3867db11f669cbb68a5828342865a4e4a86` and record which one works.
3. Set `RTGL1_SDK_PATH` to the RTGL1 root. Run `msbuild /m /p:Configuration=Release /p:Platform=x64 Sources\AllTFE.sln`. Separately try `Sources\All.sln` (TSE) to see whether it builds at all.
4. Runtime setup: copy the TFE files listed in the v1.5 release notes. Leave `OverridenTextures/` empty at first, then test with one locally generated KTX2 file.

### 8.3 Success criteria (each is pass/fail and recorded in a Phase 1 report)

| ID | Criterion | Measure |
|---|---|---|
| S1 | Classic-VK TFE and TSE Release x64 build | msbuild exit code 0 for both solutions. Count of warnings recorded. Zero source modifications (toolset override only) |
| S2 | Classic-VK TFE launches and plays | Reaches the main menu and loads `01_Hatshepsut` in Vulkan and in OpenGL. 10 minutes of play without a crash. Startup log saved |
| S3 | Classic-VK TSE launches | Loads the first TSE level (`1_0_InTheLastEpisode` path from source). Records whether issue #53 reproduces on Steam data |
| S4 | RT TFE builds | RTGL1 plus `AllTFE.sln` exit 0. Exact RTGL1 SHA, Vulkan SDK and toolset recorded |
| S5 | RT TFE path-traced run | Loads `01_Hatshepsut` with the RT API on the RTX 4070. Frame time captured at 1080p and 1440p (method recorded). No crash in 10 minutes |
| S6 | RT raster fallback | Switching to OpenGL and to Vulkan raster in the RT build renders the same level. Screenshots kept locally only |
| S7 | RT TSE status | Result of `All.sln` build and launch recorded as pass, fail or not-attempted, with reasons |
| S8 | Override proof | One TFE texture replaced through an RT KTX2 override (`<tex path>.ktx2` under `OverridenTextures/Compressed/`). One replaced through a mod-directory loose `.tex` in Classic-VK. Both visible in game |
| S9 | Reproducibility note | Two clean rebuilds of Classic-VK produce the same file list. Whether the binaries hash-match is recorded, not required |

If S1 to S3 pass and S4 to S6 fail, the evidence favours option B (or E with RT used as a code reference only). If everything passes, option E is recommended for Phase 1 and later.

---

## 9. Fork-history import options for SSTRE-Engine

**Current state** (observed 2026-11-27):

- `Handelsonderneming-S-D-Broekhoven/SSTRE-Engine` is public, `fork=false` and `size=0`.
- It has a single unrelated commit `d17edbb` "Initial commit" (README only) on `main`.
- Locally there is branch `phase0/bootstrap`.

**Constraints:**

- The upstream candidates have **unrelated histories**: RT descends from Croteam, while Classic-VK starts from a 2022 squash.
- Nothing may be force-pushed, deleted or have repo settings changed without owner approval. Every option below except O4 is non-destructive to existing refs.

| Option | How (commands to be run by the lead/owner later, not now) | Pros | Cons |
|---|---|---|---|
| **O1. Import upstream refs as namespaced branches** (recommended first step) | `git remote add rt https://github.com/sultim-t/Serious-Engine-RT.git`, `git fetch rt`, `git push origin rt/main:refs/heads/upstream/rt-main`. Same for `upstream/classic-vk-main`, and optionally `upstream/croteam-master`, `upstream/rt-dev` and tags renamed into a prefix (e.g., `upstream-rt/v1.5`) | Fully history-preserving with original SHAs, so upstream diffs stay possible. Touches nothing existing. Several upstreams can coexist. Easy to update by fetch and fast-forward push | Branch list gets noisy. Upstream tags must be namespaced to avoid clashes. The 86.6 MB `SE1_10.gro` blob triggers a GitHub size warning (allowed, < 100 MB) |
| **O2. Choose an integration branch built on the chosen upstream, then switch the default branch** | `git switch -c sstre/main upstream/classic-vk-main` (or rt), add `docs/sstre/`, push. Then the owner changes the default branch to `sstre/main` in repo settings | History stays linear on top of upstream, so upstream merges are trivial. The existing `main` with `d17edbb` stays untouched | Changing the default branch is a repo-settings change and needs owner approval. Two "main-like" branches can confuse contributors until the old `main` is archived (renamed, not deleted) |
| **O3. Merge unrelated histories into existing `main`** | `git switch main`, `git merge --allow-unrelated-histories upstream/classic-vk-main`; resolve the README conflict by keeping upstream README and moving SSTRE text to `docs/sstre/` | No settings change. `d17edbb` is preserved. Upstream SHAs stay reachable | Adds a merge commit joining two roots. Later upstream merges still work. README conflict needs care. For a dual-upstream approach (E) only one upstream can sensibly be merged into `main` |
| **O4. Recreate as a GitHub fork** | Delete or rename SSTRE-Engine and fork RT or Classic-VK into the org | Native "forked from" link, easy PRs to upstream, GitHub network graph | **Destructive** (repo deletion or rename) and needs owner approval. A fork links to only **one** upstream, but we may need two unrelated ones. Forks of public repos must stay public. One org can hold only one fork per network. An existing repo cannot be converted to a fork without GitHub Support. Not recommended |
| **O5. Mirror push** | `git push --mirror` from an upstream clone | Exact copy of all refs | **Overwrites or deletes** existing refs, including `main`/`d17edbb`. Destructive. Not recommended |
| **O6. Optionally import Classic-VK's pre-squash provenance** | Fetch `ptitSeb/Serious-Engine` (and `icculus/Serious-Engine`) into `upstream/ptitseb-master`. Optionally link it with a `git replace --graft` locally (never pushed as a rewrite) | Restores browsable git provenance for the Linux-port lineage that Classic-VK squashed | Purely informational. Grafts are local-only. Adds more branches |

**Recommendation:** O1 for RT, Classic-VK and Croteam, plus O2 for the chosen integration line once ADR-005 is accepted. O3 is an acceptable alternative if the owner prefers not to change the default branch. Avoid O4 and O5. Record the imported upstream SHAs in `docs/sstre/UPSTREAM.md` in SSTRE-Engine (proposed, not created here).

---

## 10. Recommendation (for proposed ADR-005, not a decision)

**Proposed:** adopt **option E**. Make **tx00100xt/SeriousSamClassic-VK the primary engine foundation** (main integration line), and evaluate **ray tracing as an optional backend ported from sultim-t/Serious-Engine-RT**. Keep the RT tree imported unmodified as a reference and spike branch.

Rationale, based on evidence:

1. Classic-VK is the only candidate that already meets the settled requirements:
   - Both TFE and TSE (§3.3).
   - Windows and Linux with CMake.
   - A non-RT Vulkan/OpenGL path (§3.2).
   - Active maintenance and a green 12-job CI (§2).
2. RT's distinguishing value is concentrated in `Engine/Raytracing/` plus about 100 hook points and the KTX2 override contract (§3.4, §3.6). That makes it a module to port, not necessarily a base to adopt.
3. RT's weaknesses as a base go against the settled requirements: Windows-only, TFE-only RT data, dormant since 2022, unpinned RTGL1, uncertain raster fallback.
4. RT-first remains defensible if Phase 1 shows that the RT port into Classic-VK is disproportionately costly **and** that RT's raster fallback works. ADR-005 should stay "proposed" until S1–S8 are measured.

The asset pipeline should target a **renderer-neutral override contract**:

- SE1-native `.tex` replacements via the mod directory, for raster.
- KTX2 albedo, `_n` and `_rme` files in the RT layout, for RT.

That way AssetCompiler work is not blocked by the engine decision.

---

## 11. Decision dependencies

- ADR-005 (engine foundation) depends on Phase 1 results S1–S8 and on RD-005 (rendering/RT feasibility).
- ADR-006 (licensing boundaries) depends on Agent E's audit of: GPL-2.0-only headers, unheadered RT TFE entities, RTGL1 MIT, DLSS, `SE1_10.gro`, the LightWave SDK and amp11lib.
- ADR-007 (platform strategy) depends on whether the RT backend can be made optional at build time. Classic-VK already offers `-DUSE_SYSTEM_VULKAN=FALSE`; an equivalent RT switch is needed.
- The fork-history import (§9) needs owner approval for the default-branch change (O2) or the merge into `main` (O3).
- RD-002 (Agent B) must confirm which Steam edition files each engine expects and the GRO override order.

## 12. Next steps

1. Lead/owner: approve the §9 O1 import, pushing namespaced upstream branches to SSTRE-Engine. No destructive actions.
2. Phase 1: run §8 in `local-work/`, starting with the Classic-VK build (lowest risk), then RTGL1 v1.1.0 plus RT.
3. Spike (time-boxed, after S1–S6): list each RT hook point with file:line, map it to its Classic-VK equivalent in `SamTFE/Sources/Engine`, and estimate port effort from that list.
4. Investigate unifying Classic-VK's duplicated `SamTFE/Sources/Engine` and `SamTSE/Sources/Engine` trees (13 files differ) before any large engine change.
5. Agent E: confirm the license items in §3.5. Agent B: confirm the edition file sets and GRO precedence. Agent D: RTGL1 version choice (v1.1.0 vs current `hl1` branch) and non-RT GPU behaviour.
