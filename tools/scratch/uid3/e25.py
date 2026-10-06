import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/Ornate.cs', [
    ('''public partial class Backdrop : Control
{
    public float Strength = 0.88f;

    public Backdrop(Action? onClick = null, float strength = 0.88f)
    {
        Strength = strength;
        Style.Fill(this);
        MouseFilter = MouseFilterEnum.Stop;
        if (onClick != null) GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) onClick(); };
        var dark = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(0.03f, 0.02f, 0.04f, strength * 0.72f), new Color(0.02f, 0.015f, 0.03f, strength) }, Offsets = new[] { 0.2f, 1f } },''', '''public partial class Backdrop : Control
{
    public float Strength = 0.88f;
    static Shader? blur;

    public Backdrop(Action? onClick = null, float strength = 0.88f)
    {
        Strength = strength;
        Style.Fill(this);
        MouseFilter = MouseFilterEnum.Stop;
        if (onClick != null) GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) onClick(); };
        // The world behind, out of focus and darkened (shaders/ui_backdrop.gdshader): the page
        // sits in the place the survivor stands, never on flat black.
        blur ??= GD.Load<Shader>("res://shaders/ui_backdrop.gdshader");
        var world = new ColorRect { Material = new ShaderMaterial { Shader = blur }, MouseFilter = MouseFilterEnum.Ignore };
        ((ShaderMaterial)world.Material).SetShaderParameter("dim", Mathf.Lerp(0.85f, 0.35f, strength));
        Style.Fill(world);
        AddChild(world);
        var dark = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                // (the blurred world is already dim: the shade only deepens toward the edges, where it frames the page)
                Gradient = new Gradient { Colors = new[] { new Color(0.03f, 0.02f, 0.04f, strength * 0.25f), new Color(0.02f, 0.015f, 0.03f, strength * 0.8f) }, Offsets = new[] { 0.2f, 1f } },'''),
])

edit('godot/src/Ui/Style.cs', [
    ('''    /// <summary>A quieter plate inside a plate (a group, a card's body).</summary>''', '''    static ImageTexture? column;

    /// <summary>A column on a page, with no frame: dark glass over the blurred world, a gold
    /// hairline along its top, darkest where its words begin and fading down, so the space
    /// under what it holds is never a flat black box. Frames are for what is acted on.</summary>
    public static StyleBox Column(int pad = 20)
    {
        if (column == null)
        {
            const int w = 64, h = 256;
            var img = Image.CreateEmpty(w, h, false, Image.Format.Rgba8);
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float fy = (y - 2) / (float)(h - 3), fx = Math.Min(x, w - 1 - x) / (w * 0.06f);
                    // (fading in at the sides over a few pixels' worth of the width, so its edges are soft)
                    float side = Math.Clamp(fx, 0, 1);
                    float a = y < 2 ? 0.55f * side : (0.66f - 0.5f * MathF.Pow(fy, 0.8f)) * side;
                    img.SetPixel(x, y, y < 2 ? new Color(GoldDim, a) : new Color(0.03f, 0.024f, 0.036f, a));
                }
            column = ImageTexture.CreateFromImage(img);
        }
        var b = new StyleBoxTexture { Texture = column, TextureMarginTop = 2 };
        b.ContentMarginLeft = b.ContentMarginRight = pad;
        b.ContentMarginTop = pad + 2;
        b.ContentMarginBottom = pad;
        return b;
    }

    /// <summary>A quieter plate inside a plate (a group, a card's body).</summary>'''),
])

edit('godot/src/Ui/Overlay.cs', [
    ('''    /// <summary>A pane on a page: an ornate frame at a place, with a column inside it.</summary>
    protected static VBoxContainer Pane(Control parent, Rect2 at, StyleBox? box = null, int gap = Style.Gap3)
    {
        var p = Style.Panel(box ?? Style.Plate(20));''', '''    /// <summary>A pane on a page, at a place, with a column inside it: no frame unless one is
    /// asked for (the page's one hero plate, say), so frames are not nested in frames.</summary>
    protected static VBoxContainer Pane(Control parent, Rect2 at, StyleBox? box = null, int gap = Style.Gap3)
    {
        var p = Style.Panel(box ?? Style.Column(20));'''),
])
