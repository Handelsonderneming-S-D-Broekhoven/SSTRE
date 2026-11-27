# EXP-010: Patch-series tooling (POC-27) and compile-time disable of master-server communication (POC-32)

| Field | Value |
|---|---|
| Date | 2026-11-27 |
| Backlog items | POC-27 (ADR-0008 tooling), POC-32 (master-server switch) |
| Status | **complete** for both items. Open points are listed under "Open questions" |
| Environment | Windows 11 Pro 10.0.22631, Git 2.55.0.windows.3, Python 3.10.11 (stdlib only). VS 2022 17.5 / MSVC v143, Windows SDK 10.0.22000.0, WinFlexBison 2.5.25, Vulkan SDK 1.4.363.0. Docker 20.10.23. Linux build container `ubuntu:22.04@sha256:b000e69a50ff940390233025e7a337fb8469b509e2334fa4d018ac30f3e18cdb` (as in EXP-001). Network-audit image `sstre-e2-netaudit:local` (`sha256:1118823a5fa2…`, `FROM` the same digest, plus runtime libraries, `tcpdump`, `strace`, `iproute2`) |
| Inputs | Pins from SSTRE-Engine `upstream.lock.json`: classic-vk `510d36f9…`, serious-engine-rt `0e7f223c…`, rtgl1 `b1eb3d8c…` (tag `v1.1.0`). Local branches `phase1/cvk-build` (6 commits), `phase1/rt-build` (7), RTGL1 `phase1/rtgl1-v1.1.0-sdk1.4` (1), and RTGL1 `sprint2/ktx2-cleanroom` @ `0eb4c4a` (7, by track K). New branch `sprint2/no-master-server`. Branch `phase1/no-ktx` was **not** exported (licensing hold). User-owned Steam Classic TFE/TSE data, used only for the dedicated-server runs |

