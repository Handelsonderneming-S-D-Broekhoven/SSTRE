# EXP-012: Classic `.tex` codec, AI extraction set, raster import path and HD source selection

> **Correction (2026-11-28, from [EXP-016](EXP-016-tex4096-crash.md)):** the raster import-path results show that high-density replacements *load* and tile correctly. They do **not** show that they are uploaded at full resolution: the shipped `tex_iNormalSize=9` caps uploads to a 512² area, and OpenGL uploads world textures as 16-bit unless `TEX_32BIT` is set. The '4096² crash' is a row-width buffer overflow in `FilterBitmap()` (width > 2048), fixed in EXP-016.

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | Sprint 2 track A1 (assets); RD-002 §16.6 follow-up; owner HD policy 2026-11-27 |
| Status | complete for tasks 1, 2, 4 and 5; task 3 complete except a mod-directory and a texture-size-cvar check |
| Environment | Windows 11 Pro 10.0.22631; Python 3.10.11 venv (`G:\sstre-tmp\assets\venv`): numpy 2.2.6, Pillow 12.3.0, pytest 9.2.0, jsonschema 4.26.0, reuse 5.0.2; NVIDIA RTX 4070 12 GB, driver 616.64; Classic-VK TFE runtime from EXP-001, copied to `G:\sstre-tmp\assets\runtime\cvk-tfe` |
| Inputs | Local read-only Steam installs: Classic TFE/TSE, HD TFE/TSE (builds as in RD-002 §3.1); EXP-008 local match data. No asset paths, hashes or images are published here (GATE-05) |
| Code | SSTRE-AssetCompiler branch `feature/tex-codec-source-selection` (`classic_tex.py`, `texio.py`, `texextract.py`, `source_select.py`, tests, `docs/classic-tex-codec.md`, `docs/source-selection.md`); umbrella `schemas/source-selection.schema.json` + `schemas/tests/source-selection/` |

## Goal and success criteria

1. A public GPL-3.0-only codec for Classic `.tex` (v3 + v4: header, frames, animations, alpha; mip 0 to RGBA) with `decode(encode(x)) == x`, and `encode(decode(file))` byte-identical for real files or explained per field.
2. An extraction set of 12–16 Classic TFE textures across the categories the AI track asked for, decoded to PNG plus JSON, with a `READY.json`.
3. A black-box answer to: can unmodified Classic-VK load a higher-resolution replacement with identical mex, and what are its limits?
4. A per-asset source selector (Classic / HD / HD-art) with manifest records and a schema, run on set1 and all EXP-008 verified pairs, and calibrated against the EXP-008 judgments.
5. An estimate and design for an optional HD-art layer, plus new legal questions.

## Procedure (exact, reproducible)

**Clean-room procedure (ADR-0006).** The codec author did not open engine source (`upstream/`, SSTRE-Engine branches). The author also did not open the research readers derived from engine source (`local-work/hd/scripts/cltex.py`, the Phase 0 probe scripts). The only inputs were:

- RD-002 §5;
- the EXP-007 v3 field-order correction;
- byte-level observation of local files: chunk tags, sizes implied by header fields, and visual inspection of candidate decodes.

The local probe scripts that did this are `G:\sstre-tmp\assets\probe\p1.py`–`p11.py`.

The HD research decoder (`hdtex.py`) was used only inside the local-only HD plugin. EXP-008 states that `hdtex.py` was derived from data-file observation, not from engine source.

The steps, in order:

1. **Format observation.**
   - Chunk walk over all `.tex` in both Classic installs, checking that every byte is accounted for.
   - Candidate 16-bit layouts for v3 (565, 1555, 5551, 4444 ARGB/RGBA) rendered as contact sheets. Their bit statistics were compared: bit 0 was set in 100% of pixels of every v3 file with flag 0.
   - v4 channel order checked visually (red flare, green palm, upright font).
