import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Content/Boons.cs', [
# Pyre Burst: a quarter of them, for a quarter of their health.
("""            Text = "Burning creatures have a 30% chance to explode when they die.", Requires = new(Status: Burn),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.4, 0.35, Basis.MaxHp, School.Fire, P(Burn, 0.7, 0.25, 3))], new() { TargetStatus = Burn }, chance: 0.3)] },""",
"""            Text = "Burning creatures have a 25% chance to explode when they die.", Requires = new(Status: Burn),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.4, 0.22, Basis.MaxHp, School.Fire, P(Burn, 0.7, 0.25, 3))], new() { TargetStatus = Burn }, chance: 0.25, icd: 0.05)] },"""),
("""            Triggers = [T(TriggerEvent.Explode, [new Effect.Missiles(2, 18, Basis.Flat, School.Fire, Seek.Strongest, 9, "ember_seeker")], icd: 0.12)] },""",
"""            Triggers = [T(TriggerEvent.Explode, [new Effect.Missiles(2, 14, Basis.Flat, School.Fire, Seek.Strongest, 9, "ember_seeker")], icd: 0.2)] },"""),
("""            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.6, 0.45, Basis.MaxHp, School.Frost, P(Chill, 1, 2, 2.5))], new() { TargetStatus = Frozen })] },""",
"""            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.6, 0.3, Basis.MaxHp, School.Frost, P(Chill, 1, 2, 2.5))], new() { TargetStatus = Frozen }, icd: 0.05)] },"""),
("""            Text = "Every 12th kill calls lightning down on the thickest knot of creatures near you.", Requires = new(Tag: Tag.Storm),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Strike(3, 1.6, 40, Basis.Flat, School.Storm, 6)], chance: 1.0 / 12)] },""",
"""            Text = "Every 16th kill calls lightning down on the thickest knot of creatures near you.", Requires = new(Tag: Tag.Storm),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Strike(3, 1.6, 30, Basis.Flat, School.Storm, 6)], chance: 1.0 / 16)] },"""),
("""            Text = "A marked creature that dies bursts for a fifth of its health, and the toughest thing near it is marked.", Requires = new(Status: Mark),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.4, 0.2, Basis.MaxHp, School.Arcane), new Effect.Apply(P(Mark, 1, 1, 5), OnHit: false, Radius: 7, Count: 1)],
                new() { TargetStatus = Mark }, icd: 0.08)] },""",
"""            Text = "A marked creature that dies bursts for a tenth of its health, and the toughest thing near it is marked.", Requires = new(Status: Mark),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.2, 0.1, Basis.MaxHp, School.Arcane), new Effect.Apply(P(Mark, 1, 1, 5), OnHit: false, Radius: 6, Count: 1)],
                new() { TargetStatus = Mark }, icd: 0.2)] },"""),
])

edit('logic/Content/Discoveries.cs', [
("""            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Explode(1.4, 0.5, Basis.Hit, School.Fire)], new() { Weapon = a.Id }, icd: 0.05), "disc:shadowflame") },""",
"""            Apply = (a, _, battle) => battle.AddTrigger(T(TriggerEvent.Hit, [new Effect.Explode(1.4, 0.3, Basis.Hit, School.Fire)], new() { Weapon = a.Id }, icd: 0.15), "disc:shadowflame") },"""),
])
print('ok')
