using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// Someone standing or walking in the world, as a zone's runtime moves them
/// (Play.INpcView): a Quaternius person with their clothes and what they
/// hold, a looping pose, a gesture played once and back to the loop (or
/// held on its last frame), and walking blended from standing to a walk to
/// a jog by speed.
/// </summary>
public partial class PersonView : Node3D, INpcView
{
    readonly People.Person person;
    string loop = "", loopClip = "";
    double loopSpeed = 1;
    double actLeft;
    bool walking, holding;
    readonly System.Collections.Generic.Dictionary<string, Node3D> held = new();
    /// <summary>What walking and running look like for this one (a shambling dead thing walks otherwise).</summary>
    public string WalkClip = "Walk_Loop", RunClip = "Jog_Fwd_Loop";
    /// <summary>Played by something else (the survivor's AnimationTree), which
    /// then tells her corrective layer what is hers itself.</summary>
    public bool Driven;

    /// <summary>A person; the game's figures stand at 0.8 of their authored
    /// size, a touch over life size (the web game's CHARACTER_SCALE × HUMAN_SCALE).</summary>
    public PersonView(PersonSpec spec, Held? arms, double scale)
    {
        person = People.Build(spec);
        person.Kind = HerClips.Kind(arms?.Right, arms?.Left, arms?.Forearm);
        person.Folk = (person.Kit || person.Package != null) && arms?.Right == null && arms?.Left == null && arms?.Forearm == null;
        person.Root.Scale = Vector3.One * (float)(scale / 0.8 * 1.04) * person.Jitter;
        AddChild(person.Root);
        // (a Marionette package's own walk, when its manifest names one: the risen's lurch)
        if (person.Package is string pkg && NpcPackage.WalkClip(pkg, person.Woman) is string walk) WalkClip = walk;
        if (arms?.Right is string r && Arms.All.ContainsKey(r)) { held["handslot.r"] = Arms.Hold(person, r, "hand_r"); pieces["handslot.r"] = r; }
        if (arms?.Left is string l && Arms.All.ContainsKey(l)) { held["handslot.l"] = Arms.Hold(person, l, "hand_l"); pieces["handslot.l"] = l; }
        if (arms?.Forearm is string f && Arms.All.ContainsKey(f)) { held["forearm.l"] = Arms.Hold(person, f, "lowerarm_l"); pieces["forearm.l"] = f; }
    }

    /// <summary>A held piece's long axis in its bone's frame (toward its far end from the bone), zero if the slot holds
    /// none (HerArmHold swings it along its arc).</summary>
    public Vector3 PieceAxis(string slot)
    {
        if (!held.TryGetValue(slot, out var mount) || !IsInstanceValid(mount) || mount.GetParent() is not Node3D att || !mount.IsInsideTree()) return Vector3.Zero;
        var toBone = att.GlobalTransform.AffineInverse();
        Vector3 best = Vector3.Zero;
        foreach (var n in mount.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (n is not MeshInstance3D mi) continue;
            var box = mi.GetAabb();
            for (int c = 0; c < 8; c++)
            {
                var p = toBone * (mi.GlobalTransform * box.GetEndpoint(c));
                if (p.LengthSquared() > best.LengthSquared()) best = p;
            }
        }
        return best.LengthSquared() > 1e-8f ? best.Normalized() : Vector3.Zero;
    }

    /// <summary>The weapon (Arms id) in each slot.</summary>
    readonly System.Collections.Generic.Dictionary<string, string> pieces = new();

    static string BoneOf(string slot) => slot switch { "handslot.l" => "hand_l", "forearm.l" => "lowerarm_l", _ => "hand_r" };

    /// <summary>Her pieces at their sockets (sheathed) or back in her hands (drawn); a piece with no socket stays in
    /// hand. Hers only (a calling's town clips ride with it: PlayerView).</summary>
    public void Sheathe(bool on)
    {
        if (person.Own == null) return;
        foreach (var (slot, id) in pieces) Swap(slot, id, on);
    }

