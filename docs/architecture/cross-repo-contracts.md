# Cross-repository contracts

Status: **Proposal (Phase 0).** Nothing described here is implemented. Command
names and file names are illustrative until the owning repository implements
them and an ADR accepts the interface. Date: 2026-11-27.

This document defines how the five SSTRE repositories talk to each other:
which way dependencies may point, which files and command-line interfaces form
the boundaries, who owns each schema, and how revisions are pinned for a build.

## 1. Why file and CLI boundaries

- **Licensing.** Upstream engine code keeps its own license (under audit in
  `docs/research/RD-007-licensing.md`). GPL-2.0-only and GPL-3.0-only code
  cannot simply be combined into one derivative executable, and putting code in
  a vendor folder or submodule does not change that. Independent tools therefore
  run as **separate processes** and exchange **documented files**; they do not
  link against engine code and the engine does not embed them. Whether this is
  sufficient for a given distribution is a legal question recorded in RD-007,
  not settled here.
- **Language neutrality.** Implementation languages are not chosen yet
  (plan §3). JSON files validated by JSON Schema (draft 2020-12) plus a CLI with
  stable exit codes can be produced and consumed by any language.
- **Reproducibility.** Every stage boundary is a file that can be hashed,
  cached and recorded in provenance.

## 2. Dependency direction

```text
SSTRE (umbrella) ──pins──▶ Engine, AssetCompiler, Manifests, Toolkit
AssetCompiler ──invokes (CLI)──▶ Remaster-Toolkit
AssetCompiler ──reads──▶ Manifests (data)
Remaster-Toolkit ──reads──▶ resolved recipes produced from Manifests (data, game-agnostic form)
Engine ──loads──▶ compiled asset packages (files only)
```

| From → To | Allowed | Rule |
|---|---|---|
| Umbrella → any | Yes | Pins revisions, orchestrates builds, hosts docs and contract schemas. Contains no duplicate implementation. |
| AssetCompiler → Toolkit | Yes | Via the Toolkit CLI (or, if both end up in the same language and license, a library API decided by ADR). |
| AssetCompiler → Manifests | Yes | Reads data at a pinned revision. |
| Toolkit → AssetCompiler / Manifests / Engine | **No** | The toolkit is game-agnostic: no Serious Sam names, formats, paths or IDs in its code. Game knowledge arrives only as input data. |
| Manifests → anything | **No code** | Declarative data only. No executable hooks or scripts by default; any exception needs an ADR. |
| Engine → Python / ComfyUI / inference / Toolkit | **No** | Runtime loads precompiled assets only; no Python, no live model, no network inference. |
| Any → umbrella internals | No | Repositories depend on published contract files (schemas) at a pinned revision, not on umbrella scripts. |

Circular dependencies are not allowed. A change that needs one is a sign that
the boundary belongs elsewhere and needs an ADR.

## 3. Pipeline interfaces

Stage numbers follow the asset pipeline contract in plan §4.

| # | Stage | Producer | Consumer | Boundary artifact | Schema |
|---|---|---|---|---|---|
| 1 | Detect edition, verify source hashes, extract to local workspace | AssetCompiler | AssetCompiler | Local workspace directory (never committed) | – |
| 2 | Inventory | AssetCompiler | AssetCompiler, Manifests curation, Toolkit (via recipes) | Asset inventory JSON | `asset-inventory.schema.json` |
| 3 | HD → Classic mapping | AssetCompiler (proposals), curated in Manifests | AssetCompiler | Mapping entries in Manifests `mappings/` | Inventory schema identifiers; mapping file schema TBD |
| 4 | Recipe authoring (development only) | Dev-time VLM / curators | Manifests | Per-asset recipes, overrides, profiles | `asset-recipe.schema.json` |
| 4b | Recipe resolution and freeze | Generic layered resolver (Toolkit) with game-specific layer order supplied by AssetCompiler | Toolkit | Resolved (effective) recipe JSON, canonicalized | `asset-recipe.schema.json` (resolved form) |
| 5 | Execute recipes | Toolkit | AssetCompiler | Processed intermediates (PNG/TIFF/EXR, local only) + provenance | `build-provenance.schema.json` |
| 6 | QA and fallback | Toolkit (generic metrics) | AssetCompiler | QA report JSON | TBD (see RD-008) |
| 7–8 | Compile, mipmap, compress, package | AssetCompiler | Engine | Runtime asset package + package manifest with output hashes | TBD |
| – | Integrated build pins | Umbrella | Umbrella build tooling | `release-pins.json` | `release-pins.schema.json` |

