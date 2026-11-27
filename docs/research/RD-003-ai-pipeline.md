# RD-003: AI texture pipeline (super-resolution, controlled diffusion, VLM, PBR, QA)

| Field | Value |
|---|---|
| Dossier | RD-003 |
| Author | Agent C (AI and deterministic build researcher), Phase 0 |
| Date | 2026-11-27 |
| Status | **Draft research, no benchmarks run.** Nothing in this document has been executed on project hardware. All quality, speed and VRAM statements are hypotheses until the benchmark plan in section 9 is executed. |
| Related | [RD-002 HD assets / 50-asset matrix](./RD-002-hd-assets.md), [RD-004 reproducibility](./RD-004-reproducibility.md), [RD-007 licensing](./RD-007-licensing.md), [RD-008 testing/release](./RD-008-testing-release.md), schemas [`asset-recipe.schema.json`](../../schemas/asset-recipe.schema.json), [`build-provenance.schema.json`](../../schemas/build-provenance.schema.json) |

## 1. Question and scope

Plan open decision 3: *Which AI models/workflows preserve structure, alpha, tiling and art direction best, at acceptable compute cost?*

In scope:

- Conventional single-image super-resolution (SR): Real-ESRGAN and variants, SwinIR, HAT, DAT and other architectures loadable through common tooling.
- Controlled diffusion: SDXL + tile ControlNet / tiled upscalers, FLUX-family, other current diffusion/one-step restoration models; **licenses of code and weights**.
- Orchestration: ComfyUI versus headless alternatives (diffusers, chaiNNer/spandrel, custom PyTorch).
- Development-only VLM classification (Qwen-VL family and alternatives).
- PBR map derivation (normal/height/roughness from albedo).
- Alpha handling, seamless tiling, pixel-art / low-resolution issues, textures that must not go through diffusion.
- Quality metrics as signals, and a benchmark plan against the RD-002 50-asset matrix.

Out of scope: runtime rendering of PBR (RD-005), texture compression/packaging formats (RD-005/RD-006), legal conclusions (RD-007; this dossier only reports license labels as observed).

## 2. Evidence (primary sources, accessed 2026-11-27)

Version/date data was taken from the GitHub REST API (`gh api repos/<r>/releases/latest`, `gh api repos/<r>`) and the Hugging Face model API (`https://huggingface.co/api/models/<id>`) on 2026-11-27. "sha" = HF repo revision at time of query (first 12 hex chars); pin full revisions when downloading.

