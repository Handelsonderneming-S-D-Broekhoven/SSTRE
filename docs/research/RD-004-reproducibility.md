# RD-004: Reproducible, cached and resumable asset builds

| Field | Value |
|---|---|
| Dossier | RD-004 |
| Author | Agent C (AI and deterministic build researcher), Phase 0 |
| Date | 2026-11-27 |
| Status | **Draft research and design proposal. No determinism experiment has been run.** No bit-identity is promised for any environment. |
| Related | [RD-003 AI pipeline](./RD-003-ai-pipeline.md), [RD-002 HD assets](./RD-002-hd-assets.md), [RD-008 testing/release](./RD-008-testing-release.md), schemas [`asset-recipe.schema.json`](../../schemas/asset-recipe.schema.json), [`build-provenance.schema.json`](../../schemas/build-provenance.schema.json) |

## 1. Question and scope

Plan open decision 4: *How much bit-level determinism is possible across GPU architectures, drivers and libraries? Define reference environment and tolerances from measurements.* Plus the plan §4 reproducibility requirements: recipe precedence and freezing, canonical serialization, content-addressed cache keys, incremental invalidation, resume, provenance, model hash verification, custom-node pinning.

Out of scope: CI infrastructure (RD-008), legal status of models (RD-007).

## 2. Evidence (accessed 2026-11-27)

| Source | Observed content |
|---|---|
| PyTorch 2.15 reproducibility notes — https://docs.pytorch.org/docs/2.15/notes/randomness.html | "Completely reproducible results are not guaranteed across PyTorch releases, individual commits, or different platforms." Results may differ CPU vs GPU with identical seeds. `torch.use_deterministic_algorithms(True)` errors on known-nondeterministic ops without deterministic alternative; for fused SDPA backends (Flash, Efficient, cuDNN) `warn_only=True` only warns and keeps nondeterministic paths: "To actually enforce determinism, pass warn_only=False." `cudnn.benchmark=False` "causes cuDNN to deterministically select an algorithm"; `cudnn.deterministic=True` controls convolution only. `torch.utils.deterministic.fill_uninitialized_memory` is True by default under deterministic mode. |
| cuBLAS 13.5 docs §2.1.4 "Results Reproducibility" — https://docs.nvidia.com/cuda/cublas/index.html#results-reproducibility | Same bit-wise results "when executed on GPUs with the same architecture and the same number of SMs"; "bit-wise reproducibility is not guaranteed across toolkit versions"; guarantee breaks with multiple streams unless per-stream workspace or `CUBLAS_WORKSPACE_CONFIG=:16:8` (may limit performance) or `:4096:8` (~24 MiB more memory). |
| diffusers reproducibility guide — https://huggingface.co/docs/diffusers/main/en/using-diffusers/reusing_seeds | Recommends CPU `torch.Generator` ("CPU RNG is more stable across machines"); `enable_full_determinism()` sets `CUDA_LAUNCH_BLOCKING=1`, `CUBLAS_WORKSPACE_CONFIG=:16:8`, `use_deterministic_algorithms(True)`, `cudnn.deterministic=True`, `cudnn.benchmark=False`, disables TF32 matmul; "it is not *guaranteed* even with an identical seed." diffusers latest release v0.43.0 (2026-11-12). |
| ComfyUI v0.46.0 (2026-11-18) — https://github.com/Comfy-Org/ComfyUI | `main.py`: `--deterministic` → `torch.use_deterministic_algorithms(True, warn_only=True)`; help text: "might not make images deterministic in all cases". `comfy/sample.py`: noise = `torch.randn(..., dtype=float32, generator=torch.manual_seed(seed), device="cpu")`. `--disable-all-custom-nodes`, `--whitelist-custom-nodes`, `--offline` flags exist. |
| RFC 8785 JCS — https://www.rfc-editor.org/rfc/rfc8785 | Informational RFC (June 2020). I-JSON input; ES6 number serialization; properties sorted by UTF-16 code units; no whitespace; UTF-8 output; NaN/Infinity and lone surrogates are errors. Python implementation: https://github.com/trailofbits/rfc8785.py (Apache-2.0, release v0.1.4). Reference implementations: https://github.com/cyberphone/json-canonicalization. |
| SLSA provenance v1 — https://slsa.dev/spec/v1.0/provenance | `predicateType: https://slsa.dev/provenance/v1`, in-toto Statement `_type: https://in-toto.io/Statement/v1`; `buildDefinition{buildType, externalParameters, internalParameters, resolvedDependencies[]}`, `runDetails{builder{id, version, builderDependencies}, metadata{invocationId, startedOn, finishedOn}, byproducts[]}`; ResourceDescriptor `{uri, digest{sha256,...}, name, downloadLocation, mediaType, annotations}`. Page notes v1.0 is retired in favour of v1.2. in-toto attestation: https://github.com/in-toto/attestation. |
| Real-ESRGAN — https://github.com/xinntao/Real-ESRGAN | Inference defaults to fp16 (`--fp32` opt-in); tiling "may cause block inconsistency". |
| Local host (`nvidia-smi`, 2026-11-27) | NVIDIA GeForce RTX 4070, 12282 MiB, driver 616.64. CUDA runtime/cuDNN/PyTorch not yet installed or inventoried for the project. |

