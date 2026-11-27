# RD-005: Rendering technology, raster fallback and PBR data path

| Field | Value |
|---|---|
| Dossier | RD-005 |
| Author | Agent D (renderer/platform researcher), Phase 0 |
| Date | 2026-11-27 |
| Status | **Draft.** Source was read only. Nothing was built, run or benchmarked. No performance numbers appear here because none were measured. |
| Feeds | ADR-0005 (engine foundation), ADR-0007 (platform strategy) |
| Related | [RD-001 engine baseline](./RD-001-engine-baseline.md), [RD-002 HD assets](./RD-002-hd-assets.md), [RD-003 AI pipeline](./RD-003-ai-pipeline.md), [RD-006 platforms](./RD-006-platforms.md), [RD-007 licensing](./RD-007-licensing.md) |

## 1. Question and scope

1. What does RayTracedGL1 (RTGL1) provide: API surface, material model, texture inputs and overrides, raster capability, hardware requirements, upscalers, shader toolchain and OS support? Which RTGL1 revision does Serious-Engine-RT (SE-RT) actually use?
2. Can a non-RT raster path exist, either the Serious-Engine-Vk or SeriousSamClassic-VK Vulkan renderer or the legacy OpenGL renderer, and could it be made PBR-capable?
3. Which rendering features does TSE use, beyond TFE, that matter to an RT renderer?
4. How should normal, roughness/metallic, emissive and other maps travel alongside SE1 `.tex` data? This covers animation, effect textures, reflection maps, layers and colour space.

Out of scope: choosing the engine fork and comparing build lineage (Agent A, [RD-001](./RD-001-engine-baseline.md)), HD asset formats (Agent B, [RD-002](./RD-002-hd-assets.md)), and license conclusions (Agent E, [RD-007](./RD-007-licensing.md)). License facts are reported here only as observations.

## 2. Evidence

Local read-only clones are under `<workspace>/upstream/`. All line references are to the commits listed below.

| ID | Source | Revision |
|---|---|---|
| E1 | https://github.com/sultim-t/RayTracedGL1 | branches `hl1` @ `2457acc` (2023-11-26, default), `quake` @ `9efa82d` (2023-02-23), `doom` @ `315053e` (2022-04-26). Tags `v1.1.0` = `b1eb3d8` (2022-04-20), `v1.1.1`/`v2.0.0`/`v2.0.1` = `315053e`, `v3.0.0-dev` = `4cbd9bf`, `hl1-dev` = `d676979` |
| E2 | https://github.com/sultim-t/Serious-Engine-RT | `main` @ `0e7f223c19a28014b60d900878c28831db522120` (last commit 2022-04-20; repo last pushed 2022-10-08 per `gh repo view`) |
| E3 | https://github.com/sultim-t/Serious-Engine-Vk | `master` @ `52c0f9c19f6502c91c8569b2f476de2ec02019fd` |
| E4 | https://github.com/tx00100xt/SeriousSamClassic-VK | `main` @ `510d36f901cbe883c56b155b53717e4efdeb6522` |
| E5 | https://github.com/Croteam-official/Serious-Engine | `master` @ `b408e88a16fd01aa1cfd0e0a999c86c2c1437c9e` |
| E6 | SE-RT release v1.5 notes (`gh release view v1.5 -R sultim-t/Serious-Engine-RT`) and RTGL1 release v1.1.0 notes (`gh release view v1.1.0 -R sultim-t/RayTracedGL1`) | published 2022-04-20 |
| E7 | NVIDIA RTX SDKs license, https://github.com/NVIDIA/DLSS/blob/main/LICENSE.txt (fetched 2026-11-27) | current |
| E8 | Local Steam installs of TFE/TSE Classic: aggregate extension counts from the `*.gro` zip directories only | n/a |

## 3. Observed facts

### 3.1 Which RTGL1 revision SE-RT uses

