# EXP-016: 4096×4096 texture crash in Classic-VK: root cause, fix and upload limits

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | Sprint 2 track E4 (engine); follow-up to EXP-012 §3 (raster import path) |
| Status | complete. TSE verified on TechTest (4096², Vulkan + OpenGL) and on a normal load of 1_1_Palenque |
| Environment | Windows 11 Pro 10.0.22631, Intel Core i5-11600K, NVIDIA RTX 4070 12 GB, driver 616.64 (Vulkan 1.4.351, OpenGL 4.6.0). VS 2022 17.5 / MSVC 14.35.32215 (v143), Windows SDK 10.0.22000.0, Vulkan SDK 1.4.363.0, WinFlexBison 2.5.25. Python 3.10.11 (numpy 2.2.6, Pillow 12.3.0). Crash capture: our own ctypes debugger `crashcatch.py` (local) using `C:\Windows\System32\dbghelp.dll` 10.0.22621.5471. No cdb/WinDbg/procdump is installed |
| Inputs | SSTRE-Engine local branch `phase1/cvk-build` @ `ba0c12e8` (Classic-VK `510d36f` plus the EXP-001 build commits). AssetCompiler `main` @ `6e118a0` (`tex-replace`). User-owned Classic TFE and TSE (Steam) |
| Code | SSTRE-Engine branch `sprint2/tex4096-crash` (local, not pushed): `15c567c0` (fix), `3a4d07cc` (limit and log) |

## Goal and success criteria

1. Reproduce the EXP-012 crash: a loose 4096×4096 `.tex` with unchanged mex crashes world load (0xC0000005) on Vulkan and OpenGL. Bisect the threshold (per axis, total pixels or memory).
2. Find the root cause with a symbolized stack from our own build with debug symbols.
3. Write a minimal GPL-2.0-only fix for the TFE and TSE trees. Verify on Vulkan and OpenGL: 4096² loads, 2048×4096 still works, normal level loads do not regress, VRAM is observed.
4. Answer the EXP-012 open question: does `tex_iNormalSize` cap the uploaded resolution, and are uploads recompressed?

## Procedure (exact, reproducible)

