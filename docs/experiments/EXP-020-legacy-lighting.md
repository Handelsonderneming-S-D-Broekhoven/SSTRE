# EXP-020: Legacy lighting in RT (M0.1 RD-016, POC-75..79)

Track LIGHT (L1+L2), 2026-11-28. Engine branch `m01/light` (from `sprint2/integration` @ 7eeed884).
Evidence labels: [SRC] source, [EXP] measured, [DOC] documented, [ASM] assumption.
Line numbers refer to `sprint2/integration` @ 7eeed884 unless a file is named with `m01/light`.
TFE and TSE carry byte-identical `Engine/Raytracing` sources; one citation covers both.

## Summary for RD-016

- **Root cause of dark RT interiors [SRC+EXP]:** Serious-Engine-RT converts an SE1 static
  (non-dynamic) spherical light only if its entity has a visible model, a model parent within
  2 m, or a per-level `cutscene_light` whitelist entry. Every `Light` entity is an editor model,
  so every designer-placed static light is dropped. In raster those lights are the shadow maps.
  Interiors without sun, sky or fire models are therefore lit by nothing in RT.
- `1_2_Palenque` holds 1249 such lights (876 shadow-casting point lights, 373 non-shadow
  "ambient" fill lights). About 490 of them are in RT's sector range at the spawn. E5's 25
  `cutscene_light` entries whitelisted a few of them.
- **Fix (option A, native conversion):** `srt_iLegacyLights` converts the dropped lights.
  It skips lights already represented by a fire model, so nothing is counted twice. It works
  for any level, campaign, MP or community, with no per-level data. With it, the `1_2` cave is
  as bright as with E5's manual lights, and those lights become redundant.
- Option B, a true sector-ambient term, needs an RTGL1 shader change. It is escalated, not
  built: sector ambient is rare in the measured levels, so A covers the observed defect.

## POC-75: how light reaches the image

### Raster (original SE1 / Classic-VK; SSTRE Vulkan and OpenGL are the same path)

- **Brush polygons: shadow maps [SRC].** `CLayerMixer::MixOneMipmap` fills each polygon's
  shadow map with the sector ambient colour `bsc_colAmbient`. Polygons flagged
  `BPOF_HASDIRECTIONALAMBIENT` also get the ambient colour of every directional light
  (`Light/LayerMixer.cpp:2426-2443`). Light-type gradients are added next (`:2494-2503`).
  Then every static light layer is added, point and directional, with or without shadow
  masks (`:2505-2540`). `LSF_DYNAMIC` lights are skipped there (`:2515`); they are applied
  per frame.
- **Texture modulation is 2x [SRC].** The shade layer is blended with
  `GFX_DST_COLOR, GFX_SRC_COLOR` (`Graphics/DrawPort_RenderScene.cpp:649-651`). Shadow-map
  value 128 means unchanged texture, and 255 means twice as bright.
- **Models [SRC].** `CRenderer::FindModelLights` (`Rendering/RenderModels.cpp:67-326`)
  reads the shadow layers of the polygon under the model. It adds sector ambient,
  directional ambient and gradients, plus every layer's light with the SE1 hot-spot/fall-off
  curve. It then splits the sum into one ambient and one directional term, multiplied by
  the polygon shadow colour. So models get the same static lights and ambient as the brushes.
- **Light entity types [SRC]** (`EntitiesMP/Light.es:212-261`, same in TFE `Entities/`):
  - "Point" and "Strong point" are `LSF_CASTSHADOWS` + `LSF_DIFFUSION`.
  - "Ambient" and "Strong ambient" have no shadows and no diffusion: they light every polygon
    in range regardless of normal or occluders.
  - "Strong" lights use a hot spot of 90 % of the fall-off.
  - Only directional lights carry an ambient colour.
  - Optional flags: dark light, subtract-sector-ambient, lens-flare-only, dynamic.
  - `ls_ubPolygonalMask` restricts shadow casting to illumination polygons.
  - Every `Light` entity is an editor model (`Light.es:367-371`, `InitAsEditorModel`):
    invisible in game.