- SE-RT originally pinned RTGL1 as a submodule. The last pin was `Sources/RTGL1` → `7a88e3867db11f669cbb68a5828342865a4e4a86` (2022-02-12), from the `SultimTsyrendashiev/RayTracedGL1` URL with `branch = Draft`. Commit `591abf7` (2022-04-19), "remove RTGL1 submodule to use env variable instead", deleted `.gitmodules`. Since then SE-RT has found RTGL1 only through the `RTGL1_SDK_PATH` environment variable (`Sources/Engine/Engine.vcxproj` lines 224–385), so **the current SE-RT HEAD pins no revision at all.**
- **Inferred compatible revision: RTGL1 tag `v1.1.0` = `b1eb3d8` (2022-04-20).** Three pieces of evidence support this:
  - (a) The RTGL1 v1.1.0 release notes say "Compiled binaries for Serious Sam TFE: Ray Traced 1.5". SE-RT v1.5 was published the same day and tells users to download `RayTracedGL1-DLSS.zip` from RTGL1 `v1.1.0` (E6).
  - (b) SE-RT calls `rgCreateStaticMaterial`, `rgCreateDynamicMaterial`, `rgCreateAnimatedMaterial`, `rgUploadGeometry`, `rgUploadRasterizedGeometry`, `rgSubmitStaticGeometries`, `rgStartNewScene` and others. All of them exist in the `b1eb3d8` header.
  - (c) SE-RT HEAD uses `RgPostEffectCRT` (`Sources/Engine/Raytracing/SSRT.cpp:623`), which is present at `b1eb3d8`.
  - This revision is the common ancestor of the `doom` and `hl1` branches.
- **RTGL1 `hl1` HEAD is API-incompatible with SE-RT.** Its header (`Include/RTGL1/RTGL1.h`) no longer has `rgCreateStaticMaterial`, `rgUploadGeometry` or `rgSubmitStaticGeometries`. It moved to `rgUploadMeshPrimitive` / `rgProvideOriginalTexture` / `rgUploadNonWorldPrimitive`, with texture names in place of material handles. The `quake` branch has a third, intermediate API (`rgCreateMaterial`, `rgBeginStaticGeometries`, `rgUploadPortal`). Moving SE-RT to `hl1` is a port of its `Sources/Engine/Raytracing/` layer, about 8.9k lines (`wc -l Raytracing/*.cpp` = 8855), not a version bump.

### 3.2 RTGL1 capabilities (v1.1.0 = `b1eb3d8` vs `hl1` = `2457acc`)

