PAIRS = [
("""        if (panel != "")
        {
            var box = Style.Panel(Style.Plate(20));
            box.Position = new Vector2(540, panel == "controls" ? 90 : 500);
            box.CustomMinimumSize = new Vector2(panel == "controls" ? 820 : 560, 0);
            Nav.Scope = box;
            var v = Style.V(10, new Plaque(panel switch { "load" => "Journeys", "settings" => "Settings", _ => "Controls" }, 26, 50));
            switch (panel)
            {
                case "load":
                    foreach (var s in slots)
                    {
                        var arch = Callings.Archetypes.GetValueOrDefault(s.Archetype);
                        var row = Style.H(12);
                        row.AddChild(Glyphs.Icon(s.Archetype switch { "warden" => "shield", "reaver" => "axe", "arcanist" => "staff", _ => "bow" }, 26, Style.Gold));
                        var words = Style.V(0, Style.Label(s.Name, Style.Display, 18, s.Alive ? new Color("#f2e6cc") : new Color("#a08a80")),
                            Style.Label($"{arch?.Name} {s.Level} · Day {s.Day} · {ZoneNames.GetValueOrDefault(s.Zone, s.Zone)}", Style.UiBold, Style.Caption, Style.InkDim),
                            Style.Label(s.Alive ? $"Saved {Ago(s.SavedAt)}" : "Fallen", Style.TextItalic, Style.Caption, Style.InkFaint));
                        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
                        row.AddChild(words);
                        int slot = s.Slot;
                        row.AddChild(Style.Button("Resume", () => G.Continue(slot), true, true));
                        row.AddChild(Style.Button("Forget", () => { G.Saves.Remove(slot); Refresh(); }, false, true));
                        v.AddChild(row);
                    }
                    break;
                case "settings": v.AddChild(SettingsPanel.Build(G, Refresh)); break;
                default: v.AddChild(new ControlsPanel()); break;
            }
            box.AddChild(v);
            AddChild(box);
        }""", """        if (panel != "")
        {
            // A fitted panel over the fire's picture, as the pause opens its own: its name, its rows as
            // type, back with its key at its foot.
            var v = Fitted(new Vector2(540, 16), panel == "controls" ? 880 : panel == "settings" ? 780 : 640);
            Nav.Scope = v;
            v.AddChild(new Title(panel switch { "load" => "Journeys", "settings" => "Settings", _ => "Controls" }, 30, false));
            switch (panel)
            {
                case "load":
                    foreach (var s in slots)
                    {
                        var arch = Callings.Archetypes.GetValueOrDefault(s.Archetype);
                        var mark = Glyphs.Icon(s.Archetype switch { "warden" => "shield", "reaver" => "axe", "arcanist" => "staff", _ => "bow" }, 30, s.Alive ? Kit.Ink2 : Kit.Faint);
                        mark.SizeFlagsVertical = SizeFlags.ShrinkCenter;
                        var words = Style.V(0, Style.Label(s.Name.ToUpperInvariant(), Style.Display, 20, s.Alive ? Kit.Ink : Kit.Dim, false, HorizontalAlignment.Left, false),
                            Style.Label($"{arch?.Name} {s.Level}  ·  Day {s.Day}  ·  {ZoneNames.GetValueOrDefault(s.Zone, s.Zone)}", Style.TextItalic, 16, Kit.HeadInk, false, HorizontalAlignment.Left, false),
                            Style.Label(s.Alive ? $"Saved {Ago(s.SavedAt)}" : "Fallen", Style.Ui, 14, Kit.Dim, false, HorizontalAlignment.Left, false));
                        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
                        int slot = s.Slot;
                        var resume = Kit.Word("Resume", () => G.Continue(slot), Style.EmberHi, 17);
                        var forget = Kit.Word("Forget", () => { G.Saves.Remove(slot); Refresh(); }, Kit.Dim, 15);
                        foreach (var c in new Control[] { resume, forget }) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
                        v.AddChild(Style.H(Style.Gap4, mark, words, resume, forget));
                    }
                    break;
                case "settings": v.AddChild(SettingsPanel.Build(G, Refresh)); break;
                default: v.AddChild(new ControlsPanel()); break;
            }
            v.AddChild(Style.V(Style.Gap3, Kit.RuleH(), Nav.Id(Kit.Keyed(Act.Cancel, "Back", () => Panel(panel)), "back")));
        }"""),
]