### RT (Serious-Engine-RT layer as integrated in SSTRE, RTGL1)

| SE1 contribution | RT handling | Class | Evidence |
|---|---|---|---|
| Static point/fill light whose entity has no visible model (all `Light` entities) | dropped unless a model parent is within the threshold or the position is in the world's `cutscene_light` list | **lost** (main cause) | [SRC] `CustomInfo.cpp:653-690`, `:1037-1060` (`srt_bLightSphIgnoreEditorModels = 1` treats editor models as "no vertices"); `RTLights.cpp:807-816` |
| Static light on a visible model (torch, lamp model) | sphere light, radius 5 % of hot spot, fall-off `(hot spot + fall-off) x original_light_sph_falloff_multiplier` | converted | [SRC] `RTLights.cpp:316-319` |
| Fire-texture model without its own light | sphere light at the nearest dropped light (potential light) | converted (heuristic) | [SRC] `RTLights.cpp:856-931` |
| Dynamic lights (`LSF_DYNAMIC`, explosions, projectiles) | sphere light, falloff x5 clamped 3-128 m | converted | [SRC] `RTLights.cpp:310-315` |
| Directional light (sun) | one RTGL1 directional light (RTGL1 maximum 1) | converted | [SRC] `RTLights.cpp:781-797`; RTGL1 `LightManager.cpp:37` |
| Directional light ambient colour `ls_colAmbient`, `BPOF_HASDIRECTIONALAMBIENT` | not used; sky visibility in the path tracer replaces it outdoors | intentionally omitted / replaced | [SRC] no consumer in `Engine/Raytracing` |
| Sector ambient `bsc_colAmbient` | not used anywhere | **lost** | [SRC] no consumer in `Engine/Raytracing` (grep) |
| Light-type gradients | not used | lost | [SRC] no consumer |
| Dark lights, subtract-sector-ambient | skipped | intentionally omitted (no negative lights in RTGL1) | [SRC] `RTLights.cpp:764` |
| Lens-flare-only lights | flare only | correct | [SRC] `RTLights.cpp:757-767` |
| No-shadow ("ambient") lights | always shadowed and N.L-weighted by RTGL1 (no per-light shadow or diffusion flag) | **wrongly converted** (darker in corners and behind occluders) | [SRC] RTGL1 `RaygenCommon.h:496-640` |
| Hot-spot plateau + linear fall-off | RTGL1 `((f - d) / max(f - r, 1))^2`, plateau only inside the emitter radius | wrongly converted (dimmer mid-range) | [SRC] RTGL1 `RaygenCommon.h:606-608` |
| Light colour | `(c/255)^2.2`, saturation 0.75, x1; SE1 adds `c` to a 2x modulation | different units, absorbed by auto exposure | [SRC] `RTLights.cpp:96-106` |
| Lights in sectors beyond `culling_max_sector_depth` (TSE 8) from the viewer | not uploaded | culled | [SRC] `RTModelCulling.cpp:94-99`, `:231-237` |
| Light sampling | all lights in one RTGL1 light list (SSTRE passes no `sectorID`); RIS over a stride subset of 8 per sample | noise grows with light count | [SRC] `Scene.cpp:381-397`; RTGL1 `RTGL1.h:644-656`, `RaygenCommon.h:515-561`, `LightDefs.h` (`MAX_LIGHT_LIST_SIZE` 1024) |
| Exposure | auto exposure on the log-luminance histogram, clamped to [2^min, 2^max] (min -4 from tuning, max 0), black pixels excluded | a black frame stays black (floor) | [SRC] RTGL1 `CmLuminanceAvg.comp:70-80`, `CmComposition.comp:48-53`; `SSRT.cpp:615-618` |
| SE1 fog/haze | haze = 0 in the TSE defaults; fog and haze are not rendered | intentionally omitted (EXP-018 A1) | [DOC] EXP-018 |

