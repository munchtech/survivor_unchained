# Where we are, 5 October 2026: how to pick back up

The team is running. The roster in `README.md` is the address list. Heavy work takes turns (`tools/turn.py`; see README). If you are picking up after a pause, resume the leads by SendMessage ("continue from your status page").

## The integration branch

`claude/vigilant-galileo-l6jqyx`, 663 tests green, pushed. The main session merges leads' branches as they push, and at each handoff.

## The heroine's outfits (main session)

- Done and committed: snug cups, the warden's straight straps, the stalker's top edge and binding, the arcanist's stockings, notch and neckline, soft nipple rises.
- **In progress: her skin tucked in, not cut away.** Skin under fitted pieces used to be deleted, which opened holes when pieces swung off her. Now `shaders/heroine_skin.gdshader` tucks it 6 mm inward, graded over two rings from each piece's edge (`heroine_outfits.py` writes the grades; `People.TuckSkin` sets the channel). It's built and the tests are green. It still needs seeing in motion before it's committed. Build with `bash $TEMP/hs/turn_build.sh` (full_build in turns).
- Then: the legal re-check on that build (the narrowed crotch strip, the areola-to-cup margins), then trimming cups to the smallest margin that holds; the arcanist's boot cuffs as level bands.

## The owner's standing decisions (see the memory and docs/legal)

- **Coverage is pixel-perfect.** Show as much as possible, cover exactly the areola, and never hide extra skin. Holes or see-through are worse than anything they fix. There were never any genital issues: the Warden's thong is by design, so add no briefs.
- **UI:** at most one ornamental frame per screen; layouts from research; greyboxes before art. Self, Pack, Storeroom and Trader are being redone.
- **The bodies stay** (TRELLIS from our own Krea 2 picture). Krea 2's US$1M cap applies.
- **Story fights:** small, specialised arenas with ARPG bosses and no endless phase. A loss wakes her at Chid's a day on. Redcowl can be spared or killed. Time passes outside fights. One rise in Act 1 only; later only with the rise skill.
- **US resident; Steam with honest AI disclosure.** The hymn comes from Suno. Final voices come from ElevenLabs, with no placeholders shipped.
