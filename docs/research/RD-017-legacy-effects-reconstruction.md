# RD-017: Legacy atmospheric, translucent and particle effects reconstruction

| Field | Value |
|---|---|
| Dossier | RD-017 |
| Author | Track DOCS (planning), 2026-11-28; findings to be filled by tracks FXT (L3, FX1), FXP (FX2) and A3 |
| Date | 2026-11-28 |
| Status | **Draft.** Problem statement, questions and plan only. No new source reading or measurement was made for this dossier; facts come from the owner's preview2 test, the preview2 release notes, EXP-017 and EXP-018. Findings are pending POC-80..85. |
| Feeds | Proposed ADR-0016 declarative effect/material semantic classification ([backlog](../backlog.md#proposed-adrs-for-the-leadowner)); backlog POC-80..85; roadmap criteria P3-4..P3-8 |
| Related | [RD-003 AI pipeline](./RD-003-ai-pipeline.md) (per-class policy), [RD-005 rendering](./RD-005-rendering.md), [RD-014 RT performance](./RD-014-rt-performance.md), [RD-016 lighting](./RD-016-legacy-lighting-reconstruction.md), [ADR-0009 asset layers](../adr/0009-asset-layers.md), [rendering defect register](../rendering-defects.md) RDF-002, RDF-003, RDF-005, RDF-006 |

Evidence labels: **[DOC]** published source, **[SRC]** read in our source trees, **[EXP]** observed in a run, **[ASM]** assumption or hypothesis, with what would verify it.

## 1. Question and scope

Three groups of legacy effects look wrong or unconvincing in preview2. This dossier asks, for each group, what the original implementation actually is, where the visible defect comes from, and which universal correction or modernization is justified:

1. **Translucent light volumes**: translucent white geometry representing light entering rooms, light shafts and similar atmospherics (directive §3).
2. **Lightning and atmospheric special effects**: lightning, electricity, energy arcs, fire and explosions, smoke and dust, teleport effects, glowing projectiles, light shafts, lens flares and other magical or atmospheric effects (directive §4).
3. **Particles**: the particle rendering architecture and particle assets in both campaigns and all three renderers (directive §5).

It also covers the asset side: effect and particle texture classes and their enhancement recipes in Remaster-Toolkit/AssetCompiler. Out of scope: world lighting ([RD-016](./RD-016-legacy-lighting-reconstruction.md)), menu assets ([RD-018](./RD-018-menu-ui-modernization.md)), performance rewrites (M1; opportunities are recorded only).

## 2. Problem as observed

- [EXP] Owner test of preview2: under RT, translucent light-effect geometry looks like conspicuous white translucent boxes instead of light (RDF-002).
- [EXP] Owner test of preview2: lightning looks like a poorly outlined image switching on and off at the strike location (RDF-003). It is unknown whether this comes from texture enhancement, alpha processing, RT rendering, blend semantics or a combination.
- [EXP] preview2 release notes: chainsaw first-person particles are not drawn in RT (RDF-005); SE1 fog and haze are not shown in RT (RDF-006).
- [SRC] EXP-017 commit table: `c1537cfd` stopped building RT particles outside the RT particle pass to fix a null-scene crash caused by TSE first-person chainsaw particles. [ASM] RDF-005 may be a side effect of that fix (first-person particles are emitted outside that pass).

## 3. Evidence so far

| ID | Source | Revision / date |
|---|---|---|
| F1 | Owner test notes on preview2 (lead's records) | 2026-11-28 |
| F2 | 0.1.0-preview2 release notes, "Known issues" (local build) | 2026-11-28 |
| F3 | [EXP-017](../experiments/EXP-017-engine-integration.md) commit table and R-runs | integration `7eeed884` |
| F4 | [EXP-018](../experiments/EXP-018-rt-tse.md) A1 (haze), R3 | 2026-11-28 |
| F5 | [EXP-013](../experiments/EXP-013-ai-texture-poc.md), [EXP-019](../experiments/EXP-019-vertical-slice-assets.md): enhancement profile used for preview2 (conservative, deterministic SR; conventional resampling for skies and gradients) | 2026-11-28 |
| F6 | Reference sources to read: original SE lineage, Classic-VK, Serious-Engine-RT `Raytracing/` (material/blend upload, `RTParticles.cpp`), RTGL1 v1.1.0 (transparency, emissive, bloom) | as pinned in RD-001/RD-005 |

## 4. Comparison configurations and method

Every effect defect is isolated by comparing identical effects across these **7 configurations**, at reproducible captures and fixed animation checkpoints (POC-90):

| # | Engine and renderer | Textures |
|---|---|---|
| C1 | Classic-VK (reference build), Vulkan raster | original |
| C2 | SSTRE, Vulkan raster | original |
| C3 | SSTRE, Vulkan raster | enhanced |
| C4 | SSTRE, OpenGL | original |
| C5 | SSTRE, OpenGL | enhanced |
| C6 | SSTRE, RT | original |
| C7 | SSTRE, RT | enhanced |

Plus **corrected RT** (the Preview3 candidate) once fixes exist. Reading the matrix: a defect present from C3/C5/C7 but absent from C2/C4/C6 is an asset-processing defect; one in C6/C7 only is an RT defect; one in C2 but not C1 is an SSTRE engine regression. Diagnostic RT comparisons use fixed exposure; gameplay exposure is validated separately. Debug views needed (POC-90): material and effect classification, alpha and transparency, particle classes, emissive intensity, volumetric contribution.

## 5. Investigation questions

### 5.1 Translucent light volumes (POC-80)

Determine, per observed instance, whether it comes from: translucent brush geometry; additive or alpha-blended materials; light beam entities; billboard effects; particle effects; lens flares and glow; fog, haze or volumetric media; special-purpose legacy blending; incorrect RTGL1 transparency handling; incorrect material or geometry classification. Do not assume it is conventional post-process bloom. Deliver the complete translation table SE blend mode and surface flags → RTGL1 material/blend, with mismatches marked.

### 5.2 Lightning and special effects (POC-82, POC-83)

Across C1..C7: alpha preservation during enhancement; AI-generated outlines and halos; premultiplied vs straight alpha; additive vs conventional alpha blending; wrong RGB in transparent texels; emissive intensity and HDR; filtering and compression; alpha-aware mipmaps; billboard rendering; animation timing; dynamic illumination during strikes; bloom and atmospheric scattering. Then run the same checks on the other effect classes listed in §1 before deciding whether the defect is lightning-specific (no lightning-only workaround before that).

### 5.3 Particles (POC-84)

Architecture; billboard orientation and camera alignment; transparency and additive blending; sorting and depth; alpha correctness; animation and timing; geometry intersection artefacts; soft particles; HDR emissive particles; dynamic light from explosions, fire and projectiles; density and overdraw; batching and efficiency; dynamic RT geometry uploads; consistency across RT, Vulkan and OpenGL. Performance questions for M1: per-frame uploads, BLAS builds/updates, transparent traversal, shader divergence, overdraw, CPU submission.

### 5.4 Effect and particle assets (POC-85)

Which effect and particle classes benefit from AI super-resolution, conventional resampling, alpha-aware resampling, conservative restoration, procedural reconstruction, or staying original? Candidate recipe properties: non-generative or conservative resampling; independent alpha processing; edge preservation without artificial sharpening; alpha-coverage preservation; coverage-correct mipmaps; additive semantics kept (no RGB in zero-alpha texels that would show under additive blending); automatic fallback to the original when QA fails. Effect textures never get the opaque-surface treatment.

## 6. Preferred implementation order

Light volumes (directive §3), in increasing complexity; stop at the first step that passes P3-4:

1. Correct translation of original blend modes, opacity and material flags.
2. Semantic classification of legacy light-effect surfaces from engine material flags, entity types and blend semantics (proposed ADR-0016).
3. A compatible compositing pass with correct depth testing and occlusion.
4. Replacement of eligible light-shaft geometry by physically plausible volumetric scattering (configurable; the original geometry must not stay visible as a second, overlapping effect).
5. HDR emissive intensity integrated with native bloom or glare.

Lightning and other effects: isolate (POC-82) → generic effect semantics in the renderer (POC-83) and effect-texture recipes (POC-85) → genuinely emissive RT rendering where appropriate (HDR emissive, native bloom, synchronized dynamic light on surrounding geometry, correct transparency and occlusion, optional scattering), keeping original timing and gameplay behaviour.

Particles: correctness fixes in M0.1 (POC-84); larger performance-oriented rewrites deferred to M1 with a note in RD-014.

## 7. Constraints and acceptance criteria

Constraints:

- No indiscriminate removal of translucent white geometry and no classification by texture colour or filename: such heuristics would hit windows, water, fog, particles and other legitimate transparent materials. Unavoidable exceptions are declarative, reviewed data with a documented reason.
- Generic RTGL1 improvements are preferred where technically appropriate (reuse, possible upstream contribution; technical content only).
- No silent quality change; new paths behind cvars or profile settings; volumetrics configurable; no disproportionate cost; no unnecessary particle geometry expansion or texture memory growth. Each substantial correction reports its A/B cost.
- Original particle timing, behaviour, gameplay function, density and artistic intent are preserved. Higher resolution or more generated detail is not assumed to be better.
- GATE-05: public reports use level names and entity/blend classes; per-asset tables and captures stay local.

Acceptance: roadmap criteria **P3-4** (light volumes), **P3-5** (lightning), **P3-6** (alpha coverage ±2 points per mip, transparent-texel RGB ≤ 4/255, or recorded fallback), **P3-7** (legitimate transparent materials within the quality guard), **P3-8** (particles: no new blocking defects, emitted count unchanged), plus the POC-80..85 package criteria in the [backlog](../backlog.md#stage-m01--rendering-correctness-and-legacy-visual-modernization).

## 8. Hypotheses

| # | Hypothesis | What would verify it |
|---|---|---|
| H1 [ASM] | The white boxes are translucent brush polygons whose SE blend mode is additive (or a legacy translucency mode) but are uploaded to RTGL1 as alpha-blended or opaque-ish surfaces lit by RT, so they show as white volumes | POC-80 blend translation table; classification debug view on the observed instances |
| H2 [ASM] | The lightning "outline" comes from RGB values in zero-alpha texels of the enhanced texture, made visible by additive blending or bilinear filtering; C2/C4/C6 would not show it | C1..C7 matrix at a fixed strike checkpoint; transparent-texel RGB statistics of the enhanced vs original texture |
| H3 [ASM] | Part of the lightning defect is renderer-side: missing emissive/HDR treatment in RT makes it read as a flat image, independent of the texture | C6 vs C2 with original textures |
| H4 [ASM] | The same alpha/blend defects affect other additive effect classes (fire, explosions, teleport, glowing projectiles) | POC-82 checks on ≥ 5 other classes |
| H5 [ASM] | RDF-005 (chainsaw first-person particles missing in RT) is a side effect of the crash fix that limits RT particle building to the RT particle pass | source reading of the particle path; run with first-person particles routed into the pass |
| H6 [ASM] | Per-frame dynamic particle uploads are a measurable RT cost in particle-heavy combat (M1 note) | POC-84 upload bytes and BLAS updates per frame |

## 9. Findings

### 9.1 Translucent light volumes

Pending POC-80 (root cause, blend translation, classification) and POC-81 (compositing/volumetric/emissive), track FXT (L3), EXP-021.

### 9.2 Lightning and special effects

Pending POC-82 (7-configuration isolation matrix) and POC-83 (generic effect correction), track FXT (FX1), EXP-021.

### 9.3 Particles

Pending POC-84, track FXP (FX2), EXP-022, including the M1 performance notes.

### 9.4 Effect and particle asset recipes

Pending POC-85, track A3, EXP-023.

## 10. Decision dependencies

- Proposed ADR-0016 (classification policy, declarative exceptions).
- Lead: RTGL1 changes are coordinated by the lead (possible upstream contribution); thresholds for P3-4..P3-8 after POC-90 calibration.
- Owner: only if a modern replacement (volumetrics, bloom) becomes a default or changes the original look noticeably.

## 11. Next steps

POC-80 → POC-81 (light volumes); POC-82 → POC-83 with POC-85 (effects and assets); POC-84 (particles); all validated with POC-89/POC-90 checkpoints. See the [backlog](../backlog.md#stage-m01--rendering-correctness-and-legacy-visual-modernization) and the [rendering defect register](../rendering-defects.md).
