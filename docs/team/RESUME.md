# Where we are: read this after README.md, before your handoff

The one page of what's current. Every lead starts from the latest `claude/vigilant-galileo-l6jqyx`. Merge it first and keep your own workflow; this page says what has changed around you. Updated by the main session, 5 October 2026.

## 17 October: coordinator 59f6a467 (face 28, outfits 29, animation 35; the F1 merge first)
Rules new today: README "Effort by kind of work", "Focus"; the legal gate (`tools/legal/gate.py`, docs/team/legal.md top; passed.json is empty, so the first full run, 182 clip runs, happens on the F1 merge); lead_brief.md; memory nudge-owner-forward. API credits: about $32 left this month (judges only).
- **Outfits 29** (ad20dd321ebcf2bfc, worktree agent-a5ca10091b08dc429): **G3 COMMITTED @d34afe1b** (G3L2, the ARC_GLOVE default; COLOR_0 ch1 only, 443 hand vertices; Arcanist legal clean; 917 tests). Merge request held to land with animation's. Then its triage list at 1:1. The hand reshape is ON HOLD (the owner: a proper wrap hides the fingers); it takes proportion numbers only.
- **Animation 35** (aa037c6458cfa8937, worktree agent-af8dbda3195e438e4): G3 taken and imported (no repack needed); daggers judge 4/5 (left fist FAIL, a left-fist solver running); 50 Arcanist shots, then one max judge, then **MERGE REQUEST** (F1 = outfits d34afe1b + animation). After F1: chain_strike (the solver is blocked; the right path may move toward centre, approved), then the GRIP STANDARD (spec per type, a conform tool from grip_thin.py, the staff fist and the open staff hand in run/sprint, the viking sword and axe as proof), then the crossbow pistol grip built to the spec. About 11-15 h.
- **Face 28** (a208d8ffd755d6e0c, worktree agent-a2d632df7c7f21ec0): the nine mouth items CLOSED as known (logged "Big expressions" in docs/team/face.md); gum_low unhooked. **Hair is now its top item** (the owner: physics a mess, clipping at creation): a 1:1 shoot (every style spun in 45-degree steps, cinematic back views such as c03's walk to the warden, the play and close-up cameras in motion), one max judge, then the list and an estimate. After F1: rebuild heroine.glb on merged, cmp, tests, MERGE REQUEST.
- **Done today:** close-up zoom no longer turns her (d4d3aafe; she poses only with a framed screen in town or ember zones, or after 60 s idle; town menus don't pause, which is the owner's earlier rule).
- **Outfits' list after triage (7 of 8 closed at 1:1):** stockings tinted to the glove's ivory plus a plum welt; Arcanist boots (sole, heel, slimmer toe); Warden steel highlight at the Look (re-shoot first). About 5-8 h. Hand proportions measured, on hold (index distal 14 mm stubby; proximal taller than wide; the right hand has 36% fewer vertices than the left).
- **Camera items, no owner yet:** the seated close-up looks down onto the Arcanist's hat (no face): lower or re-angle it for seated poses, or fade the hat; at close-up zoom 1.0, facing 40, the staff head sits in front of her face.
- **Waiting for a slot:** cinematics (c03 runs straight into c04a's ember beat, plus the owner's other notes); the owner picks what follows when slots free (UI, combat, classes, Flare VFX).
- **On F1 merge:** `merge_lead.sh` for both, run `python tools/legal/gate.py --full` (background), tests, push, tell face.

## How the team runs now (README has the detail)

- **Tokens and quality, always (the owner, 7 October):** the cheapest route that ends at the same quality, as standing permission. Long-running leads are `su-lead-high`; max effort goes to short-lived `su-lead-max` judges and solvers (story writer and editor stay `su-lead-max` leads). Pass `effort` on every spawn. README "Working lean".

- 3 to 5 leads at once. The rest are paused with their handoffs and resumed in turn.
- Heavy work takes turns (`tools/turn.py`): `gpu` (ComfyUI, TRELLIS, MoGe, one at a time), `blender` (three), `godot` (four), with RAM and VRAM guards. A fair queue: ask again within 90 s to keep your place.
- Batch shots and look once. Hand off at about 300k tokens of context. Lean handoffs. See README "Working lean".
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


Older state (12-13 October and before): `docs/team/RESUME_ARCHIVE.md`. Read it only when a handoff points there.