All scripts, logs, screenshots and dumps are local, under `G:\sstre-tmp\e4\` (`scripts\`, `probe\`, `runs\`).

1. **Worktree and build.**
   - Worktree: `git -C …\SSTRE-Engine worktree add G:\sstre-tmp\e4\wt-engine -b sprint2/tex4096-crash phase1/cvk-build`.
   - Build: `scripts\build-win.ps1`, which is the EXP-001 script pointed at G:. It runs MSBuild `Release|x64 /p:PlatformToolset=v143 /p:WindowsTargetPlatformVersion=10.0.22000.0 /p:UseOfMfc=false`, with targets Ecc, Engine, Entities(MP), Game(MP), Shaders, SeriousSam and the audio libraries.
   - The Release x64 configuration already sets `/Zi` and `GenerateDebugInformation=true`. That makes it a RelWithDebInfo build: optimized, with full PDBs. A separate Debug build was not needed.
   - Build times: TFE 176 s and TSE 122 s for a clean build of the runtime targets.
2. **Runtime.**
   - Private copies of the TFE and TSE runtimes: `G:\sstre-tmp\e4\runtime-cvk-tfe` and `runtime-cvk-tse`, copied from `local-work\runtime\cvk-*`. The originals were not modified.
   - Our binaries were placed in `Bin\`; the originals are kept in `Bin.phase1\`.
   - Every run: windowed 1280×720, single player, `+level`. The `+script` sets `ser_bEnumeration=0; ga_strServer="127.0.0.1"; ga_strMSLegacy="127.0.0.1"`.
3. **Test textures.**
   - `probe\gen.py` draws a synthetic pattern of our own: an 8×8 logical checker with a 1-px row probe and the label "E4 W×H". No game pixels are used.
   - It then calls the AssetCompiler CLI `tex-replace <original> <png> -o <runtime>\<path>.tex`, so the mex stays identical. Only the original's header fields are reused.
   - The loose file is removed again after each run, using a manifest.
   - Targets were chosen with `probe\find_cands.py`. It lists the textures a level references whose mex allows the size. Asset paths stay local (GATE-05).
4. **Crash capture.**
   - `scripts\crashcatch.py` starts `SeriousSam.exe` under `DEBUG_ONLY_THIS_PROCESS`. It logs first- and second-chance access violations and writes a minidump (`MiniDumpWriteDump`).
   - It walks the faulting thread with `StackWalk64`, symbolized from our PDBs. No symbol server is used.
   - Wrapper: `scripts\run-crash-e4.ps1`. Timeout 40 s; if nothing crashes, the process is terminated.
5. **Verification.**
   - `scripts\run-game-e4.ps1` is the EXP-001/EXP-012 harness. It takes a PrintWindow screenshot of the game window only and samples `nvidia-smi --query-gpu=memory.used` before launch and after about 35 s.
   - Batches: `batchA.ps1` (unpatched, under the debugger), `batchC.ps1` (patched).
6. **GPU lock.**
   - Batch A: `gpu-lock.ps1 acquire` (ACQUIRED, exit 0), 23:25:15–23:28:49.
   - Batch C: `gpu-lock.ps1 run`, 23:45–23:54.
   - Final-build confirmation: `run` (see Results).
   - No keyboard or mouse input was sent. Focus loss is not detected by the harness. None of the screenshots shows interference.

## Results ([EXP] unless labelled otherwise)

### 1. Reproduction and bisection (unpatched build at `ba0c12e8`, TFE)

| Run | Loose texture (px, mex kept) | Total pixels | API, settings | Result |
|---|---|---|---|---|
| A1 | 4096×4096 (TechTest floor, firstMip 3 → 0) | 16.8 M | Vulkan, default GLSettings | **AV at 7.6 s** during world load |
| A2 | 4096×4096 | 16.8 M | OpenGL, default | **AV at 3.4 s** |
| A3 | 4096×4096 | 16.8 M | Vulkan, custom mode `sam_iVideoSetup=3; tex_iFiltering=0` | **no crash** (40 s) |
| A4 | 4096×4096 | 16.8 M | Vulkan, custom mode `tex_iFiltering=-2` | **AV at 4.1 s** |
| B1 | 4096×2048 | 8.4 M | Vulkan, default | **AV at 4.2 s** |
| B2 | 2048×8192 | 16.8 M | Vulkan, default | **no crash** |
| B3 | 4096×1024 (01_Hatshepsut) | 4.2 M | Vulkan, default | **AV at 5.0 s** |
| B4 | 2048×4096 | 8.4 M | Vulkan, default | no crash (matches EXP-012) |

**Threshold.** The crash depends on **width alone**: width > 2048 px crashes whenever texture filtering is on.

- It does not depend on height or on total pixel count. 2048×8192 (16.8 Mpx) loads, while 4096×1024 (4.2 Mpx) crashes.
- It does not depend on memory.
- It does not depend on the API: Vulkan and OpenGL crash in the same place.
- With `tex_iFiltering=0`, 4096² loads.
- Non-power-of-two sizes such as 3072² cannot be tested. The engine format requires power-of-two sides [SRC `Texture.cpp:313-314` `FastLog2` assert], and `tex-replace` only accepts power-of-two scales.

**Symbolized stack** (identical in all 6 crashing runs; the frames are from A1):

```
EXCEPTION 0xc0000005 first-chance  read 0xffffffffffffffff
 #00 CNameTable_CTextureData::FindSlot+0x1d   [Engine\Templates\NameTable.cpp:59]
 #01 CNameTable_CTextureData::Find+0x25       [Engine\Templates\NameTable.cpp:100]
 #02 CStock_CTextureData::Obtain_t+0x1f       [Engine\Templates\Stock.cpp:46]
 #03 CTStream::DictionaryPreload_t+0xac       [Engine\Base\Stream.cpp:869]
 #04 CWorld::ReadBrushes_t+0x95               [Engine\World\WorldIO.cpp:199]
 #05 CWorld::Read_t+0x84                      [Engine\World\WorldIO.cpp:150]
