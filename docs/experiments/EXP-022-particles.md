# EXP-022: Particle rendering review and correctness fixes (raster Vulkan/OpenGL and RT)

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | POC-84 (M0.1, dossier RD-017) |
| Status | **complete for M0.1 scope** (partial for RD-017): architecture review done for all three renderers; eight RT particle defects fixed behind cvars and verified on demos; M1 performance notes recorded. Open: RT particle compositing (LDR after tonemapping, linear-space blending, no depth behind refractive surfaces) needs an RTGL1 change; fog/haze not applied to RT particles |
| Environment | Windows 11 Pro 22631, i5-11600K, RTX 4070 12 GB. VS 2022 (v143), Windows SDK 10.0.22000.0, Vulkan SDK 1.4.363.0, RTGL1 clean-room build `0eb4c4a` (same DLL as preview2) |
| Inputs | SSTRE-Engine `sprint2/integration` @ `7eeed884` (preview2). Reference sources: Serious-Engine-RT (local copy `local-work/engine/rt`), Classic-VK (`local-work/engine/cvk`). Game data: owner's Steam TFE and TSE, runtimes copied from the VS-A runtimes (original and enhanced textures) |

## Goal and success criteria

1. Describe how SE1 draws particles in the raster renderers (Classic-VK Vulkan and OpenGL) and how the SSTRE RT path feeds them to RTGL1, covering the RD-017 checklist (billboards, blending, sorting, alpha, timing, intersections, soft particles, HDR emissive, dynamic lights, overdraw, batching, RT uploads).
2. Find particle correctness defects in combat scenes on TFE and TSE, and fix them for M0.1 behind cvars without changing raster output.
3. Record per-frame particle cost for M1 (no rewrite).
4. Give A3 a per-class particle texture policy (no texture names).

## Procedure (local paths; nothing is published)

- Engine worktree `G:\sstre-tmp\fxp\wt-engine`, branch `m01/fxp` from `sprint2/integration` `7eeed884`, LF checkout (`-c core.autocrlf=false`). Builds: Release x64, TFE and TSE (`scripts\build-all.ps1`, MSBuild as in EXP-017).
- Runtimes: copies of the four VS-A runtimes (TFE/TSE, original and enhanced textures) with the FXP binaries overlaid.
- Harness `scripts\run-fxp.ps1` (from the VS-E harness, game watchdog on, window capture). New harness commit `d07ec23f`: `dem_strCheckpoints` freezes the demo timer at listed demo times for `dem_fCheckpointHold` seconds and logs it, so every renderer is captured at the **same demo frame** (RT gets 2.5-3.5 s to converge). Debug commit `2a0d050a`: `gfx_iParticleCensus` logs particle quads/flushes per entity class in the raster and RT particle passes.
- Scenes: the original auto-demos (no input injection): TSE demo 1 (1_2 Valley of the Jaguar: rockets, explosions, lasers, sniper, chainsaw, gibs), TFE demo 2 (Dunes) and demo 3 (Memphis Suburbs). 1600x900 window, VSync off.
- All GPU runs under `gpu-lock.ps1 run -Owner FXP`; runs recorded in the shared ledger (ids in R0).
- Image comparison: crops and region statistics (`scripts\crop3.py`, `regstats.py`), kept local (GATE-05).


## 1. Architecture ([SRC], SSTRE-Engine `7eeed884`, paths relative to `SamTSE/Sources/Engine`; the TFE tree is identical for every file cited)

