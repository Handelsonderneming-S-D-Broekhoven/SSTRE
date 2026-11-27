# EXP-007: Edition detection and archive inventory (first AssetCompiler code)

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | POC-03 |
| Status | complete |
| Environment | Windows 11 Pro 10.0.22631, Intel Core i5-11600K, 32 GB RAM, local SSD/HDD drives; Python 3.10.11 (venv under `local-work/inventory/venv`, pytest 9.2.0, jsonschema 4.26.0) |
| Inputs | Five local Steam installs: Classic TFE, Classic TSE, HD TFE, HD TSE, Fusion 2017 (builds as in [RD-002](../research/RD-002-hd-assets.md) §3.1). No hashes, paths or file names here (GATE-05) |
| Code | SSTRE-AssetCompiler `pyproject.toml`, `src/sstre_assetcompiler/`, `tests/` (uncommitted working tree on `phase1/validation`), version `0.1.0.dev0` |

## Goal and success criteria

Build a small, tested, stdlib-only tool that (1) identifies each local install by top-level file hashes plus Steam metadata and (2) inventories its `.gro` archives into documents that validate against `schemas/asset-inventory.schema.json` and a new `schemas/game-edition-report.schema.json`. Success: all five installs detected exactly, all outputs schema-valid, aggregate counts consistent with RD-002 §4, no game data in any repository.

## Procedure (exact, reproducible)

1. **Clean-room procedure (ADR-0006).** The author did not open engine source code (`upstream/`, SSTRE-Engine branches) or the Phase 0 probe scripts (which were written while reading engine source). Inputs were only RD-002 §4–§5 (written description), the asset-inventory schema, the PKZIP format as implemented by the Python standard library `zipfile` (PKWARE APPNOTE), and black-box observation of header bytes of local `.tex` entries, read in memory. The `.tex` layout used is documented in the module docstring of `texheader.py`.
2. `pytest` with synthetic fixtures generated at test time (invented zip archives, synthetic `TVER`/`TDAT` byte strings, a fake Steam library with an invented appmanifest).
3. Local fingerprint profiles: `sstre-ac fingerprint <install> --edition <e> --profile-id <id> --include <globs> [--exclude ...] [--file-edition GLOB=EDITION] -o ...`, one per install, merged into one local file. Selection mirrored RD-002 §3.2: content archives, main executable and (HD) signature catalog; shader caches, the Fusion SS3/JotN packs and `Mods/` excluded. Scripts and outputs: `local-work/inventory/` only.
4. `sstre-ac detect <5 installs> --fingerprints fingerprints.local.json -o detect-report.local.json`.
5. Per install: `sstre-ac inventory <install> --fingerprints fingerprints.local.json --jobs 4 -o inv/<e>.inventory.local.json --summary inv/<e>.summary.local.json`.
6. Validation with `jsonschema` (Draft 2020-12, format checker) against the umbrella schemas and the package's fingerprint schema; entry-level `.tex` statistics with the package's header reader.

## Results ([EXP] unless labelled otherwise)

