# RD-013: Geometry enhancement

| Field | Value |
|---|---|
| Dossier | RD-013 |
| Author | Track DOC-R (roadmap/planning), 2026-11-28 |
| Date | 2026-11-28 |
| Status | **Draft.** Desk research and source reading only. Nothing was implemented or measured. Updated 2026-11-28 by track DOCS for owner [issue #22](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/issues/22) (stage order, technical direction, acceptance criteria; §1.1). |
| Feeds | backlog POC-94, POC-54..56 (stage M3) and POC-95 (M2 follow-up); proposed ADR on render-only geometry ([backlog](../backlog.md#proposed-adrs-for-the-leadowner)) |
| Related | [RD-005 rendering](./RD-005-rendering.md), [RD-011 hex-tiling](./RD-011-hex-tiling.md), [RD-014 performance](./RD-014-rt-performance.md), [ADR-0009 asset layers](../adr/0009-asset-layers.md) |

## 1. Question and scope

SE1 world geometry (brushes) is low-polygon. Ray-traced lighting exposes facets, especially on natural ground. The directive asks for low-cost methods, in this order:

1. vertex normal smoothing;
2. shadow terminator correction;
3. selective offline subdivision with constrained smoothing;
4. optional displacement mapping.

Constraints: collision geometry, level structure, gameplay, UV continuity and intentional architectural edges are preserved; everything is optional and configurable.

### 1.1 Owner direction of issue #22 (Origin: [issue #22](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/issues/22))

The owner observed in gameplay that the low-polygon, angular look of the original geometry is extremely prominent, and that better surface materials alone will not fix it. Geometry enhancement (stage M3) therefore runs **after M1 and before PBR and hex-tiling (M2)**. Stage IDs are unchanged. Consequences for this dossier:

- Techniques 1–3 no longer wait for M2. Technique 4 (displacement) needs PBR height maps, so it leaves M3 and becomes the M2 follow-up **POC-95**.
- A CPU-only gameplay-capture survey (**POC-94**) ranks the visibly angular geometry first and may overlap M1.
- Scope widens from world brushes to **model meshes** (characters, enemies, props) and curved architectural features, which are investigated separately from world brushes.

Technical direction (from the issue):

1. Review this dossier and the existing geometry packages before implementation.
2. Investigate normal smoothing, shadow terminator correction and selective offline subdivision or mesh refinement that actually improves visible silhouettes and angular geometry.
3. Distinguish shading artefacts from genuinely low polygon counts: smoothing normals alone cannot fix visibly angular silhouettes.
4. Prioritize visually prominent geometry, characters, enemies, props and curved architectural features, based on representative gameplay captures (POC-94).
5. Prefer general, deterministic and configurable processing over per-level manual modifications.
6. Preserve intentional hard edges, UV mapping, material assignments, animation compatibility, LOD behaviour, original collision geometry and gameplay behaviour.
7. Investigate world brush geometry separately from model meshes; preserve sector topology, portals and visibility semantics.
8. Stay compatible with future PBR materials, tangent-space normals and hex-tiling (for example tangents per UV chart on refined meshes); avoid choices that need later rework.
9. Measure triangle counts, memory, BLAS/TLAS cost, frame time and visual quality. Platform and licensing constraints and the GPU scheduling rules stay in force.

Owner acceptance criteria (copied from the issue):

- Update the roadmap, backlog and milestone dependencies to explicitly place geometry enhancement before PBR/hex-tiling. Keep cross-references consistent if milestone numbering changes.
- Demonstrate measurable and visible improvements to prominent angular geometry in representative scenes from both campaigns.
- Validate original gameplay, collisions, animation, material mapping and supported render backends; document limitations and fallback options.
- Quantify incremental performance and memory costs relative to the M1 baseline; retain the existing overall performance objective.
- Acknowledge this directive in an issue comment and link relevant research, implementation PRs and validation evidence. Close only when acceptance criteria are met.

The roadmap and backlog update that adds this section addresses the first criterion. The measurable forms of the others are in §7.

## 2. Evidence

| ID | Source | Note |
|---|---|---|
| G1 | Serious-Engine-RT `0e7f223`, `Sources/Engine/Raytracing/RTBrushes.cpp:411-421` (`RT_ProcessNormals`), `:789`; `SceneBrushes.cpp:76` | [SRC] |
| G2 | RTGL1 `v1.1.0`, `Source/Shaders/HitInfo.inl:384-385`; `Include/RTGL1/RTGL1.h` (`vertexNormalStride`) | [SRC] |
| G3 | J. Hanika, "Hacking the Shadow Terminator", *Ray Tracing Gems II*, ch. 4, Apress 2021 (open access, https://link.springer.com/book/10.1007/978-1-4842-7185-8) | not re-read for this dossier |
| G4 | M. J.-Y. Chiang, Y. K. Li, B. Burley, "Taming the Shadow Terminator", SIGGRAPH 2019 Talks | not re-read |
| G5 | RD-005 §3.2/§3.3 (no height maps in RTGL1; terrain not ray traced in the RT fork) | [SRC] summary |

## 3. Observed facts

- [SRC] G1: every brush polygon gets the **plane normal** for all its vertices (`RT_ProcessNormals` copies `bpo_pbplPlane->bpl_plRelative` into each vertex normal). World geometry is therefore flat-shaded in RT by construction; the facets are not only geometric but also a shading choice.
- [SRC] G1: brush vertex data, normals and UVs are built per polygon in the RT layer and uploaded as static geometry (`SceneBrushes.cpp:76` passes `brush.normals`). Collision uses the engine's own brush data, not these arrays [ASM: collision code reads `CBrushPolygon`/`CBrushSector` directly; verify].
- [SRC] G2: RTGL1 takes per-vertex normals and tangents and builds the shading normal from them; it can shade smooth normals without any API change.
- [DOC] G3/G4: with smooth shading normals, low-polygon meshes show a hard "shadow terminator" where shadow rays from the flat geometric surface disagree with the smooth normal. Both papers give cheap fixes: offset the shadow-ray origin towards a smooth-surface estimate (G3), or adjust the shading term near the terminator (G4).
- [SRC] G5: RTGL1 has no height or parallax maps. SE1 terrain (TSE) is not ray traced in the RT fork, so "ground" here means brush geometry.

## 4. Assumptions and unknowns

- A1 [ASM]: SE1 levels already separate many architectural edges into different polygons with sharp dihedral angles; a crease-angle threshold (e.g. 30–45°) plus "same material and same sector" rules will keep them sharp.
- A2 [ASM]: smoothing normals changes only shading, not visibility or collision, so gameplay is unaffected by technique 1 and 2.
- A3 [ASM]: subdivision of render-only copies is safe for gameplay as long as collision, portals, sector membership and entity placement use the original brush. Shadow and visibility differences between the smooth render mesh and the flat collision mesh could expose small gaps; constrained smoothing (boundary vertices pinned) avoids holes.
- A5 [ASM]: SE1 model meshes already carry per-vertex normals, so their angularity is mostly **silhouette** (polygon count), not shading; for them technique 3 matters more than technique 1. Verify with the POC-94 facet-vs-silhouette classification.
- A4 [ASM]: displacement needs either height maps (from the PBR stage) plus tessellation offline, or a ray-traced displacement method that RTGL1 does not have. Offline displacement of a render-only mesh is the only low-risk path.
- U1: how often UV seams coincide with smoothing groups; averaging normals across a UV seam is fine, splitting UVs is not needed for normals, but tangents must be recomputed per UV chart.
- U2: lightmaps (raster path) are computed for the original flat polygons; geometry changes for raster are out of scope until shown to be needed.

## 5. Alternatives and trade-offs

| # | Technique | Where | Cost | Risk | Notes |
|---|---|---|---|---|---|
| 1 | Vertex normal smoothing | RT layer at upload (runtime) or AssetCompiler (offline normal table) | ~0 runtime; small CPU at level load | low | crease angle, material and sector boundaries, per-surface opt-out |
| 2 | Shadow terminator correction | RTGL1 shaders (generic) | small ALU per shadow ray | low | needed once 1 is on; generic RTGL1 feature, default on with 1 |
| 3 | Selective subdivision + constrained smoothing | AssetCompiler, render-only mesh per eligible surface | more triangles → BLAS size, build time, memory | medium | eligibility: natural ground and rock; pin boundary and crease vertices; preserve UVs by interpolation |
| 4 | Displacement (M2 follow-up POC-95, after the height maps exist) | AssetCompiler (offline, from height maps) | more triangles; VRAM | high | only after PBR height maps exist; strict amplitude limit; never on walkable surfaces where it would visibly float above or sink below collision |

## 6. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Smoothing rounds intentional edges | medium | crease angle, material/sector rules, curated per-level overrides |
| Render mesh no longer matches collision (feet sink, projectiles hit air) | high | technique 1/2 do not move vertices; 3/4 limit displacement amplitude; gameplay regression demos |
| BLAS growth slows RT | medium | selective eligibility; measure against Phase-1 baseline |
| Level data derived files are game-derived | medium | compiled render meshes are local outputs (ADR-0002); no distribution; only recipes and parameters go public |

## 7. Proposed experiment and success criteria

1. **POC-54 normal smoothing (RT):** setting `off / crease-angle N`; pass: on 3 TFE and 3 TSE ground-heavy scenes, facet visibility reduced (local review), 0 changes in collision (identical demo end-state in 5/5 replays), level-load time increase < 5 %, frame-time change within the regression threshold.
2. **POC-55 terminator correction (RTGL1, generic):** pass: synthetic sphere/cylinder fixtures show no terminator band at 3 light angles; no new validation errors; cost < 0.2 ms at 1440p [ASM target].
3. **POC-56 subdivision/mesh refinement (offline), world brushes and model meshes as separate sub-packages:** pass: on the top-ranked POC-94 scenes (≥ 3 per campaign), the maximum dihedral angle between adjacent render triangles on refined curved surfaces is ≤ 50 % of the original [ASM], and the lead's side-by-side review records a visible improvement; boundary vertices bit-identical to the original; UV error 0 at original vertices; material assignments unchanged; animated models play all frames without cracks and LOD switching still works; sector, portal and visibility behaviour unchanged; gameplay end-state identical (5/5 demo replays, collision unchanged); RT, Vulkan and OpenGL validated, with any raster limitation and the fallback (original meshes) documented; triangle count, memory, BLAS/TLAS size and build time, and frame time reported per scene against the M1 baseline (POC-53), within the overall performance objective.
4. **POC-94 gameplay-capture survey (CPU-only, runs first, may overlap M1):** pass: ≥ 6 scenes per campaign [ASM]; each finding classified as shading facet or silhouette angularity and as world brush, character, enemy, prop or curved architecture, with a visibility score; ranked top 10 per campaign.
5. **POC-95 displacement (M2 follow-up):** pass: amplitude limit respected on 100 % of vertices; no visible separation of walkable surfaces from collision; gameplay end-state identical; costs against the M1 baseline.

## 8. Recommendation

Start with the POC-94 survey, so that work follows the most visible problems. Do 1 and 2 together first: they are cheap, runtime-only and change no gameplay data, and they fix shading facets. Do 3 where the survey shows silhouette angularity or where 1+2 leave visible facets, for world brushes and model meshes separately. Do 4 only after the M2 PBR stage provides height maps (POC-95) and the cost is known. Keep all four as explicit settings in the quality profiles.

## 9. Decision dependencies

- Proposed ADR: render-only geometry may differ from collision geometry; collision, portals and sectors always use original data.
- PBR stage height maps for technique 4 (hence POC-95 in M2, after M3).
- M1 baseline D for cost measurement (M3 starts at M1 exit, [issue #22](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/issues/22)).

## 10. Next steps

POC-94 → POC-54 → POC-55 → POC-56 in the [backlog](../backlog.md#stage-m3--geometry-enhancement-runs-before-m2-directive-phase-2); POC-95 in [stage M2](../backlog.md#stage-m2--pbr-and-hex-tiling-after-m3-directive-phase-2).
