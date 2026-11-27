# EXP-014: Clean-room KTX2 reader for RayTracedGL1 v1.1.0 (libktx removal)

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | Sprint 2 track K: replace the Apache-2.0 libktx in the GPL-2.0-only runtime (Phase 1 owner decision "remove Apache-2.0 KTX code from the GPLv2 runtime"); feeds track E1 (engine integration and render test) |
| Status | complete. Reader, tests, fuzzing and the RTGL1 build are done. The render test belongs to track E1 |
| Environment | Windows 11 Pro 22631; VS 2022 17.5 (MSVC 14.35.32215, x64 dev prompt); CMake 4.4.4; Ninja 1.13.2; Vulkan SDK 1.4.363.0; Python 3.10. Sanitizer runs: Docker image built `FROM ubuntu@sha256:b000e69a50ff940390233025e7a337fb8469b509e2334fa4d018ac30f3e18cdb` plus `g++` 11.4.0 (local tag `sstre-ktx-asan:local`, id `sha256:01787a8e…`), run with `--network none` |
| Inputs | RTGL1 `phase1/rtgl1-v1.1.0-sdk1.4` @ `4bcf13e` (= `v1.1.0` + one shader commit); KTX-Specification @ `ac39917e`; zstd v1.5.7 release; KTX-Software v4.4.2 Windows x64 release binaries (used only as an oracle) |
| Branch | RTGL1 clone `upstream/sultim-t_RayTracedGL1`, branch `sprint2/ktx2-cleanroom` (worktree `G:\sstre-tmp\ktx\wt-rtgl1`), not pushed |

## Clean-room declaration

The reader was written on 2026-11-27 by the track K agent, from the sources below only.

**Sources consulted**

| Source | Version | Licence / terms | Used for |
|---|---|---|---|
| Khronos *KTX File Format Specification* 2.0, `ktxspec.adoc` (+ `formats.json`) | github.com/KhronosGroup/KTX-Specification, commit `ac39917e8240f51db97715a2453134a42ff959fd` (2026-07-09, "Document Revision 5 (draft)" of KTX 2.0); published version at registry.khronos.org/KTX/specs/2.0/ktxspec.v2.html | Khronos specification copyright licence (`license.adoc`): conditional licence to use and reproduce the unmodified spec, with no patent or trademark licence. Implementing the format is the spec's purpose. No spec text is copied into the code; only section names are cited | file layout, field rules, texture types, level order and sizes, `mipPadding`, supercompression schemes, key/value layout, prohibited formats; block dimensions and typeSize from `formats.json` |
| RFC 8878 (Zstandard) and the zstd public API (`zstd.h` of v1.5.7) | RFC 8878; zstd v1.5.7 | RFC / BSD-3-Clause OR GPL-2.0 | `ZSTD_decompressDCtx` semantics; hand-built raw-block, skippable and multi-frame test data |
| Vulkan SDK headers `vulkan_core.h` | 1.4.363.0 | Apache-2.0 OR MIT (headers; only numeric enum values are used) | numeric `VkFormat` values for the generated format table |
| RTGL1, outside libktx: `Source/ImageLoader.{h,cpp}` and its callers `BlueNoise.cpp`, `TextureManager.cpp`, `TextureOverrides.cpp`, `CubemapManager.cpp`, `TextureUploader.cpp`, plus `CMakeLists.txt`, `Tools/CreateKTX2.py`, `Tools/GenerateBlueNoiseKTX2.cpp` (call sites only) | `4bcf13e` | MIT | what the loader must return. Only the *names* of the libktx functions at the call sites were read |
| KTX-Software `ktx` CLI v4.4.2 (`create`, `info --format json`, `extract --raw`, `validate`) and its `--help` text | release asset `KTX-Software-4.4.2-Windows-x64.exe`, SHA-256 `1f323b0f…d2957fe` (matches the GitHub release digest), unpacked with 7-Zip into `G:\sstre-tmp\ktx\tools\ktxsw-4.4.2` without installing | Apache-2.0 (binary used as a tool, not distributed or linked) | black-box oracle: creates the corpus, reports the level index, extracts images |

**Sources deliberately not consulted**

