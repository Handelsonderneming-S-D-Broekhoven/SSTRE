# ADR-0009: Independently configurable asset layers with deterministic ordering

- **Status:** accepted (owner decision, 2026-11-27)
- **Date:** 2026-11-27
- **Deciders:** project owner
- **Evidence:** [EXP-008 HD asset matching](../experiments/EXP-008-hd-asset-matching.md), [EXP-012 tex codec and source selection](../experiments/EXP-012-tex-codec-source-selection.md), [RD-002](../research/RD-002-hd-assets.md), [ADR-0002](0002-local-user-supplied-assets.md), [ADR-0003](0003-dev-release-separation-locked-recipes.md), [ADR-0004](0004-exception-driven-curation.md)

## Context

The Phase 1 and sprint 2 measurements found that most verified HD counterparts are lossy copies at the same resolution as Classic. A minority are genuine improvements: higher resolution, extra normal/gloss maps, or redrawn artwork. The owner requires that Classic art direction stays the default experience and that the pipeline supports partial HD coverage. Sources must be selected reproducibly, every decision must be recorded, and the build must be able to target future, memory-constrained platforms.

## Decision

The asset build composes **independently configurable layers**. Layers are applied in a fixed, documented order, and a later layer overrides an earlier one only for the assets it covers.

| Order | Layer | Default | Enabling rule |
|---|---|---|---|
| 1 | **Classic Base** | on | always present; the source of truth and the fallback for every asset |
| 2 | **HD Quality Improvements** | on | only for assets where the source selector verified that HD is superior: higher effective resolution and quality, no degraded or lossy copy, UV compatible, art direction preserved |
| 3 | **HD Material Maps** | on | HD normal/gloss/companion maps combined with the selected albedo, only where compatibility is verified |
| 4 | **HD Artwork** | **off** | genuinely different artwork; needs a **global opt-in and per-asset approval** |
| 5 | **HD Interface** | **off** | separate optional sublayer of HD Artwork for menus, HUD and Netricsa images; its own opt-in |
| 6 | **AI Enhancement** | per quality profile | processing of whichever source layers 1–5 selected, according to the chosen quality profile (for example `off`, `conservative`, `standard`) and the per-class recipe policy (RD-003) |
| 7 | **Community and Curated Overrides** | optional | highest applicable priority; curated per-asset overrides (ADR-0004) and opt-in community packs |

Rules:

1. **Determinism.** The order above is fixed. Within a layer, conflicts are resolved by explicit priority, then by stable asset ID. The same inputs and configuration always give the same selection.
2. **Provenance.** Each output records, per asset: the layer that supplied the source, the layer that processed it, the source asset ID and hash, the selection rule and scores (`schemas/source-selection.schema.json`), and the recipe and provenance (`asset-recipe`, `build-provenance` schemas).
3. **Effective configuration** is written into the build manifest: enabled layers, quality profile, platform profile, approvals, and override packs with versions and hashes. Release builds read only this frozen configuration (ADR-0003).
4. **Classic remains the default experience.** Layers 4 and 5 never activate implicitly, and layer 2 never replaces an asset with a degraded copy.
5. **Platform profiles** are independent of layers. They set the texture size limits, pixel and compression formats (for example BCn on PC; ASTC or palettised formats for other targets), mip policy, memory budgets and preprocessing steps, so that future console and legacy targets can be served from the same layer selection. The current PC profile caps textures at the experimentally validated maximum (≤ 2048×4096 / 8.4 Mpx) until the 4096×4096 crash is understood (EXP-012).
6. **Publication** is unchanged. Layer selections, approvals and records that reference proprietary assets stay local until GATE-05. The HD decoder stays local until its legal status is reviewed (RD-007 Q24–Q28).

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| A single "HD on or off" switch | conflates genuine improvements with degraded copies and with redrawn art |
| HD by default wherever a match exists | contradicts the measurements (mostly lossy copies) and the art-direction requirement |
| AI enhancement as a source layer | AI processes a selected source; making it a source would hide provenance |

## Consequences

- SSTRE-AssetCompiler implements layer configuration, selection and effective-configuration recording (sprint 2, track A2), plus platform profiles.
- The source selector (EXP-012) feeds layers 2–5. Its "HD-art queue" decisions populate layer 4 or 5 candidates awaiting approval.
- SSTRE-Manifests will hold layer configurations, approvals and curated overrides as data. Their publication is subject to GATE-05.

## Clarifications (2026-11-27, lead, from the EXP-015 implementation)

- **HD Interface** has its own global opt-in, independent of HD Artwork. Re-laid-out UI pages (different layout, not only higher resolution) are a further opt-in inside HD Interface (`includeRelayout`, default off). Each still needs per-asset approval.
- **Default AI quality profile:** the tool default is `off`, so a build with no configuration gives the Classic experience. The vertical-slice configuration uses `conservative`: deterministic super-resolution, no generative steps. Generative refinement stays an explicit opt-in experiment.
- **Memory budgets** are part of the platform profile. EXP-015 measured that the `standard` AI profile needs about 5.6 GB of raster texture memory for TFE, against the 2 GiB `pc-default` budget, so profiles must prioritise which assets receive the planned upscale.
