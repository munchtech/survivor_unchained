using System;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>M4 (docs/design/M4_HUD.md section 2): what Resolve's veins in her hair show, frame by frame, as plain
/// numbers (no Godot: tests read it; ResolveVeins.cs sends them to hud_dg_resolve.gdshader, each only on change).
/// Feed it the meter once a frame (Battle.Resolve: On, Value / Max, LastReason, LastAt, the battle's clock), Tick it
/// with the frame's dt. The level eases (UpTime up, DownTime down); each reason has its own motion:
/// Landed a core-white packet runs from the tips to the front in PacketTime, then the front flares FlareTime; Taken
/// the same in edge amber; Blocked a smaller packet in the steel spark; Spent the spent band flashes core and goes
/// dark in SpentTime; Drained embers run down the veins while it drains; Faded the lit veins cool (mid, edge, bronze)
/// as they fall; Full one glint at the crown (GlintTime), a shimmer down the veins every ShimmerEvery, a warm rim.
/// Off: nothing drawn. No allocation.</summary>
public sealed class ResolveMotion
{
    public enum Packet { Core, Edge, Spark }
    public enum Motion { None, Landed, Taken, Blocked, Spent, Drained, Faded }

    public const float UpTime = 0.12f, DownTime = 0.2f, PacketTime = 0.25f, FlareTime = 0.15f, SpentTime = 0.2f,
        GlintTime = 0.07f, ShimmerEvery = 2.5f, ShimmerTime = 0.9f, RimTime = 0.4f, CoolTime = 2.0f, CoolMost = 0.85f,
        Hold = 0.6f, PacketW = 0.07f, SparkW = 0.045f, SparkK = 0.6f;
    /// <summary>A continuous reason (Drained, Faded) counts as running while its last change is this recent (s).</summary>
    public const double Running = 0.3;

    // what the shader draws
    public bool Shown;
    public float Level, PktG = -1, PktK, PktW = PacketW, Flare, SpentLo, SpentHi, SpentK, Drain, Cool, ShimmerG = -1, Glint, Rim;
    public Packet PktColor;

    float target;
    bool on, full, wasFull, draining, fading;
    double seenAt = double.NegativeInfinity;
    Motion pkt = Motion.None;
    float pktT = 99, spentT = 99, glintT = 99, shimmerT, fadeFor;
    bool pinned;

    /// <summary>Which motion a reason plays.</summary>
    public static Motion MotionFor(ResolveReason r) => r switch
    {
        ResolveReason.Landed => Motion.Landed,
        ResolveReason.Taken => Motion.Taken,
        ResolveReason.Blocked => Motion.Blocked,
        ResolveReason.Spent => Motion.Spent,
        ResolveReason.Drained => Motion.Drained,
        ResolveReason.Faded => Motion.Faded,
        _ => Motion.None,
    };

    /// <summary>The level shown, eased toward the target: up over about UpTime, down over about DownTime (exponential,
    /// 95% there by then; snapped within 0.001).</summary>
    public static float Ease(float shown, float target, float dt)
    {
        float tau = (target > shown ? UpTime : DownTime) / 3f;
        float s = shown + (target - shown) * (1 - MathF.Exp(-dt / tau));
        return MathF.Abs(target - s) < 0.001f ? target : s;
    }

    /// <summary>Her figure's fade (LifeLamp's fig_a, fadeTo..1) to the veins' alpha: they hold at Hold when she fades.</summary>
    public static float Alpha(float figA, float fadeTo) => Hold + (1 - Hold) * Math.Clamp((figA - fadeTo) / Math.Max(1e-3f, 1 - fadeTo), 0, 1);

    /// <summary>The meter, once a frame. now: the battle's clock (LastAt's).</summary>
    public void Feed(bool on, double value, double max, ResolveReason reason, double lastAt, double now)
    {
        if (pinned) return;
        this.on = on;
        target = max > 0 ? (float)Math.Clamp(value / max, 0, 1) : 0;
        full = on && max > 0 && value >= max;
        draining = reason == ResolveReason.Drained && now - lastAt < Running;
        fading = reason == ResolveReason.Faded && now - lastAt < Running;
        if (lastAt == seenAt) return;
        bool first = double.IsNegativeInfinity(seenAt);
        seenAt = lastAt;
        if (first && now - lastAt > Running) return;   // (a change from before the view came: no motion)
        switch (MotionFor(reason))
        {
            case Motion.Landed: case Motion.Taken: case Motion.Blocked:
                pkt = MotionFor(reason); pktT = 0; break;
            case Motion.Spent:
                // (a spend on a spend still flashing: the band grows from the first one's top)
                SpentHi = spentT < SpentTime ? Math.Max(SpentHi, Level) : Level; SpentLo = target; spentT = 0; break;
        }
    }