### 1.1 Particle API and the game side
- Particles are not objects. Every frame the renderer calls `CEntity::RenderParticles()` of each entity it adds, and the entity code (`EntitiesMP/Common/Particles.cpp`, 96 `Particles_*` functions in TSE; `Entities/Common/Particles.cpp` in TFE) regenerates all quads procedurally from the entity state and the lerped tick (`_pTimer->GetLerpedCurrentTick()`). There is no simulation state on the GPU and nothing is cached between frames.
- API (`Graphics/DrawPort_Particles.cpp`): `Particle_PrepareTexture(texture, blend)` (one texture and blend per batch), `Particle_SetTexturePart(w, h, col, row)` (sprite-sheet cell), `Particle_RenderSquare` (screen-aligned billboard, optional roll, aspect), `Particle_RenderLine` (camera-facing ribbon between two points), `Particle_RenderQuad3D` (world-space quad), `Particle_Sort` (back-to-front inside the batch), `Particle_Flush` (draw the batch). `Particle_GetMipFactor()` gives the effect a distance-based LOD value.
- Usage census (TSE `Particles.cpp`): 135 `Particle_PrepareTexture` calls: `PBT_BLEND` 71, `PBT_ADDALPHA` 33, `PBT_ADD` 29, `PBT_MULTIPLY` 2, `PBT_TRANSPARENT`/`PBT_FLEX` 0. 21 `Particle_RenderLine` callers (rocket, cannonball and projectile trails, sparks, rain, snow, bullet spray, lasers, blood trail), 3 `RenderQuad3D`, 2 `Particle_Sort`. 94 `Particle_SetTexturePart` calls, most on 4x4 / 8x8 sprite sheets. 15+ effects read `Particle_GetMipFactor()` for LOD fades, particle counts or sizes (`Particles_ChimneySmoke`, `Particles_Stardust`, `Particles_BloodSpray` size, `Particles_BulletSpray` count, `Particles_Twister`, `Particles_Death` visibility, ...). TFE: `PBT_BLEND` 41, `PBT_ADD` 25, `PBT_MULTIPLY` 2, `PBT_ADDALPHA` 1, no `Particle_Sort`.

### 1.2 Raster (Classic-VK Vulkan and OpenGL: one code path)
- Order in `CRenderer::RenderScene` (`Rendering/Render.cpp:588,626`): background (sky) particles after the background scene; then opaque world, models, **particles**, and only then translucent portals (water, glass). Translucent surfaces are therefore drawn over particles.
- Which entities: every entity added to `re_admDelayedModels` (`Rendering/RenderAdding.cpp:40-90`), i.e. every non-hidden model entity in a rendered sector, **whether or not its model is visible**; mip factor per entity = `MipFactor(view distance)` + `AdjustMipFactor` (`RenderAdding.cpp:80-87`), passed with fog/haze flags to `Particle_PrepareEntity` (`Rendering/RenderModels.cpp:719-748`).
- Geometry is projected on the CPU into view space (`Particle_RenderSquare` `DrawPort_Particles.cpp:218`): screen-aligned billboards, frustum sphere test, sub-half-pixel rejection, roll from a 256-entry sin table. Lines (`:321`) are widened perpendicular to their projected screen direction, so the width does not depend on the view angle.
- Blend states (`:123-188`): BLEND = SRC_ALPHA/INV_SRC_ALPHA; ADD = ONE/ONE; MULTIPLY = ZERO/INV_SRC_COLOR; ADDALPHA = SRC_ALPHA/ONE; FLEX = ONE/INV_SRC_ALPHA (all without depth write); TRANSPARENT = alpha test with depth write. Depth test is on, no soft-particle fade: particles cut hard into geometry.
- Fog and haze: per-vertex attenuation of colour (ADD/MULTIPLY) or alpha (BLEND/ADDALPHA) from the fog/haze tables; for TRANSPARENT a second fog layer pass with `GFX_EQUAL` depth (`:554-600`).
- Batching: one `gfxFlushQuads` (one draw) per `Particle_Flush`, i.e. per texture per effect per entity; Vulkan uses the shared dynamic vertex buffers. Sorting only inside a batch and only where the effect asks for it; batches are drawn in entity order.
- Blending happens in gamma space on an 8-bit back buffer; HDR, bloom and emissive do not exist.
- First-person particles (TSE chainsaw cutting sparks/blood, `EntitiesMP/Player.es` `RenderHUD`) are drawn in the HUD pass with the world camera and mip factor 2.0; NETRICSA model previews draw particles into their own drawport (`GameMP/CompModels.cpp`).

