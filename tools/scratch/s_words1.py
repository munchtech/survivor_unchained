PAIRS = [
('''            if (drives == 0) A.Say("The drive", "The gap is her lane: go through the wolves", "danger");''',
'''            if (drives == 0) A.Say("The drive", "The gap is where she runs: go through the wolves", "danger");'''),
('''                    if (!missedOnce) { missedOnce = true; A.Bark(e.X, e.Z, "She missed, and stands there blowing. Now.", null); }
                }
                else if (!hitOnce) { hitOnce = true; A.Bark(B.Player.X, B.Player.Z, "The gap was hers. Through the wolves, not the gap.", null); }''',
'''                    if (!missedOnce)
                    {
                        missedOnce = true;
                        A.Bark(e.X, e.Z, "She misses, and stands with her head down, blowing.", null);
                        A.Say("She is open", "Hit her while she blows", "boon");
                    }
                }
                else if (!hitOnce) { hitOnce = true; A.Say("The gap is hers", "Through the wolves, never the gap", "danger"); }'''),
('''    public override string BossAt => "den_mouth";''', '''    public override string BossAt => "den_mouth";
    public override string ShutSight => "Behind you, the Pack fills the way you came.";'''),
]
