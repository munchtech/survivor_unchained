PAIRS = [
("""            var dir = d.Normalized();
            float a = Mathf.Lerp(0.7f, 1f, m.Near);
            var c = m.Color with { A = a };""",
"""            var dir = d.Normalized();
            float a = Mathf.Lerp(0.7f, 1f, m.Near);
            var c = m.Color with { A = a };
            // A Legendary lying untaken: UI art's amber chevron, turned to point at it, breathing with
            // the pillar's light, its glow thrown round it (docs/design/LOOT_DESIGN.md §8.2).
            if (m.Glyph == "legendary" && UiArt.Art("hud/pointer_legendary.png") is { } chevron)
            {
                float t = Time.GetTicksMsec() / 1000f, breath = 0.85f + 0.15f * Mathf.Sin(t * 3.2f);
                var s = chevron.GetSize() * (1.05f + 0.08f * Mathf.Sin(t * 3.2f));
                DrawCircle(p, 30, m.Color with { A = 0.16f * breath });
                DrawSetTransform(p, dir.Angle());
                DrawTextureRect(chevron, new Rect2(-s / 2, s), false, Colors.White with { A = breath });
                DrawSetTransform(Vector2.Zero);
                QueueRedraw();
                continue;
            }"""),
]
