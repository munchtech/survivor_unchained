import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Actors/People.cs', [
    ('''            HerPaint(p, look.Paint);''', '''            HerPaint(p, look.Paint, look.HairColor);'''),
    ('''        public string? Paint;''', '''        public string? Paint;
        /// <summary>The colour her brows are dyed (her hair's), or none: as painted.</summary>
        public Color? Brow;'''),
    ('''    /// <summary>Paint on her face (Lore.Her.Paints: art/people/paint/ID.png, laid
    /// out on her head's own paint by tools/assets/heroine_paint.py): drawn
    /// over her skin as a pass of its own, so it lies on the skin rather than
    /// in it, with its own sheen (chalky woad, waxy kohl, bright leaf), and
    /// moves with her face as it shapes and speaks. None: taken off.</summary>
    public static void HerPaint(Person p, string? paint)
    {
        p.Paint = paint;
        var def = paint == null ? null : SurvivorUnchained.World.Lore.Her.Paints.FirstOrDefault(x => x.Id == paint);
        var file = def == null ? "" : $"res://art/people/paint/{def.Id}.png";
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName != "skin_head" || mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial skin) continue;
                if (def == null || !ResourceLoader.Exists(file)) { skin.NextPass = null; continue; }
                paintShader ??= GD.Load<Shader>("res://shaders/heroine_paint.gdshader");
                var m = new ShaderMaterial { Shader = paintShader };
                m.SetShaderParameter("paint", GD.Load<Texture2D>(file));
                m.SetShaderParameter("rough", (float)def.Rough);
                m.SetShaderParameter("metal", (float)def.Metal);
                skin.NextPass = m;
            }
    }''', '''    /// <summary>Paint on her face (Lore.Her.Paints: art/people/paint/ID.png, laid
    /// out on her head's own paint by tools/assets/heroine_paint.py): drawn
    /// over her skin as a pass of its own, so it lies on the skin rather than
    /// in it, with its own sheen (chalky woad, waxy kohl, bright leaf), and
    /// moves with her face as it shapes and speaks. None: taken off.
    /// Under it, her brows dyed her hair's colour (art/people/paint/brows.png:
    /// her painted brows, found), since they are painted copper into her skin;
    /// her hair as it grew keeps them as painted.</summary>
    public static void HerPaint(Person p, string? paint, Color? brow = null)
    {
        p.Paint = paint;
        p.Brow = brow;
        var def = paint == null ? null : SurvivorUnchained.World.Lore.Her.Paints.FirstOrDefault(x => x.Id == paint);
        var file = def == null ? "" : $"res://art/people/paint/{def.Id}.png";
        const string brows = "res://art/people/paint/brows.png";
        foreach (var mi in p.Meshes)
            for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
            {
                if (mi.Mesh.SurfaceGetMaterial(s)?.ResourceName != "skin_head" || mi.GetSurfaceOverrideMaterial(s) is not ShaderMaterial skin) continue;
                paintShader ??= GD.Load<Shader>("res://shaders/heroine_paint.gdshader");
                // The passes over her skin, in order: her brows, then the paint.
                ShaderMaterial? first = null, last = null;
                void Then(ShaderMaterial m) { if (last == null) first = m; else last.NextPass = m; last = m; }
                if (brow is Color b && ResourceLoader.Exists(brows))
                {
                    var m = new ShaderMaterial { Shader = paintShader };
                    m.SetShaderParameter("paint", GD.Load<Texture2D>(brows));
                    m.SetShaderParameter("dyed", true);
                    m.SetShaderParameter("dye", b);
                    m.SetShaderParameter("rough", 0.8f);
                    Then(m);
                }
                if (def != null && ResourceLoader.Exists(file))
                {
                    var m = new ShaderMaterial { Shader = paintShader };
                    m.SetShaderParameter("paint", GD.Load<Texture2D>(file));
                    m.SetShaderParameter("rough", (float)def.Rough);
                    m.SetShaderParameter("metal", (float)def.Metal);
                    Then(m);
                }
                skin.NextPass = first;
            }
    }'''),
    ('''        if (look.Paint != p.Paint) HerPaint(p, look.Paint);''', '''        if (look.Paint != p.Paint || look.HairColor != p.Brow) HerPaint(p, look.Paint, look.HairColor);'''),
])

edit('godot/shaders/heroine_paint.gdshader', [
    ('''uniform float strength = 1.0;
''', '''uniform float strength = 1.0;
// Her brows (paint/brows.png, how much brow there is in its alpha): drawn in
// her hair's colour, a shade darker as brows are, covering the copper brows
// painted into her skin where they are thick.
uniform bool dyed = false;
uniform vec3 dye : source_color = vec3(0.35, 0.2, 0.1);
'''),
    ('''	vec4 p = texture(paint, UV);
	ALBEDO = p.rgb;
	ALPHA = p.a * strength;''', '''	vec4 p = texture(paint, UV);
	ALBEDO = dyed ? dye * 0.55 : p.rgb;
	ALPHA = (dyed ? smoothstep(0.04, 0.55, p.a) : p.a) * strength;'''),
])
