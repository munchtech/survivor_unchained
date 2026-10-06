# Where we are: read this after README.md, before your handoff

The one page of what's current. Every lead starts from the latest `claude/vigilant-galileo-l6jqyx`. Merge it first and keep your own workflow; this page says what has changed around you. Updated by the main session, 5 October 2026.

## How the team runs now (README has the detail)

- 3 to 5 leads at once. The rest are paused with their handoffs and resumed in turn.
- Heavy work takes turns (`tools/turn.py`): `gpu` (ComfyUI, TRELLIS, MoGe, one at a time), `blender` (two), `godot` (three). A fair queue: ask again within 90 s to keep your place.
- Batch shots and look once. Hand off at about 500k tokens of context. Lean handoffs.
- Before you show the main session anything, run a strict self-critique at 1:1 and send the findings with it.

## The owner's standing decisions (newest first)

- **UI:**
  - Panels over the live world, not full pages ("we like to see our beautiful game").
  - No fades: panels end cleanly, on a ground ever so slightly translucent (about 0.9).
  - No "AI boxes": data is type on the page; stats are a ledger line.
  - Minimal dead space, strict symmetry and grid.
  - Soul through world objects that mean something: the chain (Survivor *Unchained*), coals, the watch-lamp, painted pieces, used sparingly.
  - Toasts, tips and ground labels are stylised type on the world, with no plates.
- **Sound:** CC0 is acceptable (logged in ASSET_PROVENANCE). Our own is best. The owner may send real recordings to `incoming/`.
- **Coverage:** pixel-perfect. Cover exactly what must be covered (the areola, a 2.4 cm midline strip), show everything else, and never a hole or see-through. Her skin under garments is tucked in the shader, not cut. There were never genital issues. Fit means tighter, not bigger.
- **Loot:** fewer, better drops; legendaries (some early) and sets; item level by zone; a filter; slotless stores (pouch, satchel, key ring, belt, purse).
- **Story fights:** small, specialised arenas with ARPG bosses and no endless phase. A loss wakes her at Chid's a day on. Redcowl can be spared or killed. One rise in Act 1; later only via the rise skill.
- **Models:** everything ours over time. The boar is ours (creatures lead). The heroine's and hero's bodies stay. Never Hunyuan3D, free web tools, or real people or others' art. Krea 2 is allowed (US$1M cap).
- **Cinematics:** a cinematic ending in play hands over her exact pose and facing, mid-stride, with the camera easing into play.
- **Animation:** natural, correct motion; be sceptical; sign off per clip.
- **The bar:** "we are striving for perfection". Improved isn't enough.

## Current state by area: wound down 6 October 2026 (usage low); restart here

Integration is green (774 tests) and pushed. Every lead below stopped at a clean point with a handoff; start each as a fresh successor from its handoff (the main session checks context on every report and hands off at 500k).

**Restart in this order** (3 to 5 at a time, see README):
1. **The face** (docs/handoff/face.md): v11 merged (b8ab21f9; no refit needed). Tones and irises meet the bar; her eyes and mouth read at play zoom. Short of the bar: grain at the finest scale (0.65, the AA's limit), her lips thinner and paler than her portrait's, the other faces' brows too light, skin a little smooth. Her head carried 8 degrees up in play needs animation's sign-off. Next: v12 to the bar, then face paints and sliders (freckles as a Look control; defaults hers 0.18, Hard-won 0.12, Wildling 0.1, Fey 0.06), then hair (many rounds; the hair "helmet" and pale temples are the hair pass's).
2. **Story** (docs/handoff/story.md): Act 1 rewritten in the data (e5d65111). Next: a fresh editor reads the Act 1 draft; the owner picks the love scenes (docs/story/LOVE_SCENES.md, A or B; the writer recommends the lovers' own lines); then Act 2, then Act 3. Voice: docs/voice/RERECORD.md lists Sella's and Rook's re-records; hold Holloway, Brannoc, Maeca, Vonnra, Harlan and the narrator.
3. **Rendering** (docs/handoff/performance.md): her motion judder found and fixed (positions drawn between ticks, bb86717b). Next: merge `perf-seethrough-wip` (the soft see-through, untested), run the A/B batch, choose the AA (expected: keep a temporal AA as the base for hair), exact motion data for her hair.
4. **The owner's HUD notes** (OWNER_NOTES: the HUD as the keystone, Journal and Map in the half panel, tips at full size): UI design and UI art, from their handoffs.
5. Then combat and animation (the crowd push), the experience director, arena art (the Vault's hall, the Roost), creatures (the boar), cinematics, skills VFX, crafting, loot, the male hero.

**Deferred by the owner:** the artists' kit (OWNER_NOTES); legal (paused until submission).
