PAIRS = [
("""        ((ShaderMaterial)world.Material).SetShaderParameter("dim", Mathf.Lerp(1.1f, 0.62f, strength));""",
"""        ((ShaderMaterial)world.Material).SetShaderParameter("dim", Mathf.Lerp(1.1f, 0.62f, strength));
        // A full page sees the world through it a little (the owner: "slightly see through"): a lighter
        // blur, so what is sensed through the page is the place, not a smear.
        if (page) { ((ShaderMaterial)world.Material).SetShaderParameter("blur", 1.8f); ((ShaderMaterial)world.Material).SetShaderParameter("dim", 0.82f); }"""),
("""            var v = new TextureRect { Texture = skin, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Tile, MouseFilter = MouseFilterEnum.Ignore, Modulate = new Color(1, 1, 1, 0.9f) };""",
"""            var v = new TextureRect { Texture = skin, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Tile, MouseFilter = MouseFilterEnum.Ignore, Modulate = new Color(1, 1, 1, 0.85f) };"""),
]
