PAIRS = [
("""            Link(seal, licence, link ?? "", Style.UiHeavy, 15, Style.EmberHi);
            seal.SizeFlagsVertical = SizeFlags.ShrinkCenter;""", """            Link(seal, licence, link ?? "", Style.UiHeavy, 15, Style.EmberHi);
            seal.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            // (a rich label wants its width given: its words' own, so the heading keeps the rest)
            seal.CustomMinimumSize = new Vector2(Style.UiHeavy.GetStringSize(licence, HorizontalAlignment.Left, -1, 15).X + 6, 0);"""),
]
