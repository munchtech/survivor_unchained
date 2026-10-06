from pathlib import Path
p = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\godot\src\Actors\PlayerView.cs')
s = p.read_text(encoding='utf-8')
old = """        // A charge behind the shield; a haul on the chain, blade first.
        if (b.Art.Rush != rushSeen)
        {
            rushSeen = b.Art.Rush;
            if (rushSeen is { } rk)
            {
                Rotation = new Vector3(0, Mathf.Atan2((float)b.Art.RushDX, (float)b.Art.RushDZ), 0);
                var rush = rk == Content.AbilityKind.BullRush ? "Shield_Dash" : "Sword_Dash";
                bool own = People.Clip(person, rush).StartsWith(HerClips.Prefix);
                Full(rush, own ? 1.0 : rk == Content.AbilityKind.BullRush ? 1.5 : 2.2);
            }
        }"""
new = """        // A charge behind the shield; a haul on the chain, blade first.
        if (b.Art.Rush != rushSeen)
        {
            var was = rushSeen;
            rushSeen = b.Art.Rush;
            if (rushSeen is { } rk)
            {
                Rotation = new Vector3(0, Mathf.Atan2((float)b.Art.RushDX, (float)b.Art.RushDZ), 0);
                aim = 0;
                var rush = rk == Content.AbilityKind.BullRush ? "Shield_Dash" : "Sword_Dash";
                bool own = People.Clip(person, rush).StartsWith(HerClips.Prefix);
                Full(rush, own ? 1.0 : rk == Content.AbilityKind.BullRush ? 1.5 : 2.2);
                // Her charge's plant and shove show, then give way if she runs on.
                if (rk == Content.AbilityKind.BullRush) artTail = time + b.Art.RushT + 0.25;
            }
            // Hauled all the way in: the blow she lands with (hers held in
            // the air until now, for however long the haul took).
            else if (was == Content.AbilityKind.Grapple && FullHer("chain_strike", 1, false))
                artTail = time + 0.3;
        }"""
assert old in s
s = s.replace(old, new)
old2 = """            case "grapple" or "grapple_miss":
                Upper("OverhandThrow", 2.2);
                break;"""
new2 = """            case "grapple" or "grapple_miss":
                // (Hers: the chain loosed like a thrown knife; a haul that
                // follows plays over it.)
                if (!UpperHer("throw", 1.6)) Upper("OverhandThrow", 2.2);
                break;"""
assert old2 in s
s = s.replace(old2, new2)
p.write_text(s, encoding='utf-8')
print('ok')
