# EXP-003: Runtime dependency licensing for the RTGL1 / engine runtime, and removing KTX-Software

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | RD-007 Q1 / E2 / E4 (KTX in the GPLv2 runtime, DLSS build guard). ADR-0006 "KTX in the runtime" consequence |
| Status | **complete for the compile and parse level. Runtime rendering was not tested.** This is evidence plus options. It is **not legal advice and not a legal clearance.** |
| Environment | Windows 11 Pro 10.0.22631. MSVC 19.35.32215 (VS 2022 17.5, v143, x64). CMake 4.4.4. Ninja 1.13.2 (`local-work\tools\ninja`). Vulkan SDK 1.4.363.0 (headers and `vulkan-1.lib` only). No GPU work was done. No NVIDIA or AMD SDK was downloaded. |
| Inputs | RayTracedGL1 clone `upstream/sultim-t_RayTracedGL1`: tag **`v1.1.0` = `b1eb3d8ca3fe75f6f4dda16a53aeb99ea613aead`** (the revision SE-RT most likely uses, per RD-005 §3.1) and **`hl1` HEAD = `2457acc25df5766e48289205471cc2a07499f7f6`**. SeriousSamClassic-VK `510d36f`. Serious-Engine-RT `0e7f223`. No game data was used. |
| Scratch | `local-work\deps\`. Worktree `rtgl1-noktx` on the new local branch `phase1/no-ktx` (3 commits on top of `v1.1.0`). Build logs `build-{baseline,stub,reader,reader2}.log` and `cfg-dlss.log`. Differential test in `difftest\`. Guard prototype in `scripts\check_rtgl1_build.py`. `ktxref\` holds a local-only extract of the RTGL1 v1.1.0 `Source/KTX` tree, used only as the test oracle. |

## Goal and success criteria

The owner asked for four things:

- remove Apache-2.0 KTX code from the GPL-2.0-only runtime;
- consider doing KTX processing only in the GPL-3.0-only AssetCompiler;
- audit **all** RTGL1 dependencies, plus the runtime dependencies of Classic-VK and SE-RT;
- confirm that DLSS, FSR and NRD are off and propose a guard.

The experiment succeeds if:

1. every dependency of both RTGL1 revisions is listed with its location, its license evidence and a GPL-2.0 compatibility class;
2. the exact use of libktx is identified;
3. RTGL1 v1.1.0 compiles **with no KTX-Software object code**, and the replacement reads the same data as libktx;
4. a build guard detects DLSS/NGX and KTX objects.

## Procedure (exact, reproducible)

1. Inventory [SRC]. Commands: `git show <rev>:.gitmodules`, `git ls-tree -r <rev>`, `git show <rev>:CMakeLists.txt`, and `git grep -n -E 'ktx[A-Za-z_]*\(|<ktx' <rev> -- 'Source/*.cpp' 'Source/*.h'`. License headers were read with `git show <rev>:<file> | head`. Submodule pins come from `git ls-tree`, and the commit date and license of each pin from `gh api repos/<o>/<r>/commits/<sha>` and `gh api repos/<o>/<r>` (`.license.spdx_id`). Compatibility classes come from the FSF license list <https://www.gnu.org/licenses/license-list.html>, fetched 2026-11-27 [DOC].
2. Worktree:
   ```
   git -C <ws>/upstream/sultim-t_RayTracedGL1 worktree add L:\claude-ws\SSTRE\local-work\deps\rtgl1-noktx -b phase1/no-ktx v1.1.0
   ```
3. Builds. All three use `local-work\deps\scripts\build.cmd <src> <build>`, which runs `vcvars64`, sets `VULKAN_SDK=C:\VulkanSDK\1.4.363.0`, and then:
   ```
   cmake -S rtgl1-noktx -B <build> -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=cl -DCMAKE_CXX_COMPILER=cl -DRG_WITH_SURFACE_WIN32=ON -DRG_WITH_NVIDIA_DLSS=OFF
   cmake --build <build> -- -k 0
   ```
   - `build-baseline`: unmodified `v1.1.0`.
   - `build-stub`: commit `70e3a43`.
   - `build-reader`: commit `e400441`, then `3f50942`.
4. Differential test. `difftest\build_difftest.cmd` (cl `/Od /Zi /MDd /RTC1 /GS`) compiles `difftest.cpp` together with the prototype reader and, as the oracle, the 15 libktx sources from `ktxref`. `difftest.exe <RTGL1 Tools\BlueNoise_LDR_RGBA_128.ktx2>` then:
   - generates 10 synthetic KTX2 files (DFD from libktx `vk2dfd`);
   - loads each file with both readers and compares format, dimensions, counts, `GetDataSize`, every `(level, layer, face)` offset and size, and the image bytes;
   - fuzzes the prototype with truncations and bit flips.
5. Guard. `python scripts\check_rtgl1_build.py <build>` was run on all three builds. A DLSS negative test (`scripts\cfg_dlss.cmd`) configures with `-DRG_WITH_NVIDIA_DLSS=ON` and with `DLSS_SDK_PATH` unset.

## Results ([EXP] unless labelled otherwise)

### R1. Builds

| Build | Configure + build | Objects | KTX-Software objects | `RayTracedGL1.dll` | Warnings |
|---|---|---|---|---|---|
| `build-baseline` (unmodified v1.1.0) | exit 0, `[79/79] Linking CXX shared library RayTracedGL1.dll` | 78 | **15** | 809,472 B | 3, all KTX `gl_format.h(95): warning C4005: 'NOMINMAX'` |
| `build-stub` (libktx removed, loader always fails) | exit 0, `[64/64]` | 63 | 0 | 473,088 B | 0 |
| `build-reader` (prototype KTX2 reader + zstd) | exit 0, `[66/66]`; rebuild after hardening `[2/2]` | 65 | 0 | 780,288 B | 0 |

- KTX object counts are `grep -o 'Source.KTX[^ ]*\.obj' build.ninja | sort -u | wc -l`.
- A byte scan of the baseline DLL finds the libktx metadata key strings `KTXorientation` and `KTXanimData`. The reader DLL contains **0** of them.
- `dumpbin /dependents` on the reader DLL lists only `vulkan-1.dll`, `KERNEL32.dll`, `MSVCP140.dll`, `VCRUNTIME140(_1).dll` and `api-ms-win-crt-*`. There is no NGX/DLSS DLL.
- **No other source file needed a change.** libktx is reached only through `Source/ImageLoader.cpp`.

### R2. Lines changed (`git diff --numstat v1.1.0 HEAD` on `phase1/no-ktx`)

| File | + | − |
|---|---|---|
| `CMakeLists.txt` | 7 | 26 |
| `Source/ImageLoader.cpp` | 51 | 56 |
| `Source/ImageLoader.h` | 2 | 2 |
| `Source/Ktx2Reader.cpp` (new) | 280 | 0 |
| `Source/Ktx2Reader.h` (new) | 77 | 0 |
| `Source/KTX/**` (deleted) | 0 | 62,746 across 73 files |
| `Source/Zstd/{zstd.c,zstd.h,LICENSE}` | moved verbatim from `Source/KTX/lib/basisu/zstd/` | |

The hand-written change is **about 360 new lines and about 60 changed lines**. It is split into three commits (not DCO-signed-off; sign-off trailers removed by the lead on 2026-11-27 because the DCO certification is reserved to the owner):

- `70e3a43` step 1: stub;
- `e400441` step 2: reader, zstd move, deletion of `Source/KTX`;
- `3f50942` step 3: hardening.

### R3. Effect of the stub at runtime (build-stub) [SRC]

The stub compiles but is not usable. `BlueNoise.cpp:60-64` throws `RG_ERROR_CANT_FIND_BLUE_NOISE` when `LoadLayered` fails. The blue-noise file is mandatory (`RgInstanceCreateInfo::pBlueNoiseFilePath`, `RTGL1.h:178`), so instance creation would fail. Every texture override would also silently fall back to the original texture (`TextureOverrides.cpp:131-142`). **A pure stub is therefore not an option. A reader is required.**

### R4. Differential test (prototype vs libktx, `difftest\run.log`)

```
bc7_256_mips                 libktx=0 mine=Success  vkFormat=145 256x256 L9 A1 F1 sc=0 images=9 dataSize=87408
bc7_256_mips_zstd            libktx=0 mine=Success  vkFormat=145 256x256 L9 A1 F1 sc=2 images=9 dataSize=87408
bc5_128x64_mips              libktx=0 mine=Success  vkFormat=141 128x64 L8 A1 F1 sc=0 images=8 dataSize=10960
bc1_100x60_npot              libktx=0 mine=Success  vkFormat=131 100x60 L7 A1 F1 sc=0 images=7 dataSize=4136
bc1_100x60_npot_zstd         libktx=0 mine=Success  vkFormat=131 100x60 L7 A1 F1 sc=2 images=7 dataSize=4160
rgba8srgb_64_mips            libktx=0 mine=Success  vkFormat=43 64x64 L7 A1 F1 sc=0 images=7 dataSize=21844
rgba8_array4                 libktx=0 mine=Success  vkFormat=37 32x32 L6 A4 F1 sc=0 images=24 dataSize=21840
rgba8_array4_zstd            libktx=0 mine=Success  vkFormat=37 32x32 L6 A4 F1 sc=2 images=24 dataSize=21840
rgba8_cube                   libktx=0 mine=Success  vkFormat=37 16x16 L5 A1 F6 sc=0 images=30 dataSize=8184
r8_17x9_1level               libktx=0 mine=Success  vkFormat=9 17x9 L1 A1 F1 sc=0 images=1 dataSize=153
...\Tools\BlueNoise_LDR_RGBA_128.ktx2 libktx=0 mine=Success  vkFormat=37 128x128 L1 A128 F1 sc=0 images=128 dataSize=8388608
fuzz: 34084 inputs, 13529 accepted, failures so far 0
RESULT: PASS
```

- **Uncompressed files.** Offsets, sizes, `dataSize` and bytes are identical to libktx for every image.
- **zstd files.** Image sizes and bytes are identical. Offsets differ by design: the prototype packs levels with 16-byte alignment.
- **Real file.** The one non-synthetic input, RTGL1's own `BlueNoise_LDR_RGBA_128.ktx2` (made with libktx by `Tools/GenerateBlueNoiseKTX2.cpp`), matches.
- **Fuzzing.** The fuzz run found no out-of-range claim. Writing the fuzz test led to hardening commit `3f50942`: level length must be a multiple of layers×faces, and inflated data is capped at 1 GiB.

Limitations of the test:

- An ASan build (`/fsanitize=address`) did not start (`0xC0000142`, DLL init failure). The fuzz run used `/RTC1 /GS` only and is **not** memory-safety proof.
- The KTX-Software CTS sample images were not available (`gh api …/tests/testimages/*` returned 404; they live in a separate repository).
- The synthetic files were written by our own spec-based writer. They are validated only because libktx accepts them.

### R5. DLSS / FSR / NRD switches

**v1.1.0 [SRC]:**

- `CMakeLists.txt:189` `option(RG_WITH_NVIDIA_DLSS … OFF)`. When it is ON, lines 247-262 read `$ENV{DLSS_SDK_PATH}` and link `nvsdk_ngx_d(.dbg).lib` or `libnvsdk_ngx.a`.
- `Source/DLSS.cpp:30-79` is compiled only under `#ifdef RG_USE_NVIDIA_DLSS`. Lines 493-521 are a stub that throws "RTGL1 was built without DLSS support".
- There is **no FSR2 and no NRD**. FSR 1 and CAS are compiled from MIT shader headers.

**hl1 [SRC]:**

- `CMakeLists.txt:133` DLSS OFF.
- `:135` **`RG_WITH_AMD_FSR2` ON by default**. It links the committed prebuilt `Source/FSR2/win32/ffx_fsr2_api{,_vk}_x64{,d}.lib`, FSR 2.1.2 (`ffx_fsr2.h:33-43`, commit `885e27e` "update to fsr2.1.2"). On non-Windows `:261` fails with a fatal error.
- `:134` `RG_WITH_IMGUI` ON (it also links GLFW into the DLL).
- No NRD or Streamline references were found (`git grep -E '\bNRD\b|sl\.h|streamline|nvngx'`).

**Measured [EXP]:**

- In all three builds `CMakeCache.txt` has `RG_WITH_NVIDIA_DLSS:BOOL=OFF`, and `build.ninja` has 0 matches for `RG_USE_NVIDIA_DLSS|nvsdk`.
- Negative test with `-DRG_WITH_NVIDIA_DLSS=ON` and no `DLSS_SDK_PATH`: configure fails with `CMake Error at CMakeLists.txt:244 … Can't find DLSS_SDK_PATH environment variable`. The existing script refuses DLSS without the SDK. That is not a policy guard: anyone with the SDK can switch it on.
- Guard prototype `check_rtgl1_build.py`:

  | Build | Result |
  |---|---|
  | baseline | `VIOLATION: 15 KTX-Software (Apache-2.0) objects compiled into the target`, `FAIL`, exit 1 |
  | stub | `PASS`, exit 0 |
  | reader | `PASS`, exit 0 |

### R6. Dependency inventory

Classes follow the FSF license list (fetched 2026-11-27) [DOC]:

- `#apache2`: Apache-2.0 is "not compatible with GPL version 2".
- `#Expat`, `#X11License`, `#ModifiedBSD`, `#FreeBSD`, `#ZLib`, `#boost`, `#PublicDomain`, `#Unlicense` and `#CC0`: "compatible with the GNU GPL".
- BSD-1-Clause is **not listed** by the FSF.

Labels used in the "GPL-2.0-only" column:

- **OK** = compatible.
- **✗** = incompatible.
- **?** = unclear.
- **sys** = relies on the GPLv2 §3 system-library exception, which is a hypothesis [ASM] that holds only while the component is *not shipped with* the executable.

#### R6a. RayTracedGL1 v1.1.0 (`b1eb3d8`) [SRC]

| Component | Location / how used | License evidence | SPDX | Compiled into DLL? | GPL-2.0-only |
|---|---|---|---|---|---|
| RTGL1 own code | `Source/*.cpp`, `Include/RTGL1/*` | `LICENSE` (MIT, © 2020 Sultim Tsyrendashiev). Per-file MIT headers, e.g. `Source/ImageLoader.cpp:1-19` | MIT | yes | OK |
| **KTX-Software (libktx subset)** | `Source/KTX/lib/{texture,texture1,texture2,hashlist,checkheader,swap,memstream,filestream,vkloader,vk_funcs}.c`, `dfdutils/{createdfd,interpretdfd,queries,vk2dfd}.c`; headers `include/ktx.h`, `include/ktxvulkan.h`, `other_include/KHR/khr_df.h`, `vkformat_enum.h`, `dfdutils/dfd.h`. `CMakeLists.txt:161-179,195,234,239-240`. Added in `ff792be` (2021-04-30, "minimized KTX-Software"). The **tree is byte-identical in hl1** (tree `04cc990`) | each file `SPDX-License-Identifier: Apache-2.0` (e.g. `texture2.c:5-6`). `Source/KTX/LICENSE.md`. `Source/KTX/LICENSES/Apache-2.0.txt`. `.reuse/dep5`. `NOTICE.md` | Apache-2.0 | **yes (15 objects)** | **✗** |
| KTX `uthash.h` | `Source/KTX/lib/uthash.h` (used by `hashlist.c`) | header `SPDX: BSD-1-Clause` | BSD-1-Clause | yes (header) | ? (permissive, but not on the FSF list) [ASM: likely compatible] |
| KTX `khrplatform.h` | `Source/KTX/other_include/KHR/` | MIT-style permission notice | MIT | yes (header) | OK |
| Zstandard 1.4.9 (single-file) | `Source/KTX/lib/basisu/zstd/zstd.c`, `zstd.h`; `other_include/zstd_errors.h` | `zstd.c:10-17` "licensed under both the BSD-style license … and the GPLv2 … You may select, at your option". `basisu/zstd/LICENSE` = BSD. **Conflict:** KTX `.reuse/dep5` blanket-labels `lib/basisu/*` Apache-2.0 (Binomial). [ASM] the file header governs | BSD-3-Clause OR GPL-2.0-only | yes | OK |
| KTX extra license texts | `Source/KTX/LICENSES/LicenseRef-{Cesium-Trademark-Terms,ETCSLA,HI-Trademark,Kodak,PNGSuite}.txt`, GPL-2.0-or-later, CC-BY-*, BSL-1.0 … | texts only. The files they cover (tests, `etcdec.cxx`) are **not in the tree** (`git ls-tree`) | n/a | no | n/a |
| Vulkan Memory Allocator 3.0.0-development | `Source/Vma/vk_mem_alloc.h`, `vk_mem_alloc_imp.cpp` | `Source/Vma/LICENSE.txt` (© 2017-2020 AMD, MIT). `vk_mem_alloc.h:28` version | MIT | yes | OK |
| robin_hood hashing | `Source/Hashmap/robin_hood.h` (`Containers.h:23`) | `Source/Hashmap/LICENSE` (MIT, © 2018-2021 Martin Ankerl) | MIT | yes | OK |
| AMD FidelityFX FSR 1 | `Source/Shaders/FSR/ffx_a.h`, `ffx_fsr1.h` (included by `SuperResolution.cpp:28-29` and by the shaders) | header "© 2021 AMD … Permission is hereby granted" | MIT | yes (C++ and SPIR-V) | OK |
| AMD FidelityFX CAS | `Source/Shaders/CAS/ffx_a.h`, `ffx_cas.h` (`Sharpening.cpp:29-30`) | header © 2017-2019 AMD, MIT text | MIT | yes | OK |
| NVIDIA DLSS / NGX | not in tree. `$ENV{DLSS_SDK_PATH}`, `CMakeLists.txt:243-263`, `DLSS.cpp:30-79` | NVIDIA RTX SDKs License (RD-007 §5.3) | LicenseRef-NVIDIA-RTX-SDK | **only if `RG_WITH_NVIDIA_DLSS=ON`** (default OFF) | **✗** (RD-007 Q3) |
| Vulkan headers | `find_package(Vulkan REQUIRED)` (`CMakeLists.txt:8`), from the SDK | `C:\VulkanSDK\1.4.363.0\Include\vulkan\vulkan_core.h:7` `SPDX-License-Identifier: Apache-2.0 OR MIT` | Apache-2.0 OR MIT | headers | OK (use the MIT option) |
| Vulkan loader | links `vulkan-1.lib` → `vulkan-1.dll` / `libvulkan.so.1` at runtime | KhronosGroup/Vulkan-Loader `LICENSE.txt`: "majority of files … Apache 2.0" [DOC] | Apache-2.0 | no (dynamic, from the OS/driver) | **sys**. Ships with GPU drivers and distros. **Never bundle `vulkan-1.dll`** with an SSTRE build [ASM] |
| MSVC runtime | `MSVCP140.dll`, `VCRUNTIME140*.dll`, UCRT (`dumpbin`) | Microsoft redistributable terms | proprietary | no (dynamic) | **sys** as the compiler's runtime. Shipping the redistributable beside the exe weakens this [ASM, counsel] |
| Blue-noise data | `Tools/BlueNoise_LDR_RGBA_128.ktx2` (data, loaded at runtime) | covered by the RTGL1 MIT LICENSE. Built from `C:\Git\BlueNoiseGen\Data\128_KTX\LDR_RGBA_<i>_png…` (`GenerateBlueNoiseKTX2.cpp:11`). [ASM] the source is Christoph Peters' free blue-noise set (CC0), not verified | MIT (?) | no (data) | OK [ASM] |
| Build-time only | `Tools/CreateKTX2.py` (MIT, needs Compressonator CLI), `Tools/GenerateBlueNoiseKTX2.cpp` (uses libktx, not built), `Source/Generated/GenerateShaderCommon.py`, `Source/Shaders/GenerateShaders.py` (MIT, call `glslc`) | — | — | no | not linked |
| Test submodules | `Tests/Libs/glfw` @ `3327050` (2020-11-17), `Tests/Libs/glm` @ `1cf91a1` (2020-11-21). `.gitmodules`. Only with `RG_WITH_EXAMPLES` (default OFF, `:191`) | GitHub metadata: glfw Zlib. glm NOASSERTION (Happy Bunny / MIT) | Zlib; MIT | no | OK (tests only) |

#### R6b. RayTracedGL1 `hl1` HEAD (`2457acc`): differences from v1.1.0 [SRC]

| Component | Location | License evidence | SPDX | In DLL? | GPL-2.0-only |
|---|---|---|---|---|---|
| KTX-Software | identical tree, identical `KTXSources` (`CMakeLists.txt:105-123`). Used only by `Source/ImageLoader.cpp:23-150` (same 8 API calls) | as above | Apache-2.0 | **yes** | **✗** |
| VMA 3.1.0-development | `Source/Vma/` (`vk_mem_alloc.h:28`) | MIT | MIT | yes | OK |
| stb_image v2.27 / stb_image_write | `Source/Stb/*.{h,cpp}` (Developer-mode PNG/TGA loading) | `Source/Stb/LICENSE.txt` (MIT © 2017 Sean Barrett, or public domain) | MIT OR Unlicense | yes | OK |
| Dear ImGui (docking) | submodule `Source/imgui` @ `375ae5d` (2022-10-24). `RG_WITH_IMGUI` **ON** (`:134,179-204`) | GitHub: MIT | MIT | yes (static lib) | OK |
| GLFW | submodule `Source/glfw` @ `dd8a678` (2022-09-20), linked into the DLL when ImGui is ON (`:201,269`) | GitHub: Zlib | Zlib | yes | OK |
| cgltf (sultim-t fork) | submodule `Source/cgltf` @ `f9567ab` (2023-01-07) | GitHub: MIT | MIT | yes | OK |
| glaze | submodule `Source/glaze` @ `bdbc8cf` (2022-12-23), `add_subdirectory` (`:274-275`), always on | GitHub: MIT | MIT | yes (header-only) | OK |
| **AMD FSR 2.1.2 prebuilt** | `Source/FSR2/include/**` (headers) + **`Source/FSR2/win32/ffx_fsr2_api{,_vk}_x64{,d}.lib`** (committed binaries). `RG_WITH_AMD_FSR2` **ON** (`:135,248-263`) | header `ffx_fsr2.h` © 2022 AMD, MIT text | MIT | yes (static blobs) | OK by license, but there is **no corresponding source in the tree** (RD-007 Q9). Build FSR2 from pinned source, or keep it OFF |
| AMD LPM | `Source/Shaders/LPM/ffx_a.h`, `ffx_lpm.h` | © 2017-2019 AMD, MIT text | MIT | yes (shaders) | OK |
| tinygltf | `Tests/Libs/tinygltf/` (tests only) | `LICENSE` MIT © 2017 Syoyo Fujita et al. | MIT | no | OK |
| CI | `.github/workflows/build-windows.yml` | — | — | — | n/a |

#### R6c. Engine-side runtime dependencies [SRC]

| Dependency | Classic-VK `510d36f` | SE-RT `0e7f223` | License evidence | SPDX | GPL-2.0-only |
|---|---|---|---|---|---|
| Engine code | GPL-2.0-only | GPL-2.0-only | RD-007 §3.1 | GPL-2.0-only | — |
| SDL2 | `find_package(SDL2)` with `USE_SYSTEM_SDL2` ON by default (`SamTFE/Sources/CMakeLists.txt:12,48-57`); otherwise vendored headers `SamT?E/Sources/External/SDL2/` (SDL 2.0.x, `SDL_version.h`) | Zlib headers. GitHub libsdl-org/SDL: Zlib | Zlib | OK |
| `SDL_vulkan.h` copy | `Engine/Graphics/SDL/SDL_vulkan.h` (© 2017 Mark Callow, Zlib text) | — | Zlib | Zlib | OK |
| zlib | system (`USE_SYSTEM_ZLIB` ON, `:13,60-68`) or vendored 1.1.3 `Engine/zlib/` (`zlib.h:40`) | vendored 1.1.3 `Sources/Engine/zlib` | Zlib | Zlib | OK (1.1.3 is a security concern, not a license one) |
| libogg 1.3.2 / libvorbis 1.3.5-pre | vendored `External/libogg`, `External/libvorbis` (`COPYING` © Xiph). On Linux `libvorbisfile.so` is loaded at runtime (`Base/Unix/UnixDynamicLoader.cpp:36-118`) | vendored `Sources/libogg`, `Sources/libvorbis`. Linked as `libogg.lib;libvorbis.lib` | BSD-3 (Xiph) | BSD-3-Clause | OK (notice required) |
| Tremor | optional, `USE_TREMOR` OFF (`:607`) | — | Xiph BSD | BSD-3-Clause | OK |
| amp11lib | `Sources/amp11lib/` (headers GPL-2.0-only, `COPYING` = LGPL-2.0 text) | — | RD-007 §3.3 | GPL-2.0-only / LGPL-2.0 | OK |
| VMA 3.3.0 | `Engine/Graphics/Vulkan/vk_mem_alloc.h` (© 2017-2025 AMD, MIT) | via RTGL1 | MIT | MIT | OK |
| Vulkan headers / loader | `find_package(Vulkan)`, `USE_SYSTEM_VULKAN` ON (`:14,83-90`) | `vulkan-1.lib` (`Engine.vcxproj` AdditionalDependencies) | Apache-2.0 OR MIT / Apache-2.0 | — | headers OK. Loader **sys** (do not bundle) |
| RTGL1 | — | `RayTracedGL1.lib` import lib + DLL copy (`Engine.vcxproj:224-257`) | see R6a | MIT + **Apache-2.0 (KTX)** | **✗ until KTX is removed** |
| Windows system libs | — | `DbgHelp.lib`, `kernel32` … `odbc32`; `htmlhelp.lib` (editor/tools projects only) | Microsoft | proprietary | **sys** (OS). `htmlhelp.lib` affects tools only. Keep it out of shipped runtime targets [ASM] |
| ImageMagick | build-time `find_package(ImageMagick COMPONENTS convert)` only for system installs (`:244`) | — | — | — | not linked |
| `Bison.exe` / `Flex.exe` | committed (`SamT?E/Tools.Win32/`) | committed (`Tools.Win32/`) | RD-007 §3.3 | GPL tools | not linked. Do not run or ship them (brief) |
| KTX | **none** (`git grep -l -i ktx` hits only `.gro`/`.tex` binaries) | only filenames `.ktx2` (`SSRT.cpp:316-319`, `TextureUploader.cpp:33`) | — | — | n/a |

## Deviations, modifications and failures

- **Modifications.** These are on the throwaway branch `phase1/no-ktx` only. The commits are listed in R2 and carry Co-Authored-By (no DCO sign-off). Patch descriptions:
  - **Step 1** (`70e3a43`): delete `KTXSources`, `-DKHRONOS_STATIC -DLIBKTX` and the KTX include dirs from `CMakeLists.txt`. `ImageLoader::Load` / `LoadLayered` return `false`.
  - **Step 2** (`e400441`):
    - add `Source/Ktx2Reader.{h,cpp}`;
    - `ImageLoader` keeps the same `ResultInfo` / `LayeredResultInfo` contract (contiguous `pData`, level offsets relative to it);
    - `git mv` the zstd files to `Source/Zstd/`;
    - `git rm -r Source/KTX`;
    - CMake adds the 2 sources, `Source/Zstd` and `KTX2R_WITH_ZSTD`.
  - **Step 3** (`3f50942`): two validation checks.
- **Side effect on the upstream clone.** The prescribed `git worktree add` created the branch `phase1/no-ktx` and the worktree metadata inside the read-only clone's `.git`. No upstream file or branch was changed. Removing it later takes `git worktree remove` plus `git branch -D phase1/no-ktx`.
- **Failures:**
  - ASan build of the difftest did not start (`0xC0000142`), so a non-ASan build was used instead.
  - KTX CTS sample images could not be fetched (404).
  - The first difftest compile failed (`ktxvulkan.h(65): error C3646`; `<vulkan/vulkan.h>` must come first), and was fixed.
  - The stub is not viable at runtime (R3).
- **Clean-room caveat (honest record).** The reader was written from the KTX 2.0 container layout (header, level index, level order, Zstandard per level). While doing this audit the author also read RTGL1's libktx *call sites* and a short section of libktx `texture2.c` (`LoadImageData` / zstd inflation, lines 2100-2160). The design does not follow libktx: there is no vtable, no stream abstraction and no DFD handling. It is still **not** a documented clean-room implementation. If the owner wants strict clean-room provenance, someone who has not read libktx should reimplement the reader from the spec alone. About 300 lines; [ASM] 1-2 days.
- **Not done:** no runtime rendering test (it needs SE-RT + RTGL1 integration and a scene), no Linux build, no `reuse lint` / ScanCode run.

## Interpretation ([SRC]/[DOC]/[ASM] clearly labelled)

### What libktx is actually used for [SRC]

In both v1.1.0 and hl1, libktx is called only from `Source/ImageLoader.cpp`. The v1.1.0 call sites are:

| API | v1.1.0 line |
|---|---|
| `ktxTexture_CreateFromMemory` | `:52` |
| `ktxTexture_CreateFromNamedFile` | `:60` |
| `ktxTexture_GetVkFormat` | `:96`, `:150` |
| `ktxTexture_GetData` | `:97`, `:155` |
| `ktxTexture_GetDataSize` | `:98`, `:151` |
| `ktxTexture_GetImageOffset` | `:108`, `:160` |
| `ktxTexture_GetImageSize` | `:110` |
| `ktxTexture_Destroy` | `:180` |

There are four callers:

| Caller | What it loads |
|---|---|
| `TextureOverrides.cpp:114`, via `TextureManager.cpp:247` | material overrides (`<name>`, `_rme`, `_n` `.ktx2`) |
| `TextureManager.cpp:145` | path-loaded textures, e.g. SE-RT's `WaterNormal_n.ktx2` |
| `CubemapManager.cpp:139-144` | cubemap face overrides |
| `BlueNoise.cpp:60` | mandatory 128-layer RGBA8 array |

**Features actually needed:** KTX2 header + level index, a 2D image with ≤20 pre-generated mips (`Const.h:42`), array layers (blue noise only), and the `vkFormat` from the header. The data is uploaded as-is.

**Features linked but not used:**

- the `vkloader.c` Vulkan upload path (only `GetVkFormat` is used from it);
- KTX1 (`texture1.c`), although `TextureOverrides.cpp:261-262` forces `.ktx2`;
- DFD interpretation;
- Zstandard. It is *linked*, and libktx inflates it on load (`texture2.c:2117-2150`), but RTGL1's own tool `CreateKTX2.py` writes BC7/BC5 through Compressonator without supercompression.

**Basis Universal transcoding is not compiled in at all** (RD-005 §3.2). Basis files would fail to load under libktx too.

### Options for the runtime texture format

All effort figures are [ASM]. None of these options needs libktx in the runtime. AssetCompiler (GPL-3.0-only, separate process) may use libktx, Compressonator, basisu or DirectXTex freely, because Apache-2.0 is GPLv3-compatible (FSF `#apache2` [DOC]). The process/file boundary is ADR-0006 rule 2.

| Option | What changes | Effort / LOC | Licensing risk | Technical risk | Compatibility |
|---|---|---|---|---|---|
| **(a) Own minimal KTX2 container reader** in the runtime (prototype done) | only `ImageLoader.cpp`. File names stay `.ktx2` | measured: ~360 new + ~60 changed lines, compiles, matches libktx (R1, R2, R4). [ASM] 2-4 days to production: strict review, a Linux build, CTS images, runtime test | low. Own code (MIT or GPL-2.0-only, owner's choice). zstd optional (BSD/GPLv2 dual). The KTX spec licence (`license.adoc`, KhronosGroup/KTX-Specification @ `ac39917`) grants copyright use but **no patent licence** outside the Khronos Adopter programme [DOC]. [ASM] low risk for a plain container | low. Only the subset needed. Rejects Basis/KTX1/3D | **keeps the RTGL1 and SE-RT file contract** (`SSRT.cpp:316-319`), upstream tools (CreateKTX2.py, `toktx`, `ktx create`) and the hl1 contract (same ImageLoader). The same reader can serve a Classic-VK raster HD path |
| (b) DDS (BCn) with a permissive or own loader | `ImageLoader` + override extension (`TextureOverrides.cpp:262`) + SE-RT paths (`SSRT.cpp:316-319`, `TextureUploader.cpp:33`) + the blue-noise file | [ASM] 300-500 lines (DX10 header + DXGI→VkFormat table) or vendor a reader; more fork divergence | low with an MIT/BSD reader. Candidates [DOC, GitHub metadata 2026-11-27]: **microsoft/DirectXTex** (MIT; `DDSTextureLoader` is D3D-bound, the DDS parsing is reusable), **septag/dds-ktx** (BSD-2-Clause, v1.1 tag `d961cf6`, master `5560d77`; DDS + **KTX1 only**, no KTX2), **benikabocha/tinyddsloader** (MIT, last push 2019), **spnda/dds_image** (MIT) | medium. Legacy FourCC ambiguity; sRGB only via DX10 DXGI formats | diverges from RTGL1/SE-RT upstream and from hl1. Wider tool support on Windows |
| (b′) Vendor a permissive KTX2 reader | as (a) | small | **bkaradzic/bimg** (BSD-2-Clause, master `38ceda5` 2026-11-21) parses KTX2 (`src/image.cpp:4887ff`) but **rejects supercompression** (`:5254-5256`) and pulls in `bx`. Zlib/BSD alternatives with KTX2: **none found.** DeanoC/tiny_ktx (MIT, 2019) is KTX1 only | low license risk, extra dependency weight | as (a) |
| (c) Extended SE1-native container (`.tex` + PBR chunks) | engine `.tex` loader, RTGL1 upload path, AssetCompiler writer | [ASM] highest: weeks | the format is engine-defined. GPLv3 tools need a clean-room spec or a GPL-2.0 helper (ADR-0006 rule 2) | high | no external tools at all |
| **(d) AssetCompiler does all encoding; runtime reads raw BCn** | AssetCompiler writes BC1/BC3/BC4/BC5/BC7 (+ RGBA8) KTX2 with `supercompressionScheme` 0 (or 2) and **never Basis/UASTC** | complements (a) or (b). Writer work is in AssetCompiler | none in the runtime. Apache-2.0 tools are allowed in GPLv3 [DOC] | low | an AssetCompiler conformance test can run the runtime reader as a separate GPL-2.0 CLI, or the reader if MIT |

**Recommendation [ASM, owner decision]: (a) + (d).**

- Keep KTX2 as the runtime interchange format.
- Delete `Source/KTX` from the SSTRE fork of RTGL1, replace it with a small reviewed KTX2 container reader, and keep zstd as an optional BSD/GPLv2 dependency.
- Let AssetCompiler (GPL-3.0-only) do all encoding, mip generation and any libktx/Basis work, and emit only pre-encoded BCn/RGBA8.

The reasons:

- It is the smallest change (R2), and it is measured.
- It keeps both RTGL1 API generations and SE-RT's file paths unchanged.
- It gives the same loader to the mandatory raster baseline.

Fall back to (b) only if the patent wording of the KTX spec licence worries counsel.

### Remaining GPL-2.0 issues after KTX removal [ASM]

- **Vulkan loader (Apache-2.0).** It is acceptable only as a system library. Never bundle `vulkan-1.dll` / `libvulkan.so`.
- **MSVC runtime.** Prefer to tell users to install the VC++ redistributable rather than bundling it. Counsel should decide.
- **hl1: FSR2 prebuilt blobs.** These are a corresponding-source gap. Build FSR2 2.1.2 from GPUOpen source or set `RG_WITH_AMD_FSR2=OFF` (and FSR2 is Windows-only there).
- **DLSS.** It stays excluded from distributed builds (ADR-0006 rule 5).
- **`uthash.h` (BSD-1-Clause).** Not on the FSF list. Its removal comes with `Source/KTX`, so the question disappears.

### Proposed build guard (E4) [ASM]

1. **CMake.** The SSTRE-Engine wrapper `CMakeLists.txt` defines `SSTRE_DISTRIBUTABLE` (default ON in CI release jobs). It fails at configure if `RG_WITH_NVIDIA_DLSS` is ON, `DEFINED ENV{DLSS_SDK_PATH}`, `RG_WITH_AMD_FSR2` is ON (until FSR2 is built from source), or `EXISTS ${RTGL1}/Source/KTX`.
2. **Post-build CI step.** Run `check_rtgl1_build.py <build>` (prototype, R5). It checks the CMake cache options, `build.ninja` for `nvsdk_ngx|DLSS_SDK_PATH|NRD|sl.interposer|ffx_fsr2_api*.lib|Source/KTX/*.obj`, and a byte scan of the DLLs for `nvngx`. Add `dumpbin /dependents` / `readelf -d` allow-lists (`vulkan-1`, CRT, system libraries only).
3. **REUSE / ScanCode on the shipped source set.** Fail on any `Apache-2.0`-only or `LicenseRef-NVIDIA*` file in a GPL-2.0 runtime target.
4. **Release packaging.** Refuse to package `nvngx_*.dll`, `vulkan-1.dll` or `ffx_fsr2_api*`.

## Impact on ADRs, dossiers and backlog

- **ADR-0006 "KTX in the runtime".** The candidate approach is technically confirmed at compile and parse level. Proposed wording: "the runtime reads KTX2 (supercompression none or Zstandard, pre-encoded formats only) through an SSTRE-owned reader. KTX-Software is used only in AssetCompiler."
- **RD-007:**
  - §3.5 can now cite exact files and lines.
  - The note that zstd is labelled Apache-2.0 by KTX `dep5` but is BSD/GPLv2 dual by its header should be added.
  - The Vulkan loader (Apache-2.0, system library) should be added to §5.
  - Q1 narrows to: "is an own KTX2 reader plus a system Vulkan loader acceptable", plus the KTX spec patent wording.
- **RD-005 §3.2.** libktx is confirmed as the only consumer, through `ImageLoader.cpp`, and hl1 has the same KTX tree.
- **Backlog.** Proposed new items:
  - "productionize the KTX2 reader + CTS images + runtime test on SE-RT";
  - "FSR2 from source or OFF";
  - "CI distributable guard (E4)";
  - "AssetCompiler KTX2 writer profile: BCn/RGBA8, sc 0/2, no Basis".

## Open questions

1. **Owner:** license of the new reader. MIT keeps it reusable in AssetCompiler and upstreamable to RTGL1. GPL-2.0-only is the alternative. Do we need a strict clean-room re-write (see the caveat above)?
2. **Owner:** allow Zstandard supercompression in runtime files (a smaller disk footprint for about 38.7k lines of BSD/GPLv2 zstd), or require scheme 0 only, which drops zstd from the runtime entirely?
3. **Counsel:** does the "no patent licence except for Adopters" wording of the KTX spec licence matter for an open-source reader? Is the Vulkan loader / MSVC runtime system-library reasoning acceptable?
4. **Technical:** runtime validation with SE-RT + RTGL1 v1.1.0 on real overrides (BC7/BC5 from Compressonator) and with the hl1 API, plus a Linux build.
5. **Provenance:** is the blue-noise source data CC0 (Christoph Peters)? This is unverified.