Recipe precedence (plan §4): curated override > generated per-asset recipe >
material profile > global defaults. The directory layout realizing this lives in
SSTRE-Manifests `docs/layout.md`.

### CLI conventions (proposed, all tools)

These apply to AssetCompiler and Toolkit command-line tools and to any later
umbrella builder:

1. Subcommand style: `<tool> <verb> [options]`. Inputs and outputs are explicit
   paths (`--input`, `--output`, `--workspace`); no hidden global state.
2. Machine-readable output goes to files (or stdout with `--json`), never mixed
   with log text. Logs go to stderr.
3. Exit codes: `0` success, `1` processing completed with failures recorded in
   the output report (for example assets that fell back), `2` usage or
   environment error, `3` contract violation (input failed schema validation).
4. `--version` prints tool version, Git commit and the contract schema versions
   it reads and writes.
5. Every JSON document written carries a `schema_version` (or `format_version`)
   and is serialized canonically (UTF-8, sorted keys, no insignificant
   whitespace variation, LF) so it can be hashed for cache keys.
6. No network access unless the subcommand is explicitly a fetch step, and
   fetched content is verified against expected hashes.
7. Paths inside documents are relative to a declared root, use `/`, and never
   contain user-specific absolute paths (they would leak into provenance).

## 4. Schema ownership

Cross-repo contract schemas live in the umbrella `schemas/` directory during
Phase 0 so they can be reviewed together. Consumers pin the umbrella commit
that contains the schema version they implement. A schema may move to the
repository that owns it once that repository has code; the umbrella then keeps
a pointer, not a copy.

| Schema | Owner | Producer repo | Consumer repos | Status |
|---|---|---|---|---|
| [`asset-inventory`](../../schemas/asset-inventory.schema.json) | AssetCompiler | AssetCompiler (`sstre-ac inventory`) | Manifests, Toolkit (indirectly) | proposal, implemented (EXP-007) |
| [`game-edition-report`](../../schemas/game-edition-report.schema.json) | AssetCompiler | AssetCompiler (`sstre-ac detect`) | umbrella builder | implemented (EXP-007) |
| [`asset-recipe`](../../schemas/asset-recipe.schema.json) | Toolkit | Manifests (authored), Toolkit resolver | Toolkit, AssetCompiler | proposal |
| [`build-provenance`](../../schemas/build-provenance.schema.json) | Toolkit | Toolkit, AssetCompiler | release tooling, QA | proposal |
| [`source-selection`](../../schemas/source-selection.schema.json) | AssetCompiler | AssetCompiler (`select-source`) | AssetCompiler planner, Manifests | implemented (EXP-012) |
| [`build-config`](../../schemas/build-config.schema.json) | AssetCompiler | user / umbrella builder, Manifests (layer configs) | AssetCompiler planner | implemented (EXP-015, ADR-0009) |
| [`build-manifest`](../../schemas/build-manifest.schema.json) | AssetCompiler | AssetCompiler (`sstre-ac plan`) | packaging, release tooling, QA | implemented (EXP-015) |
| [`platform-profile`](../../schemas/platform-profile.schema.json) | AssetCompiler | AssetCompiler / Manifests | AssetCompiler planner, Toolkit (target sizes) | implemented (EXP-015); non-PC profiles hypothetical |
| [`layer-approvals`](../../schemas/layer-approvals.schema.json) | Manifests (data), AssetCompiler (consumer) | curators (local until GATE-05) | AssetCompiler planner | implemented (EXP-015) |
| [`asset-pack`](../../schemas/asset-pack.schema.json) | AssetCompiler | Toolkit (`ai-enhancement` packs), curators, community | AssetCompiler planner (layers 6–7) | implemented (EXP-015) |
| [`release-pins`](../../schemas/release-pins.schema.json) | umbrella | umbrella | umbrella build tooling | proposal |
| [`engine-upstream-lock`](../../schemas/engine-upstream-lock.schema.json) | SSTRE-Engine | SSTRE-Engine | patch tooling (EXP-010) | implemented (ADR-0008) |
| QA report, package format | unassigned | – | – | not yet proposed |