- libktx / KTX-Software implementation: `Source/KTX/**` in RTGL1 (not opened, grepped or diffed; it was deleted unread in `d509ff3`), the KTX-Software source tree, and the headers in the unpacked release (`include/ktx.h`, `ktxvulkan.h`, `KHR/`), which are present but were never opened.
- The zstd copy bundled at `Source/KTX/lib/basisu/zstd/` lies inside the forbidden path, so its licence header was **not** read. Instead zstd was taken from the official upstream release, whose headers say BSD-3-Clause OR GPL-2.0 (see below).
- The Phase 1 reader on branch `phase1/no-ktx`, everything under `L:\claude-ws\SSTRE\local-work\deps\` (including its compiled test harness), and EXP-003 (not opened at all, not even its dependency table).
- Searches were limited to the RTGL1 files named above. The only directory listing that touched `Source/KTX` was a top-level `ls` of `Source/` and `Source/KTX/`, which shows file names only.

## Goal and success criteria

1. A C++17 KTX2 reader under GPL-2.0-only that gives `ImageLoader` everything it needs. The only new dependency allowed is zstd.
2. Robust against hostile input: every header field, offset and length is checked against the file size, level order is checked, supercompression none and zstd are supported, as are layers, faces and levels. vkFormat is passed through for BCn and RGBA8.
3. Byte-exact agreement with the official tool on a corpus covering BC1/BC3/BC5/BC7, RGBA8, mips, arrays, cubemaps, zstd and none, and odd sizes, plus RTGL1's shipped `.ktx2`.
4. RTGL1 builds with 0 libktx objects.

## Implementation

| Commit (`sprint2/ktx2-cleanroom`) | Content |
|---|---|
| `fbaf42ec77905f20d04c496c7f5e20f2d4e2f98b` | `Source/Ktx2Reader.{h,cpp}`, generated `Source/Ktx2FormatTable.inl` (206 formats), generator `Tools/GenKtx2FormatTable.py` |
| `2821e093149af4e68db75067831faebd138436ff` | `Source/zstd/`: zstd 1.5.7 single-file *decompressor* `zstddeclib.c` plus `zstd.h`, `zstd_errors.h`, `LICENSE`, `COPYING`, `VENDORED.txt` (provenance) |
| `f1b07270f4144d72cdf73389a1a1fb375477f74b` | `ImageLoader` switched to `Ktx2Reader`; CMake: 15 `Source/KTX` sources, `-DKHRONOS_STATIC -DLIBKTX` and the KTX include dirs removed |
| `493bb9e09bd860ddb419d7cdfe2d05c951e5a17f` | `Tests/Ktx2Reader/`: self-tests, `info`/`extract` for the oracle comparison, fuzz loop, `corpus_compare.py`, standalone CMake |
| `d509ff35f71efac2b4f1ba2b0af8bb9cbae463f0` | removes the `Source/KTX` directory (73 files), as a separate commit |
| `0eb4c4acda28399a0b35e6fa8a62fb23bf502394` | `VENDORED.txt`: records the checksum of the committed LF file (see Deviations) |

All commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. None has a `Signed-off-by` trailer. New files carry `SPDX-License-Identifier: GPL-2.0-only` and `Copyright (C) 2026 Handelsonderneming S.D. Broekhoven, trading as ITEagle Europe`. The modified `ImageLoader.{h,cpp}` and `CMakeLists.txt` keep their MIT notices.

**Validation done by `Ktx2::Read`** [SRC `Source/Ktx2Reader.cpp` @ `fbaf42e`]:
- The file must be at least header + index + one level entry (104 bytes), and the identifier must match.
- Supercompression: 0 and 2 are accepted. 1 (BasisLZ), 3 (ZLIB), vendor and reserved schemes return `ErrorUnsupportedSupercompression`.
- vkFormat must appear in the table. That excludes `VK_FORMAT_UNDEFINED` (Basis/UASTC), the prohibited `*SCALED*` and multi-planar formats, PVRTC, and unknown values. The value is passed through unchanged.
- Texture type rules from the "Texture Type" table: width > 0; 1D has no depth; block-compressed formats need height > 0; faceCount is 1 or 6; cubemaps are square with depth 0. Configurable limits (default 65536 per dimension, 65536 layers, 1 GiB of inflated data) are checked before any allocation.
- `levelCount` must not exceed `floor(log2(max dim)) + 1`. A value of 0 means one stored level.
- The level index must fit in the file. DFD: length ≥ 4, inside the file, `dfdTotalSize == dfdByteLength`. KVD: inside the file; every entry has length > 0, fits, and has a non-empty NUL-terminated key. SGD length must be 0 for schemes 0 and 2. Header, index, DFD and KVD must not overlap.
- Each level:
  - length > 0, and its range lies inside the file and after all metadata;
  - `uncompressedByteLength` equals the size computed from format, dimensions, layers and faces (overflow-checked);
  - for scheme 0, `byteLength == uncompressedByteLength`;
  - level p+1 must end at or before the start of level p (smallest level first, no overlap).
- Zstd inflation uses `ZSTD_decompressDCtx` into a buffer of exactly the expected size. Checksums are verified when present, and skippable or multiple frames are accepted. Any error or short output returns `ErrorDecompression`, so a decompression bomb cannot grow past the declared size.
- On any error the output `Texture` is left empty. `ResultToString` gives one message per error code.

**Deliberately lenient** [SRC]: `typeSize` (needed only for big-endian hosts), the alignment and padding of the metadata sections, the level `mipPadding` alignment in the file (the reader copies the data anyway), `kvdByteOffset`/`sgdByteOffset` when their length is 0, and DFD contents (not interpreted). These rules do not affect memory safety, and enforcing them could reject files that third-party writers produce.

**Output layout**: inflated levels are stored base level first, each starting at a multiple of lcm(texel block size, 4). Images are addressed in the spec order layer → face → z-slice (`GetImageOffset`).

**ImageLoader contract** [SRC `Source/ImageLoader.cpp` @ `f1b0727`]:
- `Load` fills `pData`/`dataSize` (the whole inflated buffer, including alignment padding), `levelOffsets[]`/`levelSizes[]` (one image per level), `baseSize`, `format = vkFormat`, `isPregenerated = true` and `levelCount = min(levels, 20)`. This matches how the data is consumed: `TextureUploader` copies `dataSize` bytes into staging and then uses the per-level offsets [SRC `TextureUploader.cpp:194`, `:457` @ `4bcf13e`], so the layout of the buffer does not matter.
- `LoadLayered` returns one pointer per layer of level 0, which is what `BlueNoise.cpp:60-99` uses.

Behaviour differences from the libktx version:
1. `Load` returns `false` for non-2D, array or cubemap files; before, this was only asserted.
2. `LoadLayered.dataSize` is now the size of level 0. Its only caller does not read it.
3. Inflated data is capped at 4 GiB, to fit the `uint32_t` fields.
4. For `levelCount == 0`, 1 level is reported with `isPregenerated = true`. [ASM] libktx also reports 1 level here, but that was not checked against libktx.

## Procedure (exact, reproducible)

1. Worktrees: `git -C L:\claude-ws\SSTRE\upstream\sultim-t_RayTracedGL1 worktree add G:\sstre-tmp\ktx\wt-rtgl1 -b sprint2/ktx2-cleanroom phase1/rtgl1-v1.1.0-sdk1.4` and `git -C L:\claude-ws\SSTRE\repos\SSTRE worktree add G:\sstre-tmp\ktx\wt-umbrella -b sprint2/exp-014 main`.
2. Spec: `git clone --depth 1 https://github.com/KhronosGroup/KTX-Specification.git G:\sstre-tmp\ktx\spec` gave HEAD `ac39917e`.
3. zstd: download `zstd-1.5.7.tar.gz` and check its SHA-256 `eb33e51f49a15e023950cd7825ca74a4a2b43db8354825ac24fc1b7ee09e6fa3` against the release `.sha256`. Then `python -I combine.py -r ../../lib -x legacy/zstd_legacy.h -o zstddeclib.c zstddeclib-in.c`.
4. Format table: `python -I Tools/GenKtx2FormatTable.py <spec>/formats.json C:\VulkanSDK\1.4.363.0\Include\vulkan\vulkan_core.h Source/Ktx2FormatTable.inl` reported "wrote 206 formats".
5. Tests (MSVC Release): `cmake -S Tests/Ktx2Reader -B G:\sstre-tmp\ktx\build-tests-rel -G Ninja -DCMAKE_BUILD_TYPE=Release`, then `Ktx2ReaderTest selftest`.
6. Tests with ASan and UBSan (Linux container): `gcc/g++ -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=undefined` (script `G:\sstre-tmp\ktx\scripts\linux-build.sh`), then `selftest` and `fuzz 10000000 <seed> /corpus/*.ktx2` for seeds 101, 202 and 303.
7. Oracle comparison: `python -I Tests/Ktx2Reader/corpus_compare.py <ktx.exe> <Ktx2ReaderTest.exe> G:\sstre-tmp\ktx\cmp <extra files>`. The script creates the corpus with `ktx create --raw … --testrun` from seeded random block data (seed 20261127), plus one PNG with `--generate-mipmap --zstd 12` and one `--zlib 6` file. For every file it compares `ktx validate`, the `ktx info --format json` header and level index (byteOffset, byteLength, uncompressedByteLength), and the bytes of every image from `ktx extract --all --raw`, against `Ktx2ReaderTest info`/`extract`.
8. RTGL1: in the VS 2022 x64 dev prompt with `VULKAN_SDK=C:\VulkanSDK\1.4.363.0`, run `cmake -S G:\sstre-tmp\ktx\wt-rtgl1 -B G:\sstre-tmp\ktx\build-rtgl1 -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DRG_WITH_SURFACE_WIN32=ON -DRG_WITH_NVIDIA_DLSS=OFF -DRG_WITH_EXAMPLES=OFF`, then `cmake --build` (script `G:\sstre-tmp\ktx\scripts\build-rtgl1.bat`). This was a clean build at `0eb4c4a`, with `Source/KTX` already deleted.

