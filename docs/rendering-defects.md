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
| [RDF-004](#rdf-004-sky-streaks-in-tse-1_1_palenque-rt) | Sky streaks in TSE `1_1_Palenque` RT | TSE | RT | engine | S3 | investigating | engine-other (R1 proposal) → lead | POC-89 |
| [RDF-005](#rdf-005-chainsaw-first-person-particles-not-drawn-in-rt) | Chainsaw first-person particles not drawn in RT | TSE | RT | engine | S3 | triaged | FXP (FX2) | POC-84 |
| [RDF-006](#rdf-006-se1-fog-and-haze-not-shown-in-rt) | SE1 fog and haze not shown in RT | TFE, TSE | RT | engine (+RTGL1) | S2 | root-caused | FXT | POC-80, POC-83 |
| [RDF-007](#rdf-007-engine-screenshots-grey-in-vulkan) | Engine screenshots grey in Vulkan | TFE, TSE | Vulkan raster, RT | engine | S4 | root-caused | engine-other (lead to assign) | POC-45 |
| [RDF-008](#rdf-008-rt-options-listed-in-the-vulkan-rendering-options-menu) | RT options listed in the Vulkan rendering-options menu | TFE, TSE | Vulkan raster, OpenGL [ASM] | engine | S4 | triaged | UI1 | POC-87 |
| [RDF-009](#rdf-009-sky-instead-of-distant-hillside-in-tse-1_1_palenque-rt) | Sky drawn instead of distant hillside in TSE `1_1_Palenque` RT | TSE | RT | not a defect | — | wont-fix | none | POC-89 |
| [RDF-010](#rdf-010-under-water-looks-like-open-air-in-tse-rt-no-water-medium) | Under water looks like open air in TSE RT | TSE | RT | engine | S3 | root-caused | FXT | POC-80 |
| [RDF-011](#rdf-011-first-person-weapon-framed-differently-in-rt-weapon-fov-ignored) | First-person weapon framed differently in RT (weapon FOV ignored) | TFE, TSE | RT | engine | S2 | root-caused | WPN | POC-96 |
| [RDF-012](#rdf-012-lens-flares-and-light-coronas-missing-in-vulkan-raster) | Lens flares and light coronas missing in Vulkan raster | TSE (TFE to check) | Vulkan raster | engine (inherited from Classic-VK) | S3 | triaged | FXT | POC-83 |
| [RDF-013](#rdf-013-sunlit-outdoor-scenes-brighter-and-flatter-in-rt-than-in-raster) | Sunlit outdoor scenes brighter and flatter in RT | TSE | RT | engine | S3 | triaged | LIGHT | POC-76 |
| [RDF-014](#rdf-014-weapon-viewmodel-clips-into-walls-layers-not-separated-framing-too-zoomed-out) | Weapon viewmodel clipping, layering and framing | TFE, TSE [ASM] | to establish | engine | S2 | triaged | WPN | POC-96 |
| [RDF-015](#rdf-015-tse-chainsaw-model-shows-graphical-glitches) | TSE chainsaw model glitches | TSE | to establish | unknown | S3 | new | WPN | POC-97 |
| [RDF-016](#rdf-016-ultrawide-aspect-ratios-match-no-aspect-adjuster-window) | Ultrawide aspect ratios match no adjuster window | TFE, TSE | all | engine | S2 | root-caused | WPN | POC-96 |
| [RDF-017](#rdf-017-hud-scales-by-width-only-and-is-about-134-too-large-on-ultrawide) | HUD scales by width only (1.34× on ultrawide) | TFE, TSE | all | engine | S3 | root-caused | UI1 (follow-up) | POC-87 |

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
| Reproduction | Play interiors that are adequately lit in Vulkan raster with RT on, in both campaigns; exact checkpoints to be defined by R1 in POC-89 (several per campaign, incl. non-showcase levels). Historic case: TSE `1_2_Palenque` spawn cave was black in RT until per-level cutscene lights were added (EXP-017 R3/R12). **R1 checkpoints (non-showcase, no manual lights):** `tse-corr-2_1m3` (torch-lit corridor: raster luma 33.9, RT 1.8, 97 % of pixels near-black, the torch flame is the only visible object; the weapon is black too), `tse-vol-2_4m1` (hall: raster 39.4, RT 10.7). The research sweep (`vk-enh` vs `rt-enh`) found the same in `tse-room-2_2m1`, `tse-part-2_2m20`, `tse-cave-3_1m20` and `tse-cave-3_2m18` (RT almost black; only emissive surfaces and particles visible), and in `tse-dark-1_3m20` (the red light colour of the room is lost: RT grey-brown). Outdoor and moonlit checkpoints (`tse-out-1_3m10`, `tse-snow-3_2m1`, `tse-night-3_1m1`) are lit. Local light sources (torches, lit windows) add nothing in RT. Details in EXP-025 §4. Fixed exposure −4 gives the same result (luma 1.7), so it is missing light, not exposure |
| Campaign | TFE, TSE |
| Renderer | RT; original and enhanced textures |
| Affected class | world lighting: sector ambient, brush shadowmap illumination, light entities (classes to be listed by POC-75) |
| Kind | unknown; engine/RT layer suspected |
| Severity | S1: areas become unplayably dark; central to Preview3 (P3-1..P3-3) |
| Suspected root cause | [ASM] RT does not use sector ambient and shadowmap illumination, and filters out some light entities (helper or invisible lights, threshold, culling); possibly worsened by exposure. See [RD-016](research/RD-016-legacy-lighting-reconstruction.md) H1–H4 |
| Confirmed root cause | not yet (POC-75) |
| Proposed universal correction | RD-016 order: native light conversion → legacy ambient term → lightmap-assisted compensation → probes only if needed; no per-level lights; remove the 1_2 cave override when redundant |
| Regression test | lit interior and intentionally dark checkpoints of the validation level set; P3-1, P3-2, P3-3. R1 harness: `matrix.ps1 -Ids tse-corr-2_1m3,tse-vol-2_4m1,tfe-corr-03m8,tfe-room-04m6 -Configs cvk,rt-orig,fix` with LIGHT's Bin, metric RT luma vs `cvk` (target within ±25 % at fixed exposure, no area < 50 % of raster) |
| Performance implications | to be measured per step (no point-light explosion; ambient term target ≤ 0.5 ms at 1440p [ASM]) |
| Owner track / POC | LIGHT (L1, L2), POC-75..79 |
| Status | triaged (2026-11-28) |
| Links | [EXP-017](experiments/EXP-017-engine-integration.md), [EXP-018](experiments/EXP-018-rt-tse.md) |

### RDF-002: Translucent light volumes drawn as white boxes

| Field | Value |
|---|---|
| ID | RDF-002 |
| Reported | 2026-11-28, owner manual test of 0.1.0-preview2 |
| Reproduction | Rooms with translucent geometry that represents light entering through openings or light shafts; RT on. **R1 checkpoint `tse-vol-2_4m1`** (TSE `2_4_TowerOfBabylon`, marker 1): raster shows two soft yellow light shafts, RT (orig and enh identically) shows two opaque white-grey boxes over an otherwise black room — not a showcase level, so the defect is generic |
| Campaign | observed in the preview2 levels and TSE `2_4` [EXP]; TFE [ASM] |
| Renderer | RT; raster (Classic-VK, SSTRE Vulkan, OpenGL) as intended [EXP]; identical with original and enhanced textures, so not asset-processing [EXP] |
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
| Confirmed root cause | not yet (POC-82). Update 2026-11-28 (A3 via lead): **renderer side, not assets.** The texture is the original one and only looks right with additive blending; in RT, the tuning texture class `alpha_test_particles` (`Engine/Raytracing/CustomInfo.cpp:228`, checked at `:862`) forces alpha test on it. FXT owns the fix |
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
| Reproduction | TSE levels with sector fog or haze, RT on, compare with Vulkan raster. R1 checkpoint `tse-haze-3_3m5` (TSE `3_3_CorridorOfDeath`): the yellow-green distance haze of raster is absent in RT |
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
| Owner track / POC | FXT (lead decision 2026-11-28); RTGL1 change coordinated by the lead, LIGHT consulted for exposure. POC-80/POC-83 |
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
| Owner track / POC | engine-other (lead decision 2026-11-28), track to be assigned by the lead (Vulkan back-end; not on the M0.1 critical path). The R1 harness does not need it: it captures the window with `PrintWindow`, which works in all 7 configurations. POC-45 |
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
| Owner track / POC | none |
| Status | **wont-fix** (lead decision 2026-11-28): intended behaviour. Evidence: [EXP] EXP-018 R3 correction — bubbles in both raster and RT prove the camera is under water at the start; raster draws the above-water scene without refraction, RT refracts through the water surface (Snell's law), so sky and hanging plants appear where raster shows the hillside. The real defects at this spot are RDF-004 (streaks in the refracted sky) and RDF-010 (no water medium) |
| Links | [EXP-018](experiments/EXP-018-rt-tse.md), [EXP-025](experiments/EXP-025-rendering-audit.md) |

### RDF-010: Under water looks like open air in TSE RT (no water medium)

| Field | Value |
|---|---|
| ID | RDF-010 |
| Reported | 2026-11-28, R1 (EXP-025), from preview2 captures of the `1_1_Palenque` start |
| Reproduction | TSE `1_1_Palenque` level start (player under water), RT vs Vulkan raster; checkpoint `tse-sky-1_1m0`. TFE check: `tfe-water-09m5` |
| Campaign | TSE (TFE to compare: TFE tables keep haze on per world) |
| Renderer | RT; original and enhanced |
| Affected class | camera inside a water/fog sector (SE1 sector fog/haze used as under-water tint) |
| Kind | engine (RT layer) |
| Severity | S3: under-water areas lose their tint and read as air; refraction shows a bright, streaky sky (RDF-004) |
| Suspected root cause | [SRC] consequence of RDF-006: the RT layer only knows "camera in fog/haze sector" → `RG_MEDIA_TYPE_WATER`, and `CustomInfo::CanHazeBeApplied` (`Engine/Raytracing/CustomInfo.cpp:943-947`) returns the tuning `haze` flag, which preview2 sets to 0 for all TSE worlds (EXP-018 A1). So with haze off the camera is in vacuum even under water. Water sectors and haze sectors are not distinguished |
| Confirmed root cause | [SRC] mechanism confirmed; [EXP] raster/RT capture pair at the `1_1` start (EXP-025 §4) |
| Proposed universal correction | part of the RDF-006 fix: classify the camera sector from SE1 data (fog/haze parameters plus the water content type of the sector or the water brush) instead of one boolean; map real water to `RG_MEDIA_TYPE_WATER` with the sector's fog colour as extinction tint, and plain haze to the new fog term; no per-world `haze` switch |
| Regression test | `tse-sky-1_1m0` (RT tint vs raster), `tfe-water-09m5`; EXP-018 A1 far-field check must not regress |
| Performance implications | none (media type is already supported by RTGL1) |
| Owner track / POC | FXT (lead decision 2026-11-28), together with RDF-006 |
| Status | root-caused (2026-11-28, R1) |
| Links | [EXP-018](experiments/EXP-018-rt-tse.md), [EXP-025](experiments/EXP-025-rendering-audit.md) |

### RDF-011: First-person weapon framed differently in RT (weapon FOV ignored)

| Field | Value |
|---|---|
| ID | RDF-011 |
| Reported | 2026-11-28, R1 (EXP-025) |
| Reproduction | any level, RT vs raster with the same frozen frame; e.g. `tse-out-1_3m10`, `tse-corr-2_1m3` |
| Campaign | TFE, TSE |
| Renderer | RT; original and enhanced |
| Affected class | first-person weapon models (`CPlayerWeapons`, `RMF_WEAPON`) |
| Kind | engine (RT layer) |
| Severity | S2: visible in every RT frame; the weapon is smaller, more centred and at a different angle than in raster/the original |
| Suspected root cause | — |
| Confirmed root cause | **[SRC]** raster draws the weapon with its own projection: `FOVL() = wpn_fFOV[weapon] * _fWeaponFOVAdjuster`, clip and depth range (`EntitiesMP/PlayerWeapons.es:1043-1053`). In RT, `CModelObject::SetupModelRendering` fills `CFirstPersonModelInfo.fovH` from that projection (`Engine/Models/RenderModel.cpp:483-494`), but `SSRTMain/Scene::ProcessFirstPersonModel` (`Raytracing/SSRT.cpp:481`, `Scene.cpp:474-476`) never uses `fovH`; the weapon is placed in camera space and rendered through the **world** projection (`plr_fFOV`). Same code in TFE (`Entities/PlayerWeapons.es`) |
| Proposed universal correction | apply the weapon projection: either scale the first-person geometry in view space by `tan(worldFOV/2) / tan(weaponFOV/2)` (x/y) before upload, or give RTGL1 a first-person projection (RTGL1 already has a first-person visibility class). Keep the first-person depth range so the weapon does not clip into walls |
| Regression test | weapon silhouette overlap RT vs `vk-orig` on `tse-out-1_3m10` and `tfe-out-06m2` (frozen frame) |
| Performance implications | none |
| Owner track / POC | WPN (lead decision 2026-11-28), POC-96, together with RDF-014/016 |
| Status | root-caused (2026-11-28, R1) |
| Links | [EXP-025](experiments/EXP-025-rendering-audit.md) |

### RDF-012: Lens flares and light coronas missing in Vulkan raster

| Field | Value |
|---|---|
| ID | RDF-012 |
| Reported | 2026-11-28, R1 (EXP-025) |
| Reproduction | same frozen frame in OpenGL and Vulkan: sun flare in `tse-out-1_3m10`, torch corona in `tse-corr-2_1m3`; present in OpenGL, absent in Classic-VK reference and SSTRE Vulkan |
| Campaign | TSE (TFE to check) |
| Renderer | Vulkan raster (Classic-VK and SSTRE alike); RT skips raster flares by design (`DrawPort.cpp:1323`, RT has `srt_bLensFlares`) |
| Affected class | light-source lens flares (`CLensFlareType`), visibility via depth point checks |
| Kind | engine (Vulkan back-end), inherited from Classic-VK; not an SSTRE regression |
| Severity | S3: sun and torch glare is part of the original look |
| Suspected root cause | [ASM] the Vulkan branch of `UpdateDepthPointsVisibility` (`Engine/Graphics/DepthCheck.cpp:199+`, occlusion queries) reports flare points as hidden (query timing or depth-range mismatch), or `gfx_iLensFlareQuality` differs per API. To verify with `-Extra "gfx_iLensFlareQuality=3;"` and a query-result trace |
| Confirmed root cause | not yet |
| Proposed universal correction | fix the Vulkan depth-point visibility path (read the depth value or use the query result of the previous frame consistently) |
| Regression test | `tse-out-1_3m10`, `tse-corr-2_1m3`: flare pixels present in `vk-orig` like in `gl-orig` |
| Performance implications | negligible |
| Owner track / POC | FXT (lead decision 2026-11-28): flares are an effect class. Pre-existing Classic-VK defect, S3, not a Preview3 blocker |
| Status | triaged (2026-11-28) |
| Links | [EXP-025](experiments/EXP-025-rendering-audit.md) |

### RDF-013: Sunlit outdoor scenes brighter and flatter in RT than in raster

| Field | Value |
|---|---|
| ID | RDF-013 |
| Reported | 2026-11-28, R1 (EXP-025) |
| Reproduction | `tse-out-1_3m10`: mean luma raster 111.6, RT 141.9 (orig) / 136.5 (enh); paving looks washed out, contact darkening from shadowmaps missing. `tse-snow-3_2m1`: raster 98.4, RT 161.7 (snow near clipping) |
| Campaign | TSE (TFE to check on `tfe-out-06m2`) |
| Renderer | RT |
| Affected class | sun-lit brush surfaces; exposure/tonemapping |
| Kind | engine (RT layer: sun intensity / exposure defaults for untuned worlds) |
| Severity | S3 |
| Suspected root cause | [ASM] generic TSE defaults `srt_fSunIntensity = 4` and auto exposure with `min log luminance = -4` (`CustomInfo.cpp:130-134`) are not calibrated against the original's sector light; the dark-interior side of the same calibration is RDF-001 |
| Confirmed root cause | not yet |
| Proposed universal correction | calibrate sun/sky intensity and exposure from SE1 data (directional light colour, sector ambient) as part of RD-016; verify with `-FixedExposure` A/B |
| Regression test | outdoor checkpoints: RT luma within ±15 % of `cvk` at fixed exposure |
| Performance implications | none |
| Owner track / POC | LIGHT (RD-016) (lead decision 2026-11-28), POC-76 |
| Status | triaged (2026-11-28) |
| Links | [EXP-025](experiments/EXP-025-rendering-audit.md) |

### RDF-014: Weapon viewmodel clips into walls, layers not separated, framing too zoomed out

| Field | Value |
|---|---|
| ID | RDF-014 |
| Reported | 2026-11-28, owner issue #28 (relayed by the lead) |
| Reproduction | walk up to a wall with a first-person weapon; compare weapon framing with the original (arm ends and stocks visible) |
| Campaign | to be established (TFE, TSE [ASM]) |
| Renderer | to be established; RT framing differs additionally, see RDF-011 |
| Affected class | first-person weapon models (`CPlayerWeapons`, `RMF_WEAPON`), viewmodel projection and depth range |
| Kind | engine |
| Severity | S2: visible in normal play all the time |
| Suspected root cause | under investigation (WPN). R1 note: raster uses a separate weapon projection (`wpn_fFOV` × `_fWeaponFOVAdjuster`, depth range 0–0.1, `EntitiesMP/PlayerWeapons.es:1043-1053`); RT ignores it (RDF-011, [SRC]); `_fWeaponFOVAdjuster` comes from the aspect adjusters (see RDF-016) |
| Confirmed root cause | not yet |
| Proposed universal correction | to be determined by WPN; one weapon projection per aspect ratio for all renderers |
| Regression test | R1 checkpoints with a weapon near a wall (to be added) plus `tse-out-1_3m10`, `tfe-out-06m2` |
| Performance implications | none expected |
| Owner track / POC | WPN, POC-96 |
| Status | triaged (2026-11-28) |
| Links | RDF-011, RDF-016 |

### RDF-015: TSE chainsaw model shows graphical glitches

| Field | Value |
|---|---|
| ID | RDF-015 |
| Reported | 2026-11-28, owner issue #31 (relayed by the lead) |
| Reproduction | TSE, select the chainsaw; exact symptoms not yet established |
| Campaign | TSE |
| Renderer | to be established |
| Affected class | first-person chainsaw weapon model (not its particles: those are RDF-005, FXP) |
| Kind | unknown |
| Severity | S3 (provisional, until the symptoms are known) |
| Suspected root cause | not yet |
| Confirmed root cause | not yet |
| Proposed universal correction | to be determined |
| Regression test | chainsaw first-person checkpoint (to be defined by WPN; harness `-Extra` can select the weapon) |
| Performance implications | unknown |
| Owner track / POC | WPN, POC-97 |
| Status | new (2026-11-28) |
| Links | RDF-005 (distinct) |

### RDF-016: Ultrawide aspect ratios match no aspect adjuster window

| Field | Value |
|---|---|
| ID | RDF-016 |
| Reported | 2026-11-28, UI1 [SRC] (relayed by the lead) |
| Reproduction | 3440×1440 (2.389) or 2560×1080 (2.370), any level |
| Campaign | TFE, TSE |
| Renderer | all |
| Affected class | aspect-dependent in-game FOV and HUD adjusters |
| Kind | engine |
| Severity | S2 on ultrawide displays (wrong FOV and HUD values); none at 16:9/16:10 |
| Suspected root cause | — |
| Confirmed root cause | [SRC] (UI1) `SetAdjusters` (`SeriousSam/SeriousSam.cpp:573`) matches exact aspect windows only; the 21:9 window is 2.32–2.34, so 2.37 and 2.389 fall back to the defaults |
| Proposed universal correction | derive the adjusters continuously from the aspect ratio (Hor+), or use nearest-window matching, for any aspect ratio |
| Regression test | UI1 resolution list (POC-87) at 3440×1440 and 2560×1080; FOV/HUD values logged |
| Performance implications | none |
| Owner track / POC | WPN (lead decision 2026-11-28), POC-96, together with RDF-011/014 |
| Status | root-caused (2026-11-28, UI1) |
| Links | RDF-014, RDF-017 |

### RDF-017: HUD scales by width only and is about 1.34× too large on ultrawide

| Field | Value |
|---|---|
| ID | RDF-017 |
| Reported | 2026-11-28, UI1 [SRC] (relayed by the lead) |
| Reproduction | ultrawide resolution (e.g. 3440×1440), in-game HUD |
| Campaign | TFE, TSE |
| Renderer | all |
| Affected class | in-game HUD layout |
| Kind | engine |
| Severity | S3 |
| Suspected root cause | — |
| Confirmed root cause | [SRC] (UI1) the HUD scale factor is computed from the width only |
| Proposed universal correction | scale by min(width/640, height/480) (or height) with safe-area anchoring, ADR-0017 |
| Regression test | UI1 resolution list (POC-87) |
| Performance implications | none |
| Owner track / POC | UI1 follow-up (lead decision 2026-11-28), POC-87 |
| Status | root-caused (2026-11-28, UI1) |
| Links | RDF-016 |
