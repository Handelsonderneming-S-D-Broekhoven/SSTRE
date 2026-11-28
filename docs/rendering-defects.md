# Rendering defect register

> **Status: skeleton with seed entries, created by track DOCS on 2026-11-28.** Maintained by track R1 (POC-89) from M0.1 on. R1 files and triages defects; it does not fix engine code. The lead assigns each defect to the owning track. Stage and acceptance criteria: [roadmap](roadmap.md#preview-milestones-of-stage-m01); packages: [backlog](backlog.md#stage-m01--rendering-correctness-and-legacy-visual-modernization).

Owner directive 2026-11-28 (evening) §7: a prioritized register of visible rendering defects, covering missing or wrongly culled geometry, sky artefacts, transparency and blending, water and underwater transitions, fog and haze, material classification, light intensity and colour, particles, lightning and atmospherics, decals, animated textures, emissive materials, weapon rendering, HUD, shadows, normals, texture filtering and mipmaps, and menu rendering.

## Rules

- **GATE-05.** Entries name levels, entity classes, engine source identifiers and blend/flag names only. No game asset paths, file hashes or texture names; no screenshots. Per-asset details, positions and captures stay in R1's local workspace and are referenced by a local id.
- **Engine vs asset.** Every entry is classified before it is assigned: **engine** (SSTRE engine or RT layer), **RTGL1**, **asset-processing** (Remaster-Toolkit/AssetCompiler output), **content** (original data, not fixable without a declarative exception), or **unknown** (not yet isolated). The 7-configuration matrix of [RD-017](research/RD-017-legacy-effects-reconstruction.md) §4 is the standard isolation method.
- **Universal fixes.** The proposed correction is universal (engine, RTGL1 or recipe level). Per-texture, per-entity or per-level workarounds are not accepted; an unavoidable exception is declarative data with a documented reason.
- **Evidence labels** [DOC]/[SRC]/[EXP]/[ASM] apply to the cause fields.
- Priority follows impact on playability, visual correctness and the next presentation build (Preview3).

## Severity scale

| Severity | Meaning | Examples |
|---|---|---|
| **S1** blocker | Makes an area unplayable, or crashes or hangs; or misrepresents a core Preview3 feature in a showcase level | interior too dark to navigate; level hang |
| **S2** major | Conspicuous, frequent visual error in normal play, no in-renderer workaround | light volumes drawn as white boxes; broken effect class |
| **S3** minor | Visible but localized, rare or subtle | sky streaks in one level; one particle effect missing |
| **S4** cosmetic or tooling | Minimal visual impact, or affects tooling, captures or menus only | grey engine screenshots; option listed in the wrong mode |

S1 and S2 entries block the Preview3 exit unless the lead defers them with a reason (roadmap, "open blocking defect").

## Status vocabulary

`new` → `triaged` (classified, severity and owner set) → `investigating` → `root-caused` (confirmed root cause recorded) → `fix-in-progress` → `fixed` (merged on an integration branch) → `verified` (regression test passes on the candidate build) → `closed` (released in a preview).
Side exits: `deferred` (to Preview4 or a later stage, with reason), `wont-fix` (with reason, lead approval), `duplicate` (of RDF-NNN), `cannot-reproduce`.

## Summary

| ID | Title | Campaign | Renderer | Kind | Severity | Status | Owner track | POC |
|---|---|---|---|---|---|---|---|---|
| [RDF-001](#rdf-001-interiors-almost-black-in-rt) | Interiors almost black in RT | TFE, TSE | RT | unknown (engine/RT layer suspected) | S1 | triaged | LIGHT (L1, L2) | POC-75..79 |
| [RDF-002](#rdf-002-translucent-light-volumes-drawn-as-white-boxes) | Translucent light volumes drawn as white boxes | TFE, TSE [ASM] | RT | unknown (engine/RTGL1 suspected) | S2 | triaged | FXT (L3) | POC-80, POC-81 |
| [RDF-003](#rdf-003-lightning-looks-like-an-outlined-flashing-texture) | Lightning looks like an outlined flashing texture | TSE [ASM: both] | unknown | unknown | S2 | triaged | FXT (FX1) + A3 | POC-82, POC-83, POC-85 |
| [RDF-004](#rdf-004-sky-streaks-in-tse-1_1_palenque-rt) | Sky streaks in TSE `1_1_Palenque` RT | TSE | RT | engine | S3 | triaged | R1 → lead | POC-89 |
| [RDF-005](#rdf-005-chainsaw-first-person-particles-not-drawn-in-rt) | Chainsaw first-person particles not drawn in RT | TSE | RT | engine | S3 | triaged | FXP (FX2) | POC-84 |
| [RDF-006](#rdf-006-se1-fog-and-haze-not-shown-in-rt) | SE1 fog and haze not shown in RT | TSE (TFE to check) | RT | engine | S2 | triaged | LIGHT / FXT (lead to assign) | POC-75, POC-80 |
| [RDF-007](#rdf-007-engine-screenshots-grey-in-vulkan) | Engine screenshots grey in Vulkan | TFE, TSE | Vulkan raster | engine | S4 | triaged | R1 (harness) → lead | POC-90 (POC-45) |
| [RDF-008](#rdf-008-rt-options-listed-in-the-vulkan-rendering-options-menu) | RT options listed in the Vulkan rendering-options menu | TFE, TSE | Vulkan raster, OpenGL [ASM] | engine | S4 | triaged | UI1 | POC-87 |
| [RDF-009](#rdf-009-sky-instead-of-distant-hillside-in-tse-1_1_palenque-rt) | Sky drawn instead of distant hillside in TSE `1_1_Palenque` RT | TSE | RT | engine | S3 | triaged | R1 → lead | POC-89 |

## Entry template

Copy for each new defect. Fields follow directive §7. Unknown fields say "unknown", not blank.

```markdown
### RDF-NNN: <short title>

| Field | Value |
|---|---|
| ID | RDF-NNN |
| Reported | <date>, <who / which run> |
| Reproduction | <level, start or checkpoint id, steps, settings/cvars, build> (positions and captures: local id only) |
| Campaign | TFE / TSE / both |
| Renderer | RT / Vulkan raster / OpenGL / all; textures original / enhanced |
| Affected class | <material or blend class, entity class, effect or particle class; no asset names> |
| Kind | engine / RTGL1 / asset-processing / content / unknown |
| Severity | S1..S4, with the reason |
| Suspected root cause | <hypothesis, [ASM]> |
| Confirmed root cause | <[SRC]/[EXP] with code location or experiment>, or "not yet" |
| Proposed universal correction | <engine / RTGL1 / recipe-level fix; declarative exception only with reason> |
| Regression test | <checkpoint ids in the POC-89 scene set, metric and threshold> |
| Performance implications | <expected or measured cost; M1 note> |
| Owner track / POC | <track>, <POC id> |
| Status | <status> (<date>) |
| Links | <EXP report, PR, commits> |
```

## Entries

### RDF-001: Interiors almost black in RT

| Field | Value |
|---|---|
| ID | RDF-001 |
| Reported | 2026-11-28, owner manual test of 0.1.0-preview2 |
| Reproduction | Play interiors that are adequately lit in Vulkan raster with RT on, in both campaigns; exact checkpoints to be defined by R1 in POC-89 (several per campaign, incl. non-showcase levels). Historic case: TSE `1_2_Palenque` spawn cave was black in RT until per-level cutscene lights were added (EXP-017 R3/R12) |
| Campaign | TFE, TSE |
| Renderer | RT; original and enhanced textures |
| Affected class | world lighting: sector ambient, brush shadowmap illumination, light entities (classes to be listed by POC-75) |
| Kind | unknown; engine/RT layer suspected |
| Severity | S1: areas become unplayably dark; central to Preview3 (P3-1..P3-3) |
| Suspected root cause | [ASM] RT does not use sector ambient and shadowmap illumination, and filters out some light entities (helper or invisible lights, threshold, culling); possibly worsened by exposure. See [RD-016](research/RD-016-legacy-lighting-reconstruction.md) H1–H4 |
| Confirmed root cause | not yet (POC-75) |
| Proposed universal correction | RD-016 order: native light conversion → legacy ambient term → lightmap-assisted compensation → probes only if needed; no per-level lights; remove the 1_2 cave override when redundant |
| Regression test | lit interior and intentionally dark checkpoints of the validation level set; P3-1, P3-2, P3-3 |
| Performance implications | to be measured per step (no point-light explosion; ambient term target ≤ 0.5 ms at 1440p [ASM]) |
| Owner track / POC | LIGHT (L1, L2), POC-75..79 |
| Status | triaged (2026-11-28) |
| Links | [EXP-017](experiments/EXP-017-engine-integration.md), [EXP-018](experiments/EXP-018-rt-tse.md) |

### RDF-002: Translucent light volumes drawn as white boxes

| Field | Value |
|---|---|
| ID | RDF-002 |
| Reported | 2026-11-28, owner manual test of 0.1.0-preview2 |
| Reproduction | Rooms with translucent geometry that represents light entering through openings or light shafts; RT on. Checkpoints to be defined in POC-89 |
| Campaign | observed in the preview2 levels; TFE and TSE [ASM] |
| Renderer | RT (raster looks as intended [ASM]); textures: to check both |
| Affected class | translucent brush polygons / light-effect surfaces; exact blend mode and flags to be identified |
| Kind | unknown; engine (blend translation) or RTGL1 (transparency handling) suspected |
| Severity | S2: conspicuous, recurring |
| Suspected root cause | [ASM] SE blend mode or translucency flag mistranslated to RTGL1, so the surface is lit and composited as a white volume. See [RD-017](research/RD-017-legacy-effects-reconstruction.md) H1 |
| Confirmed root cause | not yet (POC-80). **R1 [SRC] pointers for FXT:** `RT_GetPassThroughType` maps every `BPOF_TRANSLUCENT` brush polygon to `RG_GEOMETRY_PASS_THROUGH_TYPE_ALPHA_TESTED` (`Engine/Raytracing/RTBrushes.cpp:116-122`), `RT_ShouldBeRasterized` returns false for brushes (`:82-86`), and `IGNORE_BRUSH_COLOR` (`:143`, `:283-287`) drops the polygon colour; so a translucent brush is traced as a lit, alpha-tested opaque surface. R1 regression checkpoint `tse-vol-2_4m1` (light shafts) |
| Proposed universal correction | correct blend translation → semantic classification from flags/entity class (ADR-0016) → depth-correct compositing pass → optional volumetric replacement / HDR emissive with bloom |
| Regression test | light-volume checkpoints (P3-4) and transparent-material checkpoints (P3-7) |
| Performance implications | compositing pass cost to be measured; volumetrics configurable |
| Owner track / POC | FXT (L3), POC-80, POC-81 |
| Status | triaged (2026-11-28) |
| Links | — |

### RDF-003: Lightning looks like an outlined flashing texture

| Field | Value |
|---|---|
| ID | RDF-003 |
| Reported | 2026-11-28, owner manual test of 0.1.0-preview2 |
| Reproduction | A level with lightning strikes in the preview2 set; observe the strike. Fixed animation checkpoints to be defined in POC-90 |
| Campaign | TSE observed [ASM]; TFE to check |
| Renderer | unknown: to be isolated across the 7 configurations |
| Affected class | lightning effect (effect entity and its additive/alpha material) |
| Kind | unknown: asset-processing, renderer or both |
| Severity | S2: conspicuous effect in the presentation levels |
| Suspected root cause | [ASM] RGB in zero-alpha texels or halos from enhancement made visible by additive blending/filtering, and/or missing emissive treatment in RT. See RD-017 H2, H3 |
| Confirmed root cause | not yet (POC-82) |
| Proposed universal correction | generic effect semantics (POC-83) and alpha-aware effect-texture recipes with fallback (POC-85); no lightning-only workaround before the class check |
| Regression test | lightning checkpoints in C1..C7 + corrected RT (P3-5); alpha metrics (P3-6) |
| Performance implications | RT emissive path cost to be measured |
| Owner track / POC | FXT (FX1) with A3, POC-82, POC-83, POC-85 |
| Status | triaged (2026-11-28) |
| Links | — |

### RDF-004: Sky streaks in TSE 1_1_Palenque RT

| Field | Value |
|---|---|
| ID | RDF-004 |
| Reported | 2026-11-28, preview2 release notes (known issue) |
| Reproduction | TSE `1_1_Palenque`, RT, level start (player under water): the sky seen **through the water surface** shows white/blue diagonal bands; checkpoint `tse-sky-1_1m0` |
| Campaign | TSE |
| Renderer | RT; visible with original and enhanced textures |
| Affected class | sky (RT sky type / background geometry) |
| Kind | engine (not the textures: classic textures show it too) |
| Severity | S3 |
| Suspected root cause | [ASM] RT sky handling (sky type or background-geometry tuning) for this world; possibly related to RDF-009. **R1 (2026-11-28):** same spot as RDF-009; the streaks are in the refracted sky. Refracted/reflected rays that miss geometry sample RTGL1's sky **cubemap**, which the engine creates at `rasterizedSkyCubemapSize = 256` per face (`Engine/Raytracing/SSRT.cpp:360`) and fills by rasterizing the background brushes per material layer with `DEPTH_TEST|DEPTH_WRITE` also for blended layers (`SceneBrushes.cpp:203-210`; RTGL1 `Rasterizer::DrawSkyToCubemap`). H1: low cubemap resolution stretched over a refracted, magnified view; H2: blended cloud layers writing depth make layer order matter in the cubemap. Primary-ray sky (drawn to the albedo buffer at screen resolution) is not affected in the outdoor checkpoints [EXP pending] |
| Confirmed root cause | not yet: needs an A/B build (cubemap 1024; blended sky layers without depth write) |
| Proposed universal correction | if H1: cubemap size as a quality setting (e.g. 512/1024); if H2: depth write off for blended sky layers (raster parity). Both generic |
| Regression test | sky checkpoint in `1_1_Palenque` (POC-89) |
| Performance implications | none expected |
| Owner track / POC | **R1 proposal: engine-other (RT sky), lead to assign**; FXT if H2 (blend/depth state). POC-89 |
| Status | investigating (2026-11-28, R1) |
| Links | [EXP-018](experiments/EXP-018-rt-tse.md), [EXP-025](experiments/EXP-025-rendering-audit.md) |

### RDF-005: Chainsaw first-person particles not drawn in RT

| Field | Value |
|---|---|
| ID | RDF-005 |
| Reported | 2026-11-28, preview2 release notes (known issue) |
| Reproduction | TSE, RT, fire the chainsaw in first person |
| Campaign | TSE (TFE to check) |
| Renderer | RT |
| Affected class | first-person weapon particles |
| Kind | engine (RT particle path) |
| Severity | S3 |
| Suspected root cause | [ASM] side effect of `c1537cfd` (no RT particle building outside the RT particle pass, which fixed a null-scene crash with these particles). See RD-017 H5 |
| Confirmed root cause | not yet (POC-84) |
| Proposed universal correction | route first-person particles into the RT particle pass with a valid scene, without reintroducing the crash |
| Regression test | first-person weapon particle checkpoint; crash regression on `1_2_Palenque` |
| Performance implications | small (a few dynamic particles per frame) [ASM] |
| Owner track / POC | FXP (FX2), POC-84 |
| Status | triaged (2026-11-28) |
| Links | [EXP-017](experiments/EXP-017-engine-integration.md) |

### RDF-006: SE1 fog and haze not shown in RT

| Field | Value |
|---|---|
| ID | RDF-006 |
| Reported | 2026-11-28, preview2 release notes (known issue) |
| Reproduction | TSE levels with sector fog or haze, RT on, compare with Vulkan raster |
| Campaign | TSE; TFE to check (Serious-Engine-RT disables haze on several TFE worlds) |
| Renderer | RT |
| Affected class | sector fog and haze |
| Kind | engine (RT layer) |
| Severity | S2: atmospheric intent lost in many TSE areas |
| Suspected root cause | [SRC] EXP-018 A1: RT haze darkened everything beyond ~20 m, so preview2 sets RT haze off by default; SE1 fog is not translated into an RT medium |
| Confirmed root cause | **[SRC] (R1): the RT layer renders no SE1 fog or haze at all.** The only consumer is a boolean "camera is in a fog/haze sector": `RT_CheckViewerInHaze` (`Engine/Raytracing/RTModelCulling.cpp:269-300`) calls `GetHaze`/`GetFog` into dummy `CHazeParameters`/`CFogParameters` that are discarded and sets `Scene::SetCameraIsInHaze`; `SSRT.cpp:652` then sets `typeOfMediaAroundCamera = RG_MEDIA_TYPE_WATER` (water extinction from `srt_vWaterExtinction` x `srt_fWaterDensityMultiplier`, not the sector's colour or distances). That is the blue cast / far darkening of EXP-018 A1. Haze (`hp_colColor`, `hp_fNear`, `hp_fFar`, `hp_fDensity`) and fog (`fp_colColor`, `fp_fH0..H3`, `fp_fFar`, `fp_fDensity`, `fp_vFogDir`) never reach RTGL1; `RTLights.cpp:647` keeps `fFogHazeFade = 1`. RTGL1 in this tree has no fog/volumetric parameter (`RTGL1.h:1054`: media VACUUM/WATER/GLASS only). TFE uses the same code [SRC]; RT vs raster captures in EXP-025 |
| Proposed universal correction | (1) RTGL1 (generic, upstreamable): a cheap analytic distance + height fog term applied to primary-ray depth in compositing (colour, near/far or density, height band, direction), sky = far; (2) engine: per camera sector translate `CHazeParameters`/`CFogParameters` into it the way raster's `CRenderer::SetupFogAndHaze` does; (3) stop mapping haze to `RG_MEDIA_TYPE_WATER`. Behind a cvar; default on only after A/B (RD-016 Q11, RD-017 §6) |
| Regression test | R1 scene set fog/haze checkpoints (EXP-025 §3: `tse-fog-*`, `tfe-fog-*`); RT vs `vk-orig` far-field luma; far-field brightness check of EXP-018 A1 must not regress |
| Performance implications | analytic fog: one term per pixel, < 0.1 ms at 1440p [ASM]; volumetrics not needed for parity |
| Owner track / POC | **R1 proposal: FXT** (atmospherics are RD-017; RTGL1 change coordinated by the lead), LIGHT consulted for exposure. POC-80/POC-83 |
| Status | root-caused (2026-11-28, R1) |
| Links | [EXP-018](experiments/EXP-018-rt-tse.md), [EXP-025](experiments/EXP-025-rendering-audit.md) |

### RDF-007: Engine screenshots grey in Vulkan

| Field | Value |
|---|---|
| ID | RDF-007 |
| Reported | 2026-11-28, preview2 release notes (known issue); also EXP-011 issue 8 |
| Reproduction | Vulkan raster, take an engine screenshot |
| Campaign | TFE, TSE |
| Renderer | Vulkan raster and RT |
| Affected class | screen grab / read-back (engine screenshots, and every other `CDrawPort::GrabScreen` user, e.g. save-game and demo thumbnails) |
| Kind | engine |
| Severity | S4 for players; it blocks in-engine captures for the comparison harness (POC-90) and the quality guard (POC-45) |
| Suspected root cause | [ASM] the Vulkan back-end's screen grab does not read back the presented image |
| Confirmed root cause | **[SRC] (R1): not implemented.** `CDrawPort::GrabScreen` (`Engine/Graphics/DrawPort.cpp:1188-1291`) fills the buffer with `memset(..., 128, ...)` (uniform grey) and only OpenGL (`pglReadPixels`) and D3D overwrite it; the `GAT_VK` and `GAT_RT` branches (`:1277-1289`) only print "not implemented" in debug builds |
| Proposed universal correction | Vulkan: copy the last presented swapchain image (or the final colour target) to a host-visible buffer after the frame fence (`vkCmdCopyImageToBuffer`, BGRA->RGB); RT: RTGL1 has no read-back API in this tree, so either an RTGL1 "copy final image" entry point or a grab before present in the RT drawport |
| Regression test | screenshot of a known frame matches an external capture within the quality guard |
| Performance implications | none in normal play |
| Owner track / POC | **R1 proposal: engine-other** (Vulkan back-end; not on the M0.1 critical path). The R1 harness does not need it: it captures the window with `PrintWindow`, which works in all 7 configurations. POC-45 |
| Status | root-caused (2026-11-28, R1) |
| Links | — |

### RDF-008: RT options listed in the Vulkan rendering-options menu

| Field | Value |
|---|---|
| ID | RDF-008 |
| Reported | 2026-11-28, VS-E status (lead-accepted known issue) |
| Reproduction | Vulkan mode, Options → Video → Rendering options |
| Campaign | TFE, TSE |
| Renderer | Vulkan raster; OpenGL [ASM] |
| Affected class | menu (rendering options) |
| Kind | engine (menu configuration include) |
| Severity | S4 |
| Suspected root cause | [SRC] EXP-017: the RT options are included unconditionally into the rendering-options menu and only shown disabled outside RT |
| Confirmed root cause | partly (mechanism known) |
| Proposed universal correction | hide renderer-specific options when that renderer is not active |
| Regression test | menu test list: options per renderer |
| Performance implications | none |
| Owner track / POC | UI1, POC-87 |
| Status | triaged (2026-11-28) |
| Links | [EXP-017](experiments/EXP-017-engine-integration.md) |

### RDF-009: Sky instead of distant hillside in TSE 1_1_Palenque RT

| Field | Value |
|---|---|
| ID | RDF-009 |
| Reported | 2026-11-28, EXP-018 R3 (first observed TSE RT tuning artefact) |
| Reproduction | TSE `1_1_Palenque`, RT, look toward the distant hillside and trees that raster draws |
| Campaign | TSE |
| Renderer | RT |
| Affected class | background geometry / World Base handling |
| Kind | engine (RT layer) |
| Severity | S3 |
| Suspected root cause | [ASM] background geometry or World Base handling that Serious-Engine-RT solved per TFE level; TSE has only generic defaults |
| Confirmed root cause | **[EXP] EXP-018 "Correction to R3": not a defect.** At the level start the player is under water; raster draws the scene above the surface without refraction, RT refracts through the water surface and shows sky. R1 re-check in EXP-025 (spawn view, `vk-orig` vs `rt-orig`) |
| Proposed universal correction | none (physically correct RT behaviour) |
| Regression test | distant-view checkpoint in `1_1_Palenque` |
| Performance implications | none expected |
| Owner track / POC | none (R1 proposes `wont-fix: not a defect`, lead approval) |
| Status | root-caused (2026-11-28); proposed wont-fix |
| Links | [EXP-018](experiments/EXP-018-rt-tse.md), [EXP-025](experiments/EXP-025-rendering-audit.md) |
