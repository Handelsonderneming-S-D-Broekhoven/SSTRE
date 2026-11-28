# RD-009: Native PlayStation 5 homebrew port (research only)

| Field | Value |
|---|---|
| Dossier | RD-009 |
| Author | Track DOC-R (roadmap/planning), 2026-11-28 |
| Date | 2026-11-28 |
| Status | **Draft, research only.** Desk research from public secondary sources. No console, exploit, homebrew toolchain, Sony SDK or NDA material was obtained, downloaded or used. **Not legal advice.** Nothing here authorizes work on a PS5 build. |
| Feeds | [ADR-0007](../adr/0007-platform-strategy.md) review (consoles stay a research objective); backlog POC-63 |
| Related | [RD-006 platforms](./RD-006-platforms.md) §3.5, [RD-007 licensing](./RD-007-licensing.md) Q14/Q19, [RD-010 homebrew distribution](./RD-010-homebrew-distribution.md), [RD-012 input](./RD-012-input-local-multiplayer.md) |

## 1. Question and scope

The owner directive asks for a dossier on a native PS5 homebrew port. It sits last in the priority order (Console Ports) and, under ADR-0007, consoles are a research objective only. This dossier records:

1. what the public PS5 homebrew landscape looks like at the end of 2026;
2. what a "native port" of SSTRE would technically need;
3. why the legal questions block any project work, and which ones would have to be answered first.

It keeps RD-006's four questions apart: technical feasibility, official distribution, platform SDK licensing, game IP licensing.

## 2. Evidence

All sources are public. Secondary press is marked as such; details conflict between outlets.

| ID | Source | Note |
|---|---|---|
| S1 | `ps5-payload-dev/sdk`, https://github.com/ps5-payload-dev/sdk (fetched 2026-11-28) | community SDK "for PS5 payloads that uses dynamic linking", for "exploited PS5s"; GPLv3+ except BSD-licensed FreeBSD headers; can build stubs from **user-supplied decrypted system modules** (`sce_stubs`) |
| S2 | `PS5Dev/PS5SDK`, https://github.com/PS5Dev/PS5SDK | older community SDK (CMake toolchain); not read in detail |
| S3 | GamingOnLinux, "PlayStation 5 Linux project expands to support more 7.0 firmware", 2026-09-07, https://www.gamingonlinux.com/2026/09/playstation-5-linux-project-expands-to-support-more-7-0-firmware/ | secondary: a PS5 Linux loader "leverages patched HV vulnerabilities"; Phat and Slim; firmware 3.00–7.61 per the project description |
| S4 | Tom's Hardware, "PS5 Linux loader goes public…", https://www.tomshardware.com/software/linux/ps5-linux-loadr-goes-public-turning-phat-consoles-into-full-linux-pcs | secondary; only the headline was readable |
| S5 | Phoronix, "Mesa & AMDGPU Linux Driver See Patches For The Sony PS5 GPU", https://phoronix.com/news/mesa-amdgpu-ps5-patches | secondary; fetch refused (HTTP 403); search summary only: kernel `amdgpu` and Mesa patches for the PS5 GPU, March 2026 |
| S6 | RD-006 P9/P10/P25 (official partner programme; Defold PS5 support private; exploit chains on older firmware) | [DOC] via RD-006 |
| S7 | RD-007 Q14 (SDK NDA vs GPL), Q19 (circumvention/homebrew legality) | open, needs counsel |

## 3. Observed facts