| Item | Source | Observed |
|---|---|---|
| Real-ESRGAN | https://github.com/xinntao/Real-ESRGAN | BSD-3-Clause (repo); latest release `v0.3.0` (2022-09-20); last push 2024-08-06. `inference_realesrgan.py` exposes `--tile` (default 0), `--tile_pad` (default 10), `--fp32` (default is fp16: "Default: fp16 (half precision)"), `--alpha_upsampler` (`realesrgan` \| `bicubic`). README warns tiling may cause block inconsistency. Weights (e.g. `RealESRGAN_x4plus`, `realesr-general-x4v3`, `RealESRGAN_x4plus_anime_6B`) distributed as GitHub release assets; no separate weight license stated. |
| BasicSR | https://github.com/XPixelGroup/BasicSR | Apache-2.0; last push 2024-07-21 (low maintenance). |
| SwinIR | https://github.com/JingyunLiang/SwinIR | Apache-2.0 code ("Please also follow their licenses" for Swin Transformer / KAIR); real-world `_GAN` checkpoints (SwinIR-M, SwinIR-L) via GitHub releases; weight license not separately stated. |
| HAT | https://github.com/XPixelGroup/HAT | Apache-2.0 code; `Real_HAT_GAN_SRx4.pth` (2022-11-24) and `Real_HAT_GAN_SRx4_sharper.pth` (2023-08-01) via Google Drive/Baidu; weight license not separately stated. |
| DAT | https://github.com/zhengchen1999/DAT | Apache-2.0 code; DAT-S/DAT/DAT-2/DAT-light (bicubic-degradation models) via Google Drive/Baidu; weight license not stated. |
| spandrel | https://github.com/chaiNNer-org/spandrel | MIT ("architecture code inside `__arch/` covered by each architecture's original license"); latest release `v0.4.2` (2026-02-21). Supports ESRGAN/Real-ESRGAN, SRVGGNet compact, SwinIR, Swin2SR, HAT, DAT, ATD, DRCT, RGT, PLKSR/RealPLKSR, SPAN, Real-CUGAN, SCUNet, NAFNet, FBCNN, LaMa, etc. Restrictively licensed arches (SRFormer, FeMaSR, CodeFormer, MAT, Restormer, M3SNet, MPRNet, MIRNet2, DDColor) are split into `spandrel_extra_arches`. |
| chaiNNer | https://github.com/chaiNNer-org/chaiNNer | GPL-3.0; latest release `v0.26.1` (2026-10-27). GUI node editor (uses spandrel). |
| OpenModelDB | https://github.com/OpenModelDB/open-model-database | GPL-3.0 database of community SR models with per-model license metadata (community models frequently carry CC-BY-NC-SA or other non-commercial terms; **check per model**). |
| ComfyUI | https://github.com/Comfy-Org/ComfyUI | GPL-3.0; latest release `v0.46.0` (2026-11-18); very active (push 2026-11-27). `comfy/cli_args.py`: `--deterministic` ("Make pytorch use slower deterministic algorithms when it can. Note that this might not make images deterministic in all cases."), `--force-fp32`, `--fp32-vae`/`--bf16-vae`/`--fp16-vae` ("might cause black images"), `--disable-all-custom-nodes`, `--whitelist-custom-nodes`, `--offline`, `--fast` ("untested and potentially quality deteriorating optimizations"). `main.py` implements `--deterministic` as `torch.use_deterministic_algorithms(True, warn_only=True)`. `comfy/sample.py` generates initial noise with `torch.manual_seed(seed)` and `torch.randn(..., device="cpu")` in float32. |
| ComfyUI-Manager | https://github.com/Comfy-Org/ComfyUI-Manager | GPL-3.0; installs arbitrary custom nodes (code execution). |
| ComfyUI_UltimateSDUpscale | https://github.com/ssitu/ComfyUI_UltimateSDUpscale | GPL-3.0; push 2026-06-22. |
| ComfyUI-TiledDiffusion | https://github.com/shiimizu/ComfyUI-TiledDiffusion | **No license detected by GitHub API**; last push 2025-03-18. Treat as unusable for distribution until clarified. |
| diffusers | https://github.com/huggingface/diffusers | Apache-2.0; latest release `v0.43.0` (2026-11-12). Reproducibility guide: https://huggingface.co/docs/diffusers/main/en/using-diffusers/reusing_seeds (CPU `Generator` recommended; `enable_full_determinism()`). |
| PyTorch | https://github.com/pytorch/pytorch | latest release `v2.15.0` (2026-10-28); reproducibility notes https://docs.pytorch.org/docs/2.15/notes/randomness.html (see RD-004). |
| SDXL base 1.0 | https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 | Weights: CreativeML Open RAIL++-M (use-based restrictions, attachment obligations). |
| SDXL tile ControlNet (xinsir) | https://huggingface.co/xinsir/controlnet-tile-sdxl-1.0 | `license:apache-2.0`; created 2024-06-26; sha `1ae8d9529efe`. Card: supports deblur/repaint, variation, SR; "performance may unstable"; example SR splits image 3x3 and stitches. |
| FLUX.1 [dev] | https://huggingface.co/black-forest-labs/FLUX.1-dev | "FLUX.1 [dev] Non-Commercial License"; outputs "can be used for personal, scientific, and commercial purposes as described in" the license. |
| FLUX.1 [schnell] | https://huggingface.co/black-forest-labs/FLUX.1-schnell | `license:apache-2.0`; sha `169573f54945`. |
| FLUX.2 [dev] | https://huggingface.co/black-forest-labs/FLUX.2-dev | 32B rectified-flow transformer; "FLUX Non-Commercial License". |
| FLUX.2 [klein] 4B / 9B | https://huggingface.co/black-forest-labs/FLUX.2-klein-4B | 4B: `license:apache-2.0`, created 2026-01-14, sha `e7b7dc27f91d`. 9B: `license:other` (non-commercial per BFL repo/press: https://venturebeat.com/technology/black-forest-labs-launches-open-source-flux-2-klein-to-generate-ai-images-in). VRAM claims conflict across sources (~8 GB vs ~13 GB) — to benchmark. |
| Flux.1-dev ControlNet Upscaler (jasperai) | https://huggingface.co/jasperai/Flux.1-dev-Controlnet-Upscaler | `license:other` (derived from FLUX.1-dev; assume non-commercial until RD-007 confirms). |
| SD 3.5 Large | https://huggingface.co/stabilityai/stable-diffusion-3.5-large | `license:other` (Stability Community License; revenue-threshold terms — RD-007 to assess). |
| Qwen-Image | https://huggingface.co/Qwen/Qwen-Image | `license:apache-2.0`; sha `75e0b4be04f6`. |
| HunyuanImage-2.1 | https://huggingface.co/tencent/HunyuanImage-2.1 | `license:other` (Tencent community license; territorial restrictions reported — RD-007). |
| SeedVR2-3B | https://huggingface.co/ByteDance-Seed/SeedVR2-3B , https://github.com/ByteDance-Seed/SeedVR | `license:apache-2.0` (weights and code); one-step diffusion restoration (video/image), ICLR 2026. |
| SUPIR | https://github.com/Fanghua-Yu/SUPIR | "Non-Commercial Use Only Declaration" on top of repo license; depends on SDXL + LLaVA; README: "12G for Diffusion, 16G for LLaVA" in low-VRAM mode. |
| Flux seamless texture LoRA | https://huggingface.co/gokaygokay/Flux-Seamless-Texture-LoRA | `license:apache-2.0` tag on LoRA, but base is FLUX.1-dev (non-commercial base) — combined use inherits base license terms (hypothesis, RD-007). |
| Qwen2.5-VL | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct | 7B `apache-2.0`; 72B `license:other` (Qwen license); 3B: **no license tag in HF API** (verify LICENSE file before use). |
| Qwen3-VL | https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct | 2B/4B/8B/30B-A3B all `license:apache-2.0` (created 2025-09/10). |
| Qwen3.5 (natively multimodal) | https://huggingface.co/Qwen/Qwen3.5-9B | 2B/4B/9B/27B/35B-A3B: `license:apache-2.0`, `pipeline_tag: image-text-to-text`, created 2026-02. |
| InternVL3-8B | https://huggingface.co/OpenGVLab/InternVL3-8B | `license:apache-2.0`. |
| Florence-2-large | https://huggingface.co/microsoft/Florence-2-large | `license:mit` (captioning/OCR/detection; small). |
| Gemma 3 12B | https://huggingface.co/google/gemma-3-12b-it | `license:gemma` (custom terms with use policy). |
| Marigold (normals, IID appearance) | https://github.com/prs-eth/Marigold , https://huggingface.co/prs-eth/marigold-iid-appearance-v1-1 | Code Apache-2.0; weights "RAIL++-M License" (`openrail++`). IID-appearance predicts albedo / roughness / metallicity; normals model separate. |
| StableNormal | https://github.com/Stable-X/StableNormal | Code Apache-2.0 (weights license not verified — HF API query failed). |
| RGB↔X (Adobe) | https://github.com/zheng95z/rgbx | LICENSE = "ADOBE RESEARCH LICENSE", "noncommercial research purposes only". **Excluded.** |
| DeepBump | https://github.com/HugoTini/DeepBump | GPL-3.0 ("This repo is under the GPL license"); albedo→normal, normal→height, curvature; ONNX models; no explicit seamless option stated in README. |
| LPIPS | https://github.com/richzhang/PerceptualSimilarity | BSD-2-Clause; pip `lpips`, metric version `0.1`. |
| DISTS | https://github.com/dingkeyan93/DISTS | MIT; last push 2020. |
| pyiqa (IQA-PyTorch) | https://github.com/chaofengc/IQA-PyTorch | README: "PolyForm Noncommercial License 1.0.0 ... and the NTU S-Lab License for applicable components". **Do not depend on it** in distributed tooling; re-implement metrics from permissively licensed reference code. |

