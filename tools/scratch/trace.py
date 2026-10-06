import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot\balance')
p = 'Harness/ArenaSim.cs'
s = open(p, encoding='utf-8').read()
old = """                    case Ev.Kill k2: firstHit.Remove(k2.Enemy); break;
                }"""
new = """                    case Ev.Kill k2: firstHit.Remove(k2.Enemy); break;
                    // ARENA_TRACE=KEY@MINUTE: the blows that land on the survivor, from that minute (why a run fell).
                    case Ev.PlayerHit ph when trace != null && t >= traceFrom:
                        Console.Error.WriteLine($"{t / 60:0.000} {ph.Source,-22} {ph.Amount,6:0} {(ph.Dodged ? "dodged" : ph.Blocked ? "blocked" : "")} hp {p.Hp:0}/{b.MaxHp:0} shield {p.Shield:0}");
                        break;
                }"""
assert s.count(old) == 1
s = s.replace(old, new)
old2 = """        double t = 0;
        while (t < spec.Cap * 60 && p.Alive && host.Result == null)"""
new2 = """        double t = 0;
        var trace = Environment.GetEnvironmentVariable("ARENA_TRACE") is { } tr && tr.Split('@')[0] == spec.Key ? tr : null;
        double traceFrom = trace != null && trace.Contains('@') ? double.Parse(trace.Split('@')[1], System.Globalization.CultureInfo.InvariantCulture) * 60 : 0;
        while (t < spec.Cap * 60 && p.Alive && host.Result == null)"""
assert s.count(old2) == 1
s = s.replace(old2, new2)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