    public void Tick(float dt)
    {
        if (pinned) return;
        Shown = on;
        if (!on)
        {
            Level = target; pkt = Motion.None; pktT = spentT = glintT = 99;
            Drain = Cool = Rim = Glint = Flare = SpentK = PktK = 0; ShimmerG = PktG = -1; wasFull = false; return;
        }
        Level = Ease(Level, target, dt);
        // the packet: from the tips (g 0) to the front, then the front flares
        if (pkt != Motion.None)
        {
            pktT += dt;
            PktColor = pkt == Motion.Taken ? Packet.Edge : pkt == Motion.Blocked ? Packet.Spark : Packet.Core;
            PktW = pkt == Motion.Blocked ? SparkW : PacketW;
            float k = pkt == Motion.Blocked ? SparkK : 1;
            if (pktT < PacketTime) { PktG = Level * (pktT / PacketTime); PktK = k; Flare = 0; }
            else if (pktT < PacketTime + FlareTime) { PktG = -1; PktK = 0; Flare = k * (1 - (pktT - PacketTime) / FlareTime); }
            else { pkt = Motion.None; PktG = -1; PktK = 0; Flare = 0; }
        }
        // Spent: the band flashes core and goes dark
        spentT += dt;
        SpentK = spentT < SpentTime ? 1 - spentT / SpentTime : 0;
        if (SpentK == 0) SpentHi = SpentLo = 0;
        // Drained: the embers in quickly, out a little slower
        Drain = draining ? Math.Min(1, Drain + dt / 0.1f) : Math.Max(0, Drain - dt / 0.25f);
        // Faded: cooling while it falls; warm again at once when the fight is back
        fadeFor = fading ? fadeFor + dt : 0;
        Cool = fading ? Math.Min(CoolMost, fadeFor / CoolTime) : Math.Max(0, Cool - dt * 3);
        // Full: one glint as it arrives, the shimmer every ShimmerEvery, the rim eased in
        if (full && !wasFull) { glintT = 0; shimmerT = 0; }
        wasFull = full;
        glintT += dt;
        Glint = glintT < GlintTime ? 1 : 0;
        if (full)
        {
            shimmerT += dt;
            float u = shimmerT % ShimmerEvery - 0.3f;   // (the first shimmer just after the glint)
            ShimmerG = u >= 0 && u < ShimmerTime ? Level * (1 - u / ShimmerTime) : -1;
        }
        else ShimmerG = -1;
        Rim = full ? Math.Min(1, Rim + dt / RimTime) : Math.Max(0, Rim - dt / RimTime);
    }

    /// <summary>--hud-pin resolve=L[:why]: held at L, frozen at the reason's most readable instant (the packet half way
    /// up, the spent band mid-flash, the embers running, the veins cooled to the edge amber, full's glint on with the
    /// shimmer mid-hair and the rim lit). Feed and Tick do nothing after.</summary>
    public void Pin(float level, string why)
    {
        on = true; target = Level = Math.Clamp(level, 0, 1);
        Shown = true;
        PktG = ShimmerG = -1; PktK = Flare = SpentK = SpentLo = SpentHi = Drain = Cool = Glint = Rim = 0; PktW = PacketW;
        switch (why)
        {
            case "landed": PktColor = Packet.Core; PktG = Level * 0.55f; PktK = 1; break;
            case "taken": PktColor = Packet.Edge; PktG = Level * 0.55f; PktK = 1; break;
            case "blocked": PktColor = Packet.Spark; PktG = Level * 0.55f; PktK = SparkK; PktW = SparkW; break;
            case "spent": SpentLo = Level; SpentHi = Math.Min(1, Level + 0.18f); SpentK = 0.75f; break;
            case "drained": Drain = 1; break;
            case "faded": Cool = 0.5f; break;
            case "full": Glint = 1; ShimmerG = Level * 0.55f; Rim = 1; break;
        }
        pinned = true;
    }

    /// <summary>M4 section 3: her life bar and dash pips under her feet: in a fight, by night (the ember: the whole
    /// night is the fight) or in the campaign while its fight is on (fightOn: Resolve's own rule, a hostile within
    /// its FightRadius or a blow given or taken within FadeAfter; at peace they fade), alive, with the "Health under
    /// you" setting on and the Lamps not open wide.</summary>
    public static bool UnderWanted(bool combat, bool ember, bool campaign, bool fightOn, bool alive, bool setting, bool lampsWide)
        => combat && (ember || campaign && fightOn) && alive && setting && !lampsWide;

    /// <summary>M4 section 3: a step won's motion on the pips: a charge pops the new pip in with a core glint (true);
    /// stride, breath or landing glints every pip once (false).</summary>
    public static bool StepPopsNew(DashStepKind k) => k == DashStepKind.Charge;
}