2. **Round trip.** `sstre-ac tex-roundtrip <Classic TFE> <Classic TSE>` decodes and re-encodes every `.tex` in the top-level archives (`Mods/` excluded) and prints counts only. A second cycle compares the models.
3. **Set 1.**
   - A local selection file (`G:\sstre-tmp\assets\set1-selection.local.json`) holds the 16 TFE paths, their categories and the EXP-008 match context.
   - Command: `texextract.extract_set(...)` (equivalent to `sstre-ac tex-extract`). Output goes to `G:\sstre-tmp\assets\set1\`.
4. **Runtime test (GPU lock A1, 21:25:56–21:34:02).** Runs used the EXP-001 harness (`run-game.ps1`), copied as `probe\run-game-a1.ps1` and pointed at a private runtime copy. Settings: windowed 1280×720, single player, master server 127.0.0.1, `+level` start, PrintWindow capture of the game window only. No input was sent. Focus loss was not detected (the harness cannot detect it), and no screenshot showed interference.
   - Patterns: `probe\gen_patterns.py` writes **synthetic** patterns of our own as loose `.tex` files with our encoder:
     - per-texture ID patterns, to find which textures are visible;
     - a logical 8×8 checker with 1-px line probes, labelled "x1/x2/…", for scale tests.
   - Each original's mex, flags, frame count and animations are kept.
   - 13 runs: 11 Vulkan, 2 OpenGL. Levels: `02_SandCanyon` (Netricsa UI) and `TechTest`. The runtime was cleaned afterwards (0 loose files left).
5. **Source selection.**
   - The local HD plugin `G:\sstre-tmp\assets\hd-plugin\hd_export.py` wraps `hdtex.py` (copy SHA-256 `d3d02893…8f05`). It writes HD mip-0 PNGs, JSON metadata and companion `_nm`/`_gm`/`_ao`/`_hm` maps.
   - `probe\build_requests.py` builds 1376 requests: set1, all 759 EXP-008 verified pairs, 438 curate-tier pairs, 143 exact-path-only pairs and the 101 judged pairs.
   - `probe\run_metrics.py` computes the metrics with the public `source_select.compare` (6 processes, about 35 s).
   - `probe\run_select.py` applies the public `decide` and writes `G:\sstre-tmp\assets\manifests\sel-*.json` plus `summary.local.json`.
   - Every record was validated against the new schema.
6. **Checks.**
   - AssetCompiler: `python -m pytest` (with and without `SSTRE_SCHEMAS_DIR`), umbrella `validate_repo.py --root .`, `reuse lint`.
   - Umbrella: `validate_repo.py --root .`.

## Results ([EXP] unless labelled otherwise)

### 1. Codec

**Observed layout** (full table in AssetCompiler `docs/classic-tex-codec.md`):

- There are no chunk sizes; every length follows from earlier fields.
- **v4.** `FRMS` holds frames × W×H×(3 | 4) bytes: mip 0 only, R,G,B(,A), rows top-down. Flags bit 0 means 4 bytes per pixel. This held for 0 exceptions in 2,718 v4 bitmap files.
- **v3.** `FRMS` holds frames × frameSize bytes, made of ctMips levels of 16-bit words: RGBA5551 when flags bit 0 is clear, RGBA4444 when it is set. frameSize = 2·Σ mip pixels for 43/43 files.
- **`ANIM`.** Every file has `ANIM`/`ADAT`: a count, then per animation a 32-byte name field, float32 seconds per frame, n, and n frame indices.
  - The trailing bytes of the name field are uninitialised memory. They are preserved for exact round trips.
  - The single-frame default is "OnlyAnim", 0.02 s, [0].
- **Effect textures.** `FXDT` (effect payload) appears instead of `FRMS`, followed by `ANIM` and `BAST`/`DFNM` (base texture name).
- **Flags.** Values 0–3 were observed. Bit 1 is set on background/UI textures; its meaning is unknown [ASM].
- **fineMips.** In 84% of v4 files fineMips equals the full mip count of the smaller side.

**Round trip** (entry level, base archives):

| Install | `.tex` | v4 byte-identical | v3 byte-identical | effect byte-identical | model cycle equal |
|---|---|---|---|---|---|
| Classic TFE | 1229 | 1181/1181 | 29/29 | 19/19 | 1229/1229 |
| Classic TSE | 1576 | 1537/1537 | 14/14 | 25/25 | 1576/1576 |

All 43 v3 files convert to v4 with equal mip-0 pixels.

When a v3 file is re-encoded as v4, `encode(decode(file))` differs from the original in these fields, by design:

- the version (3 → 4);
- `TDAT` (ctMips and frameSize are dropped);
- the pixels (16-bit becomes 8-bit by bit replication; this is lossless and reversible);
- the stored mips (v4 keeps mip 0 only).

Alpha modes over both sets: opaque 2143, blend 556, cutout 62, none (effects) 44.

### 2. Extraction set 1 (local, `G:\sstre-tmp\assets\set1\`)

`READY.json` lists 16 textures, 0 missing; every record has `reencode_byte_identical: true`. Categories and sizes:

- tileable architecture (512², opaque);
- terrain ×2 (512² opaque; 256² with alpha);
- alpha vegetation (256², blend);
- enemy skin (256²);
- weapon (512²);
- UI text page (256²);
- HUD icon (32², alpha);
- crosshair (32², alpha);
- font page (256², alpha);
- detail (256²);
- bump (128²);
- specular mask (64²);
- sky panorama frame (512×256);
- animated effect (64², 23 frames);
- a prop with a verified HD counterpart at 2× pixels (EXP-008 verifier and this selector: R08 → HD).

Each JSON holds:

- stable asset ID, source archive, virtual path and source SHA-256;
- pixel size, mex, firstMip, fineMips and mip info;
- frames, animations, alpha mode, category;
- the EXP-008 match context;
- PNG hashes.

There are 60 files (2.6 MB). An `.alpha.png` is written for each alpha texture.

### 3. Raster import path (Classic-VK, unmodified engine binaries)

| Question | Result |
|---|---|
| Does a loose `.tex` override the archive copy? | **Yes.** Loose files under the game root (`<root>\Textures\…`, `<root>\Models\…`) took precedence over `.gro` entries: UI, fonts, brush and model textures all showed the ID patterns (both levels) |
| Identical mex at 2× / 4× density, same surfaces | **Yes, tiling unchanged.** Brush wall 128×64 → 256×128 → 512×256, floor 512 → 1024 → 2048 and column 128×256 → 512×1024 all loaded. The 8×8 logical grid and the origin cells sit at the same screen positions in the 1×, 2× and 4× screenshots; only the label/line density changes |
| Model textures | 2× (Colt 256 → 512, same mex) loads with an unchanged mapping |
| Changing mex instead | **Breaks model UVs.** The Colt at 1024 px with mex 512 → 1024 shows only the top-left quarter of the texture (cells 2× larger): model UVs are in mex units. **2D UI tolerates it**: the Netricsa picture at 1024 px with mex 256 → 1024 filled the same on-screen box correctly |
| Largest accepted | 2048×2048, 2048×1024 and 2048×4096 (8.4 Mpx) load. **4096×4096 (16.8 Mpx) crashes** the game during world load with 0xC0000005, on **both Vulkan and OpenGL** (CPU-side loader limit, [ASM]: between 8.4 and 16.8 Mpx, or 32 vs 64 MB RGBA) |
| Mips | v4 stores mip 0 only; the runtime regenerates mips. The 1-px line probes minify without garbage toward the horizon in every run, at 1×, 2×, 4× and 16× |
| Vulkan vs OpenGL | 4× configuration: visually equivalent screenshots on both APIs |

**Headroom without engine change.** The maximum density with identical mex is 2^firstMip, further capped at 8 Mpx.

| Set | Textures | At least 2× | At least 4× |
|---|---|---|---|
| TFE | 1209 | 1013 (84%) | 1001 (83%) |
| TSE | 1541 | 1334 (87%) | 1271 (82%) |

firstMip is 0 for:

- 115/142 TFE UI textures;
- 15/66 player textures;
- 42/149 effects;
- 6/457 architecture textures.

**Answer for E1 (engine track).** No engine change is needed for 2×–4× raster replacements of about 83% of textures: use a loose v4 `.tex` with identical mex, up to 8 Mpx. Engine work is needed for three things:

1. a guard or fix for the >8 Mpx crash;
2. density above 2^firstMip on models (a per-texture UV scale or a resolution-independent mex);
3. a confirmed override root for mods instead of the game root (`Mods/<x>` was not tested).

Not verified: whether the texture-size cvar `tex_iNormalSize` caps uploads above 1024 px. The cvar name was read from the runtime's `Scripts/GLSettings/*.ini`; its default value was not determined. Also not verified: whether the driver-side upload is compressed (`tex_bAlternateCompression`). The 1280×720 view cannot resolve the difference. A close-up or magnified test is still needed.

### 4. Source selection

**Records.** 1376 local records (1368 assets plus 8 extra judged pairs); **0 schema errors**. Rules R01–R12 plus the M01 companion-map modifier are documented in AssetCompiler `docs/source-selection.md`. Default thresholds:

- layout SSIM 0.55;
- same-art SSIM 0.80;
- ΔE (low-pass) 6;
- histogram intersection 0.80;
- equivalent PSNR 48 dB;
- lossy PSNR 40 dB;
- same-size blockiness excess 0.06;
- upscale artefact index 0.20;
- detail energy 0.10;
- ratio ≥ 2;
- same-size sharpness gain 1.15× (with a Classic sharpness floor of 0.001).

**Calibration against the 101 EXP-008 judgments.**

- W: 30 → `classic_fallback`, 1 → HD-art queue (unverified, opt-in only).
- R: 19 → fallback, 4 → HD-art queue.
- S: 2 → HD, 3 → Classic + HD maps, 29 → Classic (lossy copies), 8 → fallback (unverified), 5 → HD-art queue (low-pass ΔE 8–16, i.e. visible colour shifts that the 128-px judgments missed).
- **No W or R pair was auto-accepted.**
- Layout SSIM ≥ 0.55 keeps 45/47 S, 9/23 R and 3/24 W pairs.
- Results were insensitive to ΔE 4–8 and same-art SSIM 0.75–0.80. The defaults were kept.

**Verified pairs (n = 759).**

| Decision | Pairs | Rules |
|---|---|---|
| Classic | 653 | 557 R11 lossy copy, 83 R06 identical or ≥ 48 dB, 5 R09, 3 R04, 3 R12, 2 R05 |
| Classic + HD normal/gloss maps | 23 | — |
| **HD** | **14** | 12 R08 true upscales, 2 R10 same-size sharper |
| HD-art queue | 69 | — |

Same-size verified pairs have a median PSNR of 31.8 dB, a median blockiness excess of 0.18 and 79 bit-identical copies.

**Per category (all 1368 assets).** The `n` column counts all assets; the decision columns count only assets with an HD candidate.

| Category | n | HD | Classic + maps | Classic | HD-art queue | Fallback |
|---|---|---|---|---|---|---|
| architecture | 631 | 5 | 3 | 441 | 52 | 130 |
| props | 156 | 5 | 11 | 69 | 34 | 37 |
| effects | 151 | 0 | 0 | 53 | 36 | 62 |
| ui | 213 | 0 | 0 | 18 | 2 | 193 |
| items | 52 | 0 | 1 | 34 | 12 | 5 |
| player | 52 | 0 | 2 | 14 | 2 | 34 |
| enemy | 34 | 2 | 6 | 10 | 4 | 12 |
| sky | 34 | 2 | 0 | 1 | 1 | 30 |
| weapon | 22 | 0 | 0 | 5 | 4 | 13 |
| other / detail / terrain / font / technical / vegetation | 23 | 0 | 0 | 10 | 4 | 9 |

Set1 decisions:

- prop → HD (R08);
- architecture wall and terrain grass → Classic (R11 lossy copy);
- crosshair → Classic (R06 identical);
- detail → HD-art queue;
- font and specular mask → Classic (R01);
- the other 9 → fallback (no candidate or unverified).

### 5. HD-art layer

**Estimate** (selector R07 over EXP-008 data; both Classic sets): **151 candidates**, 45 of them with more pixels.

| Category | Candidates | With more pixels |
|---|---|---|
| architecture | 52 | 11 |
| effects | 36 | 8 |
| props | 34 | 21 |
| items | 12 | 2 |
| enemy | 4 | — |
| weapon | 4 | — |
| other | 4 | 2 |
| player | 2 | — |
| ui | 2 | — |
| sky | 1 | 1 |

In addition there are **122 UI/Netricsa exact-path pairs** whose HD version is higher-resolution but re-laid-out (layout SSIM < 0.55). They are not drop-in replacements for 3D, but 2D UI tolerated a mex change in task 3. They would form a separate "layout-changing UI art" sub-layer that needs text and layout review.

**Representation.**

- A source-selection record with `decision.result = hd_art_candidate`.
- The base build keeps Classic (`base_source: classic`).
- The record carries `hd_art {candidate_id, status: pending_owner_opt_in | opted_in | approved | rejected}` and `requires_opt_in: true`.

**Opt-in.** Two steps:

1. A global switch, `hd_art_opt_in` in the policy, recorded in every record.
2. Per-asset approvals, stored as a curated list in SSTRE-Manifests (local until GATE-05). The approvals feed a separate optional layer, applied after the base layer.

## Deviations, modifications and failures

- **Crash.** The 4096×4096 replacement crashed the runtime (Vulkan and OpenGL). This is recorded as a result.
- **Not tested.** The mod-directory override (`+game`) and the effective cap from `tex_iNormalSize` were not tested.
- **Selector fixes during calibration.**
  - Initial broadcast errors on tiny textures: fixed by resizing both layout images to a common size.
  - ΔE was first computed per pixel, which mixed structural detail into colour drift. It now uses a low-pass image (≤ 32 px, ≥ 8× reduction).
  - Raw blockiness rejected every BC upscale. It now uses `artefact_index` = excess / linear scale.
  - Smooth glows produced spurious R10 "sharper" hits. Fixed with a Classic sharpness floor.
- **HD-art estimate is approximate.** It rests on EXP-008's single best candidate per asset and on 128-px human judgments. The SSIM/ΔE thresholds were calibrated on 101 pairs only.
- **Commit split.** AssetCompiler commit `6723cd2` registers the `select-source` CLI entry, whose module only arrives in `32e1ed3`. The final branch state is consistent.

## Interpretation

- [EXP] Classic textures can be decoded and re-encoded losslessly. The AI track can work on PNGs and return v4 `.tex` files with identical mex.
- [EXP] The raster import path for 2×–4× textures works today without engine changes. The main limits are 2^firstMip (models and some UI) and the >8 Mpx crash.
- [EXP] Most verified HD matches are lossy copies. Only 14/759 beat Classic, and 23 contribute companion maps. This confirms RD-002 §16.4 with per-asset evidence, without a categorical rule.
- [ASM] Normal and gloss maps can only be used with a future material path in the engine; the raster baseline ignores them.

## Impact on ADRs, dossiers and backlog

- **RD-002 §5:**
  - add the v3 pixel formats (5551/4444), the `ANIM` record layout and the "no chunk sizes" note;
  - mark §16.6 Q2 as answered by policy (per-asset selector).
- **RD-005 / engine backlog (E1):**
  - fix or guard the texture size crash;
  - define a mod override root;
  - consider a per-texture UV scale for firstMip-0 model textures;
  - test `tex_iNormalSize` and upload compression.
- **RD-007:** the new questions below.
- **Schema:** `source-selection.schema.json` is a proposal. The RD-002 §16.5 inventory changes remain unapplied.

## Open questions

1. **Owner.** Approve the HD-art layer as an opt-in layer, and decide whether the 122 re-laid-out UI images form a sub-layer.
2. **RD-007 (new).**
   - Is opt-in local use of HD *artwork* (as opposed to same-content copies) in a Classic-engine build covered by the HD EULA?
   - May source-selection records, approvals and curated HD-art lists that reference HD asset IDs be published after GATE-05, given that they encode artistic choices from Croteam's HD work?
   - Can HD companion maps be combined with Classic albedo (a cross-product derivative)?
   - May the local HD plugin (CTSEMETA reader) ever be published under an interoperability exception?
   - Are metrics derived from HD pixels publishable facts?
3. **E1.** The loader limit and the model mex coupling (above).
