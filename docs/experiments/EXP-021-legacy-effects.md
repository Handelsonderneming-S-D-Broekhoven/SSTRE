# EXP-021: Legacy light volumes, lightning and effect blending in RT (POC-80..83)

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | POC-80, POC-81 (steps 1–2), POC-82, POC-83 (stage M0.1); feeds [RD-017](../research/RD-017-legacy-effects-reconstruction.md) §9.1 and §9.2, RDF-002, RDF-003 |
| Status | **partial.** Root causes confirmed for RDF-002 (two mechanisms) and RDF-003. Generic fixes on `m01/fxt` behind cvars (default on). Lightning verified across the 7 configurations plus corrected RT. Light-beam dimming verified at one location. Not done: volumetric/HDR replacement (POC-81 steps 4–5, not yet justified) and a capture of an additive translucent-brush case (none in the slice levels) |
| Track | FXT (L3 + FX1) |
| Environment | Windows 11 Pro 22631, RTX 4070 12 GB. VS 2022 (v143), Vulkan SDK 1.4.363.0. Window 1600×900, `srt_bVSync=0`, `srt_bDebugValidation=0`, god mode for level runs |
| Inputs | SSTRE-Engine `sprint2/integration` @ `7eeed884` (the preview2 engine); RTGL1 clean-room build of EXP-017 (unchanged); TFE/TSE runtimes with original textures and with slice-v1 (VS-A); the Classic-VK reference runtime |
| Outputs | SSTRE-Engine branch `m01/fxt` (§7). No RTGL1 change, no Toolkit/AssetCompiler change |

Evidence labels: **[DOC]**, **[SRC]**, **[EXP]**, **[ASM]**. Following GATE-05, this report names levels, entity classes, engine identifiers, and blend and flag names only. The per-asset census lines, positions and captures stay in the track's local workspace.

## 1. Questions

1. POC-80: what do the "translucent white boxes" that stand for light shafts and light entering rooms (RDF-002) consist of in SE? How does the SE-RT/SSTRE RT layer map them to RTGL1?
2. POC-82: why does lightning look like a badly cut-out picture that switches on and off (RDF-003)? Is the cause in the asset or in the renderer, judged across the 7 configurations?
3. POC-81/83: which generic corrections follow from the answers, behind cvars and with raster unchanged?

## 2. Method

- **[SRC]** Reading of the RT layer (`Engine/Raytracing/RTBrushes.cpp`, `SceneBrushes.cpp`, `RTModels.cpp`, `RTParticles.cpp`, `Scene.cpp`), of the SE raster paths it imitates (`Rendering/RenCache.cpp` `MakeScreenPolygon`, `Graphics/DrawPort_RenderScene.cpp`, `Models/RenderModel_View.cpp`, `Rendering/RenderModels.cpp` `FindModelLights`), of the effect entities (`Lightning.es`, `StormController.es`, `WorldBase.es`, `Common/Particles.cpp` `Particles_Lightning`), and of RTGL1's shaders (`HitInfo.inl` `processAlbedo*`, `RtAlphaTest.rahit`, `RsRasterizer.frag`) and frame order (`VulkanDevice.cpp`).
- **[EXP]** A diagnostic census in the engine, `srt_iEffectCensus` (default 0). At each scene upload it prints every class of non-opaque brush polygon as a key: polygon flags, the blend and layer-alpha class of each layer, the texture's alpha channel/effect/animation flags, and the RT class the polygon gets. It also prints each distinct model-surface class (translucency type, shading, RT path, blend factors, emissive) and each particle-flush class (`PBT_*`, texture alpha flag, RT path). With value 2 it adds local lines with file names and positions. These are not published.
- **[EXP]** Level and world scans of the `.wld` data for entity classes and referenced models (local script).
- **[EXP]** Captures with a copy of the VS-E harness, with the rule-1c watchdog kept and every run under the GPU lock. The same binary is used for A/B, with the new cvars set to 0 (preview2 behaviour) or 1.
- **[EXP]** An asset check on the slice-v1 textures against the originals: black level of dark-background texels, RGB in transparent texels, and alpha coverage (local CSV).

## 3. Findings: translucent light volumes (POC-80, RDF-002)

### 3.1 What the light volumes are in SE