### 1.3 Ray tracing (Serious-Engine-RT layer in SSTRE, RTGL1)
- `SSRT::Scene::ProcessDynamicGeometry` walks sectors around the camera (`Raytracing/RTModelCulling.cpp`) and calls `RT_AddParticlesForEntity` (`Raytracing/RTParticles.cpp:69`) for each model entity that passes `RT_TestModel` (angular-size culling, `srt_fCullingMinAngularSize` 1.5 deg, `RTModelCulling.cpp:124,170-181`) and for background entities (`Scene.cpp:530,534`). The same `Particles_*` code runs; under `GAT_RT` every `Particle_*` call is forwarded to `RT_Particle_*` (`DrawPort_Particles.cpp`).
- Geometry is built in **world space** on the CPU: billboards from the camera rotation axes, lines from `lineDir x cameraForward`. One `RT_Particle_Flush` = one `rgUploadRasterizedGeometry` (`Scene.cpp:332`) with the blend factors translated 1:1, depth test on, no depth write, `color.a = srt_fParticlesAlphaMultiplier`.
- Textures listed in `[textures alpha_test_particles]` of the RT tuning table (lightning, ghostbuster ray) go the other way: uploaded as **ray-traced** dynamic model geometry (alpha-tested, visibility WORLD_0, one colour per flush), i.e. a per-frame dynamic BLAS entry.
- RTGL1 draws all rasterized geometry **after** tonemapping and image composition, straight into the final (LDR, r11g11b10f linear) image, before upscaling and before bloom is added (`RTGL1 Source/VulkanDevice.cpp:841-861`). Vertex colours are converted with pow 2.2 (`Shaders/RsRasterizer.vert:35-45`, `rasterizedVertexColorGamma = RG_TRUE` in `Raytracing/SSRT.cpp`), textures are sampled as sRGB, so blending happens in **linear** space. The depth buffer is the primary-ray first-hit depth (`Shaders/RaygenPrimary.inl:298`, `RsDepthCopying.frag`), which is the water or glass surface where the path refracts.
- Consequences: rasterized RT particles are unlit, not tonemapped/exposed, not in reflections, refractions or indirect light, contribute nothing to bloom and are not HDR emissive; they are not fogged (no fog/haze in RT particle pass: `Particle_PrepareEntity(.., 0, 0, ..)`); they cost no BLAS/TLAS work.
- First-person particles from the HUD pass have no RT scene to go to: preview2 drops them (`c1537cfd`, previously a crash).

## 2. Correctness defects

Severity: S1 = effect missing or wrong in normal play, S2 = clearly visible difference, S3 = minor/latent. "Fixed" = fixed on `m01/fxp` behind a cvar (default on); "open" = needs work outside M0.1/FXP scope.