Not accessed / not verified: actual weight-file licenses for Real-ESRGAN/SwinIR/HAT/DAT GitHub/Google-Drive assets (repos state code licenses only); StableNormal weights; TTPlanet SDXL tile ControlNet (HF API returned non-JSON); Real-DAT; any closed/hosted model.

## 3. Observed facts (summary)

1. Every mainstream conventional SR architecture we need (ESRGAN/Real-ESRGAN, SRVGGNet, SwinIR, HAT, DAT, ATD, DRCT, RealPLKSR, SPAN, SCUNet) is loadable by **spandrel (MIT)** without the original training repos. Original code repos are Apache-2.0 / BSD-3-Clause. Weight licenses are mostly **unstated**; community fine-tunes (OpenModelDB) often carry non-commercial terms.
2. Real-ESRGAN upstream is effectively frozen (last release 2022). Its default inference precision is **fp16**; alpha is upscaled separately (`realesrgan` or `bicubic`).
3. The SDXL ecosystem has permissive-enough conditioning: SDXL base (RAIL++-M, use-restricted, not non-commercial) + xinsir tile ControlNet (Apache-2.0).
4. FLUX.1-dev, FLUX.2-dev, FLUX.2-klein-9B and derived ControlNets are **non-commercial weights**. FLUX.1-schnell and FLUX.2-klein-4B are Apache-2.0. Qwen-Image and SeedVR2 are Apache-2.0.
5. ComfyUI (GPL-3.0, v0.46.0) generates seed noise on the CPU in fp32 (good for cross-GPU seed stability), but its `--deterministic` flag uses `warn_only=True`, which per PyTorch 2.15 docs leaves fused SDPA backends nondeterministic. Custom nodes are arbitrary Python executed at load time.
6. Current open VLMs suitable for development-time classification with permissive licenses exist: Qwen3-VL 2B–30B-A3B, Qwen3.5 2B–35B-A3B, InternVL3-8B (Apache-2.0), Florence-2 (MIT). Qwen2.5-VL-72B is under a custom license.
7. Learned PBR estimators with research-only licenses (Adobe RGB↔X) must be excluded; Marigold weights are RAIL++-M; DeepBump is GPL-3.0 (compatible with a GPL-3.0 toolkit, subject to RD-007).
8. The popular all-in-one IQA library `pyiqa` is now PolyForm Noncommercial; `lpips` (BSD-2) and DISTS (MIT) are permissive.

## 4. Model and tool comparison

Legend for license column: **P** = permissive (MIT/BSD/Apache); **GPL**; **RAIL** = OpenRAIL use-restricted; **NC** = non-commercial / research-only; **?** = not stated/unverified. "Usable" assumes the project's GPL-3.0 tooling, user-local execution, and that generated textures are never redistributed by the project (plan §1); RD-007 makes final calls.