Scratch and logs stay local in `G:\sstre-tmp\engine\patchtool\` (`logs/`, `linux/`, `netaudit/out/`).

## Goal and success criteria

1. **POC-27.** A small, documented, stdlib-only tool with `fetch`, `apply`, `export`, `check` and a round-trip test. The test is the POC-27 acceptance: export, then a fresh apply on clean upstream, must give **the same tree hash** as the source branch. The tool needs synthetic unit tests and a CI job. RayTracedGL1 is added to the lock with a new role `dependency`.
2. **Part B.** Export the existing build-fix series and round-trip verify each one.
3. **POC-32.** A compile-time option, off by default in SSTRE builds, that removes master-server heartbeat and enumeration traffic for TFE and TSE, in both the client and the dedicated server, and keeps LAN play. The option must build on Windows and Linux. A dedicated server on an isolated network must show **no** packet or connection attempt to a non-local host, and no DNS query for the master host.

All criteria are met.

## Procedure (exact, reproducible)

### Tool

- Code: SSTRE-Engine `tools/sstre_patches.py`. Tests: `tools/tests/test_sstre_patches.py`. Documentation: `docs/sstre/patch-tooling.md`. CI: `.github/workflows/sstre-patches.yml`.
- Key design choices (details in the documentation):
  - **Config isolation.** Local git calls use `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL=<devnull>`, plus `-c core.autocrlf=false` and related overrides. The system `core.autocrlf=true` on this PC otherwise breaks `git am`, as observed in a first trial.
  - **fetch** creates a bare cache per upstream. It fetches only the pinned SHA, at `--depth 1`, into `refs/sstre/pinned/<name>`. It then checks the object type, that the tree is complete (`rev-list --objects --missing=error --no-walk`) and that the `swhid` is consistent with the commit. `--offline` together with `--source NAME=PATH` uses a local clone. `--check-swh` compares the Software Heritage directory with the git tree.
  - **export** runs `git format-patch --zero-commit --no-signature --full-index --no-numbered --stat=72 --filename-max-length=64 --find-renames --diff-algorithm=myers --irreversible-delete --base=<pin>`. The branch must be a linear chain on top of the pin. The series is checked in a temporary directory first and replaces `patches/<name>/` only if the check passes. A trailer audit rejects any trailer that is not in the source commit.
  - **apply** runs `git worktree add --detach` at the pin, then `git am --keep-cr --no-3way --committer-date-is-author-date` **per patch**, with the fixed committer `SSTRE patch tool`. Content-free deletions (`--irreversible-delete`) cannot be applied by plain `git am`, which reports "removal patch leaves file contents". The tool therefore re-creates each such deletion with `git diff-tree` from the blob in the pinned tree, and refuses to apply if the blob ID in the patch differs from the file at that point.
  - **check** enforces the ADR-0008 rules. They are listed in the documentation and covered by the tests. The forbidden-extension list is a copy of the umbrella validator's list. The umbrella validator is GPL-3.0-only and the engine tool is GPL-2.0-only, so the tool reads `--validator` as data through `ast` and never imports it. A test and the CI job compare the two lists.
- Commands for Part B (Git Bash, `SSTRE_UPSTREAM_CACHE=G:\sstre-tmp\engine\upstream-cache`):

  ```sh
  python tools/sstre_patches.py fetch --offline --source classic-vk=<SSTRE-Engine> \
         --source serious-engine-rt=<SSTRE-Engine> --source rtgl1=<upstream>/sultim-t_RayTracedGL1
  python tools/sstre_patches.py export classic-vk --from phase1/cvk-build --source-repo <SSTRE-Engine> --verify
  python tools/sstre_patches.py export classic-vk --from sprint2/no-master-server --source-repo <SSTRE-Engine> --verify
  python tools/sstre_patches.py export serious-engine-rt --from phase1/rt-build --source-repo <SSTRE-Engine> --verify
  python tools/sstre_patches.py export rtgl1 --from sprint2/ktx2-cleanroom --source-repo <RTGL1 clone> --max-patch-kib 1280 --verify
  python tools/sstre_patches.py --cache <fresh> fetch --check-swh     # online, from GitHub
  python tools/sstre_patches.py --cache <fresh> apply --out <dir> --force
  SSTRE_UMBRELLA_VALIDATOR=<umbrella>/scripts/validate_repo.py python -m unittest discover -s tools/tests
  ```

### POC-32

1. [SRC] Source reading at `510d36f`. TFE and TSE `Engine/GameAgent/` are byte-identical (`diff -r`). The findings below are for `SamTFE/Sources/`:
   - Master hosts: `ga_strServer` and `ga_strMSLegacy` default to `"sam.ostap.eu"` (`Engine/GameAgent/GameAgent.cpp:182-184`).
   - `_initializeWinsock()` resolves the master host with `gethostbyname` (`:304-321`). It is called by **every** GameAgent entry point, including LAN enumeration.
   - Heartbeats are sent from `GameAgent_ServerInit` (`:492`), from a periodic 150 s timer in `GameAgent_ServerUpdate` (`:803`), from `GameAgent_ServerStateChanged` (`:809`) and from `GameAgent_ServerEnd` (`:516`).
   - Internet enumeration (`GameAgent_EnumTrigger`, `:832`) opens a TCP connection to the master on port 28900, then queries the listed servers in `_MS_Thread`.
   - Call sites: `Engine/Network/Server.cpp:211,283,1322` and `Engine/Network/Network.cpp:1240,1976,2446`.
   - `ser_bEnumeration` is read only in commented-out code (`Network.cpp:2470-2485`) and in the menu. This explains EXP-001's finding that setting it to 0 does not stop the heartbeat.
2. Change: one commit on `sprint2/no-master-server`, made from `phase1/cvk-build` in worktree `G:\sstre-tmp\engine\wt-nomaster`, applied identically to the TFE and TSE trees:
   - **Build option.** `SSTRE_MASTER_SERVER` is a CMake `option(... OFF)` in `SamT?E/Sources/CMakeLists.txt` that adds `-DSSTRE_MASTER_SERVER=0/1`. A source fallback `#ifndef SSTRE_MASTER_SERVER → 0` makes the unmodified MSVC projects default to "disabled".
   - **Behaviour with the value 0:**
     - no master resolution (`_sin = NULL`);
     - `_sendPacketTo(NULL)` is a no-op;
     - no heartbeat in `ServerInit`, from the periodic timer, in `ServerStateChanged` or in `ServerEnd`;
     - `EnumTrigger` returns, with a console message, for internet enumeration and for the non-legacy protocol;
     - the default master host strings are empty.
   - **Kept:**
     - the server binds `net_iPort+1` and answers LAN `\status\` queries;
     - LAN enumeration;
     - direct-IP join (`CommunicationInterface` is unchanged).
   - The new block carries a GPL-2.0-only SSTRE modification notice. Upstream headers are untouched.
3. Windows: `MSBuild <SamT?E>.sln /m /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=v143 /p:WindowsTargetPlatformVersion=10.0.22000.0 /p:UseOfMfc=false`, with the EXP-001 runtime targets (`…:Rebuild`), trusted WinFlexBison first on `PATH`, and the outputs in the G: worktree.
4. Linux: `git -c core.autocrlf=false archive HEAD`, then the EXP-001 container build script, unchanged (`cmake` default targets, TFE + TSE).
5. Network audit. Isolated user-defined bridge: `docker network create --internal --subnet 10.231.7.0/24 sstre-e2-iso`. The network is enabled but has no external route, and it was removed afterwards.
   - **Container setup.** Each run uses `--cap-add SYS_PTRACE --cap-add NET_RAW` and mounts a `resolv.conf` with `nameserver 10.231.7.53`, a non-existent host on the isolated subnet. Any DNS lookup therefore becomes a visible attempt to a non-local address and cannot leave the network.
   - **Script.** The script starts `tcpdump -i any -nn -U -p -w cap.pcap`. It records `ss -tunap` every 2 s. It runs `timeout 40 strace -f -e trace=connect,sendto,sendmsg,sendmmsg,bind ./DedicatedServer SSTRE` with the master cvars **left at their compiled-in defaults**.
   - **Runs.** TFE first level, TSE first level, and the **unmodified** EXP-001 Linux build as a positive control. A variant adds `--add-host sam.ostap.eu:10.231.7.99`, so that the heartbeat itself becomes observable. In the LAN probe, a second container on the same network sends `\status\` to the patched server's port 25601.

## Results ([EXP] unless labelled otherwise)

### POC-27: tests and round trips

- Unit tests: **32 tests, all pass** (`Ran 32 tests in 56.9s, OK`, Windows, with the umbrella validator list comparison enabled). They cover:
  - 18 check-rule tests: binary patches, forbidden extensions and paths, flagged files, full-content versus content-free deletions, Signed-off-by, size, headers, numbering, submodules and symlinks, quoted paths, SPDX warning, validator lists read as data;
  - 2 lock tests;
  - 12 git round-trip tests: offline fetch, cache hit, missing commit, export/apply round trip with CRLF content, a rename and an exec bit, byte-identical re-export, mismatch detection, merge and orphan rejection, a forbidden change that leaves the series untouched, the Signed-off-by gate, irreversible deletes of CRLF, binary, no-EOL and flagged files, and a tampered blob ID.
- Workflow YAML parses, and every `uses:` is pinned by a 40-hex SHA. The umbrella validator on SSTRE-Engine with the allowlist reports 0 errors and 0 warnings.

| Series | Source branch | Patches | Round trip: applied tree = source tree | Applied HEAD (reproducible) |
|---|---|---|---|---|
| classic-vk (build fixes only) | `phase1/cvk-build` | 6 | `b47468128684b5532fa2715271ee8bdd1003bb86` ✔ | `4ae492c9f2da…` |
| **classic-vk (committed)** | `sprint2/no-master-server` | 7 | `62aa4840ce335c8b5a6d630f669650485f2ad488` ✔ | `5b3651ef17b8…` |
| **serious-engine-rt** | `phase1/rt-build` | 7 | `5d5c86a9d71ce4da6e3056a606b59ee5776f01f5` ✔ | `80f98ace3000…` |
| rtgl1 (shader fix only, superseded) | `phase1/rtgl1-v1.1.0-sdk1.4` | 1 | `191c6acda2972c106b54b9a7266e9a02c479da01` ✔ | `253e60178168…` |
| **rtgl1 (committed)** | `sprint2/ktx2-cleanroom` @ `0eb4c4a` | 7 (73 deletions re-expanded) | `aec117aa6b1b3ad72dac004034fc5172a326348b` ✔ | `7124442e0044…` |

- **Online path.** `fetch --check-swh` from GitHub into an empty cache took 12.8 s for all three pins at depth 1. The three Software Heritage directories equal the git trees (`d58effb4…`, `5e284d53…`, `b1452ee1…`). A subsequent `apply` (28.8 s) produced **the same HEAD SHAs** as the offline runs, which means the applied commits are reproducible across sources.
- **Determinism.** Re-exporting classic-vk and serious-engine-rt after adding `--irreversible-delete` gave SHA-256-identical files (no deletions in those series). The unit test also checks byte identity.
- **rtgl1 `0006-Remove-the-libktx-sources`.** 18.9 KB, 73 `deleted file mode` sections, **no** removed content lines. The Apache-2.0 KTX sources are not reproduced.
- **RayTracedGL1 in the lock.** `b1eb3d8ca3fe75f6f4dda16a53aeb99ea613aead` (`git rev-parse v1.1.0^{commit}`), role `dependency`, `tag_hint` `v1.1.0`, MIT (EXP-003). SWHID `swh:1:rev:b1eb3d8c…`: the SWH API returns the revision with directory `b1452ee1…`, equal to `v1.1.0^{tree}`.
- **Umbrella schema.**
  - `role` enum += `dependency`, new optional `tag_hint`. `schema_version` stays `0.1` (a backward-compatible addition).
  - The new real lock is copied as the valid test case. New negative test `invalid/bad-tag-hint.json`.
  - `scripts/validate_repo.py`: **0 errors, 0 warnings** (3 valid and 26 invalid schema-test documents).

`check` findings on the committed series (with `--max-patch-kib 1280`): **0 errors, 7 warnings.**

- `serious-engine-rt/0004` removes 1,539 lines of the committed Bison output `Sources/Engine/Base/Parser.cpp`, and the patch is 173 KB. The commit regenerates committed generated files: `Parser.cpp`, `parser.h`, `smcpars.h` and `Ecc/parser.h`.
- `rtgl1/0003` (vendored zstd 1.5.7) adds 6 files without an SPDX header. It is **1,135 KiB**, above the default 1,024 KiB limit, so the CI passes `--max-patch-kib 1280` with a comment.

### POC-32: builds

| Build | Result |
|---|---|
| Windows x64 Release, TFE runtime targets (rebuild) | **pass**, exit 0, 279 s. The only GameAgent warnings are the pre-existing C4267/C4101 (line numbers shifted) |
| Windows x64 Release, TSE runtime targets (rebuild) | **pass**, exit 0, 146 s |
| Linux x64 (Docker, pinned digest), TFE + TSE | **pass**, 80 s, same 20 output files as in EXP-001 |
| String check | `sam.ostap.eu` occurs **0** times in the patched `Engine.dll` (TFE, TSE), `libEngine.so` and `libEngineMP.so`, and once in the unmodified EXP-001 `libEngine.so`/`libEngineMP.so`. The "master server disabled at compile time" message is present in all four patched libraries |

### POC-32: dedicated-server network audit (Linux, isolated bridge, 40 s each)

| Run | Server | Non-loopback packets from the server | strace connect/send to non-loopback | DNS query for master | "Send heartbeat" |
|---|---|---|---|---|---|
| patched TFE (`01_Hatshepsut`) | `started.`, "ALL OK" | **0** | **0** | **none** | 0 |
| patched TSE (`1_0_InTheLastEpisode`) | started | **0** | **0** | **none** | 0 |
| patched TSE + `--add-host sam.ostap.eu` | started | **0** | **0** | none | 0 |
| **control**: unmodified TFE | started | 7 (ARP for 10.231.7.53 ×6, ICMP unreachable) | 1: `connect(…, 10.231.7.53:53)` + `sendto("…sam\5ostap\2eu…")` | **yes** | 2 (then "Couldn't resolve GameAgent server sam.ostap.eu.") |
| **control**: unmodified TFE + `--add-host` | started | 13 (ARP for 10.231.7.99, …) | 2: `sendto("\heartbeat\25601\gamename\serioussam…", 10.231.7.99:27900)` at start and `statechanged` at shutdown | (hosts file) | 2 |

- The only other packets captured in the patched runs are 2–3 kernel IPv6 router solicitations (`fe80::… > ff02::2`, link-local multicast from the interface, not from the game).
- `ss` shows the server bound only to `0.0.0.0:25600` (game) and `:25601` (GameAgent LAN queries). No connected sockets.
- **LAN kept.** In the LAN-probe run, the patched server answered a `\status\` query from 10.231.7.20 with a 447-byte reply (`\gamename\serioussam\gamever\1.10\…\mapname\Hatshepsut\…\dedicatedserver\yes…`, captured by tcpdump). Its only non-loopback `sendto` was that reply, to the LAN peer.
- **Not tested** [ASM]:
  - the client side at runtime, which needs a game window;
  - internet-list menu behaviour;
  - LAN enumeration from a real client;
  - direct-IP join.

  The client code paths are covered by the same `#if` guards ([SRC] diff in `classic-vk/0007`).

