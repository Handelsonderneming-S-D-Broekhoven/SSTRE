# ADR-0006: Licensing boundaries between repositories

- **Status:** proposed, pending owner confirmation and review of the open questions by counsel. This ADR is **not** legal clearance.
- **Date:** 2026-11-27
- **Deciders:** project owner; lead architect proposes
- **Evidence:** [RD-007 licensing](../research/RD-007-licensing.md), [notices policy (draft)](../policies/notices-policy.md), [RD-001](../research/RD-001-engine-baseline.md), [RD-005](../research/RD-005-rendering.md)

## Context

The Phase 0 audit (RD-007) observed the following:

- Every engine candidate ships the unmodified GPLv2 text. The operative grant in the file headers is "version 2 of the GNU General Public License" with no "or any later version". The engine is therefore treated as **GPL-2.0-only**.
- GPL-2.0-only and GPL-3.0 code cannot be combined into one derivative work. Communication between separate programs through files and command-line interfaces is generally treated as aggregation (FSF GPL FAQ). Whether that holds depends on the actual coupling.
- The engine repos also contain non-GPL material:
  - zlib and libogg/libvorbis (permissive),
  - LightWave SDK headers with no license terms,
  - a Microsoft `DSOUND.H` "All Rights Reserved" header,
  - checked-in `Bison.exe`/`Flex.exe`,
  - `SE1_10.gro` game data with no license stated,
  - TFE `Entities` sources in the RT/Vk line with no headers and uncertain provenance.
- RayTracedGL1 is MIT. It compiles in Apache-2.0 KTX code, which the FSF considers incompatible with GPLv2, and it can optionally link NVIDIA DLSS, whose SDK license forbids making it subject to an open-source license.
- None of the five SSTRE repositories has a license today.
- The Classic game license forbids distributing the game and preparing derivative works. No HD/Fusion EULA could be retrieved.

## Decision (proposed)

| Repository | Proposed license | Notes |
|---|---|---|
| SSTRE | `GPL-3.0-only` for code and docs; `schemas/` as `CC0-1.0` (RD-007 recommendation) | permissive schemas let any repository implement the contracts |
| SSTRE-Engine | **`GPL-2.0-only`, inherited and never relicensed.** Upstream LICENSE and headers are preserved verbatim | new SSTRE files follow upstream terms |
| SSTRE-AssetCompiler | `GPL-3.0-only` | must not contain code ported or copied from the engine. Anything that needs engine code (for example a `.tex` reader derived from `Texture.cpp`) is a separate GPL-2.0-only helper program, invoked as a process, or a clean-room implementation from a written spec |
| SSTRE-Manifests | **owner choice:** `GPL-3.0-only` (plan) *or* `CC0-1.0` for schemas/generated locks plus `CC-BY-SA-4.0` for curated recipes (RD-007) | contains only metadata about third-party assets, never asset content |
| Remaster-Toolkit | `GPL-3.0-only` | game-agnostic; dependencies audited before adoption |

Boundary rules:

1. Engine ↔ tools: separate processes only. They exchange compiled asset files and documented CLIs. No shared libraries, no linking, no shared address space.
2. No proprietary SDK (DLSS, NRD or any console SDK) may be distributed with, or as part of, a GPL build. Builds with DLSS enabled are never distributed by the project (RD-007 Q3).
3. No game assets, derivatives or model weights are distributed ([ADR-0002](0002-local-user-supplied-assets.md)).
4. Third-party notices are maintained per repository following the [notices policy](../policies/notices-policy.md). The REUSE/SPDX conventions there are proposed.
5. Naming and branding: an "unofficial, not affiliated with Croteam or Devolver Digital" disclaimer; no official logos. The project name itself awaits a trademark review (RD-007 Q12).

## Alternatives considered

| Alternative | Why not chosen / still open |
|---|---|
| `GPL-3.0-or-later` for the new repositories | allows future GPL versions; the plan proposes `-only`. Tradeoffs are in RD-007 §6.2; **owner decides** |
| GPL-2.0-only across all repositories | would allow linking with the engine, but drops the GPLv3 baseline the plan chose; open |
| Permissive licenses (MIT/Apache) for the toolkit | maximizes reuse; contradicts the plan's GPLv3 baseline; open only if the owner wants it |
| Monorepo with mixed licenses | rejected in [ADR-0001](0001-repository-separation.md) |

## Consequences

- During Phase 0, GPL-3.0 license text is added only on local, unpushed branches of SSTRE, SSTRE-AssetCompiler and Remaster-Toolkit, as a reviewable proposal. The GPLv3 text is the same for `-only` and `-or-later`; the SPDX identifier in the READMEs stays pending. No license is added to SSTRE-Manifests until the owner chooses.
- The SSTRE-Engine import must keep all upstream license files. Bundled `.gro` data, headerless entity sources and non-GPL files are flagged and handled in normal, reviewable commits, never by rewriting history.
- Engine-derived format knowledge used by GPLv3 tools needs a documented clean-room or separate-process approach.

## Acceptance criteria

1. The owner confirms an SPDX identifier per repository, including `-only` vs `-or-later` and the license family for Manifests.
2. The owner confirms the copyright-holder wording.
3. The owner chooses DCO or CLA.
4. RD-007 Q1 (Apache-2.0 KTX inside RTGL1), Q3 (DLSS), Q4 (entity provenance) and Q6 (local conversion under the EULA/SSA) have an owner or counsel position before any binary or engine release.