| Tool / model | Role | Code license | Weights license | Structure fidelity (hypothesis) | Alpha | Tiling/seam support | Determinism notes | Recommendation |
|---|---|---|---|---|---|---|---|---|
| Real-ESRGAN x4plus / x2plus | Conventional SR (GAN) | BSD-3 (P) | ? (GitHub release assets) | High; GAN hallucination of fine texture; known over-smoothing on flat areas | Separate alpha upsampler | Tile+pad; no circular wrap built in | Feed-forward; fp16 default — force fp32 for reference builds | **Baseline candidate** |
| realesr-general-x4v3 (SRVGGNet) | Fast compact SR | BSD-3 (P) | ? | Medium-high, fewer artifacts, less detail | via wrapper | as above | Feed-forward | Fast fallback / preview |
| SwinIR-L real GAN | Transformer SR | Apache-2.0 (P) | ? | High (to benchmark) | wrapper needed | window size constraints → pad | Attention ops; check SDPA determinism | Candidate |
| HAT / Real_HAT_GAN | Transformer SR | Apache-2.0 (P) | ? | High (to benchmark); heavy VRAM | wrapper | pad to window multiple | as SwinIR | Candidate |
| DAT / DAT-2 | Transformer SR (bicubic degr.) | Apache-2.0 (P) | ? | Bicubic-trained → may underperform on real/DXT-compressed sources | wrapper | pad | as SwinIR | Lower priority |
| spandrel | Model loader | MIT (P) | n/a | n/a | n/a | n/a | Pin version; wraps arch code under original licenses | **Use as loader** |
| chaiNNer | GUI pipeline | GPL-3.0 | n/a | n/a | has alpha nodes | has tile nodes | GUI-first; not ideal headless | Curation/manual tool only |
| SDXL base + xinsir tile ControlNet | Controlled diffusion detail | diffusers Apache-2.0 / ComfyUI GPL-3.0 | RAIL++-M + Apache-2.0 | Medium; depends on denoise; risk of style drift and invented detail | None (RGB only) — alpha must bypass | Tiled sampling + overlap; circular padding possible via conv padding patch (hypothesis) | Sampler-dependent; CPU noise; SDPA nondeterminism | **Primary diffusion candidate** |
| Ultimate SD Upscale (ComfyUI node) | Tiled diffusion upscale | GPL-3.0 | n/a | Seams mitigated by overlap/seam-fix passes | n/a | overlap, seam fix modes | Tile order fixed | Candidate if ComfyUI chosen |
| ComfyUI-TiledDiffusion / MultiDiffusion | Tiled latent diffusion | **no license** | n/a | — | — | — | — | **Do not use** until licensed |
| SeedVR2-3B | One-step diffusion restoration | Apache-2.0 | Apache-2.0 | Unknown for game textures (to benchmark); trained for real video/images | None | to verify | One-step reduces sampler variance (hypothesis) | **Benchmark candidate** |
| FLUX.2-klein-4B | Image gen/edit | Apache-2.0 | Apache-2.0 | Unknown; would need tile/edit conditioning | None | — | bf16 native | Exploratory only |
| FLUX.1-schnell | Distilled gen | Apache-2.0 | Apache-2.0 | No mature tile ControlNet with permissive weights found | — | — | — | Low priority |
| FLUX.1-dev / FLUX.2-dev / klein-9B / jasperai upscaler | High-quality gen/upscale | Apache-2.0 code | **NC** | — | — | — | — | **Exclude from default pipeline** (optional user-local only if RD-007 permits) |
| SUPIR | Diffusion SR | repo + NC declaration | NC + SDXL + LLaVA | — | — | — | — | **Exclude** |
| Qwen-Image | Gen/edit | Apache-2.0 | Apache-2.0 | Unknown; large (to benchmark VRAM on 12 GB) | — | — | — | Exploratory |
| Qwen3-VL-8B / Qwen3.5-9B | Dev-time classification, prompts | Apache-2.0 | Apache-2.0 | n/a | n/a | n/a | Use greedy decoding, record outputs; dev-only | **Primary VLM candidates** |
| Qwen3-VL-30B-A3B / Qwen3.5-35B-A3B | Higher-quality VLM | Apache-2.0 | Apache-2.0 | n/a | | | Needs quantization on 12 GB (to benchmark) | Secondary |
| InternVL3-8B | VLM alternative | Apache-2.0 | Apache-2.0 | n/a | | | | Alternative |
| Florence-2-large | Captions/OCR (text detection) | MIT | MIT | n/a | | | | **Text/HUD detector candidate** |
| Qwen2.5-VL-72B / Gemma 3 | VLM | — | custom (Qwen / Gemma terms) | | | | | Avoid unless needed |
| DeepBump | Albedo→normal→height | GPL-3.0 | GPL-3.0 (bundled ONNX; verify) | Heuristic-learned; plausible not measured | n/a | not stated; apply wrap padding externally | ONNX runtime; CPU path deterministic (hypothesis) | **PBR candidate** |
| Marigold normals / IID-appearance | Normals, albedo/roughness/metallic | Apache-2.0 | RAIL++-M | Trained on scenes/objects, not flat textures (domain gap) | n/a | none | Diffusion-based: ensemble/seed variance | Benchmark candidate |
| StableNormal | Normals | Apache-2.0 | ? | Scene-trained | | | | Benchmark only after weight license check |
| RGB↔X | Intrinsic decomposition | Adobe Research (NC) | NC | | | | | **Exclude** |
| Classical (non-ML) height/normal: Sobel/Scharr on luminance, frequency separation | PBR baseline | own code | none | Deterministic, predictable | n/a | trivially circular | Bit-exact on CPU | **Mandatory baseline + fallback** |
| lpips 0.1 / DISTS | Metrics | BSD-2 / MIT | AlexNet/VGG ImageNet backbones (torchvision weights; check terms) | n/a | | | | Use |
| pyiqa | Metric suite | PolyForm NC | mixed | | | | | **Do not depend on** |

