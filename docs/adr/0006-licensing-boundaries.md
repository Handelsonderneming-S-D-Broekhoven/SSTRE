# ADR-0006: Licensing boundaries between repositories

- **Status:** accepted (owner decision, 2026-11-27). This is a licensing *policy*, **not** legal clearance. The open legal questions in [RD-007](../research/RD-007-licensing.md) §16 remain open.
- **Date:** 2026-11-27 (proposed); 2026-11-27 (accepted by owner)
- **Deciders:** project owner
- **Evidence:** [RD-007 licensing](../research/RD-007-licensing.md), [notices policy](../policies/notices-policy.md), [RD-001](../research/RD-001-engine-baseline.md), [RD-005](../research/RD-005-rendering.md)

## Context

The Phase 0 audit (RD-007) found the following:

- **Engine license.** Every engine candidate ships the unmodified GPLv2 text. The file headers grant "version 2 of the GNU General Public License" without "or any later version". The engine is therefore treated as **GPL-2.0-only**.
- **GPL versions.** GPL-2.0-only and GPL-3.0 code cannot be combined in one derivative work. Separate programs that exchange files through CLIs are generally treated as aggregation (FSF GPL FAQ), but that depends on the actual coupling.
- **Questionable material in the engine repos:**
  - LightWave SDK headers with no license terms.
  - A Microsoft `DSOUND.H` marked "All Rights Reserved".
  - Checked-in `Bison.exe` and `Flex.exe`.
  - The `SE1_10.gro` game-data archive, with no license stated.
  - TFE `Entities` sources in the RT/Vk line, with no headers and uncertain provenance.
- **RayTracedGL1.** It is MIT-licensed, but it compiles in Apache-2.0 KTX code, which the FSF considers incompatible with GPLv2. It can also optionally link NVIDIA DLSS.
- **Game licence.** The Classic game licence forbids redistribution and derivative works.

## Decision

| Repository | License (SPDX) | Copyright notice for our own work |
|---|---|---|
| SSTRE | `GPL-3.0-only` (whole repository, including `schemas/`) | Handelsonderneming S.D. Broekhoven, trading as ITEagle Europe |
| SSTRE-Engine | **`GPL-2.0-only`**: preserved from upstream and never relicensed. Our modifications use the same terms | same, added for our changes only; upstream notices untouched |
| SSTRE-AssetCompiler | `GPL-3.0-only` | same |
| SSTRE-Manifests | `CC0-1.0` for factual manifest metadata; `CC-BY-SA-4.0` for original creative recipes and curated configuration (distinction documented in the repo's `LICENSE.md` and `REUSE.toml`) | same |
| Remaster-Toolkit | `GPL-3.0-only` | same |

Further rules:

1. **Contributions:** the Developer Certificate of Origin (`Signed-off-by:`), no CLA. Contributors keep their copyright.
2. **Engine ↔ tools boundary:** separate processes only, exchanging compiled asset files through documented CLIs. No shared libraries, no linking, no shared address space. GPLv3 tools must not contain code copied or ported from the engine. Engine-derived format knowledge is used through a separate GPL-2.0-only helper process or a clean-room implementation from a written specification.
3. **Preserve notices.** All existing third-party copyright notices are kept verbatim.
4. **No unauthorized material.** The project never publishes material whose redistribution rights are unclear. This covers game assets, derivatives of them, model weights, proprietary SDKs, and the questionable upstream files listed above. Public availability elsewhere does not establish redistribution rights.
5. **No proprietary SDKs in GPL builds.** DLSS, NRD and console SDKs are never distributed with or as part of a GPL build.
6. **No engine binaries yet.** Engine binaries are not distributed until the identified licensing blockers (RD-007 Q1, Q3, Q4) are resolved.
7. **Machine-readable licensing.** It is expressed with the [REUSE](https://reuse.software/) convention (`LICENSES/`, `REUSE.toml`) in the four non-engine repositories.
8. **Naming and branding.** Use an "unofficial, not affiliated with Croteam or Devolver Digital" disclaimer and no official logos. The project name is pending a trademark review (RD-007 Q12).

## Alternatives considered

| Alternative | Outcome |
|---|---|
| `GPL-3.0-or-later` | rejected by owner in favour of `-only` |
| GPL-3.0 for manifests | rejected; data is better served by CC0 / CC-BY-SA |
| CLA | rejected for the initial community phase; DCO adopted |
| CC0 for umbrella `schemas/` (RD-007 suggestion) | not adopted; the umbrella is uniformly `GPL-3.0-only`. Schemas may be republished under CC0 in Manifests later if needed |

## Consequences

- **License files.** The license texts are added to the four non-engine repositories. The engine gets none before the upstream import, because the imported upstream `LICENSE` applies.
- **Publishing upstream branches.** Before the upstream branches are published, the questionable headers, binaries and data archives are audited (Phase 1). Any removal happens in normal, reviewable commits on top of the preserved history, never by rewriting it.
- **KTX in the runtime.** Removing Apache-2.0 KTX code from the GPLv2 runtime is a Phase 1 investigation. The candidate approach is to do KTX processing only in the GPLv3 AssetCompiler, which emits a runtime format with a GPLv2-compatible loader.
