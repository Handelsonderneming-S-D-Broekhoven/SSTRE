# EXP-008: HD asset decoding, matching ladder, dependency mapping and HD mesh/UV probe

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | RD-002 follow-up (E-B1, E-B2, E-B4); owner direction "do not abandon HD on exact-path stats" |
| Status | partial (texture decode and matching complete for standalone HD; Fusion pixel decode, semantic stage (e) and model conversion not completed) |
| Environment | Windows 11 Pro 10.0.22631; Python 3.10.11 venv; numpy 2.2.6, Pillow 12.3.0, SciPy 1.15.3, torch 2.6.0+cu124, transformers 5.20.2; NVIDIA RTX 4070 12 GB, driver 616.64 |
| Inputs | Local read-only Steam installs: Classic TFE/TSE, HD TFE/TSE (incl. DLC TFE / Legend of the Beast archives), Fusion 2017 (builds as in RD-002 §3.1). No hashes or per-asset paths are published here (GATE-05). Embedding model: `facebook/dinov2-base`, revision `f9e44c814b77203eaa57a6bdbbd535f21ede1415`, license `apache-2.0` per the Hugging Face model API (`cardData.license`), `model.safetensors` SHA-256 `d73036b56966966d07975d696bde331762f37297e2f095de8cea0040c3aa0841`. Weights stay in `local-work/hd/models`. |

All scripts, inventories, thumbnails, candidate lists and judgments are local-only in `<workspace>/local-work/hd/` (`scripts/`, `out/`). No game binaries were run or disassembled. All decoding was in memory from the zip archives. Only 128 px thumbnails and diagnostic contact sheets were written, and only to local-work.

## Goal and success criteria

1. Decode HD `.tex` dimensions, pixel format and mip-0 pixels. Target from RD-002 E-B1: at least 95% of HD TFE textures.
2. Measure a matching ladder: (a) exact path, (b) improved normalization, (c) perceptual hash, (d) image embeddings, (e) semantic (optional). For each stage, record candidates, human-checked precision (at least 60 pairs), a recall proxy and the per-category yield beyond exact path.
3. Recover texture references and slot roles from HD `.mdl`/`.bmf`/`.mtr`, and Classic model-to-texture links.
4. Probe HD mesh and UV extraction with one small proof, and estimate the effort for conversion or reprojection.
5. Recommend a per-category source strategy and mapping-record fields.

## Procedure (exact, reproducible)

Run from `local-work/hd/scripts` with `../venv/Scripts/python.exe`:

| Step | Script | What it does |
|---|---|---|
| 1 | `census.py`, `hyp*.py`, `hypbc*.py`, `bc3seg.py` | Format hypotheses: size arithmetic, byte entropy per segment, predictor search scored by image smoothness, then visual inspection of renders |
| 2 | `hdtex.py` (decoder), `cltex.py` (Classic reader per Croteam `Graphics/Texture.cpp:677-900` @ `b408e88`) | Decoders |
| 3 | `build_inv.py classic_tfe hd_tfe classic_tse hd_tse` | Decode every `.tex` and write a 128×128 RGBA thumbnail plus metadata (later archives override earlier ones) |
| 4 | `qa_sheet.py` | Random visual QA, 8 thumbnails per HD format |
| 5 | `features.py` | 63-bit pHash (DCT of 32×32 grey), 64-bit dHash, HSV 12×4×4 histogram, and DINOv2-base CLS + mean-patch embeddings (224 px bicubic from the thumbnail, alpha composited over mid-grey, fp32, CUDA) |
| 6 | `match.py` | Ladder stages a–d; category gate; colour-role HD pool |
| 7 | `calib.py` | Score distributions and recall proxy |
| 8 | `sample.py` → `judge.py` | 80 stratified, stage-blinded pairs |
| 9 | `verify_all.py` → `holdout_judge.py` | Verifier plus 21 hold-out pairs |
| 10 | `hires_sheet.py` | 16 higher-resolution exact-path pairs |
| 11 | `scale.py`, `fidelity.py`, `gain.py` | Resolution and fidelity of matches |
| 12 | `deps.py`, `roles.py` | `RFIL`/`IDNT` tables and role labels |
| 13 | `bmf_probe.py` … `bmf_uv.py` | Mesh/UV proof |
| 14 | `fusion_census.py`, `fusion_try.py` | Fusion probes |

Human judgments were made by the agent viewing local contact sheets (Classic left, HD right; stage labels hidden on the 80-pair set). Three labels were used:

