# SSTRE compatibility matrix

> **Template. Nothing has been tested.** Every cell is `untested`. SSTRE has no release and makes no compatibility promise. Testing method: [RD-008](./research/RD-008-testing-release.md).

## Status vocabulary

| Status | Meaning | Required evidence |
|---|---|---|
| `untested` | No test report exists. Default. | none |
| `known-broken` | Tested; fails to install, build, launch, or complete the test protocol. | Linked report with failure description |
| `works-with-issues` | Completes the test protocol with documented defects (visual, performance, audio, stability) | Linked report + issue links |
| `verified` | Completes the full test protocol for the pinned versions below with no open blocking issues | Linked report: tester, date, hardware, driver, OS build, all pinned versions |

Rules:

- A cell changes only via a PR linking a test report. Status applies only to the exact pinned versions listed for that release; a new release resets affected cells to `untested` unless re-tested.
- Reports contain numbers, hashes and text only — no screenshots or other game-derived content in the repository.
- Users supply their own legally acquired game data. Editions not listed are unsupported, not "probably fine".

## Pinned versions for this matrix

| Component | Version / commit |
|---|---|
| SSTRE umbrella release | none (no release yet) |
| SSTRE-Engine | TBD |
| SSTRE-AssetCompiler | TBD |
| SSTRE-Manifests | TBD |
| Remaster-Toolkit | TBD |
| Asset build profile + output-hash manifest | TBD |
| Model/workflow set | TBD |

## Game data editions (runtime target)

Edition identification will be by top-level archive SHA-256 (see RD-002). Rows below are placeholders for editions to investigate; hashes are TBD.

| Game | Store | Edition identifier (hash set) | Detection | Extraction | Runtime |
|---|---|---|---|---|---|
| TFE Classic | Steam | TBD | untested | untested | untested |
| TFE Classic | GOG | TBD | untested | untested | untested |
| TSE Classic | Steam | TBD | untested | untested | untested |
| TSE Classic | GOG | TBD | untested | untested | untested |

## HD asset sources (texture/material source only, not runtime)

| Game | Store | Edition identifier | Detection | Extraction | Mapping to Classic |
|---|---|---|---|---|---|
| TFE HD | Steam | TBD | untested | untested | untested |
| TSE HD | Steam | TBD | untested | untested | untested |
| Fusion 2017 content | Steam | TBD | untested | untested | untested |

## Runtime matrix

Backends are candidates pending ADR-005/ADR-007; columns may change. "RT" = ray-traced backend (RTGL1/Vulkan candidate), "VK raster" = Vulkan rasterization, "GL" = legacy OpenGL.

### NVIDIA GPU

| Game × Store | Windows 10/11 x64 · RT | Windows · VK raster | Windows · GL | Linux x86_64 · RT | Linux · VK raster | Linux · GL |
|---|---|---|---|---|---|---|
| TFE Classic · Steam | untested | untested | untested | untested | untested | untested |
| TFE Classic · GOG | untested | untested | untested | untested | untested | untested |
| TSE Classic · Steam | untested | untested | untested | untested | untested | untested |
| TSE Classic · GOG | untested | untested | untested | untested | untested | untested |

### AMD GPU

| Game × Store | Windows 10/11 x64 · RT | Windows · VK raster | Windows · GL | Linux x86_64 · RT | Linux · VK raster | Linux · GL |
|---|---|---|---|---|---|---|
| TFE Classic · Steam | untested | untested | untested | untested | untested | untested |
| TFE Classic · GOG | untested | untested | untested | untested | untested | untested |
| TSE Classic · Steam | untested | untested | untested | untested | untested | untested |
| TSE Classic · GOG | untested | untested | untested | untested | untested | untested |

### Intel GPU

| Game × Store | Windows 10/11 x64 · RT | Windows · VK raster | Windows · GL | Linux x86_64 · RT | Linux · VK raster | Linux · GL |
|---|---|---|---|---|---|---|
| TFE Classic · Steam | untested | untested | untested | untested | untested | untested |
| TFE Classic · GOG | untested | untested | untested | untested | untested | untested |
| TSE Classic · Steam | untested | untested | untested | untested | untested | untested |
| TSE Classic · GOG | untested | untested | untested | untested | untested | untested |

## User-side builder (host)

| Host OS | GPU vendor | Builder install | Full asset build | Reproduces reference hashes | Equivalence within tolerance |
|---|---|---|---|---|---|
| Windows 10/11 x64 | NVIDIA | untested | untested | untested | untested |
| Windows 10/11 x64 | AMD | untested | untested | untested | untested |
| Windows 10/11 x64 | Intel | untested | untested | untested | untested |
| Linux x86_64 | NVIDIA | untested | untested | untested | untested |
| Linux x86_64 | AMD | untested | untested | untested | untested |
| Linux x86_64 | Intel | untested | untested | untested | untested |

## Feature compatibility

| Feature | Status |
|---|---|
| Classic savegames load in SSTRE | untested |
| Classic-recorded demos play in SSTRE | untested |
| Co-op LAN (same SSTRE version) | untested |
| Co-op with original Classic clients | untested |
| Split-screen | untested |

## Report template (for a cell change)

```text
Cell(s):            <table / row / column>
New status:         known-broken | works-with-issues | verified
Tester / date:
Pinned versions:    umbrella, engine, assetcompiler, manifests, toolkit, build profile hash
Game edition hash:  <from detector>
Hardware:           CPU, GPU, VRAM, RAM
Driver / OS build:
Protocol:           RD-008 §8 demo set + results (p50/p99 frame time, peak VRAM, end-state match)
Issues:             <links>
```
