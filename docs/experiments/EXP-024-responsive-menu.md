# EXP-024: Responsive menu scaling (POC-87) and font/focus note (POC-88)

| Field | Value |
|---|---|
| Date | 2026-11-28 |
| Backlog items | POC-87 (responsive menu), POC-88 (SDF/vector font feasibility, menu focus abstraction). Dossier RD-018, proposed ADR-0017 |
| Status | **POC-87: dev-stage pass** (7 of 7 questions answered; default `sam_iUILayout 1` justified). **POC-88: design note and focus API only** (no MSDF code, by directive) |
| Engine | SSTRE-Engine `m01/ui1` @ `9cafcd29` (base `sprint2/integration` @ `7eeed884`). Not pushed |
| Environment | Windows 11, i5-11600K, RTX 4070, Release x64, TFE and TSE runtimes with original (non-enhanced) data, network off |
| Evidence labels | [SRC] source read, [EXP] measured in a run, [ASM] assumption or computation |

## Architecture analysis (POC-87) [SRC]

All references are SSTRE-Engine `sprint2/integration` @ `7eeed884`, `SamTFE/Sources/...`; `SamTSE/Sources/SeriousSam` is byte-identical except project files, and `GameMP/Console.cpp` differs in two background lines.

1. **Coordinates.** Every gadget has a `mg_boxOnScreen` in normalised [0,1]x[0,1] space. `FloatBoxToPixBox` (`SeriousSam/MenuPrinting.cpp:263`) multiplies x by drawport width and y by drawport height. The menu drawport is the whole window (`CDrawPort dpMenu(pdp, TRUE)`, `Menu.cpp:2791`), so the layout stretches horizontally with the window aspect.
2. **Fonts.** `SetFontTitle/Big/Medium` (`MenuPrinting.cpp:282-301`) scale by window width only, while row heights are fractions of window height. On wide windows text grows faster than rows.
3. **Per-aspect fix-ups.** `SetAdjusters()` (`SeriousSam.cpp:573`) holds 15 menu constants and 4 game constants (weapon/player FOV, HUD armour/frag heights) for five aspect windows: 4:3, 5:4, 16:10, 16:9, 21:9 (2.32-2.34). Any other ratio keeps compiled-in defaults that match none of the tables. 3440x1440 (2.389) and 2560x1080 (2.370) fall in no window.
4. **Hit testing.** Reuses the render box of the same frame (`Menu.cpp:2975`), consistent as long as both use the same drawport. `CMGSlider::GetSliderBox` and `CMGVarButton::GetSliderBox` (`MenuGadgets.cpp:867,930`) used the view drawport instead; they coincided only because both covered the full window.
5. **Backgrounds and logos.** Clouds/grid tile with a uniform scale. The main logo uses `Min(W/640,H/480)`. The corner logos, the engine logo and the level thumbnail scaled x by `W/640` and y by `H/480` and were stretched on any non-4:3 window.
6. **Fixed-pixel text.** Console and console "last lines" use the console font at scale 1.0 (`GameMP/Console.cpp:164,179`), about 0.6 % of screen height at 2160 lines.
7. **HUD.** `EntitiesMP/Common/HUD.cpp:810` scales by `width/640`. On 21:9 the HUD is about 1.34x larger relative to screen height than on 16:9. Outside UI1's write scope; recorded as an open defect.
8. **Focus model.** Already explicit and device-neutral: per-gadget `mg_pmgUp/Down/Left/Right`, `mg_bFocused`, `gm_pmgSelectedByDefault`; `CGameMenu::OnKeyDown` (`Menu.cpp:3294`) walks the graph. Mouse hover sets focus (`MenuUpdateMouseFocus`, `Menu.cpp:2675`).

**Conclusion.** The layout is already resolution-independent on one axis. Aspect safety needs one change: put the gadgets on a centred canvas with a clamped aspect, feed the canvas ratio to the existing per-aspect tables, and move the cursor into canvas space. The menu architecture is not replaced.