**Tests.** `python -m pytest`: **69 passed**, 0 failed, 0 skipped (0.84 s). Umbrella `scripts/validate_repo.py --root .`: 0 errors, 0 warnings (new schema's example validates). `reuse lint` on SSTRE-AssetCompiler: compliant (40/40 files).

**Detection.** All five installs: status `exact`, correct edition, all profile files matched (7/7, 9/9, 5/5, 11/11, 9/9). The overlapping Classic profiles score 1 shared file each against the other install, which the best-score rule resolves. Steam app ID and build ID from the appmanifest match RD-002 §3.1 for all five; the appmanifest's account field is not read into the report (verified: absent from the output). Classic TSE: 3 archives under `Mods/` reported as excluded. HD TFE/TSE: 1 unlisted archive each (shader cache); Fusion: 8 unlisted (SS3/JotN packs, their patches, shader caches).

**Hash cross-check (local only).** The 40 file hashes in the Phase 0 local table were reproduced byte-for-byte (40/40 equal). The tool found one additional Fusion patch archive (the patch of the shared base pack) that the Phase 0 table omitted.

**Inventory** (all five documents: 0 schema errors).

| Install | Archives | Entries (files) | Uncompressed | Assets after override | Shadowed | ID collisions | Inventory time / wall incl. detect |
|---|---|---|---|---|---|---|---|
| Classic TFE | 6 | 2 410 | 0.38 GB | 2 406 | 4 | 0 | 2.0 s / 3 s |
| Classic TSE | 8 | 4 405 | 0.62 GB | 4 380 | 25 | 0 | 2.6 s / 6 s |
| HD TFE | 3 | 6 762 | 2.52 GB | 6 034 | 515 | 0 | 11.8 s / 18 s |
| HD TSE | 9 | 18 272 | 7.96 GB | 12 621 | 3 748 | 16 | 23.0 s / 45 s |
| Fusion (TFE/TSE packs) | 8 | 36 362 | 8.87 GB | 35 959 | 395 | 14 | 25.3 s / 52 s |

Totals: 68 211 entries, ~20.4 GB decompressed and hashed in memory, ~2 min wall for all five inventories; detection alone for all five: 55.8 s (10.6 GB of top-level files hashed). Every entry used method 0 or 8; 0 encrypted, 0 unsafe names, 0 CRC/read errors. Output size: 1.2–17 MB JSON per install.

**Comparison with RD-002 §4 (per-archive entry and extension counts).** Identical for every number in the RD-002 table: entries per main archive (Classic TFE base, Classic TSE base and levels, HD TFE ×3, HD TSE base, Fusion TFE and TSE packs), and `.tex`, `.mdl`, `.wld`, `.ecl`, `.wav`, `.mtr`, `.bmf`, `.rsc` counts. One apparent difference: RD-002 gives 118 entries for the Classic TSE extra archive, the tool counts 107 files + 11 directory entries; RD-002 counted directory entries. The 42 loose Classic TFE level files are not inventoried (archives only, by design).

**Comparison with RD-002 §4.1 (Classic `.tex` header statistics).** Entry-level (not deduplicated), the reader reproduces every metric exactly: TFE 1229 files, v4 1200 / v3 29, FXDT 19, animated 9, flag bit 0 set 245, non-square 454, NPOT 0, max 1024 px (5 files), mode 256 px (553); TSE 1576, v4 1562 / v3 14, FXDT 25, animated 10, bit 0 set 418, non-square 442, NPOT 0, 1024 px ×7, mode 256 (728). In the deduplicated inventory the counts are lower by exactly the shadowed textures (TFE 1228 textures, TSE 1566).

## Deviations, modifications and failures

- **v3 field order differs from the RD-002 §5 wording.** Observed (EXP): in v3 headers the first-mip value is the 6th int32 after `TDAT` (`flags, mexW, mexH, fine, ctMips, firstMip, frameSize, frames`). Under this order `frameSize` is consistent with the derived pixel size for 43/43 v3 files; under the RD-002 wording 0/43. v4 matches RD-002 as written (`flags, mexW, mexH, fineMips, firstMip, frames`, no chunk size). The naming of the 4th/5th v3 fields is [ASM].
- **First run rejected 6 Classic headers** whose logical (mex) size is 2^21, above an arbitrary sanity bound of 2^20 in the reader. Bound raised to 2^30, test added, Classic inventories re-run; 0 rejects now.
- **Schema inconsistency:** the asset-inventory `source_id` description example (`<edition>:<archive>`) violates its own pattern `^[a-z0-9_.-]+$` (no `:`). The tool uses `<edition>.<relpath with / → _>`.

## Interpretation ([SRC]/[DOC]/[ASM] clearly labelled)

- [ASM] Flag bit 0 is the "alpha channel" flag RD-002 counted (counts are identical, and in v4 files bit 0 coincides with 4-byte pixels by entry size, with 3 exceptions). The tool reports `flags_raw` only and does not yet set `has_alpha_channel`.
- [ASM] Override order: winners use the lexicographically last archive path (puts patches after bases in all five installs). Mount order is unconfirmed; every shadowed asset carries a note saying so. Matching is case-insensitive.
- [ASM] The 16/14 asset-ID collisions come from stripping `Content/<game>/` when an edition ships several roots (e.g. HD TSE also has HD TFE content); they are disambiguated with a path-hash suffix, which keeps IDs stable but is not pretty.
- [ASM] Timings were measured after the fingerprint step had read every archive, so the OS file cache was likely warm; cold-cache times on HDD will be higher.

## Impact on ADRs, dossiers and backlog

- POC-03: met. RD-002 §5 should correct the v3 `TDAT` field order; RD-002 §4 Classic TSE extra-archive count is 107 files (+11 directories).
- ADR-0002/GATE-05: fingerprints, reports and inventories stay in `local-work/inventory/`; the repo has synthetic examples only.

## Open questions

1. Owner/lead: should HD TSE's bundled HD TFE DLC be tagged `hd_tfe` per archive (supported via `--file-edition`), and Fusion's LotB DLC `fusion_hd_tse` (chosen locally)?
2. Engine archive mount order (needed for authoritative shadowing): via a GPL-2.0-only helper or a written spec?
3. Should `schemas/tests/game-edition-report/` negative tests be added (validator notes none exist)?