- **S**: same content and layout; usable as a drop-in source after checks.
- **R**: same object or material, but redrawn, recoloured or re-laid-out; reference or curation only.
- **W**: wrong.

## Results ([EXP] unless labelled otherwise)

### 1. HD `.tex` (CTSEMETA) decoding

**Format findings** (from data-file observation only; no public specification exists, see [DOC] below):

- **Header.** Magic `CTSEMETA`, then marker `0x1234ABCD`, then a version string. A reflection type table follows: `DTTY` entries giving type id, name, a kind (primitive / typedef / class / pointer / array / container) and, for classes, `STMB` member lists. Member names are stripped to numbers. `OBJS` holds the serialized objects and `METAEND` is a **trailer**, not a header end. Other tables:
  - `RFIL`: referenced files, as entries `(index, 0, len, string)`.
  - `IDNT`: identifiers, as entries `(index, len, string)`.
- **Texture object.** The `CStaticTexture`/`CBaseTexture` payload holds `width:u32, height:u32, flags:u32, format:u32`, then `STAR <len:u32>` followed by the full mip chain.
- **Payload transform (standalone HD only).** The mip chain is **plane-split and delta-coded for compression**:
  - **BC1** (format 9): whole-chain planes `[c0 u16 × Nblk][c1 u16 × Nblk][indices u32 × Nblk]`. The endpoints are a running sum (stream delta) of u16 values. The indices are raw.
  - **16-byte block formats** (formats 10 and 11): the same colour planes, then the alpha half of each block as raw interleaved 8-byte records. Format 10 decodes as BC3. Normal maps (flag `0x80`) are BC3 with X in alpha and Y in green ("DXT5nm"-style).
  - **Uncompressed formats**: k separate 8-bit planes, each covering the whole mip chain and each stream-delta coded. k = 1 for formats 7/8, 2 for format 6, 3 (RGB) for formats 2/4, and 4 (RGBA) for formats 3/5/12. Plane order R, G, B, A was validated on a prop texture of known colour.
- **Fusion.** Different format enum (adds format 15). High mips are split into paired `--Big.tex` files (flag bit `0x4000000` marks a low-res resident stub). BC1 pixels are **standard interleaved BCn** with no plane/delta transform (3/3 samples rendered correctly raw).

**Coverage:**

| Set | `.tex` | Header parsed | Pixels decoded (mip ≥128 px or mip 0) | Failures |
|---|---|---|---|---|
| HD TFE (standalone + patches) | 1623 | 1623 | **1621 (99.9%)** | 2 empty lightmap stubs (no payload) |
| HD TSE (incl. DLC TFE, LotB) | 3366 | 3366 | **3362 (99.9%)** | 4 empty stubs |
| Fusion HD TFE / HD TSE packs | 2124 / 3294 | 2124 / 3294 (100%) | not attempted at scale (enum mapping and `--Big` merge not implemented) | n/a |
| Classic TFE / TSE (`cltex.py`) | 1228 / 1501 | all | 1209 / 1477 | 19 / 24 procedural FXDT textures (no bitmap, expected) |

**Visual QA.** 87 random HD TSE thumbnails covered all 11 formats, at least 7 per format. All rendered as plausible images; normal maps appear grey in RGB, as expected for DXT5nm. One earlier full-resolution render of a format-12 lightmap was partially garbled, so **format 12 (lightmaps/skies) is "probably correct" and not verified**. Decoding is about 90 s for all ~6,600 textures on CPU when decoding the smallest mip at least 128 px.

### 2. Matching ladder

The pool is the union of the HD TFE and HD TSE standalone sets. Stages (c) and (d) search only HD textures with a colour role, within the same category group (§4).

| Stage | Rule | Classic TFE (1209 decoded) | Classic TSE (1477) |
|---|---|---|---|
| (a) exact normalized path | RD-002 normalization | **393** (RD-002 baseline vs HD TFE only: 377) | **400** |
| (b) improved normalization, new | drop `textures/`, `hd/`, `sources/` path parts; strip role suffix `_cm/_nm/_gm/...`, `_batched`, `--big`; level 2 also strips trailing digits and underscores; fuzzy stem ≥0.75 within the same model folder | +166 | +219 |
| (c) perceptual, new | in-group top-1 pHash ≤ 12 | +62 | +74 |
| (d) DINOv2, new (cos ≥ 0.85 / 0.75–0.85 / 0.65–0.75) | in-group top-1 | +20 / +61 / +118 | +14 / +96 / +171 |
| no candidate | — | 389 | 503 |
| (e) semantic (CLIP/VLM labels) | — | **not run** (time; optional) | — |