| Aspect | v1.1.0 (what SE-RT uses) | hl1 HEAD |
|---|---|---|
| License | MIT, `LICENSE` © 2020 Sultim Tsyrendashiev | same |
| RT technique | Path tracing with the ray-tracing pipeline (`RtRaygenPrimary/Direct/Indirect/ReflRefr.rgen`, `.rchit`, `.rmiss`, `.rahit`), A-SVGF denoiser, GGX BRDF (`evalBRDFSmithGGX` in `Shaders/RaygenCommon.h`) | adds ReSTIR / ReSTIR GI (README), volumetrics, light grid, glTF import/export (`GltfImporter.cpp`, `GltfExporter.cpp`) |
| Required device extensions (`hl1` `Source/VulkanDevice_Init.cpp:867-874`) | ray tracing pipeline + acceleration structure (shader stages present) | `VK_KHR_swapchain`, `VK_KHR_deferred_host_operations`, `VK_KHR_pipeline_library`, `VK_KHR_ray_tracing_pipeline`, `VK_KHR_acceleration_structure`, `VK_KHR_synchronization2`, `VK_KHR_shader_float16_int8`. Vulkan API 1.2 (`apiVersion = VK_API_VERSION_1_2`, line 700). `VK_KHR_ray_query` is not required. |
| Material per surface | `RgTextureSet` = albedoAlpha + roughnessMetallicEmission + normal. Up to **3 texture layers per geometry** with blend types OPAQUE/ALPHA/ADD/SHADE and per-layer colour (`RgGeometryUploadInfo.layerColors[3]`, `layerBlendingTypes[3]`). Scalar `defaultRoughness`, `defaultMetallicity`, `defaultEmission`. | albedo + ORM (occlusion/roughness/metallic) + normal + separate emissive. `RgTextureSwizzling` chooses the ORM channel order. Up to 3 layers plus a lightmap layer (`lightmapTexCoordLayerIndex`). `RgEditorPBRInfo` gives metallic/roughness defaults. Per-primitive `emissive`. |
| Height / parallax maps | **Not supported.** No height/parallax postfix or shader code found (`git grep -i parallax\|heightmap` only matches SVGF temporal-reprojection "parallax"). | not supported |
| Texture override | Files are looked up at `<pOverridenTexturesFolderPath><folders>/<name><postfix>.ktx2`. Postfixes are set by the application. SE-RT uses `""` (albedo, sRGB), `"_rme"` (roughness-metallic-emission, linear) and `"_n"` (normal, linear) (`SSRT.cpp:352-359`). Override folder: `OverridenTextures\Compressed\` (`SSRT.cpp:316`). The relative path comes from the `.tex` file path (`TextureUploader.cpp:105`). | postfixes fixed in `Source/Const.h:40-43`: `""`, `"_orm"`, `"_n"`, `"_e"`. Formats are albedo/emissive `R8G8B8A8_SRGB` and ORM/normal `UNORM` (`TextureManager.cpp:421-424`). A "Developer" config mode loads PNG/TGA instead of KTX2 and hot-reloads them. |
| Texture input | Original pixels: R8G8B8A8 only (`RgStaticMaterialCreateInfo` comment). Overrides: KTX2 with a native `VkFormat`, read through `ktxTexture_GetVkFormat` (`Source/ImageLoader.cpp:73`). libKTX is built from source without the Basis Universal transcoder; only zstd and DFD utils are compiled (`CMakeLists.txt:105-122`), so **Basis ETC1S/UASTC KTX2 files would not be transcoded**. The official tool `Tools/CreateKTX2.py` produces BC7 (colour), BC5 (normal) or uncompressed ARGB8888 through Compressonator CLI. | same loader |
| Animated / dynamic textures | `rgCreateAnimatedMaterial` / `rgChangeAnimatedMaterialFrame`. Per-frame override paths are supported (`TextureUploader.cpp:226-238`). Dynamic materials (`rgCreateDynamicMaterial`, `rgUpdateDynamicMaterial`) never take overrides. | `textureFrame` per primitive |
| Cubemaps | `rgCreateCubemap`. Sky is either a cubemap or rasterized sky geometry rendered into a cubemap (`rasterizedSkyCubemapSize`). | `rgProvideOriginalCubemapTexture` |
| Raster capability | **Overlay only.** `rgUploadRasterizedGeometry` with render types DEFAULT / SWAPCHAIN / SKY, alpha test, blend and depth flags. "Only the albedo-alpha texture is used for rasterized geometry." This serves HUD, UI, sky and effects. There is **no full-scene raster renderer and no non-RT fallback**: device creation requires the RT extensions. | `RgDrawFrameInfo.disableRayTracedGeometry` / `disableRasterization`, and `RgDrawFrameLightmapParams.lightmapScreenCoverage` ("How much of the screen should be rendered in a lightmap mode"). The exact semantics are unverified, and the RT extensions are still mandatory at device creation. |
| Upscalers | FSR 1.0 from shader source (`Source/Shaders/FSR/ffx_fsr1.h`, `CmFsrEasu.comp`, `CmFsrRcas.comp`), AMD CAS, optional DLSS (`RG_WITH_NVIDIA_DLSS`, OFF by default, needs `DLSS_SDK_PATH`) | FSR 2 (`RG_WITH_AMD_FSR2` ON by default) linked from **prebuilt Windows-only `.lib` binaries** under `Source/FSR2/win32/`. The CMake script fails on non-Windows unless FSR2 is disabled (`CMakeLists.txt:261`). DLSS optional as before. |
| DLSS license (E7) | "NVIDIA RTX SDKs LICENSE", proprietary. §4e: "You may not use the SDK in any manner that would cause it to become subject to an open source software license." It requires attribution and NVIDIA marks for DLSS (Supplement 7.1(b)). SE-RT v1.5 tells users to download `nvngx_dlss.dll` separately (E6). **GPL interaction flagged for Agent E; not concluded here.** | same |
| FSR / CAS / LPM license | header text in `ffx_fsr2.h` and `ffx_a.h`: © AMD, MIT-style permission notice | same |
| Shader toolchain | GLSL compiled to SPIR-V with `glslc --target-env=vulkan1.2` from `Source/Shaders/GenerateShaders.py`, which needs Python 3. Shaders are loaded from a folder at runtime and support hot reload. | the same script, now invoked automatically by CMake (commit `c2ede7a`) |
| OS / windowing | CMake options `RG_WITH_SURFACE_WIN32/METAL/WAYLAND/XCB/XLIB`. Linux compile fixes landed 2022-04-17 (`cf5d95e`). | Linux build PR merged at `2457acc`. Has a Windows-only CI workflow (`.github/workflows/build-windows.yml`). A Metal surface option exists, but MoltenVK has no RT extensions (see [RD-006](./RD-006-platforms.md)). |
| SE-RT host support | README: "Other OS: Not supported". The Visual Studio solution is Windows-only, and SE-RT links `vulkan-1.lib` and `RayTracedGL1.lib`. | n/a |

### 3.3 What SE-RT's RT path covers

- Entity coverage: `Sources/Engine/Raytracing/Scene.cpp` handles only `CEntity::RT_BRUSH`, `RT_MODEL` and `RT_EDITORMODEL` (lines 487–545). **Nothing under `Sources/Engine/Raytracing/` references `RT_SKAMODEL`, `RT_SKAEDITORMODEL` or `RT_TERRAIN`** (these are defined in `Sources/Engine/Entities/Entity.h:126-128`). No file in `Engine/Ska/` hooks the RT path either. The only RT hooks are in `Rendering/Render.cpp:960` and `Models/RenderModel.cpp`. SKA models and terrains are therefore not rendered by SE-RT's ray tracer. This observation comes from reading the source and has not been tested at runtime.
- Level-specific tuning: `Raytracing/CustomInfo.cpp` hard-codes TFE world names (`01_Hatshepsut` … `13_Luxor`, lines 51–63) with per-level light and material parameters. TSE levels have no entries.
- Brush layers: SE1 brush polygons carry up to 3 texture layers with `STXF_BLEND_OPAQUE/ALPHA/ADD/SHADE`. SE-RT maps these onto RTGL1 layer blend types (`RTBrushes.cpp:126-135`). Original SE1 shadow maps (lightmaps) are replaced by path-traced lighting from SE1 light entities (`RTLights.cpp`).
- Models: `CModelObject` has `mo_toReflection`, `mo_toSpecular` and `mo_toBump` (`Models/ModelObject.h:51-53`). SE-RT reads the `SRF_REFLECTIONS` / `SRF_SPECULAR` layer flags to mark models reflective or specular (`RTModels.cpp:295-296`). Bump is not used (the call at `RTModels.cpp:669` is commented out).
- Colour space: SE-RT has the cvar `srt_bTexturesOriginalSRGB`, default `1` (`SSRTGlobals.h:38`). It treats original `.tex` albedo as sRGB, overrides as sRGB albedo with linear `_rme` / `_n`.
- Raster APIs kept in the tree: `GfxLibrary.h:76-86` enumerates `GAT_OGL`, `GAT_VK` and `GAT_RT`. `Gfx_OpenGL.cpp`, `Gfx_Vulkan.cpp` and `Gfx_RayTracing.cpp` coexist, and the game menu enables the DLSS/FSR toggles only when `GAT_RT` is selected (`SeriousSam/GUI/Menus/MenuActions.cpp:879-881`). Whether the OGL and VK paths still work at runtime in SE-RT has **not been verified**.
- Texture data shipping: the SE-RT v1.5 release distributes `TFE_RT_Textures.zip`, described as "upscaled/PBR" textures, from release v1.1 (E6). These are derivatives of game assets distributed publicly. **Flagged for Agent E**; SSTRE must not copy this practice by default (ADR-0002).

### 3.4 Raster renderers (non-RT)

- Serious-Engine-Vk (E3) and SeriousSamClassic-VK (E4) share the same `Sources/Engine/Graphics/Vulkan/Svk*.cpp` design. The files differ, but the design is clearly a common lineage; Agent A covers lineage. The renderer emulates the SE1 fixed-function pipeline:
  - `Shaders/Textured.vert` passes through position, colour and 4 texcoords, multiplied by an MVP matrix.
  - `Shaders/Textured.frag` (`#version 400`) multiplies up to 4 textures by the vertex colour and a push-constant scale.
  - There are only 3 shader programs (`Textured`, `TexturedAlpha`, `OcclusionCheck`), compiled with `glslangValidator -V` through `GenerateSpirv.bat`. SPIR-V is committed as C headers (`Shaders/Compiled/*.h`).
  - It targets Vulkan 1.2 (`Gfx_Vulkan.cpp:172`) and requires only `VK_KHR_swapchain` (line 279). About 5.7k lines in total.