## 5. Technical issues and proposed handling

### 5.1 Alpha

- SR and diffusion models are RGB. Proposed rule: split RGBA; process RGB; process alpha separately with (a) the SR model on a 3-channel replicated alpha, (b) Lanczos/bicubic, or (c) nearest/threshold for 1-bit cutout masks. Choose by alpha class (binary, multi-level, smooth gradient).
- **Color bleeding:** before upscaling, dilate/inpaint RGB into fully transparent texels (edge padding), otherwise black/garbage RGB under alpha=0 bleeds into edges after filtering and mipmapping.
- For binary cutouts (foliage, grates, fences), re-threshold alpha at the source threshold after upscaling and measure **alpha IoU** against nearest-neighbor upscaled source mask; optionally coverage-preserving alpha for mip levels (RD-005 owns mip generation).
- Premultiplied versus straight alpha must be recorded per asset in the inventory (RD-002); processing always in straight alpha with explicit conversion.
- Diffusion never sees alpha; alpha is re-attached and the RGB under alpha<threshold is re-dilated afterwards.

### 5.2 Seamless tiling / wrap

- Most SE1 world textures are expected to tile (inventory flag from RD-002; must not be assumed). Tiling textures: pad by wrapping (`numpy.pad(mode="wrap")` / `torch.nn.functional.pad(mode="circular")`) by at least the model receptive-field margin before SR, then crop the centre. This is exact for feed-forward CNNs if the pad ≥ receptive field; for transformer models (window attention) margin must cover window shift — to measure.
- Diffusion: options are (1) wrap-padding the latent/image and cropping, (2) patching all `Conv2d` layers in UNet and VAE to `padding_mode="circular"` (community technique; hypothesis — verify quality and that it does not break ControlNet residual shapes), (3) offset-and-re-denoise seam pass (shift image by half a tile, re-process a band, blend).
- Tiled inference of large images (VRAM-driven) uses overlap with feathered blending; tile size, overlap and blending function are recipe parameters and part of the cache key (RD-004).
- **Seam metric:** for a tileable output O of size W×H, compute mean absolute difference between column 0 and column W−1 (and rows), normalised by the mean absolute difference between adjacent interior columns. Ratio ≈ 1 means seam is statistically indistinguishable from interior; also compute on the source to calibrate. Plus LPIPS of a 2×2 tiled crop centred on the seam versus an interior crop.

### 5.3 Pixel-art and low-resolution sources

- Classic SE1 textures are low-resolution (exact distribution from RD-002), frequently palettized or block-compressed. Hypotheses to test: GAN SR trained on photos over-sharpens dithering and creates ringing; anime-trained models (`RealESRGAN_x4plus_anime_6B`) preserve flat regions better; diffusion at denoise > ~0.4 invents detail inconsistent with the source (threshold to measure, not assumed).
- Pre-processing options: de-JPEG/de-DXT (FBCNN or SCUNet, via spandrel; licenses per arch), palette-aware handling (detect ≤256 unique colours).
- For UI fonts, small sprites and pixel-precise art, classical scalers (nearest + optional xBR/xBRZ-type, Lanczos) are the conservative default; ML only by curated override.
- When an HD-remaster source exists (RD-002), it is generally preferable to AI reconstruction; AI then serves only to fill resolution gaps or derive PBR maps.

### 5.4 Textures that must not go through diffusion (default policy)

Normal maps, height/bump, specular/gloss masks, detail/lightmaps, shadow/light-cast masks, cubemap faces (cross-face seam constraint), text/HUD/fonts/menu graphics, logos, numerical/technical lookup textures, palette-indexed effect textures, animated frame sets (temporal coherence — process frames identically or not at all), and any texture whose alpha encodes data rather than coverage. Detection: inventory metadata first (RD-002), VLM/OCR (Florence-2) second, curated override last.

### 5.5 PBR derivation

- PBR maps derived from albedo are **inferred, not measured** (plan §4.7). Minimum viable: classical luminance→height→normal (Sobel/Scharr with configurable strength, wrap-aware), roughness from inverted, contrast-normalised luminance with per-material-profile mapping curves, metallic from material profile (not per-pixel ML) by default.
- ML candidates to benchmark: DeepBump (GPL-3.0), Marigold normals / IID-appearance (RAIL++-M). Domain gap: these are trained on photographs/scenes, not flat tiling textures — must be measured on the matrix.
- Delighting (removing baked lighting from albedo) is a risk: SE1 textures frequently have baked shading that is part of art direction; default = do not delight.
- Normal map convention (OpenGL +Y vs DirectX −Y), encoding (2-channel BC5 vs RGB), and colour space (albedo sRGB, all others linear) are recorded per output; RD-005 decides runtime representation.

