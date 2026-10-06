import os
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695"


def edit(rel, pairs):
    p = os.path.join(W, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"godot\src\Audio\Sfx.cs", [(
'''            default:
                a.Play(new Clip { T = t, Of = name, G = 0.3 * g, Pan = pan });
                break;
        }
    }''',
'''            // C03's (docs/cinematics/shoot/c03.md), made until they are recorded.
            case "kneel_water":
                // A great weight going down into the river: a heavy slap and the water closing.
                a.Play(new Tone { T = t, F = 90, F2 = 46, D = 0.5, G = 0.32 * g, Pan = pan });
                a.Play(new Hiss { T = t, A = 0.01, D = 0.7, G = 0.13 * g, Bp = 1200, Bp2 = 500, Q = 0.8, Pan = pan });
                break;
            case "sink":
                // The greatsword going under: a long bubble, rising.
                for (int i = 0; i < 6; i++)
                    a.Play(new Tone { T = t + i * R(0.12, 0.22), F = R(220, 320), F2 = R(600, 900), D = R(0.06, 0.1), G = 0.04 * g * (1 - i / 8.0), Lp = 1600, Pan = pan });
                a.Play(new Tone { T = t, F = 70, F2 = 40, D = 0.6, G = 0.18 * g });
                break;
            case "lamp_out":
                // The flame into the water: a hiss of steam, a small pop, then nothing.
                a.Play(new Hiss { T = t, A = 0.005, D = 0.9, G = 0.12 * g, Bp = 4200, Bp2 = 2200, Q = 1.2, Pan = pan });
                a.Play(new Tone { T = t, F = 420, F2 = 160, D = 0.08, G = 0.08 * g, Pan = pan });
                break;
            case "heart_hum":
                // A wet finger round a glass rim: a pure tone and its fifth, slow to come.
                a.Play(new Tone { T = t, F = 740, F2 = 752, A = 0.8, Hold = 1.6, D = 1.4, G = 0.035 * g, Verb = 0.6, Pan = pan });
                a.Play(new Tone { T = t + 0.2, F = 1110, F2 = 1122, A = 0.9, Hold = 1.2, D = 1.4, G = 0.014 * g, Verb = 0.6, Pan = pan });
                break;
            case "burst":
                // The mud bursting up: a wet thump, earth and gravel, stones rattling down.
                a.Play(new Tone { T = t, F = 72, F2 = 30, D = 0.8, G = 0.6 * g });
                a.Play(new Hiss { T = t, A = 0.005, D = 1.0, G = 0.3 * g, Lp = 900, Lp2 = 200, Brown = true, Pan = pan });
                for (int i = 0; i < 10; i++)
                    a.Play(new Hiss { T = t + 0.15 + i * R(0.04, 0.09), D = R(0.02, 0.05), G = R(0.03, 0.07) * g, Bp = R(1500, 3500), Q = 3, Pan = pan + R(-0.3, 0.3) });
                break;
            case "sniff":
                a.Play(new Hiss { T = t, A = 0.02, D = 0.12, G = 0.07 * g, Bp = 2600, Q = 1.4, Pan = pan });
                a.Play(new Hiss { T = t + 0.16, A = 0.02, D = 0.1, G = 0.06 * g, Bp = 2900, Q = 1.4, Pan = pan });
                break;
            case "groan":
                // Under everything: first felt more than heard, then timber taking a load, 3 s.
                a.Play(new Tone { T = t, F = 31, F2 = 27, A = 1.0, Hold = 1.6, D = 1.4, G = 0.5 * g });
                a.Play(new Tone { T = t + 0.6, F = 52, F2 = 44, Type = Wave.Saw, A = 0.8, Hold = 1.4, D = 1.2, G = 0.06 * g, Lp = 320, Lp2 = 180, Verb = 0.5 });
                a.Play(new Hiss { T = t + 0.4, A = 1.0, D = 2.0, G = 0.06 * g, Lp = 220, Lp2 = 90, Brown = true });
                break;
            default:
                a.Play(new Clip { T = t, Of = name, G = 0.3 * g, Pan = pan });
                break;
        }
    }'''),
])

edit(r"tools\cinematics\animatic.py", [(
'''    else:
        rec = recording(name)''',
'''    elif name == "kneel_water":
        at(0, tone(90, 46, D=0.5, G=0.32 * g, Pan=pan))
        at(0, hiss(A=0.01, D=0.7, G=0.13 * g, Bp=1200, Bp2=500, Q=0.8, Pan=pan))
    elif name == "sink":
        for i in range(6):
            at(i * R(0.12, 0.22), tone(R(220, 320), R(600, 900), D=R(0.06, 0.1), G=0.04 * g * (1 - i / 8), Lp=1600, Pan=pan))
        at(0, tone(70, 40, D=0.6, G=0.18 * g))
    elif name == "lamp_out":
        at(0, hiss(A=0.005, D=0.9, G=0.12 * g, Bp=4200, Bp2=2200, Q=1.2, Pan=pan))
        at(0, tone(420, 160, D=0.08, G=0.08 * g, Pan=pan))
    elif name == "heart_hum":
        at(0, tone(740, 752, A=0.8, Hold=1.6, D=1.4, G=0.035 * g, Verb=0.6, Pan=pan))
        at(0.2, tone(1110, 1122, A=0.9, Hold=1.2, D=1.4, G=0.014 * g, Verb=0.6, Pan=pan))
    elif name == "burst":
        at(0, tone(72, 30, D=0.8, G=0.6 * g))
        at(0, hiss(A=0.005, D=1.0, G=0.3 * g, Lp=900, Lp2=200, Brown=True, Pan=pan))
        for i in range(10):
            at(0.15 + i * R(0.04, 0.09), hiss(D=R(0.02, 0.05), G=R(0.03, 0.07) * g, Bp=R(1500, 3500), Q=3, Pan=pan + R(-0.3, 0.3)))
    elif name == "sniff":
        at(0, hiss(A=0.02, D=0.12, G=0.07 * g, Bp=2600, Q=1.4, Pan=pan))
        at(0.16, hiss(A=0.02, D=0.1, G=0.06 * g, Bp=2900, Q=1.4, Pan=pan))
    elif name == "groan":
        at(0, tone(31, 27, A=1.0, Hold=1.6, D=1.4, G=0.5 * g))
        at(0.6, tone(52, 44, Type="saw", A=0.8, Hold=1.4, D=1.2, G=0.06 * g, Lp=320, Lp2=180, Verb=0.5))
        at(0.4, hiss(A=1.0, D=2.0, G=0.06 * g, Lp=220, Lp2=90, Brown=True))
    else:
        rec = recording(name)'''),
])
print("ok")