    // One piece to its sheathed mount (on) or back into its hand; false if it has none or is already there.
    bool Swap(string slot, string id, bool on)
    {
        if (!held.TryGetValue(slot, out var old)) return false;
        if (on && IsInstanceValid(old) && old.Name.ToString().StartsWith("sheathed:")) return false;
        Node3D? now = on ? Arms.HoldSheathed(person, id, slot == "handslot.l") : Arms.Hold(person, id, BoneOf(slot));
        if (now == null) return false;
        (old.GetParent() as BoneAttachment3D ?? (Node)old).QueueFree();
        held[slot] = now;
        return true;
    }
    readonly System.Collections.Generic.HashSet<string> lookSheathed = new();

    // The seat each held piece had in its hand mount (Slide's base), and the point and axis its tilt turns it about
    // (the fist's fitted pocket and the palm's normal, in the mount's space; none for a piece without a pocket): re-read
    // when the mount is a new one (Sheathe swaps the mount node), so a sheath transform never gets cached.
    // A left piece without a fitted left pocket (the second axe) also keeps the seat a left tilt moves it onto (onPocket:
    // WeaponSockets.TiltPocketL, animation 58).
    readonly System.Collections.Generic.Dictionary<string, (Node3D piece, Transform3D seat, Vector3? pivot, Vector3 axis, Transform3D? onPocket)> seats = new();

    /// <summary>The piece in a hand slot sits this far along its own shaft (metres) from its seat, so the fist grips
    /// lower on it (animation 47: the arcanist's combat idle), turned `tilt` degrees in the fist about the palm's normal
    /// through the fitted pocket first (animation 48; a piece without a pocket only slides). The left fist (animation 58)
    /// turns about the mirrored normal (WeaponSockets.TiltAxisL) through its pocket (TiltPocketL): a piece with no fitted
    /// left pocket (the second axe) is eased from its plain mount onto the right's mirrored pocket by `pocket` (0..1, the
    /// clips' "grip_tilt_l" weight, eased as the tilt is). Does nothing while the piece is sheathed.</summary>
    public void Slide(string slot, float metres, float tilt = 0f, float pocket = 0f)
    {
        if (!held.TryGetValue(slot, out var mount) || !IsInstanceValid(mount) || !mount.Name.ToString().StartsWith(GripSlide.MountPrefix)) return;
        if (mount.GetChildCount() == 0 || mount.GetChild(0) is not Node3D piece) return;
        if (!seats.TryGetValue(slot, out var s) || s.piece != piece)
        {
            Vector3? pivot = null;
            var axis = Vector3.Right;
            Transform3D? onPocket = null;
            if (pieces.TryGetValue(slot, out var id) && Arms.All.TryGetValue(id, out var spec))
            {
                var kind = piece.HasMeta("kind") ? (WeaponKind)(int)piece.GetMeta("kind") : spec.Kind;
                var bone = BoneOf(slot);
                var pk = WeaponSockets.Pocket(kind, bone);
                var handAxis = Vector3.Right;
                if (bone == "hand_l" && !spec.Pistol)
                {
                    var al = WeaponSockets.TiltAxisL;
                    handAxis = new Vector3(al.X, al.Y, al.Z);
                    if (pk == null && WeaponSockets.TiltPocketL(kind) is { } tp)
                    {
                        pk = tp;
                        onPocket = Arms.SeatOn(id, bone, person.Own != null, tp.At, tp.Dir);
                    }
                }
                if (pk is { } pocketAt)
                {
                    var inv = mount.Transform.AffineInverse();
                    pivot = inv * new Vector3(pocketAt.At.X, pocketAt.At.Y, pocketAt.At.Z);
                    axis = (inv.Basis * handAxis).Normalized();
                }
            }
            seats[slot] = s = (piece, piece.Transform, pivot, axis, onPocket);
        }
        if (s.pivot == null) tilt = 0f;
        static System.Numerics.Vector3 N(Vector3 v) => new(v.X, v.Y, v.Z);
        static System.Numerics.Quaternion Q(Basis b) { var q = b.GetRotationQuaternion(); return new(q.X, q.Y, q.Z, q.W); }
        var seat = s.seat;
        if (s.onPocket is { } op && pocket != 0f)
        {
            var (bq, ba) = GripSlide.Blend(Q(seat.Basis), N(seat.Origin), Q(op.Basis), N(op.Origin), pocket);
            seat = new Transform3D(new Basis(new Quaternion(bq.X, bq.Y, bq.Z, bq.W)) * Basis.FromScale(seat.Basis.Scale), new Vector3(ba.X, ba.Y, ba.Z));
        }
        var (turn, at) = GripSlide.Apply(N(seat.Origin), N((seat.Basis * Vector3.Up).Normalized()), N(s.pivot ?? Vector3.Zero),
            N(s.axis), tilt, metres);
        piece.Transform = new Transform3D(new Basis(new Quaternion(turn.X, turn.Y, turn.Z, turn.W)) * seat.Basis, new Vector3(at.X, at.Y, at.Z));
        // SU_SLIDE_DUMP=1: the piece in its hand's space at rest (its seat) and as moved, for the clips' tools to check
        // keyed.py grip_pose / grip_pose_left against (animation 58).
        if (OS.HasEnvironment("SU_SLIDE_DUMP") && (tilt != 0f || metres != 0f || pocket != 0f))
        {
            static string T(Transform3D t) => $"{t.Basis.X.X:F6} {t.Basis.X.Y:F6} {t.Basis.X.Z:F6} {t.Basis.Y.X:F6} {t.Basis.Y.Y:F6} {t.Basis.Y.Z:F6} {t.Basis.Z.X:F6} {t.Basis.Z.Y:F6} {t.Basis.Z.Z:F6} {t.Origin.X:F6} {t.Origin.Y:F6} {t.Origin.Z:F6}";
            GD.Print($"SLIDE {slot} tilt {tilt:F3} slide {metres:F4} pocket {pocket:F3} | rest {T(mount.Transform * s.seat)} | now {T(mount.Transform * piece.Transform)}");
        }
    }