## Implementation (`m01/ui1` @ `9cafcd29`)

- `sam_iUILayout` (persistent, default **1**; 0 = legacy): gadgets on a centred canvas, aspect clamped to [`sam_fUIMinAspect` 1.25, `sam_fUIMaxAspect` 1.7778]; background on the full window.
- `SetAdjusters` split into a menu table (canvas ratio, continuous buckets in layout 1) and a game table (full window ratio, legacy exact windows, unchanged).
- Mouse coordinates translated to canvas space; slider hit boxes use the canvas (`MenuFloatBoxToPixBox`).
- Logos and thumbnail keep their aspect in layout 1.
- `con_fTextScale` (default 0 = auto integer floor(H/720)) for console and last lines.
- `sam_iUIDebugLayout` 1 = draw hit/text boxes, 2 = log `UILAYOUT` / `UIGADGET` / `UIFOCUS` lines (harness input).
- POC-88b: `MenuNavigate(MenuNavCommand)` and `MenuGetFocusedGadget()`, no behaviour change.

## Questions and results (dev stage, one GPU-lock hold, about 80 s per run)

Harness metrics: `clip` = a text box leaves the window; `misaligned` = gadget box off the canvas grid; `overlap` = a gadget's text cell box intersects the next gadget's box; `mintext` = smallest text cell height in px. Mouse test: pointer at each of 8 Main-menu gadget centres, the logged `UIFOCUS` box must be that gadget. Keyboard test: 8 down-presses must give 8 distinct focus changes.

| Q | Config | Question | Result | Evidence [EXP] |
|---|---|---|---|---|
| Q1 | TFE Vulkan 3440x1440, layout 1 | Ultrawide: no clip/misalignment; mouse hit = focus; keyboard walk | **pass** (metric caveat below) | canvas 2560x1440 at x=440, menu bucket 2; clip=0, misaligned=0 on 7 menus; mouse 8/8, keyboard 8/8 |
| Q2 | TFE Vulkan 1280x800 windowed, layout 1 | Minimum text >= 12 px (Deck) and checks pass | **pass** | mintext 22 px (46 titles); clip=0, misaligned=0; mouse 8/8, keyboard 8/8 |
| Q3 | TFE Vulkan 2560x1440 (client 2560x1415), layout 1 | 16:9 canvas equals the window | **pass** | window ratio 1.809 clamped to canvas 2516x1415 (1.778) at x=22; clip=0; mouse and keyboard 8/8 |
| Q4 | TFE Vulkan 3440x1440, layout 0 | Does the legacy ultrawide defect reproduce (is default 1 justified)? | **pass** (defect reproduced) | bucket -1 (compiled defaults); clip=1 on 5 of 7 menus (Back clipped at the bottom edge in VideoOptions); VideoOptions overlap 8 vs 0 in layout 1; rows 3096 px wide; mintext 60/124 vs 44/92 |
| Q5 | TFE OpenGL 3440x1440, layout 1 | Same result as Q1 on GL | **pass** | UILAYOUT numbers identical to Q1; mouse and keyboard 8/8 |
| Q6 | TFE RT 3440x1440, layout 1 | Same result as Q1 on RT | **pass** | identical numbers; menu drawn in the swapchain UI pass, 0 RTGL1 errors, watchdog ok |
| Q7 | TSE Vulkan 3440x1440, layout 1 | TSE data and menus behave like TFE | **pass** | identical numbers; TSE background fills the window, gadgets on the canvas |

Ledger ids: `20261128201350-UI1-{9792,5229,4771,8918,4944,7888,9643}` (Q1 to Q7).

**Caveat on `overlap`.** Main, Options, SinglePlayer and SinglePlayerNew report overlap 4 to 7 in layout 1 and at 1280x800 as well. The text cell (font cell height) is taller than the row pitch; the visible ink does not overlap (checked on screenshots). Legacy is worse (Q4: 8 in VideoOptions where layout 1 has 0). Q1's "no overlap" criterion is therefore judged on clip, misalignment and the screenshots, not on the raw overlap count. The metric should use ink bounds before Integration.