## Results ([EXP], 2026-11-27)

| Item | Result |
|---|---|
| Self-tests | **176/176 pass**, both with MSVC Release and with g++ 11.4 ASan+UBSan (0 sanitizer reports). Valid cases: 2D, 13×7, RGB8 5×3 (mipPadding with lcm 12), BC1 10×6, BC7 array, BC3 cube, BC3 cube array, 3D, 1D, levelCount 0, no KVD, zstd (raw blocks, skippable+raw, two frames, multi-block > 128 KiB). Each case checks level bytes, header passthrough, KTXwriter KV and invariants. Error cases: truncation at 4 points, identifier, 5 bad vkFormats, 5 bad schemes, dimensions, faceCount, non-square cube, limits, levelCount, DFD/KVD/SGD faults, level length 0, huge offset/length (overflow), level overlapping the header, level order, size mismatch, zstd bad magic, FCS too large or small, truncated frame, size limit |
| Oracle corpus (official tool) | **34 files, 531 images: 33 MATCH, 1 REJECT-OK, 0 mismatches**. 28 raw-created files: RGBA8 (mips, 13×7 sRGB, 1×1, 5-layer array, cube, 3D 8×8×4, 1D), RGB8 5×3, R8 7×5, RGBA16F, runtime-mipmap (levelCount 0), BC1 64×32, BC1A sRGB 10×6, BC3 128, BC3 cube, BC3 cube array, BC5 4-layer array, BC5 SNORM 18×9, BC7 256, BC7 sRGB, BC7 1000×3 (10 levels), BC7 2048 without mips. 10 of the 28 files are zstd (levels 1–22). Also: PNG with tool-generated mips + zstd; ZLIB file (correctly rejected as an unsupported scheme); RTGL1 `Tools/BlueNoise_LDR_RGBA_128.ktx2`; 3 Compressonator 4.6.0 BC7/BC5 files from EXP-002 (local only, not published). `ktx validate` passed for all 34. Header fields, level index and every image's bytes are identical |
| RTGL1 blue noise (inspected with the reader) | R8G8B8A8_UNORM (37), 128×128, `layerCount` 128, 1 level, scheme 0, level at offset 256, 8 388 608 bytes, KV key `KTXwriter`, 128 images match the tool's extraction |
| Fuzzing, ASan+UBSan (Linux) | **30 000 000 iterations** (3 × 10 M, seeds 101/202/303, 32 seeds: 29 corpus files + 3 synthetic zstd), 408.5 s in total. **0 ASan/UBSan reports, 0 invariant failures.** About 34.6 % of mutants parse successfully and are then fully checked. About 2.2 % reach and fail zstd decoding (219 587 for seed 101). Every error code was hit |
| Fuzzing, MSVC Release (Windows) | 20 000 000 iterations, seed 404, 78.3 s, 0 invariant failures, 0 crashes (6 919 633 successes, 439 504 zstd failures) |
| RTGL1 build | **Exit 0, 66/66 Ninja steps, 0 compiler warnings** (EXP-002: 79 steps with libktx). `RayTracedGL1.dll` is 1 470 976 bytes, SHA-256 `54207c96…782a` (local only, not distributed) |
| libktx in the build | **0**: 0 `Source/KTX/` files and 0 `KHRONOS_STATIC`/`LIBKTX` in `ninja -t commands RayTracedGL1.dll`. The only KTX/zstd objects are `Ktx2Reader.cpp.obj` and `zstd/zstddeclib.c.obj`. 0 occurrences of `ktxTexture`, `libktx`, `KTX_SUCCESS`, `ktxHashList`, `ktxStream` or `ktxMemStream` in the DLL. The build ran with the `Source/KTX` directory deleted |