- [DOC] S1/S6: PS5 homebrew runs only on consoles where a firmware or hypervisor vulnerability has been exploited. Sony patches these in later firmware; homebrew is limited to consoles that stayed on old firmware.
- [DOC] S1: the community payload SDK is free software (GPLv3+). Access to system functions beyond its own libc goes through stubs generated from the user's decrypted firmware modules, i.e. Sony's proprietary system libraries. Graphics through the native PS5 API would depend on those libraries; no open, documented PS5 graphics API exists [ASM: none found in public sources].
- [DOC, secondary] S3/S4/S5: a separate route boots **Linux** on exploited consoles. Press reports mention desktop and Steam use; kernel and Mesa patches for the PS5 GPU were posted in 2026. Whether Vulkan ray tracing works there is **unknown** (no source found).
- [DOC] S6: the official route (PlayStation Partners, GDPA, devkits) requires a registered developer and NDA; the SDK is confidential, and open-source engines keep their PS5 code private.
- [SRC] RD-006 §3.1: no SSTRE engine source contains PS5 platform code.

## 4. What a native port would need (technical, hypothetical)

| Layer | Requirement | Status |
|---|---|---|
| Toolchain | clang/lld cross-compile to the PS5 ELF/payload format | exists in community SDKs (S1, S2) |
| OS services | files, threads, timers, sockets for the SE1 platform layer | partly via community libc; rest via proprietary-module stubs |
| Graphics | a renderer for the PS5 GPU | no open API; would need proprietary libraries (native route) or the Linux route (Mesa) |
| RT | RTGL1 needs Vulkan `VK_KHR_ray_tracing_pipeline` | not available natively; under Linux unknown |
| Input | controller via platform input API | RD-012 adapter interface would be reused |
| Assets | user-owned game data on the console | needs a transfer path from the user's PC purchase; RD-006 §3.3 notes consoles do not normally allow this |

## 5. Assumptions and unknowns

- U1: legality of developing, documenting or supporting homebrew that needs circumvention in the owner's jurisdiction (NL/EU, 2001/29/EC art. 6) and for users elsewhere (US DMCA §1201). RD-007 Q19, needs counsel.
- U2: whether linking GPL-2.0-only engine code against stubs of proprietary system modules is distributable at all. Likely not (no system-library exception for code shipped by the distributor) [ASM]; RD-007 Q14-adjacent.
- U3: whether the "Linux on PS5" route makes this a Linux port in all but name. Technically the SSTRE Linux raster build might run; the circumvention question (U1) is unchanged.
- U4: performance of the PS5 GPU for RTGL1 path tracing under Mesa, if RT is exposed at all.

## 6. Risks

| Risk | Impact | Note |
|---|---|---|
| Legal exposure from circumvention (project and owner) | high | P24 in RD-006 shows enforcement in the Switch scene |
| Proprietary material entering the repositories (stubs, headers, firmware-derived files) | high | violates RD-007/ADR-0006 boundaries |
| Reputational risk with the IP holder | high | could close the path to any licence (GATE-04) |
| Effort diverted from PC | medium | ADR-0007: consoles must not block PC |

## 7. Proposed experiment

None that touches hardware. Allowed desk work only (POC-63):

1. Track public status twice a year (firmware coverage, Mesa RT status) and update §3.
2. Keep the engine's platform layer and the input/render interfaces portable (RD-012 §5), which helps any future authorized port.
3. Ask counsel RD-007 Q19 and Q14 before any change of policy.

Success criterion: the dossier stays current; no proprietary material or exploit code enters any SSTRE repository (existing leak scans and review).

## 8. Recommendation

**Do not pursue a PS5 homebrew build.** Keep RD-009 as research only, consistent with ADR-0007 and RD-007 Q19 ("not pursued" pending counsel). Invest instead in portability that also serves an authorized route: the platform-neutral input interface, a clean platform layer and the raster baseline. Revisit only if counsel answers Q19/Q14 favourably **and** the owner approves a scope, or if an authorized route (IP-holder licence plus platform agreement, GATE-04) appears.

## 9. Decision dependencies

- RD-007 Q19 and Q14 (counsel).
- GATE-04 (rights-holder approach).
- Owner: whether a real PS5 homebrew target is wanted beyond research (this dossier recommends no).

## 10. Next steps

POC-63 (desk tracking) in the [backlog](../backlog.md#stage-m6--console-ports-research-only).