### Verdict on default layout 1

**Justified [EXP].** On 21:9, legacy (Q4) clips text on 5 of 7 menus, stretches rows to 3096 px and falls back to compiled defaults (bucket -1). Layout 1 (Q1) has no clip or misalignment, rows sit on a 16:9 canvas, and the result is identical on OpenGL, Vulkan, RT and TSE. On 16:9 windows (Q3) the canvas equals the window, so nothing changes there. Layout 0 stays available as a cvar. Residual risk: only the Main-menu mouse test and the keyboard walk were measured; the slider hit-box fix is verified by code only ([SRC]) and not exercised by a pointer drag (deferred).

### Text size [EXP + ASM]

At 1280x800 the smallest menu text is 22 px (Q2) [EXP], above the 12 px Deck recommendation. At 1280x720 it computes to about 20 px, at 1920x1080 about 34 px, at 2160 lines about 67 px, scaling linearly with canvas height [ASM, from Q2 and Q3: 22 and 44 px]. Console text (8 px cell, `con_fTextScale` auto) is 9 px at 800 lines [ASM, from the glyph cell size]: the 9 px Deck minimum is met, the 12 px recommendation is not. Console size is a cvar.

### Observations from screenshots

- In the debug capture the console "last lines" overlap the corner logo at the bottom left on 1440-line windows (console scale 2). Cosmetic; also present with layout 0.
- VideoOptions showed the resolution value `3440x1935` for the borderless window; this is the menu's own 16:9 list entry and was not investigated.
- The debug text overlay covers the top 65 px of every screenshot (artefact of `sam_iUIDebugLayout`).

## Coverage

| Item | Status |
|---|---|
| 3440x1440 TFE Vulkan layout 1 (Q1) and layout 0 (Q4) | executed |
| 1280x800 TFE Vulkan (Q2), 2560x1440 (Q3) | executed |
| 3440x1440 OpenGL (Q5), RT (Q6), TSE Vulkan (Q7) | executed |
| 1280x720, 1920x1080, 3840x2160 (all 16:9) | **not run**: covered by computed layout (canvas equals the window, same bucket logic as Q3; text sizes computed above) |
| 1280x800 on OpenGL/RT, TSE at 1280x800 | skipped (layout code is back-end independent; Q5 and Q6 equal Q1 at 3440x1440) |
| Slider drag, PlayerProfile menu (not reached by the harness) | deferred |
| Game-bucket FOV/HUD on 21:9 | deferred (HUD outside UI1 scope, see defects) |
| Full 6-size x 3-renderer x TFE/TSE matrix | deferred to the Preview3 Integration candidate (testing policy) |
| Reused earlier results | none (no earlier UI1 run existed) |
| Invalidated | none |

## Open defects

1. **UI-D1 (HUD on ultrawide):** the HUD scales by width/640, 1.34x larger relative to height on 21:9 than on 16:9. Owner: HUD code (EntitiesMP), not UI1.
2. **UI-D2 (game adjusters):** the game table still uses the legacy exact aspect windows, so at 2.389 the game bucket is -1 (compiled defaults) for weapon/player FOV and HUD armour/frag heights. Left unchanged in M0.1 on purpose (gameplay-visible).
3. **UI-D3:** harness `overlap` uses the text cell, not ink bounds (see caveat).
4. **UI-D4:** console last lines overlap the corner logo on tall windows.
5. Font atlas texture overrides must wait for the P3 fix below.

## POC-88a: MSDF font track, design note (no implementation in M0.1)

Scope: vector-source fonts (legally usable outlines first); offline MSDF atlas and metrics generation in the AssetCompiler/Toolkit (with A3); one font abstraction across OpenGL, Vulkan and RT through the UI compositing path; bitmap fonts kept as the fallback; ADR-0009 opt-in. Parallel to M1, **not a Preview3 blocker**.

