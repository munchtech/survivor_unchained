W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\godot'


def patch(rel, pairs):
    p = W + '\\' + rel
    t = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert t.count(a) == 1, (rel, a[:60])
        t = t.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='\n').write(t)


patch(r'src\Game\GameCinema.cs', [('''                case "gaze":''', '''                case "head":
                {
                    // A look with the head and neck, the body left as it is ("look" turns the body):
                    // "where" is the point looked at; "amount" 0 (or no "where") lets the head go.
                    if (!people.TryGetValue(c.Actor, out var v)) break;
                    var skel = v.Person.Skeleton;
                    var turn = skel.GetNodeOrNull<HeadTurn>("HeadTurn");
                    if (turn == null) skel.AddChild(turn = new HeadTurn());
                    bool letGo = !c.Has("where") || c.Num("amount", 1) <= 0;
                    if (!letGo) turn.Target = V(places.Resolve(c.Get("where")));
                    turn.Want = letGo ? 0 : (float)c.Num("amount", 1);
                    turn.Rate = (float)(1 / Math.Max(0.05, over));
                    break;
                }
                case "gaze":''')])
print('ok')