- There is no per-pixel lighting, normal input, or material data in the raster shaders. SE1 lighting is baked into shadow maps and blended as a texture layer, plus per-vertex model shading done on the CPU. **A PBR raster path is a new renderer, not an extension.** It would need tangent frames for brushes and models, a G-buffer or forward+ pass, light lists from SE1 light entities, shadowing (shadow maps or reuse of SE1 shadow maps), and a fallback for SE1's layer/blend semantics. This is an estimate from the code structure, not a measurement.
- The legacy OpenGL path (`Gfx_OpenGL.cpp`, `Gfx_wrapper_OpenGL.cpp`) uses fixed-function GL 1.x calls (`glTexEnv`, `glMatrixMode`, `glAlphaFunc`, `glFog` in E4 `SamTFE/Sources/Engine/Graphics/*.cpp`). It is not portable to GLES or core-profile GL without a rewrite.
- Classic-VK portability (README, E4): Windows, Linux, FreeBSD, OpenBSD, Raspberry Pi OS and macOS. Architectures are x86, aarch64 and e2k, with CI on GitHub Actions for multiple architectures. NetBSD builds OpenGL only (`SamTFE/Sources/CMakeLists.txt:78-81`). It uses SDL2 and keeps separate `SamTFE/` and `SamTSE/` trees. The macOS Vulkan route goes through `brew install vulkan-loader` (MoltenVK); a working runtime is not verified.