### Why the `1_2_Palenque` spawn cave is black [SRC+EXP]

E5's diagnosis was correct and holds generally. The cave has no sun or sky opening in view
and no fire models. All its light comes from invisible static `Light` entities, both point
and fill, and every one of them is dropped. Raster shows these lights through the shadow maps.

Run p1 with `srt_iLegacyLights = 0` and the manual lights removed: frame mean RGB 1.7/1.7/1.6.
Exposure cannot help, because the radiance is zero and black pixels are excluded from the
exposure histogram. Sector ambient plays no part here: 5 of 453 sectors in the level have
any. It is the same mechanism Serious-Engine-RT met in TFE. Upstream fixed it by hand: 23
`cutscene_light` positions in its TFE table (15 world sections).

**General rule:** any area lit only by `Light` entities (designer lights) renders black or
very dark in RT. TSE is affected more than TFE: no TSE world was hand-tuned before E5's 1_2
entries, and TSE uses more interiors.

### TFE vs TSE

- Code: `Engine/Raytracing` and `Light.es` semantics are identical [SRC].
- Data: the TFE table carries upstream's per-level whitelists. The TSE table has only E5's
  1_2 entries, and its `haze = 0` default is TSE-only (EXP-018 A1).

## POC-76: native conversion (option A)

`Engine/Raytracing/RTLights.cpp` (TFE and TSE identical). Cvars, all `srt_*` in `SSRT.cpp`:

| Cvar | Default | Meaning |
|---|---|---|
| `srt_iLegacyLights` | **3** since 3c482c98 (47eeb4d2 shipped 0) | bit 0: convert dropped shadow-casting static point lights; bit 1: convert dropped no-shadow fill ("ambient") lights |
| `srt_fLegacyPointLightIntensity` | 1 | colour multiplier, same scale as Serious-Engine-RT's original lights (`srt_fOriginalLightSphIntensity`) |
| `srt_fLegacyAmbientLightIntensity` | 1 | colour multiplier for fill lights |
| `srt_fLegacyAmbientLightRadiusMultiplier`, `...RadiusMax` | 0.25, 1 m | emitter radius of fill lights = min(hot spot x 0.25, 1 m) |
| `srt_iLightDebug` | 0 | 1 = upload only the legacy-converted lights (sun, original, dynamic, potential and flashlight off; sky stays), 2 = everything except them |
| `srt_bLightInventory` | 0 | prints the world's light/ambient inventory on load and per-frame light counts (frame 300, then every 1800 frames) |

Design:

- **Same selection as raster.** The candidates are exactly the static lights Serious-Engine-RT
  dropped in the active sectors around the viewer, collected in the same pass
  (`RT_IgnoredLights`). The existing sector culling (`culling_max_sector_depth`) bounds the
  count. Nothing is per-level.
- **No double counting.** Conversion runs after the fire-model matching
  (`RT_AddPotentialLightSources`). A dropped light that a fire model already re-emitted as a
  "potential light" is skipped. Whitelisted (`cutscene_light`) and model lights are not
  candidates.
- **Not converted:** dark lights, lens-flare-only lights and directional ambient stay omitted.
  RTGL1 has no negative or ambient light.
- **Point lights** use the original-light conversion: radius 5 % of the hot spot, fall-off
  `(hot spot + fall-off) x original_light_sph_falloff_multiplier`. E5's whitelisted 1_2 lights
  already use this path.
- **Fill lights** get a larger emitter. RTGL1's attenuation is 1 inside the emitter radius,
  which approximates SE1's hot-spot plateau, and the larger emitter gives softer shadows.
  SE1 fill lights cast no shadows and ignore N.L. RTGL1 cannot do that per light, so this is
  the closest native form; the remaining deviation is listed under open defects.
- **Linear space.** Colours go through the same sRGB-to-linear conversion as every RT light.
  There is no global multiplier and no post-process brightness change.
