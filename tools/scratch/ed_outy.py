p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\src\Ui\UiArt.cs'
s = open(p, encoding='utf-8').read()
rep = [
    ('public sealed record Slice(string File, int L, int T, int R, int B, bool Tile = false, int Out = 0, int Clear = -1);',
     'public sealed record Slice(string File, int L, int T, int R, int B, bool Tile = false, int Out = 0, int Clear = -1, int OutY = -1)\n    {\n        /// <summary>How far past the control above and below (Out unless OutY is set).</summary>\n        public int Oy => OutY >= 0 ? OutY : Out;\n    }'),
    ('["bar_casing_boss"] = new("bars/casing_boss.png", 64, 14, 64, 14, Tile: true, Out: 12),',
     '["bar_casing_boss"] = new("bars/casing_boss.png", 64, 24, 64, 24, Tile: true, Out: 64, OutY: 24),'),
    ('ExpandMarginLeft = s.Out, ExpandMarginTop = s.Out, ExpandMarginRight = s.Out, ExpandMarginBottom = s.Out,',
     'ExpandMarginLeft = s.Out, ExpandMarginTop = s.Oy, ExpandMarginRight = s.Out, ExpandMarginBottom = s.Oy,'),
    ('[Side.Top] = s.T - s.Out, [Side.Right] = s.R - s.Out, [Side.Bottom] = s.B - s.Out };',
     '[Side.Top] = s.T - s.Oy, [Side.Right] = s.R - s.Out, [Side.Bottom] = s.B - s.Oy };'),
]
for a, b in rep:
    assert a in s, a
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