- **[EXP]** In the slice levels the census finds very few translucent *brush* polygons. TSE `1_0`, `1_1`, `1_2` and TFE `01_Hatshepsut` each have 1–7 classes: the storm-cloud layer of the background sky, water surfaces, a few wall-edge decorations (translucent portal, first layer ALPHA with partial layer alpha, RGB texture), and some fullbright non-portal polygons whose first layer is ADD.
- **[EXP]** The light shafts in TSE `1_0`/`1_1`/`1_2` (also `1_3` and `2_4`) are **models**, not brushes. The level scan finds the light-beam effect models referenced by these worlds (model entities; the exact holder class was not checked [ASM: ModelHolder2]).
- **[EXP]** The census classifies their surfaces as **STT_ADD, not fullbright (shaded)**, with an RGB or alpha texture. The RT path is **rasterized** with blend (SRC_ALPHA, ONE), and the colour is the plain surface colour (≈ 0.99 white).
- **[SRC]** SE raster (`RenderModel_View.cpp`) multiplies the surface colour of shaded surfaces per vertex by the model light. That light comes from `CRenderer::FindModelLights` (the sector ambient and the shadow-map layers under the model, directional ambient, gradients) after `AdjustShadingParameters`. SE also attenuates the alpha of translucent surfaces in haze and fog.
- **[SRC]** The RT layer (`RTModels.cpp`) sets every model surface to the constant surface colour ("pcolMipBase … we don't need it"). It never calls `FindModelLights` and sets ambient white, light black. That is correct for ray-traced surfaces, which RTGL1 lights itself. It is wrong for the rasterized blended surfaces: RTGL1 composites them unlit on the tone-mapped image after the ray-traced frame (`VulkanDevice.cpp`: `Compose` → `DrawToFinalImage`).
- **Root cause A (light-beam models) [SRC+EXP]:** SE's model lighting is missing on rasterized blended model surfaces. Additive beams that SE dims with the local light (often to a small fraction in interiors) are drawn at full white in RT. RT interiors are also darker (RDF-001), so the beams stand out further and their box-like geometry becomes visible.

### 3.2 Translucent brushes: blend translation table

**[SRC]** How the RT layer translated SE's polygon blend state in preview2 (`RTBrushes.cpp` `RT_GetPassThroughType`, RTGL1 `HitInfo.inl`, `RtAlphaTest.rahit`):

| SE polygon / layer state | SE raster | preview2 RT | Mismatch |
|---|---|---|---|
| opaque polygon, layer 0 OPAQUE or ALPHA (full alpha) | opaque, lit by shadow map | ray traced OPAQUE, lit | none |
| `BPOF_TRANSPARENT` | alpha test, z-write | ray traced ALPHA_TESTED (threshold on `avg(rgb)*a + a`) | small (threshold) |
| `BPOF_PORTAL\|BPOF_TRANSLUCENT`, layer 0 ADD | translucent pass, ONE/ONE, no z-write | ray traced **ALPHA_TESTED**; RTGL1's layer combiner starts at white, so ADD gives **white albedo**; texels pass the test because alpha = 1 → **opaque, lit, shadow-casting white surface** | **yes (white box)** |
| translucent portal, layer 0 ALPHA, partial layer alpha or no texture alpha | SRC_ALPHA/INV_SRC_ALPHA | ALPHA_TESTED: opaque where the test passes, invisible elsewhere; layer alpha only moves the cut | **yes** |
| translucent portal, layer 0 ALPHA, alpha-channel cut-out texture, full alpha | blended cut-out | ALPHA_TESTED | acceptable (lattices, foliage) |
| translucent portal, layer 0 SHADE | DST_COLOR/SRC_COLOR | ALPHA_TESTED, albedo = 2·texture | **yes** |
| any ray-traced polygon with layer 0 ADD (non-portal effects) | ONE/ONE onto the frame | white albedo | **yes** |
| entity opacity < 1 | per-polygon copy of the blend | **changed the world's shared blending table** through a reference (`UBYTE &layerBlending = tb.tb_ubBlendingType`) | **bug** |
| layer colours (RGB) | used | ignored (`IGNORE_BRUSH_COLOR`) for ray-traced layers | by design for RT; wrong for blended layers |
| animated texture blendings (`WorldBase.es` storm/lightning flash, pulsing alphas) | per frame | frozen at upload | open (§6) |

- **Root cause B (translucent brushes) [SRC]:** the RT layer maps every translucent portal to RTGL1's ray-traced alpha-tested class and ignores the SE blend function. With an additive first layer, RTGL1's combiner gives exact white. These polygons are rare in the slice levels, but where they occur they give the same "white box" symptom.