## 3. Observed facts

1. No vendor or framework promises bit-identical GPU results across GPU architectures, SM counts, CUDA/cuBLAS toolkit versions, or PyTorch releases. The strongest documented guarantee (cuBLAS) is run-to-run on the same architecture + same SM count + same toolkit + single stream or fixed workspace.
2. Deterministic mode in PyTorch must be enforced with `warn_only=False`; ComfyUI's `--deterministic` does not do this.
3. Seed noise generated on the CPU in fp32 (ComfyUI default; diffusers with CPU Generator) removes one cross-device divergence source, but the denoising computation itself remains GPU-dependent.
4. fp16 inference is the default in common SR tooling (Real-ESRGAN). Reduced precision (fp16/bf16, TF32) increases sensitivity of results to kernel selection; disabling TF32 is part of diffusers' full-determinism helper.
5. JCS gives a standardised canonical byte form for JSON suitable for hashing; it requires that numbers be IEEE-754 doubles (so large integers > 2^53 and exact decimals must be avoided or encoded as strings).
6. SLSA/in-toto define a widely understood provenance vocabulary that can be reused for per-asset records without adopting the whole SLSA trust model.

## 4. Design: recipe resolution and precedence

Layers (highest wins), per plan §4:

1. `curated-override` — hand-written, in `SSTRE-Manifests/overrides/`.
2. `generated-recipe` — per-asset recipe produced (dev-time, possibly VLM-assisted) in `SSTRE-Manifests/generated/`.
3. `material-profile` — per class/material in `SSTRE-Manifests/materials/`.
4. `global-defaults` — `SSTRE-Manifests/defaults/`.

Proposed merge semantics (must be implemented identically by any tool; to be fixed by ADR):

- Deep merge of JSON objects, key by key, from lowest to highest layer.
- **Arrays replace, never concatenate** (e.g., `steps`), except where a step array is keyed by `stepId`, in which case steps merge by `stepId` and an explicit `"remove": true` removes a step. (Proposal; the simple "arrays replace" rule alone is acceptable if per-step override is not needed.)
- `null` in a higher layer deletes the key (JSON Merge Patch semantics, RFC 7396) — explicit deletion is recorded.
- The resolver records, for every leaf path, which layer supplied it (`precedence.fieldSources`, JSON Pointer → layer) and the content hash of each contributing layer file.
- The resolved recipe is validated against `asset-recipe.schema.json` after merge, then frozen: `resolvedRecipeHash = sha256(JCS(resolvedRecipe without its top-level "precedence" and "$comment" members))` (provenance of the merge is excluded so that identical effective configs from different layer arrangements share cache entries; layer hashes are recorded in the provenance record instead).
- Release builds consume only frozen resolved recipes (or re-resolve and must match the frozen hash; mismatch = build error).

## 5. Canonical serialization

- All hashed JSON documents are serialized with RFC 8785 JCS, UTF-8, then hashed with SHA-256. Hash strings are written as `sha256:<64 lowercase hex>`.
- Numeric policy: integers within ±2^53; floats only for values where IEEE-754 double round-trip is acceptable (denoise, strengths); where exact decimal semantics matter, encode as strings. Disallow NaN/Infinity (JCS forbids them).
- No Unicode normalization is performed by JCS; the resolver applies NFC to prompts *before* hashing and records that rule in the recipe format version.
- YAML may be used for authoring, but it is converted to JSON and hashed as JSON; YAML bytes are never hashed (avoids anchors/tags/float ambiguity).
- Paths inside recipes use forward slashes, are relative to a declared root, and are case-preserved; stable asset IDs, not paths, are the primary key.