    // Her grip (slide, tilt) while this view plays her clips itself (not Driven: the pack's doll, a cinematic, a
    // figure in town), eased as PlayerView eases it.
    float ownSlide, ownTilt, ownSlideL, ownTiltL, ownPocketL;

    void OwnGrip(double delta, bool snap = false)
    {
        if (Driven || person.Own is not { } own || !held.ContainsKey("handslot.r")) return;
        var clip = person.Anim.CurrentAnimation.ToString();
        float s = own.GripSlide(clip), t = own.GripTilt(clip), sl = own.GripSlideL(clip), tl = own.GripTiltL(clip), pl = tl != 0 ? 1 : 0;
        if (s == 0 && t == 0 && ownSlide == 0 && ownTilt == 0 && sl == 0 && ownSlideL == 0 && tl == 0 && ownTiltL == 0 && ownPocketL == 0) return;
        ownSlide = snap ? s : GripSlide.Ease(ownSlide, s, (float)delta);
        ownTilt = snap ? t : GripSlide.Ease(ownTilt, t, (float)delta);
        ownSlideL = snap ? sl : GripSlide.Ease(ownSlideL, sl, (float)delta);
        ownTiltL = snap ? tl : GripSlide.Ease(ownTiltL, tl, (float)delta);
        ownPocketL = snap ? pl : GripSlide.Ease(ownPocketL, pl, (float)delta);
        Slide("handslot.r", ownSlide, ownTilt);
        Slide("handslot.l", ownSlideL, ownTiltL, ownPocketL);
    }

    public People.Person Person => person;