- **Dynamic objects** are lit by the same RTGL1 lights as brushes, so they are consistent by
  construction. In raster, models use an approximation of the shadow-map lights
  (`FindModelLights`).

## POC-77 / POC-78: options B, C and D (feasibility; not built)

- **B: sector-ambient and directional-ambient reconstruction.**
  - [EXP] Sector ambient is rare in the measured worlds. Sectors with a non-black
    `bsc_colAmbient`:

    | World | Sectors with ambient |
    |---|---|
    | 1_2 | 5 / 453 |
    | 1_1 | 5 / 423 |
    | 1_0 | 13 / 185 |
    | 3_1 | 10 / 984 |
    | 3_3 | 2 / 521 |
    | 01 | 15 / 368 |
    | 03 | 2 / 536 |
    | 09 | 0 / 177 |

  - Directional ambient (`BPOF_HASDIRECTIONALAMBIENT`) flags 36-67 % of polygons on outdoor
    worlds and almost none on interior worlds (03: 17 / 4743, 09: 23 / 1864). Outdoors, RT's
    sky visibility already supplies that light.
  - Building B properly needs **an RTGL1 change**: a per-surface constant irradiance term,
    added once at the primary hit (and optionally the first bounce), with the sector given by
    per-triangle `sectorID` or a material slot. RTGL1 has no ambient or unshadowed light type
    today (`RTGL1.h:637-707`).
  - Engine-only substitutes were rejected:
    - one fill sphere light per sector: point-light explosion, leaks, shadowed;
    - emissive surfaces: wrong (they glow and bloom);
    - global sky or exposure lift: forbidden by the directive.
  - **Escalated**, with low priority given the data above.
- **C: lightmap-assisted.** SE1 computes complete static lighting per polygon at run time
  (`CLayerMixer`, shadow maps including ambient and shadows). A shadow-map layer could feed
  RTGL1 as an indirect or ambient hint for surfaces without RT light. That would double count
  wherever converted lights also reach a surface. A correct version needs an RTGL1 shader
  path ("use lightmap only as an indirect floor") and texture uploads per polygon (memory and
  upload cost). Feasible, but an architecture change: escalate only if A leaves real gaps.
- **D: automatic irradiance probes.** Not justified by the data. After A, no measured
  interior is black. Escalate only if B/C are rejected and a gap remains.

## Notes for RD-013 (geometry and normals), from the lighting work

- [SRC] SE1 brushes light per polygon from shadow maps. Fill lights ignore the normal, and
  raster shading never needs smooth vertex normals.
- RTGL1 weights every light by N.L at the shaded point (`RaygenCommon.h:445-470`,
  `:606-626`). RT therefore needs normals to be right, especially on curved cave and organic
  brush geometry built from many flat polygons.
- [ASM] RT faceting will therefore be more visible than raster faceting under converted fill
  lights. Smoothed brush normals and normal maps (M2/M3) would reduce the N.L penalty for
  converted no-diffusion lights.
- Upstream already forces calculated normals for some models (`[textures calc_normals]` in the
  tuning table).

## POC-79: validation (staged testing, owner #26)

Runtimes: copies of VS-A `runtime-tse-classic` and `runtime-classic` (original textures)
with the `m01/light` binaries. Captures are at level start, at 1600x900. Mean RGB is over the
client area. Screenshots and logs stay local (`G:\sstre-tmp\light\runs`).

L0 means `srt_iLegacyLights = 0` (preview2 behaviour); L3 means 3. "Manual" means E5's 25
1_2 entries.

### Fixed exposure (-2), radiance comparison with raster (p3) [EXP]