## 4. Findings: lightning (POC-82, RDF-003)

- **[SRC]** `Lightning` (triggered by `StormController`) draws its bolt with `Particles_Lightning`: lines with `PBT_ADDALPHA` (SRC_ALPHA, ONE) on an **RGB-only** texture (black background, no alpha channel), with per-line vertex alpha for branch strength and the 1.5 s fade. It also flashes the world shading through `WorldSettingsController` and an animated `Light`.
- **[SRC+EXP]** The per-texture tuning list `alpha_test_particles` from Serious-Engine-RT contains this texture. `RT_Particle_Flush` therefore uploads non-background strikes as **ray-traced ALPHA_TESTED dynamic geometry** (census: `pbt=ADDALPHA tex:rgb -> TRACED_ALPHA_TESTED`). The consequences:
  - The texture alpha is 1 everywhere, so the black background passes the test and the bolt quads become solid.
  - The quads are lit, specular and shadow-casting. 1_0 RT shows them as dark or teal tubes with hard outlines.
  - All lines of one flush take the colour of the first vertex.
  - The fade becomes an on/off switch once vertex alpha crosses the threshold.
  - Strikes on background entities (`ENF_BACKGROUND`) were already rasterized into the sky (census `sky=1`).
- **7-configuration matrix, TSE `1_0_InTheLastEpisode`, storm strike and time-machine arcs, captures every second from 30 to 76 s [EXP]:**

| # | Config | Lightning look | Coverage |
|---|---|---|---|
| C1 | Classic-VK, Vulkan, original | thin glowing cyan/violet arcs, soft fade | executed |
| C2 | SSTRE Vulkan, original | as C1 | executed |
| C3 | SSTRE Vulkan, enhanced (slice-v1) | as C1 | executed |
| C4 | SSTRE OpenGL, original | as C1 | executed |
| C5 | SSTRE OpenGL, enhanced | as C1 (full storm strike with flash captured) | executed |
| C6 | SSTRE RT, original, preview2 path | solid dark/teal outlined quads, lit and shadowed, switching off | executed |
| C7 | SSTRE RT, enhanced, preview2 path | as C6 | executed |
| C8/C9 | SSTRE RT, corrected (`srt_iAdditiveEffectMode=1`), original/enhanced | glowing arcs and full storm bolt as in raster | executed |

- **Asset side [EXP]:** slice-v1 does not contain the lightning texture, so every configuration uses the Classic texture. A3's verdict is the same (reused). Across the slice-v1 textures with a dark background, black stays black (p99 lift ≤ 3/255 for the effect-like ones), and no transparent-texel coverage changed by more than 2 points. Asset cause: **none**.
- **Root cause C (lightning) [SRC+EXP]:** a renderer-side mis-classification. A per-texture alpha-test list overrides the additive blend semantics. The enhanced-vs-original axis has no effect.

## 5. Corrections (POC-81 steps 1–2, POC-83)

These are generic, keyed on engine blend and flag semantics only, each behind a cvar. **0 restores preview2 behaviour exactly; the default is 1** (justified by the captures in §4 and §3). Raster code is untouched apart from the new `RT_*` helpers.

| Cvar | Effect |
|---|---|
| `srt_iTranslucentBrushMode` (persistent, default 1) | Translucent portal polygons whose first layer is ADD or SHADE, or ALPHA without a cut-out texture (no alpha channel or partial layer alpha), are **rasterized per layer with their SE blend function**. They are depth-tested against the ray-traced depth (RTGL1 copies it for the rasterizer), are not written to depth, and are not part of the ray-traced scene (no shadows, no lighting). Water, mirrors and warp portals are excluded. Parts are cached at scene upload and uploaded each frame for the brush entities the RT culling visits; movable brushes use their lerped placement. Ray-traced geometry with an ADD first layer uses the texture as base colour instead of white. Also fixes the shared-blending-table mutation. |
| `srt_iAdditiveEffectMode` (persistent, default 1) | `PBT_ADD`/`PBT_ADDALPHA` particles and `STT_ADD`/`STT_MULTIPLY` model surfaces are **never forced to alpha test by the per-texture tuning lists**. They keep the rasterized blend path. This is a semantic rule, and the lists stay in force for the other blend classes. |
| `srt_iEffectModelShading` (persistent, default 1) | For models with alpha surfaces, the RT layer looks up the SE model light (`RT_FindModelLights`: a private `CRenderer` instance calling `FindModelLights`, then `AdjustShadingParameters`). It lets `UnpackFrame` compute SE's per-vertex light (`RT_PrepareModelShading`, without overbright) and passes **per-vertex colours** for non-fullbright TRANSLUCENT/ADD/MULTIPLY surfaces to the rasterized upload. Fullbright and ray-traced surfaces are unchanged. |
| `srt_iEffectCensus` (default 0) | Diagnostic (§2). |

