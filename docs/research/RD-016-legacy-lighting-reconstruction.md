# RD-016: Universal legacy lighting reconstruction in ray tracing

| Field | Value |
|---|---|
| Dossier | RD-016 |
| Author | Track DOCS (planning), 2026-11-28; findings to be filled by track LIGHT (L1, L2) |
| Date | 2026-11-28 |
| Status | **Draft.** Problem statement, questions and plan only. No new source reading or measurement was made for this dossier; facts are taken from EXP-017, EXP-018 and the owner's preview2 test. Findings are pending POC-75..79. |
| Feeds | Proposed ADR-0015 legacy lighting reconstruction policy ([backlog](../backlog.md#proposed-adrs-for-the-leadowner)); backlog POC-75..79; roadmap criteria P3-1..P3-3 |
| Related | [RD-005 rendering](./RD-005-rendering.md), [RD-014 RT performance](./RD-014-rt-performance.md), [RD-017 effects](./RD-017-legacy-effects-reconstruction.md) (fog/haze overlap), [EXP-017](../experiments/EXP-017-engine-integration.md), [EXP-018](../experiments/EXP-018-rt-tse.md), [rendering defect register](../rendering-defects.md) RDF-001, RDF-006, [roadmap](../roadmap.md#preview-milestones-of-stage-m01) |

Evidence labels: **[DOC]** published source, **[SRC]** read in our source trees, **[EXP]** observed in a run, **[ASM]** assumption or hypothesis, with what would verify it.

## 1. Question and scope

The owner directive of 2026-11-28 (evening) makes RT a backend that must render original campaign levels, multiplayer maps and community content **without manually placed extra lights**. This dossier answers:

1. Which lighting contributions of the original Serious Engine are lost, wrongly converted or deliberately omitted by the RT pipeline (Serious-Engine-RT layer on Classic-VK, RTGL1)?
2. Which of them can be fixed by correct native conversion, and what remains for a legacy ambient term, lightmap-assisted compensation or, last, irradiance probes?
3. How is the result validated on non-showcase levels, and when can the temporary `1_2_Palenque` cave lights go?

Out of scope: translucent light volumes and other effects ([RD-017](./RD-017-legacy-effects-reconstruction.md)), performance optimization (M1; costs are measured, not optimized), PBR (M2).

## 2. Problem as observed

- [EXP] Owner test of preview2 (2026-11-28): several interiors that are adequately lit in raster become almost completely dark with RT on, in both campaigns. Register entry RDF-001.
- [EXP] EXP-017 R3/R12: the `1_2_Palenque` RT spawn cave was black (the watchdog killed one run on a flat black frame) until E5 added 25 cutscene-light entries to the TSE RT tuning table that whitelist the cave's invisible static lights. With them the cave is lit. The owner accepts this as a **temporary** workaround only.
- [SRC] EXP-018 R2: the RT layer's per-world tuning has tables and `switch (eCurrentWorld)` blocks for cutscene lights, a light threshold, ignored directional lights, haze and haze-ignored sectors, sky type and water. TFE worlds were tuned one by one in Serious-Engine-RT; TSE worlds got generic defaults. The layer therefore depends on per-level data to light some areas.
- [EXP] EXP-018 A1: TSE RT with haze on darkened everything beyond about 20 m; preview2 sets `haze = 0` by default. SE1 fog and haze are now not shown in RT at all (RDF-006).

## 3. Evidence so far

| ID | Source | Revision / date |
|---|---|---|
| L1 | [EXP-017](../experiments/EXP-017-engine-integration.md) R3, R12 and the commit table (cave lights, haze default) | integration `7eeed884`, 2026-11-28 |
| L2 | [EXP-018](../experiments/EXP-018-rt-tse.md) R2 (tuning tables), A1 (haze root cause) | 2026-11-28 |
| L3 | Owner test notes on preview2 (lead's records) | 2026-11-28 |
| L4 | Reference sources to read in POC-75: original Serious Engine lineage (via the Classic-VK history), SeriousSamClassic-VK, Serious-Engine-RT `Sources/Engine/Raytracing/`, RTGL1 v1.1.0 clean-room fork, SSTRE-Engine `sprint2/integration` | as pinned in RD-001/RD-005 |

## 4. Investigation questions (POC-75)

For each item: how does the original engine produce the contribution, what does Classic-VK do, what does Serious-Engine-RT convert, what does RTGL1 accept, and what does SSTRE do today?

| # | Contribution | Question |
|---|---|---|
| Q1 | Sector ambient | Is the per-sector ambient colour exported to RT at all? If not, is it lost or deliberately replaced by RT indirect light? |
| Q2 | Shadowmaps and precalculated surface illumination | What do brush shadowmaps encode (direct, ambient, both)? Are they ignored in RT, and can direct and indirect parts be separated? |
| Q3 | Ambient light entities | Which entity classes only contribute ambient light, and are they converted? |
| Q4 | Non-shadow-casting lights | Are lights without the shadow-casting flag, or with "no static shadows" style flags, dropped, or converted as shadowed lights? |
| Q5 | Directional and point lights | How are SE directional and point lights mapped to RTGL1 light types; are the "ignored directional lights" tables hiding real contributions? |
| Q6 | Emissive surfaces | Which SE material properties should become RT emissive, and which already do? |
| Q7 | Dynamic and scripted lights | Are animated, switched and scripted lights (light animations, on/off via triggers) followed per frame? |
| Q8 | Culling | Are lights excluded by sector, cull mask, ray length or the light threshold even though they light visible surfaces? |
| Q9 | Intensity and attenuation | How do SE falloff and hotspot distances, colour and intensity map to RTGL1 radiance and radius? Is the mapping in linear space? |
| Q10 | Exposure and tonemapping | Do auto-exposure and tonemapping make moderately lit interiors read as black, independent of the light conversion? Fixed-exposure comparison required. |
| Q11 | Fog, haze, volumetrics | How do fog and haze affect perceived brightness in raster and RT (overlap with RD-017 and RDF-006)? |
| Q12 | TFE vs TSE | Which differences are content (lighting habits of TSE levels) and which are code (entity classes, tuning defaults)? |

## 5. Preferred implementation order

The directive's order is binding. A later step starts only when the earlier one is measured as insufficient on the RD-016 checkpoint set (POC-89).

1. **A. Native light conversion** (POC-76). Translate existing SE lighting entities and parameters correctly into RTGL1: light classes and flags, scene traversal, sector handling, intensity/attenuation, exposure parameters. Generating artificial replacement lights is not a substitute for this step.
2. **B. Legacy ambient reconstruction** (POC-77). Original sector and surface illumination as a supplementary diffuse term: keep intended brightness and colour distribution, keep intentionally dark areas, no uniform global ambient increase, no light leaking between disconnected rooms, no double counting of direct light, linear space, consistent for dynamic objects, enemies and weapons, configurable. No indiscriminate post-process brightness correction as the main solution.
3. **C. Lightmap-assisted path tracing** (POC-78). Shadowmaps or precalculated illumination as a reference or supplementary indirect term, with adaptive compensation that is strongest where RT is far below the original and minimal where RT is already right; separate legacy direct and indirect parts where possible.
4. **D. Irradiance probes** (POC-78, feasibility only unless approved). Automatically generated from original level illumination: offline or level-load preprocessing, sector-aware placement, occlusion-aware interpolation, leak prevention, dynamic-object lighting, deterministic generation and caching, AssetCompiler integration. Not built if A–C suffice.
5. **Overrides** (POC-79). After A–C, re-test the `1_2_Palenque` cave without its cutscene lights and remove them if redundant. Level-specific light overrides remain possible for intentional artistic enhancement, never as a requirement for basic playability.

## 6. Constraints

- Universal solutions only; no per-level light placement for playability; exceptions are declarative data with a documented reason (proposed ADR-0015/ADR-0016).
- Every new term or changed conversion is behind a cvar or profile setting; defaults change only when shown better (M0.1 rule 3).
- Performance: no explosion of generated point lights, no extra bounces without measurements, cached static data. Each step reports its A/B frame-time cost; findings for M1 go to [RD-014](./RD-014-rt-performance.md).
- Vulkan and OpenGL raster are not changed by this work, except shared code that must stay identical in output (P3-9).
- GATE-05: public reports name levels and entity classes only; per-light tables and captures stay local.

## 7. Acceptance criteria

Roadmap criteria **P3-1** (lit interiors not unplayably dark: ≥ 50 % of raster mean luminance, ≤ 25 % of pixels below 0.01), **P3-2** (intentionally dark areas ≤ 2× raster and reviewed), **P3-3** (≥ 3 non-showcase levels per campaign, 0 added light entries, cave override disabled), and the package criteria of POC-75..79 in the [backlog](../backlog.md#stage-m01--rendering-correctness-and-legacy-visual-modernization). Thresholds are [ASM] until R1 calibrates them in POC-90.

## 8. Hypotheses

| # | Hypothesis | What would verify it |
|---|---|---|
| H1 [ASM] | Most dark interiors are lit in raster mainly by brush shadowmaps and sector ambient, which RT does not use; RT sees only the few light entities that pass its filters | POC-75 light counts per checkpoint; raster with shadowmaps disabled looks like RT |
| H2 [ASM] | Invisible or helper light entities (as in the 1_2 cave) are filtered out by the RT layer's light classification or threshold, which is why whitelisting them helped | POC-75 source reading of the light extraction filter; re-run the cave with the filter relaxed instead of the whitelist |
| H3 [ASM] | Part of the darkness is exposure: auto-exposure adapts to bright openings and crushes the interior | fixed-exposure captures vs gameplay exposure at the same checkpoints |
| H4 [ASM] | SE light falloff distances map to RTGL1 radii in a way that under-lights large rooms | compare analytic SE falloff with RTGL1 radiance at sample distances |
| H5 [ASM] | A sector-ambient term limited to the sector the shading point belongs to avoids cross-room leaks without probes | POC-77 leak test (adjacent unlit room) |
| H6 [ASM] | Native conversion plus the ambient term is enough; probes (order D) will not be needed | POC-78 memo: share of lit interior checkpoints still failing P3-1 |

## 9. Findings

Pending POC-75 (source comparison, inventory of lost, wrongly converted and omitted contributions), POC-76 (native conversion), POC-77 (legacy ambient), POC-78 (compensation/probe memo) and POC-79 (non-showcase validation, cave override). Track LIGHT fills this section and EXP-020 with [SRC]/[EXP] citations.

## 10. Decision dependencies

- Proposed ADR-0015 (policy above); ADR-0016 for any declarative exception data.
- Lead: calibrated thresholds for P3-1..P3-3; whether a default changes (rule 3).
- Owner: only if order D (probes) is needed or a default change trades atmosphere for brightness.

## 11. Next steps

POC-75 → POC-76 → POC-77 → (POC-78 if the gap remains) → POC-79, with checkpoints from POC-89 and captures from POC-90. See the [backlog](../backlog.md#stage-m01--rendering-correctness-and-legacy-visual-modernization) and register entries RDF-001 and RDF-006 in the [rendering defect register](../rendering-defects.md).
