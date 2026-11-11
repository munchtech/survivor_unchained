"""Write godot/data/content/sounds.json's events from the table below, one line per event (the bank as data;
the lead's working copy: edit a line, run this, or edit sounds.json by hand: this script only rewrites "events"
for the ids it names and keeps the rest).

    python tools/audio/events.py
"""
import json, re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, "godot", "data", "content", "sounds.json")

def L(take, gain, pitch=None, **kw):
    d = {"take": take, "gain": gain}
    if pitch: d["pitch"] = pitch
    d.update(kw)
    return d

def E(*layers, bus="sfx", near=None, gate=None, synth=None, duck=None, lead=False):
    d = {"bus": bus}
    if lead: d["lead"] = True
    if near is not None: d["near"] = near
    if gate: d["gate"] = gate
    if synth: d["synth"] = synth
    if duck: d["duck"] = duck
    d["layers"] = list(layers)
    return d

EV = {
    # her blade, by what it strikes (the most heard sounds of the game)
    "hit.flesh":        E(L("hit_flesh", 0.42, [0.9, 1.1], vary=1.5)),
    "hit.flesh.crit":   E(L("hit_flesh_crit", 0.55, [0.95, 1.05]), L("gore_thump", 0.18, [0.9, 1.1])),
    "hit.bone":         E(L("hit_bone", 0.40, [0.9, 1.12], vary=1.5)),
    "hit.bone.crit":    E(L("hit_bone_crit", 0.55, [0.95, 1.05]), L("gore_thump", 0.15, [0.9, 1.1])),
    "hit.hide":         E(L("hit_hide", 0.45, [0.9, 1.08], vary=1.0)),
    "hit.holy":         E(L("holy_smite", 0.20, [0.95, 1.12], vary=1.0)),
    "swing":            E(L("swing_blade", 0.26, [0.9, 1.12], vary=1.5)),
    "art.slash_heavy.swing": E(L("swing_heavy", 0.40, [0.92, 1.05])),
    "art.slash_heavy.hit":   E(L("gore_thump", 0.28, [0.85, 1.0]), gate=[1, 150]),
    "art.slash_quake.land":  E(L("quake_crack", 0.50, [0.95, 1.05])),
    "art.slash_quake.hit":   E(L("gore_thump", 0.20, [0.9, 1.05]), gate=[1, 200]),
    "art.slash_quake_heave.burst": E(L("quake_crack", 0.45, [0.75, 0.85]), L("gore_thump", 0.30)),
    "art.watch_bell.nova":   E(L("watch_bell", 0.50, [0.97, 1.03], stereo=True), near=1),
    "art.watch_bell.hit":    E(L("holy_smite", 0.14, [1.1, 1.3]), gate=[2, 120]),
    "art.rebuke.hit":        E(L("holy_smite", 0.30, [0.95, 1.05]), gate=[2, 150]),
    "nova.holy":             E(L("holy_smite", 0.35, [0.8, 0.9]), near=1),
    # what falls
    "kill.flesh":       E(L("kill_flesh", 0.40, [0.92, 1.06])),
    "kill.bone":        E(L("kill_bone", 0.38, [0.9, 1.1], vary=1.5)),
    "kill.hide":        E(L("kill_hide", 0.42, [0.92, 1.05])),
    # the corpse pop (the owner liked it): the burst with a thump under it for weight
    "kill.flesh.burst": E(L("gore_burst", 0.50, [0.9, 1.08]), L("gore_thump", 0.35, [0.9, 1.1])),
    "kill.bone.burst":  E(L("bone_burst", 0.48, [0.9, 1.1]), L("gore_thump", 0.30, [0.9, 1.1])),
    "kill.hide.burst":  E(L("gore_burst", 0.50, [0.85, 0.95]), L("gore_thump", 0.40, [0.85, 0.95])),
    "kill.elite":       E(L("kill_elite", 0.50, [0.95, 1.02])),
    # her
    "dash":             E(L("dash", 0.40, [0.95, 1.05]), near=1),
    "hurt":             E(L("hurt_her", 0.50, [0.95, 1.05]), near=1),
    "block":            E(L("block_shield", 0.38, [0.92, 1.08])),
    "explosion":        E(L("explosion_small", 0.40, [0.9, 1.05])),
    "spawn.rise":       E(L("spawn_rise", 0.22, [0.9, 1.1]), gate=[2, 300]),
    # the ember's pickup: the musical ladder stays, a glassy spark laid under it
    "pickup.ember":     E(L("ember_pickup", 0.10), near=1, synth="under"),
    # footsteps: the ground's recording stays, her armor laid on each step
    "step.grass":       E(L("armor_step", 0.07, [0.9, 1.1], vary=2), near=1, synth="under"),
    "step.dirt":        E(L("armor_step", 0.07, [0.9, 1.1], vary=2), near=1, synth="under"),
    "step.concrete":    E(L("armor_step", 0.07, [0.9, 1.1], vary=2), near=1, synth="under"),
    "step.wood":        E(L("armor_step", 0.07, [0.9, 1.1], vary=2), near=1, synth="under"),
    # the Long Cut
    "flare.catch":      E(L("flare_catch", 0.60, stereo=True), bus="flare", near=1),
    "flare.inhale":     E(L("flare_inhale", 0.55, stereo=True), bus="flare", near=1),
    # H7: the ultimate's two beats, per Flare: the stop's intake (its calling's, cut to the stop) and the blow with its tail
    "flare.the_long_cut.inhale": E(L("flare_intake_warden", 1.6, stereo=True), bus="flare", near=1),
    "flare.the_long_cut.boom": E(L("flare_boom_the_long_cut", 1.7, stereo=True), bus="flare", near=1, duck={"sfx": 0.15, "seconds": 1.4}),
    "flare.bell_of_the_morning.inhale": E(L("flare_intake_warden", 1.6, stereo=True), bus="flare", near=1),
    "flare.bell_of_the_morning.boom": E(L("flare_boom_bell_of_the_morning", 3.9, stereo=True), bus="flare", near=1, duck={"sfx": 0.15, "seconds": 1.4}),
    "flare.burns_twice.inhale": E(L("flare_intake_arcanist", 1.10, stereo=True), bus="flare", near=1),
    "flare.burns_twice.boom": E(L("flare_boom_burns_twice", 1.23, stereo=True), bus="flare", near=1, duck={"sfx": 0.15, "seconds": 1.4}),
    "flare.the_roads_toll.inhale": E(L("flare_intake_stalker", 1.62, stereo=True), bus="flare", near=1),
    "flare.the_roads_toll.boom": E(L("flare_boom_the_roads_toll", 2.0, stereo=True), bus="flare", near=1, duck={"sfx": 0.15, "seconds": 1.4}),
    "flare.the_branding.inhale": E(L("flare_intake_arcanist", 1.10, stereo=True), bus="flare", near=1),
    "flare.the_branding.boom": E(L("flare_boom_the_branding", 1.9, stereo=True), bus="flare", near=1, duck={"sfx": 0.15, "seconds": 1.4}),
    "flare.one_arrow.inhale": E(L("flare_intake_stalker", 1.62, stereo=True), bus="flare", near=1),
    "flare.one_arrow.boom": E(L("flare_boom_one_arrow", 4.0, stereo=True), bus="flare", near=1, duck={"sfx": 0.15, "seconds": 1.4}),
    "flare.drag_them_under.inhale": E(L("flare_intake_reaver", 2.5, stereo=True), bus="flare", near=1),
    "flare.drag_them_under.boom": E(L("flare_boom_drag_them_under", 2.0, stereo=True), bus="flare", near=1, duck={"sfx": 0.15, "seconds": 1.4}),
    "flare.the_butchers_bill.inhale": E(L("flare_intake_reaver", 2.5, stereo=True), bus="flare", near=1),
    "flare.the_butchers_bill.boom": E(L("flare_boom_the_butchers_bill", 1.8, stereo=True), bus="flare", near=1, duck={"sfx": 0.15, "seconds": 1.4}),
    "flare.bell_of_the_morning.toll": E(L("bell_toll", 0.55, stereo=True), bus="flare", near=1),
    "flare.mark": E(L("flare_mark_tick", 0.35, stereo=True), bus="flare", near=1, gate=[1, 120]),
    # batch 2: the draft, level-up, lamps, UI, the boss, the way out, results, H1's telegraphs, the Ford-Warden
    "levelup":           E(L("levelup_swell", 0.55, stereo=True), bus="ui", near=1),
    "levelup.milestone": E(L("levelup_big", 0.60, stereo=True), bus="ui", near=1),
    "ui.page":           E(L("ui_card", 0.30, [0.95, 1.05]), bus="ui", near=1),
    "ui.pick":           E(L("ui_pick", 0.35, [0.97, 1.03]), bus="ui", near=1),
    "ui.open":           E(L("ui_open", 0.30, [0.97, 1.03]), bus="ui", near=1),
    "ui.close":          E(L("ui_close", 0.30), bus="ui", near=1),
    "ui.deny":           E(L("ui_deny", 0.35), bus="ui", near=1),
    "lamps.light":       E(L("lamp_lit", 0.40, [0.97, 1.03]), bus="ui", near=1),
    "lamps.light_notable": E(L("lamp_lit_big", 0.50, [0.97, 1.03]), L("lamp_lit", 0.20), bus="ui", near=1),
    "lamps.put_out":     E(L("lamp_out", 0.35), bus="ui", near=1),
    "pickup.gold":       E(L("gold_pickup", 0.30, [0.95, 1.08]), near=1),
    "heal":              E(L("heal_glow", 0.35, stereo=True), near=1),
    "stinger.boss":      E(L("boss_arrive", 0.75, stereo=True), bus="music", near=1),
    "kill.boss":         E(L("boss_down", 0.75, stereo=True), near=1, duck={"sfx": 0.5, "seconds": 1.5}),
    "ui.way_out":        E(L("way_out", 0.65, stereo=True), bus="ui", near=1),
    "ui.skill_ready":    E(L("skill_ready", 0.18), bus="ui", near=1, gate=[1, 400]),
    "cine.to_play":      E(L("cine_whoosh", 0.30, stereo=True), bus="ui", near=1),
    "result.won":        E(L("result_won", 0.70, stereo=True), bus="music", near=1),
    "result.fell":       E(L("result_fell", 0.70, stereo=True), bus="music", near=1),
    "telegraph.ring.windup":    E(L("tg_ring_windup", 0.50), near=0.7),
    "telegraph.ring.land":      E(L("tg_ring_land", 0.55), near=0.7),
    "telegraph.charge.windup":  E(L("tg_charge_windup", 0.55), near=0.7),
    "telegraph.charge.land":    E(L("tg_charge_land", 0.55), near=0.7),
    "telegraph.pull.windup":    E(L("tg_pull_windup", 0.50), near=0.7),
    "telegraph.pull.land":      E(L("tg_pull_land", 0.55), near=0.7),
    "telegraph.closing.windup": E(L("tg_closing_windup", 0.55, stereo=True), near=1),
    "telegraph.closing.land":   E(L("tg_closing_land", 0.60, stereo=True), near=1),
    "telegraph.ring.windup.boss":   E(L("tg_ring_windup", 0.60, [0.8, 0.85]), near=0.8),
    "telegraph.ring.land.boss":     E(L("tg_ring_land", 0.65, [0.8, 0.85]), L("gore_thump", 0.4, [0.7, 0.8]), near=0.8),
    "telegraph.charge.windup.boss": E(L("tg_charge_windup", 0.65, [0.8, 0.85]), near=0.8),
    "telegraph.charge.land.boss":   E(L("tg_charge_land", 0.65, [0.8, 0.85]), L("gore_thump", 0.4, [0.7, 0.8]), near=0.8),
    "telegraph.pull.windup.boss":   E(L("tg_pull_windup", 0.60, [0.8, 0.85]), near=0.8),
    "telegraph.pull.land.boss":     E(L("tg_pull_land", 0.65, [0.8, 0.85]), L("gore_thump", 0.4, [0.7, 0.8]), near=0.8),
    # the drop ladder (Sfx.Drop / Sfx.Toll): tiers 2-4 one instrument each, the toll its own, the storied fire laid over it.
    # Levels: rare about -20 LUFS in the hits' context (hits play near -25), epic/set about -18, the toll the loudest bar a boss's fall.
    "drop.2":           E(L("drop_rare", 0.43, [0.98, 1.03]), gate=[1, 500]),
    "drop.3":           E(L("drop_epic", 0.31, [0.98, 1.02], stereo=True), gate=[1, 500]),
    "drop.4":           E(L("drop_set", 0.62, [0.98, 1.02], stereo=True), L("drop_set", 0.5, [1.49, 1.51], stereo=True, delay=0.16), gate=[1, 500]),  # the pair struck one after the other, up a fifth: its rhythm tells it from the rare's one chime
    "toll":             E(L("drop_legendary", 0.90, stereo=True), bus="ui", near=1, lead=True),
    "toll.storied":     E(L("drop_legendary", 0.90, stereo=True), L("drop_storied_fire", 0.50, stereo=True, delay=0.3), bus="ui", near=1, lead=True),
    # zone beds (Ambience.SetZone: bed.<zone>.<day|night>, then bed.<zone>; the first layer's take loops, at its gain)
    "bed.verge.day":       E(L("bed_verge_day", 0.45, stereo=True), bus="ambience"),
    "bed.lowford":         E(L("bed_lowford_night", 0.45, stereo=True), bus="ambience"),
    "bed.waystation":      E(L("bed_waystation", 0.45, stereo=True), bus="ambience"),
    "bed.arena":           E(L("bed_deepshaw_night", 0.45, stereo=True), bus="ambience"),
    "bed.title":           E(L("bed_title", 0.50, stereo=True), bus="ambience"),
    "ford.channel":        E(L("ford_channel", 0.55), near=0.8),
    "ford.channel_broken": E(L("ford_broken", 0.60), near=1),
    "ford.lamp_out":       E(L("ford_lamp_out", 0.60), near=0.8),
    "ford.lamp_shatter":   E(L("ford_lamp_out", 0.60, [0.9, 0.95]), L("block_shield", 0.25, [0.6, 0.7]), near=0.8),
}

def main():
    raw = open(PATH, encoding="utf-8").read()
    d = json.loads(raw)
    ev = d.setdefault("events", {})
    for k, v in EV.items(): ev[k] = v
    # One line per event: the bank stays readable as data.
    head = {k: v for k, v in d.items() if k != "events"}
    out = json.dumps(head, indent=2)[:-2] + ',\n  "events": {\n'
    out += ",\n".join(f'    {json.dumps(k)}: {json.dumps(v)}' for k, v in sorted(ev.items()))
    out += "\n  }\n}\n"
    json.loads(out)
    open(PATH, "w", encoding="utf-8", newline="\n").write(out)
    print(f"{len(ev)} events in {PATH}")

if __name__ == "__main__":
    main()
