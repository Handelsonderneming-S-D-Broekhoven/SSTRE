# RD-007 — Licensing, GPL compatibility, asset/model terms and branding

> **Changelog**
> - 2026-11-27 (Phase 1, compliance auditor): §16 turned into a register with a status column. Owner decisions of 2026-11-27 recorded (D1–D3, Q11). New questions Q15–Q23 added from [EXP-004](../experiments/EXP-004-upstream-publication-audit.md) (upstream publication audit) and [RD-006 §3.5](./RD-006-platforms.md#35-legal-split-per-platform-four-separate-questions) (platform legal split). Other sections are unchanged: their "proposal" wording reflects the Phase 0 state, and ADR-0006 governs where they differ.

| Field | Value |
|---|---|
| Dossier | RD-007 |
| Author | Agent E (licensing/compliance researcher), Phase 0 |
| Date | 2026-11-27 |
| Status | **Draft.** Evidence-based audit, **not legal advice and not a legal clearance.** Every conclusion below is either an observed fact with a source or an explicitly labelled hypothesis. Items that need a lawyer are collected in [§16](#16-unresolved-legal-questions-for-the-ownercounsel). |
| Related | [RD-001 engine baseline](./RD-001-engine-baseline.md), [RD-003 AI pipeline](./RD-003-ai-pipeline.md), [RD-005 rendering](./RD-005-rendering.md), [RD-008 testing/release](./RD-008-testing-release.md), [notices policy (proposed)](../policies/notices-policy.md), ADR-0006 (licensing boundaries, proposed) |

## 1. Question and scope

1. What licenses actually govern the candidate engine code bases and the RayTracedGL1 (RTGL1) renderer, file by file, including vendored third-party code, committed binaries and proprietary SDK hooks?
2. Can a GPL-2.0-only engine coexist with GPL-3.0 project tools, and under which architectural boundary? What happens if the engine links proprietary SDKs (DLSS) or Apache-2.0 code?
3. What license should each of the five SSTRE repositories carry, and is the GPL suitable for the data/manifests repository?
4. What do the game EULA, the Steam Subscriber Agreement, trademarks and AI-model licenses say about extraction, modification, derivatives and distribution?
5. How should notices, SPDX headers and attribution be maintained (see the [notices policy](../policies/notices-policy.md))?

Out of scope: the choice of engine (RD-001), models (RD-003), console SDK NDAs (RD-006). This dossier covers the compliance angle of those choices.

## 2. Evidence

### 2.1 Local upstream clones (read-only, `<workspace>/upstream/`)

| Clone | Upstream | Commit inspected |
|---|---|---|
| `Croteam-official_Serious-Engine` | https://github.com/Croteam-official/Serious-Engine | `b408e88a16fd01aa1cfd0e0a999c86c2c1437c9e` (master; first commit `d6f53cc` 2016-03-11) |
| `sultim-t_Serious-Engine-RT` | https://github.com/sultim-t/Serious-Engine-RT | `0e7f223c19a28014b60d900878c28831db522120` (main) |
| `sultim-t_Serious-Engine-Vk` | https://github.com/sultim-t/Serious-Engine-Vk | `52c0f9c19f6502c91c8569b2f476de2ec02019fd` (master) |
| `tx00100xt_SeriousSamClassic-VK` | https://github.com/tx00100xt/SeriousSamClassic-VK | `510d36f901cbe883c56b155b53717e4efdeb6522` (main) |
| `tx00100xt_SeriousSamClassic` | https://github.com/tx00100xt/SeriousSamClassic | `80b9893e5b74e5a2160eaf63e6d6b3f3981dfbbd` (main) |
| `sultim-t_RayTracedGL1` | https://github.com/sultim-t/RayTracedGL1 | `2457acc25df5766e48289205471cc2a07499f7f6` (default branch `hl1`; branches `doom`, `quake` also exist and were **not** audited) |

Header counting method: a Python script read the first 3,000 bytes of every tracked file with extensions `.cpp .c .h .hpp .inl .es .y .l .cc` (`git ls-files`) and classified the header by the first matching marker. It is a heuristic. Misclassification of individual files is possible, so treat counts as approximate. Exact `git grep` strings used: `"terms of version 2 of the GNU General Public License"`, `"any later version"`, `"SPDX-License-Identifier"`, `"Permission is hereby granted, free of charge"`, `"Microsoft Corporation|NewTek|Immersion|NVIDIA Corporation"`.

### 2.2 Web and primary sources (accessed 2026-11-27)

| Source | URL | Accessed? |
|---|---|---|
| GNU GPL FAQ (aggregate, plug-ins, system library exception, v2/v3 compatibility, compatibility matrix) | https://www.gnu.org/licenses/gpl-faq.html (anchors `#MereAggregation`, `#GPLPlugins`, `#NFUseGPLPlugins`, `#SystemLibraryException`, `#GPLIncompatibleLibs`, `#v2v3Compatibility`, `#AllCompatibility`, `#GPLOutput`) | Yes (partially rate-limited; quotes below are short excerpts) |
| Steam Subscriber Agreement (last updated 2026-09-10 per page) | https://store.steampowered.com/subscriber_agreement/ | Yes |
| Steam store pages TFE Classic (app 41050) and Fusion 2017 (app 564310) | https://store.steampowered.com/app/41050/ , https://store.steampowered.com/app/564310/ | Yes. **No game-specific EULA link was listed on either page.** |
| Devolver Digital EULA referenced by the in-game license | https://www.devolverdigital.com/eula | **Inaccessible** (HTTP 429 twice) |
| GamingOnLinux report on the 2016 GPL release | https://www.gamingonlinux.com/2016/03/croteam-releases-serious-engine-version-110-as-free-software/ | Yes. It is a secondary source. |
| NVIDIA RTX SDKs license (DLSS/NGX/NRD) | https://github.com/NVIDIA/DLSS/blob/main/LICENSE.txt (repo HEAD `9981c635…`, 2026-10-16), https://github.com/NVIDIAGameWorks/RayTracingDenoiser | Yes (via `gh api`) |
| AMD FidelityFX FSR2 license | https://github.com/GPUOpen-Effects/FidelityFX-FSR2/blob/master/LICENSE.txt | Yes |
| NVIDIA Streamline license | https://github.com/NVIDIA-RTX/Streamline | Yes (MIT header, but it references separate NSight Perf SDK terms) |
| Hugging Face model-card license metadata | `https://huggingface.co/api/models/<id>` | Yes (see §8) |
| USPTO marks (via Justia aggregator, secondary) | https://trademarks.justia.com/owners/croteam-ltd-1138924 , https://trademarks.justia.com/owners/devolver-digital-inc-5285337 | Search snippets only. **USPTO TSDR / EUIPO eSearch not checked.** |
| DreamyCecil SE1-ModSDK (TFE entity code provenance claim) | https://github.com/DreamyCecil/SE1-ModSDK | Search snippet only |

### 2.3 Local game installations (read-only; only license documents were read)

- `G:\SteamLibrary\steamapps\common\Serious Sam Classic The First Encounter\license.txt` and the TSE equivalent are byte-identical (SHA-256 recorded locally, 17,197 bytes). Licensor: **GHI Media, LLC** (Austin, Texas). The text refers to `www.devolverdigital.com/eula` as the current version.
- HD TFE and HD TSE: no EULA, license or readme file found at depth ≤ 3.
- Fusion 2017: only `Help\External_EULA\*` (third-party component notices: libpng, Lua, OpenSSL, zlib, Ogg Vorbis, Theora, Noto fonts, nvDXT, etc.). No Croteam/Devolver EULA file was found locally.

## 3. Observed facts — engine repositories

### 3.1 Top-level LICENSE and operative grant

- All five engine repositories carry a byte-identical `LICENSE` (MD5 `93fff0e526a2978a9b8383625f471b4c`, 339 lines). It is the unmodified **GNU GPL version 2, June 1991** text. The "either version 2 … or (at your option) any later version" wording at lines 298–299 is inside the license's own *How to Apply* appendix. It is a template, **not** a grant.
- **Operative grant: the per-file header**, e.g. `Sources/Engine/Engine.cpp` (Croteam official):

  > `Copyright (c) 2002-2012 Croteam Ltd. This program is free software; you can redistribute it and/or modify it under the terms of version 2 of the GNU General Public License as published by the Free Software Foundation`

  There is no "or any later version" clause. Under GPLv2 §9, a program that "specifies a version number of this License" binds that version. **Observed conclusion: Croteam's code is GPL-2.0-only.** It cannot be relicensed to GPLv3 without the permission of all copyright holders.
- Croteam `README.md` (§ License): *"Serious Engine is licensed under the GNU GPL v2 (see LICENSE file). Some of the code included with the engine sources is not licensed under the GNU GPL v2: zlib (`Sources/Engine/zlib`) …, LightWave SDK (`Sources/LWSkaExporter/SDK`) by NewTek Inc., libogg/libvorbis (`Sources/libogg`, `Sources/libvorbis`) by Xiph.Org Foundation."* The same README says 3D Exploration and IFeel support were *"disabled in the open source version … due to copyright issues"*.
- GitHub reports `GPL-2.0` for Croteam-official/Serious-Engine (`gh api …/license`).
- Release date: first commits 2016-03-11 (`d6f53cc` "Initial commit", `9d8b787` "Uploading full engine sources"). A secondary source (GamingOnLinux, 2016-03-11) states the engine was opened "under the GPLv2 license" and that *"the assets of the games that run on this engine are also still proprietary"*. **I found no Croteam primary statement on the asset question.** The repository itself contains no asset license.
- The Serious-Engine-RT README says: *"This project is licensed under the GNU GPL v2. x64 port is based on https://github.com/rcgordon/Serious-Engine (GNU GPL v2)"*, followed by the same non-GPL list. The Classic-VK README adds *"amp11lib is licensed under the GNU GPL v2 (see amp11lib/COPYING file)"*.

### 3.2 Header census (approximate; method in §2.1)

| Repo | Source files | GPL-2.0-only header (Croteam style) | of which non-Croteam holders | Other copyright notice | No header | Notes |
|---|---|---|---|---|---|---|
| Croteam official | 3,125 | 2,939 | 0 | 147 | 37 | "other" = libvorbis 69, LightWave SDK 53, Engine 21 (zlib + `DSOUND.H`), libogg 4 |
| Serious-Engine-RT | 3,311 | 2,986 | 45 Sultim Tsyrendashiev (2021) | 147 | **176** | **132 of the headerless files are in `Sources/Entities`** (TFE entity code, see §3.4) |
| Serious-Engine-Vk | 3,285 | 2,960 | 19 Sultim | 147 | 176 | same `Sources/Entities` pattern |
| SeriousSamClassic-VK (TFE+TSE trees) | 6,997 | 6,324 | Sultim 54, amp11lib (Beisert/Ladavac) 72, Dreamy Cecil 4, A. Pavlov 2, … | 481 | 26 | +148 zlib-style (SDL2 headers, zlib), 12 MIT (VMA, Khronos) |
| SeriousSamClassic | 6,941 | 6,275 | similar | 474 | 32 | — |
| RayTracedGL1 (`hl1`) | 261 | 0 | — | 3 | 15 | 204 MIT-style, 36 `SPDX: Apache-2.0` (KTX), 2 `SPDX: MIT`, 1 `SPDX: BSD-1-Clause` |

Fork-added code checked (RT `Sources/Engine/Raytracing/SSRTGlobals.h`, Classic-VK `Gfx_Vulkan.cpp`, `TEXConv.cpp`) reuses the Croteam header text verbatim, i.e. **GPL-2.0-only**.

"Or-later" text appears only in: bison skeletons (`Sources/bison.simple`, `Sources/Engine/Base/bison.simple`, `Sources/Engine/Ska/bison.simple`, `Sources/Ecc/bison.simple`) and bison-generated `Parser.cpp` files, which carry the FSF *"As a special exception, when this file is copied by Bison into a Bison output file, you may use that output file without restriction"* (Bison 1.24 exception), plus `Sources/Engine/GameAgent/MSLegacy.h` (Luigi Auriemma, *"either version 2 of the License, or (at your option) any later version"*). GPL-2.0-or-later code combines with GPL-2.0-only code under v2.

### 3.3 Vendored third-party code, binaries and blobs

| Item | Path (Croteam layout; forks equivalent) | License observed | GPL-2.0 compat. (FSF view) | Note |
|---|---|---|---|---|
| zlib 1.1.3 (1998) | `Sources/Engine/zlib/` | Zlib | Yes | very old version; security patching is a separate concern |
| libogg / libvorbis | `Sources/libogg`, `Sources/libvorbis` (`COPYING`) | BSD-3-Clause (Xiph) | Yes | attribution required in binary distributions |
| LightWave SDK headers (51 files) | `Sources/LWSkaExporter/SDK/` | "Copyright 1999, NewTek, Inc.", **no license text in repo** | **Unknown** | used only by the LightWave exporter plug-in. Exclude from SSTRE builds |
| DirectSound header | `Sources/Engine/Sound/DSOUND.H` | "Copyright (C) 1995-2000 Microsoft Corporation. All Rights Reserved." | **Unknown / proprietary** | Windows-only. Redistribution terms are not stated |
| amp11lib (Classic-VK/Classic only) | `SamT?E/Sources/amp11lib/` | file headers: GPL-2.0-only. **`COPYING` contains the GNU *Library* GPL v2 text** | Yes either way | discrepancy between header and COPYING. Record both |
| SDL2 headers (Classic-VK/Classic) | `SamT?E/Sources/External/SDL2/` (82 files) | Zlib | Yes | headers only. SDL runtime is obtained separately |
| Vulkan Memory Allocator | Classic-VK `Engine/Graphics/Vulkan/vk_mem_alloc.h`, RTGL1 `Source/Vma/` | MIT (AMD) | Yes | — |
| Bison.exe / Flex.exe + `bison.zip` / `flex.zip` | `Tools.Win32/` | GPL tools. The zips contain their sources and `COPYING` | Build tools, not linked | committed Windows **executables**. Do not run them (untrusted) and do not redistribute them |
| `SE1_10.gro` (86.6 MB, SHA-256 `f76c3cfb…0ae8`) / `SE1_10b.gro` | repo root | **No license stated.** It is a ZIP of 2,151 entries (Models 866, ModelsMP 443, Textures 240, Sounds 87, Classes, Fonts, Shaders …) | **Unclear** | Croteam resources shipped in a GPL repo "to freely use the engine". Whether the GPL covers these assets is unclear (see Q5) |
| TFE entity sources | RT/Vk `Sources/Entities/*.es` (120 `.es`, no headers). Classic-VK `SamTFE/Sources/Entities` (with Croteam GPL header) | **Provenance unverified** | ? | see §3.4 |
| Compiled SPIR-V shaders | Classic-VK `Engine/Graphics/Vulkan/Shaders/Compiled*` | generated from in-repo GLSL (GPL-2.0-only) | Yes if the source is shipped | — |

### 3.4 TFE entity code provenance (RT/Vk forks)

`Sources/Entities` (TFE gameplay entities, 120 `.es` files) was added to Serious-Engine-RT in commit `4d17950` (2020-09-23, "ability to run TFE", +68,792 lines) **with no license headers**. Croteam's official repo contains only `EntitiesMP` (TSE). A community repo (DreamyCecil/SE1-ModSDK, search snippet only) states that its TFE entity code comes from the **Croteam Serious Sam SDK released in 2001–2002**, and argues that it is GPL-2.0 because it uses Serious Engine 1.10 code. tx00100xt's copy (`c4f9322`, 2022-05-10) carries the Croteam GPL header. **Hypothesis:** the TFE entity code derives from the original proprietary 2001 SDK, which Croteam did not explicitly relicense in the 2016 release. This is the most important provenance question for a TFE-first plan (Q4).

### 3.5 RayTracedGL1

- `LICENSE`: **MIT**, "Copyright (c) 2020 Sultim Tsyrendashiev". MIT can be combined with GPL-2.0.
- Vendored code: `Source/KTX` (KTX-Software, **Apache-2.0**, 36 files. `texture.c`, `vkloader.c`, `dfdutils/*` are compiled into the library, `CMakeLists.txt` l.105–122). `KTX/lib/basisu/zstd` (BSD). `Source/Stb` (MIT/PD). `Source/Hashmap` (MIT, M. Ankerl). `Source/Vma` (MIT). `Source/Shaders/CAS`, `LPM` (AMD FidelityFX, MIT). `Tests/Libs/tinygltf` (MIT). KTX's `LICENSE.md` says `lib/etcdec.cxx` "is not open source". **That file is not present in RTGL1's copy** (checked with `git ls-files`). KTX also ships `LICENSES/LicenseRef-*` (Cesium trademark, ETCSLA, HI trademark, Kodak, PNGSuite).
- Submodules (`.gitmodules`): `Source/imgui` (ocornut/imgui, MIT, `375ae5d`), `Source/glfw` (Zlib, `dd8a678`), `Source/cgltf` (sultim-t fork, MIT, `f9567ab`), `Source/glaze` (MIT, `bdbc8cf`), `Tests/Libs/glfw`, `Tests/Libs/glm`. Licenses come from GitHub metadata. The submodule trees were not checked out.
- **Committed binary blobs:** `Source/FSR2/win32/ffx_fsr2_api_x64{,d}.lib` and `ffx_fsr2_api_vk_x64{,d}.lib` (prebuilt AMD FSR2 static libraries, linked when `RG_WITH_AMD_FSR2=ON`, **the default**). FSR2 is MIT (AMD), so redistribution is allowed with the notice. Corresponding source is public at GPUOpen-Effects/FidelityFX-FSR2 but is not in the repo, and the exact matching version is not recorded.
- **DLSS:** `option(RG_WITH_NVIDIA_DLSS … OFF)` (`CMakeLists.txt` l.133). When ON, the build reads `DLSS_SDK_PATH` and links `nvsdk_ngx_d.lib` / `libnvsdk_ngx.a` from https://github.com/NVIDIA/DLSS. No NGX binaries are committed.
- How the RT engine consumes RTGL1: `Sources/Engine/Engine.vcxproj` includes `$(RTGL1_SDK_PATH)\Include`, links the `RayTracedGL1.lib` import library and copies `RayTracedGL1.dll` into `Bin`. **This is dynamic linking with shared in-process data structures.** The submodule was removed in `591abf7` (2022-04-19). The last pinned RTGL1 commit was `7a88e3867db11f669cbb68a5828342865a4e4a86`.
- Upstream binary release `v1.5` (`TFE_RT_Bin.zip`, 2022-04-20, inspected as an archive listing only, then deleted): contains `LICENSE`, `Bin/Engine.dll`, `Entities.dll`, `Game.dll`, `RayTracedGL1.dll`, `SeriousSamTFE.exe` and Ogg/Vorbis DLLs. There is no NGX/DLSS DLL. A byte-string scan of `RayTracedGL1.dll` found no `NVSDK_NGX`/`nvngx` symbols (5 "DLSS" strings, likely UI or config text) and did find KTX strings. **Hypothesis:** that release did not link DLSS. It did contain Apache-2.0 KTX code inside a DLL loaded by a GPL-2.0-only executable. The README also points users to `TFE_RT_Textures.zip` ("additional upscaled textures and PBR textures"), an upstream precedent for distributing derivatives of game assets. **A precedent is not a permission** (Q6).

## 4. Observed facts — SSTRE repositories

Verified 2026-11-27 locally (`git ls-files`, working tree) and via `gh api repos/Handelsonderneming-S-D-Broekhoven/<repo>` → `.license` = `null` for all five:

| Repo | Tracked files | Untracked (Phase 0 work in progress) | LICENSE present? |
|---|---|---|---|
| SSTRE | `README.md` | `.gitattributes`, `.github/`, `.gitignore`, `CONTRIBUTING.md`, `SECURITY.md`, `docs/`, `schemas/`, `scripts/` | **No** |
| SSTRE-Engine | `README.md` | — | **No** (and no upstream history: not a fork) |
| SSTRE-AssetCompiler | none (no commits) | `.gitignore`, `CONTRIBUTING.md` | **No** |
| SSTRE-Manifests | `README.md` | `.gitignore`, `CONTRIBUTING.md` | **No** |
| Remaster-Toolkit | `README.md` | `.gitignore`, `CONTRIBUTING.md` | **No** |

Because no license has been granted yet, everything in these public repos is currently "all rights reserved" by default. Adding a license is an owner act (plan §9.5).

## 5. Compatibility analysis

### 5.1 GPL-2.0-only engine vs GPL-3.0 tools

- FSF GPL FAQ `#v2v3Compatibility`: "Is GPLv3 compatible with GPLv2?" → **"No."** The two licenses "are not compatible". `#AllCompatibility`: copying code under "GPLv2 only" into, or using a "GPLv2 only" library from, a GPLv3 work → **"NO"**.
- **Therefore:** no SSTRE GPL-3.0 code may be compiled or linked into the engine binary, and no engine (Croteam/fork) code may be copied into a GPL-3.0 repo. A vendor folder or submodule does not change this (plan §2).
- Corollary that affects AssetCompiler design: **format readers ported from engine source** (`.tex`, `.mdl`, `.wld`, `.gro` handling in `Sources/Engine/…`) are GPL-2.0-only. If AssetCompiler is GPL-3.0, its format code must be written independently from specifications or observation (clean-room style, documented), **or** those readers must live in a GPL-2.0-only helper executable (e.g. in SSTRE-Engine) that AssetCompiler calls as a separate process.
- The reverse direction is constrained as well. A GPL-2.0-only process may not link Apache-2.0 libraries (FSF considers Apache-2.0 incompatible with GPLv2). Much of the Python ML stack is Apache-2.0 (e.g. `transformers`, Qwen-VL code), and ComfyUI is GPL-3.0. **This makes GPL-3.0 the right license for the Python tool repos and keeps them out of process from the engine.**

### 5.2 The separate-process / file-format / CLI boundary

- GPLv2 §2 (in-repo `LICENSE` l.129–132): *"mere aggregation of another work not based on the Program with the Program … on a volume of a storage or distribution medium does not bring the other work under the scope of this License."*
- FSF FAQ `#MereAggregation`: an aggregate "consists of a number of separate programs, distributed together". Whether parts are separate programs depends on "the mechanism of communication … and the semantics of the communication". Pipes, sockets and command-line arguments are normally mechanisms used between separate programs. If the semantics are intimate enough (exchanging complex internal data structures), that "could be a basis to consider the two parts as combined into a larger program". The FSF notes that courts decide in the end.
- FSF FAQ `#GPLPlugins` / `#NFUseGPLPlugins`: fork-and-exec without intimate communication generally makes **separate programs**. Dynamic linking with shared data structures generally makes **one combined program**.
- **Proposed boundary (consistent with plan §2/§4):** the engine reads only *compiled asset files* in documented formats (DDS/KTX2/JSON metadata). AssetCompiler and Remaster-Toolkit run before the game, as separate processes. They communicate through files and documented CLIs and never load engine DLLs or share in-memory structures. Under the FSF view, the engine and the tools are then separate works that can be distributed side by side (aggregate) under their own licenses. The umbrella "builder" may *invoke* both and *package* them. It must not link them.
- Hypothesis needing review (Q2): the compiled-asset format is engine-specific, and the engine may impose structure on it. File formats as such are generally not treated as making programs derivative. That is still a legal judgment for counsel.
- The GPL does not cover a program's output (`#GPLOutput`: "copyright law does not give you any say in the use of the output"). Compiled textures are therefore not licensed by virtue of the tool's GPL. Their status is governed by the **input assets' rights** (§7).

### 5.3 Proprietary SDKs: DLSS/NGX, NRD, Streamline, FSR

- NVIDIA RTX SDKs License (DLSS, NGX, RTXGI, RTXDI, NRD; `NVIDIA/DLSS/LICENSE.txt` and NRD repo): grants object-code distribution "as incorporated … into a software application". Its §4 LIMITATIONS (e) states: *"You may not use the SDK in any manner that would cause it to become subject to an open source software license"*, giving as examples licenses that require the SDK to be disclosed in source form, licensed for derivative works, or redistributable at no charge. §2(c) further requires distribution "subject to the terms at least as protective as the terms of this license".
- GPLv2 §3 system library exception (in-repo `LICENSE` l.159–164): the source need not include *"anything that is normally distributed … with the major components (compiler, kernel, and so on) of the operating system on which the executable runs, unless that component itself accompanies the executable."* The NGX static library and `nvngx_dlss.dll` ship **with the application**, not with the OS or driver as a major component. **Hypothesis: the system library exception does not cover DLSS.** FSF FAQ `#GPLIncompatibleLibs`: linking a library outside the exception needs explicit permission from the copyright holders. For Croteam's code that is practically unobtainable.
- **Consequence (observed terms + hypothesis):** a distributed SSTRE engine build with `RG_WITH_NVIDIA_DLSS=ON` would combine GPL-2.0-only code with a proprietary SDK whose license forbids open-source subjection. **Treat this as a blocker. Do not distribute DLSS-enabled engine builds.** Local, private, non-distributed builds raise fewer GPL issues (the GPL constrains distribution) but remain subject to the NVIDIA license terms. That is counsel's call (Q3). NRD is under the same RTX SDK license, so the same conclusion applies. Streamline's own code is MIT, but it loads NVIDIA plug-ins under separate terms. Do not adopt it without review.
- **AMD FSR2 (and CAS/LPM): MIT**, which is GPLv2-compatible. The committed prebuilt `.lib` files raise a GPL "complete corresponding source" question: the distributor of a GPL combined binary must be able to provide source for all of it. Recommendation: build FSR2 from pinned public source rather than shipping opaque `.lib` blobs (Q9).

### 5.4 RayTracedGL1 vs a GPL-2.0-only engine

- RTGL1's own code is **MIT, so it can be used with GPL-2.0**. MIT, Zlib, BSD-3/BSD-1 and the other permissive dependencies are also fine.
- **Apache-2.0 KTX-Software code is compiled into `RayTracedGL1.dll`.** FSF position: Apache-2.0 is compatible with GPLv3 but **not with GPLv2**. If the FSF combined-work view of dynamic linking applies, distributing the GPL-2.0-only engine together with a KTX-containing RTGL1 DLL may be non-compliant. **This is a potential blocker for the RT candidate** (Q1). Mitigation options to evaluate: (a) replace KTX loading with a permissive or GPLv2-compatible KTX2 reader, (b) get clarity from KTX authors or counsel, (c) treat RTGL1 as a separate program (unlikely to hold for an in-process DLL).
- Branch caveat: the audited `hl1` branch is not necessarily what Serious-Engine-RT used (last pin `7a88e38`). Vendored dependencies may differ per branch. Re-audit the exact commit RD-001/RD-005 select.

## 6. Repository license recommendations

All of this is a **proposal**. The owner confirms each line (plan §2, §9.5). The SPDX identifiers are from the SPDX License List.

| Repository | Recommended `SPDX-License-Identifier` for original SSTRE code | Data / docs | Third-party content | Key conditions |
|---|---|---|---|---|
| **SSTRE** (umbrella) | `GPL-3.0-only` (owner may choose `GPL-3.0-or-later`) | docs: `GPL-3.0-only` by default, `CC-BY-SA-4.0` optional. `schemas/`: **`CC0-1.0`** so that the GPL-2.0-only engine and any tool can implement the contracts freely | none expected | builder invokes engine and tools as processes and must not link them. Release bundles = aggregate with per-component notices |
| **SSTRE-Engine** | **`GPL-2.0-only`**: preserve upstream LICENSE and headers verbatim, **do not relicense**. New SSTRE-authored files: `GPL-2.0-only`, or **`GPL-2.0-or-later`** (option; this lets SSTRE's own engine code be reused later in GPL-3.0 tools) | `docs/sstre/`: `GPL-2.0-only` or `CC-BY-SA-4.0` | per-file: `Zlib`, `BSD-3-Clause`, `MIT`, `Apache-2.0` (via RTGL1/KTX, see Q1), `LicenseRef-NewTek-LWSDK`, `LicenseRef-Microsoft-DirectSound-Header`, `GPL-2.0-or-later WITH <Bison 1.24 exception>` (verify the exact SPDX exception ID, e.g. `Bison-exception-1.24`, against the SPDX exceptions list) | first import upstream with full history (see RD-001). Exclude LWSkaExporter SDK and `DSOUND.H` from shipped builds unless cleared. **No DLSS/NRD in distributed builds** |
| **SSTRE-AssetCompiler** | `GPL-3.0-only` (or `-or-later`) | test fixtures: synthetic only, `CC0-1.0` | must not contain engine-derived (GPL-2.0-only) code. Engine-derived readers go in a GPL-2.0-only helper in SSTRE-Engine, called as a process | write clean-room format code from documentation and record the sources used |
| **SSTRE-Manifests** | scripts, if any: `GPL-3.0-only` | **recommend: `CC0-1.0` for schemas and generated lock manifests. `CC-BY-SA-4.0` for curated human-authored recipes, prompts and mappings.** Plan alternative: `GPL-3.0-only` throughout (works, but "source code"/"preferred form" concepts fit data poorly) | **must not contain game assets or derived images.** Names, paths and hashes of Croteam files: see Q7 | see §6.1 |
| **Remaster-Toolkit** | `GPL-3.0-only` (or `-or-later`) | workflows (ComfyUI JSON): same as code. Fixtures: `CC0-1.0` or a permissive license compatible with the source | ComfyUI is GPL-3.0 (GitHub metadata; version variant not checked). PyTorch BSD-3, Real-ESRGAN BSD-3, SwinIR Apache-2.0: all GPLv3-compatible | **model weights are not dependencies of the code license.** Never commit weights. Record each weight's license in provenance (§8) |

### 6.1 Data licensing for SSTRE-Manifests

| Option | Pros | Cons |
|---|---|---|
| `GPL-3.0-only` (plan default) | one license family. Copyleft on curated work | GPL terms (source, object code, installation information) are awkward for JSON/YAML data. Downstream reuse of the data outside GPLv3 tools is unclear |
| `CC-BY-SA-4.0` | built for non-software works. Share-alike. **One-way compatible with GPLv3** (Creative Commons declared this in 2015; the CC compatible-licenses page was not re-fetched this session), so manifests can be bundled into GPLv3 tools | attribution bookkeeping. Not usable *inside* a GPL-2.0-only work |
| `CC0-1.0` | maximal interoperability (engine, tools, third parties). Good for generated locks, hashes and schemas, which have little original authorship anyway | no copyleft or attribution. CC0 has a patent disclaimer and is not an OSI software license (irrelevant for data) |
| `ODbL-1.0` | designed for databases (EU sui generis right) | share-alike scope is complex. Poor fit with GPL tooling. Uncommon in game-modding contexts |

Caution for any option: manifests list **third-party asset identifiers** (Croteam/Devolver file paths, names, SHA-256 hashes, possibly dimensions and texture descriptions). Our license can only cover *our* contribution. Short factual identifiers and hashes are generally weakly protectable, but a complete structured listing of a game's file tree could, in the EU, touch the database right (Directive 96/9/EC), and text such as level or entity names may be trademark-relevant. **Hypothesis, see Q7.** The brief already restricts dossiers to aggregates and top-level hashes. Apply a similar minimisation to manifests (stable IDs and hashes; no copied text, no thumbnails).

### 6.2 `GPL-3.0-only` vs `GPL-3.0-or-later` (owner decides)

| | `GPL-3.0-only` | `GPL-3.0-or-later` |
|---|---|---|
| Control | owner keeps control over future versions. No FSF "proxy" decision | the FSF can publish a GPLv4 that recipients may choose. GPLv3 §14 allows a named *proxy* to approve later versions, a middle ground |
| Compatibility | combinable with GPL-3.0-or-later and Apache-2.0 code | the same, plus future compatibility with a hypothetical GPLv4-only ecosystem |
| Ecosystem | ComfyUI (GPL-3.0), most tooling: both work | FSF recommends "or later". Many Python projects use it |
| Relevance to engine | **neither is compatible with GPL-2.0-only.** The choice does not affect the engine boundary | same |

Neutral observation: `-only` matches the plan's stated preference and is easier to reason about. `-or-later` reduces future relicensing friction. Either way, use a DCO (or a CLA if the owner wants relicensing flexibility). That too is an owner decision (Q11).

## 7. Game assets, EULA, Steam terms, trademarks

### 7.1 Classic TFE/TSE in-game license (GHI Media, LLC; local `license.txt`)

Short excerpts (section headings as in the file):

- *LICENSE*: *"…the nonexclusive, non-transferable, limited right and license to use one copy of the Software for your personal non-commercial use for gameplay on a single computer … unless otherwise specified in the Software documentation."*
- *OWNERSHIP*: the licensor retains all rights in *"…artwork, sounds effects, musical works…"*, and *"The Software may not be copied, reproduced or distributed in any manner or medium, in whole or in part, without prior written consent from Licensor."*
- *LICENSE CONDITIONS*: you agree not to *"(a) Commercially exploit the Software; (b) Distribute … the Software … (c) Make a copy of the Software or any part thereof (other than as set forth herein) … (h) Reverse engineer, decompile, disassemble, prepare derivative works based on or otherwise modify the Software, in whole or in part; (i) Remove or modify any proprietary notices…"*
- *USER CREATED CONTENT*: content created "through use of the Software" is licensed to the licensor on an *"exclusive, perpetual, irrevocable, fully transferable and sub-licensable worldwide"* basis.
- Governing law: Texas. Venue: Travis County.
- The document says the current version is posted at `www.devolverdigital.com/eula`. **That URL was inaccessible** (HTTP 429).

Interpretation (hypothesis): taken literally, clause (h) prohibits preparing derivative works of "the Software", which the EULA defines to include all included files. Upscaled or PBR textures made from the game's textures are plausibly "derivative works". **Distributing** them is clearly unlicensed (clauses (b) and OWNERSHIP). Even **local** generation by the user is at least arguably restricted, despite the fact that the same installation ships `SeriousEditor.exe` and `SeriousModeler.exe` (observed in `Bin/`) and the readme points to "game editing and mod development" forums. The clause "unless otherwise specified in the Software documentation" and the shipped tools may support an implied modding permission. **That is for counsel** (Q6). The UCC clause may claim exclusive rights in user-created levels/content made "through use of the Software". Assess whether SSTRE curated overrides could fall under it (Q8).

### 7.2 HD and Fusion

No EULA file was found in the HD TFE/TSE or Fusion 2017 installs, and the Steam store pages list no game-specific EULA (only "© 2001-2016 Croteam. All rights reserved." for TFE Classic, "© 2018-2019 Croteam" for Fusion). The Fusion install ships only third-party notices (`Help/External_EULA`). **HD/Fusion asset terms are therefore governed by the Steam Subscriber Agreement plus any EULA accepted at first launch, which was not captured.** Plan §3 prefers HD textures as a source, so that is an open question (Q6).

### 7.3 Steam Subscriber Agreement (SSA, last updated 2026-09-10)

- §1.B: subscriptions may carry additional terms, *"an end user license agreement specific to a particular game"*.
- §2.A: Valve grants *"a non-exclusive license and right, to use the Content and Services"* (personal, non-commercial).
- §2.G: *"Except as otherwise permitted under this Agreement"* (including Subscription Terms), *"you may not … copy, … reproduce, publish, distribute … reverse engineer, derive source code from, modify, disassemble, decompile, create derivative works based on…"*.
- §4.B: no *"Cheats, mods, hacks, or any other unauthorized third-party software"* *"when playing multiplayer versions of any Content and Services"*. This is relevant to co-op/multiplayer with a modified engine and asset set.
- §6: Workshop terms (Fusion has Workshop support). These are not applicable to SSTRE unless SSTRE content is published via Workshop.

### 7.4 EU law angle (owner is a Dutch entity; hypothesis for counsel)

- Directive 2009/24/EC Art. 5(1), 5(3), 6 and 8 give lawful users certain non-overridable rights (observation, interoperability decompilation) for **computer programs**. Textures, models and sounds are generally protected as other works, not as programs, so those exceptions are unlikely to cover asset conversion (Q10).
- National private-copy and format-shifting rules vary, and their interaction with EULA clauses is a legal question. **Nothing here establishes that local conversion is permitted.** ADR-0002's "user supplies own data and processes locally" is a **project policy, not a legal clearance**.

### 7.5 Trademarks and branding

- USPTO (via the Justia aggregator, secondary): **SERIOUS SAM**, serial 76147261, owner Croteam, Ltd. (computer game software). Further SERIOUS SAM filings are owned by Devolver Digital, Inc. (e.g. one filed 2022-03-21, printed matter). Devolver acquired Croteam (reported 2020-10). **EUIPO/Benelux not checked** (Q12).
- "SSTRE — Serious Sam: The Raytraced Encounter" uses the mark in the project's *name*. Nominative or descriptive use ("for Serious Sam") is generally lower risk than a title that looks like an official product. A title in the official naming pattern ("The X Encounter") increases confusion risk. **Owner/counsel decision** (Q12).
- Proposed guidance (pending review):
  1. Every README, release and UI splash shows a standard disclaimer: *"SSTRE is an unofficial, fan-made project. It is not affiliated with, endorsed by, or sponsored by Croteam or Devolver Digital. Serious Sam is a trademark of its respective owner(s). No game assets are included; you need a legally acquired copy of the game."*
  2. Do not use Croteam/Devolver/Serious Sam **logos**, box art, key art or the official logotype in repo avatars, icons, badges or splash screens. Use original SSTRE iconography.
  3. Prefer the acronym "SSTRE" and descriptive phrasing ("a ray-tracing remaster toolkit for Serious Sam Classic"). Avoid "Official", "HD", "Remastered Edition" or "4K Edition" wording that imitates Croteam product names.
  4. No commercial use, donations-for-builds or paid distribution without counsel review (the EULA prohibits commercial exploitation).
  5. Respect existing upstream naming: forks should keep their upstream attribution (Croteam, Sultim, tx00100xt, rcgordon) in README credits.

## 8. AI model and weight licenses (compliance angle; selection belongs to Agent C / RD-003)

Hugging Face model-card metadata (`/api/models/<id>`, 2026-11-27; `sha` = model repo revision at query time):

| Model | License (card) | Revision observed | Compliance note |
|---|---|---|---|
| `stabilityai/stable-diffusion-xl-base-1.0` | `openrail++` (CreativeML Open RAIL++-M) | `462165984030d82259a11f4367a4eed129e94a7b` | use-based restrictions (Attachment A) must be passed on to downstream users of the model or derivatives. Outputs are not claimed by the licensor but must not be used for restricted purposes. Fine-tunes inherit these terms |
| `black-forest-labs/FLUX.1-dev` | `flux-1-dev-non-commercial-license` (gated) | `45d95c497444bbaebe766e1528792fc9158c0c3a` | **non-commercial. Treat as excluded for release pipelines** unless the owner accepts NC constraints for a free project. Even then the terms need review, including restrictions on outputs |
| `black-forest-labs/FLUX.1-schnell` | `apache-2.0` (gated) | `169573f54945f633efbe126a40a5676b4228363c` | permissive. Check the gating terms |
| `Qwen/Qwen2.5-VL-3B-Instruct` | `qwen-research` | `66285546…` | research-only variant. **Avoid** |
| `Qwen/Qwen2.5-VL-7B-Instruct` | `apache-2.0` | `cc594898…` | permissive (dev-time only per plan) |
| `Qwen/Qwen2.5-VL-72B-Instruct` | `qwen` (Qwen license, with a user-count threshold) | `89c86200…` | custom terms. Review before use |
| `Qwen/Qwen3-VL-8B-Instruct` | `apache-2.0` | `0c351dd0…` | permissive |
| Real-ESRGAN (code + release weights) | repo `BSD-3-Clause` (GitHub metadata); weights published as GitHub release assets (latest tag seen `v0.3.0`) | — | **Assumption:** release weights are under the repo's BSD-3. The license is not stated per weight. Confirm. Third-party community ESRGAN models often carry CC-BY-NC-SA or no license. **Exclude unlicensed or NC community upscalers** |
| SwinIR | repo `Apache-2.0` | — | weights' license to confirm |
| ComfyUI | `GPL-3.0` | `a14e815c…` (HEAD) | custom nodes each have their own license. Review every node (plan §4: never auto-execute untrusted nodes) |

Rules proposed for the toolkit (feed into RD-003/RD-004 provenance):
1. Record license ID, URL, accepted-terms date and revision hash for every weight in the lock manifest. CI rejects weights whose license is missing or on a deny-list (NC, research-only, unknown).
2. Never commit or redistribute weights (plan §1). Users download them themselves after accepting the terms.
3. A release pipeline uses only models whose license permits the intended distribution of outputs. A dev-time VLM must not be needed at release (plan §3) and is lower risk, but its license still applies to dev use.
4. AI-generated output copyrightability is unsettled and jurisdiction-dependent. Do not assert SSTRE copyright in generated pixels beyond the human-authored recipes (Q13).

## 9. Assumptions and unknowns

- The FSF's interpretation (dynamic linking = combined work; Apache-2.0 incompatible with GPLv2) is used as the conservative baseline. Courts and other commentators may differ.
- RTGL1 dependency lists are from the `hl1` branch. The branch and commit the selected engine actually needs may differ.
- Submodule licenses (imgui, glfw, cgltf, glaze) come from GitHub metadata. The pinned trees were not inspected.
- The Devolver online EULA and any HD/Fusion first-run EULA were not read. The Classic EULA text is assumed current as shipped.
- Trademark data is secondary (Justia) and US-only.
- No inspection of the `doom`/`quake` RTGL1 branches, the `rcgordon/Serious-Engine` x64 port, or the 2001 Croteam SDK license.

## 10. Alternatives and tradeoffs

| Topic | Option A | Option B | Tradeoff |
|---|---|---|---|
| Engine/tool boundary | separate processes + file formats (recommended) | single monorepo/executable | B is legally impossible with GPL-2.0-only + GPL-3.0 code |
| Engine-derived format readers | GPL-2.0-only helper CLI in SSTRE-Engine | clean-room readers in GPL-3.0 AssetCompiler | A is faster and more faithful. B gives one Python code base but needs documented clean-room discipline |
| RT upscaler/denoiser | FSR2 (MIT), built from source | DLSS/NRD | B is incompatible with distributing GPL builds (hypothesis, Q3) |
| KTX2 loading in RTGL1 | keep KTX-Software (Apache-2.0) | replace with a GPLv2-compatible loader | A carries a GPLv2 compatibility risk (Q1). B is engineering work |
| Manifests license | CC0 / CC-BY-SA split (recommended) | GPL-3.0-only throughout | §6.1 |
| Asset distribution | user-side local build only (ADR-0002) | distribute converted packs | B is clearly unlicensed under the Classic EULA (§7.1) |

## 11. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Apache-2.0 KTX code in RTGL1 makes distributed RT engine builds non-compliant with GPLv2 | Medium | High | Q1. Replace KTX loader or get advice before any binary release |
| R2 | Someone enables DLSS/NRD in a distributed build | Medium | High | CI/build-flag guard. Policy: never distribute. `RG_WITH_NVIDIA_DLSS=OFF` enforced |
| R3 | TFE entity sources are not validly GPL (2001 SDK origin) | Unknown | High (TFE-first plan) | Q4. Compare RT/Vk/tx00100xt/SE1-ModSDK provenance. Ask Croteam |
| R4 | GPL-2.0-only engine code copied into GPL-3.0 tools (format readers) | Medium | Medium | contributor guidance, review checklist, helper-CLI pattern |
| R5 | Converted or derived assets, screenshots or thumbnails get committed or published | Medium | High | `.gitignore`, pre-commit size/type checks, REUSE lint, review. ADR-0002 |
| R6 | Trademark complaint about the project name or branding | Low–Medium | Medium–High | disclaimer, no logos, counsel review of "The Raytraced Encounter" |
| R7 | NC/research-only model used in the release pipeline | Medium | Medium | license field + deny-list in lock manifests |
| R8 | Shipped `LWSkaExporter/SDK` or `DSOUND.H` without clear terms | Low | Medium | exclude from SSTRE build targets and source releases. Q9 |
| R9 | Committed prebuilt binaries (FSR2 `.lib`, Bison/Flex `.exe`) break corresponding-source or supply-chain hygiene | Medium | Low–Medium | build from pinned source. Don't ship or run upstream `.exe` files |
| R10 | Repos stay public without a LICENSE (all rights reserved), deterring contributors | High (current state) | Low | owner approves LICENSE files in Phase 0 |

## 12. Proposed experiment and measurable success criteria

| Experiment | Success criterion |
|---|---|
| E1: Run the REUSE tool (`reuse lint`), ScanCode Toolkit and `licensee` on the selected engine commit and the selected RTGL1 commit (read-only, in a scratch copy). **Proposed, not installed.** | Full per-file license inventory. Every file either REUSE-compliant or listed in a deviations table. Zero unknown licenses in files that are compiled into shipped targets |
| E2: Build RTGL1 with a KTX loader replaced by a GPLv2-compatible implementation (or prove KTX is not compiled in the selected config) | `RayTracedGL1.dll` contains no Apache-2.0-only object code (link map plus ScanCode on compiled sources) |
| E3: Provenance diff of TFE `Sources/Entities` across RT, Vk, tx00100xt and SE1-ModSDK | Origin documented with commits. Decision recorded on whether TFE entity code is usable |
| E4: Build-flag guard | CI fails if `RG_WITH_NVIDIA_DLSS` or any NGX/NRD path is enabled in release configs |
| E5: Repo hygiene | `reuse lint` passes on all four new repos in CI. LICENSE/LICENSES present after owner approval |

## 13. Recommendation

1. **Engine: `GPL-2.0-only`, preserved verbatim.** Do not relicense, and never link GPL-3.0 code into it.
2. **SSTRE, AssetCompiler, Remaster-Toolkit: `GPL-3.0-only`** (owner may pick `-or-later`). **Manifests: `CC0-1.0` (schemas, generated locks) plus `CC-BY-SA-4.0` (curated recipes)**, or `GPL-3.0-only` if the owner prefers uniformity. **Umbrella `schemas/`: `CC0-1.0`.**
3. Enforce the process boundary: tools and engine communicate only via files and CLIs. Engine-derived format code stays GPL-2.0-only in SSTRE-Engine.
4. **No DLSS/NRD/NGX in any distributed build.** FSR2 is OK, built from source.
5. **Before any binary release of the RT path, resolve Q1 (Apache-2.0 KTX in RTGL1).** Before relying on RT/Vk TFE entities, resolve Q4.
6. **Never distribute game assets or derivatives** (Classic EULA §LICENSE CONDITIONS (b), (h)). User-side local builds are a project policy, not a clearance (Q6).
7. Adopt the [notices policy](../policies/notices-policy.md) (REUSE + `THIRD_PARTY_NOTICES.md`) and the trademark disclaimer in §7.5.

## 14. Decision dependencies

- ADR-0005 (engine foundation): the RT vs Classic-VK choice changes the dependency set (RTGL1/KTX/FSR2 vs VMA/SDL2) and the TFE-entity question.
- ADR-0006 (licensing boundaries): consumes §6 and §13 and requires owner confirmation.
- RD-003/RD-004: model allow/deny list and the license fields in the provenance schema.
- RD-008: release-bundle composition (aggregate notices, corresponding-source offer for GPL binaries).

## 15. Next steps

1. Owner confirms SPDX IDs per repo (§6) and `-only` vs `-or-later`. Agent F then adds `LICENSE`/`LICENSES/` (texts from SPDX/REUSE, unmodified). Copyright line: *"Copyright (C) <year> Handelsonderneming S.D. Broekhoven and SSTRE contributors"*, wording subject to owner approval.
2. Lead/owner take the questions in §16 to counsel. Q1, Q3, Q4 and Q6 block a public binary release. None of them blocks Phase 0 documentation.
3. Run E1 to E3 once RD-001 pins the engine and RTGL1 commits.
4. Add a `license` and `license_url` field to the model/weight provenance schema (RD-004).
5. Add the trademark disclaimer to all READMEs when Agent F scaffolds them.

## 16. Unresolved legal questions for the owner/counsel

Status values: **open** (owner or research action, no counsel needed yet) · **owner-decided** (decided by the owner; date and ADR given) · **needs counsel** (legal judgment required; a project policy may already apply in the meantime). Status column added 2026-11-27. The question texts of Q1–Q14 are unchanged.

### 16.1 Decided by the owner on 2026-11-27

| # | Decision | Status | Source |
|---|---|---|---|
| D1 | Repository licences: `GPL-3.0-only` for SSTRE, AssetCompiler and Remaster-Toolkit; `GPL-2.0-only` for the engine, preserved and never relicensed; Manifests `CC0-1.0` (factual metadata) / `CC-BY-SA-4.0` (creative recipes). Answers §6 / §6.2 | owner-decided (2026-11-27) | ADR-0006 |
| D2 | Contributor terms: DCO, no CLA (closes Q11) | owner-decided (2026-11-27) | ADR-0006 rule 1 |
| D3 | Copyright holder for SSTRE's own work: "Handelsonderneming S.D. Broekhoven, trading as ITEagle Europe". Upstream notices untouched. Supersedes the §15 step 1 draft wording | owner-decided (2026-11-27) | ADR-0006, Phase 1 brief |

### 16.2 Register

| # | Question | Status | Notes / blocking |
|---|---|---|---|
| Q1 | **RTGL1 + KTX (Apache-2.0) + GPL-2.0-only engine:** is distributing `RayTracedGL1.dll` (containing Apache-2.0 KTX-Software code) together with, and dynamically linked by, the GPL-2.0-only Serious Engine compliant? Would replacing KTX be required? | needs counsel | Engineering mitigation under Phase 1 investigation: KTX only in the GPLv3 AssetCompiler (ADR-0006 consequences). Blocks binary release (ADR-0006 rule 6). |
| Q2 | **Process boundary:** does a GPL-3.0 tool chain that writes engine-specific compiled asset files, consumed by a GPL-2.0-only engine and bundled in one SSTRE release archive, count as "mere aggregation" under GPLv2 §2 and GPLv3 §5 in the relevant jurisdictions (NL/EU, US)? | needs counsel | Owner adopted the process-boundary **policy** (ADR-0006 rule 2). The legal characterisation is still open. |
| Q3 | **DLSS/NRD:** is any DLSS-enabled build (private, or distributed with a separate opt-in plug-in DLL) possible without breaching GPLv2 or the NVIDIA RTX SDK license §4(e)? Does the GPLv2 system library exception apply to driver-distributed NGX components in any configuration? | needs counsel | Owner **policy** decided: no DLSS/NRD in any distributed GPL build (ADR-0006 rule 5). Private-build question still open. Blocks binary release. |
| Q4 | **TFE entity code provenance:** is the TFE `Sources/Entities` code (RT/Vk commit `4d17950`, tx00100xt `c4f9322`) validly licensed under GPL-2.0, or does it derive from the 2001–2002 Croteam SDK under its original proprietary terms? Can Croteam/Devolver confirm in writing? | needs counsel | Needs written confirmation from Croteam/Devolver. New evidence in [EXP-004](../experiments/EXP-004-upstream-publication-audit.md) H6: absent from Croteam-official; CVK GPL header added downstream; 90 of 136 files identical to the headerless RT import; third-party claim of 2001–2002 SDK origin "under a different license". Blocks publication of both upstream branches. |
| Q5 | **`SE1_10.gro` resources:** are the Croteam models, textures and sounds bundled in the official GPL repo covered by GPL-2.0, by some other implied license, or by none? May SSTRE redistribute or depend on them? | needs counsel | EXP-004 G1: Croteam published it; 1,674 of 1,802 entries are identical to retail archive entries; README says "freely use the engine" (scope undefined). Blocks publication of `upstream/rt-main`. |
| Q6 | **Local conversion of user-owned assets:** under the Classic EULA (GHI Media, clause (h) "prepare derivative works"), the SSA §2.G, the HD/Fusion terms (not captured) and Dutch/EU law, may a user run SSTRE tools that create upscaled or PBR derivatives of their own legally acquired copy for private use? Does the bundled Serious Editor/Modeler, or "unless otherwise specified in the Software documentation", imply a modding permission? What about upstream precedent such as Serious-Engine-RT's `TFE_RT_Textures.zip`? | needs counsel | ADR-0002 user-side processing is a project policy, not a clearance. |
| Q7 | **Manifests:** may a public repo list Croteam/Devolver asset paths, names, dimensions and SHA-256 hashes (EU database right, copyright in file/level names, trademark)? What minimisation is enough? | needs counsel | Owner **policy** decided: asset IDs, paths and hashes are local use only until GATE-05 (Phase 1 brief). The legal question stays open. |
| Q8 | **EULA user-created-content clause:** does the Classic EULA's exclusive UCC license affect SSTRE contributors' curated overrides, recipes or maps that are created with the game's tools or derived from its assets? | needs counsel |  |
| Q9 | **Unlicensed vendor files in upstream:** what are the terms for redistributing `Sources/LWSkaExporter/SDK/*` (NewTek) and `Sources/Engine/Sound/DSOUND.H` (Microsoft) in the SSTRE-Engine source repo? Should they be removed from the fork? Does shipping prebuilt FSR2 `.lib` files satisfy GPLv2 corresponding-source duties? | needs counsel | EXP-004 H1/H2: the same `DSOUND.H` and LightWave SDK blobs are in Croteam-official and in both branch histories. A removal commit does not remove them from published history (see Q16). |
| Q10 | **EU Software Directive:** do any of the non-overridable rights in 2009/24/EC Art. 5–6, 8 apply to SSTRE's extraction tooling (e.g. archive/format parsing for interoperability), and do they reach non-program assets at all? | needs counsel |  |
| Q11 | **Contributor terms:** DCO vs CLA, and whether SSTRE wants the ability to relicense its own code (e.g. `-only` → `-or-later`, or GPLv2-compatible dual licensing of SSTRE-authored engine code). | owner-decided (2026-11-27) | DCO (`Signed-off-by`), no CLA; contributors keep copyright; `GPL-3.0-only` (not `-or-later`) per ADR-0006. Residual sub-question: dual licensing of SSTRE-authored engine code was not decided (open, low priority). |
| Q12 | **Trademark:** is "SSTRE — Serious Sam: The Raytraced Encounter" acceptable nominative use in the EU/Benelux and US, or should the project be renamed? Which marks are registered at EUIPO/BOIP? Is a written fan-project permission from Devolver/Croteam advisable? | needs counsel | Name pending trademark review (ADR-0006 rule 8). Disclaimer adopted. |
| Q13 | **AI outputs:** what is the copyright status of AI-assisted derivatives of copyrighted textures? Do model licenses (OpenRAIL++-M use restrictions, Qwen license thresholds) impose obligations on the distribution of SSTRE tools that merely download and run those models? | needs counsel |  |
| Q14 | **Console research:** platform SDK NDAs typically conflict with GPL source publication. Is any console path viable for a GPL-2.0-only engine? (Cross-reference RD-006; not analysed here.) | needs counsel | Split into four questions per platform in [RD-006 §3.5](./RD-006-platforms.md#35-legal-split-per-platform-four-separate-questions). This row covers only the **platform SDK licensing** column. Homebrew legality is Q19, Steam is Q18, and game IP is an owner action (RD-006 U5). |
| Q15 | **Retail game data in CVK history:** `upstream/classic-vk-main` contains, from its single import commit `c4f9322`: demo recordings and thumbnails (32 of 34 files byte-identical to the retail install), retail-identical `Scripts`/`Controls`/`Help`/`Data` files (185), `SE1_10b.gro` (not in Croteam's release; 13 entries of unknown origin) and mod thumbnails. No Croteam publication covers any of them. May any of them be redistributed? (EXP-004 G2–G5) | needs counsel | Blocks publication of `upstream/classic-vk-main` as-is. Default under ADR-0006 rule 4: do not publish. |
| Q16 | **Publication route for upstream histories:** publishing a branch publishes every reachable blob, so a removal commit (option 2) does not stop distribution. Should the owner (a) keep the branches local (option 4), (b) publish only SSTRE patches against pinned upstream URLs and SHAs (option 5), or (c) allow a *new* filtered import branch (option 3)? Option 3 conflicts with the literal ADR-0006 wording "never by rewriting it" and changes 446/449 (RT) and 309/311 (CVK) commit SHAs. | **owner-decided 2026-11-27: option 5** | Own patches against pinned upstream commits; upstream histories stay local ([ADR-0008](../adr/0008-engine-patch-distribution.md), provisional). This does not unblock binary distribution. |
| Q17 | **Screenshots in upstream histories** (CVK `Images/*.png`, RT `Github/*.png`; 54 MB of rendered game assets): are they "derivatives of game assets" under ADR-0006 rule 4, and is publishing them acceptable? (EXP-004 G9) | open (owner); counsel optional | Recommendation: exclude. |
| Q18 | **Steam distribution:** may SSTRE (GPL-2.0-only engine, no assets) be offered on Steam (own app, mod page or Workshop) without Croteam/Devolver consent? Can it use the Steamworks SDK, which Valve says is "problematic" with copyleft (RD-006 P21)? Does Steam Deck sideloading raise any issue beyond Q6? | needs counsel | RD-006 §3.5. Sideloading needs no platform permission. |
| Q19 | **Circumvention / homebrew:** under Dutch/EU law (2001/29/EC art. 6 as implemented) and US DMCA §1201, may the project document, test or support homebrew builds that require console exploits (PS5, Switch, Switch 2, Vita)? Pending an answer, the recommended project policy is "not pursued". | needs counsel | RD-006 §3.5, P24. |
| Q20 | **Xbox Developer Mode:** do the terms of the Xbox Developer Mode Activation Program (not read) allow a publicly shared, sideloadable GPL test build? Can a D3D backend for it be published as GPL without GDK/NDA material? | open (read the agreement), then needs counsel | RD-006 §3.5, P18–P20. |
| Q21 | **Unattributed RT assets:** provenance and licence of `OverridenTextures/WaterNormal_n.ktx2`, and of the blue-noise data in `BlueNoise_LDR_RGBA_128.ktx2` (the same blob ships in RTGL1, MIT, without a source credit). | open (ask the author) | EXP-004 G7/G8. |
| Q22 | **Headers without a grant:** 43 CVK files carry only "Copyright (c) 2002-2012 Croteam Ltd. All rights reserved." (downstream port files, absent from Croteam-official), and 2,946 pre-GPL Croteam blobs remain in RT history. Is the repo-level GPL-2.0 statement sufficient for them? | needs counsel (low priority) | EXP-004 H3/H4. Notices are preserved verbatim in any case. |
| Q23 | **Filtered-history attribution:** if option 3 is chosen, do omitting whole files and rewriting SHAs (with a published commit map and NOTICE) satisfy GPLv2 §1/§2 notice duties and upstream attribution expectations? | needs counsel (low priority) | Relevant only if Q16 selects option 3. |
