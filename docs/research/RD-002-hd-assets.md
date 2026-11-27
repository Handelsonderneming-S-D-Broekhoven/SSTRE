# RD-002: Classic vs HD asset formats and HD-to-Classic mapping feasibility

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Status | Draft research. Phase 0. Not a decision. |
| Author | Agent B (asset format researcher), for lead review |
| Related | [RD-001 engine baseline](./RD-001-engine-baseline.md), [RD-003 AI pipeline](./RD-003-ai-pipeline.md), [RD-005 rendering](./RD-005-rendering.md), [RD-007 licensing](./RD-007-licensing.md) |
| Schema proposal | [`schemas/asset-inventory.schema.json`](../../schemas/asset-inventory.schema.json) |

## 1. Question and scope

Can the textures and materials from the Serious Sam HD remasters (standalone HD TFE/TSE and the HD content inside Serious Sam Fusion 2017) serve as sources for a Classic (Serious Engine 1.10) runtime? The plan (§3, open decision 2) asks for an answer at five levels: texture, model, UV, material and shader. It also asks which conversions are needed, which editions and hashes to support, and how to record assets that cannot be matched or are ambiguous.

In scope:
- Identifying the editions installed locally.
- Archive and file formats.
- Aggregate statistics.
- Classic formats, using the engine source as evidence.
- HD formats, from header observation.
- Mapping strategy, the inventory schema and a 50-asset test matrix.

Out of scope:
- Any extraction to disk.
- Any conversion.
- Any legal conclusion. Legal questions are flagged for Agent E and the lead in §11.

## 2. Method and evidence

