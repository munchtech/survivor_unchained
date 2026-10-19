# SB00 soundtrack: where every sound comes from

`render.py` builds `godot/art/storybook/sb00/audio/sb00_bed.ogg`, `sb00_music.ogg` and `sb00_fx.ogg` from `sb00_cues.json`. Nothing was downloaded for it, and no generative model was used. Every input is one of three things:

1. **Ours: synthesis written for the game.** The Python in this folder (numpy and scipy). Part of it ports the game's own synthesized sounds from `godot/src/Audio/Sfx.cs` and `Synth.cs` (ASSET_PROVENANCE AU-05, "Our work").
2. **The game's CC0 recordings** in `godot/art/sound/` (AU-01, AU-02 and AU-06 in `docs/legal/ASSET_PROVENANCE.md`). The LTX-made `tell_*` takes (AU-03) are not used.
3. **The game's placeholder voice take** `godot/art/vo/warden/dlg.cin_none_cross.call.0.ogg` (AU-04: Maya1, Seed-VC and VoxCPM2, placeholder until the final voices). When the final Warden take replaces it, re-render: `p10_song` reads the file by path, and MOTIF.md says what the new take should sing.

Rooms (the reverbs) are synthesized impulse responses (`dsp.room_ir`), not sampled spaces.

## Per sound

| Cue(s) | What it is | Source |
|---|---|---|
| `drone` | The Night drone on D (D2, A2, D3 saws with a breath of noise) | Ours: `instruments.drone`, after `Sfx.Cine("drone")` moved to the Night's root |
| `p1_solo` `p2_solo` `p3_solo` `p4_solo` `p5_solo` `p6_hymn_*` `p9_solo` | The bowed solo and the hymn | Ours: `bowed.py`, a waveguide bowed string after the STK Bowed model (Smith, Cook; McIntyre, Schumacher, Woodhouse), reimplemented here; body resonances in `instruments.body` |
| `p4_scrape1/2` | The strings scraped | Ours: the same string at full bow pressure |
| `p3_pluck` | The plucked gut string under P3 | Ours: `instruments.pluck_notes` (additive partials) |
| `p7_harmonic` | The high cold harmonic | Ours: `instruments.harmonic` |
| `p8_river_song` `p10_song_close` | The deep voice singing the motif under the water, no words | Ours: `instruments.sung_phrase` (formant synthesis) |
| `p10_song` | The Warden's call, close under the water | The placeholder voice take (AU-04), low-passed |
| `wind` `p7_whistle` | Wind over hills, the winter whistle | Ours: `sounds.wind` |
| `river` `p10_river` | The river | `bed_water_0.wav`: "Park ambiences" by thimras, OpenGameArt, CC0 (AU-02) |
| `p1_torches` `p3_hearth` `p9_fire` | Torches, the hearth, the camp fire | `bed_fire_0.wav`: "Fireplace Sound loop" by PagDev, OpenGameArt, CC0 (AU-02) |
| `p2_anvil` | The smiths' hammer on the chain | `Sfx.Anvil` ported: `anvil_0.wav` ("Blacksmith's Hammer" by vishwajai, OpenGameArt, CC0, AU-02), `impactMetal_heavy` (Kenney, CC0, AU-01), FM shimmer (ours), spark ticks (ours) |
| `p2_door` | The stone door closing; the low hit | Ours (grinding noise, `Sfx.Cine("hit")` ported), `chainDrag` (AU-06, CC0), `impactMining` and `impactWood_heavy` (Kenney, CC0, AU-01) |
| `p0_striker` | Flint, the wick catching, the small flame | Ours (sparks, the catch, the flame), `impactMetal_light` (Kenney, CC0) |
| `p1_march` | The Legion far off | `footstep_dirt`, `impactPlate_medium` (Kenney, CC0, AU-01), `chainLink` (AU-06, CC0) |
| `p1_below` | The sleeper's breath under the hill | Ours, after `Sfx.Cine("groan")` |
| `p3_motes` | The crystalline hiss rising with the motes | Ours: hiss and the ember pickup's FM chime (`Sfx.Xp`) |
| `p3_town` | Door, coins, cart | `doorOpen`, `doorClose`, `handleCoins`, `creak`, `footstep_dirt` (Kenney, CC0, AU-01); the wheel rumble is ours |
| `p4_frost` `p4_rasp*` `p4_breath*` `p5_breath` | Frost splitting, the risen's rasp, the Watchman's breath | Ours: `Sfx.Cine("frost_crack" / "rasp" / "breath_out")` ported |
| `p4_spear` `p4_fall` | The spear, the body falling | `impactPunch_heavy`, `impactSoft_heavy`, `impactSoft_medium`, `creak`, `cloth` (Kenney, CC0, AU-01); the push of air is ours |
| `p4_spill` | The light spilling as stones | Ours: the ember pickup (`Sfx.Xp`) scattered; `impactGlass_light` (Kenney, CC0) |
| `p5_drain` `p5_bird*` `p5_lamp` `p6_lamps` | The light draining, birds, lamp flames | Ours |
| `p6_oil` | Oil glugging into a lamp | Ours: `Sfx.Pour` ported and stretched |
| `p7_blue` `p8_blue` `p10_lamp` | The blue lamps' cold hiss | Ours |
| `p7_ring*` `p8_drip*` `p8_weed*` | Rings, drips from the drowned, weed | Ours: `Sfx.Cine("drip" / "cloth_water")` ported |
| `p9_owl` | The night bird | Ours: `Sfx.Cine("owl")` ported |
| `p9_steps` `p10_kneel` | The traveler's steps, kneeling on stone | `footstep_grass`, `footstep_concrete`, `cloth`, `impactSoft_medium`, `handleSmallLeather` (Kenney, CC0, AU-01) |
| `p10_flask` | The flask filling: glugs and bubbles | Ours |
| `p10_splash` | The pull and splash | `impactSoft_heavy`, `impactPunch_heavy` (Kenney, CC0); spray, `Sfx.Cine("kneel_water")` and `("water_close")` ported (ours) |
| `p10_under` `p10_blub` `p10_thrash` | The muffled roar, bubbles bursting, cloth and thrashing | Ours; `cloth`, `impactSoft_medium` (Kenney, CC0) |
| `p10_heart` | The slowing heartbeat | Ours: `Sfx.Heartbeat` ported, with a dull thump under it |

Credits: the CC0 recordings need no credit, and `public/assets/CREDITS.md` already names them. Nothing new to add to `docs/legal/ASSET_PROVENANCE.md` beyond a line saying SB00's bed is derived from AU-01, AU-02, AU-04, AU-05 and AU-06. That line is the lead's call.
