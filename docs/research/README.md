# Research dossiers

Canonical Phase 0 research dossiers. Each one follows the format in the [project plan](../project-plan.md) §6. It separates observed facts, with sources, from assumptions, and ends with a recommendation, the decisions it depends on, and next steps. A dossier is evidence for a decision, not the decision itself. Decisions are recorded in [ADRs](../adr/).

| ID | Topic | Feeds |
|---|---|---|
| [RD-001](RD-001-engine-baseline.md) | Engine baseline: comparison of the RT, official, Vulkan and Classic(-VK) forks | ADR-0005 |
| [RD-002](RD-002-hd-assets.md) | Classic/HD asset formats, edition fingerprints, mapping feasibility, 50-asset test matrix | inventory schema, POC backlog |
| [RD-003](RD-003-ai-pipeline.md) | AI models and workflows, per-class processing policy, benchmark plan | recipe schema, toolkit POC |
| [RD-004](RD-004-reproducibility.md) | Determinism, cache keys, recipe resolution, reference environment | ADR-0003 follow-up, provenance schema |
| [RD-005](RD-005-rendering.md) | RayTracedGL1, raster fallback, PBR data path, TSE rendering | ADR-0005, ADR-0007 |
| [RD-006](RD-006-platforms.md) | Windows/Linux and console feasibility | ADR-0007 |
| [RD-007](RD-007-licensing.md) | Licenses, GPL compatibility, asset/model terms, trademarks | ADR-0006 |
| [RD-008](RD-008-testing-release.md) | Acceptance gates, QA, regression, release matrix | backlog, compatibility matrix |

Status vocabulary: **draft** (written, not reviewed) → **reviewed** (lead-reviewed) → **superseded**.