| Start view | Raster (Vulkan) | RT L0 | RT L3 | Reading |
|---|---|---|---|---|
| TSE 1_2 cave | 17/23/16 | 22/31/24 (manual) | 28/38/30 (no manual) | lit, about as bright as with the manual lights |
| TFE 03 Tomb of Ramses hall | 32/37/45 | 6/8/6 | 42/47/60 | near raster; the moody blue hall stays moody |
| TSE 1_1 Palenque | 13/36/44 | 36/44/47 | 41/55/59 | small lift (+13 %), outdoor sun dominates |
| TFE 01 Hatshepsut (outdoor) | 74/67/68 | 103/89/90 | 103/89/90 | unchanged (no dropped lights in range) |

### Auto exposure, the player's view (p1, p2) [EXP]

| Start view | Raster | RT L0 | RT L3 |
|---|---|---|---|
| TSE 1_2 cave (no manual) | 17/23/16 | 1.7/1.7/1.6 (black) | 57/74/59 (manual L0: 48/63/49) |
| TFE 03 | 32/37/45 | 6/9/4 | 78/86/107 |
| TFE 09 Sewers | 4/27/14 | 12/13/14 | 69/70/16 |
| TSE 3_1 Gothic Castle | 94/92/89 | 46/69/136 (different camera pitch) | 93/92/103, visually matches raster |
| TSE 3_3 Corridor of Death | 75/72/64 | 75/70/55 | 89/82/66 |
| TSE 1_0 (outdoor intro) | 32/27/22 | 193/161/120 | 195/162/121 (no dropped lights in range) |

Notes:

- `srt_iLightDebug = 1` on 1_2 shows the cave lit by the converted lights alone (59/76/60),
  so the converted lights are the cave's whole light.
- Light counts per frame on the 1_2 start, L3: 20 original lights + 372 legacy point + 118
  legacy fill. Other starts: 3_1 90 + 429 + 400; 03 144 + 2; 09 3 + 74 + 10; 1_1 29 + 92 + 28.
  All stay under RTGL1's 1024.
- RTGL1 errors: 0 in every run. The watchdog never fired. All levels started.
- Under auto exposure, RT is brighter than raster in dim interiors (03, 09). The cause is
  RTGL1's exposure policy, not the lights: at fixed exposure the radiance is close to raster.
  See the open item on the exposure floor.

### FPS (p3 / p4, one run each, not quiet mode, indicative) [EXP]

Demo `auto-demo0001` (1_2), RT, 1600x900:

| Config | FPS without peaks | Low sustained |
|---|---|---|
| L0 + manual lights (preview2 state) | 97.3 | 79.2 |
| L3 | 94.2 | 77.5 |

About -3 % (about 0.3 ms per frame) with roughly 500 sphere lights. CPU light extraction plus
RTGL1 light-list cost. Formal numbers belong to E3 (POC-91).

### Coverage

| Item | Status |
|---|---|
| TSE 1_2, 1_1, 1_0 (showcase), 3_1, 3_3; TFE 01 (showcase), 03, 09 at start, RT L0/L3 auto exposure + Vulkan | executed (p1, p2; ledger 20261128192120-LIGHT-7604, -4604) |
| Fixed exposure -2: 1_2, 03, 1_1, 01 | executed (p3, ledger 20261128193625-LIGHT-2463) |
| Branch head with default cvars, 1_2; RDF-013 check on 1_3 | executed (p6) |
| OpenGL raster; Vulkan raster with the new binaries | skipped: the change is in `Engine/Raytracing` only and the raster code path is unchanged [SRC]; Vulkan captures are the comparison reference |
| Enhanced-texture runtimes | skipped: lighting code does not depend on textures |
| Mid-level interiors, MP levels, community level | deferred to R1's comparison harness / Integration matrix (POC-90/92) |
| TFE 01 p2 capture | invalidated (ESC opened the game menu); redone in p3 |

## Changes (`m01/light`, not pushed)

| Commit | Content |
|---|---|
| `47eeb4d2` | `srt_iLegacyLights` conversion, debug and inventory cvars (TFE+TSE) |
| `3c482c98` | default `srt_iLegacyLights = 3` (shown better above; `0` restores upstream) |
| `ed930793` | data: drop the 25 1_2 `cutscene_light` entries (redundant) |