**Human-checked precision.** 80 stratified, stage-blinded pairs:

| Stage | n | S | R | W | S-precision | S+R |
|---|---|---|---|---|---|---|
| a | 14 | 11 | 3 | 0 | 0.79 | 1.00 |
| b | 18 | 10 | 2 | 6 | 0.56 | 0.67 |
| c | 10 | 2 | 5 | 3 | 0.20 | 0.70 |
| d ≥ 0.85 | 14 | 3 | 2 | 9 | 0.21 | 0.36 |
| d 0.75–0.85 | 14 | 1 | 6 | 7 | 0.07 | 0.50 |
| d 0.65–0.75 | 10 | 0 | 4 | 6 | 0.00 | 0.40 |

**Pair-level verifier.** The rule is DINOv2 score ≥ 0.90 **and** pHash ≤ 16, applied to the best candidate from any stage.

- In-sample: 18/19 S.
- **Hold-out (21 fresh pairs passing the verifier): 20 S, 1 R → 95% S-precision** (Wilson 95% CI about 0.77–0.99).
- An additional 16 exact-path pairs where the HD copy has more pixels: 6 S (true upscales, same layout: statue/prop sheets and glows), 8 R (redrawn: doors, wall panels, level-preview images), 2 W.
- **Total pairs human-checked: 117.**

**Recall proxy.** For the 793 exact-path pairs whose HD side has a colour role, how often does a pixel-only search find that same HD texture?

- DINOv2: top-1 **87%**, top-5 **93%**.
- Perceptual: top-1 **73%**, top-5 76%.
- By category (DINOv2 top-1): architecture 94% (462/490), UI 66% (125/190); for UI the perceptual top-1 is only 12%, because of many near-identical Netricsa images.

**Calibration** (exact-path pairs vs random same-group pairs):

| Measure | Exact-path pairs | Random pairs |
|---|---|---|
| pHash median (p25–p75) | 2 (0–22) | 32 (30–34) |
| Embedding median | 0.962 | 0.242 |

Per pair, only 0.3% of negatives reach an embedding score ≥ 0.75. But the top-1 is taken over hundreds of candidates, which explains the low (d) precision.

**Verified yield** (verifier passed, by stage of origin):

| Category group | Classic TFE: n / verified (a+b+c) / curate-tier | Classic TSE: n / verified / curate-tier |
|---|---|---|
| Architecture (`Textures/Levels` etc.) | 457 / **283** (255+1+27) / 65 | 467 / **190** (183+0+6, +1 d) / 78 |
| Effects | 149 / 32 / 34 | 172 / 35 / 44 |
| Props (other models) | 120 / 30 / 8 | 237 / 70 / 42 |
| Items | 44 / 15 / 2 | 64 / 28 / 6 |
| Enemies | 69 / 9 / 3 | 123 / 12 / 7 |
| Player | 66 / 8 / 15 | 101 / 8 / 20 |
| Weapons | 31 / 3 / 5 | 38 / 4 / 7 |
| UI / Netricsa | 142 / 11 / 18 | 190 / 9 / 50 |
| Sky | 111 / 2 / 24 | 27 / 1 / 5 |
| Technical (reflection/specular) | 10 / 0 / 0 | 10 / 0 / 0 |
| Other | 10 / 2 / 3 | 48 / 7 / 2 |
| **Total** | **1209 / 395 (32.7%) / 177** | **1477 / 364 (24.6%) / 261** |

Beyond exact path, the ladder adds **+105 (TFE) and +108 (TSE)** verified same-content sources. Notably, it finds verified sources for items, player, enemies and weapons, where RD-002 recorded 0 by exact path. "Curate-tier" means the best candidate has an embedding score ≥ 0.75 but fails the verifier. Those are mostly R (redrawn/related) and need human curation.

### 3. Value of matched HD textures (resolution and fidelity)

- **Resolution.** Verified same-content matches have the **same pixel dimensions as Classic in 96% (TFE: 378/395) and 90% (TSE: 326/364)** of cases. Only 9 (TFE) and 24 (TSE) have more pixels; 23 of those 24 TSE cases are props or architecture.
- **Fidelity.** 275 same-size verified pairs were compared at native resolution:
  - 33 (12%) are bit-identical; all are uncompressed plane formats.
  - 231 are BC1/BC3 re-encodes.
  - 11 are other non-identical uncompressed copies.
  - PSNR vs Classic: p5 25.1, p25 30.4, **median 32.5**, p75 35.3 dB.

  **Most "matched" HD textures are lossy DXT copies of the Classic art. They are worse than the Classic source, not better.**
