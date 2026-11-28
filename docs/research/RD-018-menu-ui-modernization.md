# RD-018: Menu asset enhancement and responsive UI architecture

| Field | Value |
|---|---|
| Dossier | RD-018 |
| Author | Track DOCS (planning), 2026-11-28; findings to be filled by tracks UI1 and A3 |
| Date | 2026-11-28 |
| Status | **Draft.** Problem statement, questions and plan only. No new source reading or measurement was made for this dossier. Findings are pending POC-86..88. Updated 2026-11-28 by track DOCS for owner [issue #21](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/issues/21): POC-88 is now the MSDF font track (§5.1), parallel to M1; the focus abstraction moved to POC-87. |
| Feeds | Proposed ADR-0017 resolution-independent UI layout ([backlog](../backlog.md#proposed-adrs-for-the-leadowner)); backlog POC-86, POC-87, POC-88 (MSDF font track, [issue #21](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/issues/21)) (and POC-93 if Preview4 is opened); roadmap criteria UI-1..UI-6 |
| Related | [ADR-0009 asset layers](../adr/0009-asset-layers.md) (UI approval and opt-in), [RD-003 AI pipeline](./RD-003-ai-pipeline.md), [RD-012 input](./RD-012-input-local-multiplayer.md) (M4 controller navigation), [RD-015 Steam Deck](./RD-015-steam-deck-pre-hardware-testing.md) (POC-68 legibility), [rendering defect register](../rendering-defects.md) RDF-008 |

Evidence labels: **[DOC]** published source, **[SRC]** read in our source trees, **[EXP]** observed in a run, **[ASM]** assumption or hypothesis, with what would verify it.

## 1. Question and scope

The owner directive of 2026-11-28 (evening, §6) adds a menu modernization track:

1. Which menu and interface assets exist, and which enhancement recipe suits each class without changing typography or artistic identity?
2. How does the existing menu layout and rendering work, and can resolution-independent positioning and configurable scaling be introduced **incrementally**, without replacing the whole menu architecture?
3. Are distance-field or vector fonts feasible and compatible with the original look and the licensing rules?
4. Which small abstractions (focus, navigable controls, selection state, device-independent interaction, dynamic button prompts) keep the menu ready for M4 controller navigation?

Out of scope: the full controller implementation (M4, [RD-012](./RD-012-input-local-multiplayer.md)), a redesign into an unrelated modern UI, and HUD redesign (HUD defects go to the defect register).

## 2. Problem as observed

- [ASM] The original menus were laid out for 4:3 resolutions of their time. Behaviour at 16:10, 16:9 and 21:9 and at 4K (stretching, clipping, small text, hit-region alignment) has not been measured in SSTRE. POC-87 measures it.
- [EXP] EXP-017: the RT rendering options are added to the rendering-options menu through one `Include:` line; in Vulkan mode they are listed (disabled). Lead-accepted known issue, register entry RDF-008.
- [EXP] EXP-017/EXP-018: automated menu navigation was inconclusive because the mouse pointer over the window changes the hover selection. [ASM] Mouse hover and keyboard focus share one selection state; relevant for the focus abstraction (Q7).
- [DOC] RD-015/POC-68: minimum on-screen glyph size targets for 1280×800 (≥ 9 px, target 12 px).

## 3. Evidence so far

| ID | Source | Revision / date |
|---|---|---|
| U1 | [EXP-017](../experiments/EXP-017-engine-integration.md) (menu `Include:` mechanism, M01–M04 runs) | integration `7eeed884` |
| U2 | [RD-015](./RD-015-steam-deck-pre-hardware-testing.md) §4.7 and POC-68 (legibility, 16:10) | 2026-11-28 |
| U3 | [ADR-0009](../adr/0009-asset-layers.md): interface assets need approval and are opt-in | accepted |
| U4 | Sources to read in POC-87: Classic-VK `SeriousSam/Menu*` (menu gadgets, layout), GameMP UI drawing, the engine font and draw-port code, for TFE and TSE | SSTRE-Engine `sprint2/integration` |

## 4. Investigation questions

| # | Question | Package |
|---|---|---|
| Q1 | Inventory by class: menu backgrounds, buttons, icons, logos, decorative elements, font textures, loading screens, interface animations, other menu textures. Counts per class and per game (public); per-asset list local | POC-86 |
| Q2 | Which classes contain text or glyphs (conservative upscaling only), which are pure art, which are animated? | POC-86 |
| Q3 | How are menu positions and sizes expressed today (absolute pixels, fractions of a 640×480-style virtual screen, per-gadget boxes)? Where is the aspect ratio applied, if anywhere? | POC-87 |
| Q4 | How is mouse hit detection computed, and does it use the same transform as drawing? | POC-87 |
| Q5 | How are fonts rendered (bitmap font textures, scaling, filtering), and what is the smallest glyph at each target resolution? | POC-87, POC-88 |
| Q6 | Which vector sources exist for the original typography (SVG glyph outlines, OpenType vector fonts), are they legally usable, and if not, can outlines be reconstructed locally from legally owned assets without publishing derivatives? (Original font textures are game data; any new font needs a compatible licence.) | POC-88 |
| Q6a | How are glyph metrics, kerning, character sets and localization handled today, and what must the MSDF metrics format carry to keep them? Can Unicode be supported without regressing existing localization? | POC-88 |
| Q7 | Is there one selection/focus state shared by mouse and keyboard? What minimal abstraction separates focus, navigable controls, selection, activation and prompts from the input device? | POC-87 |
| Q8 | Do RT, Vulkan and OpenGL draw the menu through the same path (consistency requirement)? | POC-87 |

## 5. Preferred implementation order

1. **Inventory and recipes** (POC-86, A3): UI recipes in Remaster-Toolkit/AssetCompiler. Preserve typography and artistic identity, transparency and layout; conservative upscaling for text-bearing textures; no AI-generated lettering, wrong glyphs or artificial outlines; no excessive sharpening; animation compatibility; automatic fallback to the original when QA fails; ADR-0009 approval and opt-in unchanged.
2. **Layout transform** (POC-87, UI1): a resolution-independent virtual layout space with aspect-preserving scaling (pillar/letter-boxing or anchored edges, not stretching), configurable UI scale, hit regions from the same transform, minimum text size on handheld resolutions, consistent in all renderers. Introduced incrementally in the existing menu code.
3. **Focus** (POC-87, UI1): focus/selection abstraction prepared for M4. No controller backend work in M0.1 beyond trivial preparation.
4. **MSDF fonts** (POC-88, UI1 + A3, parallel to M1): see §5.1. Preview3 and Preview4 ship with the original bitmap fonts.

If steps 1–3 are disproportionate, they move to Preview4 (POC-93) and do not delay Preview3.

### 5.1 MSDF font track (Origin: owner [issue #21](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/issues/21))

Owner decision: adopt resolution-independent vector-source fonts with offline multi-channel signed distance field (MSDF) atlas generation as the preferred font architecture.

- [EXP] EXP-023 §6: glyph UVs are pixel offsets divided by the texture width, so an upscaled bitmap atlas breaks glyph lookup without an engine change. The enhancement recipes therefore keep the original glyph atlases; resolution independence needs this track.
- **Sources:** SVG glyph outlines and OpenType vector fonts; existing, legally usable original outlines first. If none exist, local reconstruction from legally owned assets; nothing derivative is published unless cleared (RD-007, ADR-0006).
- **Look:** keep the recognizable original typography: glyph shapes, spacing, outlines, shadows and colour styling.
- **Offline generation:** MSDF atlases and glyph metrics generated by AssetCompiler/Remaster-Toolkit, deterministic and cached; no per-frame SVG rasterization.
- **Layout:** resolution-independent metrics, UVs and layout replace texture-pixel glyph positioning; alignment, kerning and the supported character sets are kept; Unicode is investigated without regressing localization.
- **Rendering:** one shared font abstraction for OpenGL, Vulkan and RT, preferably through the existing UI compositing path; menu and HUD; configurable UI scaling, ultrawide, 4K and Steam Deck (1280×800); no platform-specific dependency that would complicate future console ports.
- **Fallback and gates:** the original bitmap fonts stay a working fallback; ADR-0009 opt-in and all licensing, provenance and publication gates stay in force.
- **Schedule:** in parallel with M1; blocks neither Preview3 (bitmap fonts) nor the start of M1; integrated once validated. GPU validation follows the GPU-lock and quiet-mode rules and never runs during benchmark campaigns. Track UI1 finishes POC-87 first, then takes POC-88 with A3 for atlas generation.

## 6. Constraints

- Keep the recognizable Serious Sam interface; no redesign.
- Validate at 1280×720, 1280×800 (Steam Deck), 1920×1080, 2560×1440, 3440×1440 (ultrawide) and 3840×2160, in RT, Vulkan and OpenGL, for TFE and TSE.
- No stretched backgrounds or distorted elements; no overlapping, clipped or inaccessible elements; correct alignment of buttons and interactive regions; correct mouse hit detection after scaling.
- Compatible with the Steam Deck validation work of RD-015 and with M4 controller navigation; no decision that makes controller navigation harder.
- New behaviour behind a setting; original layout reproducible at 4:3.
- GATE-05: inventories with asset names stay local; public reports give class counts.

## 7. Acceptance criteria

Roadmap criteria **UI-1** (assets validated or fallen back, opt-in), **UI-2** (0 clipped/off-screen elements, 0 overlapping interactive regions, aspect error ≤ 1 % at all 6 resolutions in 3 renderers), **UI-3** (21:9 and 16:10), **UI-4** (bitmap fonts: cap height ≥ 9 px at 1280×800, target 12 px; no clipped or misaligned glyphs; the former sharpness clause moved to POC-88), **UI-5** (centre-click activates the item 100 %, hit-box offset ≤ 2 px), **UI-6** (all items reachable by directional focus navigation; design note), plus the POC-86..88 package criteria in the [backlog](../backlog.md#stage-m01--rendering-correctness-and-legacy-visual-modernization). They are met in Preview3 or in Preview4.

MSDF font track POC-88, owner acceptance criteria ([issue #21](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/issues/21), copied unchanged); not a Preview3/Preview4 criterion:

- Original typography remains recognizable and readable at 720p, 800p, 1080p, 1440p, ultrawide and 4K.
- Glyph lookup, layout and alignment remain correct at different scale factors; no clipping, atlas bleeding or missing supported glyphs.
- Original bitmap fallback and existing menu/HUD functionality remain operational.
- Rendering validated across the supported PC backends; Linux build compatibility maintained, Steam Deck runtime validation when hardware is available.
- Document visual comparisons, performance cost, atlas generation reproducibility, licensing constraints and remaining platform limitations.

Proposed measurable checks for these [ASM, lead to confirm]: at each of the 6 resolutions and at UI scales 1.0, 1.5 and 2.0, every glyph of the supported character sets renders (0 missing), 0 glyph quads are clipped, and no pixel of a neighbouring glyph is sampled (atlas padding ≥ the distance range); text bounding boxes are within 1 px of the layout dump; the former UI-4 sharpness clause (≥ 1 font texel per screen pixel, or the distance-field path) passes; two atlas builds from the same inputs are byte-identical; the bitmap fallback passes UI-2..UI-5 unchanged.

## 8. Hypotheses

| # | Hypothesis | What would verify it |
|---|---|---|
| H1 [ASM] | Menu coordinates are mostly expressed relative to the screen size, so one central transform (virtual space → screen with aspect preservation) fixes most layout issues without touching each menu | POC-87 source reading (Q3) and layout dump at 21:9 |
| H2 [ASM] | Hit detection uses the same coordinates as drawing, so a central transform keeps them aligned automatically | POC-87 click test (UI-5) |
| H3 [ASM] | Bitmap fonts become blurry at 4K because they are magnified with bilinear filtering; enhanced bitmap atlases cannot fix this without an engine change (EXP-023), so MSDF is the route | POC-88 sharpness measurement at 3840×2160, bitmap vs MSDF |
| H5 [ASM] | MSDF rendering costs well under 0.1 ms per frame for menu and HUD text at 2560×1440 | POC-88 A/B frame time, outside benchmark campaigns |
| H4 [ASM] | Conservative (non-generative) upscaling is sufficient for text-bearing menu textures; generative SR is limited to text-free backgrounds, if used at all | POC-86 glyph QA results |

## 9. Findings

Pending POC-86 (inventory, UI recipes; track A3, EXP-023), POC-87 (responsive scaling; track UI1, EXP-024) (including the focus abstraction) and POC-88 (MSDF font track; tracks UI1 and A3, parallel to M1, [issue #21](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/issues/21)).

## 10. Decision dependencies

- Proposed ADR-0017 (layout model); ADR-0009 for UI asset approval.
- Lead: Preview3 vs Preview4 for menu work (POC-93).
- Owner: any new font with a new licence (direction decided: MSDF, [issue #21](https://github.com/Handelsonderneming-S-D-Broekhoven/SSTRE/issues/21)); any visible change of the original menu look beyond scaling.

## 11. Next steps

POC-86 and POC-87 in parallel for Preview3/Preview4; then POC-88 (MSDF fonts) in parallel with M1; checkpoints for high-resolution and ultrawide menus come from POC-89. See the [backlog](../backlog.md#stage-m01--rendering-correctness-and-legacy-visual-modernization).
