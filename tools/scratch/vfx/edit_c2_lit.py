from ed import edit
edit(r"src\Game\Game.cs", [
    ("""        // --lit: a story night's deadfalls all burning (pictures of them alight).
        if (!litDone && Args.Has("lit") && zone is StoryNight sn3 && Battle != null)
        {
            litDone = true;
            foreach (var f in sn3.Fires) { f.Lit = 9999; f.EverLit = true; scene.SetLit(f.Light, true); }
        }""",
     """        // --lit [S]: a story night's deadfalls all burning (pictures of them alight); for S seconds
        // only, if given (pictures of a fed fire taking, guttering and going out).
        if (!litDone && Args.Has("lit") && zone is StoryNight sn3 && Battle != null)
        {
            litDone = true;
            double litFor = Args.Num("lit", 1) > 1 ? Args.Num("lit", 1) : 9999;
            foreach (var f in sn3.Fires) { f.Lit = litFor; f.EverLit = true; scene.SetLit(f.Light, true); }
        }"""),
])
