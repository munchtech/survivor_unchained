from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\godot\src\Actors\Arms.cs")
t = p.read_text(encoding="utf-8")
old_rec = '''    public sealed record Spec(string File, float Length, float Grip, bool Flip = false, float Roll = 0, string? Node = null, bool Pistol = false, Func<Node3D>? Build = null);'''
new_rec = '''    /// Lean: degrees its shaft leans in a diagonal grip, from square to the
    /// fingers toward them (a sword's grip runs from the root of the
    /// forefinger to the heel of the hand), for those whose own clips are
    /// keyed to it (tools/anim/keyed.py GRIP), not the library's.
    public sealed record Spec(string File, float Length, float Grip, bool Flip = false, float Roll = 0, string? Node = null, bool Pistol = false, Func<Node3D>? Build = null, float Lean = 0);'''
assert t.count(old_rec) == 1
t = t.replace(old_rec, new_rec)
rows = {
    '["chevalier_sword"] = new("chevalier_sword", 1.0f, 0.1f),': '["chevalier_sword"] = new("chevalier_sword", 1.0f, 0.1f, Lean: 35),',
    '["viking_sword"] = new("viking_sword", 0.92f, 0.13f),': '["viking_sword"] = new("viking_sword", 0.92f, 0.13f, Lean: 35),',
    '["longsword"] = new("longsword", 1.05f, 0.22f, Flip: true),': '["longsword"] = new("longsword", 1.05f, 0.22f, Flip: true, Lean: 35),',
    '["mace"] = new("mace", 0.75f, 0.12f),': '["mace"] = new("mace", 0.75f, 0.12f, Lean: 30),',
    '["viking_axe"] = new("viking_axe", 0.8f, 0.15f, Roll: Mathf.Pi),': '["viking_axe"] = new("viking_axe", 0.8f, 0.15f, Roll: Mathf.Pi, Lean: 30),',
    '["snake_axe"] = new("snake_axe", 1.3f, 0.22f),': '["snake_axe"] = new("snake_axe", 1.3f, 0.22f, Lean: 30),',
    '["wand"] = new("", 0.38f, 0.12f, Build: Made.Wand),': '["wand"] = new("", 0.38f, 0.12f, Build: Made.Wand, Lean: 30),',
    '["daggers"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004"),': '["daggers"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004", Lean: 30),',
    '["dagger_b"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004_01"),': '["dagger_b"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004_01", Lean: 30),',
}
for a, b in rows.items():
    assert t.count(a) == 1, a
    t = t.replace(a, b)
old_hold = '''        mount.Basis = new Basis(x, y, x.Cross(y));
        mount.Position = forearm ? new Vector3(0, 0.14f, 0) : new Vector3(-0.025f, 0.075f, 0);'''
new_hold = '''        mount.Basis = new Basis(x, y, x.Cross(y));
        // Her and the hero hold it in the diagonal grip their clips are keyed
        // to: the shaft turned about the hand's across axis toward the fingers.
        if (!forearm && person.Own != null && All[id].Lean != 0)
            mount.Basis = new Basis(Vector3.Right, Mathf.DegToRad(-All[id].Lean)) * mount.Basis;
        mount.Position = forearm ? new Vector3(0, 0.14f, 0) : new Vector3(-0.025f, 0.075f, 0);'''
assert t.count(old_hold) == 1
t = t.replace(old_hold, new_hold)
p.write_text(t, encoding="utf-8")
print("ok")
