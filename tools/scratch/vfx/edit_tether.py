p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\BattleFx.Skills.cs"
s = open(p, encoding="utf-8").read()
a = """                // The tether: a thread back to the hand that cast it.
                if (art.StartsWith("tether") && b0 != null)
                {
                    var hand = V(b0.Player.X, Y(b0.Player.X, b0.Player.Z) + 1.15, b0.Player.Z);
                    var mid = (hand + at) / 2 + Vector3.Up * 0.3f + new Vector3(Mathf.Sin((float)now * 7 + p.Id), 0, Mathf.Cos((float)now * 6 + p.Id)) * 0.25f;
                    Ribbons.Now(new[] { hand, (hand + mid) / 2, mid, (mid + at) / 2, at }, 0.07f, Hdr("#b080ff", 1f), 1.6f, Ribbons.Style.Wisp, new[] { 0.3f, 0.8f, 1f, 0.8f, 0.5f });
                }"""
b = """                // The tether: a coil of the dark wound back to the hand that cast it, twisting as it
                // pays out, and what it takes running back up it to her in her blood's rose. (A
                // single faint wisp of a thread was not seen at all in a crowd.)
                if (art.StartsWith("tether") && b0 != null)
                {
                    var hand = V(b0.Player.X, Y(b0.Player.X, b0.Player.Z) + 1.15, b0.Player.Z);
                    var span = at - hand;
                    float len = Mathf.Max(0.3f, span.Length());
                    var along = span / len;
                    var side = Mathf.Abs(along.Y) < 0.95f ? along.Cross(Vector3.Up).Normalized() : Vector3.Right;
                    var lift = side.Cross(along);
                    const int N = 28;
                    var coil = new Vector3[N + 1];
                    var core = new Vector3[N + 1];
                    var w = new float[N + 1];
                    float turns = Mathf.Max(2, len / 0.8f), tf = (float)now * 9 + p.Id;
                    for (int j = 0; j <= N; j++)
                    {
                        float u = j / (float)N, bell = Mathf.Sin(u * Mathf.Pi);
                        var spine = hand + span * u + Vector3.Up * bell * 0.4f;
                        float ang = u * turns * Mathf.Tau - tf, rad = 0.05f + 0.13f * bell;
                        core[j] = spine;
                        coil[j] = spine + (side * Mathf.Cos(ang) + lift * Mathf.Sin(ang)) * rad;
                        w[j] = 0.35f + 0.65f * bell;
                    }
                    Ribbons.Now(core, 0.05f, Hdr("#3a1460", 1f), 1f, Ribbons.Style.Wisp, w);
                    Ribbons.Now(coil, 0.04f, Hdr("#b47cff", 1.25f), 1.7f, Ribbons.Style.Glow, w);
                    if (R() < 0.6f)
                    {
                        float k = (float)((now * 1.4 + p.Id * 0.37) % 1.0);
                        var back = at - span * k + Vector3.Up * Mathf.Sin(k * Mathf.Pi) * 0.4f;
                        Sparks.Spawn(back, -along * 0.5f, 0.22f, 0.09f, Hdr("#ff6a9a", 1.3f), Hdr("#a0204a", 0.8f), 0.03f, 0, 1);
                    }
                }"""
assert a in s
s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