EXIT code=0xc0000005
```

- The fault is in the texture stock's name table, in the lookup of the **next** texture after the oversized one was loaded. The table's data had been overwritten.
- In B1, frames #03–#05 are `CTextureObject::SetData_t` ← `CBrushPolygonTexture::Read_t` instead, because the corrupted lookup came from another caller.
- The faulting address is a victim, not the cause. The minidumps are in `runs\dumps-*\` (local).

### 2. Root cause ([SRC] at `ba0c12e8`, SamTFE paths; SamTSE identical)

1. `Engine/Graphics/Graphics.cpp:1225` declares `extern "C" { ULONG aulRows[2048]; }`. This is the "temp rows for in-place filtering" buffer of `FilterBitmap()` (`:1345`).
2. `FilterBitmap()` advances `rowptr` through `aulRows` once per texel of a row. This happens in all code paths: the x64 MSVC build uses the portable C path at `:2286–2545`; the MMX-intrinsics and x86 asm variants (`:1371–2285`) do the same. A row wider than 2048 texels therefore writes past the end of the array into neighbouring `.bss` globals.
3. `CTextureData::Read_t` (`Texture.cpp:943–958`) passes `tex_iFiltering` to `MakeMipmaps()`. Only `TEX_CONSTANT` textures and exports are excluded. `MakeMipmaps()` calls `FilterBitmap()` on mip 0 and on every following level (`Graphics.cpp:527/531`).
4. This all happens **before** `RemoveOversizedMipmaps()` (`Texture.cpp:962`) reduces the texture, so neither the size cvars nor the driver limits can prevent it.
5. `tex_iFiltering` defaults to 0 in code (`GfxLibrary.cpp:148`). The shipped `Scripts/GLSettings/Initial.ini:67` sets it to **−2** (sharpen). That script runs on every start unless `sam_iVideoSetup=3` (custom) [SRC `SeriousSam/GLSettings.cpp:157-165`]. So every default install filters every texture.

This also explains why EXP-012's 2048×4096 worked: its width is 2048.

Other fixed limits checked, none of which is the cause:

- The OpenGL `_aulLastMipmaps[1365]` (`Gfx_OpenGL_Textures.cpp:38`) depends only on the aspect-ratio tail.
- Vulkan `mipmapSizes[32]` is large enough.
- `GetMipmapOffset(15,…)` covers 4096² (13 mip levels).
- `ColorizeMipmaps` skips textures above 1024 px.
- No 32-bit size overflow: 4096² RGBA with mips is 89 MB.

### 3. Fix (local branch `sprint2/tex4096-crash`, both TFE and TSE)

| Commit | Change | Lines |
|---|---|---|
| `15c567c0` fix(gfx) | `aulRows[2048]` → `aulRows[FILTERROWS_MAX]` with `FILTERROWS_MAX 16384` (64 KB static, covers the Vulkan default `gl_pixMaxTextureDimension` 8192 and more). Guard in `FilterBitmap()`: a row wider than the buffer is copied unfiltered and logged once, instead of overflowing. `#include <Engine/Base/Console.h>` | +27/−1 per tree |
| `3a4d07cc` feat(gfx) | `tex_iNormalSize` clamp 5..11 → 5..**12** (opt-in to an uploaded area of 4096²; defaults unchanged). One console line per texture above 2048 px: size, skipped mip levels, uploaded size, limits | +17/−5 per tree |

- New code carries the ITEagle copyright and the `GPL-2.0-only` SPDX tag in the style of POC-32. Croteam notices are unchanged.
- No `Signed-off-by` trailer.
- TSE Release (targets Ecc, Engine, EntitiesMP, GameMP, Shaders, SeriousSam) builds with 0 errors.
- "Real support" was chosen over rejecting oversized textures. The fix is a buffer size plus a defensive guard; no behaviour changes for textures ≤ 2048 px.

### 4. Verification (patched Release build)

Batch C, 35 s per run, the `  started.` marker was reached in every run, and every process was still `Responding=True` when killed:

| Run | Configuration | Log / result | VRAM before → end (MiB) |
|---|---|---|---|
| C0 | TFE TechTest, Vulkan, no loose texture | loads, 5.1 s | 718 → 1267 |
| C1 | 4096², Vulkan, default | loads; `4096x4096 px, 3 mip(s) skipped, uploaded as 512x512 (area limit 262144, max dimension 8192, tex_iNormalSize=9)` | 687 → 1297 |
| C2 | 4096², OpenGL, default | loads; uploaded as 512×512 (max dimension 32768) | 717 → 760 |
| C3 | Vulkan, custom `tex_iFiltering=-2; tex_iNormalSize=12`, no loose texture | loads | 717 → 1297 |
| C4 | 4096², Vulkan, same custom settings | loads; **`0 mip(s) skipped, uploaded as 4096x4096`** | 717 → 1297 |
| C5 | 4096², OpenGL, same custom settings | loads, `uploaded as 4096x4096`; the screenshot shows our pattern on the floor | 717 → **800** |
| C6 | 2048×4096, Vulkan, default | loads (no regression); uploaded as 256×512 | 717 → 1297 |
| C7 | 4096×1024, 01_Hatshepsut, Vulkan | loads (crashed before the fix); uploaded as 1024×256 | 717 → 1297 |
| C8 / C9 | 01_Hatshepsut, no loose texture, Vulkan / OpenGL | load normally (3.9 s / 3.6 s), no new log errors | 717 → 1265 / 685 → 788 |
| D1 / D2 | **TSE** TechTest, 4096² wall, Vulkan / OpenGL | load; uploaded as 512×512 | 716 → 1297 / 716 → 780 |
| D3 | TSE 1_1_Palenque, no loose texture, Vulkan | loads normally | 716 → 1296 |

