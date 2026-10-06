p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\tools\anim\clips\story.py"
s = open(p, encoding="utf-8").read()
s = s.replace('{"hand_r": {**keyed, "pos": tuple(at),', '{"hand_r": {**_aimed_only(keyed), "pos": tuple(at),')
s = s.replace('out["hand_r"] = {**keyed, "pos": tuple(at),', 'out["hand_r"] = {**_aimed_only(keyed), "pos": tuple(at),')
anchor = "PROP_TOWARD = (-0.55, 0.0, 0.83)"
helper = '''def _aimed_only(spec):
    """A keyed hand without its place (a contact puts it), keeping its aim."""
    return {k: v for k, v in spec.items() if k not in ("arc", "mix", "pos")}


'''
assert anchor in s
s = s.replace(anchor, helper + anchor, 1)
open(p, "w", encoding="utf-8").write(s)
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\tools\anim\held.py"
s = open(p, encoding="utf-8").read()
old = '''    from keyed import Track
    track = Track(keys)'''
new = '''    from keyed import Track, _one_frame
    track = Track(_one_frame(rig, keys, base))'''
assert old in s
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("ok")
