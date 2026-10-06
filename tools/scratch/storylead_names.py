"""The creation screen's suggested names and the default name never spend a
name the story has (Ashe, Kell, Orrin) or nearly has (Isolde/Ysolde,
Brannagh/Brannoc, Corwen/Corran, Hollis/Holloway, Tamsin/Tam)."""
root = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\src\\"
edits = {
    r"Ui\Front.cs": [(
        'static readonly string[] Names = { "Ashe", "Brannagh", "Corwen", "Dace", "Edda", "Fen", "Garrow", "Hollis", "Isolde", "Jessamy", "Kell", "Lorne", "Maren", "Nolly", "Orrin", "Pim", "Quill", "Rhosyn", "Sabre", "Tamsin", "Ulla", "Voss", "Wren", "Yarrow" };',
        '// Never a name the story has spent or nearly spent (Ashe, Kell, Orrin; Ysolde, Brannoc, Corran, Holloway, Tam).\r\n'
        '    static readonly string[] Names = { "Alder", "Bryony", "Cass", "Dace", "Edda", "Fen", "Garrow", "Hester", "Ilse", "Jessamy", "Kit", "Lorne", "Maren", "Nolly", "Orla", "Pim", "Quill", "Rhosyn", "Sabre", "Tegan", "Ulla", "Voss", "Wren", "Yarrow" };')],
    r"Game\Game.cs": [('Name = Args.Get("name") ?? "Ashe",', 'Name = Args.Get("name") ?? "Wren",')],
    r"Game\GameFront.cs": [('draft.Name = "Ashe";', 'draft.Name = "Wren";')],
}
for f, pairs in edits.items():
    p = root + f
    b = open(p, "rb").read().decode("utf-8")
    for o, n in pairs:
        assert b.count(o) == 1, (f, o[:40])
        b = b.replace(o, n)
    open(p, "wb").write(b.encode("utf-8"))
print("ok")
