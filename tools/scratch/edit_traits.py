import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    for old, new in pairs:
        old = old.replace('\n', nl); new = new.replace('\n', nl)
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit('data/content/archetypes.json', [
("""   "text": "+20% fire damage; what burns burns 30% longer.",
   "mods": [
    {
     "stat": "damage.fire",
     "kind": "inc",
     "value": 0.2,
     "source": "trait"
    }
   ]""", """   "text": "+20% fire damage; what burns burns 30% longer.",
   "mods": [
    {
     "stat": "damage.fire",
     "kind": "inc",
     "value": 0.2,
     "source": "trait"
    },
    {
     "stat": "statusDuration.burn",
     "kind": "inc",
     "value": 0.3,
     "source": "trait"
    }
   ]"""),
("""    {
     "stat": "statusChance",
     "kind": "inc",
     "value": 0.1,
     "source": "trait"
    }""", """    {
     "stat": "statusPower.chill",
     "kind": "inc",
     "value": 0.25,
     "source": "trait"
    }"""),
("""   "text": "Bleeds hurt 30% more. Kills heal 1.",
   "mods": [
    {
     "stat": "statusDamage",""", """   "text": "Bleeds hurt 30% more. Kills heal 1.",
   "mods": [
    {
     "stat": "statusDamage.bleed","""),
])

edit('logic/Content/Boons.cs', [
("""            Mods = r => [Inc(Stat.DamageOf(Tag.Dot), 0.12 * r, "boon:venom"), Inc(Stat.StatusChance, 0.1 * r, "boon:venom")] },""",
"""            Mods = r => [Inc(Stat.DamageOf(Tag.Dot), 0.12 * r, "boon:venom"), Flat(Stat.StatusChance, 0.1 * r, "boon:venom")] },"""),
("""            Text = "Damage over time (burning, bleeding, poison, searing) is 12% stronger, and poisons take hold 10% more often.",""",
"""            Text = "Damage over time (burning, bleeding, poison, searing) is 12% stronger, and every status takes hold 10% more often.","""),
])
print("ok")