### 5.6 VLM classification (development only)

- Role: propose texture class, tileability, "contains text", material profile, and an optional prompt. Outputs are written to generated per-asset recipes, frozen and reviewed; never called in release builds (plan §3).
- Run greedy decoding (temperature 0) with a fixed prompt template and a constrained JSON output schema; store model id + revision hash + prompt template hash + raw response in the generated recipe's provenance. Measure agreement with a hand-labelled subset (section 9).

### 5.7 Orchestration: ComfyUI versus headless

| Option | Pros | Cons |
|---|---|---|
| ComfyUI (GPL-3.0) as engine, API-format workflow JSON | Large node ecosystem, fast iteration, API endpoint, CPU noise | Custom nodes = arbitrary code; rapid release cadence (v0.46.0 on 2026-11-18); `--deterministic` is `warn_only`; workflow JSON not a stable interface; GUI-centric |
| diffusers (Apache-2.0) + spandrel (MIT) + own Python | Small, pinnable, testable, explicit determinism control (`enable_full_determinism`), easy cache keys | Must implement tiling/ControlNet tile orchestration ourselves; fewer ready-made upscalers |
| chaiNNer (GPL-3.0) | Good SR/alpha/tile tooling | GUI-first; weak headless/batch reproducibility story |

Proposal: **headless Python (diffusers + spandrel + own tiling) is the release-build executor**; ComfyUI is allowed as a development/curation sandbox, with exported workflows translated to resolved recipes. Revisit if the headless prototype proves too costly (Phase 3 gate).

## 6. Per-texture-class processing policy (proposal)

Classes are expected to come from the RD-002 inventory schema; names here are proposals. "SR" = conventional SR model chosen by benchmark; "CD" = controlled diffusion.

| Class | Default chain | Diffusion | Alpha | Tiling | PBR | Fallback |
|---|---|---|---|---|---|---|
| HD-remaster source available and mapped | Use HD source → resample to target size (Lanczos), convert colour space | No | as source | verify seam | derive from HD | Classic + SR |
| Architecture / walls / floors (tileable, opaque) | Wrap-pad → SR (x4) → downscale to target → optional CD (low denoise, tile ControlNet) | Optional, low denoise, by profile | n/a | wrap pad, seam metric | classical + ML candidate | SR-only → original |
| Terrain / ground / rock | as architecture | Optional | n/a | wrap | as above | SR-only |
| Vegetation / foliage / grates (cutout alpha) | Edge-dilate RGB → SR RGB → alpha nearest/threshold or SR on alpha → re-dilate | No by default | binary threshold, alpha IoU gate | per flag | height optional | bicubic alpha + SR RGB → original |
| Translucent effects (glass, particles, smoke) | SR or Lanczos; alpha via SR | No | smooth alpha | per flag | none | Lanczos |
| Character / enemy skins (UV atlases) | SR only, no wrap padding (UV islands), gutter dilation | No by default (curated only) | as needed | no wrap; island-aware padding | optional | original |
| Weapons (first-person, prominent) | SR; candidate for curation | Curated only | as needed | no | optional | original |
| Sky / backgrounds | SR; check horizontal wrap | Optional low denoise | n/a | horizontal wrap if flagged | none | SR-only |
| Cubemap / environment faces | Per-face SR with cross-face padding (assemble cross) | No | n/a | cube-edge continuity | none | Lanczos |
| UI / HUD / fonts / text / logos | Nearest or Lanczos; optional SR anime model by override | **Never** | exact | no | none | original |
| Normal maps (if any), height, specular, masks, lightmaps, LUTs | Linear-space resample (Lanczos/bicubic); normals renormalised | **Never** | exact | per flag | n/a | original |
| Animated texture frame sets | Same deterministic chain per frame; no CD | No | as class | as class | consistent across frames | original |
| Unknown / unclassified | SR-only with conservative model | No | as detected | per flag | none | original |

QA gates per class (thresholds to calibrate in benchmark): dimension/format check; alpha IoU (cutout) ≥ calibrated threshold; seam ratio ≤ calibrated threshold; structural similarity of downscaled output vs source (SSIM on luminance at source resolution) ≥ threshold; LPIPS/DISTS vs SR-only reference for CD outputs (drift bound); mean colour shift (ΔE2000 on downscaled image) ≤ threshold. Failing a gate triggers the next fallback in the row and is recorded in provenance.

## 7. Quality metrics (signals, not proof)