- **Exact-path pairs where HD has more pixels.** These number 87 (TFE) and 132 (TSE) of the colour-role exact pairs; 172 of the 219 are UI/Netricsa. The 16-pair sample shows most are redrawn (R), with a minority of true upscales (S).
- **Curate-tier with more pixels.** 86 / 177 (TFE) and 145 / 261 (TSE).
- **HD companion maps.** Verified matches rarely have HD companion maps: `_nm` 6 / `_gm` 5 of 395 (TFE), and 17 / 22 of 364 (TSE).

### 4. Dependency and role mapping

- **References.** `RFIL` tables parsed for 100% of HD `.mdl`/`.bmf`/`.mtr`/`.wld`/`.rsc`/`.pfx`/`.ep` files. **1437/1621 HD TFE (88.6%) and 3035/3362 HD TSE (90.3%)** textures are referenced by at least one HD resource. 858 and 1852 respectively are referenced by a material or mesh (`.mtr`/`.bmf`/`.mdl`).
- **Role labels.** Explicit labels from suffix convention plus format flag: **550/1621 (33.9%) TFE and 1311/3362 (39.0%) TSE**. The rest are "albedo (implicit)", mostly carried-over Classic textures.

  | Role | TFE | TSE |
  |---|---|---|
  | normal | 129 | 344 |
  | gloss/spec (`_gm`) | 51 | 187 |
  | mask | 29 | 124 |
  | ao | 11 | 21 |
  | height | 3 | 3 |
  | translucency | 2 | 5 |
  | illumination | 4 | 11 |
  | opacity | 1 | 3 |
  | albedo (`_cm`, sky faces) | 320 | 613 |

  The `_nm` suffix and the BC3 normal flag `0x80` agree 473/473, and no flagged texture lacks the suffix.
- **Slot names are not recoverable from strings.** `IDNT` holds only generic argument names: "Texture", "Texture 1..3", "bump offset U/V", "diffuse color", "alpha threshold". Shader slot semantics live in shader classes whose member names are stripped. Binding a texture to a slot therefore needs object deserialization of `CShaderArgValTexture`, which was not done. Roles currently rest on naming and pixel evidence.
- **Classic model to texture links.** Only 3/359 Classic TFE `.mdl` files contain `.tex` strings. Textures are bound by entity code ([SRC] `.es` sources, e.g. `SetModelMainTexture`) and by `.amc` animation/config scripts (23 files, 93 `.tex` references). Model-level path correspondence (RD-002 `pathmap.json`): Classic TFE `.mdl` exact path in HD TFE 56/359, Classic TSE 171/630.

### 5. HD mesh and UV probe (one proof)

The smallest HD TFE `.bmf` (a static prop):

- Index array: `CStaticArray<UWORD>`, raw u16, **not delta-coded**; 948 indices = 316 triangles.
- Vertex buffer: a 13 664-byte structure-of-arrays block of **plain float32** streams: position (float3), normal (float3), a [0,1] float stream (probably tangent or colour), a zero block (probably skin data), then **UV float2 last**.
- The vertex count (244) was inferred by search: UV range [0.01, 0.99], **0 degenerate UV triangles**.
- Rendered locally, the UV atlas and the front projection are coherent (images in local-work only).
- Not decoded: the vertex-format descriptor, multiple sections and LODs, skin weights and bones (`.skl`), animations (`.ans`/`.anh`), and `.mdl` configs, attachments and mechanisms.

## Deviations, modifications and failures

- Stage (e), semantic CLIP/VLM labelling, was not run (optional; time).
- Fusion pixel decode at scale was not implemented. Only header parsing and a 3-sample raw-BC1 check were done.
- Format-12 decode is not fully verified (one partially garbled lightmap render).
- The precision samples are small. Per-stage CIs are wide (e.g. stage c, n = 10). The verifier precision comes from a hold-out of 21.
- Judgments were made on 128 px thumbnails. Fine differences (e.g. text, small details) can be missed; a full-resolution pass is needed before any build uses them.
- Failed hypotheses (recorded as results):
  - per-field (R5/G6/B5) endpoint deltas;
  - left/up/average/MED/gradient 2-D predictors;
  - Laplacian-pyramid predictor;
  - per-channel row deltas on interleaved 32-bpp data.

  Only the whole-chain plane split with u16 (BC) or u8 (planes) stream delta reproduced clean images.
