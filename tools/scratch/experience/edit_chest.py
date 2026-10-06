p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1f5623590e09883\godot\src\Ui\ItemModels.cs'
s = open(p, encoding='utf-8').read()
old = s[s.index("    static Node3D Chest()"):s.index("    /* ----------------------------------------------------------- gathered -- */")]
new = '''    /// <summary>An ironbound chest. Its lid is a child of its own ("Lid"), hinged along the back of
    /// the top, so a chest opening in a fight can throw it back (ChestCeremony); merged into one
    /// mesh (a chest lying on the ground) it is the same chest.</summary>
    static Node3D Chest()
    {
        var root = new Node3D();
        var wood = Grain("#8a6a48", "#4a3420", 3, 0.75f);
        var iron = Iron();
        // The hinge: the top's back edge.
        const float hy = 0.25f, hz = -0.31f;
        var lid = new Node3D { Name = "Lid", Position = new Vector3(0, hy, hz) };
        root.AddChild(lid);
        Transform3D L(float x, float y, float z) => At(x, y - hy, z - hz);
        Add(root, new BoxMesh { Size = new Vector3(1.0f, 0.5f, 0.6f) }, wood);
        Add(lid, new BoxMesh { Size = new Vector3(1.02f, 0.16f, 0.62f) }, wood, L(0, 0.33f, 0));
        foreach (float x in new[] { -0.32f, 0.32f })
        {
            Add(root, new BoxMesh { Size = new Vector3(0.07f, 0.51f, 0.625f) }, iron, At(x, -0.005f, 0));
            Add(lid, new BoxMesh { Size = new Vector3(0.07f, 0.17f, 0.625f) }, iron, L(x, 0.335f, 0));
        }
        Add(root, new BoxMesh { Size = new Vector3(1.03f, 0.04f, 0.63f) }, iron, At(0, 0.25f, 0));
        foreach (float x in new[] { -0.49f, 0.49f })
            foreach (float z in new[] { -0.29f, 0.29f })
            {
                Add(root, new BoxMesh { Size = new Vector3(0.08f, 0.08f, 0.08f) }, iron, At(x, -0.23f, z));
                Add(lid, new BoxMesh { Size = new Vector3(0.08f, 0.08f, 0.08f) }, iron, L(x, 0.39f, z));
            }
        Add(root, new BoxMesh { Size = new Vector3(0.2f, 0.22f, 0.03f) }, Brass(), At(0, 0.18f, 0.31f));
        Add(root, new BoxMesh { Size = new Vector3(0.03f, 0.07f, 0.01f) }, Mat("#0a0806"), At(0, 0.15f, 0.327f));
        Add(lid, new BoxMesh { Size = new Vector3(0.08f, 0.14f, 0.03f) }, iron, L(0, 0.33f, 0.325f));
        var rivets = new Build();
        var lidRivets = new Build();
        foreach (float x in new[] { -0.32f, 0.32f })
        {
            foreach (float y in new[] { -0.15f, 0.05f }) rivets.Append(Rivet(), At(x, y, 0.313f));
            lidRivets.Append(Rivet(), L(x, 0.33f, 0.313f));
        }
        Add(root, rivets, iron);
        Add(lid, lidRivets, iron);
        return root;
    }

'''
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print("ok")