| Metric | What it signals | Reference | Notes |
|---|---|---|---|
| SSIM / MS-SSIM (downscaled output vs source) | Structural fidelity to original | own implementation or scikit-image (BSD-3) | Compare at source resolution after a fixed downscale (area/box) — avoids rewarding blur at HR |
| PSNR (downscaled vs source) | Gross colour/structure deviation | trivial | |
| LPIPS v0.1 (alex/vgg) | Perceptual difference | https://github.com/richzhang/PerceptualSimilarity (BSD-2) | Also used for determinism tolerance (RD-004) |
| DISTS | Perceptual, texture-tolerant | https://github.com/dingkeyan93/DISTS (MIT) | Better suited to texture resampling than LPIPS (hypothesis) |
| ΔE2000 mean / p95 | Colour drift | own code | On linearised, downscaled images |
| Seam ratio (section 5.2) | Wrap continuity | own code | Calibrate on source |
| Alpha IoU / alpha MAE | Cutout integrity | own code | Binary at source threshold |
| High-frequency energy ratio | Over-sharpening / hallucination | own code (Laplacian variance vs SR-only reference) | Signal for diffusion drift |
| No-reference IQA (NIQE, MUSIQ, …) | Generic naturalness | various | Low priority; trained on photos; avoid pyiqa (NC) |
| Human A/B (blind, in-engine screenshots) | Art-direction preservation | local only | Ground truth for gate calibration; no restricted images in repos |

## 8. Alternatives and tradeoffs

- **SR-only versus SR + controlled diffusion:** SR-only is faster, more deterministic and structurally safer; diffusion adds detail but risks art-direction drift, seams and nondeterminism. Default proposal: SR-only for most classes, diffusion as opt-in per material profile, gated by drift metrics.
- **SDXL + tile ControlNet versus FLUX-family:** FLUX dev-class weights are non-commercial; Apache-2.0 FLUX variants (schnell, klein-4B) lack proven tile conditioning for upscaling (not found in this survey). SDXL (RAIL++-M) + Apache-2.0 ControlNet is the most license-viable mature option; SeedVR2 (Apache-2.0) is a promising one-step alternative to benchmark.
- **Release-time diffusion versus "frozen outputs":** the plan requires users to build locally (no distribution of derivatives). Therefore release builds re-run diffusion on user hardware, making cross-GPU determinism a core problem (RD-004). SR-only pipelines are much easier to keep within tolerance.
- **Headless versus ComfyUI:** see 5.7.

## 9. Benchmark plan (Phase 3 POC)

### 9.1 Asset set

Use the 50-asset test matrix defined in [RD-002](./RD-002-hd-assets.md) (classes: architecture, terrain, vegetation, enemies, weapons, UI, alpha, normal maps, technical masks; plan §8 POC). Each matrix row must carry: stable asset ID, source SHA-256, class, dimensions, alpha type, tileable flag, HD-counterpart flag. If RD-002's matrix lacks any class in section 6, the lead adds rows before the benchmark starts. Assets remain local (`<workspace>/local-work/` or user workspace); only IDs, hashes and metrics are committed.

### 9.2 Candidate configurations (initial)

| ID | Chain |
|---|---|
| B0 | Lanczos x4 (control) |
| B1 | Real-ESRGAN x4plus fp32 (via spandrel) |
| B2 | realesr-general-x4v3 fp32 |
| B3 | RealESRGAN_x4plus_anime_6B fp32 |
| B4 | SwinIR-L real GAN fp32 |
| B5 | Real_HAT_GAN_SRx4 fp32 |
| B6 | Best of B1–B5 + SDXL base + xinsir tile ControlNet, denoise ∈ {0.2, 0.35, 0.5}, fixed sampler (Euler, non-ancestral), 20 steps, fp16 UNet / fp32 VAE |
| B7 | Best of B1–B5 + SeedVR2-3B |
| B8 | Each of B1/B5/B6 in fp16 and bf16 (precision sensitivity) |
| P0–P2 | PBR: classical Sobel height/normal; DeepBump; Marigold normals |
| V0–V2 | VLM classification: Qwen3-VL-8B, Qwen3.5-9B, InternVL3-8B (+ Florence-2 for text detection) |

All with wrap padding for tileable assets and alpha policy per section 5.1.

### 9.3 Measurements

- Quality: all metrics in section 7, per asset and per class (median, p10, p90).
- Cost: wall time per asset (warm, excluding model load; model load separately), peak VRAM (`torch.cuda.max_memory_allocated` and NVML), CPU time, output size. **No cost estimates are given here — all to benchmark.**
- Determinism: run each configuration 3× in the same process and 3× in fresh processes; compare output SHA-256 and LPIPS/max-abs-diff (protocol in RD-004 §8).
- VLM: accuracy of class, tileable and contains-text labels versus a hand-labelled ground truth of the 50 assets; JSON-schema validity rate.
- Human review: blind A/B of B1-best vs B6 vs B7 on in-engine screenshots for ≥ 10 prominent assets (local only).

### 9.4 Hardware and environment recording

Each run writes a build-provenance record ([schema](../../schemas/build-provenance.schema.json)) including: GPU model, VRAM, SM count/compute capability, driver version, CUDA runtime, cuDNN, PyTorch, diffusers, spandrel versions, OS build, Python version, CPU model, env flags (`CUBLAS_WORKSPACE_CONFIG`, deterministic settings), model file SHA-256s. Initial host observed by `nvidia-smi` on 2026-11-27: NVIDIA GeForce RTX 4070, 12282 MiB, driver 616.64 (single-GPU reference candidate; a second GPU architecture is needed for cross-GPU tests).

