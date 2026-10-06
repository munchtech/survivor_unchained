G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot"


def edit(path, pairs):
    p = G + "\\" + path
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8").write(s)


edit(r"src\Fx\BattleFx.Loot.cs", [
    ('''///   Uncommon  a low green glow, under a metre;
///   Rare      a blue column, two and a half metres;''',
     '''///   Common and Uncommon: no light, their names only (a horde's worth of them must not glow);
///   Rare      a blue column, two and a half metres;'''),
    ('''            case LootTier.Uncommon:
                Column(p.X, gy, p.Z, 0.8f, 0.14f, Palette.Rarity[1], 0.45f);
                break;
''', ''),
])

edit(r"src\Fx\BattleFx.cs", [
    ('''        embers.Begin(); coins.Begin(); flasks.Begin(); lodestones.Begin(); sacks.Begin(); chests.Begin(); lootBeams.Begin();''',
     '''        embers.Begin(); coins.Begin(); flasks.Begin(); lodestones.Begin(); sacks.Begin(); chests.Begin(); BeginLoot();'''),
    ('''        embers.End(); coins.End(); flasks.End(); lodestones.End(); sacks.End(); chests.End(); lootBeams.End();''',
     '''        embers.End(); coins.End(); flasks.End(); lodestones.End(); sacks.End(); chests.End(); EndLoot();'''),
    ('''                        lootBeams.Add(new Transform3D(Godot.Basis.Identity.Scaled(new Vector3(1.3f, 4.5f, 1.3f)), V(p.X, gy + 2.25, p.Z)), new Color("#ff3a2a"));''',
     '''                        Column(p.X, gy, p.Z, 4.5f, 0.2f, StoriedRed, 0.7f);'''),
    ('''                    if (hidden) break;
                    float h = p.Kind is PickupKind.Material ? 1.4f : 3.2f, w = 1;
                    // Loot rolled whole carries its tier (docs/design/LOOT_DESIGN.md §8.1): the beam's
                    // height says how rare, its colour the band. Placeholder heights for the VFX lead.
                    if (p.Loot >= 0)
                    {
                        (h, w, col) = (LootTier)p.Loot switch
                        {
                            LootTier.Common => (0f, 1f, col),
                            LootTier.Uncommon => (0.8f, 1f, col),
                            LootTier.Rare => (2.5f, 1f, col),
                            LootTier.Epic => (5f * (1 + 0.08f * Mathf.Sin((float)now * 2.5f)), 1.2f, col),
                            LootTier.Set => (6f, 1.4f, SetColour),
                            LootTier.Legendary => (40f, 2.6f, Palette.Rarity[4]),
                            LootTier.Storied => (40f, 2.6f, Palette.Rarity[5]),
                            LootTier.Chart => (2f, 1f, new Color("#e8d8b0")),
                            LootTier.Quest => (1.5f, 1f, new Color("#ffd46a")),
                            LootTier.Book => (1.5f, 1f, col),
                            _ => (0f, 1f, col),
                        };
                    }
                    if (h <= 0) break;
                    lootBeams.Add(new Transform3D(Godot.Basis.Identity.Scaled(new Vector3(w, h, w)), V(p.X, gy + h / 2, p.Z)), col);
                    // A set's beam is two strands that twist about each other.
                    if (p.Loot == (int)LootTier.Set)
                    {
                        float a = (float)now * 1.6f;
                        lootBeams.Add(new Transform3D(Godot.Basis.Identity.Scaled(new Vector3(0.7f, h * 0.9f, 0.7f)), V(p.X + Mathf.Cos(a) * 0.18f, gy + h * 0.45f, p.Z + Mathf.Sin(a) * 0.18f)), col);
                    }
                    break;''',
     '''                    if (hidden) break;
                    // Loot rolled whole carries its tier (docs/design/LOOT_DESIGN.md §8.1): the light's
                    // height says how rare, its colour the band (BattleFx.Loot).
                    LootLight(p, gy, now, col);
                    break;'''),
])
print("ok")
