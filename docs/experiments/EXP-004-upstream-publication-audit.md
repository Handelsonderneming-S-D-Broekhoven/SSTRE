# EXP-004: Upstream publication audit (full history of `upstream/classic-vk-main` and `upstream/rt-main`)

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | ADR-0006 "Publishing upstream branches" consequence; RD-007 Q4, Q5, Q9 |
| Status | complete (inventory and evidence). **Not legal advice and not a clearance.** Every publication decision below belongs to the owner. Items marked "needs counsel" are listed in [RD-007 §16](../research/RD-007-licensing.md#16-unresolved-legal-questions-for-the-ownercounsel). |
| Environment | Windows 11 Pro 10.0.22631, Git 2.55.0.windows.3, Python 3.10.11 (`local-work\venv`). Read-only git plumbing only. No branch was checked out or modified. Scripts and raw outputs: `L:\claude-ws\SSTRE\local-work\audit\` (local only) |
| Inputs | SSTRE-Engine local branches `upstream/classic-vk-main` = `510d36f901cbe883c56b155b53717e4efdeb6522` (311 commits) and `upstream/rt-main` = `0e7f223c19a28014b60d900878c28831db522120` (449 commits). Reference: `upstream\Croteam-official_Serious-Engine` @ `b408e88` (99 commits). Local retail Classic TFE/TSE installs (read-only, used only for byte-identity counts) |

## Goal and success criteria

The owner asked for an audit of questionable headers, binaries and game-data archives before these branches are published. Pushing a branch publishes **every blob reachable from it**, not only the files at HEAD, so the audit covers whole histories.

Success criteria:

1. Every reachable blob of both branches is enumerated, with sizes.
2. Each finding has its origin (first commit and author), the evidence for and against redistribution rights, a risk rating, the publication options, and a recommendation.
3. The question "does Croteam-official carry the same files?" gets an explicit answer.

All three are met.

Restriction honoured: engine-repo file paths are listed. Game-data contents are reported **only as aggregate counts**. No per-file hashes and no game-asset entry names appear here.

## Procedure (exact, reproducible)

All commands ran from `L:\claude-ws\SSTRE\repos\SSTRE-Engine` or the audit directory, using Git Bash with `MSYS_NO_PATHCONV=1`.

1. **Blob totals.** `git rev-list --objects <branch> | cut -d' ' -f1 | git cat-file --batch-check='%(objecttype) %(objectsize)'`, summing the blobs.
2. **Per-path history.** `enum_history.py` parses `git log <branch> --reverse --raw --no-abbrev --no-renames -m --root`. For every path that ever existed it records the first commit, the author, the number of blob versions and the sizes. It reproduced the step-1 blob counts exactly.
3. **Header classification.** `headers.py` reads the first 3,000 bytes of **every historical blob** of source-like files (`.c .cpp .h .hpp .inl .es .y .l .cc .asm .py .sh .pl .cmake .frag .vert .rc .def`). `headcls.py` does the same for HEAD blobs. Markers used: "All rights reserved", "Microsoft Corporation", "NewTek", "version 2 of the GNU General Public License", "any later version", SPDX, MIT/Zlib/BSD phrases. This is a heuristic, and individual misclassifications are possible.
4. **Croteam-official comparison.**
   - `git merge-base --is-ancestor b408e88… upstream/rt-main`.
   - Blob-set comparison against `git rev-list --objects HEAD` of the Croteam-official clone (`cmp.py`, `rtonly.py`, `cvk_vs_cro.py`).
5. **Retail comparison (aggregate only).** `retail_cmp.py`, `cvk_data3.py` and `gro2.py` compare blobs with SHA-256 of loose files in the local retail Classic TFE/TSE installs. They compare `.gro` (ZIP) entries by (name, CRC-32, size) against the entries of the retail `.gro` archives. Only counts are printed.
6. **TFE entity provenance.** `ent.py` compares `Sources/Entities` at RT `4d17950` with `SamTFE/Sources/Entities` at CVK `c4f9322`. It strips the leading comment header and normalises line endings.

## Results

### R1. Totals [EXP]

| | `upstream/classic-vk-main` (CVK) | `upstream/rt-main` (RT) |
|---|---|---|
| Commits | 311 | 449 |
| Reachable blobs (unique) | 5,581 (136.7 MB) | 8,438 (199.8 MB) |
| Paths ever / at HEAD | 11,302 / 11,197 | 5,676 / 5,120 |
| History-only paths (deleted before HEAD) | 105 (1.8 MB), all source/build files plus one `.png` | 556 (9.9 MB), mostly Croteam's generated `EntitiesMP/*.cpp`/`_tables.h` from `9d8b787` |
| `.exe` | `Tools.Win32/Bison.exe`, `Flex.exe` (×2 trees) | same 2 files |
| `.dll` `.lib` `.obj` `.pdb` | **none, in any commit** | **none, in any commit** |
| Submodules | none | RTGL1 gitlink in history (a commit pointer only, no blobs). `.gitmodules` is empty at HEAD |
| Root / lineage | root `67d2e93` + `c4f9322` "Upload sources" (2022-05-10, tx00100xt), which imports the whole tree in one commit. No earlier history | **Croteam-official master `b408e88` is an ancestor** (all 99 Croteam commits, 6,628 blobs), plus 350 Sultim commits adding 1,810 blobs (67.0 MB) |

### R2. Game-data archives and game-data files [EXP]

| ID | Item (paths) | Branch | First commit / author | Size | Croteam-official? | Retail identity (aggregate) |
|---|---|---|---|---|---|---|
| G1 | `SE1_10.gro` | RT | `9d8b787` 2016-03-11 SLAwww (Croteam) | 86.6 MB, 2,151 entries (1,802 files) | **yes** (same blob) | **1,674 of 1,802** file entries are identical (name, CRC-32, size) to entries in the retail Classic TFE/TSE `.gro` archives; 128 are not |
| G2 | `SamTFE/SE1_10b.gro`, `SamTSE/SE1_10b.gro` (byte-identical) | CVK | `c4f9322` 2022-05-10 tx00100xt | 2.78 MB, 105 textures | **no** | 92 are identical to entries in Croteam's `SE1_10.gro`. 87 are identical to retail archive entries. **13 match neither**: they carry 2001 timestamps and have unknown provenance |
| G3 | `SamT?E/Demos/*` (`.dem` recordings, `*Tbn.tex` thumbnails, `.ini`, `.des`), 34 files | CVK | `c4f9322` tx00100xt | 20.5 MB | **no** | **32 of 34** non-empty files are byte-identical to files in the local retail installs |
| G4 | `SamT?E/Scripts/*` (223 non-empty), `Controls/*` (40), `Help/ShellSymbols.txt` (2), `Data/*` (15) | CVK | `c4f9322` tx00100xt | ≈0.8 MB | Scripts: 11 yes; Controls: 0; Help: 0; Data: 7 yes | Not in Croteam-official but retail-identical: Scripts 148, Controls 31, Help 2, Data 4. The rest match neither (edited or new) |
| G5 | `SamT?E/Mods/*Tbn.tex`, `.des`, `.lst` (12 non-empty) | CVK | `c4f9322` tx00100xt | 2.3 MB | no (except empty files) | 7 are retail-identical. 5 are not, including both `XPLUSTbn.tex` (1 MB each, XPLUS community mod thumbnail, provenance unstated) |
| G6 | `Data/Default.ifr`, `Data/Logitech.ifr` (force-feedback effect data) | both | RT `9d8b787` SLAwww; CVK `c4f9322` | 182 KB | **yes** | retail-identical |
| G7 | `OverridenTextures/BlueNoise_LDR_RGBA_128.ktx2` | RT | `40fcf7a` 2021-08-17 Sultim | 8.4 MB | no | n/a. **Same blob as `Tools/BlueNoise_LDR_RGBA_128.ktx2` in the RTGL1 repo (MIT)**. No notice names the noise source |
| G8 | `OverridenTextures/WaterNormal_n.ktx2` | RT | `dd297f2` 2021-08-24 Sultim | 1.4 MB | no | n/a. **No provenance or licence stated** |
| G9 | Screenshots: `Images/samvulkan_1..6.png`, `samxplus_1..3.png` (13 blob versions, 37.3 MB) | CVK | `c29fe96` 2022-05-20 / `b38d197` 2023-03-26 / `c4f9322` tx00100xt | 37.3 MB | no | n/a. These are screenshots of the game rendering Croteam assets |
| G9b | Screenshots: `Github/Vulkan_Screenshot_0..4.png` (10 blob versions) | RT | `9cf30c2` 2020-02-07 Sultim | 16.7 MB | no | n/a (as G9) |

Not found in any commit of either branch: `.wld`, `.mdl`, `.wav`, `.ogg`, `.mp3` as loose files. Those formats exist only *inside* G1/G2.

### R3. Binaries and other non-source files [EXP]

| ID | Item | Branch / origin | Croteam-official? | Note |
|---|---|---|---|---|
| B1 | `Tools.Win32/Bison.exe`, `Flex.exe` (+ `bison.zip`, `flex.zip` with sources and `COPYING`, per RD-007 §3.3) | both; RT `8068ab1`/`9d8b787` SLAwww 2016-03-11; CVK `c4f9322` | **yes** (identical blobs) | GPL build tools, never linked. Supply-chain hygiene: never run them (lead brief) |
| B2 | `*.aps` (MSVC resource caches), `hlp/AfxCore.rtf` (MFC AppWizard help template), `OldHelp.doc`, `hlp/images/*.jpg` | both | **yes** | Croteam editor help and IDE artefacts |
| B3 | `CompiledSpirv/*.spv` | both (Sultim 2020; tx00100xt 2022) | no | generated from in-repo GLSL (GPL-2.0-only) |
| B4 | `FLEX.skl`, `smcFlex.skl` (flex skeletons), `*.bmp`, `*.ico`, `*.cur` (resource icons) | both | yes, except CVK edits | Croteam source resources |

### R4. Headers across history [EXP] (counts are paths; history = any blob version)

| Class | CVK at HEAD | CVK history-only | RT at HEAD | RT history-only |
|---|---|---|---|---|
| GPL-2.0-only Croteam-style grant | 6,326 | — | 2,987 | — |
| **"All rights reserved", no GPL grant** (Croteam-style text) | **43** (see H3) | 0 | 0 | **2,946** pre-GPL versions from `9d8b787` (Croteam), plus **88** 2016 zcaliptium files (see H4) |
| Microsoft `DSOUND.H` "All Rights Reserved" | 2 | — | 1 | — |
| NewTek (LightWave SDK + `servmain.c`, `shutdown.c`, `startup.c`, `username.c`) | 106 (53 per tree) | — | 53 | — |
| No header at all | 80 | 20 | **194** (132 of them TFE `Sources/Entities{,/Common}`) | 6 |
| Copyright line only (zlib, libogg/libvorbis, cmake modules, …) | 344 | 4 | 96 | 437 (Croteam's generated `EntitiesMP`) |
| Zlib (SDL2 headers) / MIT (VMA, SDL GL headers) | 148 / 8 | — | 1 / 0 | — |
| GPL-or-later (Bison outputs, `MSLegacy.h`) | 6 | 16 | 1 | — |

No-header files by directory:

- **RT HEAD:**
  - `Sources/Entities` 120 and `Sources/Entities/Common` 12, all from Sultim `4d17950`.
  - `Sources/Engine/Graphics` 12 (Sultim).
  - Croteam-official-origin files: `Engine/Base` 9, `Models/Player_old` 8, `SeriousSkaStudio` 5, `GameAgent` 3, `Ecc` 3, `Engine/Ska` 3, `libvorbis` 4, `zlib` 2, and singles.
- **CVK HEAD**, per tree, with SamTFE and SamTSE mirroring each other: `Engine/Graphics` 5, `External/SDL2` 4, `External/libvorbis` 4, `libvorbis` 4, `GameAgent` 3, `SeriousSkaStudio` 3, `zlib` 2, `LWSkaExporter` 3, plus root build files (6). CVK's TFE `Entities` **do** carry the Croteam GPL header (see H6).

### R5. Specific header items

| ID | Item | Evidence |
|---|---|---|
| H1 | `Sources/Engine/Sound/DSOUND.H` (all three lines: Croteam, RT, CVK ×2) | `Copyright (C) 1995-2000 Microsoft Corporation.  All Rights Reserved.` **The same blob is in Croteam-official** (`9d8b787`). The Croteam README does not list it among the non-GPL components [SRC]. |
| H2 | LightWave SDK `Sources/LWSkaExporter/SDK/*` (49 headers) + 4 `.c` stubs | `Copyright 1999, NewTek, Inc.` / `Copyright 1995,1997 NewTek, Inc.` A `git grep` for license, permission, confidential or proprietary in `SDK/` returns nothing: **there is no licence text**. Same blobs in Croteam-official (51/51 identical). The Croteam README explicitly lists it as "not licensed under the GNU GPL v2" [SRC]. |
| H3 | CVK, 43 files whose header is only `/* Copyright (c) 2002-2012 Croteam Ltd. All rights reserved. */`: `Engine/Base/{DynamicLoader.h, FileSystem.h, ThreadLocalStorage.h, SDL/*, Unix/*, Win32/*}`, `Engine/Graphics/{SDL,Win32}/*`, `Engine/Sound/SoundMixer386.asm`, `SeriousSam/Menu{,Gadgets,Printing}.{cpp,h}` | All first appear in `c4f9322` (tx00100xt, single import commit, so no earlier history). None of these paths exists in Croteam-official HEAD. They match the style of the 2016 Linux/SDL port lineage (Ryan C. Gordon's commit is in RT history) [ASM]. The text grants no licence; the GPL applies only through the repo `LICENSE`/README. |
| H4 | RT history: 2,946 paths whose `9d8b787` version reads "Croteam Ltd. All rights reserved." | Croteam's own upload. It was superseded the same day by `a4af93f` (2016-03-11, Matt Lee, "Add GPL header to files"). Croteam-official HEAD has **0** such headers. The 88 zcaliptium files (`a84fb76` etc., 2016-03-12) are in Croteam-official history and were deleted later. |
| H5 | `GameAgent/MSLegacy.h` (Luigi Auriemma, GPL-2.0-or-later) | compatible with GPL-2.0-only (RD-007 §3.2) |
| H6 | **TFE `Entities` provenance** | RT `4d17950` (2020-09-23, Sultim, "ability to run TFE") adds 139 files with **no** header (137 contain no "copyright" string at all). CVK `c4f9322` (2022-05-10) has 139 files with the Croteam GPL-2.0 header. Of 136 common names, **90 are identical after removing the header** and 46 differ slightly (median similarity 0.999). Croteam-official contains **no** TFE `Entities` (only TSE `EntitiesMP`). The CVK header was therefore added downstream, with no Croteam commit showing it. DreamyCecil/SE1-ModSDK README (fetched 2026-11-27) states: "This repository contains code from Serious Sam SDK by Croteam released in 2001-2002" and "The license header isn't present because of a different license that the SDK was released under during that time" [DOC, third-party claim]. |

### R6. Croteam-official comparison (explicit answer) [EXP]

- **RT:** yes. `b408e88` (Croteam-official master) is an ancestor of `upstream/rt-main`. All 6,628 Croteam-official blobs are reachable from RT, so publishing RT republishes the whole Croteam-official history. Inherited items: G1 `SE1_10.gro`, G6 `.ifr`, B1 Bison/Flex, B2 help files, H1 `DSOUND.H`, H2 LightWave SDK, and the H4 pre-GPL "All rights reserved" blobs.
- **RT, not from Croteam:** the 1,810 blobs from Sultim's 350 commits, including the TFE `Entities` (H6), G7/G8 KTX2 files and G9b screenshots.
- **CVK:** separate lineage (no shared commits), but 2,988 CVK blobs are byte-identical to Croteam-official blobs, including `DSOUND.H`, all 51 LightWave SDK files, Bison/Flex and `.ifr`.
- **CVK items with no Croteam-official counterpart:** G2 `SE1_10b.gro`, G3 Demos, the retail-identical G4/G5 files, G9 screenshots, H3 and the TFE `Entities` (H6).
- **Does this change anything?** It does not establish redistribution rights by itself. ADR-0006 rule 4 says the same: "Public availability elsewhere does not establish redistribution rights." It does change the *quality* of the evidence for each item:
  - **Croteam-owned items that Croteam itself published** (G1, the H4 history, Croteam's own code). The copyright holder's own publication, and its README sentence that `SE1_10.GRO` lets you "freely use the engine", are evidence of *some* permission. That permission is undefined in scope: "use" is not "redistribute" or "modify", and no licence is attached. This is the best-evidenced category, but it is still needs-counsel (RD-007 Q5).
  - **Third-party items that Croteam republished** (Microsoft `DSOUND.H`, NewTek SDK). Croteam's publication cannot grant rights that Croteam may not hold. Their presence in the official repo is weak evidence.
  - **Items absent from Croteam-official** (CVK Demos, retail scripts and controls, `SE1_10b.gro`, TFE `Entities`, screenshots, KTX2). No Croteam publication covers them at all. Retail byte-identity (G2–G5) is positive evidence that they are **retail game data**, which the Classic EULA (RD-007 §7.1) says may not be distributed.

## Findings, risk and options

Options, as defined by the owner:

1. **Publish as-is.**
2. **Publish with a follow-up removal commit.** The blobs stay reachable in history, so **publishing still distributes them**. This option therefore does **not** satisfy ADR-0006 rule 4 for any item rated Medium or High.
3. **Publish a filtered history as a new, separate branch** (e.g. `import/cvk-filtered`, made with `git filter-repo --invert-paths --path …`). This is a rewrite of an *import*, not of any existing published ref.
4. **Do not publish; keep local.**

Attribution impact of option 3 [ASM, based on `git filter-repo` documented defaults]:

- **Preserved:** author and committer names, e-mails, dates and messages.
- **Changed:** every commit from the first one touching a removed path gets a new SHA. That is **446 of 449** RT commits (because `SE1_10.gro` arrives in `9d8b787`) and **309 of 311** CVK commits (because everything arrives in `c4f9322`).
- **Lost:**
  - Existing signatures on 4 RT and 95 CVK commits (`%G?` = `E`, i.e. signed).
  - Correspondence with upstream SHAs, unless the generated `commit-map` is published alongside.
  - Commits that touched only removed files are pruned unless `--prune-empty never` is used.
- **Mitigations:**
  - Publish the commit map.
  - Name the original upstream URLs and SHAs in the branch README.
  - Keep `LICENSE` and every remaining header untouched.
  - State in a NOTICE which paths were removed and why. GPLv2 §1/§2 notice duties stay intact, because only whole files are omitted and no file is modified.
- **Conflict with ADR-0006.** The ADR says removals happen "in normal, reviewable commits on top of the preserved history, never by rewriting it". Taken literally, option 3 needs an owner clarification or amendment of ADR-0006. Taken literally together with rule 4, ADR-0006 leaves **only option 4** for Medium/High items.
- **Option 5 (a variant I add for completeness).** Publish **no** upstream history. Publish only SSTRE's own commits, as patches or a branch, against pinned upstream URLs and SHAs. Users or CI fetch upstream directly from its original host. SSTRE then distributes none of the questionable blobs.

| ID | Finding | Branch | Risk | Evidence for rights | Evidence against / gap | Recommendation (owner decides) |
|---|---|---|---|---|---|---|
| G1 | `SE1_10.gro` (Croteam resources, 93% retail-identical) | RT | **High** (unclear scope) | Croteam published it in its official GPL repo; README: "allow you to freely use the engine" [DOC] | no licence attached; "use" ≠ redistribute; the assets are proprietary per secondary source (RD-007 §3.1); the EULA forbids distribution | **4** (or 3 excluding it); counsel Q5. Option 2 is insufficient |
| G2 | `SE1_10b.gro` (2 paths) | CVK | **High** | 92/105 entries also in Croteam's G1 | not in Croteam-official; 13 entries of unknown origin | **4** or 3 |
| G3 | Demo recordings and thumbnails (34 files, 32 retail-identical) | CVK | **High** | none found | retail game data, not in Croteam's release | **4** or 3 |
| G4 | Retail-identical `Scripts`/`Controls`/`Help`/`Data` (185 files) and 73 edited/new ones | CVK | **Medium** | small functional config files; 18 counterparts exist in Croteam-official | retail game files not covered by a Croteam publication | **3** (exclude the retail-identical files; keep new tx00100xt files) or 4 |
| G5 | Mod thumbnails (`XPLUSTbn.tex` etc.) | CVK | **Medium** | — | provenance unstated; possibly derived from game art [ASM] | 3 or 4 |
| G6 | `.ifr` force-feedback data | both | Low–Medium | in Croteam-official | Immersion data format; authorship of the effects unstated | 1 (follows the G1/Croteam evidence class); flag in register |
| G7 | BlueNoise KTX2 | RT | Low | same blob ships in RTGL1 (MIT) | the source of the noise data is not credited [ASM: Christoph Peters' free blue-noise set] | 1; note in NOTICE |
| G8 | WaterNormal KTX2 | RT | **Medium** | — | no provenance | 3 or ask the author (Sultim) |
| G9/G9b | Screenshots (14 paths, 23 blobs, 54 MB) | both | **Medium** (ADR-0006 rule 4 lists "derivatives" of game assets) | customary in fan READMEs (precedent ≠ permission) | rendered Croteam assets | 3 (exclude) or 4 |
| B1 | Bison/Flex `.exe` + source zips | both | Low (legal); supply-chain concern | GPL tools; sources and `COPYING` alongside; in Croteam-official | binary provenance not reproducible | 1 or 2 (the owner may prefer 3 for hygiene); never run them |
| B2–B4 | `.aps`, MFC help templates, `.spv`, skeletons, icons | both | Low | Croteam-official or generated from in-repo source | MFC `AfxCore.rtf` is Microsoft AppWizard boilerplate [ASM] | 1 |
| H1 | `DSOUND.H` (Microsoft, ARR) | both | **Medium** | in Croteam-official; the DirectX SDK header was publicly distributed [ASM] | ARR; no redistribution terms in the repo; Croteam cannot grant Microsoft's rights | 3 (exclude and use the Windows SDK system header in an SSTRE commit) or 4; option 2 still distributes it. Counsel Q9 |
| H2 | LightWave SDK (53 files) | both | **Medium** | in Croteam-official, declared non-GPL | no licence text at all | 3 (exclude; the exporter is not needed) or 4. Counsel Q9 |
| H3 | 43 CVK files with "Croteam … All rights reserved" only | CVK | Low–Medium | Croteam code inside a GPL-licensed repo; README GPL statement | the header grants nothing; downstream origin (single squashed import) | 1 (preserve notices verbatim); record in register |
| H4 | 2,946 pre-GPL Croteam versions and 88 zcaliptium ARR files in RT history | RT | Low | Croteam's own history; GPL header added the same day; README GPL grant | the literal ARR text in old blobs | 1 (inherent to Croteam's public history) |
| H5 | GPL-or-later and Bison exception files | both | Low | compatible | — | 1 |
| H6 | **TFE `Entities`** (RT 132 headerless; CVK 139 with a downstream-added GPL header, ×2 trees) | both | **High** (provenance) | Croteam GPL'd SE 1.10; CVK carries a GPL header; long public availability (≠ rights) | absent from Croteam-official; third-party statement that it comes from the 2001–2002 SDK "under a different license"; the CVK header was added without a traceable Croteam act | **4** until Croteam/Devolver confirm in writing (Q4). Option 3 removes TFE support, which conflicts with the owner's "keep TFE and TSE" |
| — | Other no-header files (RT 62, CVK 80 excluding Entities) | both | Low | mostly Croteam-official files or permissive vendored code | — | 1 |

**Overall [ASM, recommendation]:**

- **Do not publish either upstream branch as-is.** Both reach at least one High item: RT has G1 and H6, CVK has G2, G3 and H6.
- Option 2 cannot cure that, because the blobs stay reachable.
- The viable routes are option 4, which keeps today's state and is what the pre-push hook enforces, or option 5.
- Option 3 is possible only after the owner clarifies ADR-0006. Even then, H6 would have to stay out until Q4 is answered, which would disable TFE in the published copy.

## Deviations, modifications and failures

- No branch, ref, hook or working tree was modified. `git status` in SSTRE-Engine was clean after the run.
- The game-data blobs `SE1_10.gro` and `SE1_10b.gro` were extracted to `local-work\audit\blobs\` for entry listing. They were deleted after the run.
- First script run failed: `--format=@@` is an invalid pretty format in Git 2.55. It was replaced by `%x40%x40`.
- Header classification is a heuristic, covering the first 3,000 bytes. For example, "Immersion" matched a variable name and was discarded by manual review.
- The retail comparison covers only the Classic TFE/TSE Steam installs. A file that is "not retail-identical" may still be game-derived.

## Interpretation

- [SRC] Every questionable item that Croteam itself published (G1, B1, B2, H1, H2, H4) reaches RT through Croteam's own history. Every item with retail identity and no Croteam counterpart (G2–G5) entered CVK in a single squashed commit, `c4f9322`, so CVK history gives no finer provenance.
- [ASM] The CVK items are probably copied from a retail install to make the repo run out of the box. The CVK README itself tells users to copy game directories (`README.md` l.420).
- [ASM] None of this is a legal conclusion. Risk ratings reflect evidence quality and ADR-0006 rule 4, not a legal judgment.

## Impact on ADRs, dossiers and backlog

- ADR-0006: needs an owner clarification. "Never rewrite" plus rule 4 makes option 4 or 5 the only compliant routes for High/Medium items. If option 3 is wanted, the ADR should say that a *new* filtered import branch is permitted.
- RD-007 §16: new questions Q15–Q23 added and statuses set (see that file).
- The pre-push hook stays as it is.
- Backlog suggestion: add an item for "publication route for engine upstream (option 4/5/3)". GATE-05 is unaffected.

## Owner decision (2026-11-27)

The owner chose **option 5**: publish only SSTRE's own patches against pinned upstream commits. This is the provisional official distribution strategy for SSTRE-Engine, recorded in [ADR-0008](../adr/0008-engine-patch-distribution.md). The upstream branches stay local behind the pre-push hook. Binary distribution remains blocked (ADR-0006 rule 6).

## Open questions

1. Owner: choose between option 4 (status quo), option 5 (patch-only publication against upstream) and option 3 (filtered import branch, which needs an ADR-0006 clarification).
2. Counsel / Croteam: G1 scope (Q5), TFE entities (Q4), `DSOUND.H` and the LightWave SDK (Q9), retail data in CVK (Q15); publication route (Q16); screenshots (Q17); WaterNormal/blue-noise (Q21).
3. Sultim: provenance of `WaterNormal_n.ktx2` and the blue-noise source.
