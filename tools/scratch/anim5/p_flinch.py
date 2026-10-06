from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\story.py")
t = p.read_text(encoding="utf-8")
a = '''ALL = (("lie_side_wake", lie_side_wake), ("sit_back_heels", sit_back_heels), ("reach_coals", reach_coals),
       ("letter", letter), ("kneel_to_stand_snap", kneel_to_stand_snap), ("take_from_log", take_from_log),
       ("cup_hands", cup_hands), ("nod", nod), ("exhale", exhale), ("shiver", shiver))
# Judged on sheets (still to be judged in the cinematic itself). Anything
# else here is work in progress, built only when named.
JUDGED = {"lie_side_wake", "sit_back_heels", "reach_coals", "nod", "exhale", "shiver"}'''
b = '''def flinch(rig):
    """A blow taken on the move: the chest caves and twists away from it,
    the shoulders jerk up round the neck and the head snaps back, in two
    frames, and she shakes it off over a third of a second. Laid over a run
    or a cut (the legs keep going, the arms keep what they hold): only the
    back, the shoulders and the head move, so nothing is added to the legs
    or the arms. Big enough to read at 31 m."""
    keys = [
        (0, _still(), "ease"),
        (2, _still(spine=(16, -16, -8), neck=(6, -10, 0), head=(12, -20, -10), clav_l=(14, -8), clav_r=(14, -8)), "ease"),
        (5, _still(spine=(9, -8, -4), neck=(3, -5, 0), head=(7, -10, -5), clav_l=(7, -4), clav_r=(7, -4)), "auto"),
        (14, _still(), "ease"),
    ]
    return build("flinch", rig, keys, meta={"layer": "gesture", "note": "struck on the move: the back caves, the head snaps, 0.47 s"})


ALL = (("lie_side_wake", lie_side_wake), ("sit_back_heels", sit_back_heels), ("reach_coals", reach_coals),
       ("letter", letter), ("kneel_to_stand_snap", kneel_to_stand_snap), ("take_from_log", take_from_log),
       ("cup_hands", cup_hands), ("nod", nod), ("exhale", exhale), ("shiver", shiver), ("flinch", flinch))
# Judged on sheets (still to be judged in the cinematic itself). Anything
# else here is work in progress, built only when named.
JUDGED = {"lie_side_wake", "sit_back_heels", "reach_coals", "nod", "exhale", "shiver", "flinch"}'''
assert t.count(a) == 1
t = t.replace(a, b)
p.write_text(t, encoding="utf-8")

pv = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\godot\src\Actors\PlayerView.cs")
t = pv.read_text(encoding="utf-8")
a = '''        if (p.HurtT > 0.25 && hurtSeen <= 0)
        {
            hurtSeen = 0.4;
            if (!Busy) Upper("Hit_A", mine && own.Has("hit") ? 1.2 : 1.6);
        }'''
b = '''        if (p.HurtT > 0.25 && hurtSeen <= 0)
        {
            hurtSeen = 0.4;
            // On the move or mid-blow, her own flinch is laid over what she is
            // doing (the legs keep running, the arms keep their hold); standing,
            // the whole of her upper body takes the hit.
            bool jolt = mine && own.Has("flinch") && person.Gestures != null && (sp > 1.5f || Busy);
            if (jolt) person.Gestures!.Play(person.Anim.GetAnimation(own.Prefix + "flinch"));
            else if (!Busy) Upper("Hit_A", mine && own.Has("hit") ? 1.2 : 1.6);
        }'''
assert t.count(a) == 1
t = t.replace(a, b)
pv.write_text(t, encoding="utf-8")
print("ok")
