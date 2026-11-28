# RD-012: Modern input architecture and local multiplayer

| Field | Value |
|---|---|
| Dossier | RD-012 |
| Author | Track DOC-R (roadmap/planning), 2026-11-28 |
| Date | 2026-11-28 |
| Status | **Draft.** Desk research and source reading only. Nothing was built or tested; no controller hardware was used. |
| Feeds | backlog POC-57..62; proposed ADR on input abstraction ([backlog](../backlog.md#proposed-adrs-for-the-leadowner)) |
| Related | [RD-006 platforms](./RD-006-platforms.md), [RD-007 licensing](./RD-007-licensing.md), [RD-014 performance](./RD-014-rt-performance.md), [ADR-0007 platform strategy](../adr/0007-platform-strategy.md) |

## 1. Question and scope

The directive puts native controller support after graphical modernization, with single-player first. The PC version must become fully usable without keyboard and mouse. Questions:

1. What does the engine's input code do today on Windows and Linux?
2. Which cross-platform input library fits (SDL3 or an alternative), given existing dependencies and GPL-2.0-only licensing?
3. How do Steam Input and the Steam Deck interact with it?
4. How should the core stay platform-neutral so that console adapters could reuse it?
5. What would multi-controller play, four-player split-screen and ray-traced split-screen require?

## 2. Evidence

| ID | Source | Note |
|---|---|---|
| I1 | SeriousSamClassic-VK `510d36f` (local upstream clone): `SamTFE/Sources/Engine/Base/Input.h:32-38`, `Input.cpp`, `Base/Win32/Win32Input.cpp`, `Base/SDL/SDLInput.cpp`, `Engine/Engine.vcxproj:570`, `SamTFE/Sources/CMakeLists.txt:11-48`, `External/SDL2/` | [SRC] |
| I2 | Same tree, `SamTFE/Sources/GameMP/Game.h:191-201` (`SplitScreenCfg`), `Engine/Network/Network.h:31` (`NET_MAXLOCALPLAYERS 4`) | [SRC] |
| I3 | RTGL1 `v1.1.0` `Include/RTGL1/RTGL1.h:1147-1154` (`RgDrawFrameInfo`: one `view`/`projection` pair) | [SRC] |
| I4 | SDL licence, https://raw.githubusercontent.com/libsdl-org/SDL/main/LICENSE.txt (fetched 2026-11-28): zlib licence | [DOC] |
| I5 | FSF licence list, "zlib License … compatible with the GNU GPL", https://www.gnu.org/licenses/license-list.html#ZLib | [DOC], not re-fetched |
| I6 | SDL3 wiki: `CategoryGamepad`, `SDL_RumbleGamepad`, `SDL_RumbleGamepadTriggers` (Xbox One only), `SDL_GetGamepadSensorData`, https://wiki.libsdl.org/SDL3/CategoryGamepad | [DOC] |
| I7 | Valve Steamworks distribution terms on copyleft (RD-006 P21) and Steam Deck FAQ (RD-006 P23) | [DOC] via RD-006 |

## 3. Observed facts

### 3.1 Current engine input

- [SRC] I1: input is a single `CInput` object with a flat table of axes and buttons: keyboard, mouse, and up to `MAX_JOYSTICKS 8` joysticks with 6 axes (`XYZRUV`) and 32 buttons + 4 POV directions each (`Input.h:32-38`). Bindings in the game map named buttons/axes to actions; there is no concept of a "player's device".
- [SRC] I1: **on Windows** the build compiles `Base/Win32/Win32Input.cpp` (`Engine.vcxproj:570`), which reads joysticks through the legacy WinMM API (`joyGetNumDevs`, `joyGetPosEx`). There is no XInput, no hot-plug event, no rumble, and no standard layout: an Xbox pad appears as generic axes with the triggers combined on one axis (WinMM behaviour [ASM]).
- [SRC] I1: **on Linux/Unix** the CMake build uses SDL2 (system SDL2 by default, `USE_SYSTEM_SDL2`); `Base/SDL/SDLInput.cpp` uses the raw `SDL_Joystick*` API, not the SDL2 GameController (standard-layout) API. Vendored SDL2 headers are in `External/SDL2/`.
- [SRC] I2: SE1 already supports up to **four local players** in split-screen (`SSC_PLAY1..4`, `NET_MAXLOCALPLAYERS 4`). Each local player has its own controls file; any player can use any device, because all devices feed the one `CInput` table.
- [SRC] I3: RTGL1 v1.1.0 draws one view per `rgDrawFrame` (one view and projection matrix, one render size). Its denoiser and accumulation keep one history.

### 3.2 Libraries

| Option | Licence | Gamepad model | Hot-plug | Rumble | DS4/DualSense | Steam Deck | Platforms | Note |
|---|---|---|---|---|---|---|---|---|
| **SDL3** | zlib (I4), GPL-compatible (I5) | `SDL_Gamepad` standard layout + mapping DB, sensors, touchpad (I6) | yes | yes; trigger rumble on Xbox One pads only (I6) | yes (HIDAPI drivers) [DOC I6, details ASM] | yes (Deck controls via HIDAPI and Steam virtual pads) [ASM] | Windows, Linux, macOS; console ports of SDL exist privately under NDA [ASM] | also window/events; SDL2→SDL3 API changes are large |
| SDL2 (already used on Linux) | zlib | `SDL_GameController` | yes | yes | yes | yes | same | in maintenance mode once SDL3 shipped [ASM]; smallest change for Linux |
| GLFW | zlib | gamepad mapping, no rumble | partly | no | via mapping | via Steam | desktop only | too limited |
| XInput + own HID code | Windows SDK / various | Xbox only (XInput) | yes | yes | needs own HID driver | via Steam | Windows only | platform-specific core: rejected by the directive |
| Microsoft GameInput | proprietary redistributable [ASM] | modern Windows API | yes | yes | partial [ASM] | n/a | Windows (and Xbox GDK) | not GPL-friendly to bundle [ASM]; SDL3 can use it as a backend [DOC: SDL commit notes, via search] |
| Steam Input API (Steamworks) | proprietary | action sets | yes | yes | yes | yes | Steam only | RD-006 P21: copyleft "will be problematic"; keep out of the GPL engine |

### 3.3 Steam Input and Steam Deck

- [DOC] I7: the Deck runs non-Steam games through Proton or natively. Steam Input can present any controller to a game as a virtual Xbox-style pad, so a game that handles standard gamepads well works without the Steamworks SDK [ASM; standard Steam behaviour, verify on hardware].
- Validation needs the hardware; the directive requires a separate Deck validation (RD-006 Tier 2).

## 4. Assumptions and unknowns

- A1 [ASM]: SDL3's gamepad subsystem can be used for input only, while the engine keeps its own Win32 window on Windows; SDL3 works without owning the window for gamepads. Verify in the spike.
- A2 [ASM]: SDL3 builds from pinned source with CMake on Windows (MSVC v143) and Linux; static or bundled DLL. Distribution adds the zlib notice only.
- A3 [ASM]: the game's controls and menu code (Game/GameMP, SeriousSam menu) can take a "focused element + directional navigation" model without a rewrite of every menu.
- U1: button-prompt art. Platform-holder glyphs (Xbox, PlayStation symbols) are trademarks/artwork; the project needs its own or permissively licensed glyphs and must not copy console SDK assets. Check RD-007 trademark notes (Q12).
- U2: RT split-screen performance. N views at 1/N area each is roughly the same ray count as one view, but per-view fixed costs (denoiser passes, AS update per frame, upscaler) multiply, and RTGL1 v1.1.0 would need either N `rgDrawFrame` passes per present or a multi-view change.

## 5. Proposed architecture

```text
devices (SDL3 backend; later: console adapters)
   -> InputDevice (id, type, layout, caps: rumble, gyro, prompts)
   -> DeviceRouter (hot-plug, last-active device, per-player assignment)
   -> ActionMap per player (bindings, deadzones, curves, sensitivity; persisted)
   -> existing CInput axes/buttons (compatibility layer) -> game actions
   -> UI navigation layer (focus, directional moves, confirm/back) + prompt provider
```

- The core (router, action maps, UI navigation, prompt provider) has no platform API calls. A backend interface wraps SDL3 on PC. A console adapter would implement the same interface with the platform's input API (only if a console path is ever authorized, ADR-0007).
- Compatibility: keep the existing `CInput` table so old controls files and keyboard/mouse keep working; map gamepads into it first, then move the game to per-player action maps.

## 6. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| SDL3 on Windows conflicts with the engine's Win32 window/message loop | medium | input-only init; spike first (POC-57) |
| Breaking original controls/configs | high | compatibility layer; regression with original controls files |
| Prompt glyph trademark issues | medium | own glyph set; neutral labels (A/B/X/Y, Cross/Circle wording) after RD-007 review |
| RT split-screen too slow | medium | raster split-screen first; RT split-screen as an explicit option only if measured acceptable |
| Steam Deck unvalidated | medium | hardware needed (POC-31 already pending) |

## 7. Proposed experiments and success criteria

1. **POC-57 spike:** SDL3 (pinned tag, built from source) gamepad input in the Classic-VK build on Windows and Linux, input only. Pass: Xbox, DualShock 4 and DualSense pads detected with standard layout, hot-plug add/remove without restart, rumble on one pad, no change in keyboard/mouse behaviour; licence notice added; build reproducible from pinned source.
2. **POC-58/59 single-player:** pass criteria = the directive list, tested on Windows with three pad families and one generic USB pad: full menu navigation from start to in-game options without keyboard/mouse; analog move/look with configurable deadzone/sensitivity persisted across restarts; device switch within one frame of input; prompts change with the last active device.
3. **POC-60 Steam/Deck:** pass: same checklist through Steam Input on Windows; on the Deck (native Linux or Proton), complete a level start-to-end without keyboard.
4. **POC-61/62 local multiplayer:** pass: 4 pads assigned to 4 players, mixed keyboard/mouse + pads; raster split-screen 4 players at ≥ 60 FPS on the reference PC; RT split-screen feasibility report with measured cost for 2 and 4 views.

## 8. Recommendation

Use **SDL3** as the PC input backend for gamepads on both Windows and Linux, built from pinned source (zlib, GPL-compatible), behind an engine-owned, platform-neutral input interface. Replace the WinMM path on Windows; move Linux from raw SDL2 joysticks to the SDL3 gamepad API in the same change. Do not use the Steamworks SDK in the GPL engine; rely on Steam Input's standard-pad presentation. Do raster split-screen first; RT split-screen only after a feasibility measurement.

## 9. Decision dependencies

- Proposed input-abstraction ADR (SDL3, interface, compatibility layer, no Steamworks).
- Whether SDL3 also replaces SDL2 for windowing on Linux (separate decision; not required for input).
- Steam Deck hardware availability.

## 10. Next steps

POC-57..62 in the [backlog](../backlog.md#stage-m4--native-controller-support-directive-phase-3).