    public void Place(double x, double y, double z, double heading, bool visible)
    {
        Visible = visible;
        Position = new Vector3((float)x, (float)y, (float)z);
        Rotation = new Vector3(0, (float)heading, 0);
    }

    public void Loop(string clip, double blend = 0.3, double speed = 1)
    {
        loop = clip;
        loopSpeed = speed;
        // A held pose gives way to the loop.
        if (holding) { holding = false; actLeft = 0; person.Anim.Play(); }
        if (actLeft <= 0) PlayLoop(blend);
    }

    void PlayLoop(double blend)
    {
        var name = People.Clip(person, walking ? loopClip : loop, emptyHanded, emptyHanded ? "" : null);
        bool fresh = person.Anim.CurrentAnimation != name;
        person.Anim.Play(name, blend, (float)loopSpeed);
        Native(name);
        // A townsperson's first stand starts somewhere of its own in the loop (Play.TownStands.Phase), so the town
        // does not sway in step. Not hers or the hero's (their own clips).
        if (PhaseKey is string key && person.Own == null && !walking)
        {
            PhaseKey = null;
            var len = person.Anim.CurrentAnimationLength;
            if (len > 0.5) person.Anim.Seek(TownStands.Phase(key) * len, true);
        }
        // A package copy's stand and walk start at its own place in the loop (NpcDye: Person.Phase), so a row of one
        // package never moves in step.
        else if (fresh && person.Phase >= 0 && person.Own == null)
        {
            var len = person.Anim.CurrentAnimationLength;
            if (len > 0.5) person.Anim.Seek((person.Phase + (walking ? 0.37 : 0)) % 1.0 * len, true);
        }
    }

    /// <summary>Who or where this townsperson is (WorldScene.Person: their id and spot), for where their first
    /// stand starts in its loop; cleared once used.</summary>
    public string? PhaseKey;

    /// <summary>Her corrective layer stands down for her own clips (eased
    /// over the blend, so her pelvis does not jump).</summary>
    void Native(string name) => native = person.Own?.Owns(name) == true ? 1 : 0;
    float native;

    public void Act(string clip, double speed = 1) => Act(clip, speed, false);

    /// <summary>The flourish of her calling, as it is chosen (her own, or the
    /// library clip given for anyone else).</summary>
    public void Flourish(string fallback)
    {
        if (person.Own is { } own && own.Has($"{person.Calling}_show")) Act(own.Prefix + person.Calling + "_show");
        else Act(fallback);
        breakT = Mathf.Max(breakT, 6);
    }

    // Her idle breaks: standing a while, now and then she does something.
    double breakT = 8;
    readonly RandomNumberGenerator rng = new();

    void Fidget(double delta)
    {
        if (person.Own is not { } own || walking || holding || actLeft > 0 || Driven) return;
        // Only while she stands in her calling's idle.
        if (!People.Clip(person, loop).StartsWith(own.Prefix + "idle_")) return;
        breakT -= delta;
        if (breakT > 0) return;
        breakT = rng.RandfRange(9, 15);
        var brk = Sheath.Pick(People.Clip(person, loop).EndsWith("_town"), $"idle_{person.Calling}", "_break", own.Has);
        if (brk != null && own.Has(brk)) Act(own.Prefix + brk);
    }

    /// <summary>A gesture once; held on its last frame (a fall, getting up)
    /// until the next loop or gesture, or back to the loop.</summary>
    public void Act(string clip, double speed, bool hold)
    {
        var name = People.Clip(person, clip);
        var anim = person.Anim.GetAnimation(name);
        person.Anim.Play(name, 0.15, (float)speed);
        Native(name);
        holding = hold;
        actLeft = hold ? double.MaxValue : anim.Length / Mathf.Max(0.05, speed) - 0.2;
        bent = !hold && person.Own == null && FolkSpacing.BendsOver(clip);
    }
    // A townsperson's stoop (work at a stall, the well's bucket) is never walked in: Locomotion cuts it the moment
    // they move off (Play.FolkSpacing.BendsOver).
    bool bent;