### 9.5 Pass/fail criteria (proposed; thresholds calibrated in first run, then frozen)

| Criterion | Pass |
|---|---|
| Coverage | 50/50 assets produce an output or an explicit recorded fallback; no stall/crash aborts the batch |
| Technical classes | 100% of UI/text/normal/mask/technical assets routed away from diffusion (policy compliance) |
| Alpha | Cutout assets: alpha IoU ≥ threshold T_a (calibrated from B0/B1 distribution, proposed start 0.95) on 100% after fallback |
| Seams | Tileable assets: seam ratio ≤ T_s (calibrated from source distribution) on 100% after fallback |
| Fidelity | SSIM(downscaled output, source) ≥ T_f for ≥ 95% of assets per selected config |
| Automated acceptance | Fraction passing all gates without fallback reported per config (aspirational 95%, not a gate) |
| Human preference | Selected diffusion config preferred over SR-only on ≥ 50% of prominent assets, else diffusion stays opt-in only |
| Cost | Recorded for all; selection requires the full TFE texture set be processable on the reference GPU in a time the owner accepts (target set after measurement) |
| Determinism | Per RD-004 §8 tolerance classes |
| VLM | Class accuracy and contains-text recall reported; contains-text recall must be 100% after OCR+inventory rules before VLM labels drive diffusion routing |
| License | Every model in the selected config has a recorded, RD-007-reviewed license; none NC |

## 10. Assumptions and unknowns

- RD-002 matrix contents, texture sizes, compression and alpha conventions are not yet known to this dossier.
- Weight licenses for SR checkpoints are unstated by upstream; treated as "?" pending RD-007.
- Whether Apache-2.0 FLUX variants support adequate tile/upscale conditioning is unknown.
- Whether circular conv padding in SDXL UNet/VAE yields clean seams with ControlNet is a hypothesis.
- VRAM fit of SDXL + ControlNet + tiled VAE, Qwen3.5-9B and SeedVR2-3B on 12 GB: to benchmark.
- Whether users' GPUs (non-NVIDIA, older) can run the pipeline at all: unknown; CPU fallback cost unknown.

## 11. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Diffusion drifts from art direction | Loss of recognisable identity | SR-first default, low denoise, drift gates, human review of prominent assets |
| Non-commercial / unclear weight licenses | Legal exposure, rework | License column mandatory in recipes; RD-007 review; exclude NC |
| Cross-GPU nondeterminism of user-side builds | Irreproducible builds, cache misses | Tolerance-based equivalence (RD-004), SR-only default |
| Custom-node supply-chain risk (ComfyUI) | Code execution | Headless executor; pinned, reviewed nodes only in dev |
| Domain gap of PBR estimators | Implausible materials | Classical baseline + profile curves; ML opt-in |
| Upstream abandonment (Real-ESRGAN, BasicSR) | Dependency rot | Load weights via spandrel; vendor no training code |
| Metric gaming | Passing gates with bad results | Multiple metrics + human calibration; metrics are signals |

## 12. Recommendation

1. Build the release executor headless: Python + PyTorch + spandrel (SR) + diffusers (optional diffusion), own tiling/alpha/wrap code. ComfyUI only as dev sandbox.
2. Default chain = conventional SR (select among Real-ESRGAN, SwinIR, HAT variants by benchmark, fp32 reference) with wrap padding and alpha policy; HD-remaster sources preferred where mapped.
3. Controlled diffusion = opt-in per material profile, SDXL base + xinsir tile ControlNet, non-ancestral sampler; benchmark SeedVR2-3B as alternative. Exclude FLUX dev-class, SUPIR, RGB↔X and other NC weights.
4. VLM dev-time: Qwen3-VL-8B or Qwen3.5-9B (Apache-2.0) with Florence-2 for text detection; frozen outputs only.
5. PBR: classical baseline mandatory; DeepBump/Marigold benchmarked as candidates.
6. Metrics: own implementations + `lpips` + DISTS; avoid `pyiqa`.

## 13. Decision dependencies

- RD-002: inventory schema, class taxonomy, 50-asset matrix, HD mapping.
- RD-004: determinism settings, cache keys, tolerance classes.
- RD-005: runtime PBR representation, normal convention, mip/compression.
- RD-007: weight-license review, GPL compatibility of DeepBump/ComfyUI usage, RAIL++-M obligations.
- RD-008: acceptance gates integration.
- Owner: acceptable compute time budget for user-side builds; whether diffusion is in scope for v1.

## 14. Next steps

1. Inventory reference GPU(s): obtain a second NVIDIA architecture (and ideally an AMD GPU) for cross-hardware tests.
2. Prototype headless SR runner (spandrel) with wrap padding, alpha split and provenance output (Remaster-Toolkit, Phase 3).
3. Download candidate weights by pinned revision, record SHA-256, record license text per model.
4. Execute benchmark B0–B5, calibrate thresholds, then B6–B8, P*, V*.
5. Write ADR for model selection after benchmark; update this dossier with measured results.