### 3.5 TSE versus TFE rendering-relevant differences

- Engine-level rendering is the same SE1 1.05/1.10 engine for both games. The game-side differences are in `EntitiesMP` (TSE) versus `Entities` (TFE). Entity classes present only in E4 `SamTSE/Sources/EntitiesMP` that affect rendering include:
  - `Terrain.es` (heightmap terrain, `Engine/Terrain/`)
  - `GruntSka.es` and `ModelHolder3.es` (SKA skeletal models)
  - `EnvironmentParticlesHolder.es` (rain/snow)
  - `MeteorShower.es`, `Fireworks.es`, `SeriousBomb.es` and `PowerUpItem.es` effects
  - `TextFXHolder.es`, `HudPicHolder.es`, `CreditsHolder.es`
- SKA models render through the `Shaders` library (E5 `Sources/Shaders/`: `BaseShader`, `DetailShader`, `MultiLayerShader`, `Reflection`, `Specular`, `ReftectionAndSpecular`, `Displace`, `Translucent`, `Invisible`, `Color`, `AddShader`, plus `*DS` double-sided variants).
- Local TSE data (E8, aggregate counts over `*.gro` of the Steam Classic TSE install): 1576 `.tex`, 664 `.mdl`, 2 `.bm` (SKA mesh), 2 `.smc`, 13 `.sha`, 36 `.wld`. Local TFE: 1229 `.tex`, 359 `.mdl`, 0 SKA, 17 `.wld`. Loose files outside `.gro` (for example the `Levels/` folders) were not counted. Whether the TSE campaign itself uses SKA models or terrain is **not yet established**; Agent B / Phase 1 should inventory it per world.
- Consequence: SE-RT is TFE-tuned. For TSE it lacks SKA, terrain and per-level tuning. These gaps come from reading the code and have not been tested.

