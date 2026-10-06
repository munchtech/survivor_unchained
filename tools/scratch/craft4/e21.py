from ed import sub

sub("src/Ui/Forge.cs", [
("""        links = new Links(this) { CustomMinimumSize = new Vector2(width, 36) };""",
"""        // As long as the chain is (a link a point, at the links' own pitch), up to the width allowed, so
        // its count sits beside its last link rather than across a gap.
        int most = Math.Max(full, heat) ;
        links = new Links(this) { CustomMinimumSize = new Vector2(Math.Min(width, Links.Length(most)), Links.H) };"""),
("""    sealed partial class Links : Control
    {
        readonly HeatGauge g;
        public Links(HeatGauge g) { this.g = g; MouseFilter = MouseFilterEnum.Ignore; }""",
"""    sealed partial class Links : Control
    {
        readonly HeatGauge g;
        public Links(HeatGauge g) { this.g = g; MouseFilter = MouseFilterEnum.Ignore; }

        /// <summary>The links' drawn height, and a chain's length for n links at their own pitch.</summary>
        public const float H = 38;
        public static float Length(int n) => (n - 1) * 17.2f * (H / 44f) + 52 * (H / 44f);"""),
])
