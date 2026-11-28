# EXP-023: Effect, particle and UI texture recipes (POC-85, POC-86)

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | POC-85 (effect and particle texture classification and recipes), POC-86 (menu/UI inventory and UI recipes); feeds [RD-017](../research/RD-017-legacy-effects-reconstruction.md) §9.4, [RD-018](../research/RD-018-menu-ui-modernization.md), roadmap P3-5, P3-6, UI-1; proposed ADR-0016 |
| Status | partial: classification, recipes, QA and CI tests done; slice-v1 audit done; slice-v2 candidate built locally (deterministic); UI inventory and UI recipe QA run done. Not done: in-engine A/B of the slice-v2 candidate, brush-polygon blend metadata, AssetCompiler integration |
| Environment | Windows 11 Pro 10.0.22631; CPU only (no GPU job, no learned SR; the GPU lock was not taken). Python 3.10.11 venv of EXP-013 (numpy 2.2.6, Pillow 12.3.0, pytest 9.2.0, jsonschema). Compressonator CLI 4.6.0 (as EXP-013/EXP-019) for KTX2 encode and decode; KTX-Software 4.4.2 `ktx validate` |
| Inputs | slice-v1 of [EXP-019](EXP-019-vertical-slice-assets.md) (conservative profile; AI1 level-1 packs of TFE `01_Hatshepsut` and TSE `1_0_InTheLastEpisode` + `1_1_Palenque`); the owner's Steam Classic TFE and TSE installs (read-only); engine sources of SSTRE-Engine `sprint2/integration` @ `7eeed884` (read-only). No asset paths, hashes, texture names or images are published here (GATE-05) |
| Code | Remaster-Toolkit `m01/effect-recipes` @ `9d8a9a3` (game-agnostic). The game-specific usage extraction, audit, regeneration and inventory scripts are local (`G:\sstre-tmp\a3\driver\`), not in any repository |

## Goal and success criteria

1. Find out how the conservative slice treated effect and particle textures, with an early verdict on the lightning texture for track FXT (RDF-003).
2. Classify effect textures from reliable metadata (how the engine draws them and with which blend semantics), not from filenames or colours. Exceptions must be declarative with a reason.
3. Recipes for effect classes: conservative, non-generative, alpha-aware, independent alpha, no artificial sharpening, coverage-preserving mips, additive semantics kept, automatic QA fallback to the original. Synthetic CPU tests in CI.
4. Regenerate the affected slice textures as a local `slice-v2` candidate (slice-v1 untouched).
5. A menu/UI inventory for TFE and TSE (per-asset table local, counts here) and UI recipes: conservative, no generated or altered lettering, no outlines, transparency and layout kept, animation-compatible, QA fallback, ADR-0009 opt-in unchanged.

## Procedure

1. **Usage metadata** (local `usage.py`; reads engine source and the installs, writes per-texture records):
   - particle code: texture objects loaded with `SetData_t` and drawn with `Particle_PrepareTexture(&obj, PBT_*)` [SRC `Entities*/Common/Particles.cpp`];
   - entity classes: `.es` texture and model components paired by `AddAttachment*`/`SetModel`+`SetModelMainTexture` [SRC];
   - world model holders: the `EPT_FILENAME` properties "Model" and "Texture" of the `ModelHolder`/`ModelHolder2` classes, read as packed property IDs plus indices into the world's entity dictionary [SRC `EntityProperties.cpp`, `FileName.cpp`];
   - model files: the translucency type (`STT_*`) and visibility of each mapping surface of the first model mip (V009/V010 format) [SRC `Model.cpp` `MappingSurface::Read_t`].
   - blend semantics from the engine's blend functions [SRC `DrawPort_Particles.cpp`, `RenderModel_View.cpp`]: `PBT_ADD` = ONE,ONE → `additive`; `PBT_ADDALPHA` and model `STT_ADD` = SRC_ALPHA,ONE → `additive-alpha`; `PBT_BLEND`, `STT_TRANSLUCENT` → `alpha-blend`; `PBT_FLEX` = ONE,INV_SRC_ALPHA → `premultiplied`; `PBT_MULTIPLY`, `STT_MULTIPLY` = ZERO,INV_SRC_COLOR → `multiply-inverse` (black is neutral); `PBT_TRANSPARENT`, `STT_TRANSPARENT` → `alpha-test`.
2. **Audit** (local `audit.py`): every slice-v1 asset that the AI pack replaced and that is an effect by usage or has an alpha channel; enhanced output vs Classic source with the toolkit's effect QA metrics, alpha statistics, alpha coverage per mip for the PNG and for the decoded KTX2 mip chain, and BC7 decode error.
3. **Toolkit** (`m01/effect-recipes`): `effects.py` (classification, alpha-aware resampling, coverage-preserving mips, QA), an anti-ringing option in `resample.py`, an `effect` workflow and alpha-aware UI recipes in `workflows.py`, policy rules and implicit QA gates in the executor. `pytest` with synthetic images only.
4. **slice-v2 candidate** (local `regen.py`, `build-slice-v2.sh`): the effect recipe on the Classic sources of the affected slice-v1 assets, written into a copy of the AI1 packs (version 0.1.1), then VS-A's plan/package pipeline twice into `slice-v2` and `slice-v2-rerun` under the A3 workspace, `diff -r`, `ktx validate`.
5. **UI inventory** (local `ui_inventory.py`) and a run of the UI recipes on it (local `ui_recipe_run.py`, CPU, 2×).

## Results

### 1. Lightning: asset verdict (RDF-003)

- [EXP] slice-v1 contains **no lightning texture**: neither AI pack has one, and no `.tex` or `.ktx2` for it is in the slice. Classic and enhanced runtimes load the same Classic original. All particle textures and the whole `effects` category were `not-eligible` in the conservative profile, so **no particle texture was enhanced** in preview2.
- [SRC] The particle lightning is drawn with `PBT_ADDALPHA` (SRC_ALPHA, ONE). [EXP] Its texture has no alpha channel (alpha = 1 everywhere), black left and right edges and a gradient strip over its full height. It is correct only when blended additively. Any path that treats it as alpha-tested or opaque shows the whole quad as a hard-edged dark rectangle around the core, which matches the owner's "outlined PNG".
- Conclusion: the asset is not the cause. The cause is on the renderer side (track FXT reports an RT tuning list that forces this particle texture to alpha-tested geometry; EXP-021). The P3-5 condition on enhanced lightning textures is met trivially because none exist; with the new recipes the texture would be class `additive` (ADDALPHA without alpha = ADD) and processed without SR.

### 2. How slice-v1 treated effect textures

| Measure (slice-v1, effect textures by usage) | Value |
|---|---|
| Enhanced textures that are effects by usage metadata | 13 distinct (TFE 7, TSE 7, 1 shared): 11 `additive`/`additive-alpha` model surfaces (space-background sprites, a cut-scene flare, an enemy aura, 2 atlases that also have opaque surfaces), 2 `alpha-blend` model textures |
| Of these, processed with learned SR (L2) | 12 (the 13th fell to the conventional L1 rung); their path-based category was props, enemy, weapon or vegetation, so the conservative profile treated them as opaque surfaces |
| SR halo fraction on additive textures (output texels outside the min/max of their source footprint by > 2/255) | 5.7–14.7 % (median ~9 %) |
| Energy drift of the visible contribution (area-downscaled back to source size) | up to 5.9 % |
| Neutral lift (black interior becoming visible > 2/255) | ≤ 0.4 % of interior texels |
| Alpha MAE, all enhanced alpha textures (63 non-effect + effect) | max 0.011, median 0.0015 |
| Alpha coverage at 0.5 per mip, PNG box chain vs source (levels down to 1/8) | within 1.6 pp |
| Alpha coverage per mip, packaged KTX2 (compressonator chain) vs source | within 5.9 pp; larger deviations only at levels ≤ 8×8 texels |
| BC7 decode error vs the packaged PNG | RGB ≤ 0.008, alpha ≤ 0.008 (mean absolute, 0..1) |
| Premultiplied textures in the slice | none (KTX2 data-format flag `ALPHA_STRAIGHT`) |
| Colour under fully transparent texels | Classic: mostly black; enhanced: changed by the edge dilation of the AI1 recipes (a deliberate change, but it violates the P3-6 [ASM] limit of 4/255 for effect textures) |

- [EXP] The usage metadata found 242 TFE and 329 TSE textures with at least one recorded use. 29 of the 132 TFE and 81 of the 260 TSE enhanced slice assets have usage records; the rest are brush (world-polygon) textures, whose blend data is not parsed yet (gap, see Deviations).
- [EXP] Path categories disagree with usage: an additive texture can live in any directory, and the effects directory also holds opaque models. This is why usage metadata, not the path, must decide the effect class.
- [EXP] Observation for VS-A (not effect-specific): the packaged KTX2 albedo files are `BC7_UNORM` with transfer function `LINEAR` in the data format descriptor, while the content is sRGB-encoded. Whether RTGL1 relies on this flag was not checked here.

### 3. Classification and recipes (Remaster-Toolkit `9d8a9a3`)

- **Classification** `effects.classify(usages, stats, exception)`. The caller supplies usage records (`consumer`, `blend`). Rules, in order: a declarative exception (requires a reason) → `texel-lookup` consumer (code reads texels as data) → `lut` → no known usage → not an effect → only opaque/alpha-test usages → surface → one effect blend → that class (`additive-alpha` on a texture without alpha becomes `additive`, which is the same arithmetic) → several effect blends → `mixed`; `premultiplied` declared but RGB > A in more than 1 % of texels → `mixed`. An atlas used both as an effect and as an opaque surface gets the effect recipe for the whole atlas (`surface: true`).
- **Effect recipe** (`workflow=effect`): one resampling step, Lanczos 3 clamped to the min/max of each output texel's source footprint (anti-ringing: no overshoot, no halos or outlines, black stays exactly black); RGB and alpha filtered independently; straight alpha filtered premultiplied, so hidden colour never bleeds into visible texels; colour under fully transparent output texels copied from the original (P3-6); `premultiplied` keeps RGB ≤ A. No learned SR, diffusion or sharpening; the policy refuses them for effect profiles (`EFFECT_NO_LEARNED`) even if a caller adds them. `lut` and `mixed` keep the original (`EFFECT_LUT_ORIGINAL`, `EFFECT_MIXED_ORIGINAL`). The fallback chain is the original only, because the generic conventional rung (plain Lanczos) is not effect-safe.
- **Effect QA** (implicit gates, recorded by name in provenance, uncalibrated placeholders): neutral lift ≤ 0.2 %, halo fraction ≤ 0.2 %, energy drift ≤ 3 %, alpha MAE ≤ 0.03, hidden-colour drift ≤ 4/255 and alpha coverage per mip level ≤ 2 pp (both the P3-6 limits). Any failure → original, with reason codes `NEUTRAL_LIFT`, `HALO`, `ENERGY_DRIFT`, `ALPHA_DRIFT`, `HIDDEN_RGB_DRIFT`, `MIP_COVERAGE`.
- **Mips**: `effects.mip_chain` builds box mips that average straight alpha premultiplied and, for alpha-tested use, rescale each level's alpha so the coverage at the threshold equals level 0. On a synthetic thin-detail cutout, plain box mips lose 28 pp of coverage by 1/8 size; the preserving chain stays within 0.05 pp. The toolkit outputs only level 0; using the chain needs the packager (KTX2) or the engine (`.tex` mips are generated at load time), see Next steps.
- **CI**: 19 new synthetic tests, 103 in total, CPU-only, no game data: classification from declared blends (the same pixels drawn opaque are not an effect), ADDALPHA without alpha, lut/mixed/exceptions, premultiplied consistency, anti-ringing on a hard strip, hidden colour not bleeding, premultiplied and multiply invariants, coverage-preserving mips, end-to-end recipes for every class with schema-valid provenance, SR refused, a faulty resampler that lifts black falls back to the original, every effect class gets no SR/diffusion/sharpen/PBR step, glyph QA. `validate_repo` 0 errors.

### 4. slice-v2 candidate (local)

| Measure | slice-v1 (learned SR) | slice-v2 candidate (effect recipe) |
|---|---|---|
| Effect textures re-processed | — | 13 distinct (TFE 7, TSE 7) |
| Ladder | L2 SR | L2 effect recipe, 0 fallbacks |
| Halo fraction | 5.7–14.7 % | 0 |
| Neutral lift | ≤ 0.4 % | 0 |
| Energy drift | ≤ 5.9 % | ≤ 2.0 % |
| Hidden-colour drift (alpha effects) | changed by dilation | ≤ 0.0004 |
| Alpha coverage per mip (alpha effects) | — | ≤ 0.02 pp |

- [EXP] Build (CPU, after `wait-quiet`): plans identical run1 = run2 for both games (TFE 132 applied, TSE 260 applied, 0 rejected, the same counts as slice-v1); `slice-v2` and `slice-v2-rerun` `diff -r` identical; `ktx validate` 407/407 pass; the same file set as slice-v1 (TFE 272, TSE 534 files). Exactly 28 texture files differ from slice-v1 (14 asset entries, one `.tex` and one `.ktx2` each; one asset is in both games), plus the manifests and checksums. No raster memory change (same sizes).
- [EXP] Determinism: re-running the effect recipes in a fresh workspace (0 cache hits) gave 14/14 identical output hashes.

Trade-off: 2 of the 13 are atlases of a weapon and an enemy that also have opaque surfaces. With the effect recipe the opaque part loses the SR detail of slice-v1. `regen.py --mixed-surface keep` keeps slice-v1 for such atlases; region-aware processing (per-surface UV masks) would remove the trade-off and is not implemented.

### 5. Menu/UI inventory (POC-86)

Classification by the code that uses the texture: `.fnt` font files (glyph atlas), the HUD code (icons), the campaign-map code (icons and map backgrounds), the menu and Netricsa LCD objects (logo, cursor, background, grid decoration), Netricsa message files (`IMAGE` pictures), and `.tbn` level pictures used in the level and save lists.

| Class | TFE | TSE |
|---|---|---|
| Background (menu/LCD backdrop, map backgrounds) | 6 | 6 |
| Button / widget | 0 (menu gadgets are drawn text) | 0 |
| Icon (HUD, map) | 46 | 57 |
| Logo | 4 | 5 |
| Decoration (LCD grid) | 1 | 1 |
| Cursor | 1 | 1 |
| Font texture (glyph atlas) | 6 | 6 |
| Loading / selection pictures (level thumbnails) | 110 | 136 |
| Netricsa pictures | 71 | 104 |
| UI animation (multi-frame UI textures) | 0 (UI animation is code-driven) | 0 |
| **Total textures** | **245** | **316** |

- [EXP] There is no dedicated loading-screen texture: the loading screen draws the LCD backdrop and text [SRC `GameMP`].
- [EXP] The path-based fallback categories of the AssetCompiler mislabel many of these: 114 (TFE) and 304 (TSE) are not labelled `ui`/`font`, and 18 (TFE) and 4 (TSE) fall into categories that the conservative profile would send to SR (architecture, sky). They are safe today only because world-dictionary scopes do not reference them. UI eligibility must also come from usage metadata.
- [EXP] Alpha: fonts, logos and the cursor use soft alpha; most icons soft or cutout alpha; thumbnails and Netricsa pictures are mostly opaque. 181 (TFE) and 132 (TSE) have firstMip 0, so a Classic `.tex` cannot hold more pixels without changing the mex (EXP-013); raster use of enhanced UI needs an engine-side decision (UI1/lead).

### 6. UI recipes

- `ui_kind="text"`: the same alpha-aware, ringing-free resampling as the effect recipe, no learned SR, diffusion or sharpening (`UI_NO_LEARNED`), gates SSIM ≥ 0.9, alpha MAE ≤ 0.03, glyph alpha IoU ≥ 0.9, plus the halo and neutral-lift checks (an added outline is a halo). Fallback: original.
- `ui_kind="glyph-atlas"`: fonts keep the original (`UI_GLYPH_ATLAS_ORIGINAL`). Track UI1 confirmed that glyph UVs are pixel offsets divided by the texture width, so an upscaled atlas breaks glyph lookup without an engine change; resolution independence belongs to SDF/vector font work (POC-88).
- Glyph QA tests: a resampler that drops a letter stroke fails (`ALPHA_DRIFT`, IoU), one that adds a dark outline fails (`HALO`); both fall back to the original.
- The legacy `ui` workflow is unchanged (no silent quality change). Opt-in stays as ADR-0009 defines it: the AssetCompiler conservative profile keeps UI not-eligible; the HD Interface layer keeps its own opt-in.

- [EXP] **UI recipe run on the inventory** (local, CPU, 2×, `ui_kind="text"` for every class except fonts):

| Result | TFE | TSE |
|---|---|---|
| Accepted by the UI QA (L2) | 233 | 303 |
| Fell back to the original, font atlas by policy (`UI_GLYPH_ATLAS_ORIGINAL`) | 6 | 6 |
| Fell back to the original by QA: `ALPHA_DRIFT` (icon/picture alpha or glyph IoU) | 4 | 5 |
| Fell back to the original by QA: `ENERGY_DRIFT` (LCD grid decoration, one tiled backdrop) | 2 | 2 |
| **Total** | **245** | **316** |

  Every UI texture is either accepted or falls back with a recorded reason, which is the UI-1 condition at recipe level. Whether the accepted outputs look right in the menu is not yet checked in-engine, and the outputs are not installed anywhere (UI stays not-eligible in the conservative profile). The backdrop fallback is plausibly a wrap-tiled texture processed with clamp edges [ASM]; wrap metadata for UI textures is not provided yet.

## Deviations, modifications and failures

- Brush (world-polygon) texture blending was not parsed: it needs the brush-sector polygon stream and the world's texture-blending table. Effect-like brush textures (for example additive decals) are therefore not classified yet and kept the slice-v1 treatment.
- The `.es` pairing and world model-holder pairing are pattern reads of source and files; model attachments set by world data and textures assigned through scripts or other entity properties are not followed.
- The audit metrics and gate thresholds are first placeholders, set after one look at the data, not a human-audited calibration.
- First KTX2 decode used the DDS output in the wrong channel order (BGRA); corrected before the numbers above.
- The model-surface multiply semantics was first mapped to "multiply" (white neutral); the engine blend function is ZERO, INV_SRC_COLOR (black neutral), so a `multiply-inverse` class was added.
- No in-engine check of the slice-v2 candidate yet (needs a GPU lock session and a runtime overlay).

## Next steps and proposals for the lead

1. AssetCompiler: take effect and UI eligibility from usage metadata (or from an engine usage dump that records texture, consumer and blend at load/draw time, which also covers brush polygons), not from path categories; route effect classes to the toolkit `effect` workflow (proposed ADR-0016, declarative exceptions in SSTRE-Manifests).
2. Packager mip policy: use the coverage-preserving chain for alpha-tested textures in KTX2; for `.tex`, mips are generated at load time by the engine (owner: engine track).
3. In-engine A/B of the slice-v2 candidate (Vulkan, OpenGL, RT) at the space-background and cut-scene checkpoints, then merge into the slice if accepted.
4. Owner question: for atlases that combine an effect surface with an opaque surface, prefer effect-safe processing of the whole atlas (loses SR detail on the opaque part) or keep SR until region-aware processing exists?