    /// <summary>A clip played out and held at its end at once (a body lying where it fell).</summary>
    public void Pose(string clip)
    {
        var name = People.Clip(person, clip);
        var len = person.Anim.GetAnimation(name).Length;
        person.Anim.Play(name, 0);
        person.Anim.Seek(len - 0.02, true);
        person.Anim.Pause();
        Native(name);
        holding = true;
        actLeft = double.MaxValue;
    }

    /// <summary>Played by a cinematic's clock (CinemaDirector): its own animation
    /// clock, moved only by Advance, so the performance keeps to the timeline.</summary>
    public bool Cinema { get; private set; }

    /// <summary>Her double in a safe cinematic: her pieces at their sockets and every clip cued her town one.</summary>
    public bool Sheathed { get; set; }

    /// <summary>A clip from a moment in it, at a speed (0 holds that frame), blended in.</summary>
    public void Cue(string clip, double from, double speed, double blend)
    {
        Cinema = true;
        var name = People.Clip(person, clip, Sheathed);
        if (!person.Anim.HasAnimation(name)) { GD.PushWarning($"cinema: no clip {clip}"); return; }
        // A gesture (a nod, an exhale) is laid over what plays, not played in its place.
        if (person.Own is { } own && own.Owns(name) && own.Gesture(name[own.Prefix.Length..]) && person.Gestures is { } g)
        {
            g.Play(person.Anim.GetAnimation(name), speed, own.Holds(name[own.Prefix.Length..]));
            return;
        }
        person.Gestures?.Release();
        person.Anim.CallbackModeProcess = AnimationMixer.AnimationCallbackModeProcess.Manual;
        person.Anim.Play(name, blend);
        person.Anim.SpeedScale = (float)speed;
        person.Anim.Seek(from, true);
        Native(name);
        holding = true;
        actLeft = double.MaxValue;
    }

    /// <summary>The cinematic's clock moved on.</summary>
    public void Advance(double dt)
    {
        if (!Cinema) return;
        person.Anim.Advance(dt);
        // A clip played to its end (or stopped on a frame) holds a wax figure: breathe it.
        var a = person.Anim;
        bool held = !a.IsPlaying() || a.SpeedScale == 0
            || (a.HasAnimation(a.AssignedAnimation) && a.GetAnimation(a.AssignedAnimation) is { } clip
                && clip.LoopMode == Animation.LoopModeEnum.None && a.CurrentAnimationPosition >= clip.Length - 0.02);
        if (breath == null)
        {
            if (!held) return;
            breath = new CineBreath();
            person.Skeleton.AddChild(breath);
            // After the clip's gestures, before the head turns and her corrective joints.
            if (person.Gestures != null && person.Gestures.GetParent() == person.Skeleton)
                person.Skeleton.MoveChild(breath, person.Gestures.GetIndex() + 1);
        }
        breath.Want = held ? 1 : 0;
    }
    CineBreath? breath;

    public void Locomotion(double speed)
    {
        if (holding) return;
        // Standing, walking, jogging: the stride matched to the ground. Her
        // own run is played at the rate that keeps her feet planted.
        string run = People.Clip(person, RunClip);
        float natural = person.Own is { } own && own.Owns(run) ? own.Speed(run[own.Prefix.Length..]) * person.Root.Scale.X : 0;
        string want = speed < 0.3 ? "" : natural > 0 || speed >= 2.6 ? RunClip : WalkClip;
        bool was = walking;
        walking = want != "";
        if (walking && bent && actLeft > 0) { bent = false; actLeft = 0; was = false; }
        if (walking)
        {
            // A townsperson's own walk, at the rate that keeps their feet planted.
            string walk = People.Clip(person, WalkClip);
            float stride = walk.StartsWith(FolkClips.Prefix) ? FolkClips.Speed(walk) * person.Root.Scale.X : 0;
            loopSpeed = natural > 0 ? Mathf.Clamp(speed / natural, 0.4, 1.6)
                : want == WalkClip ? Mathf.Clamp(speed / (stride > 0 ? stride : 1.5), 0.6, 1.5) : Mathf.Clamp(speed / 3.6, 0.7, 1.5);
            if (want != loopClip || !was) { loopClip = want; if (actLeft <= 0) PlayLoop(0.25); }
            else if (actLeft <= 0) person.Anim.SpeedScale = (float)loopSpeed;
        }
        else if (was)
        {
            loopSpeed = 1;
            if (actLeft <= 0) PlayLoop(0.3);
        }
        if (loop == "") loop = "Idle";
    }