| ID (proposed) | Renderer | Defect | Evidence | Cause | Status |
|---|---|---|---|---|---|
| FXP-1 | RT | Line particles (`Particle_RenderLine`: rocket/cannonball/projectile trails, sparks, bullet sprays, rain, lasers) shrink to zero width when they point along the view; trails behind a projectile flying away from the camera vanish | [EXP] TSE demo 1 at 66 s (R1): trail visible in Vulkan/OpenGL, invisible with `srt_bParticleLineFix=0`, visible with 1 | [SRC] `RTParticles.cpp:342` `cross = lineDir x cameraForward`, not normalised, width scaled by sin(angle); and the camera forward instead of the eye vector | **fixed** `0a85734c`, `srt_bParticleLineFix` |
| FXP-2 | RT | Hidden entities (`ENF_HIDDEN`) emit particles; the raster renderer never adds them | [SRC] `RenderAdding.cpp:43` vs `RTParticles.cpp:69` (no check) | missing check | **fixed**, `srt_bParticleRasterParity` |
| FXP-3 | RT | Particles of entities whose model is below `srt_fCullingMinAngularSize` (1.5 deg) are culled with the model: distant fire/smoke emitters with small or editor models, projectiles and their trails beyond a few tens of metres | [SRC] `RTModelCulling.cpp:170-181`; [EXP] particle entities per frame on TSE demo 1 with parity on: ~1240-1290 (R3) | particles tied to model culling | **fixed**, `srt_bParticleRasterParity` |
| FXP-4 | RT | Constant particle mip factor 4.0 for every entity instead of the per-entity distance mip: LOD fade-outs never happen, sizes that depend on it are wrong (e.g. `Particles_BloodSpray` drop size is `clamp(mip/4)`, so close blood drops are up to 20x too large in RT; first-person chainsaw spray uses 2.0 in raster) | [SRC] `RTParticles.cpp:91`, raster `RenderAdding.cpp:80-87`, 15+ users of `Particle_GetMipFactor()` | constant in the RT port | **fixed**, `srt_bParticleRasterParity` |
| FXP-5 | RT | `Particle_Sort()` is a no-op (2 TSE effects rely on it) | [SRC] `DrawPort_Particles.cpp:638` | not ported | **fixed**, `srt_bParticleSort` |
| FXP-6 | RT | Alpha-tested (ray-traced) particle path swaps colour channels (GFXColor read as COLOR) | [SRC] `RTParticles.cpp:491` | byte order | **fixed**, `srt_bParticleColorFix` (affects the lightning / ray textures of the `alpha_test_particles` list: FXT informed) |
| FXP-7 | RT | `PBT_TRANSPARENT` particles are invisible (rasterized with blend ZERO/ONE); latent, no shipped effect uses it | [SRC] `RTParticles.cpp:183,444` | blend flag forced on | **fixed** (traced as alpha-tested), `srt_bParticleColorFix` |
| FXP-8 | RT (TSE) | First-person chainsaw cutting sparks and blood not drawn (crash before `c1537cfd`) | [SRC] `Player.es` `RenderHUD` draws them in the HUD pass, which has no RT scene; [EXP] R4 | HUD pass cannot submit to RT | **fixed** `78081e7a`, `srt_bParticlesFirstPerson` |
| FXP-9 | RT | Additive and alpha-blended particles look weaker than in raster: explosion cores do not saturate, grey trails and debris sparks nearly vanish over bright ground, smoke/gore clouds are more transparent | [EXP] TSE demo 1 cp12: near-white pixels in the explosion 11.5 % (Vulkan) / 10.5 % (OpenGL) vs 0.6 % (RT); TFE demo 2 cp04 gore cloud | [SRC] RTGL1 draws rasterized geometry after tonemapping into the linear final image; vertex colour pow 2.2 and sRGB textures, so blending is in linear space while SE art was made for gamma-space blending (`VulkanDevice.cpp:841-861`, `RsRasterizer.vert:35-45`) | **fixed** (A1): RTGL1 `m01/fxp-rtgl1` + `srt_bRasterGammaBlend` |
| FXP-10 | RT | Particles are LDR overlays: not exposed/tonemapped with the scene (too bright in dark interiors, relatively dim in bright exteriors), no bloom, no HDR emissive, not in reflections/refractions | [SRC] as FXP-9 | design of the RT port | **open**, RD-017 step "HDR emissive + bloom"; M1 cost note §3 |
| FXP-11 | RT | Particles behind or below refractive surfaces (water, glass) fail the depth test against the primary first-hit depth; raster draws translucent portals over particles | [SRC] `RaygenPrimary.inl:298`, `RsDepthCopying.frag`; raster order `Render.cpp:626` | depth buffer = first hit | implemented, default off, repro deferred (A1): `srt_bRasterDepthBehindRefraction` |
| FXP-12 | RT | No fog/haze attenuation of particles (raster attenuates per vertex) | [SRC] `RTParticles.cpp:91` passes no fog/haze | RT fog/haze not modelled (haze disabled in TSE, EXP-018) | open, depends on the RT fog decision (LIGHT/FXT) |
| FXP-13 | RT | NETRICSA model previews lose their particles (`GameMP/CompModels.cpp`, own drawport, no RT scene) | [SRC] | as FXP-8 | open, S3 (UI) |
| FXP-14 | RT | Sky (background) particles are oriented with the main camera axes and then rotated by the inverse background-viewer orientation | [SRC] `RTParticles.cpp` `RT_GetViewVectors`, `Scene.cpp:352-357` | | open, [ASM] only visible if a background viewer is rotated; not reproduced |
| FXP-15 | all | No soft particles: particles cut hard into geometry in all renderers | [SRC] depth test only | original design | not a regression; candidate for RD-017 (cheap in RTGL1's raster pass, depth is available) |
| FXP-16 | RT | `RT_SKAMODEL` entities get no RT particles (raster renders them) | [SRC] `RTModelCulling.cpp` handles RT_MODEL/RT_EDITORMODEL only | | open, S3 (few SKA entities in TFE/TSE) |

Found while testing, not particles (handed to FXT/R1): in TFE demo 3 the blood spill/stain models are drawn as hard black alpha-tested shapes in RT (soft green translucent decals in raster); the RT tuning table lists those textures as `fully_metallic`.

## Results ([EXP] unless labelled otherwise)

### R0. Coverage

| Run set | Question | Status | Ledger id |
|---|---|---|---|
| A: TSE demo 1, Vulkan / RT fixes off / RT fixes on / OpenGL, 23 checkpoints (6-138 s) | which particle effects differ | executed (before the staged-testing rule) | 20261128192117-FXP-856 |
| B: TFE demos 2 and 3, Vulkan / RT off / RT on | same on TFE | executed (before the rule) | 20261128192117-FXP-1206 |
| C1: TSE demo 1, 98-112 s at 1 s steps, Vulkan + RT on, census | Q1 chainsaw particles in RT | executed | 20261128194756-FXP-5847 |
| C2: TSE demo 1 RT, demo profile, fixes off vs on | Q2 cost | executed | 20261128194756-FXP-1875 |
| C3: TFE demo 2 at 21/28 s, Vulkan + RT on, census | Q3 missing class? | executed | 20261128194756-FXP-3041 |
| enhanced textures (slice, slice-v2) | particle textures | skipped: neither pack contains an enhanced particle texture (A3 status, §4) | 20261128194756-FXP-9284 |
| OpenGL in B/C | raster regression | skipped: raster code unchanged ([SRC] diff: only `Particle_Sort` routes to RT under `GAT_RT`, census counters); A shows OpenGL = Vulkan (cp12 explosion region mean RGB 129/124/86 vs 131/125/89) | - |
| water/glass occlusion (FXP-11), sky orientation (FXP-14) | | deferred (source finding; needs an RTGL1 change first) | - |

All 19 runs: watchdog ok, 0 RTGL1 errors, process ended normally. Focus was not held in sessions A and B (no input is injected, so captures are valid); held in C.

### R1. Line particles (FXP-1)
TSE demo 1 at 66 s, a projectile trail seen from behind: drawn in Vulkan and OpenGL, invisible with `srt_bParticleLineFix=0` (preview2), visible with the fix. A remaining difference is FXP-9 (the additive squares of the same trail are much fainter in RT).

### R2. Additive / blended particles weaker in RT (FXP-9)
TSE demo 1 at 78 s, explosion core region: near-white pixels 11.5 % (Vulkan), 10.5 % (OpenGL), 0.6 % (RT, fixes off and on identical); mean blue 89 vs 66. At 36 s the explosion debris sparks (additive lines) are dense in raster and nearly absent in RT over the bright ground. TFE demo 2 at 35 s: the gore cloud (`PBT_BLEND`) is visibly more transparent in RT.

### R3. RT particle pass statistics with the fixes on
See §3. Particle-emitting entity calls per frame ~1240-1290 with `srt_bParticleRasterParity=1`.

### R4. First-person chainsaw (FXP-8)
TSE demo 1 at 105 s: with the fix the census shows the player entity with 8 particle flushes in the RT pass (1 in the other checkpoints, the ambient viewer particles) and the cutting dust spray is visible at the blade; preview2 drew none (E5 A2).

### R5. Census check of a suspected missing effect (TFE demo 2, 21 s)
Raster and RT submit the same particle classes (Werebull, Projectile, Blood Spray; RT also off-screen ones, it has no frustum rejection). The projectile glow that is bright in Vulkan and absent in RT at this frame is therefore not a missing particle system: it is FXP-9 or a light flare [ASM: verify with the flare path, FXT/LIGHT].


## 3. Performance notes for M1 (rough, not a benchmark; E3 owns formal runs)

[EXP] `srt_iParticleStats=120` on TSE demo 1 (1_2, RT, fixes on, 1600x900, RTX 4070), 120-frame averages over the whole demo:

| Metric | Range |
|---|---|
| entities whose `RenderParticles()` is called per frame | 1237-1292 (most produce nothing) |
| particle flushes (= `rgUploadRasterizedGeometry` calls) per frame | 4.4-18.1 |
| quads per frame | 1553-2221 (max 2272) |
| upload per frame (24 B vertex x4 + 6 indices x4 B) | 182-260 KB |
| ray-traced (alpha-tested) particle flushes | 0 in this demo |
| CPU time of the RT particle pass (generation + upload calls) | 0.26-0.31 ms/frame |

[EXP] Demo profile, TSE demo 1, RT, one run each, not in quiet mode: fixes off 96.1 FPS average without peaks (low sustained 79.6), fixes on 100.4 FPS (83.3). The fixes have no measurable cost; the 4 % difference is run-to-run noise in the wrong direction.

Observations [SRC]:
- Rasterized RT particles cost no BLAS/TLAS work and no transparent ray traversal; they are drawn once at render resolution after composition (before DLSS/FSR). GPU cost is raster overdraw only. Only the `alpha_test_particles` textures (lightning, ghostbuster ray) create per-frame dynamic BLAS geometry, one entry per flush with ID `entityID:100000+n`.
- Per-frame cost is CPU-side and small. M1 opportunities, in order of expected value: (1) merge flushes with the same texture, frame and blend state into one upload per frame (the RT path has no draw-order constraint between entities beyond what raster had, and sorting is per flush anyway); (2) reuse a static quad index buffer instead of copying indices per upload; (3) skip `RenderParticles()` for entity classes that never emit particles (class flag, data not heuristics); (4) for the alpha-tested path, upload one dynamic geometry per frame instead of one per flush.
- If M1/RD-017 moves additive particles into the HDR path (emissive geometry), the cost changes class: per-frame dynamic BLAS for 2000+ quads plus any-hit shading. Measure before committing; the low-cost route is an RTGL1 raster pass before tonemapping (no BLAS), see §5.

## 4. Per-class particle texture policy (input for A3 / POC-85)

Classes are defined by engine use (blend type, sprite-sheet use, geometry kind), not by texture names. The VS-A slice runtimes contain **no** enhanced particle texture (TFE 0 of 71 overridden files, TSE 1 level flare that is not a particle texture) [EXP], so "enhanced" runs show original particle textures over enhanced surfaces.

| Class (engine signature) | Typical effects | Failure modes of naive SR | Recommended recipe | Fallback |
|---|---|---|---|---|
| P1 additive emissive, `PBT_ADD` (RGB = shape, alpha ignored) | fire, explosion cores, muzzle and projectile glows, stars, sparks heads | lifted black level turns the quad into a visible box; ringing gives dark/bright rims; compression noise in black is added up by overdraw | conventional SR (no generative), then clamp near-black to 0 (black-point preserve), no sharpening; BC7/uncompressed, never BC1 for gradients | original |
| P2 additive with alpha, `PBT_ADDALPHA` (alpha masks, RGB colours) | energy, plasma, glows with coloured cores, many TSE effects | RGB garbage in alpha=0 texels bleeds in at mip/filter; alpha and RGB upscaled differently | **alpha-aware**: upscale alpha separately, premultiply for resampling and mip generation, dilate RGB into transparent texels | original |
| P3 alpha-blended, `PBT_BLEND` | smoke, dust, debris, blood drops/sprays, rain/snow sprites | dark or white fringes from unpremultiplied filtering; alpha edge sharpening changes soft smoke into cut-outs | alpha-aware (as P2), keep alpha softness (no alpha sharpening), conservative SR factor (2x) | original |
| P4 multiply, `PBT_MULTIPLY` | darkening/shadow-like particles | white level drift darkens the whole quad | conventional, preserve white = 1.0 exactly | original |
| P5 sprite sheets (`Particle_SetTexturePart` grids 2x2..8x8, also tall strips 512x4096) | explosion and fire animations, numbered variants | cell bleeding at cell borders after SR and in mips; changed cell size breaks the mex grid | process per cell with border padding/clamp, keep exact power-of-two multiple of the cell grid, alpha-aware if P2/P3 | original |
| P6 line/streak textures (used with `Particle_RenderLine`) | trails, sparks, rain, lasers, tracers | SR adds nothing (1-D gradients); ringing at the ends | keep original, or plain bicubic 2x | original |
| P7 alpha-tested particle textures (RT `alpha_test_particles` list, `PBT_TRANSPARENT`) | lightning, ghostbuster ray (track FXT) | threshold 0.5 changes the silhouette if alpha is smoothed | alpha-aware with threshold-preserving alpha (coverage-preserving mips) | original |
| P8 tiny point sprites (<= 32 px) | stardust, sparkles | generative SR invents detail at sub-pixel size | none (original) | original |

General rules: never generative SR for particles; no colour/filename heuristics, classify by the blend/usage signature (a census tool can derive the class from `Particles.cpp` call sites); keep the original as fallback per texture; mips must be generated from premultiplied linear data for P2/P3/P5; for the RT path the textures are sampled as sRGB and blended in linear space, so P1 brightness balance must be judged in both raster and RT.

## 5. Fixes and rejected approaches

Branch `m01/fxp` (not pushed), on `7eeed884`:

| Commit | Content | Files |
|---|---|---|
| `d07ec23f` | harness: demo checkpoints (default off) | `Engine/Network/Network.cpp` (TFE+TSE) |
| `0a85734c` | RT particle fixes FXP-1..7, `srt_iParticleStats` | `Raytracing/RTParticles.cpp`, `RTProcessing.h`, `SSRT.cpp` (2 lines), `RTModelCulling.cpp` (9 lines), `Graphics/DrawPort_Particles.cpp` (1 line), `Gfx_RayTracing.cpp` (stubs); TFE+TSE identical |
| `78081e7a` | FXP-8 TSE first-person chainsaw particles in RT | `EntitiesMP/Player.es` |
| `2a0d050a` | debug census `gfx_iParticleCensus` (default off) | `DrawPort_Particles.cpp`, `GfxLibrary.cpp`, `RenderModels.cpp`, `DrawPort.h`, `RTParticles.cpp` |

Cvars (non-persistent, default 1 = fixed; 0 = preview2 behaviour): `srt_bParticleLineFix`, `srt_bParticleColorFix`, `srt_bParticleSort`, `srt_bParticleRasterParity`, `srt_bParticlesFirstPerson`. Defaults are on because each restores raster behaviour (R1, R4, [SRC] for the rest) at no measurable cost (§3). The shared RT upload (`Scene::AddParticles`) is not touched. Raster output is unchanged.

Rejected:
- Engine-side gain on additive particles to compensate FXP-9: a colour heuristic that cannot reproduce gamma-space blending (the result depends on the destination); against the directive.
- Submitting all HUD-pass particles to the RT scene generically: would also move NETRICSA preview particles into the world; the chainsaw is the only HUD-pass world effect, so the fix is at its call site.
- Uploading additive particles as ray-traced emissive geometry for HDR: per-frame dynamic BLAS for ~2000 quads plus any-hit cost; not justified before measuring (§3).

Proposed RTGL1 change (lead coordinates; not made): draw the rasterized DEFAULT pass into a gamma-encoded UNORM target (encode the final image, draw particles with gamma-space colours, decode), optionally before tonemapping with an exposure-matched scale; and give the raster pass the depth of the first non-refractive hit. This addresses FXP-9, FXP-10 (partly) and FXP-11 with no ray-tracing cost.

## Impact on ADRs, dossiers and backlog
- RD-017 particles section: §1 (architecture), §2 (defect list, ids to be renumbered RDF-xxx by R1), §4 (texture classes) can be taken over directly.
- ADR-0016 (effect classification): particle classes are defined by blend type and API use; no texture lists are needed for particles except the existing `alpha_test_particles` list, which FXT is reviewing (lightning).
- Backlog: RTGL1 gamma-space particle pass (M0.1 if the lead accepts an RTGL1 change, else M1); RT fog for particles after the RT fog decision; M1 batching items in §3.
- Track handovers: FXT: FXP-6 changes the colour of `alpha_test_particles` geometry (lightning); TFE blood spill/stain models black in RT. R1: the checkpoint harness and the census are reusable.

## Open questions
- Answered by the lead: RTGL1 change in M0.1, see A1.

## Addendum A1 (2026-11-28 evening): RTGL1 gamma-space particle blending and raster depth behind refraction

Lead decision: build the RTGL1 change for M0.1. Generic (no game references), optional, preview2 behaviour kept.

### Change
- RTGL1 branch `m01/fxp-rtgl1` @ `243b8ee` (own worktree `G:\sstre-tmp\fxp\wt-rtgl1`, from `sprint2/rtgl1-sstre` `0eb4c4a`; the shared RTGL1 worktree is untouched). New public struct `RgDrawFrameRasterizedParams` (`RgDrawFrameInfo::pRasterizedParams`, null = off):
  - `blendInGammaSpace`: around the draw of rasterized DEFAULT geometry into the final image, a compute pass (`CmRasterGamma.comp`) encodes the final image with gamma 2.2 and keeps the original in a new framebuffer; the geometry is drawn by a second pipeline set whose fragment shader writes gamma-encoded colour (specialization constant); a second pass decodes. Pixels the geometry did not change get their exact original value back. Without that copy, an in-place r11g11b10f round trip would change untouched pixels by up to 2.6 display codes [EXP, numeric simulation]. Lens flares are drawn after the decode, unchanged. Side effect, by design: particle contributions below one r11g11b10f ulp (1.6 % of the pixel value for R and G, 3.1 % for B) are dropped.
  - `depthBehindRefraction`: the primary and reflect/refract raygen write a new `DepthRaster` framebuffer. Where the path went through refractive surfaces only, it holds the NDC depth of the surface seen behind them (never closer than the first hit); everywhere else it holds the first hit. The depth-copy pass uses it; split (checkerboarded) pixels take the farthest of their horizontal split neighbours.
- Engine `m01/fxp`: `c0580ab6` sets the params from `srt_bRasterGammaBlend` (default **1**) and `srt_bRasterDepthBehindRefraction`; `769e62aa` sets the default of the latter to **0**, see below. The engine must be built against the new header and needs the new DLL and SPIR-V (46 shaders).
- Scope: this changes every rasterized DEFAULT draw into the final image, not only particles. In SSTRE that also covers FXT's rasterized translucent geometry and the lightning after FXT `ea90c65c` (see the FXT note below).

### Results ([EXP], TSE demo 1 / TFE demo 2, same demo frames, RT runs on the new binaries, Vulkan reused from session A/B)

| Question | Result |
|---|---|
| FXP-9, explosion at 78 s and 36 s: particle contribution = capture minus the same frame with `gfx_bRenderParticles=0`, mean over the effect region | 78 s: Vulkan -8.0, RT linear -45.9, RT gamma **-8.6**; 36 s: Vulkan +3.1, RT linear -11.1, RT gamma **+3.2** |
| Near-white share in the same regions (the metric of R2) | 78 s: Vulkan 11.5 %, RT linear 0.6 %, RT gamma 18.7 %; 36 s: 3.8 / 2.6 / 15.2 %. RT gamma overshoots because the RT background in these regions is brighter than in raster (mean 207 vs 161 at 36 s; exposure, FXP-10), not because of the blend |
| TFE check (shared path): gore cloud, TFE demo 2 at 35 s | the cloud opacity is close to Vulkan with gamma blending; it was visibly too transparent before |
| FXP-11 repro | not found: the TSE 1_1 spawn (under water) shows no particle beyond the surface, and TSE demos 2/3 contain no water/glass with particles (ledger `...210834-FXP-611`). **Deferred.** The 1_1 views with the setting off and on show no artifact (differences = water and bubble animation between two level runs) |
| Cost: TSE demo 1 RT demo profile, both settings off vs on | 94.0 vs 93.8 FPS average (no measurable cost) |

Decision: `srt_bRasterGammaBlend` defaults to 1, because the particle contribution now matches Vulkan within 1 display level in both test frames. `srt_bRasterDepthBehindRefraction` defaults to 0 until a water/glass scene shows it better (R1 regression scene `tfe-water-09m5` is a candidate).

Residual difference: RT exterior backgrounds are brighter than raster, so additive particles saturate more there. That is exposure (FXP-10), not blending.

### FXT coordination (lightning)
- FXT `ea90c65c` (`srt_iAdditiveEffectMode`, default 1) moves `PBT_ADD`/`PBT_ADDALPHA` particle flushes, which includes lightning, off the alpha-tested traced path onto the rasterized blend path. With it:
  - FXP-6 (the colour byte order in the traced path) no longer affects lightning; it only applies with `srt_iAdditiveEffectMode=0`.
  - Lightning now goes through the raster blend and therefore **does depend on `srt_bRasterGammaBlend`**. Gamma blending makes additive bolts brighter over bright backgrounds, matching raster. FXT should check their lightning A/B with gamma blending on.
- Merge: `ea90c65c` and FXP `0a85734c` both edit `RT_Particle_Flush` in `RTParticles.cpp` (`isRasterized` / alpha-test decision). Expect a textual conflict; the logic composes as `isAlphaTested = (forced && !additive) || (colorFix && PBT_TRANSPARENT)`.

### Other findings logged for routing (lead to FXT or R1)
- RDF candidate: in TFE demo 3 (Memphis Suburbs) at 28 s and 35 s, the blood spill/stain **models** render in RT as hard-edged, nearly black alpha-tested shapes. In Vulkan they are soft green translucent stains. The RT tuning table lists those textures as `fully_metallic`. They are models, not particles.
- RDF-019: the EXP-009 synthetic tommygun overrides were present in the FXP TFE runtimes; they are now quarantined. Only the TFE demo 3 RT captures at 21 s show that weapon (ledger `20261128204310-FXP-7362`, invalidated); no particle finding used them.

Coverage (A1): executed: D (gamma A/B, 1_1 water A/B, perf, TFE check) and E (demo 2/3 water survey, particles-off backgrounds); reused: Vulkan captures from A/B; deferred: FXP-11 repro.