- **Workspace incident (environment failure).** The `L:` volume reached 100% (233 GB) during the run, mostly from data outside local-work (local-work totalled about 8 GB, of which this experiment used 5.4 GB). One diagnostic image write failed with ENOSPC (`fusion_try.py`) and succeeded on re-run once space was freed. A `pip uninstall` also failed with ENOSPC, so `torch`/`torchvision` were removed directly from the venv after the embedding stage. Versions are recorded in `out/pip-freeze.txt`; reinstall from the cu124 index to reproduce `features.py`.
- **Location change (owner-approved, 2026-11-27).** After the run, the large local outputs (`models/`, `out/` with inventories, thumbnails, features, candidate lists and judgments, and `venv/`) were moved from `local-work/hd/` to the temporary work area `G:\sstre-tmp\hd\`. The scripts remain in `local-work/hd/scripts/`. To re-run them, point their hard-coded `...\local-work\hd\out` and `...\models` paths at `G:\sstre-tmp\hd\`, and set `HF_HOME=G:\sstre-tmp\hd\hf`, `TORCH_HOME=G:\sstre-tmp\hd\torch`, `TEMP/TMP=G:\sstre-tmp\hd\tmp`. The same rules apply: nothing from game data goes into any repo.

## Interpretation

- [DOC] No public specification or tool exists for the SE3-era `.tex` format. A web search on 2026-11-27 found only the unanswered r/Croteam thread cited in RD-002, plus Classic-only tools. The decoder here is original, derived from data-file analysis only.
- [EXP] The HD texture format is fully decodable for standalone HD. A clean-room reimplementation in AssetCompiler is small (about 300 lines), but it is reverse engineering of a proprietary data format and must pass the RD-007/GATE review first. [ASM] It may fall under EULA terms.
- [EXP] Exact path is a poor proxy in **both** directions:
  - It overstates value: most same-path HD textures are lossy re-encodes of Classic art, at the same resolution.
  - It understates coverage: normalization and pixel verification add about 105–108 verified sources per game, including models.
- [EXP] Embeddings are excellent for **retrieval** (93% top-5 recall) but not sufficient for **acceptance** (21% S-precision at ≥ 0.85). Use them to generate candidates, and accept automatically only with a pixel-level verifier, or route the candidate to curation.
- [ASM] The real HD value lies in:
  1. a minority of true upscales (props/architecture, about 2–5% of Classic textures);
  2. redrawn HD textures for architecture and UI, which need art-direction approval;
  3. HD-only normal and gloss maps where the albedo layout is unchanged (rare, under 3% of verified matches);
  4. remade character, weapon and item art that belongs to new UV layouts.
- [ASM] For item 4, reprojection or baking requires registering two different meshes: the HD skinned mesh and the Classic vertex-animated MDL in a reference frame. That means pose matching, scale alignment and a ray-cast bake per texel, followed by manual cleanup of seams and of areas that exist in only one mesh. Estimated effort: about 2–4 person-weeks for a tooling prototype, plus about 0.5–2 person-days per character/weapon for curation. Full HD model import into SE1 (MDL or SKA) additionally needs skeleton/animation decode and retargeting, plus gameplay-parity work (collision boxes, attachment indices, animation names used by entity code; RD-002 §6.3). That remains a separate high-risk project.

## Impact on ADRs, dossiers and backlog

- RD-002 §6/§7/§13 revised (Phase 1 update section).
- New backlog candidates:
  - AssetCompiler HD `.tex` reader (clean-room spec from this report, after legal review);
  - verifier-gated mapping;
  - Fusion enum mapping;
  - `CShaderArgValTexture` deserialization for slot roles;
  - a reprojection prototype for one enemy.
- The schema changes are proposed in RD-002 (not applied).

## Open questions

1. Owner: should redrawn (R-tier) HD architecture and UI textures be offered as an optional "HD art" layer, given that they change the look?
2. Owner: is an HD source that is lossy at the same resolution ever preferable to Classic plus AI upscaling? (Recommendation: no.)
3. Legal (RD-007): does a CTSEMETA reader in the AssetCompiler fall within the HD/Fusion EULA? Are the HD-only normal/gloss maps usable cross-product?
4. Which edition is authoritative when both standalone HD and Fusion carry a texture? Fusion is standard BCn with split mips, while standalone uses the transform.