    /// <summary>Where the tip of what a hand holds is (world), or null (--cinebones: a blade's clearance).</summary>
    public Vector3? TipOf(string slot)
    {
        if (!held.TryGetValue(slot, out var m) || !IsInstanceValid(m)) return null;
        foreach (var c in m.GetChildren())
            if (c is Node3D w && w.HasMeta("tip")) return w.GlobalTransform * new Vector3(0, (float)w.GetMeta("tip"), 0);
        return null;
    }

    /// <summary>What the hands hold shown or not (creation's look screen: her face and hair, nothing in front of them).
    /// With them put away her hands are empty, so she stands as she does in a safe place with nothing in them (her
    /// calling's town stand: relaxed arms, open hands), not in the stand made around a hilt and a shield, whose
    /// clenched fists and held-out arms read as nobody stands (the owner, 26 October 2026, on this camp). Hers at the Look:
    /// pieces that ride at her waist are sheathed and shown (her town stand's hands rest on them: the Warden's fist on her
    /// sword's grip), pieces that ride on her back stay hidden so nothing covers her hair.</summary>
    public void ShowHeld(bool shown)
    {
        if (person.Own != null)
        {
            if (!shown)
            {
                foreach (var (slot, id) in pieces)
                    if (WeaponSockets.AtWaist(WeaponSockets.SocketOf(Arms.KindOf(id))) && Swap(slot, id, true)) lookSheathed.Add(slot);
            }
            else
            {
                foreach (var slot in lookSheathed) if (pieces.TryGetValue(slot, out var id)) Swap(slot, id, false);
                lookSheathed.Clear();
            }
        }
        foreach (var (slot, m) in held)
            if (IsInstanceValid(m)) m.Visible = shown || (person.Own != null && !shown && lookSheathed.Contains(slot));
        if (emptyHanded == !shown) return;
        emptyHanded = !shown;
        if (!walking && actLeft <= 0 && !holding) PlayLoop(0.4);
    }
    bool emptyHanded;

    public void Hold(string slot, string? pack, string? piece)
    {
        if (held.Remove(slot, out var old)) old.QueueFree();
        pieces.Remove(slot);
        if (piece == null) return;
        var bone = BoneOf(slot);
        if (Arms.All.ContainsKey(piece)) { held[slot] = Arms.Hold(person, piece, bone); pieces[slot] = piece; return; }
        // A package's left fist round a lit torch, the arm brought up to carry it (NpcTorchArm), the torch kept upright.
        if (piece == "torch_lit" && person.Package != null && slot == "handslot.l" && Carried(piece) is Node3D torch)
        {
            held[slot] = TorchFist(torch);
            return;
        }
        // The kits' small things (a torch, a bucket) as simple stand-ins
        // until the KayKit packs come over.
        if (Carried(piece) is Node3D thing)
        {
            var at = new BoneAttachment3D { BoneName = bone };
            person.Skeleton.AddChild(at);
            at.AddChild(thing);
            held[slot] = at;
        }
    }