### 3.6 SE1 texture data that a PBR path must preserve (E5 `Sources/Engine/Graphics/Texture.h`, `TextureEffects.h`)

- `td_ulFlags` include `TEX_ALPHACHANNEL`, `TEX_32BIT`, `TEX_TRANSPARENT` (1-bit alpha), `TEX_EQUALIZED`, `TEX_GRAY` and `TEX_KEEPCOLOR` ("don't (de)saturate (for heightmaps and such!)"). `td_ctFrames` gives multi-frame animated textures. `td_ptegEffect` gives procedural effect textures (water, fire; `TextureEffectGlobalProperties_Water/_Fire`) that are regenerated at runtime.
- Model reflection maps are 2D textures (`mo_toReflection`), not cubemaps. Background and sky come from `BackgroundViewer` brushes.

## 4. Assumptions and unknowns

- A1. The RTGL1 `v1.1.0` + SE-RT `0e7f223` pair is assumed to build. It is unverified because no CMake or VS is on the host yet and the build has not been attempted.
- A2. AMD RDNA2+ support at v1.1.0 is suggested by the v1.5 notes ("RTGL1 with AMD support"). Intel Arc support is unknown.
- U1. The meaning of `hl1` "lightmap mode" (`lightmapScreenCoverage`) and whether it could serve as a reduced-cost mode on weak RT hardware.
- U2. Whether SE-RT's `GAT_OGL` / `GAT_VK` paths are still functional, which would give a raster fallback inside the same binary.
- U3. Which TSE worlds use SKA, terrain or `Shaders`-library materials (needs per-world inventory).
- U4. Contents and licensing of `TFE_RT_Textures.zip` (not downloaded, deliberately).
- U5. Whether HD-remaster normal and specular maps can be converted into RTGL1's roughness/metallic convention without visible errors (depends on RD-002).

## 5. Alternatives and trade-offs