Generic across effect classes: these rules apply to every effect that uses the blend class. That covers electricity and energy rays (the TFE GhostBuster ray was on the same list), flares, fire, explosions, teleport and projectile particles, and translucent brush effects, not only lightning.

**Light-beam check, TSE `1_1_Palenque` start [EXP]** (session E, ledger `20261128194955-FXT-6120`). Same binary for all runs. NETRICSA was closed with ESC at 16 s.

- With `srt_iEffectModelShading=1`, the light-beam model in culling range gets an SE-shaded vertex colour of mean (0.61, 0.56, 0.52) instead of the constant 0.99 white of the preview2 path. That is about 43 % less light, coming from the shadow-map light under the model.
- In the capture the additive beam wedge above the pool is visibly dimmer and keeps its shading gradient.
- The view is from under water: RT shows the open-air sky through the surface (RDF-010), and Vulkan shows only the underwater tint, so a pixel comparison with raster is not meaningful there.
- An out-of-water view of a beam in an interior is **deferred** to R1's regression scenes (POC-89). Positions for it are available locally from `srt_iEffectCensus=2`.

Translucent brushes (`srt_iTranslucentBrushMode`) [EXP]:
- In the same level, census class 4 (wall-edge translucent ALPHA, partial alpha) moves to RASTER_BLENDED.
- No other change was visible in the 1_0/1_1 captures.
- No slice level contains an additive translucent-portal light volume, so the brush rule is verified only by source and census, not by a capture of a white-box case. A capture is deferred to the first R1 checkpoint that contains one.


## 6. Not done, rejected, open

- **Rejected [ASM]:**
  - Removing or hiding "white translucent" geometry, or classifying it by texture colour or name (directive §3).
  - Extending the per-level `ignore_polygons` lists that Serious-Engine-RT uses for TFE (per-level workaround).
  - Editing the `alpha_test_particles` list per texture. The semantic rule makes the entry moot for additive use and keeps the list for other classes.
