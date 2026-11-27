# ADR-0003: Separate development-time AI assistance from release builds; release builds run frozen, locked recipes

- **Status:** accepted
- **Date:** 2026-11-27
- **Deciders:** project owner (project plan v0.1 §3, §4), lead architect
- **Evidence:** [RD-003 AI pipeline](../research/RD-003-ai-pipeline.md), [RD-004 reproducibility](../research/RD-004-reproducibility.md)

## Context

Vision-language models and diffusion workflows help classify textures and propose processing recipes. They are also nondeterministic, change over time behind mutable aliases, and may be unavailable or costly. Users must be able to rebuild the remaster locally, years later, without a live AI service.

## Decision

1. **Development mode** may use a vision LLM to classify assets, draft prompts and propose recipes. It may also generate and score multiple candidates and capture curation decisions. Its outputs are *proposals* committed to SSTRE-Manifests after review.
2. **Release mode** executes only frozen, fully resolved recipes. It has no live LLM, no external AI API, no prompt generation and no mutable model alias. Every model, checkpoint, VAE, conditioning model and custom node is referenced by content hash, and downloads are verified against those hashes.
3. Recipe precedence: **curated override > generated per-asset recipe > material profile > global defaults**. The effective, resolved recipe for each asset is frozen into a lock manifest for each release.
4. Cache keys are content-addressed over input bytes, the canonicalized resolved recipe, dependency and workflow identity, runtime and target profile. A seed alone is never a sufficient key.
5. Bit-identical output is claimed only for a documented reference environment once demonstrated. Other environments are held to documented equivalence thresholds (see RD-004).

## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| Live LLM in the user builder | Violates the requirement for no external AI in release; not reproducible |
| Ship prompts only, resolve models at build time via "latest" | Mutable aliases break reproducibility and auditability |

## Consequences

- Manifests need schemas for recipes and provenance (proposals: `schemas/asset-recipe.schema.json`, `schemas/build-provenance.schema.json`).
- Model-weight licensing becomes a release concern: weights the user must download need licenses that allow the intended use (RD-007).
- Toolkit implementation details (ComfyUI or a headless alternative) stay open; this ADR constrains only *behavior*.
