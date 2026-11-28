# RD-011: Realtime, baked and hybrid hex-tiling

| Field | Value |
|---|---|
| Dossier | RD-011 |
| Author | Track DOC-R (roadmap/planning), 2026-11-28 |
| Date | 2026-11-28 |
| Status | **Draft.** Desk research and source reading only. Nothing was implemented or measured. |
| Feeds | backlog POC-50..53; proposed ADR on the material/PBR data contract ([backlog](../backlog.md#proposed-adrs-for-the-leadowner)) |
| Related | [RD-005 rendering](./RD-005-rendering.md), [RD-003 AI pipeline](./RD-003-ai-pipeline.md), [RD-014 performance](./RD-014-rt-performance.md), [ADR-0009 asset layers](../adr/0009-asset-layers.md), [RD-007 licensing](./RD-007-licensing.md) |

## 1. Question and scope

The owner directive (2026-11-28) puts stochastic hex-tiling into the PBR stage. Questions:

1. What does Mikkelsen's *Practical Real-Time Hex-Tiling* need from a renderer, and how does it fit RTGL1's ray-traced material path?
2. Can it be a **generic RTGL1 capability** (per-material flag, no Serious Sam code) that could be offered upstream?
3. How are tangent-space normal maps, mip selection and filtering handled correctly?
4. How does the AssetCompiler decide eligibility, and which materials are excluded?
5. What are the offline-baked, hybrid and low-end alternatives, and how are they compared on cost and VRAM?

Out of scope: generating the PBR maps themselves (RD-003, backlog POC-47..49).

## 2. Evidence

| ID | Source | Note |
|---|---|---|
| H1 | M. S. Mikkelsen, "Practical Real-Time Hex-Tiling", *Journal of Computer Graphics Techniques* vol. 11, 2022 (issue number not verified), https://jcgt.org/published/0011/03/05/ (paper PDF there) | primary; abstract and method read from the search summary and the demo README, not a full re-read |
| H2 | `mmikk/hextile-demo`, https://github.com/mmikk/hextile-demo, MIT licence (fetched 2026-11-28) | reference shader code; parameters for rotation, tile rate, separate border contrast for colour and normals; a large-world precision variant (`hextiling_rws.h`) |
| H3 | E. Heitz, F. Neyret, "High-Performance By-Example Noise using a Histogram-Preserving Blending Operator", HPG 2018; T. Deliot, E. Heitz, "Procedural Stochastic Textures by Tiling and Blending", GPU Zen 2, 2019 | the methods H1 adapts (cited by H1/H2; not re-read) |
| H4 | RTGL1 `v1.1.0` (`b1eb3d8`), local clone: `Source/Shaders/RayCone.h:85-122`, `Source/Shaders/HitInfo.inl:319,384-385`, `Source/Shaders/ShaderCommonGLSLFunc.h:85` | [SRC] |
| H5 | RD-005 §3.2 (RTGL1 material model, no height maps, override postfixes) | [SRC] summary |

## 3. Observed facts

### 3.1 The technique

- [DOC] H1/H2: the UV plane is covered by a hexagonal lattice. Each lattice cell gets a random offset (and optionally rotation) of the source texture. Each shaded point blends **three** samples, one per surrounding hex vertex, with weights from barycentric-like coordinates.
- [DOC] H1/H2: unlike H3, Mikkelsen omits histogram preservation and samples the **original texture directly**, so no Gaussianized or LUT texture is needed. Seams are hidden by an exponentiated blend curve with a contrast parameter, set separately for colour and normals.
- [DOC] H2: for normal maps, the average normal must be close to (0,0,1), or the tilt shows clearly in the lit result. Rotated tiles require the sampled tangent-space normal to be rotated by the same angle in the tangent plane.
- [DOC] H1 (search summary): side by side, colour textures lose some quality compared with plain tiling; the author considers it acceptable. Cost: three texture fetches per map instead of one, plus the lattice math.

### 3.2 RTGL1 v1.1.0 material path

- [SRC] H4: hit shaders compute UV derivatives from a **ray cone** (`getTriangleUVDerivativesFromRayCone`, `RayCone.h:85`) and sample with `textureGrad` (`RayCone.h:122`, `ShaderCommonGLSLFunc.h:85`). Explicit gradients are exactly what hex-tiling needs: each of the three samples uses the same gradients, rotated with the tile.
- [SRC] H4: normal mapping builds the world normal from the per-vertex tangent (with handedness) and the geometric normal (`HitInfo.inl:384-385`). A hex-tiled normal therefore has to be un-rotated in tangent space **before** this step.
- [SRC] H5: a material is albedo-alpha + roughness/metallic/emission + normal, with up to three blended layers. There is no height map support.
- [ASM]: all hit paths that sample materials (primary, reflection/refraction, indirect) go through shared `HitInfo.inl` functions. One change there would cover direct, reflected and indirect lighting consistently. Verify by listing every `getHitInfo*` caller.

### 3.3 Requirements check (directive list)

| Requirement | How it is met (proposal) |
|---|---|
| Same transform for all maps of a material | Compute lattice cell, offsets, rotation and weights once per hit; apply to albedo, ORM/RME and normal fetches |
| Correct tangent-space normals | Rotate the sampled XY by the inverse tile rotation; blend in tangent space (or use the demo's derivative-based blending); renormalize; then the existing TBN step |
| Material continuity | Contrast parameters per material; disable on surfaces whose UVs are not continuous across polygons |
| Mipmapping and filtering | Use the ray-cone gradients for all three fetches, rotated per tile; anisotropic filtering as today |
| Per-material eligibility and configuration | Per-material flag plus parameters (tile rate, rotation on/off, contrast) carried with the material, not hard-coded per game |
| Automatic eligibility via AssetCompiler | Classifier proposes a flag per texture; curated overrides win (ADR-0004, ADR-0009) |
| Explicit exclusions | text, signage, decals, HUD/UI, directional artwork (arrows, murals, trims), animated and effect textures, alpha-tested cut-outs, atlas textures, lightmap-like or technical textures |
| Runtime activation | global setting (off / eligible materials / forced debug) plus per-material flag |
| RT lighting, reflections, GI | Covered if the change is in the shared hit-info code ([ASM] §3.2) |
| Generic RTGL1 capability | New optional fields in the material create-info (flag + parameters); default off; no engine-specific names |

## 4. Assumptions and unknowns

- A1 [ASM]: tripling material fetches on eligible surfaces costs less than 1 ms at 1440p on the RTX 4070 because only primary and a fraction of secondary hits sample materials. Must be measured (POC-53).
- A2 [ASM]: SE1 world textures are mostly tileable terrain and architecture; text and directional art are a minority but highly visible. The classifier error that matters is a false positive on signage.
- A3 [ASM]: random offsets need a stable per-cell hash that does not depend on frame or camera, so the denoiser's temporal history stays valid.
- U1: whether the RTGL1 material API can carry extra per-material parameters without breaking the SE-RT-era API that SSTRE uses. An optional extension struct is the likely route.
- U2: whether upstream RTGL1 (dormant since 2023, RD-005) would accept a contribution. The feature must work as an SSTRE patch even if not.
- U3: whether raster paths (Classic-VK fixed-function Vulkan/OpenGL) can show it. Realtime hex-tiling needs a programmable shader; the raster paths emulate the fixed-function pipeline (RD-005 §3.4). Baked variants work everywhere.

## 5. Alternatives and trade-offs

| Approach | Description | Runtime cost | VRAM | Quality | Platforms |
|---|---|---|---|---|---|
| **R** Realtime hex-tiling (H1) | three fetches + blend in RTGL1 hit shaders | 3× material fetches on eligible hits | none extra | best repetition hiding, slight colour softening | RT only (RTGL1) |
| **B** Offline baked | AssetCompiler synthesizes a larger, non-repeating texture (e.g. 2×2 or 4×4 the period) with the same hex method, tileable at the new period | none | 4–16× per eligible texture | repetition only pushed to a larger period | all, incl. raster |
| **H** Hybrid | baked variant at a moderate period for near/medium distance, realtime only at distance or on large terrain; or baked "variation masks" that select among 2–4 pre-shifted copies with one extra fetch | low | 1–4× | close to R | RT; masks may work in raster with multitexture |
| **L** Low-end | no hex-tiling; detail textures or macro variation already in SE1 data; or B at period 2× with BC compression | none | ≤ 2× | modest | raster, Deck, low-end |

## 6. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Visible artefacts on signage or directional art | high | conservative classifier; exclusion classes; curated overrides; quality profile "off" |
| Normal-map tilt or wrong rotation | medium | synthetic fixtures (checker normal, tilted normal) with numeric checks |
| Denoiser shimmer from unstable hashing | medium | world-stable per-cell hash (A3); temporal test at fixed camera |
| VRAM growth for baked variants on 12 GB | medium | budget per profile; BCn; only on eligible high-frequency textures |
| Upstream non-acceptance | low | keep as a self-contained patch with tests |

## 7. Proposed experiment and success criteria

1. **Synthetic fixtures** (CI-safe, no game data): generated tileable albedo/normal/ORM sets; checks: identical transform across maps (bitwise same cell IDs), normal error < 1° vs a reference implementation on a flat surface, no mip popping at fixed camera distance sweep.
2. **RTGL1 prototype** (POC-50): flag + parameters, shared hit-info change, debug view of cell IDs. Pass: on two TFE and two TSE scenes, eligible surfaces show no tiling period at 3 test distances (visual review, local), no new validation errors, cost reported per mode (N/T).
3. **Eligibility** (POC-51): classifier on the 50-asset test matrix plus all textures of the slice levels; pass: 0 false positives on the hand-labelled exclusion set, ≥ 80 % recall on hand-labelled eligible terrain/architecture.
4. **Comparison** (POC-52/53): R, B, H, L on the same scenes; table of mean FPS, p99, 1 % low and VRAM per approach, plus FLIP against the R reference.

## 8. Recommendation

Implement R as an optional, default-off generic RTGL1 material feature in the shared hit-info code, using the existing ray-cone gradients. Add eligibility to the AssetCompiler with a conservative classifier and curated overrides, and treat exclusions as a hard list. Offer B for raster and low-end profiles. Decide H only after the comparison shows R is too expensive on the reference PC.

## 9. Decision dependencies

- Material/PBR data contract (proposed ADR): where the flag and parameters live (manifest, compiled material record, RTGL1 create-info).
- Phase 1 baseline (RD-014) must exist so the cost is measured against the optimized engine.
- Owner: whether an upstream RTGL1 contribution may be offered (posting upstream is an external action).

## 10. Next steps

POC-50 (prototype), POC-51 (eligibility), POC-52 (baked/hybrid), POC-53 (feature cost matrix) in the [backlog](../backlog.md#stage-m2--pbr-and-hex-tiling-after-m3-directive-phase-2).
