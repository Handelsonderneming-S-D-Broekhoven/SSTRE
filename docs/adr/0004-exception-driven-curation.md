# ADR-0004: Automated bulk processing by default; human curation only for prominent assets and exceptions

- **Status:** accepted
- **Date:** 2026-11-27
- **Deciders:** project owner (project plan v0.1 §3), lead architect
- **Evidence:** [RD-003 AI pipeline](../research/RD-003-ai-pipeline.md), [RD-008 testing and release](../research/RD-008-testing-release.md)

## Context

TFE and TSE contain thousands of textures. Manual per-asset work does not scale, and blindly running every texture through generative models risks damaging art direction, technical textures, text and HUD elements.

## Decision

1. Every asset goes through an automated pipeline. The pipeline classifies the asset, applies the resolved recipe, runs automated QA, and falls back conservatively (controlled diffusion → super-resolution only → original asset).
2. Human curation is reserved for (a) prominent assets on a curated priority list and (b) assets that fail QA or are flagged ambiguous. Curation outcomes become *curated overrides* in SSTRE-Manifests.
3. The target is **95% or more automated acceptance**. This is an aspirational metric, not a proven result. It is measured against a defined denominator with human audit sampling (defined in RD-008), and progress is reported honestly, including fallbacks.
4. A full build must never stall on a single asset failure. Failures are recorded and the fallback is used.

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Manual curation of every asset | Does not scale; slows reproducible rebuilds |
| Fully automated, no curation | Prominent assets and edge cases (fonts, HUD, masks) are likely to need review |

## Consequences

- QA metrics (SSIM, LPIPS and similar) are calibrated against human judgment on the 50-asset test matrix before thresholds are trusted.
- Curation tooling is a later toolkit feature. Phase 0–3 use simple file-based review.