`srt_iLegacyLights` is a persistent cvar. Profiles saved by this branch's earlier builds keep
their stored value; preview2 profiles never stored it, so they pick up the new default.

## Rejected approaches

- **Flipping `srt_bLightSphIgnoreEditorModels = 0`** (an existing upstream switch that would
  keep all `Light` entities): it converts the lights before the fire-model matching (double
  counting with potential lights). It also applies one parameter set to point and fill lights.
- **Per-level whitelists** (upstream / E5 style): not universal; the directive forbids them.
- **Global brightness or exposure lift:** forbidden, and it would also lift intentionally
  dark areas.
- **One sphere light per sector for ambient:** light explosion, leaks, shadowed.

## Open defects and follow-ups (for RD-016 and the defect register)

1. **Fill lights are shadowed and N.L-weighted in RT** (SE1: neither). A per-light "no shadow"
   and "no diffusion" flag needs an RTGL1 shader change. **Escalated.**
2. **Sector ambient and gradients are lost** (option B). This needs an RTGL1 per-surface
   ambient term. **Escalated, low priority** (rare in the data).
3. **RTGL1 light sampling ignores sectors:** SSTRE passes no `sectorID`, so all 100-900 lights
   share one list and RIS samples a stride subset of 8. More lights mean more noise. Passing
   brush sector IDs and `rgSetPotentialVisibility` would improve quality and cost. This
   touches the shared geometry upload (FXT/FXP); coordinate via the lead.
4. **Auto-exposure floor** (`tonemapping_min_log_luminance = -4`) lets RT brighten dim
   interiors above raster. Raising the floor (for example to -2) would keep dark areas darker.
   This is a visible default change: owner/lead decision; data in the tables above.
5. Lights beyond `culling_max_sector_depth` are not uploaded, so light can pop on long sight
   lines (upstream behaviour, unchanged).
6. Observed, not lighting: the TFE 09 RT capture shows a magenta/cyan checker texture on the
   first-person weapon (the VS-A runtime's synthetic override, EXP-009). Owner: VS-A/A3.

### Branch head and RDF-013 (p6) [EXP]

- Branch head `ed930793`, default cvars, with the manual entries removed: the 1_2 cave reads
  57/74/59 (auto exposure), the same as L3 in p1. 0 RTGL1 errors.
- **RDF-013** (sunlit outdoor too bright and flat in RT). Start of TSE 1_3, fixed exposure -2:

  | Config | Mean RGB |
  |---|---|
  | Raster | 99.7/101.8/75.4 |
  | RT L0 | 118.4/104.8/68.1 |
  | RT L3 | 118.5/104.8/68.2 |

  The conversion does **not** make RDF-013 worse: it adds 1021 lights there, but the sun and
  sky dominate. RDF-013 shares the **exposure/sun calibration** cause, not the light
  conversion:
  - [SRC] sun `srt_fSunIntensity 4 x srt_fFixSunIntensityGlobal 0.75`, colour `^2.2`;
  - sky fill `srt_fFixSkyIntensityGlobal 0.5`;
  - auto exposure targets mid-grey;
  - SE1's baked contact darkening from shadow maps has no RT counterpart except GI occlusion.

  Recommended: handle RDF-013 with open item 4 (exposure policy) plus a sun/sky calibration
  against SE1 directional colour. This is a separate change, not part of A.
- **Light budget:** on 1_3, 29 original + 91 dynamic + 1021 legacy lights exceed
  `srt_iLightSphMaxCount` / RTGL1's 1024. Legacy lights are added last, so the dynamic lights
  are kept and the excess legacy lights are dropped without warning (`Scene.cpp:383-386`).
  Follow-up: prioritise legacy lights by distance and intensity, and measure FPS at about
  1000 lights. Only the 1_2 demo (about 500 lights) was timed.
