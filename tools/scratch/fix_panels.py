import re
p='godot/src/Ui/Panels.cs'
s=open(p,encoding='utf-8',newline='').read()
nl='\r\n' if '\r\n' in s else '\n'
s=s.replace('\r\n','\n')
blocks=list(re.finditer(r'<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>> origin/worktree-agent-abd496197891ea843\n', s, flags=re.S))
assert len(blocks)==2
first='''        panel.SetMeta("frame", crown ? "card_evolve" : $"card_{Math.Min(r, 4)}");
        // A painted card has no glow of its own: its rarity's, when lifted, is drawn behind it.
        var glow = new Panel { MouseFilter = MouseFilterEnum.Ignore, ShowBehindParent = true, Name = "Glow" };
        Style.Fill(glow);
        panel.AddChild(glow);
'''
second='''            var edge = banishing && on ? new Color("#ff6a4a") : ch ? Style.GoldHi : rc;
            // A crested card: its rarity in the crest and the corners, a glow when lifted.
            var s = OrnateBox.Make(OrnateBox.Kind.Card, 0, edge);
            s.Crest = 120;
            s.Glow = on ? 1.4f : 0;
            s.Top = new Color("#211c26").Lerp(rc, 0.05f);
            bool art = UiArt.Has((string)panel.GetMeta("frame"));
            panel.AddThemeStyleboxOverride("panel", art ? UiArt.Frame((string)panel.GetMeta("frame"), s) : s);
            if (panel.GetNodeOrNull<Panel>("Glow") is { } glow)
            {
                var g = Style.Box(new Color(0, 0, 0, 0), new Color(0, 0, 0, 0), 0, 10, 0);
                g.ShadowColor = on ? edge with { A = 0.45f } : new Color(0, 0, 0, 0.7f);
                g.ShadowSize = on ? 34 : 18;
                glow.AddThemeStyleboxOverride("panel", g);
                glow.Visible = art;
            }
            if (b.FindChild("Medal", true, false) is Medallion m) { m.Lit = on; m.QueueRedraw(); }
'''
b1,b2=blocks
s=s[:b1.start()]+first+s[b1.end():b2.start()]+second+s[b2.end():]
open(p,'w',encoding='utf-8',newline='').write(s.replace('\n',nl))
print('ok', nl=='\r\n')
