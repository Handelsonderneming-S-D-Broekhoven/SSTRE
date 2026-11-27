# RD-006: Platform feasibility (PC, handheld, macOS, consoles)

> **Changelog**
> - 2026-11-27 (Phase 1, compliance auditor): added [§3.5](#35-legal-split-per-platform-four-separate-questions). It splits every console/handheld verdict into four separate questions, per owner direction and ADR-0007: technical homebrew feasibility, official distribution, platform SDK licensing, and game IP licensing. The single "blocked" verdicts in §3.2 and §8 are replaced by per-question verdicts. Added evidence P18–P25. Nothing else changed. Not legal advice.

| Field | Value |
|---|---|
| Dossier | RD-006 |
| Author | Agent D (renderer/platform researcher), Phase 0 |
| Date | 2026-11-27 |
| Status | **Draft.** Desk research only. No platform SDK was obtained, no NDA material was accessed, and nothing was built. Statements about NDA-gated content are marked **[NDA: inaccessible]**. |
| Feeds | ADR-0007 (platform strategy) |
| Related | [RD-005 rendering](./RD-005-rendering.md), [RD-001 engine baseline](./RD-001-engine-baseline.md), [RD-007 licensing](./RD-007-licensing.md), [RD-008 testing/release](./RD-008-testing-release.md) |

## 1. Question and scope

For each candidate platform, this dossier asks:

- What toolchain and graphics API would SSTRE need, and is ray tracing available?
- Which authorization path applies (developer programme, NDA, devkit)?
- Is there a concern about shipping GPL open-source code with that platform's SDK? This question is flagged for Agent E and not concluded here.
- Can an *unofficial* fan remaster of third-party IP get publishing authorization?
- Which texture formats are suitable?
- Is the platform viable, a research item, or blocked?

Platforms covered: Windows, Linux, Steam Deck/Proton, macOS, Xbox Series X|S, PS5, Switch / Switch 2, and PS Vita.

This is not legal advice. It draws no legal conclusions, and RD-007 / Agent E own the licensing analysis.

## 2. Evidence

| ID | Source (fetched 2026-11-27 unless noted) | What it supports |
|---|---|---|
| P1 | Upstream code: see [RD-005 §2](./RD-005-rendering.md#2-evidence) (RTGL1 `v1.1.0` = `b1eb3d8` and `hl1` = `2457acc`; SE-RT `0e7f223`; Classic-VK `510d36f`) | Engine and renderer OS support |
| P2 | MoltenVK Runtime User Guide, https://github.com/KhronosGroup/MoltenVK/blob/main/Docs/MoltenVK_Runtime_UserGuide.md | Layered Vulkan 1.4 implementation. Its supported-extension list does **not** include `VK_KHR_ray_tracing_pipeline`, `VK_KHR_ray_query` or `VK_KHR_acceleration_structure` |
| P3 | Microsoft, "GDC 2026: What's Changed in Xbox Development", https://developer.microsoft.com/games/articles/2026/03/gdc-2026-press-start-get-your-pc-game-ready-for-xbox-in-one-day/ | The GDK is public ("No NDA, no partner agreement" to install, through `winget install Microsoft.GDK`). Partner Center, sandboxes and Xbox services are unlocked after account verification **and NDA**. Publishing agreements are a separate track. |
| P4 | https://github.com/microsoft/GDK (public release repo) and the "Meet the Microsoft GDK" FAQ, https://developer.microsoft.com/en-us/games/articles/2021/07/meet-the-microsoft-game-developer-kit-gdk/ | The GDK is a binary release, not open source |
| P5 | Xbox devdocs graphics/ray-tracing pages, https://devdocs.xbox.com/build/core-features/graphics/newfeatures/raytracing. Seen only as search-result snippets; the direct fetch redirected to https://docs.xbox.com/ | "XDXR is the Xbox implementation of the DirectX Raytracing (DXR) API on Xbox Series X\|S"; "Direct3D 12 on Xbox" is the console graphics API. **No public evidence of Vulkan on Xbox consoles was found.** |
| P6 | Nintendo Developer Portal, https://developer.nintendo.com/ | Registration is open to individuals ("You can register even if you are an individual"). The page links to "Developing for Nintendo Switch 2". Technical details are behind the portal **[NDA: inaccessible]** |
| P7 | NVIDIA blog, https://blogs.nvidia.com/blog/nintendo-switch-2-leveled-up-with-nvidia-ai-powered-dlss-and-4k-gaming/ (seen as a search snippet) | Switch 2 has a "custom NVIDIA processor featuring an NVIDIA GPU with dedicated RT Cores and Tensor Cores" and DLSS |
| P8 | Khronos conformance reports from 2016, via secondary coverage, e.g. https://www.gamedeveloper.com/programming/nintendo-switch-to-support-vulkan-opengl-4-5-and-opengl-es. Primary list: https://www.khronos.org/conformance/adopters/conformant-products | The original Switch was listed as Vulkan 1.0 conformant. **No Switch 2 Khronos listing was found** in this search |
| P9 | PlayStation Partners, https://partners.playstation.net/ (the page content was not readable by the fetch tool). Sony "Complimentary PlayStation Development Hardware", https://sonyinteractive.com/en/news/blog/complimentary-development-hardware/ | Registration as a partner, the Global Developer and Publisher Agreement (GDPA), and devkits loaned subject to SIE terms |
| P10 | Defold manual, "Sony PlayStation", https://www.defold.com/llms/manuals/sony-playstation/ | An open-source engine's PS4/PS5 support "is not included in the standard version" due to licensing; source access "will only be provided to PS5 licensed game developers" |
| P11 | Godot Foundation, "About official console ports", https://godotengine.org/article/about-official-console-ports/ and https://godotengine.org/consoles | Console ports cannot be published as FOSS because of NDAs and paywalls; ports are distributed only to vendor-approved developers |
| P12 | NVIDIA RTX SDKs license (DLSS), https://github.com/NVIDIA/DLSS/blob/main/LICENSE.txt | §4e forbids subjecting the SDK to an open-source license. See RD-005 |
| P13 | Mesa RADV ray tracing on by default since Mesa 23.2: https://www.phoronix.com/news/RADV-RT-Default-Mesa-23.2 (secondary). Mesa feature matrix `docs/features.txt` lists `VK_KHR_ray_tracing_pipeline` DONE for radv gfx10.3+ (seen as a search snippet) | Linux AMD RDNA2+ RT driver support, which is relevant to the Steam Deck (RDNA2 APU per https://www.steamdeck.com/en/tech) |
| P14 | Mesa Dozen (Vulkan on D3D12), https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/14766, and issue #7255 ("dzn is not a conformant Vulkan implementation, testing use only") | A Vulkan-over-D3D12 layer exists; its ray-tracing support was not found |
| P15 | Khronos KTX 2.0 specification, https://registry.khronos.org/KTX/specs/2.0/ktxspec.v2.html, and Basis Universal (Apache-2.0), https://github.com/BinomialLLC/basis_universal | Container and supercompression options |
| P16 | Apple Metal Feature Set Tables, https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf (not re-fetched in this session) | BC and ASTC format availability per Apple GPU family. **Verify before relying on it** |
| P17 | VitaSDK, https://vitasdk.org/ (community homebrew toolchain; not fetched) | Vita homebrew toolchain exists outside Sony's programme |
| P18 | Microsoft Learn (archived), "Xbox Developer Mode activation", https://learn.microsoft.com/en-us/windows/uwp/xbox-apps/devkit-activation (fetched 2026-11-27) | Developer Mode is enabled on **retail** Xbox One / Series X\|S through the Xbox Dev Mode app and a Partner Center app-developer account, under the "Xbox Developer Mode Activation Program" agreement. In Dev Mode "you cannot play retail games or run retail apps" |
| P19 | Microsoft Learn (archived), "System resources for UWP apps and games on Xbox One", https://learn.microsoft.com/en-us/windows/uwp/xbox-apps/system-resource-allocation (fetched 2026-11-27) | UWP on Series X\|S: "DirectX 11 and DirectX 12 with Hardware Feature Level 11.0"; games get 5 GB. **No Vulkan**; no DXR statement |
| P20 | Microsoft UWP-on-Xbox FAQ, https://learn.microsoft.com/windows/uwp/xbox-apps/frequently-asked-questions, and Microsoft Q&A https://learn.microsoft.com/en-us/answers/questions/5630614/uwp-no-longer-accepted-for-xbox-game-submissions-i (search snippets, 2026-11-27) | "UWP based games are no longer accepted in the Xbox Store. Please use the ID@XBOX program" |
| P21 | Steamworks, "Distributing Open Source Applications on Steam", https://partner.steamgames.com/doc/sdk/uploading/distributing_opensource (fetched 2026-11-27) | "The Steamworks SDK is incompatible with some open source licenses"; copyleft/GPL "will be problematic when combining code with the Steamworks SDK"; Valve "doesn't review your codebase" and the developer must warrant that it holds all necessary rights |
| P22 | Steamworks, "Distributing Source Engine Games / Mods", https://partner.steamgames.com/doc/sdk/uploading/distributing_source_engine (search snippet, 2026-11-27) | For **Valve's own** IP: mods using Valve IP need Valve approval and must require base-game ownership. This shows the pattern that a Steam mod release needs the IP holder's consent. **Not** a rule for Croteam/Devolver IP |
| P23 | Steam Deck FAQ, https://www.steamdeck.com/en/faq (fetched 2026-11-27) | "Multi-boot is supported"; boot from microSD; non-Steam games can be added and run through Proton. This is an open PC: no exploit is needed |
| P24 | *Nintendo of America v. Bowser*, W.D. Wash. No. 2:21-cv-00519, consent final judgment and permanent injunction, 2021-12-07, https://cases.justia.com/federal/district-courts/washington/wawdce/2:2021cv00519/298468/24/0.pdf (search snippet; not read in full) | US DMCA §1201 anti-circumvention claims over Switch hacking tools resulted in USD 10 M damages and an injunction (settled, so not a merits ruling) |
| P25 | Secondary press on console exploits (not primary, details conflict across outlets): PS5 "Relapse" chain up to FW 13.60, Kotaku https://kotaku.com/new-ps5-jailbreak-exploit-works-on-systems-running-july-2026-firmware-2000738283 and TechSpot https://techspot.com/news/114037-new-ps5-jailbreak-works-almost-every-firmware-version.html. Switch 2 userland/tethered exploits, 2026: Notebookcheck https://www.notebookcheck.net/Switch-2-Developer-unveils-a-universal-exploit-that-works-entirely-offline.1347373.0.html and Android Authority https://androidauthority.com/nintendo-switch-2-software-jailbreak-3727013 | Homebrew on PS5 and Switch 2 depends on firmware-specific exploits that the vendor patches |

## 3. Observed facts

### 3.1 Engine and renderer facts that constrain platforms (from [RD-005](./RD-005-rendering.md))

- RTGL1 requires `VK_KHR_ray_tracing_pipeline` and `VK_KHR_acceleration_structure` on Vulkan 1.2. It has no non-RT fallback.
- SE-RT is Windows/MSVC only (its README says "Other OS: Not supported").
- RTGL1 itself has Win32, Wayland, XCB, Xlib and Metal surface options. The `hl1` branch has a Linux build PR (`2457acc`), but its FSR2 is linked from Windows-only prebuilt libraries.
- SeriousSamClassic-VK (raster Vulkan plus legacy GL) lists Windows, Linux, FreeBSD, OpenBSD, Raspberry Pi OS and macOS. It supports x86, aarch64 and e2k, with GitHub Actions CI (README in the `510d36f` tree).
- Shaders are GLSL compiled to SPIR-V with `glslc` (RTGL1) or `glslangValidator` (Classic-VK). No HLSL or DXIL path exists in any of the forks.
- No fork or RTGL1 contains console platform code. The check was `git grep -w -i -E 'XboxOne|_GAMING_XBOX|_GAMING_XBOX_SCARLETT|ORBIS|PROSPERO|__NX__|NVN|sceGxm|gnm|agc'` over `*.c/*.cpp/*.h/*.txt` at the HEADs listed in RD-005, and it returned 0 files in all five repos. The `-w` flag matters: without it, "vorbis" matches "orbis".

### 3.2 Per-platform feasibility table

Verdict key:

- **viable**: can proceed on public, authorized toolchains.
- **research**: technically plausible, but unverified or with significant unknowns.
- **blocked**: requires an authorization that an unofficial fan project cannot realistically obtain, or a capability that does not exist.

Since 2026-11-27, a console or handheld verdict is given **per question**, with the four questions kept apart (ADR-0007; detail and sources in [§3.5](#35-legal-split-per-platform-four-separate-questions)): **T** = technical homebrew feasibility, **D** = official distribution, **S** = platform SDK licensing versus GPL, **IP** = game IP licence. The PC rows keep a single technical verdict, because no platform SDK or store is required there.

| Platform | Toolchain (public?) | Graphics API | HW RT available? | Authorization path | GPL / SDK concern (flag for Agent E) | Texture formats | Verdict |
|---|---|---|---|---|---|---|---|
| **Windows 10/11 x64** | MSVC or clang, CMake, Vulkan SDK (public) | Vulkan 1.2+ (RTGL1, Classic-VK). Legacy OpenGL 1.x | Yes on RT-capable GPUs through `VK_KHR_ray_tracing_pipeline`. Vendor coverage is driver-dependent and unmeasured | None needed for open-source distribution. Steam distribution of a **free mod** that requires owned base games is a separate question for E and the owner | DLSS (P12) proprietary; FSR2 prebuilt `.lib` | KTX2 + BC1/3/4/5/7 (what RTGL1 v1.1.0 loads); DDS optional | **viable** (RT and raster) |
| **Linux x64** | GCC or clang, CMake, distro Vulkan loader (public) | Vulkan (Mesa RADV/ANV, NVIDIA proprietary) | Yes: RADV RT pipelines default-on since Mesa 23.2 for gfx10.3+ (P13); NVIDIA driver supports the KHR RT extensions (not re-verified here) | None | Same as Windows. Distro packaging (Flatpak, AppImage) has its own policies | KTX2 + BCn | **viable** for raster (Classic-VK proven upstream). **research** for RT: SE-RT is Windows-only and the RTGL1 Linux build is only in `hl1`, which is API-incompatible |
| **Steam Deck (SteamOS) / Proton** | Native Linux build, or a Windows build under Proton (Wine `winevulkan` passes Vulkan through, so no D3D translation is needed). Hypothesis, untested | Vulkan via RADV | RDNA2 APU (P13 hardware page). RT is supported by the driver, but performance for full path tracing at Deck resolutions is **unknown**; expect it to be marginal | None for sideloading. "Steam Deck Verified" is a Valve review label, not a requirement | none additional | KTX2 + BCn | **viable** for raster (native Linux). **research** for RT (performance). Legal split in §3.5: sideloading is fine (P23); **Steam store distribution is a separate, open question** (P21, P22) |
| **macOS (Apple Silicon / Intel)** | Xcode/clang, CMake, Vulkan SDK with MoltenVK (public) | Vulkan through MoltenVK, layered on Metal | **No through Vulkan**: MoltenVK lists no RT extensions (P2). Metal has its own RT API, but no fork targets Metal directly | Apple Developer Program only for signing and notarization (outside this dossier's verification) | MoltenVK is Apache-2.0 (not verified here) | BC on Apple Silicon Macs and ASTC per Metal tables (P16, verify) | **research** for raster (Classic-VK claims macOS). **blocked** for RTGL1 RT |
| **Xbox Series X\|S** | Microsoft GDK. The PC GDK installs publicly, but console development needs onboarding, NDA, Partner Center and dev hardware or Dev Mode (P3). Console docs are partly public (P5) **[console specifics: NDA: inaccessible]** | Direct3D 12 on Xbox (P5). **Vulkan not available** (no public evidence; treat as unavailable). Dozen (Vulkan over D3D12, P14) is non-conformant, has unknown RT support and is not a console product | Yes, DXR/"XDXR" on Series X\|S (P5) | ID@Xbox / Xbox Onboarding Hub; the publishing agreement is a separate track (P3) | GDK is a proprietary binary (P4); console code under NDA cannot be published as GPL source (pattern in P10/P11). **Core GPL tension, flag for E** | BCn (AMD RDNA2-class GPU; [NDA: format list inaccessible]) | **T:** research. Dev Mode is sanctioned, but needs a new D3D11/12 backend because RTGL1 is Vulkan/GLSL-only and UWP gets D3D FL11.0 (P19). **D:** blocked (UWP games no longer accepted, P20; ID@Xbox needs a publisher agreement). **S:** open question, GDK/NDA vs GPL (RD-007 Q14). **IP:** blocked, no licence |
| **PlayStation 5** | Sony SDK through PlayStation Partners, the GDPA and devkit loan (P9) **[NDA: inaccessible]** | Proprietary Sony graphics APIs (commonly reported as GNM/AGC; **not verifiable from public primary sources**). No Vulkan publicly documented | Sony publicly advertises hardware RT on PS5 (marketing; specifics [NDA]) | Partner registration as a legal entity plus GDPA approval (P9) | Platform code and SDK confidentiality are incompatible with publishing source. Open-source engines keep their PS ports private (P10) | [NDA: inaccessible]; BCn likely (AMD RDNA2-class), unverified | **T:** homebrew needs firmware exploits only (P25); not pursued. **D:** blocked (GDPA). **S:** blocked in practice (NDA, P10). **IP:** blocked |
| **Nintendo Switch** | Nintendo Developer Portal (individuals may register, P6). SDK, NVN docs and devkits are behind the portal **[NDA: inaccessible]** | NVN (proprietary), plus Vulkan 1.0 conformance listed in 2016 (P8) | No (Maxwell-class Tegra X1, no RT cores; not re-verified) | Portal registration, then title approval and a publishing licence | Same NDA/GPL tension (P11) | ASTC and BCn likely on Tegra; [NDA: inaccessible] | **T:** research only (community homebrew; RT impossible; raster needs a low-spec path; circumvention legality, P24). **D:** blocked. **S:** blocked in practice (NDA, P11). **IP:** blocked |
| **Nintendo Switch 2** | Same portal (P6) **[NDA: inaccessible]** | NVN2 reported (community, not primary). **Vulkan availability unknown**: no Khronos listing found (P8) | Yes: dedicated RT cores (P7). API exposure [NDA: inaccessible] | Same as Switch | Same, plus DLSS licensing if used | [NDA: inaccessible] | **T:** not feasible today (only tethered or userland exploits reported, P25; API unknown). **D:** blocked. **S:** blocked in practice (NDA). **IP:** blocked |
| **PS Vita** | No official SDK available to new developers (Sony programme; not verified). Homebrew only through VitaSDK (P17) on exploited or modded consoles | GXM (proprietary). No Vulkan | No | None legitimate for new commercial titles. Homebrew requires firmware exploits; **legal status of circumvention varies by jurisdiction (e.g. US DMCA §1201, EU Directive 2001/29/EC art. 6). Flag for E** | VitaSDK is community-made; GPL code is technically shippable as homebrew, but the legal status of the exploit route is unresolved | PVRTC and ETC likely (PowerVR SGX543MP4+), unverified | **T:** research, low priority (VitaSDK; GPL-shippable as homebrew; circumvention legality open). **D:** blocked (no programme for new titles [ASM]). **S:** not applicable to the homebrew route. **IP:** blocked for any public build |

### 3.3 Publishing authorization for an unofficial remaster (assessment, not legal conclusion)

- Every console path (P3, P6, P9) runs through a publisher or developer agreement with the platform holder. Certification and storefront submission sit with that publisher of record. From standard industry practice, though not from a cited clause, platform holders expect the publisher to hold or license the rights in the content it submits.
- SSTRE is "independent of Croteam and Devolver Digital", and users supply their own game data (plan §1). A console build cannot rely on user-supplied PC game files: consoles do not allow side-loading user data into retail titles without the platform holder's approval. **Realistically, a console release needs a licence from the IP holder** (Croteam / Devolver Digital), and probably their participation as publisher.
- Open-source engines with console support (Godot P11, Defold P10) all keep the console layer private and give it only to approved licensees. An SSTRE console port would therefore have a private, NDA-covered layer. Whether that layer can be combined with GPL-2.0 engine code is a question for Agent E. It is the same issue Godot avoided by being MIT-licensed (P11 discussion).

### 3.4 Texture compression and packaging per platform

| Target | Recommended runtime encoding | Notes |
|---|---|---|
| Windows / Linux / Deck | KTX2 + BC7 (colour, alpha), BC5 (normal XY), BC4 (single channel), BC1 optional | Matches the RTGL1 loader (native `VkFormat`; no Basis transcoder compiled, see RD-005 §3.2) |
| macOS (Apple Silicon) | KTX2 + BCn if the Metal tables confirm support (P16); ASTC fallback | Verify per GPU family |
| Consoles (if ever authorized) | Platform-native formats and containers [NDA] | Produce them from the same lossless intermediates (PNG16/EXR) per plan §4 step 8 |
| Mobile-class / Switch | ASTC (likely) | NDA-gated confirmation |
| Universal distribution option | KTX2 + Basis UASTC/ETC1S, transcoded at load or install (P15, Apache-2.0) | Requires adding the transcoder to the engine loader. Encoding is lossy, so record compressor settings in provenance (RD-004) |

### 3.5 Legal split per platform (four separate questions)

Added 2026-11-27 per owner direction (ADR-0007, "Console questions are four separate questions"). **Not legal advice.** Each cell carries an evidence label: [DOC] means a documented source (P-number), [ASM] means an assumption or hypothesis. A positive answer to one question never implies anything about the other three.

- **Technical homebrew feasibility:** can SSTRE's engine run on the hardware using community or retail-sanctioned toolchains, without an official SDK licence? This is technical only. The legality of the route is noted separately in the same cell.
- **Official platform distribution:** can a build be published through the platform's store or programme?
- **Platform SDK licensing:** can the SDK or toolchain that the official route requires coexist with GPL-2.0-only engine source publication and the GPLv2 binary-distribution duties?
- **Game IP licensing:** does SSTRE hold, or can it reasonably obtain, the rights holder's permission for *Serious Sam* on that platform? A console build cannot use the user's own PC data (§3.3).

| Platform | Technical homebrew feasibility | Official platform distribution | Platform SDK licensing | Game IP licensing |
|---|---|---|---|---|
| **Xbox Series X\|S** | **Research.** Retail consoles have a Microsoft-sanctioned Developer Mode (Partner Center account, activation agreement) [DOC P18]. UWP code there gets D3D11/D3D12 FL11.0 and 5 GB, with no Vulkan [DOC P19]. SSTRE would need a new D3D backend (no DXR evidence for UWP [ASM]). No circumvention is involved, but the use is bound by the Dev Mode Activation agreement, which was not read [ASM] | **Blocked.** UWP games are "no longer accepted in the Xbox Store", and the route is ID@Xbox [DOC P20]. GDK console publishing needs an NDA, Partner Center onboarding and a publishing agreement [DOC P3] | **Open, likely conflicting.** The PC GDK is public but proprietary binary [DOC P4]. Console GDK material is under NDA [DOC P3]. Open-source engines keep console layers private [DOC P10, P11]. Whether a private layer can be combined with GPL-2.0-only code is unresolved [ASM] (RD-007 Q14) | **Blocked: none held.** No licence requested from Croteam/Devolver [ASM; U5]. Required for any store release [ASM, §3.3] |
| **PlayStation 5** | **Technically possible only through firmware exploits** (public chains reported up to FW 13.60; later firmware patched) [DOC P25, secondary]. **Not pursued.** Circumvention legality varies: US DMCA §1201, EU 2001/29/EC art. 6 [ASM] | **Blocked.** Partner registration as a legal entity, GDPA and devkit loan [DOC P9] | **Blocked in practice.** SDK and source access only for licensed developers [DOC P10]. NDA vs GPL source duties [ASM] | **Blocked: none held** [ASM] |
| **Nintendo Switch** | **Research only.** Community homebrew relies on circumvention [ASM]. Nintendo has enforced anti-circumvention claims (US consent judgment) [DOC P24]. Hardware has no RT; a raster port needs a low-spec path [ASM] | **Blocked.** Developer Portal registration is open to individuals, but title approval and a publishing licence follow [DOC P6] | **Blocked in practice.** NVN/SDK under NDA [DOC P6, P11] | **Blocked: none held** [ASM] |
| **Nintendo Switch 2** | **Not feasible today.** Only userland or tethered exploits reported in 2026 and partly withdrawn [DOC P25, secondary]. Graphics API unknown [DOC P8; NDA]. Same circumvention exposure as Switch [DOC P24] | **Blocked** (same portal and approval path) [DOC P6] | **Blocked in practice.** NDA. DLSS adds NVIDIA licence terms [DOC P12] | **Blocked: none held** [ASM] |
| **Steam Deck** | **Viable.** It is an open PC: multi-boot, microSD boot, non-Steam games through Proton [DOC P23]. The native Linux raster build or Windows build under Proton needs no exploit (§3.2) | **Two different questions.** (a) *Sideloading or out-of-store distribution* of a GPL engine that requires the user's own game data: no platform permission needed [DOC P23]. The GPL and asset questions are in RD-007. (b) *Steam store release* (own app or Workshop): the developer must warrant all necessary rights [DOC P21]. For Valve's own IP, Valve requires approval and base-game ownership [DOC P22]. By analogy the Croteam/Devolver IP holder's consent would be needed [ASM]. **Open** | **Conditional.** Without the Steamworks SDK: none. **With** the Steamworks SDK (achievements, overlay APIs): Valve says copyleft/GPL "will be problematic" [DOC P21]. Keep any Steam integration out of the GPL engine or obtain counsel review [ASM] | **Not needed for sideloading** while no assets are shipped (ADR-0002; see RD-007 Q6 on local conversion). **Needed for a Steam store page** using the name or IP [ASM]. Trademark use is a separate matter (RD-007 Q12) |
| **PS Vita** | **Research, low priority.** VitaSDK community toolchain [DOC P17] on exploited consoles [ASM]. GPL code is shippable as homebrew [ASM]. Circumvention legality is open (DMCA §1201 / 2001/29/EC art. 6) [ASM] | **Blocked.** No programme for new titles is known [ASM, not verified] | **Not applicable to the homebrew route.** The official SDK is unavailable [ASM] | **Blocked** for any public build [ASM]. A homebrew build that requires user-owned data still raises RD-007 Q6 |

Consequences for ADR-0007 [ASM]:

1. Only the **Steam Deck** clears the technical question without circumvention or NDAs. Its open legal questions concern **Steam store distribution** and the **Steamworks SDK**, not the hardware.
2. For **Xbox**, the technical question is answerable lawfully through Dev Mode, which makes it the only console where a technical spike would not need circumvention. Official distribution, the SDK and the IP remain blocked.
3. **PS5 / Switch / Switch 2 / Vita** homebrew depends on circumvention. Its legality is a counsel question (RD-007 Q19), and it should not be pursued by the project.

## 4. Assumptions and unknowns

- U1. Actual RT performance on the Steam Deck, Intel Arc and older AMD RDNA2 for RTGL1 v1.1.0 is unmeasured.
- U2. Whether Xbox Dev Mode (retail console developer mode, https://learn.microsoft.com/en-us/windows/uwp/xbox-apps/devkit-activation, not fetched) permits Vulkan or DXR for UWP or GDK apps, and its distribution limits.
- U3. Switch 2 Vulkan support and exposure of the RT API [NDA].
- U4. Whether a GPL-2.0 engine can be legally combined with a private platform layer for consoles (Agent E).
- U5. Whether Devolver Digital or Croteam has any community or console licensing programme (owner action; not researched).
- U6. Whether the Classic-VK macOS build actually runs on MoltenVK (README claim, not verified).

## 5. Alternatives and trade-offs (inputs to ADR-0007)

| Option | Description | Pros | Cons |
|---|---|---|---|
| P-A | Windows-only RT plus raster (SE-RT lineage) | Smallest scope; matches the upstream RT work | Ignores the Linux/Deck audience; RT-only binaries exclude many GPUs |
| P-B | **Windows + Linux, with Vulkan raster as baseline and RT as an optional backend** | Uses portable, proven Classic-VK-style rendering; RT where hardware allows; Deck covered by the native Linux build | Two renderer paths to test; the Linux RT build needs RTGL1 or SE-RT porting work |
| P-C | P-B plus macOS raster through MoltenVK | Wider reach | No RT; extra CI and signing cost; unverified |
| P-D | Plan a D3D12/HLSL backend now for future Xbox | Prepares for consoles | Large cost with no authorized distribution path; the work would be speculative |

## 6. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Console ports assumed achievable | High (wasted effort, legal exposure) | Gate console work on (1) an IP licence and (2) a platform agreement, per plan §8 phase 8 |
| GPL source obligations versus NDA SDKs | High | Keep any console layer out of public repos; get Agent E and counsel review before any console code exists |
| RT-only build alienates users without RT GPUs | Medium | Ship the raster baseline (P-B) |
| Platform-specific texture packaging diverges | Medium | One manifest record and lossless intermediates; per-target compile profiles (RD-005 §6) |
| Proprietary upscalers (DLSS) on Linux and Windows | Medium | Optional, user-supplied DLSS only; FSR1/CAS (MIT) by default, subject to RD-007 |

## 7. Proposed experiment: Spike S2 "PC platform matrix"

Run Spike S2 after RD-005 Spike S1 has produced builds.

1. Build the raster baseline (the Classic-VK-lineage candidate chosen in ADR-0005) on Windows and on Linux (Ubuntu LTS plus Mesa RADV, and an NVIDIA proprietary driver if hardware is available).
2. Run the Windows SE-RT build under Proton on Linux and, if available, on a Steam Deck. Also run the native Linux raster build on the Deck.
3. Optional: a macOS Apple Silicon raster build through MoltenVK.
4. Use the same scripted TFE demo as S1. Capture frame time and VRAM, and capture `vulkaninfo` (extension list) per device.

| # | Criterion | Pass threshold |
|---|---|---|
| S2.1 | Raster build on Windows and Linux | Both build from documented steps and complete the 5-minute demo with no crash |
| S2.2 | Deck raster | Native Linux build sustains the demo at the Deck panel's native resolution (1280×800); p99 frame time recorded (target to be set after the baseline) |
| S2.3 | RT availability probe | `vulkaninfo` confirms or denies `VK_KHR_ray_tracing_pipeline` on every test device; results recorded in the compatibility matrix |
| S2.4 | RT under Proton or native Linux | SE-RT reaches the main menu and loads `01_Hatshepsut` (yes/no) |
| S2.5 | macOS (optional) | Classic-VK raster runs on MoltenVK (yes/no). Absence of RT extensions confirmed |
| S2.6 | Texture formats | One KTX2 BC7/BC5 override set loads identically on all PC targets (same hash in, visually identical screenshot within the RD-004 tolerance) |

## 8. Recommendation (input for ADR-0007)

1. **Accepted direction (already in plan §3):** PC-first. Propose **Windows x64 and Linux x64 as Tier 1**, with the Vulkan raster renderer as the always-available baseline and RTGL1 path tracing as an optional backend where `VK_KHR_ray_tracing_pipeline` exists (option P-B).
2. **Steam Deck**: Tier 2 through the native Linux raster build. RT on the Deck remains research (performance).
3. **macOS**: Tier 3 research, raster only. Do not promise RT.
4. **Xbox Series X|S, PS5, Switch, Switch 2.** Use the per-question verdicts in §3.5 instead of a single "blocked" (updated 2026-11-27):
   - **Official distribution:** blocked on all four.
   - **Game IP licence:** blocked on all four. None is held.
   - **Platform SDK licensing:** open or likely conflicting (Xbox); blocked in practice (PS5, Switch, Switch 2).
   - **Technical homebrew:** research only on Xbox Dev Mode (no circumvention); not pursued on PS5 / Switch / Switch 2 (circumvention).
   - Do no console code, no console-specific backend work (no D3D12, NVN or Sony APIs) and no console claims in public docs until the owner obtains written authorization from the IP holder. The GPL-versus-NDA structure (RD-007 Q14) must also be resolved first.
5. **PS Vita**: out of scope for official work (distribution and IP blocked). Technical homebrew is low-priority research, and only after counsel reviews the legality of circumvention (RD-007 Q19).
6. **Steam Deck** (added 2026-11-27): technically viable and sideloadable. A **Steam store** release is a separate open question, covering IP-holder consent and the Steamworks SDK versus the GPL (§3.5; RD-007 Q18).
7. Texture runtime standard for PC: **KTX2 + BCn** (BC7/BC5/BC4). Keep lossless intermediates so ASTC, Basis or console formats can be produced later without re-running AI steps.

## 9. Decision dependencies

- ADR-0005: the engine base determines whether the raster baseline already exists (Classic-VK lineage) or must be revived (SE-RT `GAT_VK`/`GAT_OGL`, unverified).
- ADR-0006 / RD-007: DLSS, FSR2 binaries, GPL versus console NDA, legality of Vita homebrew, derived asset distribution.
- Owner: whether to approach Devolver Digital or Croteam about licensing (prerequisite for any console verdict change).

## 10. Next steps

1. Lead: record ADR-0007 as "PC-first accepted; Tier 1 Windows/Linux and raster-baseline-plus-optional-RT **proposed**; consoles blocked pending licence".
2. Agent E: answer U4, assess the DLSS and Vita questions, and review the wording of §3.3.
3. Agent F/G: add a "platform / GPU / RT extension present" axis to the compatibility matrix ([RD-008](./RD-008-testing-release.md)).
4. Phase 1: run Spike S2 after S1.
5. Owner: decide whether to contact the IP holder before any console research continues beyond this desk study.