## 6. Cache-key definition

The cache key for one pipeline step output is:

```
stepKey = sha256( JCS({
  "keyVersion": 1,
  "inputs":   [ <sha256 of each input artifact's bytes, in step-declared order> ],
  "step":     <the resolved step object from the recipe, JCS-canonical>,
  "models":   [ <sha256 of each model/weight file used by the step, by role> ],
  "code":     { "executor": <toolkit version + git commit>, "stepImpl": <sha256 of step implementation module or workflow JSON> },
  "runtime":  <runtime identity class: see below>,
  "target":   <target profile id + hash, only for steps whose output depends on it>
}) )
```

and the asset-level key is `assetKey = sha256(JCS({ "keyVersion":1, "assetId", "sourceHash", "resolvedRecipeHash", "stepKeys":[...], "targetProfileHash" }))`.

Rules:

- Keys chain: a step's `inputs` are the **output hashes** of upstream steps (not their keys), so a byte-identical upstream output (e.g., after an irrelevant recipe change) does not invalidate downstream work.
- `runtime` contains the **equivalence class**, not every detail: `{ "class": "ref-nvidia-ada-cu12.x-torch2.15-fp32-det" }` for steps proven bit-stable within that class; for steps not proven stable, the class is the full environment fingerprint (GPU name, SM count, driver, CUDA, cuDNN, torch, OS) so caches never mix outputs from unproven-equivalent environments. Classes are defined by the measurement in §8 and are versioned.
- Seed, sampler, scheduler, steps, denoise, precision, tiling, prompts and negative prompts are inside `step` — a seed alone is never the key.
- Excluded from keys: timestamps, host names, absolute paths, log verbosity, worker count (unless shown to affect output), cache location.
- Cache storage: content-addressed blobs `cas/sha256/ab/cdef…`, plus an index `stepKey → outputHash(es)`. Writes are atomic (write to temp, fsync, rename).

## 7. Incremental invalidation and resume

- The build planner computes `stepKey` for every step of every asset top-down; any step whose key exists in the index with a present, hash-verified blob is skipped.
- Changing a material profile changes `resolvedRecipeHash` only for assets whose effective configuration changed (field-level resolution), so only those assets are rebuilt.
- Model update → new model hash → only steps using that model are invalidated.
- Resume: each completed step is committed to the index immediately; an interrupted build restarts by re-planning (no separate journal needed beyond an optional "in-progress" marker for diagnostics). Partially written blobs are never visible (atomic rename).
- Per-asset failure isolation: a failing step records a provenance record with `status: "failed"` and the fallback decision; the batch continues (plan Phase 4 gate "does not stall").
- Garbage collection: mark-and-sweep from the current lock manifest plus N retained previous locks.

## 8. Determinism experiment design (Phase 3)

### 8.1 Variables

| Factor | Levels |
|---|---|
| Pipeline | SR feed-forward (e.g., Real-ESRGAN via spandrel); SR transformer (SwinIR/HAT); SDXL + tile ControlNet (non-ancestral Euler, 20 steps); SDXL with ancestral/SDE sampler; PBR classical (CPU); PBR ML; VLM classification (greedy) |
| Precision | fp32 (TF32 off); fp16; bf16; fp32 with TF32 on |
| Determinism settings | D0 default (`cudnn.benchmark` default, no flags); D1 `use_deterministic_algorithms(True, warn_only=False)`, `cudnn.benchmark=False`, `cudnn.deterministic=True`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, TF32 off; D1 + forced math SDPA backend |
| Execution | same process ×3; fresh process ×3; after reboot ×1 |
| Tiling | whole image vs tiled (if VRAM allows both) |
| Environment | E-ref (reference); E-driver (same GPU, different driver); E-torch (same GPU, different PyTorch minor); E-gpu2 (different NVIDIA architecture); E-cpu (CPU-only for SR/PBR); optional AMD/ROCm or DirectML |

### 8.2 Measurements per output pair

- SHA-256 of the encoded output and of the raw decoded pixel buffer (separates encoder nondeterminism from compute).
- Max absolute pixel difference (8-bit and float), count of differing pixels, PSNR, SSIM, LPIPS v0.1 (alex), DISTS.
- For downstream compressed outputs (BCn/ASTC, RD-005): hash of compressed bytes, and the same metrics after decode.
- Runtime and peak VRAM per determinism setting (cost of determinism).

### 8.3 Tolerance classes (proposed; numbers are fixed only after measurement)

