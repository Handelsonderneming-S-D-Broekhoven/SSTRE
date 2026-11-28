# RD-015: Steam Deck testing before hardware is available

| Field | Value |
|---|---|
| Dossier | RD-015 |
| Author | Track DECK-EMU, 2026-11-28 |
| Date | 2026-11-28 |
| Status | **Draft.** Desk research, source reading and one host inspection. No GPU job, no game run and no container run was made. The one planned container proof (§8) was not run; §8 says why. |
| Feeds | [ADR-0007](../adr/0007-platform-strategy.md) Tier 2 (Steam Deck); backlog POC-64..74; [RD-008](./RD-008-testing-release.md) §10 compatibility matrix |
| Related | [RD-006 platforms](./RD-006-platforms.md) (Deck row, S2.2), [RD-012 input](./RD-012-input-local-multiplayer.md) (POC-57..60), [RD-014 RT performance](./RD-014-rt-performance.md), [RD-008 testing/release](./RD-008-testing-release.md) |

## 1. Question and scope

The owner decided on 2026-11-28 that Steam Deck problems should be caught before the hardware arrives. This dossier answers four questions:

1. Which emulation or approximation options exist on this machine (Windows 11, RTX 4070, i5-11600K, 32 GB, Docker Desktop, WSL2, no AMD GPU) or on a generic Linux box?
2. For each option, what can and cannot it validate? What does it cost, how faithful is it, and how likely is it to give false confidence?
3. What should be set up now, ranked by value per cost?
4. What can only the real hardware validate?

Out of scope: Steam store distribution and the Steamworks SDK (RD-006 §3.5, RD-007), console ports, and implementing anything.

Evidence labels: **[DOC]** published source, **[SRC]** read in our source trees, **[EXP]** observed on this machine during this track, **[ASM]** assumption or inference.

## 2. Evidence

All web sources were fetched on 2026-11-28 unless noted.