| Option | Description | Pros | Cons |
|---|---|---|---|
| R1 | SE-RT + RTGL1 `v1.1.0`, as-is | Working TFE path tracer (per upstream release); `_rme` / `_n` override pipeline already exists; MIT library | Windows-only; RT hardware mandatory; no SKA or terrain; TFE-only tuning; upstream inactive since 2022; no raster fallback in RTGL1 |
| R2 | SE-RT ported to RTGL1 `hl1` | Newer denoising (ReSTIR GI), ORM + emissive maps, glTF replacement, Linux build PR | Port of about 8.9k lines of integration code; prebuilt FSR2 libraries are Windows-only (disable or rebuild on Linux) |
| R3 | Classic-VK raster engine as the base, with RTGL1 added as an optional backend (`GAT_RT` style, as SE-RT does on top of SE1's Gfx abstraction) | Proven multi-OS base, TFE + TSE trees, works without RT hardware | RT integration has to be re-done on another fork; two renderers to maintain |
| R4 | New PBR raster renderer (Vulkan) beside RTGL1 | One material data path for both renderers; console-friendly if later re-targeted to D3D12 | Largest effort; must reproduce SE1 layer, fog and haze semantics |
| R5 | Keep the raster path "classic look" only (no PBR), with PBR only in RT | Smallest effort; honest fallback | Visual gap between modes; HD albedo still applies to both |

## 6. Proposed PBR data path (proposal, not implemented)

Principles: the engine never parses AI outputs. AssetCompiler emits runtime-ready files keyed to the original `.tex` path, and the engine looks them up exactly the way RTGL1 already does.

1. **Key.** Normalised SE1 virtual path of the `.tex`, for example `Models/Enemies/Foo/Foo.tex`. This path is the RTGL1 `pRelativePath`, and it must also be the stable asset ID in SSTRE-Manifests (RD-002 / RD-004).
2. **Runtime files per material** in `<override-root>/<path-without-ext><postfix>.ktx2`:
   - albedo-alpha `""`: sRGB, BC7, or BC1/BC3/BC4 per the alpha class
   - normal `_n`: linear, BC5 (RG with Z reconstructed). The tangent-space and green-channel convention must be fixed in the manifest.
   - packed `_rme` (R roughness, G metallic, B emission) for RTGL1 v1.1.0, linear BC7
   - or `_orm` + `_e` for RTGL1 `hl1`
   - The manifest records the packing so one source set can be repacked per backend. Height/displacement is stored only as an intermediate (EXR/PNG16) and is not shipped at runtime until a renderer consumes it.
3. **Sidecar material record** (`<path>.material.json`, in the Manifests or AssetCompiler output, never read by the RT renderer directly; it is compiled into engine-side tables). Fields:
   - source `.tex` hash and flags (`TEX_*`)
   - frame count, plus a per-frame file list for animated textures (`<name>_fNN<postfix>.ktx2`, to be agreed with the engine loader)
   - `effect: water|fire|...` → **no override**; keep the procedural effect and set `RG_MATERIAL_CREATE_DISABLE_OVERRIDE_BIT`
   - colour space per map
   - default roughness / metallic / emission scalars
   - reflection-map handling (model `mo_toReflection` → metallic/roughness hint, not a texture)
   - layer role (base, detail, shade/lightmap) when known from brush usage
   - provenance hash (RD-004)
4. **Colour space.** Original SE1 textures are authored for gamma-space blending. Treat albedo as sRGB (matches the SE-RT default `srt_bTexturesOriginalSRGB = 1`). Normal, roughness, metallic and ORM are always linear (UNORM). Emissive is sRGB in `hl1` (`R8G8B8A8_SRGB`) but packed into linear `_rme` in v1.1.0, so the compiler must convert. Mark `TEX_KEEPCOLOR` / `TEX_GRAY` textures as data, not colour.
5. **Layers.** Brush layer 2/3 textures (detail, shade) get their own override sets keyed by their own `.tex`. RTGL1 resolves each layer independently, so no combined maps are needed.
6. **Raster fallback.** Only the albedo `""` file is used in raster or classic mode. PBR maps are ignored, so one package serves both modes (option R5). If R4 is chosen later, the same files feed it.
7. **Platform variants.** The same logical record is compiled into a per-platform container. PC/Linux use KTX2 with BCn; ASTC is used where BCn is not supported (see [RD-006](./RD-006-platforms.md)). Basis/UASTC supercompression is only an option if the loader gains the transcoder, which the RTGL1 build currently omits.

## 7. Risks

| Risk | Impact | Note |
|---|---|---|
| Upstream SE-RT/RTGL1 abandoned or API-diverged | High | SE-RT HEAD has no revision pin; `hl1` is incompatible. SSTRE must vendor or pin `v1.1.0` itself (Agent A / ADR-0005). |
| RT-only renderer excludes non-RT GPUs, macOS and most consoles | High | RTGL1 requires `VK_KHR_ray_tracing_pipeline`; no fallback in the library |
| TSE gaps (SKA, terrain, level tuning) | High for the TSE goal | Code-read finding; confirm with Spike S1 |
| DLSS proprietary license versus GPL distribution | Medium | §4e of the DLSS license; keep DLSS an optional, user-supplied runtime piece pending RD-007 |
| FSR2 prebuilt Windows-only `.lib` in `hl1` | Medium | Linux builds must disable FSR2 or rebuild it from FidelityFX sources |
| Inferred PBR maps look wrong under path tracing (over-glossy, wrong metal) | Medium | Plan §4.7: maps are inferred, not measured; needs curated defaults |
| Gamma-space SE1 art under linear-light path tracing changes look | Medium | Needs a calibrated tone-map / white point; SE-RT already exposes a white-point option (commit `805a96c`) |

## 8. Proposed experiment: Spike S1 "RT/raster baseline and PBR override"

Preconditions: CMake, Vulkan SDK and VS installed on the reference PC; GPU inventoried. Builds use the untrusted upstream code in an isolated work tree, as plan §9 requires.

1. Build RTGL1 `v1.1.0` (`b1eb3d8`) and SE-RT `0e7f223` unmodified. Record the exact toolchain (VS, Vulkan SDK, glslc versions) and every failure.
2. Run TFE `01_Hatshepsut` and one heavy level (for example `13_Luxor`) with a scripted demo in modes `GAT_RT`, `GAT_VK` and `GAT_OGL` (U2).
3. Load TSE data. Pick 3 TSE worlds: one with terrain and one with SKA content if the RD-002 inventory finds them.
4. PBR override test: for 10 textures from the RD-002 matrix (brush base, brush detail layer, model, animated, alpha-tested, effect texture), place hand-made `_n` / `_rme` KTX2 files (BC7 / BC5 via Compressonator) and confirm they are picked up.
5. Capture frame time (mean, 99th percentile), VRAM, and screenshots at fixed camera positions at 1080p, native and FSR1.

Measurable success criteria:

| # | Criterion | Pass threshold |
|---|---|---|
| S1.1 | Unmodified build succeeds | RTGL1 + SE-RT build with documented steps; 0 source edits, or every edit listed |
| S1.2 | TFE RT run | Both TFE levels load and play 5 min of demo with no crash and no Vulkan validation errors at "error" severity |
| S1.3 | Raster fallback in the same binary | `GAT_VK` or `GAT_OGL` renders the same demo (yes/no; record which) |
| S1.4 | TSE coverage | For each TSE world: list entities not rendered (SKA, terrain) by screenshot comparison against `GAT_VK`. Pass = the gap list is complete and reproducible; it is not expected to be empty |
| S1.5 | Override pickup | 10/10 overrides load (confirmed by RTGL1 log or a visual marker texture); 0 overrides applied to effect textures |
| S1.6 | Colour-space correctness | A neutral 18 % grey test albedo override renders within ΔE2000 ≤ 3 of the original in `GAT_VK` under a flat-lit test room (calibrates the sRGB assumption) |
| S1.7 | Performance record | Frame-time p50/p99 and VRAM recorded per mode and GPU. No pass/fail target until a baseline exists |

## 9. Recommendation

1. Treat **RTGL1 `v1.1.0` (`b1eb3d8`) + SE-RT `0e7f223`** as the only known-compatible pair. Record it in the umbrella pins as a pair; do not track RTGL1 `hl1`.
2. Do **not** assume a raster fallback exists in RTGL1. The portable fallback should be the SE1 Vulkan renderer (Serious-Engine-Vk / Classic-VK lineage) with albedo-only HD textures (option R5). Defer a PBR raster renderer (R4) until after Phase 5.
3. Adopt the PBR data path in §6, keyed on the `.tex` virtual path, with backend-neutral manifest records and per-backend packing (`_rme` now, `_orm` + `_e` if RTGL1 is upgraded).
4. Before committing to SE-RT as the TSE base, run Spike S1. SKA, terrain and the TFE-only tuning are the main TSE risks.
5. Keep DLSS out of SSTRE-distributed binaries pending RD-007. FSR1/CAS (MIT) are acceptable candidates, subject to Agent E.

## 10. Decision dependencies

- ADR-0005 (engine foundation): R1/R2 versus R3. Depends on RD-001 build results and Spike S1.
- ADR-0006 (licensing): DLSS, FSR2 binaries, MIT RTGL1 inside GPL-2.0 engine; derived texture distribution.
- ADR-0007 (platform strategy): the RT-only renderer limits platforms (see [RD-006](./RD-006-platforms.md)).
- RD-002 inventory (SKA, terrain, animated/effect textures) and RD-004 stable IDs.

## 11. Next steps

1. Lead: decide whether Spike S1 enters the first POC sprint; inventory the reference GPU.
2. Agent A: confirm the pair `RTGL1 v1.1.0 ↔ SE-RT 0e7f223` in RD-001 and record it as the pinned revision.
3. Agent B: per-world TSE inventory of SKA, terrain and `.sha` usage; flag animated and effect textures in the inventory schema.
4. Agent E: DLSS license §4e versus GPL-2.0; MIT RTGL1 linked into a GPL-2.0 engine; FSR2 binary libraries; status of upstream `TFE_RT_Textures.zip`.
5. After S1: draft the `material.json` schema in `schemas/`. It is not written now because the evidence is insufficient.