    /// <summary>A light of its own in the held torch's flame (a shot's; Folk lights its walkers' torches itself).</summary>
    public void TorchLight()
    {
        if (!held.TryGetValue("handslot.l", out var at)) return;
        Node3D host = at;
        foreach (var c in at.GetChildren()) if (c is UprightNode u) host = u;
        // (at the flame itself, short and soft: a light above the head flattened his face to plaster at chest-up, judge r2)
        host.AddChild(new OmniLight3D { Position = new Vector3(0, TorchFlameY, 0), LightColor = new Color("#ffa050"), LightEnergy = 1.1f, OmniRange = 3.5f, ShadowEnabled = true });
    }

    /// <summary>The held torch's flame above its grip (the flame kit's card from 0.31, 0.26 tall at 0.55).</summary>
    public const float TorchFlameY = 0.40f;

    /// <summary>Where the flame of a torch held in a slot is in the world (Folk's patrol light follows it), or null.</summary>
    public (double X, double Y, double Z)? HeldAt(string slot)
    {
        if (!held.TryGetValue(slot, out var at) || !IsInstanceValid(at) || !at.IsInsideTree()) return null;
        Node3D host = at;
        foreach (var c in at.GetChildren()) if (c is UprightNode u) host = u;
        var p = host.GlobalTransform * new Vector3(0, TorchFlameY, 0);
        return (p.X, p.Y, p.Z);
    }

    Node3D TorchFist(Node3D torch)
    {
        var sk = person.Skeleton;
        if (sk.GetNodeOrNull<NpcTorchArm>("NpcTorchArm") == null)
        {
            var arm = new NpcTorchArm();
            sk.AddChild(arm);
            // (before HerJoints, so the twist and share bones follow the raised arm)
            if (sk.GetNodeOrNull("HerJoints") is Node hj) sk.MoveChild(arm, hj.GetIndex());
        }
        if (sk.GetNodeOrNull<NpcHands>("NpcHands") is { } hands) hands.FistL = true;
        var at = new BoneAttachment3D { BoneName = "hand_l" };
        sk.AddChild(at);
        // (the fist's pocket: three quarters of the way to the middle knuckle, a little to the palm's side)
        int mid = sk.FindBone("middle_01_l");
        var knuckle = mid >= 0 ? sk.GetBoneRest(mid).Origin : new Vector3(0, 0.1f, 0);
        var grip = new UprightNode { Size = person.Root.Scale.X, Position = knuckle * 0.72f + new Vector3(0, 0, knuckle.Length() * 0.35f) };
        at.AddChild(grip);
        grip.AddChild(torch);
        return at;
    }

