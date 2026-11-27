# EXP-015: Layered asset pipeline and platform texture profiles

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | Sprint 2 track A2 (assets); ADR-0009 consequences 1 and 3 |
| Status | complete (planning only; conversion/packaging of the planned outputs is not part of this experiment) |
| Environment | Windows 11 Pro 10.0.22631; Python 3.10.11 venv `G:\sstre-tmp\assets\venv` (jsonschema 4.26.0, referencing 0.37.0, pytest 9.2.0, reuse 5.0.2). CPU only; no GPU, no game window |
| Inputs | EXP-012 local outputs: 1376 source-selection records (`G:\sstre-tmp\assets\manifests\`) and texture set 1 (16 textures, `G:\sstre-tmp\assets\set1\READY.json`). No asset paths, hashes or images are published here (GATE-05) |
| Code | SSTRE-AssetCompiler branch `feature/asset-layers-profiles` (`layers.py`, `platform_profiles.py`, `jcs.py`, `docs/asset-layers.md`); umbrella branch `feature/build-config-schemas` (five schemas below + `schemas/tests/`) |

## Goal and success criteria

1. Implement [ADR-0009](../adr/0009-asset-layers.md): seven layers in a fixed order, the opt-in and approval gates, deterministic resolution and full per-asset provenance.
2. A frozen effective build manifest with RFC 8785 hashes; schemas with synthetic valid and invalid tests.
3. Declarative platform profiles (`pc-default`, `pc-low-memory`, a hypothetical `legacy-constrained`) that the planner applies and records.
4. A CLI and synthetic tests for every layer rule, gate, the ordering determinism, profile clamping and override precedence.
5. A local run on the EXP-012 data for three configurations, run twice.
6. The interface through which AI-track outputs enter layer 6.

## Design (what was built)

**Layers** (AssetCompiler `docs/asset-layers.md` has the full rules):

| # | Layer | Default | Gate implemented |
|---|---|---|---|
| 1 | Classic Base | on (cannot be disabled; schema `const`) | always the fallback |
| 2 | HD Quality Improvements | on | record result `hd` and the selected candidate verified |
| 3 | HD Material Maps | on | maps of the selected HD source, or M01 maps verified for the Classic albedo; filtered by the config roles and the platform profile; dropped when an override replaces the albedo (unless `keepMaps`) |
| 4 | HD Artwork | off | `hd_art_candidate`, category not `ui`; global opt-in **and** an approval for the exact candidate (optional hash pin; a changed file makes it stale) |
| 5 | HD Interface | off | the same for category `ui`, with its own opt-in. Optional `includeRelayout` offers the re-laid-out UI images of EXP-012 §5 (approval still required; `layoutChanged`, so no firstMip cap) |
| 6 | AI Enhancement | quality profile `off` | processes the source chosen by 1–5, never supplies one |
| 7 | Overrides | off | curated/community packs: `replace`, `use-classic`, `skip-ai` |

**Resolution.** The highest layer wins. Inside a layer, the higher explicit priority wins, then the smaller stable ID. Packs are ranked by priority, then curated before community, then `packId`. All inputs are sorted before use.

**Provenance per asset.** The plan records:

- the supplying layer and the deciding layer;
- the source kind, ID, file hash, decoded-image hash (when known) and size;
- the record ID and record hash, policy, result, rule and scores;
- the maps with their layer;
- the AI processing status, planned size and output;
- the status of all seven layers with a reason;
- the platform result: target size per texture, format per target, preprocessing steps, actions and an estimated size in bytes.

**Effective configuration.** The manifest freezes:

- layer switches and the quality-profile definition;
- the full platform profile and its hash;
- the approvals (embedded);
- packs by version and hash;
- the selection record set by hash, and the policies;
- the asset-facts hash.

Hashes are `sha256:` over RFC 8785 JCS:

- `effectiveConfigHash` = H(effectiveConfig);
- `planHash` = H({effectiveConfig, assets}).

Pins for approvals and packs are JCS hashes of the parsed document with its list in canonical order. Records are hashed without `generated_at`. The manifest has no timestamps.

**Platform profiles.** Each profile has size limits, targets (container, status, allowed formats, default format per role slot, mips), the mip policy, a memory budget and preprocessing.

- `pc-default` caps at ≤ 4096 per axis, short edge ≤ 2048 and ≤ 8 388 608 px. These are the EXP-012 limits: 2048×4096 loaded, 4096×4096 crashed.
  - Raster target: `.tex` v4 RGB8/RGBA8 (validated).
  - RT target: KTX2 BC7/BC5/BC4, RGBA8 allowed ("partial": reader validated in EXP-014, render test pending).
- `pc-low-memory`: 2048 px, 4 Mpx, 512 MiB with `reduce-largest`, BC1 for opaque colour on RT, normal maps only.
- `legacy-constrained` is **hypothetical**: invented round numbers, and its 16-bit, palettised, ASTC and ETC2 targets are `not-validated` placeholders. It contains no console or SDK information.

**Schemas (umbrella, all PROPOSAL).** They reuse existing definitions by `$ref`: `sha256` from `build-provenance`; category, record ID, result and rule ID from `source-selection`; the optional per-asset `provenance` is a `build-provenance` record.

- `build-config.schema.json`
- `build-manifest.schema.json`
- `platform-profile.schema.json`
- `layer-approvals.schema.json`
- `asset-pack.schema.json`: the layer-6 and layer-7 pack index

## Layer-6 interface for the AI track (AI1)

AI outputs are consumed only as an `asset-pack` with `kind: ai-enhancement` and a `qualityProfile`. Each entry needs these fields:

- `assetId`: the plan ID, not a set-local ID;
- `role`;
- `file`, `sha256` and `px` of the output;
- `input.sourceSha256`: the hash of the exact source processed, either the source file or the decoded mip-0 PNG (set 1 JSON `images[].sha256`);
- `recipeHash`: the `asset-recipe` resolvedRecipeHash;
- `qa.passed`;
- optionally `provenanceSha256` (the `build-provenance` record).

An entry is used only if all of these hold:

- the input hash equals the source the plan selected;
- the profile matches;
- QA passed;
- the aspect ratio is kept and the output is not smaller than the source.

Otherwise the asset stays `awaiting-output`, and the plan gives `processing.plannedPx`. That size is already clamped by the platform profile, the firstMip cap and the budget. [ASM] The AI1 run-A recipe files seen locally use a set-local `assetId` and the PNG hash as `source.hash`. They would match once the pack uses the plan's asset ID.

## Procedure (exact, reproducible)

1. Tests (synthetic only):
   - AssetCompiler: `python -m pytest -p no:cacheprovider`, with and without `SSTRE_SCHEMAS_DIR=<umbrella>/schemas`;
   - umbrella: `scripts/validate_repo.py --root .` and `--root <AssetCompiler>`;
   - `reuse lint` in each repository.
2. Synthetic approvals (`G:\sstre-tmp\assets\a2\make_approvals.py`). These are **not owner decisions**:
   - every `hd_art_candidate` is approved, except every 5th by sorted asset ID, which is rejected;
   - re-laid-out UI candidates with ≥ 4× pixels are approved.
   - Result: 338 entries, 308 approved.
3. Configurations in `G:\sstre-tmp\assets\a2\configs\`:
   - (a) defaults on `pc-default`;
   - (b) HD Artwork + HD Interface (`includeRelayout`) + synthetic approvals + `conservative` AI;
   - (c) defaults on `pc-low-memory`;
   - (c2) `standard` AI on `pc-low-memory`;
   - (c3) `standard` AI on `pc-default`, as a reference for c2.
4. `run_all.sh`: for each configuration, `sstre-ac validate-config`, then twice `sstre-ac plan --selection ../manifests --assets ../set1/READY.json` for all 1376 assets, and twice with `--only-listed` (set 1 only). `cmp` compares the outputs of run 1 and run 2.
5. `analyse.py` aggregates the results. It also re-resolves (b) in-process three times with the records, approvals and facts shuffled (seeds 0–2).

## Results ([EXP] unless labelled otherwise)

**Tests.**

- AssetCompiler: 167 passed with the schemas; 161 passed and 6 skipped without them.
- Umbrella `validate_repo.py`: 0 errors, 0 warnings, now including 18 valid and 60 invalid schema test documents. The new schemas contribute 10 valid and 25 invalid documents, plus synthetic examples inside each schema.
- REUSE compliant.
- Coverage was not measured (`coverage` is not installed).

**Supplying layer per run (1376 assets).**

| Run | Classic Base | HD Quality | HD Artwork | HD Interface | Overrides |
|---|---|---|---|---|---|
| (a) default | 1362 | 14 | 0 | 0 | 0 |
| (b) art + interface opt-in | 1054 | 14 | 119 | 189 | 0 |
| (c) pc-low-memory | 1362 | 14 | 0 | 0 | 0 |

- **(a).** HD Material Maps apply to 27 assets (46 maps). HD Artwork and HD Interface are `disabled` for 149 and 2 assets: these are the candidates that wait for an opt-in.
- **(b).** HD Artwork: 119 applied, 30 rejected by the synthetic list. HD Interface: 2 UI art plus 187 re-laid-out pages applied; 2 relayout candidates are awaiting approval. Classic Base is superseded for 322 assets. Maps apply to 33 assets.
  - Conservative AI: 890 awaiting output, 473 not eligible, 12 source already ≥ 2×, 1 platform-capped.
  - Estimated raster memory: 642 MB now, 1.59 GB once the AI outputs exist (2 GiB budget).
  - One HD Artwork source was reduced by the firstMip density cap.
- **(c).** No source exceeds 2048 px (the largest HD candidate is ≤ 2048), so the low-memory limits change nothing without AI. 20 assets get maps instead of 27, because the profile keeps normal maps only.
- **(c2) vs (c3), `standard` AI.**
  - Planned raster memory is 5.64 GB on `pc-default`. That profile only reports, so the plan is flagged over its 2 GiB budget.
  - On `pc-low-memory`, the budget reduced it from 5.61 GB to 536.5 MB (≤ 512 MiB) in 1554 deterministic halvings. 657 AI targets fell back to the source size (`platform-capped`, memory budget) and 480 remain to be produced. The largest planned size dropped from 2048² to 512².
  - One 1024-px texture was clamped by the limits on `pc-default` (×4 = 4096² → 2048²).

**Set 1 (16 textures, `--only-listed`).**

| Run | Layers | AI |
|---|---|---|
| (a) | Classic 15, HD Quality 1 (the prop, R08) | — |
| (b) | Classic 13, HD Quality 1, HD Artwork 1 (detail, capped from the HD-art size to 2^firstMip × Classic = 512²), HD Interface 1 (the Netricsa page, re-laid-out, 512²) | 7 awaiting, 7 not eligible (UI, font, technical, effect, plus the HD-sourced detail), 1 source-sufficient, 1 platform-capped (the firstMip-0 bump map) |
| (c2) | as (a) | 10 awaiting, with planned sizes up to 2048² (sky 2048×1024). Set 1 alone (80 MB) fits the budget, so it is not reduced. The firstMip-0 bump map is platform-capped. The firstMip-1 detail texture is capped from 1024² to 512² |

**Determinism.**

- Every plan file of run 1 is byte-identical to run 2: 10 of 10 pairs.
- 10 distinct `planHash` values, one per configuration and scope. For example:
  - (a) full `sha256:f2f49fa8fc2578b3…`;
  - (b) full `sha256:060f731a012ebda1…`;
  - (c) full `sha256:300b4593e7d5369a…`;
  - (c2) full `sha256:71e02fa54fd1fd8c…`.
- In-process shuffles of the records, approvals and facts (3 seeds) gave the same `planHash` as the CLI.
- A full plan takes about 1.3 s; the first cold read of the 1376 records took about 10 s.

## Deviations, modifications and failures

- **First determinism test failed.** It first failed on shuffled pack lists, because pins were byte hashes of the files. Fixed: pins and recorded hashes are now JCS hashes with lists in canonical order.
- **AI targets ignored the firstMip cap.** Planned AI targets first ignored the cap and were not counted by the budget, so `pc-low-memory` showed no effect. Fixed:
  - the planned size respects the cap and the profile;
  - the budget counts planned sizes and reduces them first;
  - a fully removed gain becomes `platform-capped`.
- **Misleading action fixed.** `below-classic-resolution` was reported for re-laid-out UI sources that are smaller on one axis. It is now reported only when the profile actually reduced the size.
- **Module renamed.** The module was renamed `platform_profiles.py` so that it does not shadow the standard-library `platform`.

## Interpretation

- [EXP] With the defaults, Classic remains the experience for 99 % of the assets (1362/1376). Only verified-superior HD (14) and verified maps (27) are added. Layers 4 and 5 change nothing without an opt-in and per-asset approvals.
- [EXP] The `standard` AI profile does not fit a 512 MiB raster budget on the EXP-012 asset set: about 58 % of the AI gains would be dropped. Memory-constrained targets therefore need a smaller quality profile or BCn raster upload. [ASM] Classic-VK may already compress uploads (EXP-012: `tex_bAlternateCompression` was not verified).
- [ASM] firstMip is not in the selection records. For the 1376 assets, the density cap is therefore applied only where asset facts exist. The full-set planned sizes are upper bounds.

## Impact on ADRs, dossiers and backlog

- **ADR-0009.** Implemented as specified. Two clarifications for the lead to fold in:
  - HD Interface is an independent opt-in; the HD Artwork opt-in never covers UI.
  - Re-laid-out UI is an optional part of layer 5 (`includeRelayout`, off by default).
- **RD-004.** JCS is implemented (`jcs.py`). The "list-order-canonical pin" rule is new.
- **Backlog.**
  - A converter step that executes the plan (`.tex` v4 / KTX2 writer).
  - firstMip in the selection records.
  - Map sizes from the HD plugin.
  - AI1 packs in the `asset-pack` format.

## Open questions

1. **Owner.** The default quality profile stays `off` (Classic as the default experience); `conservative` is opt-in. Is that the intended default for the vertical slice?
2. **Owner / RD-007.** Approvals and curated override lists reference HD asset IDs and encode artistic choices. They stay local until GATE-05 (see the EXP-012 open questions).
