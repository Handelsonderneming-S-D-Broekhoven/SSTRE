# SSTRE — Serious Sam: The Raytraced Encounter

An **unofficial**, open-source modernization project for *Serious Sam: The First Encounter* (TFE) and *The Second Encounter* (TSE). It aims to keep the original campaigns, gameplay and art direction, and to add ray/path tracing, PBR materials and AI-assisted texture reconstruction built locally from the player's own copy of the game.

> **Status: Phase 1 — technical validation (started 2026-11-27).** Nothing is playable from this project yet. The engine direction is provisional, no asset pipeline exists, and no platform is supported. This repository holds documentation, research, proposed architecture decisions and cross-repo contract proposals.
>
> SSTRE is not affiliated with, endorsed by or connected to Croteam or Devolver Digital. *Serious Sam* is a trademark of its respective owner. You need your own legally acquired copy of the game. This project never distributes game assets or derivatives of them.

## What this repository is

The umbrella repository coordinates the project. It owns:

- documentation, [roadmap](docs/roadmap.md), [backlog](docs/backlog.md) and [compatibility matrix](docs/compatibility.md),
- [architecture decision records](docs/adr/) and [research dossiers](docs/research/),
- cross-repository contract proposals in [`schemas/`](schemas/),
- eventually: pinned multi-repository releases and the user-side builder that turns a local game installation into a remastered build.

## Non-goals (currently)

- Distributing original or remastered game assets, screenshots of restricted content, or model weights.
- Changing gameplay, levels or enemy behavior by default.
- Console ports. Xbox, PlayStation and Switch are research targets only and are blocked without a rights-holder license ([RD-006](docs/research/RD-006-platforms.md)).
- Future games beyond TFE/TSE.
- Requiring a live LLM or AI service in release builds.

## Repositories

| Repository | Role |
|---|---|
| [SSTRE](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE) | this umbrella |
| [SSTRE-Engine](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-Engine) | engine fork (Serious Engine 1 lineage), rendering, runtime, platform ports |
| [SSTRE-AssetCompiler](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-AssetCompiler) | Serious Sam-specific asset discovery, extraction, mapping, conversion, packaging |
| [SSTRE-Manifests](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE-Manifests) | declarative recipes, mappings, locks and curated overrides |
| [Remaster-Toolkit](https://github.com/Handelsonderneming-S-D-Broekhoven/Remaster-Toolkit) | game-agnostic texture/material processing, QA and caching |

See the [repository registry](docs/repository-registry.md), the [architecture overview](docs/architecture/overview.md) and the [cross-repo contracts](docs/architecture/cross-repo-contracts.md).

## Fixed requirements vs. open decisions

The binding requirements are listed in the [project plan](docs/project-plan.md) §3 and summarized in the [architecture overview](docs/architecture/overview.md). Technology choices are **not** final until their ADR is accepted:

| ADR | Topic | Status |
|---|---|---|
| [0001](docs/adr/0001-repository-separation.md) | Repository separation | accepted |
| [0002](docs/adr/0002-local-user-supplied-assets.md) | Local, user-supplied game data | accepted (project policy, not legal clearance) |
| [0003](docs/adr/0003-dev-release-separation-locked-recipes.md) | Dev/release separation, locked recipes | accepted |
| [0004](docs/adr/0004-exception-driven-curation.md) | Exception-driven curation | accepted |
| [0005](docs/adr/0005-engine-foundation.md) | Engine foundation (Classic-VK main line + RT backend) | accepted as **provisional** direction; final selection after Phase 1 validation |
| [0006](docs/adr/0006-licensing-boundaries.md) | Licensing boundaries | accepted (policy, not legal clearance) |
| [0007](docs/adr/0007-platform-strategy.md) | Platform strategy | PC-first, Windows + Linux, raster baseline with optional RT accepted; consoles research only |

## Prerequisites

| Area | Known | To be decided |
|---|---|---|
| Docs and schema checks | Python 3.10+, `jsonschema` 4.26.0 | — |
| Engine build | Windows x64 with MSVC (upstream solutions); CMake on Linux for Classic-VK | exact toolchain, Vulkan SDK version (Phase 1, POC-01/02) |
| Game data | a user-owned Classic TFE/TSE install; HD editions optional as a texture source | supported editions and hashes ([RD-002](docs/research/RD-002-hd-assets.md)) |
| Asset pipeline | — | models, runtime and GPU requirements ([RD-003](docs/research/RD-003-ai-pipeline.md)) |

## Working with this repository today

The only working development task is validating the documentation and schemas:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate    POSIX: . .venv/bin/activate
python -m pip install "jsonschema==4.26.0"
python scripts/validate_repo.py
```

This checks the JSON Schemas against draft 2020-12, relative Markdown links, and that no game data or model weights are committed. CI runs the same script.

## Licensing

Copyright © 2026 Handelsonderneming S.D. Broekhoven, trading as ITEagle Europe, and contributors.

- This repository: `GPL-3.0-only` ([`LICENSE`](LICENSE), machine-readable in [`REUSE.toml`](REUSE.toml)).
- SSTRE-AssetCompiler and Remaster-Toolkit: `GPL-3.0-only`. SSTRE-Manifests: `CC0-1.0` for factual metadata and `CC-BY-SA-4.0` for creative recipes and curated configuration.
- SSTRE-Engine keeps its upstream `GPL-2.0-only` license and is never relicensed. The engine and the GPLv3 tools communicate only through files and CLIs, in separate processes ([ADR-0006](docs/adr/0006-licensing-boundaries.md)).
- No engine binaries are distributed until the identified licensing blockers are resolved ([RD-007](docs/research/RD-007-licensing.md)).
- Contributions use the Developer Certificate of Origin (`git commit -s`). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the [notices policy](docs/policies/notices-policy.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) first, especially the no-game-data rule. Report security issues privately as described in [SECURITY.md](SECURITY.md).
