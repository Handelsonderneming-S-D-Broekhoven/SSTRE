# Research dossiers

Canonical research dossiers: RD-001..008 from Phase 0, RD-009..014 added on 2026-11-28 for the post-demonstration stages ([roadmap](../roadmap.md)), RD-015 added on 2026-11-28 for pre-hardware Steam Deck testing, RD-016..018 added on 2026-11-28 (evening) for stage M0.1 Rendering Correctness & Legacy Visual Modernization. Each one follows the format in the [project plan](../project-plan.md) §6. It separates observed facts, with sources, from assumptions, and ends with a recommendation, the decisions it depends on, and next steps. A dossier is evidence for a decision, not the decision itself. Decisions are recorded in [ADRs](../adr/).

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
| [RD-009](RD-009-ps5-homebrew.md) | Native PlayStation 5 homebrew port (research only, not pursued) | ADR-0007 review, backlog M6 |
| [RD-010](RD-010-homebrew-distribution.md) | Homebrew distribution: what may be distributed, channels, console homebrew out of scope | ADR-0007 review, RD-008 §11 |
| [RD-011](RD-011-hex-tiling.md) | Realtime, baked and hybrid hex-tiling (Mikkelsen), as a generic RTGL1 feature | backlog M2, proposed material-contract ADR |
| [RD-012](RD-012-input-local-multiplayer.md) | Modern input architecture (SDL3), Steam Input/Deck, local multiplayer and split-screen | backlog M4/M5, proposed input ADR |
| [RD-013](RD-013-geometry-enhancement.md) | Geometry enhancement: capture survey, normal smoothing, terminator fix, subdivision for brushes and models (M3, before M2 per issue #22), displacement as M2 follow-up | backlog M3 (POC-94, POC-54..56), POC-95, proposed render-only-geometry ADR |
| [RD-014](RD-014-rt-performance.md) | RT and engine performance: measurement design, profiling tools, hypotheses, stop rule | backlog M1, proposed performance-target ADR |
| [RD-015](RD-015-steam-deck-pre-hardware-testing.md) | Steam Deck testing before hardware: emulation and approximation options, what only hardware can validate | ADR-0007 Tier 2, backlog POC-64..74 |
| [RD-016](RD-016-legacy-lighting-reconstruction.md) | Universal legacy lighting reconstruction in RT: lost and wrongly converted light contributions, native conversion, legacy ambient, lightmap-assisted compensation, probes (draft) | proposed ADR-0015, backlog POC-75..79 |
| [RD-017](RD-017-legacy-effects-reconstruction.md) | Legacy atmospheric, translucent and particle effects: translucent light volumes, lightning and special effects, particles, effect-texture recipes (draft) | proposed ADR-0016, backlog POC-80..85 |
| [RD-018](RD-018-menu-ui-modernization.md) | Menu asset enhancement and responsive, resolution-independent UI; MSDF font track per issue #21; controller-ready focus (draft) | proposed ADR-0017, backlog POC-86..88 |

Status vocabulary: **draft** (written, not reviewed) → **reviewed** (lead-reviewed) → **superseded**.
