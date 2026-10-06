L = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic\Play\Story\Levy.cs"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:60], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

sub(L, """ * The camp's yard (the Pike-Captain behind it) and Redcowl's second phase (his
 * own levy, out of the carts under the old red standard) both use it. */""", """ * The camp's yard (the Pike-Captain behind it) and Redcowl's second phase (his
 * own levy, out of the carts under the old red standard) both use it, and the
 * Seventh Legion's shield lines in the Vault (the Decurion's, the Barrow Lord's
 * "Iungite!"), which march silent behind their shields. */""")
sub(L, """    /// <param name="caller">Who calls the step ("Level! ...Step! ...Step!"), if anyone is named.</param>
    public Levy(IStoryArena a, double x, double z, double toX, double toZ, int n, string def = "levy_pike", string? caller = null)
    {
        A = a;
        this.caller = caller;""", """    /// <param name="caller">Who calls the step ("Level! ...Step! ...Step!"), if anyone is named.</param>
    /// <param name="front">What its front is, where it hurts her (the levy's pikes, the Legion's shields).</param>
    /// <param name="calls">The step's words (the first, then every fourth step), if not the levy's.</param>
    public Levy(IStoryArena a, double x, double z, double toX, double toZ, int n, string def = "levy_pike", string? caller = null,
        string front = "the levy's pikes", (string First, string Then)? calls = null)
    {
        A = a;
        this.caller = caller;
        this.front = front;
        this.calls = calls ?? ("Level! ...Step! ...Step!", "Step!");""")
sub(L, """    readonly string? caller;
""", """    readonly string? caller;
    readonly string front;
    readonly (string First, string Then) calls;
""")
sub(L, """            if (caller != null && steps++ % 4 == 0) A.Bark(X - Fx * 2, Z - Fz * 2, steps == 1 ? "Level! ...Step! ...Step!" : "Step!", caller);""",
"""            if (caller != null && steps++ % 4 == 0) A.Bark(X - Fx * 2, Z - Fz * 2, steps == 1 ? calls.First : calls.Then, caller);""")
sub(L, """            B.ShovePlayer(Fx, Fz, 2.2, biteGrace <= 0 ? pike.Damage * 0.5 : 0, "the levy's pikes");""",
"""            B.ShovePlayer(Fx, Fz, 2.2, biteGrace <= 0 ? pike.Damage * 0.5 : 0, front);""")
print("ok")