### 1. Where glyph lookup and positioning depend on texture pixels [SRC, `SamTFE/Sources/Engine/Graphics`, `7eeed884`]

| # | Place | Dependency | Consequence for an MSDF or re-rasterised atlas |
|---|---|---|---|
| P1 | `Font.h:36-37`, `Font.cpp:40-46` `CFontCharData` | `fcd_pixXOffset/YOffset` = glyph position in atlas pixels; `fcd_pixStart/End` = ink span used for the advance | the lookup table is tied to the original atlas grid |
| P2 | `Font.h:52-53` | cell size in atlas pixels doubles as the layout unit | the layout unit must stay, or every caller changes |
| P3 | `DrawPort.cpp:1485-1486` | `fCorrectionU/V = 1/GetPixWidth()/GetPixHeight()` of the loaded texture | an atlas of another resolution samples the wrong glyphs; this also breaks a plain upscaled bitmap atlas, so **font textures must not be overridden** until fixed |
| P4 | `DrawPort.cpp:1466-1471, 1590-1597, 1613-1614` | quad is the full cell scaled by 16.16 fixed point; advance truncated per glyph | the quad must cover the glyph plus the distance-field margin; integer pixel positions (up to 1 px drift per glyph at high scale) |
| P5 | `DrawPort.cpp:1403-1441` `GetTextWidth` | same pixel metrics as P4 | must stay bit-identical to P4 or centring and right alignment move |
| P6 | callers | line heights from `fd_pixCharHeight` (`GameMP/Console.cpp`), cursor offsets (`MenuGadgets.cpp`), HUD, Computer, credits, the bold/italic quads (`DrawPort.cpp:1626-1652`) | about 20 files read the bitmap metrics; **keep `CFontData`'s metric API** |
| P7 | `Font.cpp:135-195` `CFontData::Make` | builds the table from a texture grid (tools only) | the MSDF generator replaces it offline |
| P8 | render back ends | PutText goes through the `gfx*` wrapper to OpenGL fixed function or Classic-VK; RT turns DrawPort quads into `CHudElementInfo`, `SSRT::ProcessHudElement`, `rgUploadRasterizedGeometry` with blend, swapchain render type (`Raytracing/SSRT.cpp:490-533`) | OpenGL has no font shader; the RTGL1 rasterised pass has fixed shaders but supports `STATE_ALPHA_TEST` |

### 2. Abstraction and integration points

- Keep `CFontData` as the single font object, with an optional `CFontMSDF *fd_pmsdf` face (atlas texture, per-glyph float plane/atlas bounds, distance range, optional kerning) loaded from a sidecar next to the font in the opt-in asset layer. Missing or invalid sidecar: `fd_pmsdf = NULL` and the bitmap path runs unchanged; a cvar forces bitmap.
- Layout compatibility by construction: the generator expresses each glyph in the legacy cell coordinate system (P1/P2), so `GetTextWidth`, advances and line heights stay bit-identical to the bitmap font; only rasterisation changes.
- One code path in `CDrawPort::PutText`: a branch at P3/P4 takes UVs from the MSDF table, enlarges the quad by the field margin and sets a font material flag.
  - Tier 1, all back ends: MTSDF atlas (RGB = MSDF, A = true SDF) drawn with alpha test at 0.5 on A. Works in OpenGL fixed function, Classic-VK and RTGL1 (`RG_RASTERIZED_GEOMETRY_STATE_ALPHA_TEST`) without an RTGL1 change. Crisp but aliased edges.
  - Tier 2, Vulkan and RT: font fragment shader with `median(r,g,b)` and screen-space-range `smoothstep`. Vulkan gets a pipeline variant; RT needs an RTGL1 rasterised-pass shader variant (lead-coordinated, generic, may go upstream). OpenGL stays at tier 1.