## Deviations, modifications and failures

- **MSVC AddressSanitizer does not start** on this machine. The VS 17.5 `/fsanitize=address` build fails at load with `0xC0000142` (DLL init failed), even outside the sandbox and with the runtime DLL next to the exe. The sanitizer runs were therefore done with g++ ASan+UBSan in a Docker container instead. The Windows fuzz run has no sanitizer.
- **Fuzz harness bug (fixed before the recorded runs)**: UBSan caught a division by zero in *the fuzzer's own* mutation code, for files of 13–15 bytes. It was not in the reader.
- **zstd checksum**: `combine.py` on Windows writes CRLF. Git stores the file as LF, so the committed blob has SHA-256 `5eb38abe…f3d0` and the CRLF original has `06401e20…384b`. Both are recorded in `VENDORED.txt` (`0eb4c4a`). The amalgamation itself is unmodified.
- The zstd bundled with RTGL1 was **replaced, not reused**. To keep the clean room, its file (inside `Source/KTX/lib/**`) was never opened, so its licence header could not be confirmed. The vendored upstream release says, in `zstd.h` and `LICENSE`: "licensed under both the BSD-style license … and the GPLv2 … You may select, at your option" [SRC `Source/zstd/zstd.h:1-9` @ `2821e09`].
- Not done here: shader generation and a runtime or render test. Both belong to track E1. No GPU and no game window was used, so the GPU lock was not needed.
- `Tools/GenerateBlueNoiseKTX2.cpp` is a standalone RTGL1 tool, not built by CMake, and still uses the libktx API. It was left unchanged.