- **POC-81 steps 3–5 (deferred):** the compositing pass with depth already exists in RTGL1 (raster on ray-traced depth). It is used by the fixes above, and no RTGL1 change is needed. Not done:
  - volumetric replacement of beam geometry;
  - HDR emissive with bloom: the rasterized effects are drawn after tone mapping in LDR, like raster;
  - a synchronized RT light for strikes (the SE `Light` entity animation is already converted by the RT light path, which is LIGHT's scope).
  None is justified until the corrected look has been reviewed against Classic. They are candidates if the owner wants effects brighter than Classic in RT.
- **Open, engine:**
  - Animated world texture blendings (`WorldBase.es` storm darkening, lightning flash on world shading, pulsing translucent alphas) are frozen at RT scene upload. The fix is per-frame layer colours for the affected parts.
  - Scrolling or effect textures on rasterized translucent brush parts are not updated per frame (the tex-coords are cached).
  - SE haze/fog alpha attenuation of translucent surfaces is not reproduced (RDF-006).
  - `PBT_TRANSPARENT` particles are rasterized with (ZERO, ONE) and therefore invisible (`RTParticles.cpp`), handed to FXP.
  - The census reports water polygons as "RASTER_BLENDED" because it does not know the water class. Water itself is excluded from the rule.
- **Open, data:** the Serious-Engine-RT texture lists remain the source for other RT classes. Turning them into declarative class rules belongs to ADR-0016.

## 7. Commits (SSTRE-Engine `m01/fxt`, base `sprint2/integration` @ `7eeed884`; TFE and TSE trees identical)

| Commit | Subject |
|---|---|
| `e60381d3` | rt(fx): blend-semantic translation of translucent brushes, effect census |
| `ea90c65c` | rt(fx): additive particles are never alpha-tested (lightning). Touches `RTParticles.cpp` only (shared with FXP) |
| `9e244975` | rt(fx): SE model shading for rasterized effect model surfaces. Touches `Rendering/Render.cpp` and `Models/RenderModel_View.cpp` with new `RT_*` helpers only |
| `5ebab5c3` | rt(fx): census prints the mean SE-shaded vertex colour (diagnostic) |

Builds: Windows Release x64, TFE and TSE, exit 0. Linux is not built (no platform-specific code).

## 8. Measurements and coverage

| Run / session | Question | Coverage | Ledger |
|---|---|---|---|
| A (5 runs) | census of the effect classes in TSE 1_0/1_1/1_2 and TFE 01 (RT) | executed (before directive #26) | `…-FXT-8204` |
| B1/B2 | lightning on 1_0, RT, same binary with `srt_iAdditiveEffectMode` 0/1 | executed, pass | `…-FXT-2355` |
| B3/B4 | light-beam classes on TSE demo 1 (RT census, Vulkan) | executed, inconclusive (beams not in view) | `…-FXT-7877` |
| C1–C9 | lightning matrix on 1_0 (§4) | executed (started before directive #26); enhanced axis = A3 verdict, reused | `…-FXT-8782` |
| D (6 runs) | beams at the 1_1/1_2 spawn | **invalidated** (NETRICSA covered the view) | `…-FXT-691` |
| E (3 runs) | beam shading A/B at the 1_1 start | executed, pass (partial, see §5) | `20261128194955-FXT-6120` |
| TFE RT A/B of the new cvars | — | **deferred** (TFE census showed only sky and water translucency; TFE trees build and share the code) | — |
| OpenGL/Vulkan regression of the shared `Render.cpp`/`RenderModel_View.cpp` change | C2–C5 ran on the patched binary; lightning and scene look identical to Classic-VK | executed | `…-FXT-8782` |

Results:
- RTGL1 errors: 0 in all RT runs.
- Watchdog: ok in every run (no kill).
- Focus: lost in sessions A and B (the captures still hold; no input was injected), held in C.
- Cost [EXP, indicative, HUD FPS, same view]:
  - 1_1 start: 79.3/77.7 FPS with model shading vs 78.7/77.0 without;
  - 1_0: about 148–155 FPS with all three cvars at 0 or 1.
  - No measurable cost. The work per frame is a few rasterized parts and one light lookup per alpha-surface model. Formal measurement is E3's (POC-91).


## 9. A3 spec (effect-texture recipe, for POC-85)

Classification comes from the engine use found by the census (particle `PBT_*`, model `STT_*`, brush layer `STXF_BLEND_*`, translucent portal), never from colour or file name.

1. **Additive classes** (`PBT_ADD`, `PBT_ADDALPHA`, `STT_ADD`, `STXF_BLEND_ADD`): texels with max(RGB) ≤ 4/255 in the original stay ≤ 4/255 at p99 after processing. Under additive blending, any lift shows as a grey box or halo.
2. RGB-only effect textures stay RGB-only: no alpha channel added, flags unchanged. `PBT_ADDALPHA` takes its alpha from the vertex colour.
3. Straight alpha only, never premultiplied. RGB in transparent texels within 4/255 of the original, and alpha coverage at 128 within ±2 points per mip (P3-6).
4. No generative super-resolution or sharpening for effect classes. Use conventional resampling or keep the original, and fall back to the original on any QA failure.
5. Animated and multi-frame effect textures: process all frames identically or none.

A3 has finished; slice-v2 (effect-safe) exists. It was not needed here, because the lightning texture is Classic in every configuration.


## 10. Defects handed over after this work (lead, 2026-11-28): first triage only

- **RDF-006** (fog/haze) and **RDF-010** (underwater looks like air): R1's root cause stands. The fix needs an RTGL1 fog term plus per-sector media classification; it is not linked to the fixes here. **Deferred.**
- **RDF-012** (no lens flares/coronas in Vulkan raster) [SRC, first reading]: the Vulkan branch of `UpdateDepthPointsVisibility` (`Graphics/DepthCheck.cpp`) answers depth points with occlusion queries (`CreateOcclusionQuery(…, di_fOoK)`, then `GetOcclusionResults`). Two suspects:
  - depth convention or timing of those queries against the scene depth;
  - `queries[0].queryId` is read even when no query was created.
  Not reproduced here. **Deferred** (S3, pre-existing in Classic-VK).