Every schema must:

- declare `"$schema": "https://json-schema.org/draft/2020-12/schema"` and a
  stable `$id` under
  `https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/schemas/`;
- include synthetic `examples` (no real game paths or hashes are required; if
  real-looking values are used they must not reproduce proprietary listings);
- pass `python scripts/validate_repo.py`, which checks the metaschema and
  validates each example, resolving `$ref` between schemas by `$id`.

Schema versioning (proposed): documents carry `schema_version` using semantic
versioning. Adding optional fields is a minor change; removing or changing the
meaning of a field is a major change and needs an ADR plus coordinated PRs in
every consuming repository.

## 5. Version pinning: submodules vs. lock file

| | Git submodules in umbrella | Pinned-revisions lock file (`release-pins.json`) |
|---|---|---|
| Mechanism | Gitlinks record each component commit | JSON file records repository URL + full commit SHA per component |
| Exactness | Exact commit | Exact commit (40-hex SHA enforced by schema) |
| Tooling | Native Git; known friction (`--recurse-submodules`, detached HEADs, Windows path issues) | Needs a small fetch/verify script (not yet written) |
| Clone cost | Recursive clone pulls the full engine history (upstream RT candidate pack ≈ 116 MiB observed locally) | Fetch only what a build needs; shallow fetch by SHA possible |
| Review | Gitlink diffs show only SHAs | Plain JSON diff; can carry status, notes, upstream base, contract versions |
| Validation | None beyond Git | Validated by `release-pins.schema.json` in CI |
| Licensing perception | Bundles GPL-2 and GPL-3 trees in one checkout (does not by itself create a combined work, but blurs boundaries) | Keeps repositories visibly separate |

**Proposal:** use a lock file (`release-pins.json`, conforming to
[`schemas/release-pins.schema.json`](../../schemas/release-pins.schema.json)) for
Phases 1–4. Revisit submodules only if the eventual user-facing builder or
release packaging benefits from them; record that in an ADR. No
`release-pins.json` exists yet, because there is nothing to pin.

Rules (proposed):

- Pin full commit SHAs, never branches; tags are informational.
- The engine entry records its upstream base repository and commit.
- A pin set lists the contract schema versions all components agree on.
- Updating a pin is a reviewed PR in the umbrella that states what changed in
  the component and which checks were run.

## 6. Open questions

1. Will AssetCompiler and Toolkit share an implementation language (making a
   library API possible), or stay CLI-only? Depends on RD-003 and licensing.
2. Where does the layered recipe resolver live? Proposed: generic resolver in
   Toolkit, Serious Sam layer order supplied by AssetCompiler.
3. Runtime asset package format and whether the engine reads SE1 native
   formats only or gains DDS/KTX2 loaders (RD-005, ADR-005).
4. Whether Manifests needs any executable content (default: no).
5. Owner confirmation of the lock-file approach over submodules.
6. **Two asset taxonomies (lead finding, 2026-11-27).** The inventory schema's
   `category` (semantic content, e.g. `architecture`, `enemy`, `ui_hud`) and the
   recipe schema's `textureClass` (processing class, e.g. `vegetation-cutout`,
   `normal-map`, `mask-technical`) are deliberately separate axes. The mapping
   `category` (+ alpha/tileability/format facts) → `textureClass` is not yet
   specified. Proposed: a declarative classification profile in Manifests,
   applied by AssetCompiler, with VLM proposals in development mode only. Settle
   it during POC-04/POC-06.
7. Input data point for item 3: the RT fork already loads `<tex>.ktx2`
   overrides with `_n`/`_rme` companions by virtual path (RD-001, RD-005).
   Classic-VK has no such loader, so under proposed ADR-0005 the loader must be
   ported.
