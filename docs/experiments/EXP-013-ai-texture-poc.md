# EXP-013: AI texture-processing proof of concept (Remaster-Toolkit)

> **Correction (2026-11-28, from [EXP-016](EXP-016-tex4096-crash.md)):** the in-engine comparison ran with the shipped `tex_iNormalSize=9` (uploads capped to a 512² area) and, on OpenGL, 16-bit uploads of textures without `TEX_32BIT`. Its in-engine numbers are therefore partly affected by downscaled uploads. A corrected re-run with `tex_iNormalSize=11`, `tex_iNormalQuality=22` and `TEX_32BIT` follows as an addendum.

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | Sprint 2 track AI1 (AI PoC); RD-003 §9 benchmark plan (subset); RD-004 §8 determinism (subset); RD-008 §6–7 |
| Status | partial: toolkit, deterministic SR, QA, fallback, caching, provenance, raster import with a frame-exact in-engine comparison, and the layer-6 asset pack are done; generative refinement works and is deterministic but QA rejects it; KTX2 is produced but not render-tested (needs E1's RT build) |
| Environment | Windows 11 Pro 10.0.22631; NVIDIA RTX 4070 12 GB (CC 8.9, 46 SM), driver 616.64; Python 3.10.11 venv `G:\sstre-tmp\ai\venv`: torch 2.14.1+cu130 (CUDA 13.0, cuDNN 9.24), torchvision 0.29.1, spandrel 0.4.2, diffusers 0.41.0, transformers 5.20.2, accelerate 1.15.0, numpy 2.2.6, Pillow 12.3.0, lpips 0.1.4, DISTS_pytorch 0.1 (`pip freeze` SHA-256 `7a76d2f1…0e79`, local only). CI emulation: a second venv with numpy, Pillow, pytest and jsonschema only. Compressonator CLI 4.6.0 (zip SHA-256 `6fb42c9b…43d5`, the same file as EXP-002). Classic-VK TFE runtime: a private copy of the Phase 1 runtime with binaries copied from E3's `sprint2/bench-fixes` build |
| Inputs | Track A1 set1: 16 decoded Classic TFE textures plus JSON (`G:\sstre-tmp\assets\set1`, local only); A1 `.tex` codec (AssetCompiler `feature/tex-codec-source-selection` @ `32e1ed3`); A2 build plan (AssetCompiler `feature/asset-layers-profiles`). No asset paths, hashes or images are published here (GATE-05) |
| Code | Remaster-Toolkit branch `feature/ai-texture-poc` (package `src/remaster_toolkit/`, `tests/`, CI `pytest` job). The game-specific driver is outside every repo, in `G:\sstre-tmp\ai\driver\` (local) |

## Goal and success criteria

The goal is a small set of reproducibly enhanced textures that load in the Classic-VK runtime, built with real toolkit code. No full-scale generation. Success means:

1. Recipe and caching: resolved recipes (asset-recipe schema), RFC 8785 canonicalisation, content-addressed step keys chained on output hashes, resume after interruption, and incremental invalidation, all tested.
2. Deterministic SR through spandrel, with pinned weights and recorded hashes and licences, fp32 vs fp16, and a run-twice hash comparison.
3. Seamless tiling: wrap padding, overlap and feathering, a seam metric.
4. Alpha preservation: a separate alpha path, re-thresholding, an IoU/coverage check.
5. Opt-in generative refinement: a locked model and seed, run twice, never applied to UI, normal maps or masks.
6. Material workflows: tileable, cutout, skin, UI (conservative), data maps (non-generative), plus a classical normal/height baseline.
7. Automated QA, a fallback ladder with reason codes, and a build-provenance record per output.
8. Runtime output: PNG, KTX2 (BC7/BC5) and Classic `.tex`, plus an in-engine comparison.

## Procedure (exact, reproducible)

1. **Environment.** `py -3.10` cannot be executed in the agent sandbox (STATUS_ACCESS_DENIED). The venv was therefore created from the Phase 1 venv interpreter. torch was installed from the `cu130` index with an exact version (`torch==2.14.1+cu130`; 2.15 has no Python 3.10 wheel there). TEMP, PIP_CACHE_DIR, HF_HOME and TORCH_HOME all point to `G:\sstre-tmp\ai\`.
2. **Weights** (`driver/download_models.sh`) were downloaded from immutable references only: a GitHub release tag for SR, and a Hugging Face commit SHA for diffusion. Each was registered by content hash (`remaster-toolkit models-register`; local `models/registry.json`). Results are in the table below.
3. **Toolkit.** `src/remaster_toolkit/` contains `jcs` (own RFC 8785, stdlib only), `recipe` (layered resolution `deep-merge/arrays-replace/null-deletes@1`, NFC prompts, schema validation), `cache` (CAS plus atomic index), `executor` (planning, step keys, QA, ladder, provenance), `ops`, `sr` (spandrel; `torch.load(weights_only=True)` state dict, no TorchScript fallback), `diffusion` (diffusers SDXL + ControlNet img2img), `tiling`, `resample` (exact edge-mode weight matrices), `alpha`, `pbr`, `qa`, `perceptual` (LPIPS/DISTS, optional), `workflows`, `policy`, `models`, `env` and `cli`.
4. **Tests:** `SSTRE_SCHEMAS_DIR=<umbrella>/schemas python -m pytest` runs 82 tests, both with the full GPU venv and in the CPU-only CI emulation without torch. The CI job `pytest` was added to `.github/workflows/sstre-checks.yml` with pinned numpy, Pillow, pytest and jsonschema. All fixtures are procedural, and GPU ops are replaced by CPU stand-ins.
5. **SR benchmark** (`driver/bench_sr.py run1`, then `run2` in a fresh process, under the GPU lock): 9 SR-eligible set1 textures × {Lanczos, RealESRGAN_x4plus, x4plus_anime_6B, realesr-general-x4v3, SwinIR-L real GAN} × {fp32, fp16/bf16}. Each configuration ran twice in-process. Settings were D1: `use_deterministic_algorithms(True, warn_only=False)`, cuDNN benchmark off, cuDNN deterministic, TF32 off, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, math SDPA.
6. **set1 runs** (`driver/run_set1.py runB|runC`, each in a fresh process with a fresh cache): the per-texture class/wrap/target table is game-specific and lives in the driver. Recipes were built with `workflows.build`, resolved, validated against `asset-recipe.schema.json`, and executed by `executor.build_asset`. Provenance was validated against `build-provenance.schema.json`. Targets follow the lead/EXP-012 constraints: 2× or 4×, longest side ≤ 2048, mex unchanged; generative textures 2× (1024).
7. **Export** (`driver/export_runtime.py runC`): KTX2 via `compressonatorcli -fd BC7|BC5 -miplevels 20` into a virtual-path mirror. Classic `.tex` via A1's `classic_tex.make_replacement` (imported from A1's worktree): same mex, firstMip lowered by log2(scale). The original texture is rebuilt from A1's sidecar and must re-encode byte-identically to the archive file first.
8. **In-engine comparison** (raster, GPU lock `AI1`). The loose `.tex` files were copied into a private runtime copy at their virtual paths, and paired original/enhanced captures were taken on Vulkan and OpenGL (§Results 5). Afterwards the runtime was cleaned.

## Results ([EXP] unless labelled otherwise)

### 1. Models, hashes, licences

| Model | Source (immutable ref) | SHA-256 (prefix) | Weight licence (honest) |
|---|---|---|---|
| RealESRGAN_x4plus | GitHub xinntao/Real-ESRGAN release `v0.1.0` | `4fa0d389…` | **unknown**: no licence stated for the weights; code BSD-3-Clause. Hash is trust-on-first-use (no upstream digest for this asset) |
| RealESRGAN_x4plus_anime_6B | release `v0.2.2.4` | `f872d837…` | unknown (as above) |
| realesr-general-x4v3 | release `v0.2.5.0` | `8dc7edb9…` | unknown (as above) |
| SwinIR-L realSR x4 GAN | GitHub JingyunLiang/SwinIR release `v0.0` | `99adfa91…` | unknown; code Apache-2.0 |
| SDXL base 1.0 (fp16 UNet + text encoders, fp32 VAE; bundle) | HF `stabilityai/stable-diffusion-xl-base-1.0` @ `462165984030d82259a11f4367a4eed129e94a7b` | bundle `54c4d94c…` | CreativeML Open RAIL++-M: use-based restrictions (Attachment A) must be passed on; not non-commercial. Every LFS file matched the HF-listed SHA-256 |
| xinsir controlnet-tile-sdxl-1.0 (bundle) | HF @ `1ae8d9529efe58f7362a987363ff86a7904dc84f` | bundle `c35d7e0f…` | Apache-2.0 (HF tag). LFS SHA-256 matched |
| LPIPS AlexNet / DISTS VGG16 backbones (metrics only) | torchvision `alexnet-owt-7be5be79`, `vgg16-397923af` | match their file-name prefixes | ImageNet-trained torchvision weights; terms not reviewed (RD-003 table note) |

HAT and DAT were not tested because their weights are only on Google Drive or Baidu, which have no immutable reference. pyiqa was not used.

### 2. SR benchmark (9 textures, x4, whole image; SwinIR tiled 256/32)

| Config | median ms/texture | peak alloc / reserved MiB | in-process A==B | run1==run2 (fresh process) | SSIM↓src | LPIPS↓src | DISTS↓src | seam ratio (tileables, median) |
|---|---|---|---|---|---|---|---|---|
| Lanczos (CPU) | 213 | – | yes | yes | 0.989 | 0.013 | 0.029 | 1.35 |
| x4plus fp32 | 302 | 2446 / 4120 | yes | yes | 0.940 | 0.072 | 0.098 | 1.82 |
| x4plus fp16 | 309 | 2412 / 3512 | yes | yes | 0.940 | 0.072 | 0.098 | 1.82 |
| anime_6B fp32 | 196 | 2399 / 4100 | yes | yes | 0.872 | 0.165 | 0.149 | 1.50 |
| general-x4v3 fp32 | 69 | 219 / 592 | yes | yes | 0.953 | 0.063 | 0.094 | 1.38 |
| general-x4v3 fp16 | 54 | 215 / 548 | yes | yes | 0.953 | 0.063 | 0.094 | 1.38 |
| SwinIR-L fp32 | 4308 | 1107 / 1686 | yes | yes | 0.965 | 0.038 | 0.073 | 1.25 |
| SwinIR-L bf16 | **failed** | – | – | – | – | – | – | – |

- Warm GPU time per texture for 512² inputs (→2048²): general-x4v3 0.12–0.21 s, x4plus 0.9–1.2 s, SwinIR-L 9.5 s. Model load takes 0.05–0.64 s after the first process-level import.
- **Determinism:** every SR configuration was bit-identical (SHA-256 of the float32 output) in-process (A/B) and across two fresh processes. That is **T0 for this host, driver and torch build** under D1 settings. Claimed only for this environment.
- **Precision:** fp16 vs fp32 differs by at most 13/255 (x4plus) or 3–4/255 (compact, anime), on 12–20 % of pixels (median). The cost difference is negligible, so fp32 is the reference.
- SwinIR bf16 fails in spandrel 0.4.2 (`expected scalar type Float but found BFloat16`), and spandrel reports SwinIR as not fp16-capable.
- The SSIM/LPIPS columns compare an area downscale of the output with the source. Lanczos scores best by construction because it adds no detail. These are signals, not quality rankings.
- **Wrap padding is architecture-dependent.** Terrain seam ratio (source 1.06): general-x4v3 gives 3.50 with no pad, 1.21 with 16 px and 1.18 with 32/64 px. At ≥ 32 px it is exactly roll-equivariant (max |Δ| = 0 against rolled input). RRDB x4plus gives 4.29 / 1.83 / 1.39 / 1.24 for 0/16/32/64 px and is still not equivariant at 64 px (max |Δ| 0.011): its receptive field exceeds 64 px.
- Visual check (local crops: weapon, enemy skin, carved frieze, palm). anime_6B repaints and smears detail (rejected). x4plus is sharp but removes plaster grain. general-x4v3 keeps grain and edges closest to the source. SwinIR-L is the most faithful but 35–60× slower than general-x4v3.
- **Decision:** default SR = realesr-general-x4v3 fp32 with 32 px wrap padding; SwinIR-L is a candidate for curated prominent assets.

### 3. set1 through the toolkit (run C; workflows, QA, fallback)

| # | Category → class (workflow) | Target | Ladder | Notes |
|---|---|---|---|---|
| 0 | architecture → architecture (tileable, wrap U, SDXL refinement opt-in) | 1024² (2×) | L2 sr-only | SDXL refine failed STRUCT_LOW (SSIM 0.47 < 0.75; LPIPS vs SR 0.22) |
| 1 | terrain → terrain (tileable, wrap UV, refinement opt-in) | 1024² | L2 sr-only | refine failed STRUCT_LOW (SSIM 0.59); SR-only seam 1.16 (source 1.06) |
| 2 | terrain grass overlay → vegetation-cutout (soft alpha) | 1024² | **L0 original** | SEAM (premultiplied seam 2.86 vs source 2.24: the overlay is not actually tileable; the U-wrap plan was wrong) and COLOR_DRIFT 3.67 |
| 3 | vegetation → vegetation-cutout | 1024² | L2 | alpha MAE 0.007, IoU@0.5 0.969 |
| 4, 15 | enemy, props → character-skin | 1024² | L2 | |
| 5 | weapon → weapon | 2048² | L2 | |
| 6–9 | UI, crosshair, icon, font → ui-text (Lanczos only) | 1024² / 128² | L2 | never SR or diffusion; alpha MAE ≤ 0.022 |
| 10, 12 | detail, specular → mask-technical (linear resample) | 512² / 256² | L2 | |
| 11 | bump → height-map | 512² | L2 | |
| 13 | sky → sky (no wrap: seam 30 in both axes) | 2048×1024 | L2 | |
| 14 | 23-frame effect → animated-frame (identical chain per frame) | 256² ×23 | L2 | |

- **QA calibration history** (thresholds are uncalibrated placeholders, RD-008 §6.1). In run B, per-pixel CIEDE2000 failed most SR outputs (2.2–3.5) because it penalises the detail SR adds, and RGB seam/LPIPS on alpha textures were dominated by hidden colour under alpha = 0. Run C measures colour drift on low-passed images (alpha-weighted for alpha textures) and seam/LPIPS on premultiplied colour, and keeps the per-pixel value as a signal. This is a metric definition change made after one look at the data, not a human-audited calibration. It is reported as such.
- **Fallback ladder works.** First diffusion run (run A): a dtype error in refine gave `STEP_ERROR` and the build continued on `sr-only` (L2). Run B: gate failures descended to `conventional` (L1) and `original` (L0) with reason codes. The policy test blocks diffusion for a mislabelled UI recipe (`DIFFUSION_FORBIDDEN`). A single failure never stopped the batch.
- Provenance: 38 records (16 assets + 22 extra frames). All validate against `build-provenance.schema.json` and all recipes against `asset-recipe.schema.json`.
- Cost, run C: SR steps take 0.01–0.41 s (GPU). The whole set1 SR-only path takes < 40 s, most of it CPU (QA, PNG encode, LPIPS/DISTS). The SDXL refine step takes 50 s warm per 1024² texture (20-step schedule at denoise 0.3, so 6 executed steps, math SDPA, CPU offload), with peak allocated 10.6 GiB and **peak reserved 11.8 GiB of 12 GiB**. The first call includes a 220–370 s cold load (pipeline load plus hash verification of the 7.5 GB bundle).

### 4. Generative refinement (SDXL base + xinsir tile ControlNet)

- Locked parameters: seed 1234 (CPU `torch.Generator`, float32 noise), Euler, 20 steps, denoise 0.3, CFG 5, ControlNet 0.9, fp16 UNet/ControlNet, fp32 VAE decode, math SDPA, deterministic algorithms. Circular padding is patched per axis into all 122 Conv2d layers for wrap textures.
- **Determinism:** runs B and C (separate processes, fresh caches) produced identical output hashes for **all 171 shared step keys, including both diffusion steps**: T0 on this host. [ASM] Not expected across GPUs or drivers (RD-004).
- Seams: circular convolution kept terrain seamless (seam 1.00 vs source 1.06). Wrap-U architecture seam is 1.47.
- **Quality:** visually plausible, with a crisper frieze, but the plaster turns greyer and smoother than the source. QA rejects it (SSIM 0.47/0.59; low-pass ΔE 2.7/2.3). This matches RD-003's art-direction drift risk. Lower denoise (0.15) was not tested in time.
- Policy: workflows never emit generative steps for ui-text, normal, height, mask or lightmap. The executor refuses them independently (`policy.check`), and curated-only classes need a curated-override layer.

### 5. Runtime outputs and in-engine comparison (raster, Classic-VK)

- **`.tex`:** all 16 originals rebuild byte-identically through A1's codec from the set1 sidecars. 9 replacements were written: wall 1024², terrain 1024², palm 1024², werebull 1024², tommygun 2048², sky 2048×1024, detail 512², sphinx 1024², effect 256² ×23. mex is unchanged and firstMip is lowered by 1–2. UI, font, bump and specular textures (firstMip 0) cannot gain pixels without changing mex, so they get **no `.tex`**: PNG/KTX2 only (`TexCodecError` recorded).
- **KTX2:** 15 albedo (BC7) and 1 normal (BC5, terrain) files, 22 KB–5.6 MB, produced in 0.3–3 s each. Not render-tested: this needs E1's RT build.
- **Comparison 1** (wall-clock-synced). The menu Intro flyover over Karnak was captured at the log marker `Adding player` + 28/33/38/43 s, on VK and GL. `+demo` was not available in the Phase 1 binary, and campaign level starts open Netricsa. All replacements loaded on both APIs with no log errors. Camera jitter of a few frames dominates pixel metrics (SSIM 0.50–0.97 per pair), so these are not texture-quality numbers. Laplacian-variance ratio enhanced/original is 0.96–0.99: no over-sharpening at screen scale. Zoomed crops: palm fronds cleaner and less blocky; other surfaces indistinguishable at that distance.
- **Comparison 2** (frame-exact demo playback): see §5b.

### 5b. Frame-exact demo comparison (Classic-VK, E3 `+demo` build)

- Method [SRC+EXP]. The engine exposes `dem_fSyncRate` (`Engine/Network/Network.cpp:760`): with a rate N the demo clock advances exactly 1/N s per rendered frame. `dem_iAnimFrame` (`GameMP/Game.cpp:598, 2825–2844`) saves every rendered frame as `ScreenShots\Anim_NNNNN.tga`. With `dem_fSyncRate=20; dem_iAnimFrame=0;` and E3's `+demo` option (engine `sprint2/bench-fixes` `b7c7e998`; binaries copied into the private runtime, E3's tree untouched), frame k shows the same demo time in every run. Every 10th frame was kept. Shipped demos `auto-demoMP0002` (Karnak coop, close-range combat) and `auto-demo0001` (Alley of Sphinxes) were run on Vulkan and OpenGL, original vs the 9 loose `.tex` of run C, under the official `gpu-lock.ps1 run` mode.
- **Vulkan `GrabScreen` returns a flat grey frame** (all pixels 128, 530 frames). Frame dumps work only on OpenGL in this build. Vulkan was verified with comparison 1 (window capture).
- **Camera identity verified (OpenGL).** In `auto-demoMP0002`, 46 of 253 matched frames are pixel-identical, namely the frames with no replaced surface in view; the median changed area is 3.0 %. In `auto-demo0001`, 13 of 96 are identical (median 2.1 %). Frames after the demo ends belong to the real-time menu intro and are excluded. HUD chat lines and the score counter differ between runs; they are excluded from the crops.
- Metrics on fixed crops covering replaced surfaces (orig vs enhanced; local-only images):

| Crop (frame) | Asset class | SSIM | LPIPS | DISTS | HF ratio enh/orig |
|---|---|---|---|---|---|
| Werebull at close range (MP0002 #940) | enemy skin, 4× | 0.901 | 0.116 | 0.097 | 1.04 |
| first-person weapon view (MP0002 #1390) | weapon, 4× | 0.873 | 0.028 | 0.048 | 1.24 |
| Werebull at mid range (MP0002 #940) | enemy skin | 0.988 | 0.016 | 0.033 | 0.93 |
| Alley view (demo0001 #270, largest change) | mixed | 0.998 | 0.004 | – | 0.99 |

- Visual judgement (local crops). **At close range the 4× enemy skin shows coherent, sharper hide and crack detail with faithful colours, where the original is visibly blurry. Weapon panel edges are crisper.** At mid or long range the enhanced textures are indistinguishable (engine mip selection). No seams, alpha fringes or colour shifts were seen on the replaced surfaces. FLIP was not computed because no FLIP implementation is installed.

### 7. ADR-0009 layer 6: asset pack (local)

- I generated a conservative-profile plan with A2's planner (AssetCompiler `feature/asset-layers-profiles`; config `ai1-conservative`, pc-default). It sets 8 assets to `awaiting-output` at `plannedPx` (×2: 512–1024 px). It does not process the HD-Quality-supplied sphinx (`source-sufficient`), the effect (`not-eligible` in conservative), or UI, font and technical maps.
- `driver/run_set1.py runP --plan …`: deterministic SR ×4 followed by an area downscale to `plannedPx`, with no generative steps. 7 of 8 passed (L2). grass09 fell back to the original (L0, SEAM/COLOR_DRIFT), so it is not in the pack and stays `awaiting-output`.
- Pack `ai1-runp` (`kind: ai-enhancement`, `qualityProfile: conservative`, `localOnly`): 7 entries, each with the plan's asset ID, output SHA-256 and px, `input.sourceSha256` = SHA-256 of the decoded mip-0 PNG the plan records as `source.imageSha256` (layer `classic-base`), `recipeHash` (= `resolvedRecipeHash`), `provenanceSha256` (JCS hash of the build-provenance record, file shipped next to it), and `qa.passed`/`fallbackUsed`. It validates against `asset-pack.schema.json` (umbrella `feature/build-config-schemas`).
- With the pack listed in the config, A2's `validate-config --verify-files` reports OK and `plan` reports `applied` for all 7 entries (none rejected), with grass09 `awaiting-output`.

### 6. Tests and checks

- Remaster-Toolkit: 82 tests pass, with full GPU deps and in CPU-only CI emulation. They cover the JCS RFC samples and number serialisation, the precedence and merge rules, resolved-hash layout independence, schema validation, no-change → 0 recomputed, a single parameter → only `sharp` + `encode`, formatting-only → 0, a byte-identical upstream output keeping downstream hits, corrupt blob detection, resume after a kill at steps 1/3/4 (identical lock), model-hash invalidation, wrap padding equal to a circular network, tiled = untiled with overlap, seam fix, alpha binarity and IoU, the fallback ladder, step errors, policy, and the boundary deny-list.
- Remaster-Toolkit: `validate_repo.py --root .` gives 0 errors and 0 warnings; `reuse lint` is compliant. Umbrella worktree: `validate_repo.py` gives 0 errors; `reuse lint` is compliant with reuse 5.0.2, the CI pin. reuse 6.3 flags two pre-existing SPDX-like strings in EXP-003, which this change does not touch.
- Commits (Remaster-Toolkit `feature/ai-texture-poc`): `90e119d` (package, tests, CI job), `086a418` (GPU-run fixes), `70467dd` (QA metric fixes).

## Deviations, modifications and failures

- SwinIR-L bf16 failed in spandrel. HAT and DAT were not tested (no immutable download).
- The first set1 runs exposed four real bugs, each fixed and committed: in-place clamp on an inference tensor; diffusers re-casting the force-upcast VAE to fp16 before our fp32 decode; a naive `einsum` resampler (50× slower); and a GPU runtime class that depended on whether torch had been imported, which caused a cache miss on re-plan.
- QA metric definitions changed between runs B and C (above).
- Grass overlay (#2) wrap flag was wrong in the driver plan; it was correctly rejected by QA.
- The diffusion denoise sweep was not done. The diffusion cost is near the 12 GB limit.
- `py.exe` / Windows Store Python is not executable in the sandbox.
- **Lock incident (reported to the lead):** a timed-out `acquire` did not stop my PowerShell chain. Two ~40 s demo runs started at 23:21–23:22 while E3 held the lock, and E3 re-ran the affected samples. Since then all GPU work uses `gpu-lock.ps1 run`.
- `+demo` (comparison 1) was not available in the Phase 1 binary, and campaign level starts open Netricsa. Comparison 1 therefore used the menu flyover; comparison 2 used E3's build.

## Interpretation ([SRC]/[DOC]/[ASM] clearly labelled)

- [EXP] On one RTX 4070 / driver / torch build, deterministic settings make both feed-forward SR and SDXL+ControlNet img2img bit-reproducible run to run. RD-004's T0 can be claimed for this reference-environment candidate, for these pipelines. Cross-GPU equivalence is untested.
- [EXP] Conventional SR with a compact model is cheap: about 0.1–0.2 s per 512² texture, so roughly 15 min of GPU time for a few thousand textures [ASM: linear scaling, excluding QA/CPU]. It is wrap-exact with adequate padding. Large RRDB/transformer models need bigger pads or cost far more.
- [EXP] SDXL tile refinement at denoise 0.3 is deterministic but drifts from the source art. Conservative SR-only should stay the default (consistent with the owner's `conservative` profile decision). Refinement remains an opt-in experiment.
- [ASM] The low-pass ΔE and premultiplied seam definitions are better aligned with "colour drift" and "seam" than the RD-003 drafts. Thresholds still need the human-audited calibration (RD-008 §6.5).

## Impact on ADRs, dossiers and backlog

- RD-003: fill the §9 cells for B0–B4 (partial) and B6 (one configuration). Record that HAT and DAT are blocked by their distribution channel.
- RD-004: first measured T0 cells (SR fp32/fp16 and SDXL fp16 under D1, same host). Add the rule "runtime class must be computed independently of import order".
- RD-008: the reason codes were used as specified; add `STEP_ERROR`. Define colour drift as low-pass ΔE.
- ADR-0009 layer 6: outputs published as an `asset-pack` (`kind: ai-enhancement`), accepted by A2's planner; see §7.
- Engine/bench: Vulkan `GrabScreen` (used by `dem_iAnimFrame` and screenshots) returns grey in Classic-VK. A fix would enable frame-exact Vulkan comparisons.

## Open questions

- Owner: is SR-only acceptable as the vertical-slice default, with refinement kept experimental? (This matches the `conservative` profile.)
- RD-007: the weight licences of the Real-ESRGAN and SwinIR checkpoints are unstated. Is "unknown, user-downloaded, hash-pinned" acceptable for a user-side builder?