- **Engine source (primary for Classic):** `upstream/Croteam-official_Serious-Engine` @ `b408e88a16fd01aa1cfd0e0a999c86c2c1437c9e`, plus `upstream/sultim-t_Serious-Engine-RT` @ `0e7f223c19a28014b60d900878c28831db522120` for the texture-override mechanism. The files cited below are under `Sources/Engine/`.
- **Local installs (read-only):** the five Steam installs (Classic TFE/TSE, HD TFE/TSE, Fusion 2017) listed in the Phase 0 lead brief (a local working note, not committed). Probes were made with Python 3.10 (`python -I`) and `zipfile`. The probes read the zip central directories and the first 64 bytes to 4 KB of selected entries, in memory only. Only aggregates were written, all of them to `<workspace>/local-work/agent-b\` (scripts `gro_survey.py`, `pathmap.py`, `hdprobe*.py`). No game binaries were run and nothing was extracted to disk.
- **Web sources:** searches found no public specification or tool for the Serious Engine 3 (HD) `.tex`/`.mdl` formats. The only related project is [purifetchi/SS1TexConverter](https://github.com/purifetchi/SS1TexConverter), which targets Classic/Revolution `.tex`; I did not verify whether it handles HD files. A community question on opening HD `.tex` files has no answer (r/Croteam thread, Feb 2025, which returned HTTP 403 when fetched). **HD format details below come only from header observation and are marked uncertain.**

## 3. Observed facts: edition fingerprints

### 3.1 Steam metadata (`steamapps/appmanifest_*.acf`)

| Edition | App ID | Install dir | buildid | LastUpdated (unix) | Engine version string observed in assets |
|---|---|---|---|---|---|
| Classic TFE | 41050 | `Serious Sam Classic The First Encounter` | 22445611 | 1776167503 | n/a (SE1.x; Steam build ships SE1.10-era tools) |
| Classic TSE | 41060 | `Serious Sam Classic The Second Encounter` | 22445660 | 1776167506 | n/a |
| HD TFE | 41000 | `Serious Sam HD The First Encounter` | 5820849 | 1678025586 | `SeriousSamHD; Win32; Standard; Final; 3.003.00:112039` |
| HD TSE | 41010 | `Serious Sam HD The Second Encounter` | 5821931 | 1678026548 | `SeriousSamHD_TSE; Win32; Standard; Final; 3.003.00:120201` (also `:120225`, `:120242` in patch archives) |
| Fusion 2017 | 564310 (name "Serious Sam Fusion 2017 (beta)") | `Serious Sam Fusion 2017` | 3897313 | 1678029082 | `SE2017_PC_dev; SeriousSam2017-Windows-Final; 404079 2018-11-…` |

The version strings come from the `$Version:` field inside the `CTSEMETA` headers of HD assets.

**Needs confirmation:**
- Whether other storefronts (GOG, retail CD, Steam "Revolution") produce different hashes.
- Whether the HD games are still sold or patched standalone. Their Steam builds date from 2023.
- How Fusion's "beta" status affects its content stability.

### 3.2 Top-level archive and executable SHA-256 (local, 2026-11-27)

SHA-256 hashes and byte sizes were recorded for 40 top-level archives and executables across the five installs. Shader caches, redistributables and third-party `Mods/` content were excluded.

**Publication status:** per owner decision (2026-11-27), the per-file hash table is kept **locally only**, in the workspace file `local-work/agent-b/RD-002-hd-assets.FULL.local.md`, until its provenance and the applicable restrictions have been reviewed (backlog GATE-05). The public dossier keeps only the method and the aggregate facts:

- Every edition is identified by its set of top-level `.gro` archives and its main executable.
- Two archives are byte-identical between Classic TFE and Classic TSE (the `1_04` patch and logo archives).
- HD TFE, HD TSE and Fusion each ship a `SignatureCatalog.dat` alongside their content archives.

**Known vs needs confirmation:**
- These hashes describe **one** machine on 2026-11-27.
- I don't know whether Steam serves byte-identical archives to other users at the same buildid. This is likely but unverified.
- The Classic TSE install also contains a third-party `Mods/Warped/` (3 archives). The inventory must exclude `Mods/` by default.

## 4. Observed facts: archive formats and aggregate counts

All `.gro` files in every edition are **standard PKZIP archives**:
- They start with local-header magic `PK\x03\x04` and end with an EOCD record.
- Entries use only methods 8 (deflate) and 0 (stored).
- **No encrypted entries** were found in any archive.
- Python `zipfile` opened every archive, including the 3.1 GB Fusion pack.

The HD and Fusion installs also ship `SignatureCatalog.dat` / `*.dat` files (magic `SIGSTRM12GIS`, containing key name `SignKey.Official…`). This is an archive-signing catalog, and it implies the **HD runtimes may refuse modified archives**. That does not matter here, because SSTRE only reads HD content.

| Edition (main content archives) | Entries | `.tex` | `.mdl` | `.wld` | Other notable |
|---|---|---|---|---|---|
| Classic TFE `1_00c.gro` | 2267 | 1228 | 359 | 0 (42 loose `.wld` under `Levels/`, 17 in ExtraTools) | `.ecl` 99, `.wav` 330, `.amc` 23, `.fnt` 6 |
| Classic TSE `SE1_00*.gro` | 3142 + 118 + 49 | 1495 + 56 + 23 | 637 + 27 | 23 (Levels gro) | `.bm` / `.smc` / `.sha` (SKA and shaders) in `1_07_tools.gro` |
| HD TFE `All*.gro` | 5684 + 445 + 633 | 1556 + 66 + 45 | 1399 + 83 + 77 | 18 + 7 + 7 | `.mtr` 247, `.mat` 40, `.bmf` 25, `.pfx` 293, `.rsc` 291 |
| HD TSE `All*.gro` + DLC | 8476 + … | 2531 (All) + 1317 (DLC_TFE) + 1024 (LotB) | 2239 + 1334 + 779 | 36 + 23 + 7 | `.mtr` 352, `.mat` 56, `.bmf` 54 |
| Fusion `10_Game_SeriousSamHD_TFE.gro` | 12318 | 2124 | 2585 | 31 | `.bmf` 2327, `.rsc` 1914, `.mtr` 507 |
| Fusion `10_Game_SeriousSamHD_TSE.gro` | 18119 | 3294 | 4061 | 35 | `.bmf` 3774, `.rsc` 2578, `.mtr` 617 |

**Path roots:**
- Classic uses bare roots: `Textures/`, `TexturesMP/`, `Models/`, `ModelsMP/`, `Levels/`, `Classes/`, `Data/`.
- HD prefixes every path with `Content/SeriousSamHD/` (the TSE install adds `Content/SeriousSamHD_TSE/`).
- Fusion uses the same `Content/SeriousSamHD[_TSE]/` roots inside game-pack archives, plus `Content/Shared/`, `Content/SeriousSamFusion/` and `Content/SeriousSam3/`.
- HD TSE's `DLC_TheFirstEncounter.gro` is a second HD TFE content source.

### 4.1 Classic texture header statistics (TDAT parsed from the first 64 bytes; base archives only)

| Metric | Classic TFE (1229 `.tex`) | Classic TSE (1576 `.tex`) |
|---|---|---|
| Version (TVER) | v4: 1200, v3: 29 | v4: 1562, v3: 14 |
| Procedural effect textures (FXDT) | 19 | 25 |
| Animated (frames > 1) | 9 | 10 |
| Alpha-channel flag | 245 | 418 |
| Max pixel dimension | 1…1024; mode 256 (553); 1024 only 5 | 1…1024; mode 256 (728); 1024 only 7 |
| Non-power-of-two | 0 | 0 |
| Non-square | 454 | 442 |

## 5. Format table

| Asset | Classic SE1 (evidence: source) | HD / Fusion SE3-era (evidence: header observation, **uncertain**) |
|---|---|---|
| Archive | `.gro` = zip; later-loaded archives override earlier ones (mount-order rules still to be confirmed from `Base/Unzip.cpp`) | `.gro` = zip (all archives < 4 GiB; zip64 use not checked); signed with `SignatureCatalog.dat` |
| Texture | `.tex`: `TVER` + int version (3 or 4), then chunks `TDAT` (flags, mexW, mexH, fineMips, firstMip, [v3: ctMips, frameSize], frames), `FRMS` (raw RGB/RGBA per frame, v4 stores mip 0 only, mips regenerated on load), `ANIM` (CAnimData), `BAST` (base texture name), `FXDT`/`FXBF`/`FXB2` (procedural effect), `DTLT` (legacy). Pixel = mex >> firstMip; max 1024 px (`MAX_MEX`, `Base/Types.h:162-169`); power-of-two asserted. Source: `Graphics/Texture.cpp:677-900` | `.tex`: magic `CTSEMETA` + `0x1234ABCD` marker, then self-describing reflection metadata (`$Version:`, class names `CResourceFile`, `CStaticTexture`, `CBaseTexture`, `CPlatformMip`, `TexFlags`, `TexFormat`, `GfxTexWrap`, `CTextureMatrix` (TSE/Fusion), `CColorModifiers` (Fusion), `CResourceStreamingData` (Fusion)), `METAEND`, then data. Pixel format, dimensions and compression are not yet decoded; a `CTSEMETA` reader is required |
| Model | `.mdl`: `MDAT` + version chunk `V007`…`V010` observed (TFE: V010 338, V009 17, V008 2, V007 2), vertex-animated mip-models, `STXW`/`STXH` = texture size in mex that the UVs are authored against. Source: `Models/Model.cpp:1270ff, 1495`, `Models/Model_internal.h:25-31`. TSE adds SKA: `.bm` (`MESH`, v12), `.bs` (`SKEL`), `.ba` (`ANIM`), `.smc` (text). Source: `Ska/Mesh.cpp:19-20` | `.mdl`: `CTSEMETA`; classes `CSkeleton`, `CMesh`, `CRenderMesh`, `CModelConfigChildrenHolder`, `CModelAnimHost`, `CMechanismTemplateHolder`, `CDestructionHolder`. Geometry in `.bmf` (`CRenderMesh`, `CCollisionMesh`, `CShaderModifierList`, `CRenderMeshSection`, vertex buffers). Skeletal (`.skl`), animation (`.ans`/`.anh`) |
| World | `.wld`: starts `BUIV` (build version, `Network/Network.cpp:2251`), then `WRLD`, brushes (BSP, polygons with 3 texture layers `bpo_abptTextures[3]`, `Brushes/Brush.h:394`), entities (`WSTA`). Source: `World/WorldIO.cpp` | HD standalone `.wld`: `CTSEMETA` (`CWorldInfoEntity`, `CLightmapAtlas`, `CStaticAtlasGroup`). Fusion `.wld`: magic `WRKSTRM1`. Mesh-based worlds, **not** brush/BSP |
| Material | None as a separate asset: surface = texture plus per-polygon flags/blend on the brush; models use mdl render flags, plus reflection/specular/bump textures set by entity code. TSE SKA uses `.sha` shader DLL entries (`Shaders/`) | `.mtr` (`CTSEMETA`, 247 in HD TFE), `.mat` (`CSamMaterial`, `CMaterialAttributes`; physical/sound/decal/particle "scheme", **a gameplay material, not a render shader**). Render shader parameters live in `CShaderModifierList` in meshes and `.mtr` (uncertain) |
| Shader | Fixed-function / `Shaders.dll` (TSE SKA) | Compiled caches `CachedShaders_*.gro` (`.shc`; D3D9 for HD, D3D11/D3D12/VLK/MTL for Fusion). Not reusable |
| Font | `.fnt` `FTTF` + `.tex` atlas (`Graphics/Font.cpp:83`) | `.fnt` `CTSEMETA`; Fusion also ships `.ttf` |
| Entity classes | `.ecl` (references the `.es`-compiled DLL class); `.es` sources in the engine repo | Lua (`.lua`), `.ep` / `.rsc` / `.nfo` databases |

## 6. Mapping feasibility by level

### 6.1 Texture level: **feasible for a subset; path heuristics work for architecture**

Normalized path match: lowercase, strip `Content/SeriousSamHD[_TSE]/`, fold `TexturesMP`→`Textures` and `ModelsMP`→`Models`, drop the extension.

| Pair | Classic `.tex` | HD `.tex` | Exact normalized path | Basename-only | Basename-only unique |
|---|---|---|---|---|---|
| Classic TFE → HD TFE standalone | 1228 | 1623 | **377 (31%)** | 243 | 190 |
| Classic TFE → Fusion HD TFE | 1228 | 2123 | 369 | 244 | 190 |
| Classic TSE → HD TSE (incl. DLC TFE/LotB) | 1501 | 3363 | **400 (27%)** | 218 | 158 |
| Classic TSE → Fusion HD TSE | 1501 | 3293 | 379 | 197 | 162 |

Breakdown for Classic TFE against both HD sources:

| Classic prefix | Classic count | Exact match | Basename-only | Interpretation |
|---|---|---|---|---|
| `Textures/Levels/` | 390 | 253 (65%) | 70 | Architecture largely kept the Classic path |
| `Textures/Computer/` | 91 | 71 | 0 | Netricsa message images (contain text) |
| `Textures/Effects/` | 92 | 20 | 4 | Partly kept |
| `Textures/Interface/` | 37 | 7 | 1 | Crosshairs kept; HUD redrawn |
| `Textures/Background/` | 111 | 1 | 56 | Skies reorganized (`Textures/Background/Panoramica/…`); basename hits like `frame0001` are false positives |
| `Models/Enemies/`, `Models/Weapons/`, `Models/Player/`, `Models/Items/`, `Models/Plants/` | 76 / 31 / 66 / 45 / 4 | **0 / 0 / 0 / 0 / 0** | 29 / 2 / 3 / 22 / 0 | HD remade characters, weapons and items. Basename hits are mostly false (e.g. an enemy's `laser` matching a HUD weapon icon) |
| `Fonts/`, `Textures/Detail/`, `Models/ReflectionTextures/`, `Models/SpecularTextures/` | 6 / 3 / 7 / 3 | 0 | ≈0 | No counterpart; keep Classic or regenerate |

An exact path match is **necessary but not sufficient**. HD textures with the same name may differ:
- in aspect ratio, content crop or atlas layout;
- in being split into separate albedo/normal/specular maps;
- by being designed for HD lighting (baked AO, different color grading).

HD dimensions are **not yet determined**, because the `CTSEMETA` payload is undecoded. Every candidate therefore needs:
- an aspect-ratio check;
- a perceptual comparison against the Classic texture after downscaling the HD one to Classic resolution;
- a tileability and seam check.

### 6.2 UV level: **compatible for brush architecture, incompatible for remade models**

- **Brush (world) UVs** are derived from per-polygon mapping definitions (`Math/TextureMapping.h:113-118`) scaled by the texture's **mex** size. In `Graphics/DrawPort_RenderScene.cpp:206-257`, UVs are normalized via `1024/mexTexSize`. A replacement texture therefore keeps world-space tiling **if its logical (mex) size equals the original's**, regardless of pixel resolution, provided the runtime decouples pixels from mex.
- **Classic models (MDL)** author UVs in mex against `md_Width`/`md_Height` and normalize by the bound texture's `GetWidth()` (`Models/RenderModel_View.cpp:2085, 2184`). A higher-resolution texture with the **same aspect ratio and identical UV layout** works. The HD character and weapon textures belong to new meshes with new UV unwraps, so they are **UV-incompatible** with Classic MDLs. The 0% path match for enemies, weapons and player above is consistent with this, though it does not prove it.
- **Runtime constraint:** stock SE1 rejects textures larger than 1024 px (`MAX_MEX`) and asserts power-of-two dimensions (`Graphics/Texture.cpp:295-301`). Higher-resolution replacements therefore need the runtime override path.
- **Override path in the RT fork:** it already loads overrides by virtual path from `OverridenTextures/Compressed/<dir>/<name>.ktx2`, with `_n` (normal) and `_rme` (roughness/metallic/emission) postfixes and `NNN` frame suffixes for animated textures (`Sources/Engine/Raytracing/SSRT.cpp:316-355`, `TextureUploader.cpp:33, 100-235`). Mex sizes stay untouched, so UVs are preserved. This is the natural target contract for compiled HD-derived textures; see [RD-005](./RD-005-rendering.md).

### 6.3 Model level: **not feasible to import HD models into SE1**

The HD and Fusion `.mdl`/`.bmf` formats are skeletal render meshes with configs (`CModelConfigChildrenHolder`, `CMechanismTemplateHolder`). Classic TFE uses vertex-animated MDL with collision boxes and attachments, and its gameplay code references them through entity classes, so animation names and attachment indices are game logic. Classic TSE has SKA (`.bm`/`.bs`/`.ba`), but SKA is a different format and is mostly unused by the Classic campaign content.

Importing HD geometry would require:
- a `CTSEMETA` reader;
- retargeting the skeletons and animations;
- remapping the gameplay attachment points;
- changes to entity code.

This is a separate, high-risk project and is **not recommended** for Phase 2. Keep Classic models and upscale their own textures (see [RD-003](./RD-003-ai-pipeline.md)).

### 6.4 Material level: **limited, metadata-only reuse**

HD `.mat` files are physical and gameplay surface schemes (sound, decal, particle), not shaders. HD `.mtr` and `CShaderModifierList` files probably carry shader parameters and the texture-slot bindings for normal/specular/detail maps. This is a hypothesis.

If they can be decoded, they would give **slot-role hints**: which HD texture is the normal map for a given albedo. These hints are useful for inferring `_n`/`_rme` maps, but not for direct reuse. SE1 has no material asset to receive them.

### 6.5 Shader level: **not feasible**

HD and Fusion shaders ship only as compiled caches (`.shc`) for D3D9, D3D11, D3D12, Vulkan and Metal. They are tied to SE3 renderer conventions and cannot be used by SE1, RTGL1 or any raster fallback. Their **behaviour** (detail blending, specular) may serve as a visual reference only.

### 6.6 Levels / worlds: **not feasible**

The HD worlds are rebuilt mesh worlds (`CTSEMETA`/`WRKSTRM1`, `CLightmapAtlas`), not SE1 brushes. The Classic `.wld` files remain authoritative; the project mandate also requires gameplay parity.

## 7. Proposed mapping strategy

The pipeline lives in AssetCompiler; its output goes to SSTRE-Manifests `mappings/`.

1. **Inventory** every Classic and HD texture. HD records stay `texture_info`-incomplete until a `CTSEMETA` reader exists. Every record carries a stable ID, `<edition>:<normalized path>` (see schema).
2. **Candidate generation**, in order of cost:
   - (a) exact normalized path;
   - (b) folder-aware alias rules (`TexturesMP`→`Textures`, HD `…/Textures/` subfolders, `…/hd/` subfolders);
   - (c) basename within the same top category;
   - (d) perceptual-hash search (pHash/dHash on a grayscale downscale, plus a color histogram) across all HD textures of the same category.
   Basename matches outside the same category are never accepted automatically.
3. **Verification**, which produces a confidence in [0, 1]:
   - aspect-ratio match;
   - pHash distance below threshold after downscaling the HD texture to Classic dimensions;
   - SSIM/LPIPS against the Classic texture, used as a signal only, per plan §4;
   - matching alpha presence and cutout coverage;
   - seam continuity for tiling surfaces;
   - an optional affine fit (flip, rotate 90°, crop) recorded as `transform`.
4. **Decision:**
   - Confidence at or above the threshold with UV `identical`/`affine` → `matched`.
   - Two or more candidates within a small margin → `ambiguous`, which goes to the curation queue.
   - No candidate → `unmatched`, which falls back to Classic plus the AI pipeline.
   - Models known to be remade → `rejected_uv_incompatible`.
   - Owner decisions → `curated_override` (highest precedence, per plan §4).
5. **Recording:** every non-matched asset gets an explicit record with `mapping_status`, the candidate list (possibly empty) and evidence. The build report counts each status. Nothing is silently dropped.
6. **Output contract:** for matched assets, compile to the runtime override path and naming (for example the RT fork's `<virtual dir>/<name>.ktx2`, `_n`, `_rme`, `NNN`), keeping the original mex size.

## 8. Inventory schema

The schema is [`schemas/asset-inventory.schema.json`](../../schemas/asset-inventory.schema.json) (JSON Schema 2020-12, status **proposal**). It defines:

- **Inventory document:** `schema_version`, `generated_at`, `generator`, `sources[]` (one per archive: edition, Steam app/build, relpath, SHA-256, load priority) and `assets[]`.
- **Asset record:**
  - Identity: stable `asset_id` (`<edition>:<normalized path>`, deliberately hash-free so that patches keep their identity), `virtual_path` as stored, `source_sha256` of the uncompressed entry, `shadowed_sources`.
  - Type: `asset_type`, `file_format`, `category`, `semantic_tags`.
  - Texture: `texture` block with pixel and **logical (mex)** dimensions, `first_mip_level`, `mip_count`, `frames`, `procedural_effect`, alpha flag, raw flags, pixel format, cubemap, role.
  - Model: `model` block with UV fingerprint and `texture_logical_width`.
  - Rendering hints: `color_space` plus provenance, `alpha_mode` (`cutout_1bit` ↔ SE1 `TEX_TRANSPARENT`), `tileability` (hint, measured seam score, source), `dependencies[]` (typed relations, including `base_texture` for `BAST`).
  - Mapping: `mapping_candidates[]` (target, method, confidence, UV compatibility, pHash distance, transform, evidence, reviewer) and `mapping_status`.

Generated inventories enumerate proprietary file names. They belong in the user's local workspace, not in public repos, unless RD-007 clears it.

## 9. 50-asset test matrix (selection criteria; concrete paths are candidates pending owner review)

**Principles:**
- Use TFE first (plan §3), plus a few TSE-only items.
- Deliberately include each mapping outcome: exact match, ambiguous, unmatched and UV-incompatible.
- Include each Classic technical feature: v3 vs v4, FXDT, multi-frame, alpha, non-square, and 1024 px vs ≤32 px.
- The concrete candidate asset paths for each row are kept **locally only** (same local file as §3.2) until GATE-05 clears publication. The selection is a candidate set pending owner review.

| # | Category | Count | Selection criteria |
|---|---|---|---|
| 1 | Architecture | 8 | `Textures/Levels/*`; at least 4 with exact HD path match, 1 ambiguous, 1 unmatched, at least 2 non-square, at least 1 v3 |
| 2 | Terrain | 5 | Ground, sand and grass used on large tiling surfaces or terrain; measure seam and tiling |
| 3 | Vegetation | 4 | Alpha-cutout foliage on models |
| 4 | Enemies | 5 | Mix of small and large skins; expected UV-incompatible with HD |
| 5 | Weapons | 4 | First-person weapon skins (high screen coverage) |
| 6 | UI / HUD / fonts | 5 | Text and glyph integrity; never diffused |
| 7 | Alpha / cutout | 4 | Level textures with the alpha flag; test 1-bit vs blend detection |
| 8 | Animated textures | 3 | Multi-frame `FRMS` (frames > 1) |
| 9 | Normal / bump / detail | 3 | SE1 detail layers and bump textures; output is data, not color |
| 10 | Technical masks | 3 | Heat maps, shadow masks, reflection/specular maps (color space = data) |
| 11 | Skies / backgrounds | 3 | Background or sky frames; HD reorganized them, so test perceptual matching and check pHash false positives |
| 12 | Effects | 3 | 1 procedural FXDT (must be excluded from bitmap upscaling), 1 flare, 1 particle |
| | **Total** | **50** | |

SE1 has no true cubemaps. Reflection maps (`Models/ReflectionTextures/*`) stand in for that category, and one of them should replace a mask item if the owner prefers.

## 10. Assumptions, unknowns, alternatives, risks

**Assumptions and unknowns:**
- The HD `.tex` payload layout is unknown: pixel format (DXT/BCn likely, given the Fusion EULA list includes libsquish/nvDXT, but this is unverified), dimensions and mip storage.
- Whether HD `.tex` files carry separate normal/specular textures referenced from `.mtr` is unknown.
- The Classic archive mount and override order needs confirming from source.
- Whether Fusion HD content supersedes the standalone HD content (it carries more textures) is unknown.

**Alternatives:**
- (A) HD textures where matched, Classic plus AI elsewhere. This is the recommended option.
- (B) Classic plus AI only. Simplest legally and technically, but discards HD art.
- (C) Port HD models and levels. Rejected for scope and parity reasons.

**Risks:**
- HD art direction differs from Classic (color grading, added detail), which may conflict with plan §3's "recognizable visual identity".
- An undecoded proprietary format is needed to read HD textures. Writing a `CTSEMETA` reader is reverse engineering, which raises EULA questions (§11).
- False-positive matches; mitigated by category gating and verification.
- Mixed sources may look inconsistent within one level.

## 11. Legal flags (for Agent E / lead; no conclusions drawn)

1. Classic TFE and TSE ship an identical `license.txt` (Devolver Digital "Limited Software Warranty; License Agreement…", referencing `devolverdigital.com/eula`). A keyword scan found 3 lines matching "reverse", "modif" or "decompil"; I have not interpreted them. Agent E should review whether local extraction and conversion by the user is permitted.
2. The HD and Fusion EULA terms were not found as a single file. `Fusion/Help/External_EULA/` lists only third-party licenses (libsquish, nvDXT, zlib, Lua, Noto, …). The Steam subscriber agreement and Croteam/Devolver terms for HD and Fusion still need retrieving.
3. Reading `CTSEMETA` and signed archives may fall under anti-reverse-engineering clauses. Using HD-derived textures in a Classic runtime is a cross-product use. Both need a terms review.
4. The RT fork distributes a `TFE_RT_Textures.zip` of "upscaled textures and PBR textures" on its Releases page (`upstream/sultim-t_Serious-Engine-RT/README.md`). Agent E should note this precedent, not treat it as clearance.
5. Inventory documents enumerate proprietary file names. The policy on publishing mapping manifests (names plus hashes) in SSTRE-Manifests needs a decision.

## 12. Proposed experiments and success criteria

| ID | Experiment | Success criterion |
|---|---|---|
| E-B1 | Build a read-only `CTSEMETA` texture header reader (decode `CStaticTexture`/`CPlatformMip` fields) on the 50 HD counterparts | Dimensions and format decoded for at least 95% of the HD `.tex` files in the HD TFE `All.gro`; the result matches pixel count after decode |
| E-B2 | Run the mapping pipeline (steps 2–4) on the full Classic TFE set | Each of the 1228 textures gets a status; manual audit of 50 random `matched` entries shows ≥ 95% correct; zero cross-category auto-matches |
| E-B3 | Import into a representative level (Hatshepsut) via the RT override path | No UV or tiling regressions on matched brush textures (screenshot diff at fixed camera positions); fallbacks are logged |
| E-B4 | Model UV compatibility probe: compute UV-island fingerprints for 5 Classic MDLs vs HD meshes | Confirms or refutes "remade = incompatible" for the enemy, weapon and item categories |
| E-B5 | Byte-identity check of the archive hashes on a second machine or account | The same buildid gives the same SHA-256; otherwise add per-file entry hashes as the fingerprint |

## 13. Recommendation

- Use **HD textures as an optional, verified source for brush architecture, Netricsa images, crosshairs and some effects** (about 30% of Classic textures by exact path, mostly `Textures/Levels`).
- Treat **all character, weapon, item, plant, font, detail and technical textures as Classic-sourced**, processed through the RD-003 pipeline.
- Do **not** attempt HD model, world or shader import.
- Target the RT fork's override contract (virtual path + `.ktx2` + `_n`/`_rme`), or an equivalent in the chosen engine, so that pixel resolution is decoupled from SE1's 1024 px and mex limits.
- Gate any HD reading on the RD-007 terms review.

## 14. Decision dependencies

- [RD-001](./RD-001-engine-baseline.md): which engine, and whether its texture-override contract matches the RT fork.
- [RD-005](./RD-005-rendering.md): runtime texture formats (KTX2/BCn), PBR slot conventions.
- [RD-007](./RD-007-licensing.md): whether HD reading, cross-product use and mapping manifests are permitted.
- Owner: whether HD art direction is acceptable versus Classic fidelity, and approval of the 50-asset selection.

## 15. Next steps

1. The lead and owner review §9 and approve or edit the 50 candidates; a selection script fills the "by script" slots.
2. Agent E reviews §11.
3. Implement E-B1 and E-B2 in SSTRE-AssetCompiler, read-only and local, with synthetic fixtures for CI.
4. Freeze schema v0.1 after one real inventory run validates against it.