- Compositing: fonts stay in the existing UI pass (raster after the 3D view; RT as swapchain-type rasterised geometry), so HUD/menu ordering and screenshots behave as today.
- Linux: engine side is C++ plus SPIR-V only; generation is offline in the Toolkit container (`--network none`), so no new runtime dependency.

### 3. Vector sources (licensing first)

1. [ASM] No vector original of the menu/console fonts is known in the retail data; they are bitmap atlases.
2. First choice: a licensed or OFL face, only if the owner accepts the different look (distributable).
3. Otherwise traced outlines from the owner's local bitmaps (potrace, GPL-2.0-or-later, compatible with the GPL-3.0 Toolkit, or own contour tracing), then msdfgen (MIT). The output is a local derivative like the AI texture layer: never distributed, opt-in. Tracing gives smooth outlines of the original shapes, not new lettering; each glyph sheet needs a visual QA gate (A3).

### 4. Acceptance mapping

| Criterion | How tested |
|---|---|
| readable at 720p/800p/1080p/1440p/ultrawide/4K | POC-87 harness matrix with captures; `UILAYOUT mintext` (Deck >= 9 px, 12 px recommended) |
| correct glyph lookup, layout, alignment | `UIGADGET` text boxes: bitmap vs MSDF identical (P5 invariant); a glyph sheet of all 256 codes per font |
| no clipping, bleeding, missing glyphs | atlas padding >= distance range + 1; generator check that every non-empty cell has an outline; harness clip flags |
| bitmap fallback works | runs without the sidecar, with the force-bitmap cvar, and with a corrupt sidecar |
| all PC back ends | OpenGL tier 1, Vulkan tier 1+2, RT tier 1 (+2) |
| Linux build | container build of the engine changes (VS-E procedure) |

### 5. Estimate

| Work package | pd |
|---|---|
| Toolkit/AssetCompiler (A3): glyph extraction, tracing, msdfgen atlas and metrics in legacy cell space, QA sheet | 3.0 |
| Engine: `CFontMSDF` loader, sidecar, fallback, PutText branch, P3 fix | 1.5 |
| Tier 1 alpha-test path (GL/VK/RT) | 0.5 |
| Tier 2 Vulkan font pipeline | 1.5 |
| Tier 2 RT (RTGL1 shader variant, lead-coordinated) | 1.5 |
| Validation matrix + Linux build | 1.5 |
| **Total** | **about 9.5 pd** (tier 1 only: about 6.5 pd) |

Separate prerequisite, useful without MSDF: the **P3 fix** (UV divisor from the original atlas size, stored in a sidecar or derived from the glyph table [ASM: `NextPow2(max(xOffset)+cellW)` matches the retail atlases, unverified]); about 0.5 pd, after which A3 may override font textures safely.

## POC-88b: menu focus abstraction (prepared, no controller code)

The focus model is already device-neutral [SRC `SeriousSam/Menu.cpp:3294`]. Added with no behaviour change: `enum MenuNavCommand {UP, DOWN, LEFT, RIGHT, ACCEPT, BACK, PAGEUP, PAGEDOWN}`, `MenuNavigate(cmd)` (routes into the keyboard path so lists, sliders and popups behave identically) and `MenuGetFocusedGadget()`. The keyboard focus walk was verified in all 7 runs (8/8). Gaps for a controller track: text entry needs an on-screen or Steam keyboard; key-binding gadgets wait for a raw key; mouse hover takes focus whenever the pointer moves (`_bMouseUsedLast`), so a pad backend must keep it FALSE.

## Reproduce (local)

Build with `build-win.ps1`; runs with `run-menu.ps1`; the dev session `session.ps1` runs under `gpu-lock.ps1 run -Owner UI1` with the game watchdog built in (all under `G:\sstre-tmp\ui1\scripts\`). Screenshots and logs stay local (`G:\sstre-tmp\ui1\runs\`).
