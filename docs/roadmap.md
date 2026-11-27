# Roadmap

**Current phase: 1, technical validation** (Phase 0 reviewed by the owner on 2026-11-27). No calendar or budget is approved. Effort is estimated only after the first proof-of-concept sprint (see [backlog](backlog.md)).

| Phase | Objective | Exit gate | Status |
|---|---|---|---|
| 0 | Bootstrap and evidence-based research | Five repository roles documented; license boundaries reviewed; dossiers, ADRs and POC backlog available | done (owner-reviewed 2026-11-27) |
| 1 | Engine baseline | Selected engine builds and launches TFE on the reference PC; gameplay and performance baseline captured; TSE support assessed | in progress: builds and TFE/TSE launch **done**; performance baseline **open** (see backlog Phase 1 status) |
| 2 | Asset extraction and mapping | Representative Classic and HD assets extracted locally, mapped, and either round-tripped or with fallback documented | not started |
| 3 | AI toolkit prototype | 50 representative textures processed; deterministic reruns measured; QA, provenance and caching demonstrated | not started |
| 4 | First full texture build | Required assets covered with explicit fallback; high-priority and problem textures reviewed; full build does not stall on individual failures | not started |
| 5 | PBR integration | Coherent maps and correct material behavior shown in the engine on representative surfaces | not started |
| 6 | Rendering and TSE compatibility | Both campaigns supported with the selected rendering path; ray tracing and raster fallback handled according to approved ADRs | not started |
| 7 | PC alpha | Full campaign playtests, co-op/multiplayer regression where applicable, performance and memory profiles; user-side builder tested | not started |
| 8 | Console feasibility and ports | Only platforms with viable authorized toolchains, runtime support and a distribution path progress to port implementation | not started |
| 9 | Public stable release | Pinned multi-repo release, validated local build instructions, documented compatibility, notices and issue reporting | not started |

Notes:

- Phases 1–3 may overlap once Phase 0 is approved. A rendering or TSE spike may be needed early to validate the engine choice.
- Console work is optional and must not block a viable PC release. Xbox Series X|S, PS5 and Switch/Switch 2 are research targets, not promised ports. PS Vita is low priority. See [RD-006](research/RD-006-platforms.md).
- Future games are outside the current delivery scope.
- Detailed, measurable gate criteria are proposed in [RD-008](research/RD-008-testing-release.md).
