# RD-010: Homebrew distribution

| Field | Value |
|---|---|
| Dossier | RD-010 |
| Author | Track DOC-R (roadmap/planning), 2026-11-28 |
| Date | 2026-11-28 |
| Status | **Draft, research only.** Desk research. **Not legal advice.** No release, upload or store submission was made, and none is proposed here. |
| Feeds | [ADR-0007](../adr/0007-platform-strategy.md) review; RD-008 §11 release format; backlog POC-63 |
| Related | [RD-006 platforms](./RD-006-platforms.md), [RD-007 licensing](./RD-007-licensing.md), [RD-008 testing/release](./RD-008-testing-release.md), [RD-009 PS5 homebrew](./RD-009-ps5-homebrew.md), [ADR-0002](../adr/0002-local-user-supplied-assets.md), [ADR-0008](../adr/0008-engine-patch-distribution.md) |

## 1. Question and scope

"Homebrew distribution" here means distributing SSTRE outside official stores, to users who supply their own game data. Questions:

1. What may SSTRE distribute at all, today and once the open licensing questions are answered?
2. Which channels fit a GPL engine that needs user-owned data (PC, Linux, Steam Deck)?
3. What would console homebrew distribution involve, and why is it out of scope?

## 2. Evidence

| ID | Source | Note |
|---|---|---|
| D1 | Flathub listing `io.itch.tx00100xt.SeriousSamClassic`, https://flathub.org/apps/io.itch.tx00100xt.SeriousSamClassic (search summary, 2026-11-28) | an SE1 engine (the Classic-VK author's) is distributed on Flathub without game data; users must own and supply TFE/TSE data |
| D2 | Snapcraft `serioussam`, https://snapcraft.io/serioussam (search summary) | same pattern: "only provides the engine, you need a valid copy of the (proprietary) game data" |
| D3 | RD-006 P21/P22/P23 (Steamworks terms on copyleft; Valve IP approvals; Steam Deck as an open PC) | [DOC] via RD-006 |
| D4 | RD-007 §5.3/§5.4 and Q1/Q3/Q4/Q6/Q12/Q18/Q19 | licensing blockers and open questions |
| D5 | ADR-0002 (user-supplied assets), ADR-0008 (engine published as own patches only), sprint-2 rule "no binaries distributed" | project policy |

## 3. Observed facts

- [DOC] D5: **today SSTRE distributes no binaries and no game-derived data.** GitHub carries code, patch series, tooling and documentation. Builds and asset packs stay local.
- [DOC] D4: binary distribution is blocked until counsel answers RD-007 Q1 (Apache-2.0 KTX in RTGL1; mitigated by the clean-room KTX2 reader, needs confirmation), Q3 (DLSS: never in a distributed build), Q4 (entity-code provenance), Q6 (local conversion of game data), and Q12 (project name/trademark).
- [DOC] D1/D2: other SE1 engine forks are distributed on Linux app stores as engine-only packages that require the user's own data. This shows a working pattern; it is not a legal clearance for SSTRE, whose RT backend and asset tooling add questions (D4).
- [DOC] D3: the Steam Deck needs no exploit; sideloading is supported. A Steam store page is a different question (rights warranty, Steamworks copyleft caution).
- [DOC] RD-009: console homebrew distribution presupposes circumvention on the user's console (RD-007 Q19) and is not pursued.

## 4. Channel options (if and when binaries are cleared)

| Channel | Fit | Obligations / issues |
|---|---|---|
| GitHub Releases (umbrella) | source archives, patch series, checksums; later engine binaries | GPL corresponding source for every binary (pinned patches + upstream commits, ADR-0008); notices (RD-007); signatures (RD-008 §11.4) |
| User-side builder | user builds engine and assets locally from pinned sources | avoids binary distribution entirely; heavier for users; already the plan's direction (RD-008 §11.3) |
| Flathub / AppImage (Linux, Deck) | engine-only package, data from the user | store policies; GPL source offer; no game data or derivatives |
| itch.io / mod sites | engine-only download | same; check site terms for "requires base game" content |
| Steam (own app or Workshop) | not recommended | rights warranty and copyleft caution (D3); IP-holder consent likely needed (RD-007 Q18) |
| Console homebrew stores/loaders | **out of scope** | circumvention (RD-007 Q19), proprietary stubs (RD-009 U2), IP |

## 5. Rules for any distribution (proposal)

1. No game assets, extracted assets, AI-enhanced derivatives, asset paths or hashes (ADR-0002, GATE-05).
2. No proprietary SDK code or binaries (DLSS/NGX, Steamworks, console SDKs, firmware-derived stubs).
3. Every binary has corresponding source at exact pins, reproducible build instructions, notices and checksums.
4. The unofficial-project disclaimer and trademark-safe naming (RD-007 Q12).
5. No telemetry or master-server contact by default (POC-32).

## 6. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Publishing a binary before Q1/Q3/Q4 are answered | high | release gate in RD-008 §5 phase 9; lead audit |
| Third parties repackaging builds with assets | medium | clear licence notices; no asset tooling output in releases |
| Console homebrew sites picking up the code | low | not within project control; the project does not support or link them |

## 7. Proposed experiment

Desk only: draft the GPL source-offer and notice set for a hypothetical engine-only Linux package and check it against RD-007 (part of POC-63). Success: a checklist the lead can apply at release time; no upload.

## 8. Recommendation

Keep the current policy: source, patches and tools only. Prefer the **user-side builder** as the first distribution form, then engine-only packages for Windows/Linux/Deck once counsel clears the RD-007 blockers. Do not use Steam store distribution or any console homebrew channel.

## 9. Decision dependencies

RD-007 Q1/Q3/Q4/Q6/Q12/Q18/Q19 (counsel); owner approval of any first binary release.

## 10. Next steps

POC-63 in the [backlog](../backlog.md#stage-m6--console-ports-research-only).