**VRAM.**

- **Vulkan:** the end-of-run VRAM is 1297 MiB whether or not the texture is present (C3 vs C4). Classic-VK suballocates every texture from one device-local pool that it allocates up front: 256·256·4·4/3 × 512 × 3 ≈ 537 MB [SRC `Vulkan/SvkTextures.cpp:31-33`, `SvkMemoryPool.cpp:24`]. `nvidia-smi` therefore cannot see individual Vulkan textures.
  - [SRC/ASM] A full-size 4096² upload costs 4096²·4·4/3 ≈ 85 MiB of that pool (Vulkan maps every format, including RGB5, to `R8G8B8A8_UNORM`, `Texture.cpp:86-95`).
  - The pool is not chained. When it is exhausted, `Allocate` prints "Vulkan: Increase SvkMemoryPool…" and the texture is dropped [SRC `SvkMemoryPool.cpp:244`, `SvkTextures.cpp:314-322`]. No run printed that message.
- **OpenGL:** C5 used 40 MiB more than C2. The two runs differ only in the floor's upload size (512² vs 4096²): every other TechTest texture is at most 512², so the area cap does not touch them. 40 MiB matches **16-bit** storage of 4096² with mips (4096²·2·4/3 = 42.7 MiB), not 32-bit (85 MiB). See §5.
- **Final-build confirmation** at `3a4d07cc` (`runs\batchC2.txt`, `gpu-lock.ps1 run` 00:30–00:33). The log now names the texture.
  - C1 (Vulkan, default): 4096² loads, uploaded as 512×512.
  - C4 (Vulkan, `tex_iNormalSize=12`): uploaded as 4096×4096.
  - **C3b (OpenGL baseline, same custom settings, no loose texture) ended at 749 MiB, and C5 (same with the 4096² floor) at 789 MiB: +40 MiB.**
  - D4 (TSE, OpenGL, `tex_iNormalSize=12`): 4096² loads, uploaded as 4096×4096, 810 MiB.
  - All runs reached `started.` and were still responsive.

### 5. `tex_iNormalSize` and recompression (EXP-012 open question)

- **[SRC] Yes, it caps.** `RemoveOversizedMipmaps()` skips mip levels until the area is ≤ 4^`tex_iNormalSize` (animated textures use `tex_iAnimationSize`) and the largest side is ≤ `gl_pixMaxTextureDimension` [`Texture.cpp:581-630`, `Graphics.cpp:40-51`]. Only `TEX_CONSTANT` textures get a fixed area of 4096² (`:590`).
  - The code default is 9 (`GfxLibrary.cpp:138`); `Initial.ini:62` also sets 9. Before the fix the clamp was 11 (`Texture.cpp:188`).
- **[EXP] At runtime with the shipped settings, the effective value is 9, i.e. an area of 512²** (C1, C2, C6, C7, D1, D2).
  - Every replacement is reduced to 512² area: 4096² → 512², 2048×4096 → 256×512, 4096×1024 → 1024×256.
  - **Consequence for EXP-012 [inference]:** its 2×/4× density screenshots most likely showed textures downsampled back to ≤ 512² area. The "4× works" result proves loading and mapping, not resolution. The 1-px probes did not show aliasing because mip generation happens before the cap.