## Interpretation

- [EXP] The reader matches the official Khronos tool byte for byte on every file it accepts. That includes RTGL1's own blue-noise file and Compressonator output, which is the format RTGL1's asset pipeline produces. Hostile input is rejected without memory errors under ASan and UBSan.
- [SRC] With `d509ff3`, the RTGL1 tree no longer contains Apache-2.0 KTX-Software code. **Licence consequence:** `Ktx2Reader.{h,cpp}` and `Ktx2FormatTable.inl` are GPL-2.0-only, so any RTGL1 binary built from this branch is GPL-2.0-only as a combined work. The RTGL1 files themselves stay MIT and zstd is used under BSD-3-Clause/GPL-2.0. This matches the only consumer, the GPL-2.0-only engine, but the branch should not be offered back upstream as MIT without relicensing the reader.
- [ASM] The behaviour differences listed under "ImageLoader contract" should not affect SE-RT, which uses plain 2D BC7/BC5 overrides, the blue-noise array and the water normal. This needs to be verified by E1's render test.

## Impact on ADRs, dossiers and backlog

- Phase 1 owner question "remove Apache-2.0 KTX code from the GPLv2 runtime": the code-level work is done on `sprint2/ktx2-cleanroom` and is ready for E1 to integrate. The lead should update the dependency/licence inventory: RTGL1 deps lose libktx and gain the GPL-2.0-only reader plus zstd 1.5.7 (BSD-3-Clause OR GPL-2.0).
- ADR-0005 `.ktx2` contract: unchanged.

## Open questions

- None for the owner. Routine choice made by this track: zstd is vendored at 1.5.7 (mature) rather than 1.6.0, which was released 2026-11-23.
