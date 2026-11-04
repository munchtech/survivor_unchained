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

def E(*layers, bus="sfx", near=None, gate=None, synth=None, duck=None):
    d = {"bus": bus}
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
    "flare.the_long_cut.boom": E(L("longcut_boom", 0.85, stereo=True), bus="flare", near=1, duck={"sfx": 0.4, "seconds": 1.2}),
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