| Class | Definition | Where it may be claimed |
|---|---|---|
| T0 bit-exact | Identical SHA-256 of decoded pixels and of final files | Only for (pipeline, environment) pairs where ≥ 10/10 repeated runs and fresh processes matched |
| T1 numerically equivalent | Max abs diff ≤ 1 LSB (8-bit) on ≤ X% of pixels, PSNR ≥ P1 | Set X, P1 from observed E-ref run-to-run spread under D0, then require cross-env diffs to be within k× (proposed k=2) the worst observed same-env spread |
| T2 perceptually equivalent | LPIPS ≤ L2 and DISTS ≤ S2 and all RD-003 QA gates still pass identically (same pass/fail and same fallback decision) | Diffusion outputs across GPUs; L2/S2 set as the p99 of same-config run-to-run deltas plus margin, validated by blind human A/B showing no reliable preference |
| T3 not equivalent | Anything else | Environment not supported for that pipeline, or pipeline restricted to SR-only there |

Key acceptance rule: **gate decisions must be equivalent** — an output in another environment must not flip a QA pass/fail or fallback choice relative to the reference, or the build is reported as diverged for that asset.

### 8.4 Success criteria for the experiment

- Report for every (pipeline × precision × setting × environment) cell its tolerance class, with raw numbers committed as a non-restricted metrics table (asset IDs and hashes only).
- Reference build: a second clean rebuild on E-ref yields T0 for all SR-only and classical steps, or the exceptions are documented with root cause.
- Measured cost of D1 versus D0 recorded; if D1 cost is unacceptable, document which steps run in D0 and their class.
- Incremental test: modify one material profile → only affected assets rebuild (counted), and unchanged assets keep identical output hashes.
- Resume test: kill the build at a random point 3 times → final lock identical to an uninterrupted build.

## 9. Reference-environment definition (template)

To be filled by measurement; recorded as part of build provenance (`environment` object) and as a versioned file in SSTRE umbrella (e.g., `docs/reference-environments/ref-01.json`, proposal).

```yaml
referenceEnvironmentId: ref-01            # stable id, versioned
status: proposal                           # proposal | measured | retired
hardware:
  gpu: {vendor: NVIDIA, name: TBD, computeCapability: TBD, smCount: TBD, vramMiB: TBD}
  cpu: {model: TBD, isa: x86_64}
  ramGiB: TBD
software:
  os: {name: TBD, build: TBD}
  gpuDriver: TBD
  cudaRuntime: TBD
  cudnn: TBD
  cublas: TBD
  python: TBD
  packages:                               # exact versions from lockfile; lockfile hash below
    torch: TBD
    diffusers: TBD
    spandrel: TBD
  lockfileHash: sha256:TBD                 # e.g., uv/pip-tools lock with hashes
  containerDigest: null                    # sha256 image digest if containerised
settings:
  env: {CUBLAS_WORKSPACE_CONFIG: ":4096:8", PYTHONHASHSEED: "0"}
  torch: {deterministicAlgorithms: true, warnOnly: false, cudnnBenchmark: false, cudnnDeterministic: true, allowTF32: false, sdpaBackend: math}
  rngDevice: cpu
equivalenceClasses:                        # filled from §8 measurements
  - pipeline: sr-feedforward-fp32
    class: T0                              # measured, not assumed
    evidence: <path to metrics table + commit>
```

Candidate first reference host: the local RTX 4070 (12282 MiB, driver 616.64 observed 2026-11-27); this is a candidate only.

## 10. Model and dependency integrity

- Models are referenced by **content hash (SHA-256 of file bytes)**, with optional source URL and pinned revision (e.g., Hugging Face commit SHA) as metadata. Mutable aliases (`main`, `latest`, model names) are never resolved in release builds.
- Download → verify SHA-256 → store in content-addressed model cache → record license id and license-text hash.
- Prefer `.safetensors`; refuse pickle (`.pth/.ckpt`) loading in release mode unless loaded with `torch.load(weights_only=True)` and explicitly allow-listed by hash (pickle can execute code).
- Python dependencies locked with hashes (pip `--require-hashes` or equivalent lock tool); lockfile hash recorded.
- ComfyUI (dev only): pin core by commit, pin each custom node by git commit, review before use, run with `--disable-all-custom-nodes --whitelist-custom-nodes <reviewed>` and `--offline`; record workflow (API-format JSON) by JCS hash. Never auto-install nodes from Manager in build contexts.