| ID | Source | Supports |
|---|---|---|
| D1 | Valve, Steam Deck tech specs, https://www.steamdeck.com/en/tech (OLED) and https://www.steamdeck.com/en/tech/deck (LCD, seen as a search snippet) | Zen 2 4C/8T at 2.4–3.5 GHz; 8 RDNA 2 CUs at 1.0–1.6 GHz, 1.6 TFLOPS FP32; 16 GB LPDDR5, quad 32-bit, 5500 MT/s (LCD) or 6400 MT/s (OLED); APU 4–15 W; 1280×800; LCD 60 Hz, OLED up to 90 Hz; SteamOS 3 (Arch-based) |
| D2 | Linux kernel docs, "Misc AMDGPU driver information", https://docs.kernel.org/gpu/amdgpu/driver-misc.html (search snippet, versions 6.4–6.15) | Steam Deck = VANGOGH, GC 10.3.1 (RDNA2, gfx1033) |
| D3 | Mesa `docs/features.txt`, read through the Android mirror `platform/external/mesa3d` `refs/heads/main` (that mirror's last merge is dated 2025-03-07, so the snapshot may be older than Mesa main) | `VK_KHR_acceleration_structure`, `VK_KHR_ray_query`, `VK_KHR_ray_tracing_pipeline`: DONE for `radv/gfx10.3+` and `lvp`; `VK_EXT_image_drm_format_modifier`: radv/gfx9+, **not lvp** |
| D4 | Mesa docs, environment variables, https://docs.mesa3d.org/envvars.html | `RADV_DEBUG=nort` ("RT extensions will still be advertised"), `RADV_PERFTEST=rtwave64`, `RADV_EXPERIMENTAL=emulate_rt`, `LP_NUM_THREADS`, `MESA_VK_DEVICE_SELECT`. The current page does **not** list `RADV_FORCE_FAMILY` |
| D5 | Mesa commit "radv: implement a dummy winsys for creating devices without AMDGPU", https://lists.freedesktop.org/archives/mesa-commit/2020-February/100389.html; "docs/envvars: update RADV_FORCE_FAMILY", https://lists.freedesktop.org/archives/mesa-commit/2020-May/103247.html; null winsys GFX12 follow-up, https://gitlab.freedesktop.org/asahi/mesa/-/commit/01f92acf10d6d36778d81016b08ac8d72707654b (all via search snippets) | `RADV_FORCE_FAMILY=<family>` creates a null device "to compile shaders without a AMD GPU"; the null winsys is in `src/amd/vulkan/winsys/null/` and is still maintained |
| D6 | Gamescope README, https://github.com/ValveSoftware/gamescope | `-W/-H` output size, `-w/-h` game size, `-r` frame limit, `-F fsr` (FSR 1.0); NVIDIA needs 515.43.04+ and `nvidia-drm.modeset=1`; AMD needs Mesa 20.3+; nothing about WSL |
| D7 | Gamescope issue #1984 "Headless backend not rendering anything apart from pointer", https://github.com/ValveSoftware/gamescope/issues/1984 (opened 2025-10-10, open; later reports in May and June 2026) | `--backend headless` exists. On NVIDIA it failed with `vkGetPhysicalDeviceFormatProperties2 returned zero modifiers` |
| D8 | NVIDIA forum, "Valve Gamescope Crashing when Scaling Filters are Applied on 580.105.08", https://forums.developer.nvidia.com/t/valve-gamescope-crashing-when-scaling-filters-are-applied-on-580-105-08/354533 (search snippet) | gamescope scaling filters on NVIDIA are fragile |
| D9 | WSLg/NVIDIA reports, e.g. https://forums.developer.nvidia.com/t/wsl2-ubuntu-24-04-lts-nvidia-gpu-detected-but-wslg-not-working-opengl-llvmpipe/347383 and https://forums.developer.nvidia.com/t/critical-bug-rtx-5070-ti-mobile-missing-nvidia-icd-json-in-wsl2-causes-vulkan-initialization-failure-on-driver-591-86/359933 (search snippets) | WSL2 graphics on NVIDIA often fall back to llvmpipe; Vulkan ICD availability in WSL is inconsistent |
| D10 | A. Garcia (Igalia), "Running the Steam Deck's OS in a virtual machine using QEMU", https://blogs.igalia.com/berto/?p=783 (2022, edited up to July 2025) | SteamOS 3 recovery image installs in QEMU/KVM with OVMF; **Gaming Mode does not work in QEMU**; 3.7+ images boot to Desktop Mode in a VM; plain `VGA` display |
| D11 | Mesa Venus driver docs, https://docs.mesa3d.org/drivers/venus.html | Venus needs a Linux (or Android) host with virglrenderer, QEMU `virtio-gpu-gl,blob=true,venus=true`, host kernel 6.13+ for RADV; tested host drivers include NVIDIA 570.86+ and lavapipe; no mention of Windows hosts or RT |
| D12 | Khronos/LunarG Profiles layer docs, https://vulkan.lunarg.com/doc/view/latest/mac/profiles_layer.html | The layer overrides query results. It "cannot add … capability to an actual device that doesn't already provide it" and "will not enable a less-capable device to emulate a more-capable device"; it does not enforce; use it with the Validation layer |
| D13 | S. Willems, "Vulkan profiles support for the Vulkan Hardware Capability Viewer and database", https://saschawillems.de/blog/2022/03/12/vulkan-profiles-support-for-the-vulkan-hardware-capability-viewer-and-database/ | gpuinfo.org generates a profile JSON per report, e.g. `https://vulkan.gpuinfo.org/api/v3/getprofile?id=<report>` |
| D14 | PC Games Hardware, 2024-02-02, https://www.pcgameshardware.de/Steam-Deck-Hardware-277668/News/Pathtracing-mit-30-Fps-1439705/ (secondary; source is a YouTube video) | Portal with RTX on the Deck through Proton (`-dx12`, `RADV_PERFTEST=rt`): ~30 FPS at 864×486, RTX Remix "Low", secondary bounces off |
| D15 | GamingOnLinux, 2022-04, https://www.gamingonlinux.com/2022/04/yes-the-steam-deck-will-eventually-get-ray-tracing-once-the-amd-gpu-driver-matures/ (search snippet); Phoronix SteamOS 3.5 review, https://phoronix.com/review/steamos-35-benchmarks/3 (403 on fetch; search snippet only) | Quake II RTX ran on the Deck "but not well" in 2022; no change from SteamOS 3.4 to 3.5 |
| D16 | Steamworks, "Steam Deck Compatibility Review", https://partner.steamgames.com/doc/steamdeck/compat | Deck controls must work by default; glyphs must match the active input; supported resolution (1280×800 preferred); smallest glyph **≥ 9 px tall at 1280×800**, 12 px recommended; playable = **30 FPS at 800p** in the default configuration; nothing on suspend/resume |
| D17 | Steamworks, "Steam Deck Recommendations", https://partner.steamgames.com/doc/steamdeck/recommendations | Vulkan recommended "for best performance and battery life"; support many aspect ratios; no hardware-locked settings |
| D18 | ValveSoftware/steam-runtime README, https://github.com/ValveSoftware/steam-runtime | scout (SLR 1.0), soldier, sniper (SLR 3.0, used by Proton 8–10), **steamrt4 (SLR 4.0, Proton 11+; recommended for new native games)**; build inside a Steam Runtime SDK container (OCI images; Podman/Docker/Toolbx) |
| D19 | Steam Deck UI on desktop: PC Gamer, https://pcgamer.com/at-long-last-the-steam-deck-ui-has-replaced-steams-big-picture-mode; GamingOnLinux 2023-02 (search snippets) | The Deck UI replaced Big Picture in February 2023; `-gamepadui` was the beta switch |
| D20 | Deck frame-limit slider: GamingOnLinux 2023-11, https://www.gamingonlinux.com/2023/11/valve-refines-new-steam-deck-unified-frame-limit-slider-to-show-refresh-rate; Tom's Hardware on limiter latency, https://www.tomshardware.com/news/steam-deck-framerate-limiter-egregiously-raises-input-latency (search snippets) | The QAM frame limit is tied to the panel refresh rate; the limiter adds input latency |
| D21 | Microsoft Learn, "Case Sensitivity", https://learn.microsoft.com/en-us/windows/wsl/case-sensitivity | `fsutil.exe file setCaseSensitiveInfo <dir> enable` (admin, empty directory, inherited by new subdirectories) |
| D22 | lavapipe in CI: llama.cpp PR https://github.com/ggml-org/llama.cpp/pull/10809 and its Vulkan workflow (search snippets) | `mesa-vulkan-drivers` on GitHub-hosted Ubuntu runners is used for Vulkan CI; "very slow"; distro Mesa may be old |
| D23 | PC Gamer, "Steam Deck: what sort of gaming performance can we expect", https://www.pcgamer.com/steam-deck-performance-expectations (search snippet) | The Deck CPU is roughly a Ryzen 3 3100 (4C/8T Zen 2), slightly slower. No published, validated desktop-proxy method was found |
| S1 | RTGL1 SSTRE clone `rtgl1-noktx` at `3f50942`, `Source/VulkanDevice.cpp:1540-1620` | [SRC] required device extensions: swapchain, deferred host operations, pipeline library, `VK_KHR_ray_tracing_pipeline`, `VK_KHR_acceleration_structure`, synchronization2, float16/int8. Required features include `shaderFloat64`, `shaderInt64`, `shaderInt16`, `shaderResourceResidency`, `shaderResourceMinLod`, `multiview`, `bufferDeviceAddress`, `runtimeDescriptorArray`, `storageBuffer16BitAccess`. DLSS extensions only when present |
| S2 | SSTRE-Engine `sprint2/integration` `c1537cfd`, `SamTFE/Sources/CMakeLists.txt:127-128` (same in SamTSE) | [SRC] the Linux build sets `SE1_RAYTRACING=0` |
| S3 | Same tree, `SamTFE/Sources/SeriousSam/SeriousSam.cpp:98-99,370-377` | [SRC] `sam_iMaxFPSActive` defaults to **500**; inactive 10 |
| S4 | Same tree, `SamTFE/Sources/Engine/Base/Timer.cpp:42-60,555-558`; `SamTFE/Sources/CMakeLists.txt:70` (`USE_ASM` default TRUE) | [SRC] the timer reads RDTSC on x86 builds with ASM; `CLOCK_MONOTONIC` only when `NOT_USE_ASM`. Which path the Linux build uses depends on `Types.h:170-172` |
| E1 | Host inspection, this track, 2026-11-28 (read-only commands, no GPU job) | [EXP] WSL is the inbox build (`wsl --version` unsupported), kernel `5.10.16.3-microsoft-standard-WSL2`; the installed `Ubuntu` distro (24.04.1) has `/dev/dxg` but **no `/mnt/wslg`**; `/usr/lib/wsl/lib` has CUDA/D3D12 libraries but **no `nvidia_icd.json`**. Docker Desktop engine 20.10.23 on WSL2 |
| V1 | VS-E status 2026-11-28 (`G:\sstre-tmp\status\VS-E.md`) | Linux build: clean Ubuntu 22.04 container, rc 0, 165 s at `c1537cfd`; never run on a GPU (POC-31 open) |

## 3. Target facts that drive the tests

- [DOC D1, D2] Van Gogh: Zen 2 4C/8T at 2.4–3.5 GHz; RDNA2 gfx1033 with 8 CUs at up to 1.6 GHz (1.6 TFLOPS FP32), so 8 ray accelerators [ASM: one per RDNA2 CU]; 16 GB LPDDR5 shared between CPU and GPU at 88 GB/s (LCD) or 102 GB/s (OLED) [D1 MT/s × 128 bit]; APU 4–15 W.
- [DOC D1, D16] Output 1280×800 (16:10). LCD 60 Hz, OLED up to 90 Hz. Valve's "playable" bar is 30 FPS at 800p in the default configuration.
- [DOC D3] RADV exposes `VK_KHR_ray_tracing_pipeline`, `VK_KHR_ray_query` and `VK_KHR_acceleration_structure` on gfx10.3+, which includes the Deck. [DOC D14, D15] RT works on the Deck in practice. The best public data point is Portal with RTX at about 30 FPS at 864×486 on its lowest settings. No controlled RTGL1 measurement exists.
- [SRC S2] Our Linux build has no RT. **Today, RT on a Deck is only possible with the Windows build under Proton** (winevulkan passes the KHR RT extensions through; [DOC D14] shows a DXR→vkd3d-proton→RADV path working, so the extensions do reach RADV through Proton).
- [SRC S3] An uncapped default of 500 FPS is a battery and thermal problem on a 15 W device. The menu and loading screens are included.

## 4. Options

Fidelity is how much of the Deck's behaviour the option reproduces. False-confidence risk is how likely a pass is to hide a real Deck failure.

### 4.1 Linux build under gamescope (1280×800, 60/40/30 Hz cap, FSR1)

| Setting | Viable? | Notes |
|---|---|---|
| WSL2/WSLg on this host | **No** | [EXP E1] WSLg is not installed (no `/mnt/wslg`) and there is no NVIDIA Vulkan ICD in `/usr/lib/wsl/lib`. In WSL, Vulkan on NVIDIA would need Mesa's `dzn` (Vulkan on D3D12; no KHR RT in [D3]) or an NVIDIA WSL ICD whose presence is inconsistent [DOC D9]. Gamescope's embedded mode needs DRM/KMS, which WSL does not have; its nested mode needs a Wayland/X host and DRM format modifiers [DOC D6, D7]. Updating WSL to the Store build might add WSLg, but that is a host change for the owner and does not fix the driver gap [ASM] |
| Docker container + lavapipe, `--backend headless` | **Unlikely** | [DOC D3] lavapipe does not list `VK_EXT_image_drm_format_modifier`. [DOC D7] headless gamescope fails without modifiers even on NVIDIA. Expect failure; worth a 10-minute check only as part of POC-66 [ASM] |
| Linux box with NVIDIA proprietary driver | Possible | [DOC D6] 515.43.04+, `nvidia-drm.modeset=1`; [DOC D8] scaling filters have crashed on recent NVIDIA drivers. Tests gamescope plumbing (window size, `-r` cap, `-F fsr`), not the Deck GPU |
| Linux box with an AMD RDNA2 dGPU or APU | Best pre-Deck option | Same driver family (RADV, ACO) as the Deck, and gamescope's primary target. Hardware we do not have |

**What it validates:** that the game accepts a 1280×800 16:10 output, behaves under an external frame cap, survives gamescope's Xwayland path, and how FSR1 upscaling looks on our HUD and fonts.
**What it does not validate:** Deck performance, RADV correctness on gfx1033, Steam's per-game QAM settings, the Deck panel.
**Cost:** zero on this host, because it does not work here. Needs a Linux box.
**False-confidence risk:** medium. Gamescope on NVIDIA takes a different code path (modifiers, async compute) from the Deck.

**Recommendation:** do not try to run gamescope on this Windows host. Emulate its effects inside the game instead (POC-68: render at 1280×800, cap the frame rate in the engine, use the engine's own FSR1 at 50–77 % scale), and keep real gamescope runs for an AMD Linux box or the Deck.

### 4.2 Windows build under Proton/Wine vs the native Linux build

| Aspect | Native Linux build | Windows build under Proton |
|---|---|---|
| RT | none (`SE1_RAYTRACING=0`) [SRC S2] | yes, if winevulkan exposes RTGL1's required extensions and features [ASM, D14 indirect] |
| Input path | SDL2 raw joystick API (RD-012 §3.1) | WinMM joystick through Wine's HID/SDL back end [ASM]; differs from both native paths |
| Windowing | SDL2 | Win32 through Wine (X11/Wayland drivers) |
| File system | case-sensitive | Wine maps Windows paths case-insensitively [ASM: standard Wine behaviour] |
| Runtime container | none by default for a non-Steam shortcut; optionally "Steam Linux Runtime" as a compatibility tool [ASM] | Proton 8–10 run in sniper, Proton 11+ in steamrt4 [DOC D18] |
| Libraries | must work against SteamOS's system libraries, or ship them | bundled with Proton |

**Which would Deck users actually run?** SSTRE is sideloaded: users add the engine as a non-Steam game, with their own game data (ADR-0002). For raster, the native build is the natural default and what ADR-0007 assumes. For RT, Proton is the only route until a Linux RTGL1 build exists. **So both will be used, and both need a test row.** [ASM]

**Emulation without a Deck:** both can run CPU-only in a `--network none` Linux container on lavapipe [DOC D3: lavapipe advertises the KHR RT extensions], including the Windows build under upstream Wine. Cost: low to medium (image built once, assets mounted read-only). Fidelity: functional only. False-confidence risk: high for anything driver-specific, because lavapipe is not RADV. POC-66 and POC-67 cover this.

### 4.3 SteamOS 3 in a virtual machine

| Hypervisor on this host | Vulkan in the guest | Verdict |
|---|---|---|
| QEMU/KVM (Linux host) | `virtio-gpu` + Venus forwards Vulkan to the host driver [DOC D11]; RT extensions not documented | Gaming Mode (the gamescope session) does not work in QEMU [DOC D10]. Desktop Mode, the Steam client and updates work |
| QEMU on Windows (WHPX) | No virglrenderer/Venus path on a Windows host [ASM; D11 lists only Linux and Android hosts] | Desktop Mode with software rendering at best |
| Hyper-V | GPU-P paravirtualisation is meant for WSL, not general Linux guests [ASM]; no Venus | Same as above |
| VirtualBox | VMSVGA; no Vulkan in Linux guests [ASM] | Same as above |

**Useful for:** checking that our packaging and launch scripts work on SteamOS's file layout and its read-only root file system [ASM], that the Steam client can add the engine as a non-Steam shortcut and pass launch options, and that a native build finds its libraries on SteamOS.
**Not useful for:** the gamescope session, the Deck's input stack, suspend/resume (the VM's virtual ACPI is not the Deck's s2idle path [ASM]), performance and RADV.
**Cost:** medium (OVMF and NVMe set-up, 8 GB RAM, ~20 GB disk, Valve's recovery image needs a download). **False-confidence risk:** high if anyone reads "runs in a SteamOS VM" as "runs on the Deck".

**Recommendation:** not worth it on this Windows host. It is worth one afternoon on a Linux box, and only for packaging and library checks (part of POC-73's runtime check).

### 4.4 GPU and driver correctness without AMD hardware

**a) Mesa lavapipe (CPU Vulkan).** [DOC D3] Lavapipe is Vulkan 1.4 and lists the KHR RT extensions, so in principle RTGL1 can initialise on it. It does not list `VK_EXT_image_drm_format_modifier` (gamescope). Whether it supports RTGL1's required `shaderResourceResidency` and `shaderFloat64` features [SRC S1] is **unknown**. A `vulkaninfo` run in POC-64 answers it.
- Validates: Vulkan API use against a second, independent driver; validation-layer cleanliness on a non-NVIDIA driver; the menu and level-load paths; screenshots for UI layout at 1280×800 (POC-68); headless CI on GitHub runners [DOC D22].
- Does not validate: RADV or ACO behaviour, performance (orders of magnitude slower [ASM]), memory pressure on a UMA device.
- Cost: low. CPU-heavy while running, so it must wait for `wait-quiet`. False-confidence risk: medium. Lavapipe tolerates some undefined behaviour that a real GPU does not, and the reverse [ASM].

**b) RADV null device (`RADV_FORCE_FAMILY`).** [DOC D5] Since a February 2020 commit (Mesa 20.1 cycle [ASM]), `RADV_FORCE_FAMILY=<family>` makes RADV create a device on a null winsys, without any AMD GPU, so that shaders can be compiled "without a AMD GPU". The current envvars page no longer lists the variable [DOC D4], but the null winsys is still maintained [DOC D5, GFX12 commit]. Whether `vangogh` is an accepted family name is **not verified** (the family table is in `src/amd/common/amd_family.h`). The planned container proof (§8) would have answered it.
- Use: in a Linux container, `RADV_FORCE_FAMILY=vangogh` with the RADV ICD selected (`VK_DRIVER_FILES`), then (1) `vulkaninfo` and `vulkaninfo --json` to dump what RADV would advertise for gfx1033, and (2) create every pipeline (raster and RTGL1 RT pipelines, from SPIR-V or a Fossilize capture) with `RADV_DEBUG=shaders` or shader statistics, to get ACO compile success, VGPR/SGPR use, spills and scratch for gfx1033.
- Validates: that every shader compiles for the Deck's ISA with the Deck's driver compiler, register pressure and spilling (a strong performance hint for RT shaders), and, roughly, the extension list and limits.
- Does not validate: execution. The null device cannot submit work, so there are no rendering results and no timings [ASM: the purpose stated in D5 is compile-only]. Its reported limits and memory heaps may differ from a real Deck [ASM], so compare them with a gpuinfo.org report (c).
- Cost: low (CPU only, short). False-confidence risk: low for compile failures; medium if someone reads "it compiles" as "it renders correctly".

**c) Vulkan Profiles layer with a Deck profile.** [DOC D12, D13] Take a gpuinfo.org report for "AMD Custom GPU 0405 (RADV VANGOGH)" (`api/v3/getprofile?id=<report>`), or the RADV null-device `vulkaninfo --json` output, and run the Windows build on the RTX 4070 with `VK_LAYER_KHRONOS_profiles` *below* the validation layer.
- What it catches: use of extensions, features, formats or limits that the RTX 4070 has but the Deck does not, for example NVIDIA-only extensions, larger descriptor or push-constant limits, or formats RADV does not support for a given usage. With `fail_on_error`, device creation fails loudly when the profile lacks something RTGL1 requires [DOC D12].
- What it cannot do: it only *restricts*, and it "does not enforce" [DOC D12]. Without the validation layer an application can still use what it was told is missing. It cannot emulate RADV bugs, ACO code generation, UMA memory behaviour or performance.
- The gpuinfo.org report ID for a current SteamOS Mesa was not retrieved (the device list is rendered by JavaScript). POC-64 does this.
- Cost: low (one GPU-locked short run per game per renderer). False-confidence risk: low for "missing extension"; nil for performance, because it says nothing about performance.

**d) Does the Deck support RTGL1's RT, and how fast?** Support: yes on the driver side for the core extensions [DOC D3]. The full required set [SRC S1] is unverified until POC-64 compares it. Speed: no RTGL1 data. Public data points: Portal with RTX at ~30 FPS at 864×486 on the lowest preset [DOC D14], and Quake II RTX "not well" in 2022 [DOC D15]. For scale, the RTX 4070 has roughly 18× the Deck's FP32 throughput and roughly 5–6× its memory bandwidth (NVIDIA's published 29 TFLOPS and 504 GB/s, not re-fetched here), and its RT cores are a later and stronger design than RDNA2's ray accelerators [ASM]. **Expectation [ASM]: RTGL1 path tracing at native 800p will be well below 30 FPS; RT on the Deck would need a low internal resolution plus FSR, and possibly reduced bounces.** That must be measured on hardware (POC-74) and must never be extrapolated from EXP-011/POC-35 numbers.

### 4.5 Performance approximation

| Can be estimated before hardware | Cannot be estimated |
|---|---|
| **CPU-side cost per frame** with a 4-core/8-thread affinity mask and a frequency cap on the i5-11600K, to see whether the main thread or a single thread would limit 30/40/60 FPS (POC-72) [ASM] | GPU frame time on RDNA2, both raster and RT |
| **Work counts that do not depend on the GPU:** draw calls, triangles, BLAS/TLAS sizes, texture memory, upload bytes per frame (RD-014 harness counters) | Memory-bandwidth contention between CPU and GPU on shared LPDDR5 |
| **Register pressure and spills** of every shader for gfx1033 (RADV null device, §4.4b) | Power draw, TDP behaviour (4–15 W), thermals, clock behaviour under load, battery life |
| **Texture budget fit:** the size of the raster and RT asset profiles against an assumed Deck GPU budget [ASM: a few GiB out of 16 GB shared] | gamescope composition cost, and the cost of FSR1 in gamescope |
| | Real frame pacing at 40 Hz on the LCD panel, or 90 Hz on the OLED panel |

- [DOC D23] No published, validated method maps a down-clocked desktop to Deck performance. The closest CPU analogue cited is a Ryzen 3 3100. The i5-11600K is a different microarchitecture (Rocket Lake) with different cache and memory, so even a CPU proxy is coarse [ASM].
- **NVIDIA results do not transfer.** A down-clocked RTX 4070 has a different architecture, driver, RT hardware, memory system and compiler. Down-clocking changes ratios unpredictably. This dossier recommends **no** GPU-proxy runs, because they would produce numbers that look precise and are not.
- Do not use a proxy number in a release note or a compatibility-matrix row. Use it only to rank risks.

### 4.6 Input: Steam Input and the Deck controller

- [DOC D19] The desktop Steam client's Big Picture mode *is* the Deck UI since February 2023. With an Xbox or DualSense pad and Steam Input enabled for a non-Steam shortcut, the game sees a Steam virtual pad, as on the Deck [ASM, as in RD-012 §3.3].
- **Usable proxy for:** controller-only menu navigation (POC-59), Steam Input's standard-pad presentation, the overlay and on-screen keyboard flow, and glyph switching when the active device changes (Valve requires glyphs to match the active input [DOC D16]).
- **Not a proxy for:** the Deck's trackpads, back grips, gyro, Deck-specific default templates, the Deck's own controller identity (USB IDs, SDL mappings), or Steam's per-game Deck configuration.
- Today the engine reads joysticks through WinMM (Windows) and raw SDL2 joysticks (Linux) (RD-012 §3.1), so a baseline now only records the status quo. The useful pass/fail comes after POC-58/59. POC-71 records the baseline and becomes the pre-Deck half of POC-60.

### 4.7 Constraints that need tests

| Constraint | What we can check now | Real hardware only |
|---|---|---|
| Battery, TDP | [SRC S3] default 500 FPS cap: set a sane default, cap menus, idle when unfocused; measure CPU and GPU busy time per frame on the PC at a 30/40/60 cap (less work per frame means less power [ASM]) | watts, battery hours, TDP-limited clocks |
| 800p UI scale, text legibility | 1280×800 screenshots (PC window, or lavapipe headless); measure the smallest glyph height against **9 px minimum, 12 px recommended** [DOC D16]; 16:10 HUD layout; FSR1 at 50–77 % scale | the 7" panel at ~30 cm, OLED HDR |
| Frame caps 60/40/30 | in-engine cap, and correct timing at 40 FPS (25 ms) with no judder in game logic [ASM] | QAM cap and refresh interaction, limiter latency [DOC D20] |
| Suspend/resume | process freeze: `SIGSTOP`/`SIGCONT` (Linux container) and process suspend (Windows) for 10 s, 60 s and 10 min; check the timer (RDTSC vs `CLOCK_MONOTONIC`, [SRC S4]), the simulation delta clamp, audio device recovery, Vulkan swapchain recreation | the real s2idle suspend: GPU power state, `VK_ERROR_DEVICE_LOST`, TSC behaviour across suspend, audio sink changes, Wi-Fi loss |
| Case sensitivity | Linux build in a container on ext4 (case-sensitive by default) with the real data layout mounted read-only; Windows build from an NTFS directory with `setCaseSensitiveInfo` [DOC D21]; a static scan of our own overlay files and of the `Include:` line SSTRE adds to the retail rendering-options menu script | SD card formats (ext4 by default on the Deck [ASM]) |
| Steam runtime containers | build in a Steam Runtime SDK image (sniper or steamrt4, pinned digest) [DOC D18]; run the native build inside the same runtime; Flatpak is out of scope unless a packaging decision asks for it | the SteamOS host's library versions and Steam's runtime selection for a non-Steam shortcut |
| Shared memory (UMA) | asset-profile sizes against an assumed budget; RADV null-device heap layout (indicative only) | real memory pressure, swap, BIOS UMA frame-buffer size |

### 4.8 CI options

| Option | Feasible? | Notes |
|---|---|---|
| GitHub Actions, Linux build inside a Steam Runtime SDK container | **Yes** | [DOC D18] OCI images; pin the digest. Proves the build works against the Deck-era runtime ABI. No game data needed |
| GitHub Actions + lavapipe `vulkaninfo` + SPIR-V checks | **Yes** | [DOC D22] used by other projects; slow but adequate for small jobs. Distro Mesa may be too old for lavapipe RT, so install a pinned newer Mesa [ASM] |
| GitHub Actions + RADV null device shader compile for `vangogh` | **Yes** (if §4.4b holds) | CPU-only; catches ACO compile failures and spill regressions per commit. Needs a SPIR-V/pipeline corpus that is our own code, never game data |
| GitHub Actions + engine run on lavapipe | **No** for now | The engine needs game data to reach the menu, and game data never goes into CI (backlog estimation assumptions). Local-only (POC-66) |
| GitHub Actions + gamescope headless | **No** | §4.1: no modifiers on lavapipe, and the headless back end is fragile [DOC D7] |

## 5. Comparison

| Option | Cost | Fidelity to Deck | False-confidence risk | Value now |
|---|---|---|---|---|
| RADV null device `vangogh` (caps + shader compile) | low, CPU | high for compile and ISA; none for execution | low | **high** |
| Profiles layer with a Deck profile on the RTX 4070 | low, short GPU runs | medium for "missing feature or limit" | low | **high** |
| 1280×800 output, frame caps, FSR1, legibility on the PC | low, short GPU runs | high for layout and text; none for performance | low | **high** |
| Lavapipe headless functional smoke (native build) | low to medium, CPU-heavy | low to medium | medium | medium |
| Case-sensitivity and path audit | low | high for that class of bug | low | medium |
| Process-freeze suspend proxy | low | low to medium | medium (it is not s2idle) | medium |
| Steam client Big Picture + Xbox/DualSense | low | medium for Steam Input; none for Deck-only controls | medium | medium (higher after POC-58/59) |
| Windows build under Wine on lavapipe | medium | low | high | low to medium (the RT-on-Deck route) |
| Steam Runtime SDK build in CI | low to medium | high for ABI and libraries | low | medium |
| CPU proxy (affinity + frequency cap) | low, needs quiet periods | low | medium to high | low to medium |
| gamescope on a Linux box | needs a box | medium (high on AMD) | medium | later |
| SteamOS 3 VM | medium | low (no Gaming Mode) | high | low |
| GPU down-clock proxy | low | very low | **high** | **do not do** |

## 6. What only real hardware can validate

1. Performance of raster and RT on RDNA2 gfx1033: frame time, 1 % lows, frame pacing at 30/40/60 (and 45/90 on OLED), FSR1 in gamescope versus in the engine.
2. RADV/ACO *execution* correctness on gfx1033: rendering artefacts, GPU hangs, device loss, RT results.
3. Power, TDP behaviour (4–15 W), thermals, clock behaviour, battery life.
4. Shared-memory pressure: the real VRAM budget, swapping and the BIOS UMA setting.
5. Real suspend/resume (s2idle) on the Deck, including GPU and audio recovery.
6. The Deck's controls: trackpads, back grips, gyro, the default Steam Input templates for the Deck, and glyph identity.
7. The gamescope session in Gaming Mode: QAM frame limit and refresh, per-game profiles, the overlay, focus handling.
8. Legibility on the 7" panel at hand-held distance (the 9 px rule is only the proxy), and OLED HDR behaviour.
9. Proton versus native on actual SteamOS (Mesa, Proton and runtime versions as shipped), including microSD storage performance.
10. Whether a non-Steam shortcut runs the native build in a Steam Linux Runtime container or on the host.

## 7. Recommendation

Set up now, ranked by value per cost:

1. **Deck capability profile and RADV `vangogh` offline compile (POC-64, POC-65).** CPU-only, no game data, can go into CI. Gives the one fact that matters most for RT on the Deck (does RTGL1's required set exist on gfx1033?) and catches shader compile failures and spilling for the Deck's ISA.
2. **Deck output emulation on the reference PC (POC-68).** 1280×800, 16:10, engine frame caps 30/40/60, FSR1 at Deck-like scales, a measured smallest glyph height, and a sane default instead of the 500 FPS cap [SRC S3]. Short, GPU-locked runs on hardware we have. Fixes real Deck-Verified-class issues ([DOC D16]) before the hardware arrives.
3. **Lavapipe headless smoke and path audit (POC-66, POC-69).** Native Linux build in a `--network none` container with the local data mounted read-only: reaches the menu, loads a level, runs a demo, screenshots at 1280×800, validation layer on, case-sensitive file system. First real run of the Linux build anywhere (POC-31 is still open).

Then: the Steam Input baseline (POC-71), the suspend proxy (POC-70), Steam Runtime SDK CI (POC-73), Wine-on-lavapipe for the RT route (POC-67) and the CPU proxy (POC-72). Do not run GPU down-clock proxies. Do not set up a SteamOS VM on this Windows host. Do not try gamescope under WSL here. Plan the hardware session (POC-74) now, so that it reuses everything above.

## 8. The container proof that was not run

Planned [EXP]: an Arch Linux container (closest to SteamOS's base) with `mesa`, `vulkan-radeon`, `vulkan-swrast`, `vulkan-tools`, `glslang` and `gamescope`. The image is built with network access and contains no game data. It then runs with `--network none` and does four things: `RADV_FORCE_FAMILY=vangogh vulkaninfo` (and `--json`); a 100-line C harness that creates a device and compiles one plain compute pipeline and one `GL_EXT_ray_query` compute pipeline on the RADV null device and on lavapipe; and a 60-second `gamescope --backend headless -W 1280 -H 800 -r 30 -F fsr` attempt on lavapipe.

The `wait-quiet` plus `docker build` step was **refused by the session's permission policy** (automated classifier), so nothing was built or run. The context (Dockerfile, harness, shaders, run script) is kept locally under the DECK-EMU scratch area on G: for POC-64/65; it is not committed. **No [EXP] result about Mesa behaviour exists in this dossier.** The only [EXP] item is the read-only host inspection E1.

## 9. Assumptions and unknowns

- U1: whether `vangogh` is accepted by `RADV_FORCE_FAMILY` in current Mesa, and how faithful the null device's limits are (POC-64/65).
- U2: whether lavapipe supports `shaderResourceResidency` and `shaderFloat64`, which RTGL1 requires [SRC S1] (POC-64).
- U3: whether winevulkan/Proton exposes every RTGL1 requirement (POC-67, then POC-74).
- U4: which runtime Steam uses for a non-Steam native shortcut by default.
- U5: the Mesa and Proton versions in the SteamOS release current when the Deck arrives. Record them in the POC-74 report.
- U6: whether the Linux build's timer is RDTSC or `CLOCK_MONOTONIC` (`Types.h:170-172`) and how each behaves across s2idle [SRC S4].

## 10. Decision dependencies

- Owner: buy or borrow a Linux box with an AMD RDNA2 GPU before the Deck arrives? (It would turn §4.1 and part of §6 into tests.)
- Owner/lead: whether the Linux RTGL1 build (RD-006 §2 RT "research") is in scope. If not, RT on the Deck means Proton only.
- Lead: CI budget for the Steam Runtime and RADV-compile jobs (POC-73).

## 11. Next steps

POC-64..74 in the [backlog](../backlog.md#steam-deck-before-hardware-rd-015).