    static Node3D? Carried(string piece)
    {
        var root = new Node3D();
        var wood = new StandardMaterial3D { AlbedoColor = new Color("#3a2a1e"), Roughness = 0.9f };
        switch (piece)
        {
            case "torch_lit":
            {
                // A tapered dark wood handle (0.5 m, gripped near its middle) and a charred wrapped head; the flame is the kit's.
                root.AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.026f, BottomRadius = 0.017f, Height = 0.5f, Material = wood }, Position = new Vector3(0, 0f, 0) });
                var char_ = new StandardMaterial3D { AlbedoColor = new Color("#1c1612"), Roughness = 1f };
                root.AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.021f, BottomRadius = 0.035f, Height = 0.12f, Material = char_ }, Position = new Vector3(0, 0.30f, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
                var ember = new StandardMaterial3D { AlbedoColor = new Color("#1c1612"), Roughness = 1f, EmissionEnabled = true, Emission = new Color("#8a2a08"), EmissionEnergyMultiplier = 0.35f };
                root.AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.0205f, BottomRadius = 0.025f, Height = 0.035f, Material = ember }, Position = new Vector3(0, 0.3425f, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
                FlameKit.Add(root, new Vector3(0, 0.31f, 0), FlameKind.Torch, scale: 0.55f, light: false);
                return root;
            }
            case "bucket_water":
            {
                var tin = new StandardMaterial3D { AlbedoColor = new Color("#6a5a48"), Roughness = 0.7f };
                root.AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.13f, BottomRadius = 0.1f, Height = 0.22f, Material = tin }, Position = new Vector3(0, -0.2f, 0) });
                return root;
            }
        }
        root.Free();
        return null;
    }

    public override void _Ready() => Settle();

    /* ------------------------------------------------- a townsperson's LOD -- */

    /// <summary>On screen (with room round it for its shadow, cast long at dusk): while it isn't, its clip is held
    /// still (no mixing, no skeleton to lay) and the time kept, and when it comes back the clip is moved on by
    /// that time first, so it stands where it would have been.</summary>
    VisibleOnScreenNotifier3D? seen;
    FolkShadow.Job? shadowJob;
    bool lodHeld;
    double lodHeldFor;
    AnimationMixer.AnimationCallbackModeProcess lodMode;
    static readonly bool LodOff = Args.Get("folk-lod") == "off";

    /// <summary>The town's people (walkers and those who stand): its clip held off screen, and its shadow one draw
    /// (FolkShadow). Not for her, nor anyone a cinematic plays.</summary>
    public void Lod()
    {
        BeginShadow();
        if (LodOff || seen != null) return;
        // (6 m round: the shadow of a person at the edge of the frame reaches in from about 4 m out with the sun low)
        seen = new VisibleOnScreenNotifier3D { Aabb = new Aabb(new Vector3(-6, -1, -6), new Vector3(12, 5, 12)) };
        seen.ScreenExited += LodHold;
        seen.ScreenEntered += LodResume;
        AddChild(seen);
    }

    /// <summary>Its one shadow begun (FolkShadow), here or on the worker that made it (WalkerView).</summary>
    public void BeginShadow() { if (!shadowBegun) { shadowBegun = true; shadowJob = FolkShadow.Begin(person); } }
    bool shadowBegun;

    void LodHold()
    {
        if (Cinema || Driven || lodHeld) return;
        lodHeld = true;
        lodHeldFor = 0;
        lodMode = person.Anim.CallbackModeProcess;
        person.Anim.CallbackModeProcess = AnimationMixer.AnimationCallbackModeProcess.Manual;
    }
    int lodFrames;

    void LodResume()
    {
        if (!lodHeld) return;
        lodHeld = false;
        if (Cinema) return;   // (a cinematic took it while away: its clock plays it now)
        person.Anim.CallbackModeProcess = lodMode;
        if (person.Anim.IsPlaying()) person.Anim.Advance(lodHeldFor);
    }

    /// <summary>Posed now, as it will be drawn. A figure added in the middle of a frame showed its
    /// bind pose (a T) for that frame, and her corrective layer eased in from nothing: the pack's
    /// doll did both on every refresh.</summary>
    public void Settle()
    {
        if (Driven || Cinema || !IsInsideTree()) return;
        if (person.Pose is HerPose hp) hp.Lower = hp.Upper = native;
        if (person.Anim.IsPlaying()) person.Anim.Advance(0);
        OwnGrip(0, snap: true);
    }

    public override void _Process(double delta)
    {
        if (shadowJob is { Done: true } sj) { shadowJob = null; FolkShadow.Finish(person, sj); }
        if (lodHeld) { if (Cinema || Driven) LodResume(); else lodHeldFor += delta; }
        // (made off screen: held from its third frame, once the notifier has had a look)
        else if (seen != null && lodFrames < 3 && ++lodFrames == 3 && !seen.IsOnScreen()) LodHold();
        if (person.Pose is HerPose hp && !Driven)
        {
            float k = 1 - Mathf.Exp(-12 * (float)delta);
            hp.Lower += (native - hp.Lower) * k;
            hp.Upper += (native - hp.Upper) * k;
        }
        OwnGrip(delta);
        if (Cinema) return;
        if (actLeft > 0 && !holding)
        {
            actLeft -= delta;
            if (actLeft <= 0) PlayLoop(0.25);
        }
        Fidget(delta);
    }

    // Explicit, so it does not shadow Godot's own Dispose().
    void INpcView.Dispose() => QueueFree();
}