- **[SRC] Recompression.**
  - Vulkan uploads every format as uncompressed RGBA8 (`Texture.cpp:86-95`).
  - OpenGL compresses (ARB/S3TC/FXT1) only when the quality digit is 3 (`DetermineInternalFormat`, `Texture.cpp:451-515`). That is not the default.
  - However, with the default `tex_iNormalQuality=00` ("optimal"), an opaque texture is uploaded as **`GL_RGB5` (16-bit) and dithered** (`tex_iDithering=3`) unless its `.tex` flags contain `TEX_32BIT` = bit 1 (`Texture.h:31`). An alpha texture without that bit is uploaded as `GL_RGBA4` or `GL_RGB5_A1`.
  - [EXP] The OpenGL VRAM delta (§4) supports 16-bit storage. [ASM] The driver keeps the requested 16-bit internal format; this was not verified with a pixel readback.
  - EXP-012 saw flag bit 1 only on background and UI textures, so it is the "32-bit" flag. A replacement that `tex-replace` writes with the original flags keeps 16-bit OpenGL uploads for ordinary world textures.

## Deviations, modifications and failures

- **Lock wait.** The first two `acquire` attempts (22:20 and 22:40) timed out or waited behind AI1 and E3 for about 65 minutes in total. No game was started without the lock.
- **Harness bugs (ours, fixed):**
  - a path in `run-game-e4.ps1` was broken by shell escaping. The first `run` of batch C (23:28) aborted before the game was launched, and the lock was released.
  - the first version of `crashcatch.py` had a wrong `MINIDUMP_EXCEPTION_INFORMATION` packing (fixed with `_pack_=4`).
- **First log version printed an empty texture name**, because `GetName()` is not set during `Read_t`. Fixed in `3a4d07cc`, which passes the stream description. Batch C ran on the version before that fix. Engine logic is otherwise identical.
- The final build was re-confirmed with five runs (§4, "Final-build confirmation"). Rerun with `batchC.ps1 -Only '^(C1-|C3b-|C4-|C5-|D4-)'`.
- Not done:
  - a standalone Debug|x64 build (Release has full PDBs);
  - a pixel-exact check that the 4096² upload is sampled at full resolution (the 1280×720 view cannot resolve it);
  - long play sessions;
  - Linux.

## Interpretation

- [SRC+EXP] The ">8 Mpx crash" from EXP-012 is a **width > 2048 px** static buffer overflow in `FilterBitmap()`. It is not a memory or pixel-count limit. It affects every renderer, because the filtering is done on the CPU before upload.
- [EXP] With `15c567c0`, textures up to the 16384 px row buffer can be filtered without overflow, and wider textures are skipped with a log line. Uploads are then limited by `tex_iNormalSize`, not by a crash.
- [SRC] Without engine changes, high-resolution replacements are **reduced to 512² area by the shipped settings**. Raster HD needs a platform profile that sets the size and quality cvars, and replacements with `TEX_32BIT` for OpenGL.

## Recommended platform-profile limit

- **Desktop PC (RTX-class, 8 GB+):** `sam_iVideoSetup=3` (custom), `tex_iNormalSize=11` (2048² area, 4 Mpx) as the default HD tier.
  - Allow 12 (4096², needs `3a4d07cc`) only for a curated set: each 4096² texture costs 85 MiB of the fixed 537 MB Vulkan pool.
  - Also set `tex_iNormalQuality=22` (32-bit; avoids RGB5/RGBA4 plus dithering on OpenGL), or set `TEX_32BIT` (flag bit 1) in AssetCompiler output.
  - Keep `tex_iFiltering` as is: it is safe after the fix.
- **Hard limits:** source width ≤ 8192 (Vulkan `gl_pixMaxTextureDimension` default; OpenGL reports 32768). Power-of-two sides.
- **Steam Deck/low-VRAM (ASM, untested):** `tex_iNormalSize=10` (1024²).

## Impact on ADRs, dossiers and backlog

- EXP-012 §3:
  - correct "largest accepted" to "width ≤ 2048 without the fix";
  - note that the default settings downscale to 512²;
  - mark the `tex_iNormalSize` and compression questions answered.
- Engine backlog: merge `15c567c0` (crash fix, both trees). Treat `3a4d07cc` as optional and tie it to the platform profile.
- New items:
  - make the Vulkan memory pool chain or grow for HD sets;
  - add a platform profile that sets the texture cvars;
  - add AssetCompiler support for setting `TEX_32BIT` on replacements.

## Open questions

1. Lead / engine: should SSTRE builds ship a default `sam_iVideoSetup=3` profile with HD texture cvars, or keep the original GLSettings scripts and override them only for HD mode?
2. AssetCompiler: should `tex-replace` set flag bit 1 (`TEX_32BIT`) by default for replacements? This decision belongs to track A1.