## 11. Provenance recording

Per-asset build output records follow `build-provenance.schema.json` (proposal), modelled on SLSA v1 / in-toto concepts but not claiming SLSA compliance:

- `subject` ≈ output artifacts with digests;
- `inputs` ≈ resolvedDependencies (source asset, models, recipe layers);
- `resolvedRecipeHash` ≈ externalParameters digest;
- `environment` ≈ builder + internalParameters;
- plus SSTRE-specific QA results, tolerance class claimed, fallback decision, timing.

A build-level lock manifest = sorted list of `{assetId, assetKey, outputHashes, provenanceHash}`, JCS-hashed; two builds are "identical" iff lock hashes match, "equivalent" iff every asset is within its declared tolerance class (§8.3). Signing (in-toto/Sigstore) is a later option, not Phase 0/3 scope.

## 12. Assumptions and unknowns

- Actual tolerance numbers: unknown until §8 runs.
- Whether image encoders (PNG zlib level/filters, EXR compression) and GPU texture compressors are deterministic across versions: to measure; pin encoder versions and settings.
- Whether non-NVIDIA user GPUs (AMD, Intel) are in scope: owner decision.
- Whether PyTorch deterministic mode supports all ops in the chosen SR/diffusion models (some may raise): to test with `warn_only=False`.
- Performance cost of deterministic settings and math SDPA on 12 GB VRAM: unknown.

## 13. Alternatives and tradeoffs

| Topic | Alternative | Tradeoff |
|---|---|---|
| Canonical JSON | RFC 8785 JCS (proposed) vs "sorted keys + compact" ad hoc | JCS has defined number/string rules and independent implementations; ad hoc differs across languages on floats/escaping |
| Hash | SHA-256 (proposed) vs BLAKE3 | SHA-256 ubiquitous, used by SLSA/HF/OCI; BLAKE3 faster but less tooling; allow multihash-style prefix for future change |
| Cache keying | Content-addressed per step (proposed) vs per-asset only | Per-step enables reuse of SR output across diffusion experiments; more index entries |
| Determinism target | Tolerance classes (proposed) vs bit-identity everywhere | Bit-identity across GPUs is not supported by vendors (§3) |
| Reproducibility vehicle | Locked venv + recorded env (proposed) vs container | Containers fix userland but not driver/GPU; Windows GPU containers are limited; record digest when used |
| Provenance | SLSA-inspired custom schema vs full in-toto attestations | Custom is simpler now; mapping to in-toto later is straightforward |

## 14. Risks

- Users' heterogeneous GPUs produce T2/T3 differences, causing support confusion → communicate tolerance classes; SR-only default.
- Deterministic mode errors on required ops → per-step exceptions recorded.
- Cache poisoning from mixing environments → runtime class in key; unproven envs get full fingerprint.
- Silent recipe drift from tool updates → executor version and step implementation hash in keys.
- Lock/manifest churn from float formatting → JCS + numeric policy.

## 15. Recommendation

1. Adopt RFC 8785 JCS + SHA-256 for all hashed manifests; YAML only as authoring sugar.
2. Adopt the step-level cache key in §6 with runtime equivalence classes derived from measurement.
3. Adopt the four-layer precedence with deep-merge/array-replace/null-delete semantics and per-field source recording; freeze resolved recipes for release.
4. Reference builds: D1 settings (`warn_only=False`, cuDNN benchmark off, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, TF32 off, CPU RNG, fp32 for SR); claim T0 only where measured.
5. Use tolerance classes T0–T3 and the "gate decisions must not flip" rule for cross-environment equivalence.
6. Provenance schema SLSA-inspired; signing deferred.

## 16. Decision dependencies

- RD-003 model/pipeline selection (which steps exist).
- RD-002 stable asset ID and source hash definitions.
- RD-005/RD-006 target profiles and compressors (affect `target` key part).
- RD-008 CI/acceptance gates and how tolerance tests run without game data (synthetic fixtures).
- Owner: supported GPU vendors; whether containers are used.

## 17. Next steps

1. Implement JCS hashing + recipe resolver prototype with tests on synthetic recipes (Remaster-Toolkit).
2. Install pinned PyTorch/CUDA stack on reference host; record environment per §9.
3. Run §8 experiment on synthetic + RD-002 matrix assets; publish metrics table; fill tolerance thresholds.
4. Write ADR for cache key / canonicalization / precedence once prototype passes incremental and resume tests.