## Deviations, modifications and failures

- **Lead instruction mid-task.** The lead asked for `--irreversible-delete`, a check rule against full deletion content, and the rtgl1 series from `sprint2/ktx2-cleanroom` in place of the shader fix alone. All three are implemented. The shader-only round trip above is kept for the record.
- **Failed trials.**
  - `git am` on CRLF content in a worktree checked out under the system `core.autocrlf=true` fails with "does not match index". Fixed by config isolation and `core.autocrlf=false` in the cache repos.
  - Plain `git am` rejects irreversible deletions ("removal patch leaves file contents"). Fixed by the expansion step.
- **Network-audit artefact.** Two containers ran concurrently on the same bridge, and the patched run captured the control run's broadcast ARP. That run was discarded and repeated alone (table above).
- **LAN-probe script.** The bash `/dev/udp` read printed nothing (a timing issue). The reply is evidenced by tcpdump and strace instead.
- `--check-swh` and `--offline` are mutually exclusive (decision: offline means no network at all).

## Interpretation

- [EXP] POC-27 acceptance holds for every series: the published patches plus the public pinned upstream reproduce the local branch trees exactly, online and offline. Applied commit IDs are reproducible, because the committer is fixed and the committer date equals the author date.
- [ASM] ADR-0008 says the series is "applied in order with `git am`". With `--irreversible-delete`, a plain `git am` no longer works for series that delete files (currently only rtgl1). Users must apply with the tool. ADR-0008 item 2 should say so.
- [SRC]/[EXP] POC-32: with `SSTRE_MASTER_SERVER=0` the dedicated server performs no master DNS lookup and sends no heartbeat, even when the host would resolve. The positive controls show that the same harness detects both behaviours in the unmodified build.

## Impact on ADRs, dossiers and backlog

- ADR-0008 item 1: roles are now `primary`/`secondary`/`dependency`. Item 2: "apply with `tools/sstre_patches.py`" (irreversible deletions). Item 4: the rules are now enforced by CI (`sstre-patches.yml`).
- Backlog: POC-27 done. POC-32 done for the dedicated server on Linux; the client runtime check is open.
- EXP-001 open question 4 is answered (compile-time switch, default off).

## Open questions

1. Owner/lead:
   - `serious-engine-rt/0004` republishes regenerated Bison output (GPL-3.0-or-later with the Bison exception): about 4,000 changed lines of generated code. Keep it, or rewrite the commit so that the build regenerates these files and the patch does not carry them?
   - `rtgl1/0003` vendors third-party zstd (BSD-3-Clause OR GPL-2.0) inside a patch, and `rtgl1/0001` is a backport of an upstream commit by Friedrich Vock. ADR-0008 says patches contain "only changes authored by SSTRE contributors". Accept these as documented exceptions? Is the raised 1,280 KiB limit acceptable?
2. SSTRE-Engine `README.md` still says "Contributions use the Developer Certificate of Origin (`git commit -s`)", which conflicts with the "never add Signed-off-by" rule. Not changed here.
