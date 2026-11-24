using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The den's painted set (den round 10, 15 Nov): paintings by an image model (tools/look/den_set.py: art/dungeon/den/set/)
/// laid by rule along the walkable edge and cast along the fixed play camera's view onto their proxies (the bank's surface
/// and the floor for the banks; a half-ellipsoid on the floor for a boulder), drawn by shaders/den_set.gdshader as the
/// painting times the room's light. The camera never turns in a dungeon, so a painting laid in its plane and cast along its
/// view shows exactly as painted, and every pixel sits at the depth of the ground it shows (she stands in front of the far
/// bank, behind the near bank's crest, on the roots spilled over the floor; nothing collides).
/// The rule: the room's edge by rays from its middle; each edge station classed by which way its bank faces (far: the bank
/// north of the floor, its face to the camera, B1/B1b; near: south, seen from above and behind, B2/B2b; left and right
/// walls, B3/B3R), runs of a class laid with modules end to end (2 m overlaps; a module over its neighbour shows only its
/// brightest masses at first, roots crossing roots, never a seam), the module's foot following the edge.
/// --den-set: 0 off (round 9), 1 the entry room only (the prototype gate), 2 every room (r10c: the default).
/// </summary>
public static partial class DungeonDress
{
    public static readonly int SetMode = (int)SurvivorUnchained.Args.Num("den-set", 2f);
    static readonly float SetScale = SurvivorUnchained.Args.Num("den-set-scale", 1f);
    static readonly float SetGain = SurvivorUnchained.Args.Num("den-set-gain", 0.85f);   // (r11 1.1 -> 1.0: lit tone 156 against 134)   // (r10d 1.25 -> 1.1: the lit root tops measured (166,122,100) against (134,95,73))
    static readonly float SetObjGain = SurvivorUnchained.Args.Num("den-set-obj-gain", 1f);
    static readonly float SetSat = SurvivorUnchained.Args.Num("den-set-sat", 0.5f);   // (r11 0.7 -> 0.5 with shade-hi 0.15: satShade .34 -> .18, cool 15 -> 25 %, as den_room.png)
    static readonly float SetBoulderScale = SurvivorUnchained.Args.Num("den-set-boulder", 1f);
    static readonly float SetCool = SurvivorUnchained.Args.Num("den-set-cool", 0.4f);   // (r13 1 -> 0.4 with shade-tint 1,.95,.85: the banks' darks h 233-331 (mauve) -> 7-17, lane E Banks band warm umber)   // (r10b) the paintings' shade to cool grey (den_set.gdshader shade_k)

    static readonly float SetRockGain = SurvivorUnchained.Args.Num("den-rock-gain", 0.45f);   // (den r13 rooms) the O1 boulders: their brightest 10 % at luminance <= 85
    static readonly float SetVary = SurvivorUnchained.Args.Num("den-set-vary", 1f);   // (den r14 objects, item 4) caps, mirror and turn on bone piles and logs
    static readonly float SetRockLit = SurvivorUnchained.Args.Num("den-rock-lit", 1f);   // (den r14 objects, item 3) open-floor boulders: round, lit, mossed (sheet O1r); 0 the r13 stones
    static readonly float SetRockBig = SurvivorUnchained.Args.Num("den-rock-big", 1.45f);   // their scale
    static readonly float SetRockGainLit = SurvivorUnchained.Args.Num("den-rock-gain-lit", 1f);
    // (den r15 A, R14 judge item 1: r14's O1r blurred O1 to a mip and painted a procedural top: 24 px blocks, no ink) O1r drawn
    // from its own sheet (tools/look/den_rocks.py: O1's stones at 2x in the target's value band, inked), no blur branch; 0 r14's
    static readonly float SetRockPaint = SurvivorUnchained.Args.Num("den-rock-paint", 1f);
    static readonly float SetRockDome = SurvivorUnchained.Args.Num("den-rock-dome", 0f);   // (den r15 G) plain O1 stones cast on their own dome over the floor, not the bank surface
    static readonly float SetRockLanePaint = SurvivorUnchained.Args.Num("den-rock-lanepaint", 0f);   // (den r15 G) the lane/alcove stones drawn from the painted round sheet O1r too
    static string? LaneRockKey => SetRockLanePaint > 0f && SetRockPaint > 0f && SetRockLit > 0f ? "O1r" : null;
    static readonly float SetRockNoCube = SurvivorUnchained.Args.Num("den-rock-nocube", 0f);   // (den r15 A) 1: plain O1 stones never the flat-topped block (PlaceSetObj). Off: a1 showed the s11 pale cube is not that piece (the cast over the bank's rise makes the cube)
    static readonly int SetLairCrowns = (int)SurvivorUnchained.Args.Num("den-lair-crowns", 2f);   // (den r18 lead, R17 item 4: 6-7 crowns carpeted the lairs; r17 3) (den r13 rooms) root-crowns (B6) a lair may hold (0: no cap)
    static int lairPits;   // (den r13 rooms) lair holes met so far
    static readonly float SetPitCells = SurvivorUnchained.Args.Num("den-pit-cells", 1f);   // (den r16 A, R15f item 1) the lair pits as glowing cracks in a dark pit (SetMat); 0: the r15 strokes
    static Vector3 setBossC;   // (r12) the lair's centre x, z and radius for the set's gloom (0: none), taken where the set is built
    internal static readonly float SetBossGloom = SurvivorUnchained.Args.Num("den-boss-gloom", 1.2f);
    static readonly float SetSpurLift = SurvivorUnchained.Args.Num("den-spur-lift", 1f);   // (den r16 G2, R15f item 11) the lair gloom taken off the set by its root spurs (DungeonGen.LairSpurs): spur banks as the rooms' banks (0: gloomed as the rim)
    static readonly Vector4[] setSpurSeg = new Vector4[16];
    static readonly float[] setSpurR = new float[16];

    static ShaderMaterial SetMat(string sheet, float gain)
    {
        // (r10d) the hole paintings (H1, H2) lie on the floor blended (their surround fades into it); the rest cut at alpha 0.5
        var mat = new ShaderMaterial { Shader = sheet[0] == 'H' ? setSoftShader : setShader };
        bool rockPaint = sheet == "O1r" && SetRockPaint > 0f;   // (den r15 A) the round boulders' own painted sheet
        mat.SetShaderParameter("paint_tex", GD.Load<Texture2D>(SetDir + (sheet == "O1r" && !rockPaint ? "O1" : sheet == "O1r" && SetRockFacets > 0f ? "O1rf" : sheet) + ".png"));   // (den r16 D: O1rf)
        if (rockPaint) gain *= SurvivorUnchained.Args.Num("den-rock-paint-gain", 1.5f);   // (a1: the stones Lp90 .25-.40, the target lit .45-.60)
        if (sheet == "O1r" && !rockPaint)
        {
            mat.SetShaderParameter("rock_k", SurvivorUnchained.Args.Num("den-rock-k", 1f));
            mat.SetShaderParameter("rock_lod", SurvivorUnchained.Args.Num("den-rock-lod", 2.2f));
            mat.SetShaderParameter("rock_lit", V3("den-rock-col", new Vector3(0.23f, 0.155f, 0.085f)));
            mat.SetShaderParameter("rock_moss", V3("den-rock-moss", new Vector3(0.1f, 0.13f, 0.04f)));
            mat.SetShaderParameter("rock_moss_k", SurvivorUnchained.Args.Num("den-rock-moss-k", 0.6f));
        }
        if (sheet == "B6" && SetRootK != 1f) gain *= SetRootK * SetRootK * SetRootK;
        mat.SetShaderParameter("gain", gain);
        mat.SetShaderParameter("sat", SetSat);
        mat.SetShaderParameter("shade_k", SetCool);
        mat.SetShaderParameter("dark_floor", SetDark);
        mat.SetShaderParameter("amb_floor", SetAmb);
        // (r11) the roots and shade read pink-mauve: the paintings' mids warmed (less blue), the shade's cool narrowed to the
        // deepest darks and turned blue-teal (den_room.png: warm brown in the light, cool only down in the hollows)
        mat.SetShaderParameter("tint", V3("den-set-tint", new Vector3(1f, 0.98f, 0.81f)));
        mat.SetShaderParameter("shade_tint", V3("den-set-shade-tint", DenShade.On ? new Vector3(0.8f, 0.78f, 1.4f) : new Vector3(1.0f, 0.95f, 0.85f)));
        mat.SetShaderParameter("shade_hi", SurvivorUnchained.Args.Num("den-set-shade-hi", 0.15f));
        // (den r15 helper D) the bone piles' shade warm umber (hue 40-60), not the grey-violet the judge measured (hue ~210, C .02)
        if (sheet == "O3") mat.SetShaderParameter("shade_tint", V3("den-bone-shade", new Vector3(1.0f, 0.80f, 0.55f)));
        // (den r14 corr, item 9) the camera-side banks (near class) are the frame's nearest roots: their lit tops read bleached
        // (seed-23 corridor L .45, room L .51 against den_room.png's foreground .33-.41): their highlights rolled off and warmed
        if (sheet == "O6") mat.SetShaderParameter("sat", SetSat * SurvivorUnchained.Args.Num("den-fur-sat", 1.1f));   // (den r16 W, R15f item 10) the fur reads pale grey (C <= .03), not pink or cream; (den r17 lead, R16 item 6: 0.35 -> 2) the O6 painting itself is warm grey now (S e6cebe99d), sat 1 keeps it (h 50 C .054)
        if (sheet == "O6") { mat.SetShaderParameter("tint", V3("den-fur-tint", new Vector3(1f, 0.97f, 0.72f))); mat.SetShaderParameter("shade_tint", V3("den-fur-shade", new Vector3(1f, 0.95f, 0.6f))); }   // (den r16 lead, R15f item 10) the set's warm tint made the fur cream in light (C .05-.09); neutral here
        if (sheet == "O2" && SetLogSat != 1f) mat.SetShaderParameter("sat", SetSat * SetLogSat);   // (den r16 D, R15f item 8)
        if (sheet == "O2" && SetLogTint != Vector3.One) mat.SetShaderParameter("tint", V3("den-set-tint", new Vector3(1f, 0.98f, 0.81f)) * SetLogTint);
        if (sheet is "B2" or "B2b") mat.SetShaderParameter("hi_roll", SurvivorUnchained.Args.Num("den-near-hi", 0.72f));
        if (sheet == "O9")   // (den r19 B, R18b item 2) the carcasses read red flesh with pale fur: the set's half saturation and warm tint left them pink-grey
        {
            mat.SetShaderParameter("sat", SurvivorUnchained.Args.Num("den-carc-sat", 1.0f));
            mat.SetShaderParameter("tint", V3("den-carc-tint", new Vector3(1.1f, 0.85f, 0.75f)));
        }
        if (sheet == "O5")
        {
            // (r12 judge: the seed-23 room's blood read magenta) the set's half saturation and its grey-violet shade turned the
            // painted blood pink-mauve: blood keeps its own red, a touch darker and browner
            // (den r19 B, R18b item 8) dark red, not salmon: the tint's lift off (1.45, 1.3, 1.1 -> 1.1, 0.85, 0.8), the set's half saturation up, less rust
            mat.SetShaderParameter("sat", SurvivorUnchained.Args.Num("den-blood-sat", 0.9f));
            mat.SetShaderParameter("tint", V3("den-blood-tint", new Vector3(1.1f, 0.85f, 0.8f)));
            mat.SetShaderParameter("blood_rust", SurvivorUnchained.Args.Num("den-blood-rust", 0.25f));   // (den r15 C) crimson h 15-22 into rust 33-37
            mat.SetShaderParameter("blood_dir", V3("den-blood-dir", new Vector3(1.5f, 0.9f, 0.45f)));
            mat.SetShaderParameter("shade_k", 0f);
        }
        if (rockPaint)   // (den r15 A) den_rocks.py paints O1r's hue and chroma in the target's band: the set's half saturation and warm tint off
        {
            mat.SetShaderParameter("sat", SurvivorUnchained.Args.Num("den-rock-sat", 1f));
            mat.SetShaderParameter("tint", V3("den-rock-tint", new Vector3(1f, 1f, 1f)));
        }
        mat.SetShaderParameter("occ_k", SetOcclude);   // (den r15 F, lane A judge) the occlusion cut-out round her: roots and banks nearer the camera fade to 20 % over her
        mat.SetShaderParameter("occ_a", SurvivorUnchained.Args.Num("den-occlude-a", 0.2f));
        mat.SetShaderParameter("bank_gloom", SetGloom);   // (den r13 corr) COLOR.b's depth gloom (bank modules only: objects carry 0)
        mat.SetShaderParameter("gloom_m", SetGloomM);
        mat.SetShaderParameter("boss_c", setBossC);   // (r12) the lair's gloom, as the floor's
        // (den r16 G2, R15f item 11) the root spurs run in to 9-14 m and read black (L50 .17) under the radial gloom:
        // the gloom comes off within 1-4 m of a spur, so its banks read as a room's (.25-.29); the rim banks keep their dark
        mat.SetShaderParameter("spur_seg", setSpurSeg);
        mat.SetShaderParameter("spur_r", setSpurR);
        mat.SetShaderParameter("spur_lift", SetSpurLift);
        mat.SetShaderParameter("boss_gloom", SetBossGloom);
        if (sheet == "O6") mat.SetShaderParameter("boss_gloom", SetBossGloom * SurvivorUnchained.Args.Num("den-fur-gloom", 0.6f));   // (den r19 BK2, R18b item 12) the lair gloom collapses a tuft to a grey and turns it blue (lilac, h 320-345): the fur takes 0.6 of it (and, same item, a warm grey-brown tint: h 60-80, C .02-.04) (--den-fur-gloom 1 = the old full gloom)
        mat.SetShaderParameter("mush_glow", SurvivorUnchained.Args.Num("den-mush-glow", 0.35f));   // (r12 judge) teal on the ground under the painted caps
        mat.SetShaderParameter("fungus_sat", SurvivorUnchained.Args.Num("den-fungus-sat", 0.4f));   // (den r14, lane E) the painted caps' cyan into its band
        if (sheet[0] == 'H')
        {
            mat.SetShaderParameter("pit_glow", SurvivorUnchained.Args.Num("den-pit-glow", 0.8f));
        mat.SetShaderParameter("pit_dark", SurvivorUnchained.Args.Num("den-pit-dark", 0.35f));
        mat.SetShaderParameter("pit_col", new Color(SurvivorUnchained.Args.Num("den-pit-r", 0.5f), SurvivorUnchained.Args.Num("den-pit-g", 0.8f), SurvivorUnchained.Args.Num("den-pit-b", 0.4f)));   // (den r13 rooms) less neon   // (r12) den_boss.png's green pits
            mat.SetShaderParameter("pit_net", SurvivorUnchained.Args.Num("den-pit-net", 0.6f));
            mat.SetShaderParameter("pit_floor", SurvivorUnchained.Args.Num("den-pit-floor", 0.3f));
            mat.SetShaderParameter("pit_sat",SurvivorUnchained.Args.Num("den-pit-sat", 0.3f));
            mat.SetShaderParameter("pit_halo", SurvivorUnchained.Args.Num("den-pit-halo", 0.14f));
            mat.SetShaderParameter("rim_in", SurvivorUnchained.Args.Num("den-hole-rim-in", 1.15f));
            mat.SetShaderParameter("rim_out", SurvivorUnchained.Args.Num("den-hole-rim-out", 1.45f));
            // (den r16 A, R15f item 1: hairy nests of green scribble) a lair pit as glowing cracks in a dark pit: a closed cell network of
            // dark plates (lit top edges), a thin lime core in a soft halo, a hard broken lip with an inner shadow, 2-3 cracks past the
            // rim (den_set.gdshaderinc pit_cells). --den-pit-cells 0: the r15 strokes on the painting
            mat.SetShaderParameter("pit_cells", SetPitCells);
            mat.SetShaderParameter("pit_cell_m", SurvivorUnchained.Args.Num("den-pit-cell", 1.0f));
            mat.SetShaderParameter("pit_cw", V3("den-pit-cw", new Vector3(0.045f, 0.18f, 0.75f))   /* (den r17 lead, p3a) .04,.17,.7 -> .045,.18,.75 */   /* (den r17 P) z now the share lit (r16 .3 lit 70 %); (r17 P2, R16 item 1) .03,.14,.6 -> .04,.17,.7: glow runs 2/6 px against den_boss 7/22 */);
            mat.SetShaderParameter("pit_core_c", V3("den-pit-core", new Vector3(0.2f, 0.25f, 0.18f))   /* (den r17 lead, p3a) core desaturated */   /* (den r17 P, R16 item 1) C x.75, luminance kept (r16 .18,.27,.14) */);
            mat.SetShaderParameter("pit_halo_c", V3("den-pit-halo-c", new Vector3(0.15f, 0.2f, 0.125f))   /* (den r17 lead, p3a) */   /* (den r17 P2) was .1,.145,.085: wider, less saturated (q7c at .2,.3,.17: 11 % of the pit, C .097) */);
            mat.SetShaderParameter("pit_plate_c", V3("den-pit-plate", new Vector3(0.04f, 0.04f, 0.036f))   /* (den r17 lead, p3a: P2 plates .03 high) .05 -> .04 */);
            mat.SetShaderParameter("pit_lipw", V3("den-pit-lip", new Vector3(0.08f, 0.12f, 0.4f)));
            mat.SetShaderParameter("pit_ray", V3("den-pit-ray", new Vector3(1f, 0.7f, 1.3f)));
            // (den r16 A2, R15f item 1: a raised turtle shell) the pit sunken: depth (m; 0 flat), the near lip's shadow reach, the
            // plates' brightness at the middle; H1 (the lair's walkable hollows) shallower than H2 (holes); the wall's earth face
            mat.SetShaderParameter("pit_deep", sheet == "H1" ? V3("den-pit-deep1", new Vector3(0.35f, 1.6f, 0.65f)) : V3("den-pit-deep", new Vector3(1.1f, 1.6f, 0.9f)));
            mat.SetShaderParameter("pit_wall_c", V3("den-pit-wall", new Vector3(0.17f, 0.12f, 0.078f)));   // (den r17 P) the far wall a lit earth band (r16 .06,.042,.028); (r17 P2) .12,.085,.055 -> .17,.12,.078 (q7c: brink .34 on floor .42, den_boss .39 on .47)
            mat.SetShaderParameter("pit_cast_min", SurvivorUnchained.Args.Num("den-pit-cast", 0.5f));
            // (den r17 P2, R16 item 1: still a dome) the pit a bowl: no spot/omni light inside, the far wall lit at the brink to
            // --den-pit-bw x at its foot, the floor y at the far foot within z metres; smooth lip, no crumbs (den_set pit_bowl). 0: as r17 P
            mat.SetShaderParameter("pit_bowl", SurvivorUnchained.Args.Num("den-pit-bowl", 1f));
            mat.SetShaderParameter("pit_bw", V3("den-pit-bw", new Vector3(0.35f, 0.55f, 0.5f)));
            // (den r18 P4, R17 items 1, 5) --den-pit-v2 1: veins not plates, a smooth far wall, the near lip's shade, no shader root wires (den_set pit_v2); 0: r17
            mat.SetShaderParameter("pit_v2", SurvivorUnchained.Args.Num("den-pit-v2", 1f));
            var pv = V3("den-pit-vein", new Vector3(0.06f, 0.15f, 0.55f));
            mat.SetShaderParameter("pit_vein", new Vector4(pv.X, pv.Y, pv.Z, SurvivorUnchained.Args.Num("den-pit-branch", 0.35f)));
            mat.SetShaderParameter("pit_wg", V3("den-pit-wg", new Vector3(1.4f, 0.45f, 0.8f)));
            mat.SetShaderParameter("pit_near", new Vector2(SurvivorUnchained.Args.Num("den-pit-near", 0.7f), SurvivorUnchained.Args.Num("den-pit-near-m", 0.9f)));
            mat.SetShaderParameter("pit_self", new Vector2(SurvivorUnchained.Args.Num("den-pit-self-alb", 1f), SurvivorUnchained.Args.Num("den-pit-self", 0f)));
            // (den r18 P5, R17 items 1, 5) H3, the painted lair pits (PlaceSetHole, --den-pit-paint): no procedural pit over the painting;
            // its lime veins emit --den-pit-paint-k x their colour (--den-pit-paint-alb of their albedo off; lime from lo to hi, G over
            // max(R, B) linear), a spot's or omni's light kept at --den-pit-paint-pt inside the lip (the painting carries its own light)
            if (sheet == "H3")
            {
                mat.SetShaderParameter("pit_cells", 0f);
                mat.SetShaderParameter("pit_paint", new Vector4(SurvivorUnchained.Args.Num("den-pit-paint-k", 1.7f), SurvivorUnchained.Args.Num("den-pit-paint-alb", 1f), SurvivorUnchained.Args.Num("den-pit-paint-lo", 0.02f), SurvivorUnchained.Args.Num("den-pit-paint-hi", 0.12f)));
                mat.SetShaderParameter("pit_paint_pt", SurvivorUnchained.Args.Num("den-pit-paint-pt", 0f));
                // (den r18 P5, p8a: glow 1.7 % of the s11 main box against 8-12, the far wall L .20-.22 against .40) the veins' bleed
                // (--den-pit-bleed gain, mip lod, lime-ness full; 0 off) and the painting's light x --den-pit-paint-gain
                var pb = V3("den-pit-bleed", new Vector3(3.5f, 6f, 0.019f));   // (den r19 V2: 3 -> 3.5, .03 -> .019, c .055,.085,.042 -> .04,.062,.032, cmax 0 -> .06, cap .1 -> .06: s11 L p50 .50 C90 .089 share .79, s23 .50/.088/.61) (den r19 V, R18b item 1: veins pastel, L p50 .63 -> .52, C90 .115 -> .097) a wide dim bleed (r18 1.2,4.5,.06), cap .35 -> .1, paint-alb .8 -> 1
                mat.SetShaderParameter("pit_bleed", new Vector4(pb.X, pb.Y, pb.Z, 0f));
                mat.SetShaderParameter("pit_cmax", SurvivorUnchained.Args.Num("den-pit-cmax", SurvivorUnchained.Args.Num("den-pit-lines", 1f) > 0f ? 0.0375f : 0.06f));   // (den r19 lead, judge 7: the lines take .0375, s19m)   // (den r19 V2, R18b item 1) hard OKLab chroma clamp on the veins' emissive and bleed (0 off)
                // (den r19 S, R19 judge item 1: the pits inverted, the bleed lit the plates mid-green, the cracks dark) --den-pit-lines 1: the
                // veins' light from H3_vein.png (den_set.py veins, the painting's own lime lines): --den-pit-line-core x its cores, plus
                // --den-pit-line-glow x (--den-pit-line-w x its narrow glow + y its wide one), the cores' albedo off by z; no lime
                // emission and no bleed, so the plates stay dark (den_set pit_lines). 0: the lime and bleed path (b637960e8's look)
                mat.SetShaderParameter("pit_lines", SurvivorUnchained.Args.Num("den-pit-lines", 1f));   // (den r19 lead) default 1: judge 7 (R19v) PASS on its J14 gate at s19m (cmax .0375, core .145/.16/.12, w .3/2.3/1); 0 = b637960e8
                mat.SetShaderParameter("pit_vein_tex", GD.Load<Texture2D>(SetDir + "H3_vein.png"));
                mat.SetShaderParameter("pit_line_core", V3("den-pit-line-core", new Vector3(0.145f, 0.16f, 0.12f)));   // s19m (s19f .17/.19/.14)
                mat.SetShaderParameter("pit_line_glow", V3("den-pit-line-glow", new Vector3(0.031f, 0.06f, 0.02f)));
                mat.SetShaderParameter("pit_line_w", V3("den-pit-line-w", new Vector3(0.3f, 2.3f, 1f)));   // s19m (s19f 2.4)
                // (den r19 V2, R18b item 6) the crumb ring's gaps (half-width rad, the blurred alpha kept above: from, to; 0 off) and the edge's darker falloff (albedo off, alpha lod; 0 off)
                mat.SetShaderParameter("pit_gaps", V3("den-pit-gaps", new Vector3(0.22f, 0.7f, 0.95f)));
                mat.SetShaderParameter("pit_fall", new Vector2(SurvivorUnchained.Args.Num("den-pit-fall", 0.45f), SurvivorUnchained.Args.Num("den-pit-fall-lod", 4f)));
                mat.SetShaderParameter("pit_bleed_c", V3("den-pit-bleed-c", new Vector3(0.04f, 0.062f, 0.032f)));
                // (den r18 lead, R18 judge item 1: the veins neon, glow C50 .150 -> .076 at v9 j, den_boss .073; r18 judged: sat 1, cap 0, k 1.2, alb .5, hi .25, bleed .6/3.5 c .16,.4,.06) --den-pit-sat (saturation kept, 1 = as judged) and --den-pit-cap
                // (the veins' emission luminance cap, linear; 0 off)
                mat.SetShaderParameter("pit_look", new Vector2(SurvivorUnchained.Args.Num("den-pit-sat", 0.15f), SurvivorUnchained.Args.Num("den-pit-cap", 0.06f)));
                // (den r18 lead, R18 judge item 5: the rims stickers) --den-pit-rim-dark (the painting darkened toward its fade),
                // --den-pit-rim-lilac (the lilac fringe's saturation out), the fade itself from --den-pit-rim-in to -out lip radii (H3 only)
                mat.SetShaderParameter("pit_rim", new Vector2(SurvivorUnchained.Args.Num("den-pit-rim-dark", 0.15f), SurvivorUnchained.Args.Num("den-pit-rim-lilac", 1f)));
                mat.SetShaderParameter("pit_feather", new Vector3(SurvivorUnchained.Args.Num("den-pit-feather", 3f), SurvivorUnchained.Args.Num("den-pit-feather-lo", 0.6f), SurvivorUnchained.Args.Num("den-pit-feather-hi", 1.0f)));   // (den r18 lead, R18 item 5) the painting's edge eroded and feathered (alpha at this mip; 0 off)
                mat.SetShaderParameter("rim_in", SurvivorUnchained.Args.Num("den-pit-rim-in", 1.0f));
                mat.SetShaderParameter("rim_out", SurvivorUnchained.Args.Num("den-pit-rim-out", 1.6f));
                mat.SetShaderParameter("gain", gain * SurvivorUnchained.Args.Num("den-pit-paint-gain", 1.4f));
            }
        }
        return mat;
    }
    internal static Vector3 V3(string flag, Vector3 dflt)
    {
        if (SurvivorUnchained.Args.Get(flag) is string t && t.Split(',') is { Length: 3 } p)
        {
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            return new Vector3(float.Parse(p[0], ci), float.Parse(p[1], ci), float.Parse(p[2], ci));
        }
        return dflt;
    }
    const string SetDir = "res://art/dungeon/den/set/";
    // the play camera's basis in a dungeon (it never turns: it looks north at the map's pitch, MapRun.CamPitch 62; r10c: it
    // was cast at 56, the road's, so every painting drew 6% tall on the floor and its raised parts sank)
    static readonly float CamPitchR = Mathf.DegToRad((float)SurvivorUnchained.Play.Zones.MapRun.CamPitch);
    static readonly Vector3 CamUp = new(0f, Mathf.Cos(CamPitchR), -Mathf.Sin(CamPitchR)), CamView = new(0f, -Mathf.Sin(CamPitchR), -Mathf.Cos(CamPitchR));
    // (den r16 W) 0 now: the second variants B3b/B3Rb replace the mirror (R15f item 3: its flat clearing showed as a blurred patch)
    static readonly float SetRowMirror = SurvivorUnchained.Args.Num("den-set-rowmirror", 0f);   // (den r15 lead, judge item 7) a side wall's odd rows behind lay the other wall's card mirrored; 0: its own card (the s11 corridor's duplicate rock)
    static readonly float SetRowJit = SurvivorUnchained.Args.Num("den-set-row-jit", 2.5f);   // (r13) metres a row behind's depth varies by module
    static readonly int SetRows = (int)SurvivorUnchained.Args.Num("den-set-rows", 3f);       // (r10c) side walls: rows of modules deeper in the bank
    static readonly float SetCorners = SurvivorUnchained.Args.Num("den-set-corners", 0f);    // (r10c) B4/B4R_2 where a far run meets a wall's (r11 1 -> 0: the corner's arm drew a straight seam and a dark band across the room's top, c_p13)
    static readonly float SetSpills = SurvivorUnchained.Args.Num("den-set-spills", 1f);      // (r10c) B6 spills on the floor at the banks' feet and pits
    static readonly float SetDark = SurvivorUnchained.Args.Num("den-set-dark", 0.02f); // (r11 0.008 -> 0.02)      // (r10c) the paintings' darks lit at least this (cool)
    static readonly float SetAmb = SurvivorUnchained.Args.Num("den-set-amb", 0.25f); // (r11 0.2 -> 0.25)        // (r10c) and at least this share of their painted value
    // (r10c) the objects in one mesh per sheet (they were a node each: ~137 draws) and the boulders' shadow hulls in one
    static readonly Dictionary<string, SetBuf> objBufs = new();
    static readonly List<Transform3D> hulls = new();

    sealed record SetBank(string Name, string Kind, Vector2 Metres, float FootV, float FootU, bool Mirror = false);
    sealed record SetPiece(string Sheet, Rect2 Uv, Vector2 Metres, float FootV, Vector4 Mouth);
    sealed class SetBuf
    {
        public readonly List<Vector3> V = new(), N = new();
        public readonly List<Vector2> U = new();
        public readonly List<Vector2> U2 = new();   // (den r16 A) the hole cards' floor offset from the pit's centre (UV2; empty elsewhere)
        public readonly List<Color> C = new();
        public readonly List<int> I = new();
    }

    static List<SetBank>? setBanks;
    static Dictionary<string, List<SetPiece>>? setSheets;
    static (float X, float Z, float R, string Kind) setRoom;
    static Shader? setShader, setSoftShader;
    static readonly float SetHoles = SurvivorUnchained.Args.Num("den-set-holes", 1f);   // (r10d) H2 over the pits, H1 over the hollows
    static readonly float SetOpenK = SurvivorUnchained.Args.Num("den-set-open", 1f);    // (r10d) things in the rooms' open floor
    static readonly float SetDrifts = SurvivorUnchained.Args.Num("den-set-drifts", 1f);   // (r11) bone drifts (O4) at the far banks' feet: their scale (0 off)
    static readonly float SetStretch = SurvivorUnchained.Args.Num("den-set-stretch", 4f);  // (r11) a module cell cast longer than this many cells is dropped (0 keeps all)
    static readonly float SetBackRow = SurvivorUnchained.Args.Num("den-set-backrow", 2f);  // (r11) a far run's row behind: 0 none, 1 whole, 2 past the run's ends only
    static readonly Dictionary<long, float> surfCache = new();

    static bool LoadSet()
    {
        if (setBanks != null) return setBanks.Count > 0;
        setBanks = new(); setSheets = new();
        if (!FileAccess.FileExists(SetDir + "set.json")) return false;
        using var doc = JsonDocument.Parse(FileAccess.GetFileAsString(SetDir + "set.json"));
        var r = doc.RootElement;
        foreach (var b in r.GetProperty("banks").EnumerateArray())
        {
            var m = b.GetProperty("metres");
            setBanks.Add(new SetBank(b.GetProperty("name").GetString()!, b.GetProperty("kind").GetString()!, new Vector2(m[0].GetSingle(), m[1].GetSingle()),
                b.TryGetProperty("foot_v", out var fv) ? fv.GetSingle() : 1f, b.TryGetProperty("foot_u", out var fu) ? fu.GetSingle() : 0f));
        }
        foreach (var s in r.GetProperty("sheets").EnumerateArray())
        {
            string name = s.GetProperty("name").GetString()!;
            var px = s.GetProperty("px");
            float aw = px[0].GetSingle(), ah = px[1].GetSingle();
            var list = new List<SetPiece>();
            foreach (var p in s.GetProperty("pieces").EnumerateArray())
            {
                var rc = p.GetProperty("rect"); var m = p.GetProperty("metres");
                list.Add(new SetPiece(name, new Rect2(rc[0].GetSingle() / aw, rc[1].GetSingle() / ah, rc[2].GetSingle() / aw, rc[3].GetSingle() / ah),
                    new Vector2(m[0].GetSingle(), m[1].GetSingle()), p.GetProperty("foot_v").GetSingle(),
                    p.TryGetProperty("mouth", out var mo) ? new Vector4(mo[0].GetSingle(), mo[1].GetSingle(), mo[2].GetSingle(), mo[3].GetSingle()) : Vector4.Zero));
                if (p.TryGetProperty("leaf", out _)) setLeaves.Add(list[^1]);   // (den r16 W, R15f item 10) O6's dry leaf drifts, flagged by the build
            }
            setSheets[name] = list;
        }
        setShader = GD.Load<Shader>("res://shaders/den_set.gdshader");
        setSoftShader = GD.Load<Shader>("res://shaders/den_set_soft.gdshader");
        return setBanks.Count > 0;
    }

    /// <summary>True where the painted set dresses the den (mode 1: the entry room and its banks; mode 2: everywhere).</summary>
    static bool SetIn(float x, float zz) =>
        SetMode >= 2 || (SetMode == 1 && new Vector2(x - setRoom.X, zz - setRoom.Z).Length() < setRoom.R + 9f);

    /// <summary>Where the set dresses, for the mound's shader (dungeon_wall.gdshader set_area): the prototype room's x, z and
    /// radius; w the mode (0 off, 1 that room, 2 everywhere).</summary>
    public static Vector4 SetArea(ZoneData z)
    {
        if (SetMode <= 0 || z.DungeonTheme != "den" || z.Rooms.Count == 0) return Vector4.Zero;
        var r = z.Rooms[0];
        foreach (var q in z.Rooms) if (q.Kind == "Start") { r = q; break; }
        return new Vector4(r.X, r.Z, r.R, SetMode >= 2 ? 2f : 1f);
    }

    static void PickSetRoom(ZoneData z)
    {
        setRoom = z.Rooms[0];
        foreach (var r in z.Rooms) if (r.Kind == "Start") { setRoom = r; break; }
        setLayer = 0; setCov.Clear(); surfCache.Clear(); foreach (var d in smCache) d.Clear(); objBufs.Clear(); hulls.Clear();
        SurfGrid(z);
    }

    // (lane K, 19 Nov: the owner's "god the den load time is insane": the den took 61 s cold and 91 s from the Verge, 47 s of
    // it in SurfBank's five dictionaries and the closures each call made) The same lazily filled lattices, held in flat
    // arrays over the map and 16 m round it (NaN: not yet worked out). Every value is worked out as before, in the same
    // order of sums, so the set is laid exactly as it was; a lattice point past the arrays takes the dictionaries.
    const float SurfQ = 0.25f;
    const int SurfPad = 64;
    static float[][] surfGrid = System.Array.Empty<float[]>();
    static int surfN, surfO;

    static void SurfGrid(ZoneData z)
    {
        int n = 2 * (Mathf.CeilToInt(z.Half / SurfQ) + SurfPad) + 1;
        if (surfGrid.Length != 5 || surfN != n) { surfN = n; surfGrid = new float[5][]; for (int k = 0; k < 5; k++) surfGrid[k] = new float[n * n]; }
        surfO = Mathf.CeilToInt(z.Half / SurfQ) + SurfPad;
        foreach (var g in surfGrid) System.Array.Fill(g, float.NaN);
    }

    /// <summary>Lattice (i, j)'s cell in the flat arrays, or -1 past them.</summary>
    static int SurfCell(int i, int j)
    {
        int a = i + surfO, b = j + surfO;
        return (uint)a < (uint)surfN && (uint)b < (uint)surfN ? a * surfN + b : -1;
    }

    static float SurfRaw(Ctx c, int i, int j)
    {
        int cell = SurfCell(i, j);
        if (cell >= 0 && !float.IsNaN(surfGrid[0][cell])) return surfGrid[0][cell];
        long k = ((long)i << 32) ^ (uint)j;
        if (cell < 0 && surfCache.TryGetValue(k, out float v)) return v;
        float px = i * SurfQ, pz = j * SurfQ;
        float s = -Wall(c, px, pz);
        float bank = SetProxy > 0f ? DungeonWalls.BankHoldY(c.Z, px, pz) : DungeonWalls.BankY(c.Z, px, pz);
        v = Mathf.Max(H(c, px, pz), bank + 0.3f * SetSm(0.05f, 0.6f, s));
        if (cell >= 0) surfGrid[0][cell] = v; else surfCache[k] = v;
        return v;
    }

    // The four blur passes (den r12): 1 Bz over the raw, 2 Bx over 1, 3 Bz over 2, 4 Bx over 3 (smCache[0..3] as before).
    static float SurfPass(Ctx c, int pass, int i, int j, int r)
    {
        if (pass == 0) return SurfRaw(c, i, j);
        int cell = SurfCell(i, j);
        var grid = surfGrid[pass];
        if (cell >= 0 && !float.IsNaN(grid[cell])) return grid[cell];
        long k = ((long)i << 32) ^ (uint)j;
        var cache = smCache[pass - 1];
        if (cell < 0 && cache.TryGetValue(k, out float v)) return v;
        float acc = 0f;
        bool alongZ = pass == 1 || pass == 3;
        for (int d = -r; d <= r; d++) acc += alongZ ? SurfPass(c, pass - 1, i, j + d, r) : SurfPass(c, pass - 1, i + d, j, r);
        v = acc / (2 * r + 1);
        if (cell >= 0) grid[cell] = v; else cache[k] = v;
        return v;
    }

    static float SetSm(float a, float b, float x) { float t = Mathf.Clamp((x - a) / (b - a), 0f, 1f); return t * t * (3 - 2 * t); }

    // The banks' proxy: the floor, and over the bank its surface (DungeonWalls' profile) raised 0.3 m clear of the mesh's
    // lumps, cached on a 0.25 m lattice and read bilinear.
    static float SurfBank(Ctx c, float x, float zz)
    {
        const float q = SurfQ;
        float fx = x / q, fz = zz / q;
        int ix = Mathf.FloorToInt(fx), iz = Mathf.FloorToInt(fz);
        float tx = fx - ix, tz = fz - iz;
        // (den r12) the proxy box-blurred twice over +-SetSmooth metres (separable): no crease left for a card to span
        int r = SetProxy > 0f ? Mathf.RoundToInt(SetSmooth / q) : 0;
        int top = r <= 0 ? 0 : 4;
        if (surfGrid.Length != 5) SurfGrid(c.Z);
        return Mathf.Lerp(Mathf.Lerp(SurfPass(c, top, ix, iz, r), SurfPass(c, top, ix + 1, iz, r), tx), Mathf.Lerp(SurfPass(c, top, ix, iz + 1, r), SurfPass(c, top, ix + 1, iz + 1, r), tx), tz);
    }
    static readonly float SetLiftAdd = SurvivorUnchained.Args.Num("den-set-lift", 0f);   // (r12 diagnosis) every bank card pulled this much more toward the camera
    static readonly float SetKeepAll = SurvivorUnchained.Args.Num("den-set-keepall", 0f);   // (r12 diagnosis)
    static readonly float SetLog = SurvivorUnchained.Args.Num("den-set-log", 0f);   // (r13 diagnosis) every ring's runs printed
    static readonly string[]? SetOnly = SurvivorUnchained.Args.Get("den-set-only")?.Split(',');   // (r13 diagnosis) only these sheets drawn (B3,B3R,...)
    static int setLayer;
    static readonly float SetLairWant = SurvivorUnchained.Args.Num("den-lair-want", 70f), SetLairRing = SurvivorUnchained.Args.Num("den-lair-ring", 13f);   // (r12) the lair's open pieces and their ring (3 m + this)
    static readonly float SetEdgeWave = SurvivorUnchained.Args.Num("den-set-wave", 0f);   // (r12) metres
    static readonly float SetBends = SurvivorUnchained.Args.Num("den-set-bends", 0f);
    static readonly float SetFootFade = SurvivorUnchained.Args.Num("den-set-footfade", 1f);   // (r12) a bank card's floor-side border fades to its bright masses
    static readonly float SetRagged = SurvivorUnchained.Args.Num("den-set-ragged", 1f);   // (r14) metres a module's border cut wanders in (0: its straight rectangle)
    static readonly float SetRaggedEnds = SurvivorUnchained.Args.Num("den-set-ragged-ends", 0.6f);   // (den r13 corr) a module's unfaded end cut ragged by this share of SetRagged (0: straight)
    static readonly float SetGloom = SurvivorUnchained.Args.Num("den-set-gloom", 0f);   // (den r13 corr) corridor banks' roots darken with depth into the bank (0 off; 0.8 tried, k2_corr: card-space depth disagrees between classes, so a near module gloomed over a lit side one drew hard dark wedges: it needs a world depth field that does not saturate)
    static readonly Vector2 SetGloomM = new(SurvivorUnchained.Args.Num("den-set-gloom-a", 2.5f), SurvivorUnchained.Args.Num("den-set-gloom-b", 6.5f));   // metres in: from, full
    static readonly float SetLayerStep =SurvivorUnchained.Args.Num("den-set-layer", 0.04f);   // (r12) metres between modules' depth layers
    static readonly Dictionary<long, float>[] smCache = { new(), new(), new(), new() };
    static readonly float SetProxy = SurvivorUnchained.Args.Num("den-set-proxy", 1f);    // (r12) 0: the bank's own profile (crest and fall); 1: its rise held at the crest, smoothed
    static readonly float SetSmooth = SurvivorUnchained.Args.Num("den-set-smooth", 1.25f); // (r12) the proxy's blur half-width, metres (twice, box)

    /// <summary>The point where the view ray through p (any point on it) meets the surface: marched down from the height top.</summary>
    static Vector3 SetCast(Vector3 p, System.Func<float, float, float> surf, float top)
    {
        var o = p + CamView * ((top - p.Y) / CamView.Y);
        const float stepT = 0.2f;
        for (int i = 0; i < 600; i++)
        {
            var q = o + CamView * (i * stepT);
            if (q.Y > surf(q.X, q.Z)) continue;
            float lo = Mathf.Max(0f, (i - 1) * stepT), hi = i * stepT;
            for (int b = 0; b < 8; b++)
            {
                float m = 0.5f * (lo + hi);
                var qm = o + CamView * m;
                if (qm.Y <= surf(qm.X, qm.Z)) hi = m; else lo = m;
            }
            return o + CamView * hi;
        }
        return o + CamView * (600 * stepT);
    }

    static int SetClassOf(float th, int cls) => cls switch
    {
        0 => Mathf.Abs(th) <= 50f ? 1 : 0,               // far: the bank north of the floor, its face to the camera
        1 => th >= 40f && th <= 140f ? 1 : 0,            // right wall (east of the floor)
        2 => Mathf.Abs(th) >= 130f ? 1 : 0,              // near: south, seen from above and behind
        _ => th <= -40f && th >= -140f ? 1 : 0,          // left wall (west)
    };

    static void DenSet(Ctx c)
    {
        if (!LoadSet()) { GD.Print("DenSet: no set.json"); return; }
        var bufs = new Dictionary<string, SetBuf>();
        var rooms = new List<(float X, float Z, float R, string Kind)>();
        if (SetMode >= 2) { foreach (var r in c.Z.Rooms) if (r.Kind != "Bend" || SetBends > 0f) rooms.Add(r); }   // (r12 --den-set-bends: the corridors' bends ring too)
        else rooms.Add(setRoom);
        int modules = 0, runs = 0, corners = 0, spills = 0;
        int ri = 0;
        foreach (var r in rooms)
        {
            ri++;
            // the room's edge: a ray from its middle every half degree to the first wall (pits are not walls)
            const int n = 720;
            var P = new Vector3[n]; var th = new float[n]; var open = new bool[n];
            for (int k = 0; k < n; k++)
            {
                float a = k * Mathf.Tau / n;
                var d = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                float t = 0.5f, lim = r.R + 8f;
                while (t < lim && Wall(c, r.X + d.X * t, r.Z + d.Y * t) >= 0f) t += 0.1f;
                if (t >= lim) { open[k] = true; continue; }
                float lo = t - 0.1f, hi = t;
                for (int b = 0; b < 10; b++) { float m = 0.5f * (lo + hi); if (Wall(c, r.X + d.X * m, r.Z + d.Y * m) < 0f) hi = m; else lo = m; }
                float x = r.X + d.X * lo, zz = r.Z + d.Y * lo;
                P[k] = new Vector3(x, H(c, x, zz), zz);
            }
            // outward normals smoothed over +-2 m of edge, then the class angle (0 north, 90 east, 180 south)
            for (int k = 0; k < n; k++)
            {
                if (open[k]) continue;
                var g = Vector2.Zero;
                for (int j = -6; j <= 6; j++)
                {
                    int kk = (k + j + n) % n;
                    if (open[kk]) continue;
                    var p = P[kk];
                    float gx = Wall(c, p.X + 0.3f, p.Z) - Wall(c, p.X - 0.3f, p.Z), gz = Wall(c, p.X, p.Z + 0.3f) - Wall(c, p.X, p.Z - 0.3f);
                    g += new Vector2(gx, gz);
                }
                var o = -g.Normalized();
                th[k] = Mathf.RadToDeg(Mathf.Atan2(o.X, -o.Y));
            }
            float top = H(c, r.X, r.Z) + 14f;
            var ends = new List<(int cls, List<Vector3> pts)>();
            for (int cls = 0; cls < 4; cls++)
            {
                // runs of the class round the ring (cut at openings and jumps of the edge)
                int start = -1;
                for (int k = 0; k < n; k++) if (open[k] || SetClassOf(th[k], cls) == 0) { start = k; break; }
                if (start < 0) start = 0;
                var run = new List<Vector3>();
                for (int s = 1; s <= n; s++)
                {
                    int k = (start + s) % n;
                    bool inRun = !open[k] && SetClassOf(th[k], cls) == 1 && (run.Count == 0 || run[^1].DistanceTo(P[k]) < 2.5f);
                    if (inRun) run.Add(P[k]);
                    if ((!inRun || s == n) && run.Count > 0)
                    {
                        if (SetLog > 0f) GD.Print($"DenSet run: room {ri} ({r.X:0.0},{r.Z:0.0}) cls {cls} n {run.Count} from ({run[0].X:0.0},{run[0].Z:0.0}) to ({run[^1].X:0.0},{run[^1].Z:0.0})");
                        if (run.Count >= 6) { modules += SetRun(c, bufs, run, cls, ri * 16 + cls * 4 + runs, top); runs++; ends.Add((cls, new List<Vector3>(run))); foreach (var q in run) SetCover(q); }
                        run.Clear();
                        if (!open[k] && SetClassOf(th[k], cls) == 1) run.Add(P[k]);
                    }
                }
            }
            // (r10c) the inner corners: where a far run's end meets a wall run's north end, the corner painting (B4 back-left,
            // B4R_2 back-right) with its inner point on the meeting, over both runs' ends; its arms fade to their bright roots
            if (SetCorners > 0f)
                foreach (var (fc, fp) in ends)
                {
                    if (fc != 0) continue;
                    var w = fp[0]; var e = fp[0];
                    foreach (var p in fp) { if (p.X < w.X) w = p; if (p.X > e.X) e = p; }
                    foreach (var (sc, sp) in ends)
                    {
                        if (sc != 1 && sc != 3) continue;
                        var nth = sp[0];
                        foreach (var p in sp) if (p.Z < nth.Z) nth = p;
                        var at = sc == 3 ? w : e;
                        if (new Vector2(nth.X - at.X, nth.Z - at.Z).Length() > 5f) continue;
                        string nm = sc == 3 ? "B4" : "B4R_2";
                        var b = setBanks!.Find(q => q.Name == nm);
                        if (b == null) continue;
                        if (!bufs.TryGetValue(nm, out var cb)) bufs[nm] = cb = new SetBuf();
                        SetCorner(c, cb, b, nth.X, at.Dot(CamUp), top);
                        corners++;
                    }
                }
            // (r10c) root spills lying on the floor at the far and side banks' feet, every 6-9 m, now and then skipped
            if (SetSpills > 0f)
                foreach (var (sc, sp) in ends)
                {
                    if (sc == 2) continue;
                    float acc = 0f, next = 2f + 4f * Hash(ri, sc, 811);
                    for (int i = 1; i < sp.Count; i++)
                    {
                        acc += sp[i].DistanceTo(sp[i - 1]);
                        if (acc < next) continue;
                        next = acc + 6f + 3f * Hash(ri * 31 + i, sc, 812);
                        if (Hash(ri * 31 + i, sc, 813) < 0.3f) continue;
                        var dir = new Vector2(r.X - sp[i].X, r.Z - sp[i].Z).Normalized();
                        var at = new Vector2(sp[i].X, sp[i].Z) + dir * (1.2f + 1.0f * Hash(ri * 31 + i, sc, 814));
                        if (SetPick("B6", Hash(ri * 31 + i, sc, 815)) is SetPiece pc && Wall(c, at.X, at.Y) > 0.5f)
                        { PlaceSetObj(c, "B6", pc, at.X, at.Y, 0.5f + 0.25f * Hash(ri * 31 + i, sc, 816), 0f, false, 0f); spills++; }
                    }
                }
            // (r11) bone drifts (O4) along the far banks' feet: every 5-8 m in the boss lair (den_boss.png's ribs and bone
            // drifts along its far wall), now and then in a room; only on far runs (a card's long axis runs east-west)
            if (SetDrifts > 0f && setSheets!.ContainsKey("O4"))
                foreach (var (sc, sp) in ends)
                {
                    if (sc != 0) continue;
                    bool boss = r.Kind == "Boss";
                    float acc = 0f, next = 1.5f + 3f * Hash(ri, sc, 821);
                    for (int i = 1; i < sp.Count; i++)
                    {
                        acc += sp[i].DistanceTo(sp[i - 1]);
                        if (acc < next) continue;
                        next = acc + (boss ? 5f : 12f) + 3f * Hash(ri * 37 + i, sc, 822);
                        if (!boss && Hash(ri * 37 + i, sc, 823) < 0.5f) continue;
                        var dir = new Vector2(r.X - sp[i].X, r.Z - sp[i].Z).Normalized();
                        var at = new Vector2(sp[i].X, sp[i].Z) + dir * (0.9f + 0.6f * Hash(ri * 37 + i, sc, 824));
                        if (Wall(c, at.X, at.Y) < 0.5f || Hole(c, at.X, at.Y) < 1.5f) continue;
                        if (SetPick("O4", Hash(ri * 37 + i, sc, 825)) is SetPiece pc)
                        { PlaceSetObj(c, "O4", pc, at.X, at.Y, SetDrifts * (0.8f + 0.3f * Hash(ri * 37 + i, sc, 826)), 0.1f, false, 0.3f); c.Tick("set drifts"); }
                    }
                }
        }
        Perf.Lap("set: room rings");
        if (SetLanes > 0f && SetMode >= 2) SetLaneRings(c, bufs, ref modules, ref runs, ref spills);
        Perf.Lap("set: lane rings");
        if (SetAlcoveK > 0f && c.Z.WalkField != null && c.Z.WalkField != c.Z.WallField) SetAlcoves(c);
        Perf.Lap("set: alcoves");
        setBossC = Vector3.Zero; lairPits = 0;
        foreach (var rb in c.Z.Rooms) if (rb.Kind == "Boss") setBossC = new Vector3(rb.X, rb.Z, rb.R);
        System.Array.Clear(setSpurSeg); System.Array.Clear(setSpurR);   // (den r16 G2) the lair's spurs for its gloom (radius 0: none)
        for (int i = 0; i < c.Z.Spurs.Count && i < setSpurSeg.Length; i++) { setSpurSeg[i] = c.Z.Spurs[i].Seg; setSpurR[i] = c.Z.Spurs[i].R; }
        if (SetOpenK > 0f) SetOpen(c, rooms.FindAll(q => q.Kind != "Bend"));
        Perf.Lap("set: open");
        if (SetFurK > 0f) SetFur(c);
        Perf.Lap("set: fur");
        LitterOffCrowns(c);   // (den r19 B, R18b item 5)
        Perf.Lap("set: litter off crowns");
        int tris = 0;
        foreach (var (name, b) in bufs)
        {
            if (b.I.Count == 0 || (SetOnly != null && System.Array.IndexOf(SetOnly, name) < 0)) continue;
            var bm = SetMat(name, SetGain);
            if (SetDbgMod > 0f) bm.SetShaderParameter("dbg_mod", SetDbgMod);   // (den r15 E, diagnosis)
            if (name[0] == 'B') { bm.SetShaderParameter("top_k", SetBankTop); bm.SetShaderParameter("pt_take", SetBankPt); }
            if (name[0] == 'B' && SetBankCorr != 1f && CorrTex(c) is ImageTexture ct)   // (den r16 D) the corridor banks darker than the rooms'
            { bm.SetShaderParameter("corr_k", SetBankCorr); bm.SetShaderParameter("corr_tex", ct); bm.SetShaderParameter("corr_map", new Vector3(-c.Z.Half - 0.5f * c.Z.Step, -c.Z.Half - 0.5f * c.Z.Step, 1f / (c.Z.Res * c.Z.Step))); }   // (den r16 D, R15f item 4) every bank card: lit tops and pool light down
            if (SetCutNoise > 0f || SetCutLum > 0f)   // (den r15 E, judge r14 item 4) the bank cards' cut wanders finely and follows the roots
            { bm.SetShaderParameter("cut_noise", SetCutNoise); bm.SetShaderParameter("cut_lum", SetCutLum); bm.SetShaderParameter("cut_scale", SetCutScale); }
            c.Root.AddChild(new MeshInstance3D { Name = "Set_" + name, Mesh = SetMesh(b), MaterialOverride = bm, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
            tris += b.I.Count / 3;
        }
        // (r10c) the objects (boulders, logs, bones, spills): one mesh a sheet; the boulders' shadow hulls in one
        int otris = 0;
        foreach (var (name, b) in objBufs)
        {
            if (b.I.Count == 0 || (SetOnly != null && System.Array.IndexOf(SetOnly, name) < 0)) continue;
            c.Root.AddChild(new MeshInstance3D { Name = "SetObj_" + name, Mesh = SetMesh(b), MaterialOverride = SetMat(name, SetGain * SetObjGain * (name is "O1" ? SetRockGain : name is "O1r" ? SetRockGainLit : 1f)), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
            otris += b.I.Count / 3;
        }
        if (hulls.Count > 0)
        {
            var sph = new SphereMesh { Radius = 1f, Height = 2f, RadialSegments = 16, Rings = 8 }.GetMeshArrays();
            var sv = (Vector3[])sph[(int)Mesh.ArrayType.Vertex]; var si = (int[])sph[(int)Mesh.ArrayType.Index];
            var hb = new SetBuf();
            foreach (var t in hulls)
            {
                int b0 = hb.V.Count;
                foreach (var v in sv) { hb.V.Add(t * v); hb.N.Add(Vector3.Up); hb.U.Add(Vector2.Zero); hb.C.Add(Colors.White); }
                foreach (int ix in si) hb.I.Add(b0 + ix);
            }
            c.Root.AddChild(new MeshInstance3D { Name = "SetObjShadows", Mesh = SetMesh(hb), CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly });
        }
        Perf.Lap("set: meshes");
        c.Count["set modules"] = modules; c.Count["set tris"] = tris; c.Count["set corners"] = corners; c.Count["set spills"] = spills;
        laidHollows.Clear();
        GD.Print($"DenSet: mode {SetMode}, {rooms.Count} rooms, {runs} runs, {modules} modules, {corners} corners, {spills} spills, {tris} bank tris, {otris} object tris, {bufs.Count + objBufs.Count + (hulls.Count > 0 ? 1 : 0)} draws");
    }

    // (r13) The lanes. A room's ring sees a corridor's walls only at grazing angles, and a wall in line with the room's middle
    // never: seed 11's corridor north of its first clearing had no card on its west bank (the Start ring's 4 points there
    // fell under a run's 6), so the wall mesh's dark mound and its foot along the generator's straight capsule showed (the
    // ruled edge and the muddy left bank, r12 judge). Rings from the corridors' own middles (a 2 m lattice where the floor
    // is open round the point, outside every room's circle) gather the edge points no room's run dressed, outside the rooms'
    // circles; each class's points joined where they lie within 1.5 m make one run (one long run a bank, not a short run a
    // ring: every run's ends fade), laid by the rooms' own SetRun, with root spills at its feet. Cards only: nothing collides.
    static readonly float SetLanes = SurvivorUnchained.Args.Num("den-set-lanes", 1f);
    static readonly HashSet<long> setCov = new();
    static long CovK(int i, int j) => ((long)i << 32) ^ (uint)j;
    static void SetCover(Vector3 p)
    {
        const float cs = 0.5f; const int rad = 2;   // (1 m round every dressed edge point)
        int ci = Mathf.FloorToInt(p.X / cs), cj = Mathf.FloorToInt(p.Z / cs);
        for (int i = -rad; i <= rad; i++) for (int j = -rad; j <= rad; j++) if (i * i + j * j <= rad * rad) setCov.Add(CovK(ci + i, cj + j));
    }
    static bool SetCovered(Vector3 p) => setCov.Contains(CovK(Mathf.FloorToInt(p.X / 0.5f), Mathf.FloorToInt(p.Z / 0.5f)));

    static void SetLaneRings(Ctx c, Dictionary<string, SetBuf> bufs, ref int modules, ref int runs, ref int spills)
    {
        const int n = 360;
        const float reach = 9f, lat = 2f, cs = 0.4f;
        bool InRoom(float x, float zz, float pad)
        {
            foreach (var r in c.Z.Rooms) if (r.Kind != "Bend" && new Vector2(x - r.X, zz - r.Z).Length() < r.R + pad) return true;
            return false;
        }
        var P = new Vector3[n]; var open = new bool[n];
        var pool = new Dictionary<long, Vector3>[4];
        for (int q = 0; q < 4; q++) pool[q] = new();
        int rings = 0, lanes = 0;
        float half = c.Z.Half;
        for (float cz = -half + lat; cz < half; cz += lat)
            for (float cx = -half + lat; cx < half; cx += lat)
            {
                if (!SetIn(cx, cz) || Wall(c, cx, cz) < 1.5f || InRoom(cx, cz, 0f)) continue;
                rings++;
                if (Wall(c, cx, cz) >= 1.8f && !InRoom(cx, cz, 3f) && Hole(c, cx, cz) > 2.5f) laneMid.Add(new Vector2(cx, cz));
                for (int k = 0; k < n; k++)
                {
                    float a = k * Mathf.Tau / n;
                    var d = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                    float t = 0.5f;
                    while (t < reach && Wall(c, cx + d.X * t, cz + d.Y * t) >= 0f) t += 0.1f;
                    open[k] = t >= reach;
                    if (open[k]) continue;
                    float lo = t - 0.1f, hi = t;
                    for (int b = 0; b < 10; b++) { float m = 0.5f * (lo + hi); if (Wall(c, cx + d.X * m, cz + d.Y * m) < 0f) hi = m; else lo = m; }
                    float x = cx + d.X * lo, zz = cz + d.Y * lo;
                    P[k] = new Vector3(x, H(c, x, zz), zz);
                }
                for (int k = 0; k < n; k++)
                {
                    if (open[k] || SetCovered(P[k]) || InRoom(P[k].X, P[k].Z, 0.5f)) continue;
                    // the outward normal smoothed over the neighbours' +-3 degrees, as the rooms' rings (their +-1.5 m of edge)
                    var g = Vector2.Zero;
                    for (int j = -3; j <= 3; j++)
                    {
                        int kk = (k + j + n) % n;
                        if (open[kk]) continue;
                        var p = P[kk];
                        g += new Vector2(Wall(c, p.X + 0.3f, p.Z) - Wall(c, p.X - 0.3f, p.Z), Wall(c, p.X, p.Z + 0.3f) - Wall(c, p.X, p.Z - 0.3f));
                    }
                    var o = -g.Normalized();
                    float th = Mathf.RadToDeg(Mathf.Atan2(o.X, -o.Y));
                    long key = CovK(Mathf.FloorToInt(P[k].X / cs), Mathf.FloorToInt(P[k].Z / cs));
                    for (int cls = 0; cls < 4; cls++)
                        if (SetClassOf(th, cls) == 1) pool[cls].TryAdd(key, P[k]);
                }
            }
        // each class's points joined where within 1.5 m (cells of 0.4 m, +-4), a component a run
        for (int cls = 0; cls < 4; cls++)
        {
            var left = new HashSet<long>(pool[cls].Keys);
            var keys = new List<long>(pool[cls].Keys);
            keys.Sort();
            foreach (long k0 in keys)
            {
                if (!left.Remove(k0)) continue;
                var run = new List<Vector3>();
                var todo = new Stack<long>(); todo.Push(k0);
                while (todo.Count > 0)
                {
                    long k = todo.Pop();
                    var p = pool[cls][k];
                    run.Add(p);
                    int ci = Mathf.FloorToInt(p.X / cs), cj = Mathf.FloorToInt(p.Z / cs);
                    for (int i = -4; i <= 4; i++)
                        for (int j = -4; j <= 4; j++)
                        {
                            long kk = CovK(ci + i, cj + j);
                            if (left.Contains(kk) && pool[cls][kk].DistanceTo(p) < 1.5f) { left.Remove(kk); todo.Push(kk); }
                        }
                }
                bool alongX = cls == 0 || cls == 2;
                run.Sort((u, v) => alongX ? u.X.CompareTo(v.X) : u.Dot(CamUp).CompareTo(v.Dot(CamUp)));
                if (run.Count < 6 || run[0].DistanceTo(run[^1]) < 3f) continue;
                float top = -1e9f;
                foreach (var p in run) top = Mathf.Max(top, p.Y);
                int seed = 7919 + (int)(k0 & 0xffff) * 7 + (int)((k0 >> 32) & 0xffff) * 13 + cls;
                if (SetLog > 0f) GD.Print($"DenSet lane: cls {cls} n {run.Count} from ({run[0].X:0.0},{run[0].Z:0.0}) to ({run[^1].X:0.0},{run[^1].Z:0.0})");
                modules += SetRun(c, bufs, run, cls, seed, top + 14f); runs++; lanes++;
                foreach (var q in run) SetCover(q);
                // the rooms' root spills at these feet too (far and side banks), toward the floor (the wall field's rise)
                if (SetSpills > 0f && cls != 2)
                {
                    float acc = 0f, next = 1f + 3f * Hash(seed, cls, 831);
                    for (int i = 1; i < run.Count; i++)
                    {
                        acc += run[i].DistanceTo(run[i - 1]);
                        if (acc < next) continue;
                        next = acc + 4f + 3f * Hash(seed + i, cls, 832);
                        var p = run[i];
                        var dir = new Vector2(Wall(c, p.X + 0.3f, p.Z) - Wall(c, p.X - 0.3f, p.Z), Wall(c, p.X, p.Z + 0.3f) - Wall(c, p.X, p.Z - 0.3f)).Normalized();
                        var at = new Vector2(p.X, p.Z) + dir * (1.0f + 0.8f * Hash(seed + i, cls, 834));
                        if (SetPick("B6", Hash(seed + i, cls, 835)) is SetPiece pc && Wall(c, at.X, at.Y) > 0.5f)
                        { PlaceSetObj(c, "B6", pc, at.X, at.Y, 0.5f + 0.25f * Hash(seed + i, cls, 836), 0f, false, 0f); spills++; }
                    }
                }
            }
        }
        // (den r16 D, R15f item 4) energy 3.2 -> 8.5, ffc08a -> ffcc88: the corridor floor L50 .34 -> .40-.42 at h 45-48, the room pool's (the banks take half of it: --den-bank-pt)
        // (r14, F2) warm pools along the lanes: the corridors had no light of their own (the shafts are the rooms'), their
        // floor a near-black trench (median ~39 against den_room.png's lit floor 79-109). A warm omni over the lane's middle
        // every LanePoolGap metres (greedy, outside the rooms' circles + 3 m), low and soft, no shadow: light only.
        int pools = 0;
        if (LanePoolEnergy > 0f)
        {
            var at = new List<Vector2>();
            foreach (var m in laneMid)
            {
                bool far = true;
                foreach (var q in at) if (q.DistanceTo(m) < LanePoolGap) { far = false; break; }
                if (!far) continue;
                at.Add(m);
                float e = LanePoolEnergy * (0.8f + 0.4f * Hash((int)(m.X * 7f), (int)(m.Y * 7f), 841));
                c.Root.AddChild(new OmniLight3D
                {
                    Name = "lane_pool", Position = new Vector3(m.X, H(c, m.X, m.Y) + LanePoolHigh, m.Y),
                    LightColor = new Color(SurvivorUnchained.Args.Get("den-lane-pool-colour") ?? "ffcc88"), LightEnergy = e,
                    OmniRange = LanePoolRange, OmniAttenuation = 1.3f, ShadowEnabled = false, LightSpecular = 0.1f,
                });
                pools++;
            }
        }
        // (r13) the corridors dressed as thin rooms: den_room.png has things IN the floor, the corridors were bare earth. A
        // stone, a short log or a bone pile now and then off the lane's middle (wall field 0.9-2.0 m in: never its middle
        // 1.5 m), 4.5 m apart at least, about half the lattice's chances skipped; cards, she walks through them.
        int dressed = 0;
        if (SetLaneDress > 0f)
        {
            var taken = new List<Vector2>();
            foreach (var m in laneMid)
            {
                int hx = Mathf.FloorToInt(m.X * 1.7f), hz = Mathf.FloorToInt(m.Y * 1.7f);
                if (Hash(hx, hz, 861) > 0.5f * SetLaneDress) continue;
                float a = Hash(hx, hz, 862) * Mathf.Tau, d = 1.0f + 1.5f * Hash(hx, hz, 863);
                var p = m + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * d;
                float w = Wall(c, p.X, p.Y);
                if (w < 0.9f || w > 2.0f || Hole(c, p.X, p.Y) < 2.2f || InRoom(p.X, p.Y, 2f)) continue;
                bool near = false;
                foreach (var t in taken) if (t.DistanceTo(p) < 4.5f) { near = true; break; }
                if (near) continue;
                float u = Hash(hx, hz, 864), q = Hash(hx, hz, 865), k = Hash(hx, hz, 866);
                string sheet = u < 0.4f ? "O1" : u < 0.6f ? "O2" : "O3";
                if (!setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) continue;
                var sorted = new List<SetPiece>(all);
                sorted.Sort((x, y) => x.Metres.X.CompareTo(y.Metres.X));
                int hf = Mathf.Max(1, sorted.Count / 2);
                var pc = sheet == "O3" ? sorted[(int)(q * sorted.Count) % sorted.Count] : sorted[(int)(q * hf) % hf];
                if (sheet == "O1") PlaceSetObj(c, "O1", pc, p.X, p.Y, Mathf.Min(1f, (1.1f + 0.6f * k) / pc.Metres.X), 0.62f, true, -1f, LaneRockKey);
                else if (sheet == "O2") PlaceSetObj(c, "O2", pc, p.X, p.Y, 0.75f + 0.2f * k, 0.18f, false);
                else PlaceSetObj(c, "O3", pc, p.X, p.Y, 0.9f + 0.3f * k, 0.1f, false);
                taken.Add(p); dressed++;
            }
        }
        laneMid.Clear();
        GD.Print($"DenSet lanes: {rings} rings, {lanes} runs, {pools} lane pools, {dressed} lane pieces");
    }
    // (den r16 W, R15f item 10) Fur tufts and dry leaf drifts (O6) on the open floor of rooms, lairs and corridors: about one per
    // 3.5 m cell in 0.6 (a view's open floor is a third of its frame), seeded; never within 3.6 m of her spawn or the lair's middle (the sticks' rule), the pits, the hollows,
    // the walls' feet or a boulder. The two leaf drifts are flagged "leaf" in set.json by the build (orange pieces).
    static readonly float SetFurK = SurvivorUnchained.Args.Num("den-fur", 1f);   // (den r16 W, R15f item 10) 0 = no fur tufts or leaf drifts
    static readonly float SetFurDens = SurvivorUnchained.Args.Num("den-fur-dens", 0.6f);
    static readonly HashSet<SetPiece> setLeaves = new();
    static void SetFur(Ctx c)
    {
        if (!LoadSet() || !setSheets!.TryGetValue("O6", out var all) || all.Count == 0) return;
        float half = c.Z.Half, clr = SurvivorUnchained.Args.Num("den-stick-clear", 3.6f);
        var leaves = new List<SetPiece>(); var furs = new List<SetPiece>();
        foreach (var pc in all) (setLeaves.Contains(pc) ? leaves : furs).Add(pc);
        var hollows = DenHollows(c);
        var taken = new List<Vector2>();
        foreach (var (bp, _) in c.Boulders) taken.Add(bp);
        int n = 0, nl = 0;
        const float cell = 3.5f;
        int nc = (int)(2f * half / cell);
        for (int j = 0; j < nc; j++)
            for (int i = 0; i < nc; i++)
            {
                if (Hash(i, j, 3101) > SetFurDens * SetFurK) continue;
                var p = new Vector2(-half + (i + 0.15f + 0.7f * Hash(i, j, 3102)) * cell, -half + (j + 0.15f + 0.7f * Hash(i, j, 3103)) * cell);
                if (Wall(c, p.X, p.Y) < 2.0f || Hole(c, p.X, p.Y) < 2.2f) continue;
                if (c.Z.Rooms.Count > 0 && p.DistanceTo(new Vector2(c.Z.Rooms[0].X, c.Z.Rooms[0].Z)) < clr) continue;
                if (setBossC.Z > 0f && p.DistanceTo(new Vector2(setBossC.X, setBossC.Y)) < clr) continue;
                bool bad = false;
                foreach (var (hp, hr, _) in hollows) if (hp.DistanceTo(p) < hr + 1.2f) { bad = true; break; }
                if (!bad) foreach (var t in taken) if (t.DistanceTo(p) < 1.8f) { bad = true; break; }
                if (bad) continue;
                bool leaf = leaves.Count > 0 && Hash(i, j, 3104) < 0.12f;
                var list = leaf ? leaves : furs;
                if (list.Count == 0) continue;
                var pick = list[(int)(Hash(i, j, 3105) * list.Count) % list.Count];
                PlaceSetObj(c, "O6", pick, p.X, p.Y, (leaf ? 0.9f : 0.85f) + 0.3f * Hash(i, j, 3106), 0.1f, false);
                taken.Add(p); n++; if (leaf) nl++;
                if (SetLog > 0f) GD.Print($"DenSet fur at {p.X:0.0},{p.Y:0.0} leaf {leaf}");
            }
        c.Count["set fur"] = n;
        GD.Print($"DenSet fur: {n} tufts and drifts ({nl} leaf)");
    }

    static readonly List<Vector2> laneMid = new();
    static readonly float SetLaneDress = SurvivorUnchained.Args.Num("den-lane-dress", 1f);   // (r13) the corridors' floor pieces (0 off)

    // (r13) The alcoves: ground the drawn wall line bares outside the walkable edge (DenRagged: the corridors' banks pushed
    // outward), which she cannot walk on, is never open floor: a root spill (B6), a stone (O1) or a bone pile (O3) on it,
    // greedy on a 0.6 m lattice where the bared ground is at least 0.3 m deep, 1.4 m apart, the spill most often.
    static readonly float SetAlcoveK = SurvivorUnchained.Args.Num("den-alcove", 1f);
    static void SetAlcoves(Ctx c)
    {
        float half = c.Z.Half;
        var taken = new List<Vector2>();
        int n = 0, sp = 0, st = 0, bo = 0;
        for (float zz = -half + 1f; zz < half - 1f; zz += 0.6f)
            for (float x = -half + 1f; x < half - 1f; x += 0.6f)
            {
                float walk = Bil(c.Z, c.Z.WalkField!, x, zz), drawn = Wall(c, x, zz);
                if (walk > -0.3f || drawn < 0.3f || Hole(c, x, zz) < 1.5f) continue;
                var p = new Vector2(x, zz);
                bool near = false;
                foreach (var t in taken) if (t.DistanceTo(p) < 1.4f) { near = true; break; }
                if (near) continue;
                taken.Add(p);
                int hx = Mathf.FloorToInt(x * 3.1f), hz = Mathf.FloorToInt(zz * 3.1f);
                float u = Hash(hx, hz, 851), q = Hash(hx, hz, 852), k = Hash(hx, hz, 853);
                string sheet = u < 0.62f ? "B6" : u < 0.88f ? "O1" : "O3";
                if (!setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) continue;
                var sorted = new List<SetPiece>(all);
                sorted.Sort((a, b) => a.Metres.X.CompareTo(b.Metres.X));
                int hf = Mathf.Max(1, sorted.Count / 2);
                var pc = sheet == "O1" ? sorted[(int)(q * hf) % hf] : sorted[(int)(q * sorted.Count) % sorted.Count];
                if (sheet == "B6") { PlaceSetObj(c, "B6", pc, x, zz, SetAlcoveK * (0.55f + 0.3f * k), 0f, false, 0f); sp++; }
                else if (sheet == "O1") { PlaceSetObj(c, "O1", pc, x, zz, Mathf.Min(1f, (0.9f + 0.7f * k) / pc.Metres.X), 0.62f, true, -1f, LaneRockKey); st++; }
                else { PlaceSetObj(c, "O3", pc, x, zz, 0.8f + 0.3f * k, 0.1f, false); bo++; }
                n++;
            }
        c.Count["set alcoves"] = n;
        GD.Print($"DenSet alcoves: {n} ({sp} spills, {st} stones, {bo} bones)");
    }
    static readonly float LanePoolEnergy = SurvivorUnchained.Args.Num("den-lane-pool", 8.5f), LanePoolGap = SurvivorUnchained.Args.Num("den-lane-pool-gap", 6.5f),
        LanePoolRange = SurvivorUnchained.Args.Num("den-lane-pool-range", 6.5f), LanePoolHigh = SurvivorUnchained.Args.Num("den-lane-pool-high", 2.4f);

    // One run of a class: modules end to end along it, each laid in the camera's plane with its foot on the edge and cast
    // onto the bank and floor. Returns the modules laid.
    static readonly float SetBankLift = SurvivorUnchained.Args.Num("den-set-banklift", 1f);   // (den r14 corr r3; d14g_L: a 1 m lift lit 1b .26 -> .32, 1c box .25 -> .39) metres the cards over the bank come toward the camera
    static readonly float SetShearMax = SurvivorUnchained.Args.Num("den-set-shear", 0.5f);   // (den r14 corr r3) a far/near run's steepest foot slope (0: all laid)
    static readonly float SetDbgMod = SurvivorUnchained.Args.Num("den-set-dbgmod", 0f);   // (den r15 E, diagnosis) every bank module its own false colour (rows behind striped)
    // (den r15 E, judge r14 item 4: ruled card seams) the cut's fine wander and root-following in the shader (den_set cut_noise,
    // cut_lum, cut_scale), over a wider ramp (SetCutW metres: the ragged border's g from 0 to 1; 0.3 was a 24 px step), and
    // the ragged field unsharpened (SetRagSharp 0: its smoothstep held the cut at 0 or 1 over a fifth of a border, straight)
    static readonly float SetOcclude = SurvivorUnchained.Args.Num("den-occlude", 0f);   // (den r18 lead, coordinator item: a stone hid her whole body, s11 leg L10) back to 0 after test r8o: on a bank card the cut opened a black hole onto the void behind it, and the x-ray silhouette already shows her through the cards. (den r15 F) default 0 until a den_set card is proven over her (the roots that cover her in the film are kit scenes, other shaders); 1 on: set pieces between the camera and her fade round her (den_set.gdshaderinc occ_cut); 0 off
    static readonly float SetCutNoise = SurvivorUnchained.Args.Num("den-set-cut-noise", 0.4f);
    static readonly float SetCutLum = SurvivorUnchained.Args.Num("den-set-cut-lum", 0.5f);
    static readonly float SetCutScale = SurvivorUnchained.Args.Num("den-set-cut-scale", 2.2f);
    static readonly float SetCutW = SurvivorUnchained.Args.Num("den-set-cut-w", 0.8f);
    static readonly float SetRagSharp = SurvivorUnchained.Args.Num("den-set-rag-sharp", 0f);
    static int SetRun(Ctx c, Dictionary<string, SetBuf> bufs, List<Vector3> run, int cls, int seed, float top)
    {
        bool alongX = cls == 0 || cls == 2;
        string kind = cls switch { 0 => "far", 1 => "right", 2 => "near", _ => "left" };
        var choices = setBanks!.FindAll(b => b.Kind == kind);
        if (choices.Count == 0) return 0;
        // the foot as a function of the along coordinate (X for far and near, the plane's Y for the walls)
        var pts = new List<(float a, float f)>();
        foreach (var p in run)
        {
            float X = p.X, Y = p.Dot(CamUp);
            pts.Add(alongX ? (X, Y) : (Y, X));
        }
        pts.Sort((u, v) => u.a.CompareTo(v.a));
        // (den r14 corr r3, items 1 slab/1c) a far or near run along a wall that climbs steeply on screen shears its modules:
        // each column shifted by the foot, the painting's lying roots drawn as diagonal planks and its deep cut a ruled
        // diagonal (seed 11's corridor: room 2's far runs up the corridor mouth's diagonal walls, slopes .84 and .56, laid B1
        // as two dark wedges over the corridor banks' B3/B3R). Past SetShearMax (screen metres per metre, least squares)
        // the run is not laid: the side classes' overlap (40-50 degrees) covers those walls.
        if (alongX && SetShearMax > 0f && pts.Count >= 2)
        {
            float ma = 0f, mf = 0f;
            foreach (var (pa, pf) in pts) { ma += pa; mf += pf; }
            ma /= pts.Count; mf /= pts.Count;
            float sxy = 0f, sxx = 0f;
            foreach (var (pa, pf) in pts) { sxy += (pa - ma) * (pf - mf); sxx += (pa - ma) * (pa - ma); }
            // (den r19 K, R18b item 7: the s23 corr's bottom-left slab was room 1's far run, 152 points / 12 m at slope -0.52, dropped at the 0.5 limit and left bare) a long run (>= 100 points) is laid to --den-set-shear-long (0: the same limit)
            float shearLim = pts.Count >= 100 ? Mathf.Max(SetShearMax, SurvivorUnchained.Args.Num("den-set-shear-long", 0f)) : SetShearMax;
            if (sxx > 1e-4f && Mathf.Abs(sxy / sxx) > shearLim) { if (SetLog > 0f) GD.Print($"DenSet run dropped: cls {cls} slope {sxy / sxx:0.00} n {run.Count} from ({run[0].X:0.0},{run[0].Z:0.0}) to ({run[^1].X:0.0},{run[^1].Z:0.0})"); return 0; }
        }
        float FootAt(float a)
        {
            if (a <= pts[0].a) return pts[0].f;
            if (a >= pts[^1].a) return pts[^1].f;
            int lo = 0, hi = pts.Count - 1;
            while (hi - lo > 1) { int m = (lo + hi) / 2; if (pts[m].a <= a) lo = m; else hi = m; }
            float t = (a - pts[lo].a) / Mathf.Max(pts[hi].a - pts[lo].a, 1e-4f);
            return Mathf.Lerp(pts[lo].f, pts[hi].f, t);
        }
        float a0 = pts[0].a, a1 = pts[^1].a, ext = 1.0f, ov = 2.0f;
        int k = 0, laid = 0;
        SetBank? prev1 = null, prev2 = null;
        var first = choices[(int)(Hash(seed, 61, 0) * choices.Count) % choices.Count];
        float L0 = (alongX ? first.Metres.X : first.Metres.Y) * SetScale;
        float span = a1 - a0 + 2 * ext;
        float s = a0 - ext - Hash(seed, 62, 0) * (L0 > span ? L0 - span : 0.35f * L0);
        while (s < a1 + ext && k < 40)
        {
            var b = k == 0 ? first : choices[(int)(Hash(seed, 63, k) * choices.Count) % choices.Count];
            // (den r15 R, R15 judge item 7: the same mossy rock twice in the s11 corridor) a run's next card is never one of the last two laid
            for (int t = 1; SetNoRepeat > 0f && k > 0 && choices.Count > 2 && t < 8 && (b == prev1 || b == prev2); t++)
                b = choices[(int)(Hash(seed, 63 + 7 * t, k) * choices.Count) % choices.Count];
            // (den r16 W, R15f item 3) a side wall now has two cards (B3/B3b, B3R/B3Rb): with only two, a run's next card is the other one
            if (SetNoRepeat > 0f && k > 0 && !alongX && choices.Count == 2 && b == prev1) b = choices[0] == b ? choices[1] : choices[0];
            prev2 = prev1; prev1 = b;
            float L = (alongX ? b.Metres.X : b.Metres.Y) * SetScale;
            float from = Mathf.Max(s, a0 - ext), to = Mathf.Min(s + L, a1 + ext);
            if (to - from > 0.5f)
            {
                if (!bufs.TryGetValue(b.Name, out var buf)) bufs[b.Name] = buf = new SetBuf();
                SetModule(c, buf, b, alongX, s, L, from, to, FootAt, true, s + L > a1 + ext, 0.05f + 0.03f * (k % 2), top);
                laid++;
                // (r10c) a wall's bank part is 3.8-5.4 m deep: rows behind it, each its bank part 1 m into the one before,
                // drawn under it, so the frame's sides are root tangle to their edges and not the mound's dark mass
                if (!alongX)
                    for (int row = 1; row < SetRows; row++)
                    {
                        var b2 = choices[(int)(Hash(seed + 97 * row, 64, k) * choices.Count) % choices.Count];
                        for (int t = 1; SetNoRepeat > 0f && choices.Count > 2 && t < 8 && b2 == b; t++) b2 = choices[(int)(Hash(seed + 97 * row, 64 + 7 * t, k) * choices.Count) % choices.Count];   // (den r15 R) a row behind is never its own front's card
                        // (den r16 W, R15f item 3) with two cards a side wall's row behind lays the card its front module does not (the same painting side by side)
                        if (SetNoRepeat > 0f && choices.Count == 2 && b2 == b) b2 = choices[0] == b ? choices[1] : choices[0];
                        // (den r15 lead, R15 judge item 7: one mossy rock twice, 390 px apart in the s11 corridor) a side wall has one
                        // card each side, and a row behind lies at its front module's along start: the same painting side by side.
                        // An odd row lays the other wall's card mirrored across (a bank facing this way, another painting)
                        if (SetRowMirror > 0f && row % 2 == 1 && setBanks!.Find(o => o.Kind == (kind == "left" ? "right" : "left") && !o.Mirror) is SetBank ob)
                            b2 = ob with { Kind = kind, FootU = 1f - ob.FootU, Mirror = true };
                        var bd = b2.Mirror ? b : b2;   // (a mirrored row sits where its front's bank part ends: its own foot left a dark trench)
                        float deep = row * Mathf.Max(1.5f, (cls == 3 ? bd.FootU : 1f - bd.FootU) * bd.Metres.X * SetScale - 1f);
                        // (r13) each module's row behind its own depth: at one depth the cards' far border ran parallel to the
                        // corridor down the whole frame (the seed-11 vertical at x ~200)
                        deep += SetRowJit * (Hash(seed + 97 * row, 68, k) - 0.35f);
                        float sh = cls == 3 ? -deep : deep;
                        if (!bufs.TryGetValue(b2.Name, out var buf2)) bufs[b2.Name] = buf2 = new SetBuf();
                        SetModule(c, buf2, b2, false, s, L, from, to, a => FootAt(a) + sh, true, s + L > a1 + ext, 0.0f - 0.01f * row, top, true, deep);
                    }
            }
            s += L - ov;
            k++;
        }
        // (r10c) a far run's row behind, its foot 4 m up the bank and 7 m past the run's ends, its bank part only (under the
        // front row and the corners): the deep bank beyond the corners was the mound's flat black
        if (cls == 0 && SetRows >= 2 && SetBackRow > 0f)
        {
            float e2 = 7f, s2 = a0 - e2 - Hash(seed, 66, 0) * 4f;
            for (int k2 = 0; s2 < a1 + e2 && k2 < 40; k2++)
            {
                var b = choices[(int)(Hash(seed, 67, k2) * choices.Count) % choices.Count];
                float L = b.Metres.X * SetScale;
                float from = Mathf.Max(s2, a0 - e2), to = Mathf.Min(s2 + L, a1 + e2);
                // (r11) only past the front run's ends (behind the corners): over the run's middle its flat earth middle
                // drew a hard dark rectangle across the frame's top (c_p13); --den-set-backrow 1 lays the whole row again
                if (SetBackRow < 1.5f)
                {
                    if (to - from > 0.5f)
                    {
                        if (!bufs.TryGetValue(b.Name, out var buf)) bufs[b.Name] = buf = new SetBuf();
                        SetModule(c, buf, b, true, s2, L, from, to, a => FootAt(a) + 4f, true, s2 + L > a1 + e2, -0.01f, top, true, 4f);
                    }
                }
                else
                    foreach (var (f0, t0) in new[] { (from, Mathf.Min(to, a0 + 1.5f)), (Mathf.Max(from, a1 - 1.5f), to) })
                        if (t0 - f0 > 0.5f)
                        {
                            if (!bufs.TryGetValue(b.Name, out var buf)) bufs[b.Name] = buf = new SetBuf();
                            SetModule(c, buf, b, true, s2, L, f0, t0, a => FootAt(a) + 4f, true, true, -0.01f, top, true, 4f);
                        }
                s2 += L - ov;
            }
        }
        return laid;
    }

    // (den r14 corr) the ragged cut's field: isotropic 2-octave value noise in the world (0..1, sharpened); 0 keeps the sines
    static readonly float SetRaggedIso = SurvivorUnchained.Args.Num("den-set-ragged-iso", 1.6f);
    static float SetRagNoise(float x, float zz)
    {
        static float Vn(float px, float pz, int s)
        {
            int i = Mathf.FloorToInt(px), j = Mathf.FloorToInt(pz);
            float fx = px - i, fz = pz - j;
            fx = fx * fx * (3 - 2 * fx); fz = fz * fz * (3 - 2 * fz);
            return Mathf.Lerp(Mathf.Lerp(Hash(i, j, s), Hash(i + 1, j, s), fx), Mathf.Lerp(Hash(i, j + 1, s), Hash(i + 1, j + 1, s), fx), fz);
        }
        float n = 0.65f * Vn(x / 2.4f, zz / 2.4f, 871) + 0.35f * Vn(x / 0.9f, zz / 0.9f, 872);
        return SetRagSharp > 0f ? SetSm(0.25f, 0.75f, n) : Mathf.Clamp((n - 0.15f) / 0.7f, 0f, 1f);
    }

    static void SetModule(Ctx c, SetBuf buf, SetBank b, bool alongX, float s, float L, float from, float to,
        System.Func<float, float> footAt, bool fadeIn, bool fadeOut, float lift, float top, bool bankOnly = false, float deepAdd = 0f)
    {
        float Wm = b.Metres.X * SetScale, Hm = b.Metres.Y * SetScale, ov = 2.0f;
        const float cell = 0.35f;
        int na = Mathf.Max(2, Mathf.CeilToInt((to - from) / cell) + 1);
        int nc = Mathf.Max(2, Mathf.CeilToInt((alongX ? Hm : Wm) / cell) + 1);
        int base0 = buf.V.Count;
        // (r12) every module its own depth layer: two rooms' rings both laid cards over one corridor bank at the same lift,
        // and the two coplanar casts took the depth test a triangle each (the corridor's checkerboard facets, c_p15)
        float lay = bankOnly ? -0.03f * (setLayer % 5) : SetLayerStep * (setLayer % 10);
        setLayer++;
        var keepv = new bool[na * nc];
        System.Func<float, float, float> surf = (x, zz) => SurfBank(c, x, zz);
        for (int i = 0; i < na; i++)
        {
            float a = Mathf.Lerp(from, to, (float)i / (na - 1));
            float foot = footAt(a);
            float fa = 1f;
            if (fadeIn) fa = Mathf.Min(fa, (a - from) / ov);
            if (fadeOut) fa = Mathf.Min(fa, (to - a) / ov);
            for (int j = 0; j < nc; j++)
            {
                float t = (float)j / (nc - 1);
                float u, v, X, Y;
                bool bankSide;
                float fe;
                if (alongX)
                {
                    u = (a - s) / L; v = t;
                    X = a; Y = foot + (b.FootV - v) * Hm;
                    bankSide = b.Kind == "far" ? v < b.FootV - 0.02f : v > b.FootV + 0.02f;
                    fe = b.Kind == "far" ? v / 0.08f : (1f - v) / 0.08f;   // (the image's straight cut deep in the bank)
                    if (SetFootFade > 0f) fe = Mathf.Min(fe, (b.Kind == "far" ? 1f - v : v) / 0.08f);   // (r12) and its straight cut out on the floor
                }
                else
                {
                    v = 1f - (a - s) / L; u = t;
                    Y = a; X = foot + (u - b.FootU) * Wm;
                    bankSide = b.Kind == "left" ? u < b.FootU - 0.02f : u > b.FootU + 0.02f;
                    fe = b.Kind == "left" ? u / 0.1f : (1f - u) / 0.1f;
                    if (SetFootFade > 0f) fe = Mathf.Min(fe, (b.Kind == "left" ? 1f - u : u) / 0.1f);   // (r12: the corridor's straight floor edge)
                }
                var pc = new Vector3(X, 0f, 0f) + CamUp * Y;
                var q = SetCast(pc, surf, top);
                // (r12) the bank side hidden where its cast lands on walkable floor, by a smooth measure (its 0.5 contour follows
                // the edge's own curve; a flag per vertex cut grid-aligned steps: the pale square cut-outs)
                // (r12) its 0.5 contour wanders up to SetEdgeWave out onto the floor (a slow two-sine field in the world): the
                // corridors' edges ran dead straight (the generator's capsules), a ruled cut down both sides of the frame
                float wv = SetEdgeWave * (0.5f + 0.25f * Mathf.Sin(q.X * 0.83f + 1.7f * Mathf.Sin(q.Z * 0.61f + 0.4f)) + 0.25f * Mathf.Sin(q.Z * 1.37f - q.X * 0.29f + 2.1f));
                float g = SetKeepAll > 0f || !bankSide ? 1f : 1f - SetSm(0.05f, 0.55f, Wall(c, q.X, q.Z) - wv);
                bool keep = g > 0.01f;
                // (r10c) a row behind: its bank part only (its pour would double the front row's on the floor)
                // (r12) its cut fades first (only its brightest masses past it, gone 1.2 m on): the hard cut's straight lines and
                // corners drew pale square cut-outs at a corridor's edge
                if (bankOnly)
                {
                    float d = !alongX ? (b.Kind == "left" ? u - b.FootU - 1f / Wm : b.FootU - 1f / Wm - u) * Wm
                                      : (b.Kind == "far" ? v - b.FootV - 1f / Hm : b.FootV - 1f / Hm - v) * Hm;
                    // (den r13 corr) its floor-side cut ragged too: at d > 1.2 it was a straight column of the card (u fixed),
                    // a ruled vertical down the seed-11 left bank; now 0.15 + up to SetRagged metres short of 1.2 by a world field
                    if (SetFootFade > 0f && SetRagged > 0f)
                    {
                        float nb = 0.5f + 0.3f * Mathf.Sin(q.Z * 1.9f + 1.1f * Mathf.Sin(q.X * 1.3f + 2.2f)) + 0.2f * Mathf.Sin(q.X * 2.7f - q.Z * 0.9f + 1.4f);
                        g = Mathf.Min(g, SetSm(0.15f, 0.45f, 1.2f - d - SetRagged * nb));
                        if (d > 0f) fe = Mathf.Min(fe, 1f - d / 1.0f);
                    }
                    else if (SetFootFade > 0f) { if (d > 1.2f) keep = false; else if (d > 0f) fe = Mathf.Min(fe, 1f - d / 1.0f); }
                    else if (d > 0f) keep = false;
                }
                // (r12) a row behind never reaches the floor's edge (its cut there followed a straight corridor edge: pale slabs)
                if (bankOnly && SetFootFade > 0f) g = Mathf.Min(g, SetSm(0.8f, 1.6f, -Wall(c, q.X, q.Z)));
                // (r14, B1-B2) a module's borders cut ragged: its rectangle's edges are straight lines on screen (the camera's
                // plane), and the fade still shows the brightest masses up to them (the far left's straight-sided cards, the
                // right foot's ruled edge). The cut wanders 0.3 to 0.3 + SetRagged metres in from every border by a slow world
                // field, so a module ends in an organic line of roots against the mass behind it.
                if (SetRagged > 0f)
                {
                    // (the deep border only: the floor side's pour is SetFootFade's, and cut it bared the mesh's foot)
                    float dEdge = alongX ? (b.Kind == "far" ? v : 1f - v) * Hm : (b.Kind == "left" ? u : 1f - u) * Wm;
                    float dEnd = Mathf.Min(fadeIn ? a - from : 99f, fadeOut ? to - a : 99f);
                    float nz = 0.5f + 0.3f * Mathf.Sin(q.X * 2.1f + 1.3f * Mathf.Sin(q.Z * 1.7f + 0.4f)) + 0.2f * Mathf.Sin(q.Z * 2.9f - q.X * 1.1f + 0.7f);
                    // (den r14 corr, item 1a) that field is a sine of X: along a north-south border (a corridor's side bank) X
                    // hardly changes, so the cut wandered +-0.2 m (the seed-11 left bank's vertical at x ~206, IQR 24 px). An
                    // isotropic value noise (2.4 m and 0.9 m) wanders the full 0..1 along any border.
                    if (SetRaggedIso > 0f) nz = SetRagNoise(q.X, q.Z);
                    g = Mathf.Min(g, SetSm(0.15f, 0.15f + SetCutW, Mathf.Min(dEdge, dEnd) - SetRagged * (SetRaggedIso > 0f ? SetRaggedIso : 1f) * nz));
                    // (den r13 corr) the module's end under its neighbour (no fade: the next one's faded start lies over it) was
                    // cut at the painting's own end, a ruled line where the neighbour shows only its bright masses (the seed-11
                    // left bank's horizontal at y 590); ragged too, by a share of SetRagged (it must still meet the neighbour)
                    if (!fadeOut && SetRaggedEnds > 0f)
                        g = Mathf.Min(g, SetSm(0.05f, 0.05f + 0.667f * SetCutW, to - a - SetRaggedEnds * SetRagged * nz));
                    if (!fadeIn && SetRaggedEnds > 0f)
                        g = Mathf.Min(g, SetSm(0.05f, 0.05f + 0.667f * SetCutW, a - from - SetRaggedEnds * SetRagged * nz));
                }
                if (g <= 0.01f) keep = false;
                if (!keep) g = 0f;
                keepv[i * nc + j] = keep;
                // (den r14 corr r3, items 1a/1b/1c) the wall mesh's lumps poked through the cards where the blurred proxy sank under
                // them (the dark mass in front: 1b's black slab, 1c's black box, half of 1a's ruled edge; hidden walls, those boxes
                // lit .26 -> .32, .25 -> .35). Over the bank (never over walkable floor, where she and the floor's things stand) every
                // card is pulled toward the camera by up to SetBankLift metres, the same at a point for all modules (their order holds)
                float bl = SetBankLift > 0f ? SetBankLift * SetSm(0.3f, 1.5f, -Wall(c, q.X, q.Z)) : 0f;
                buf.V.Add(q - CamView * (lift + lay + SetLiftAdd + bl));
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(Mathf.Clamp(b.Mirror ? 1f - u : u, 0f, 1f), Mathf.Clamp(v, 0f, 1f)));   // (den r15 lead) a mirrored bank: the other wall's card, its texture flipped across
                // (den r13 corr) COLOR.b: metres into the drawn bank / 10, in the corridors only (DenRagged's weight): the
                // shader's bank gloom takes the roots dark as they go deeper, so the deep rows' borders and the mass behind
                // meet in the dark (the seed-11 far left's ruled vertical where the cards ended against the mound)
                // (the card's own metres from its foot plus its row's: the wall field saturates a little way into the bank)
                float dIn = deepAdd + (alongX ? (b.Kind == "far" ? b.FootV - v : v - b.FootV) * Hm : (b.Kind == "left" ? b.FootU - u : u - b.FootU) * Wm);
                float gb = SetGloom > 0f ? Mathf.Clamp(dIn * DenRagged.Corridor(q.X, q.Z, c.Z.Rooms) / 10f, 0f, 1f) : 0f;
                buf.C.Add(new Color(Mathf.Clamp(Mathf.Min(fa, fe), 0f, 1f), g, gb, SetDbgMod > 0f ? 0.5f * Mathf.PosMod(setLayer * 0.618034f, 1f) + (bankOnly ? 0.5f : 0f) : 1f));
            }
        }
        for (int i = 0; i < na - 1; i++)
            for (int j = 0; j < nc - 1; j++)
            {
                int k0 = i * nc + j, k1 = k0 + 1, k2 = k0 + nc, k3 = k2 + 1;
                if (!keepv[k0] && !keepv[k1] && !keepv[k2] && !keepv[k3]) continue;
                // (r11) a cell whose cast jumped (the view ray fell off a ledge of the proxy) stretched the painting into a
                // long shard: the black shard on the right and the pale plank strips top left (c_p13). Such cells are dropped.
                if (SetStretch > 0f)
                {
                    float cellM = Mathf.Max((to - from) / (na - 1), (alongX ? Hm : Wm) / (nc - 1));
                    var v0 = buf.V[base0 + k0]; var v1 = buf.V[base0 + k1]; var v2 = buf.V[base0 + k2]; var v3 = buf.V[base0 + k3];
                    float me = Mathf.Max(Mathf.Max(v0.DistanceTo(v1), v0.DistanceTo(v2)), Mathf.Max(v3.DistanceTo(v1), v3.DistanceTo(v2)));
                    if (me > SetStretch * cellM) continue;
                }
                buf.I.Add(base0 + k0); buf.I.Add(base0 + k2); buf.I.Add(base0 + k1);
                buf.I.Add(base0 + k1); buf.I.Add(base0 + k2); buf.I.Add(base0 + k3);
            }
    }

    /// <summary>A painted boulder (O1) on its half-ellipsoid proxy, in the round 6 boulders' place: the painting cast onto
    /// the stone's own form, a shadow-only hull and a contact blob. Returns its footprint's half width (m).</summary>
    static float PlaceSetBoulder(Ctx c, int pick, float x, float zz, float scale, bool big)
    {
        if (!LoadSet() || !setSheets!.TryGetValue("O1", out var all) || all.Count == 0) return 0f;
        var sorted = new List<SetPiece>(all);
        sorted.Sort((p, q) => q.Metres.X.CompareTo(p.Metres.X));
        var pool = sorted.GetRange(big ? 0 : sorted.Count / 2, Mathf.Max(1, sorted.Count / 2));
        var pc = pool[pick % pool.Count];
        bool lit = SetRockLit > 0f;   // (den r14 objects, item 3) the wall groups' stones: bigger, round, lit and mossed
        float rx = PlaceSetObj(c, "O1", pc, x, zz, scale * SetBoulderScale * (big ? 1f : 0.8f) * (lit ? (big ? 1.05f : SetRockBig) : 1f), 0.62f, true, -1f, lit ? "O1r" : null);
        c.Tick("set boulders");
        c.Boulders.Add((new Vector2(x, zz), rx));
        return rx;
    }

    /// <summary>(round 10b) A painted object from a sheet (O1 boulders, O2 logs, O3 bone piles) on its half-ellipsoid
    /// proxy: ry is its height as a share of its half width (a boulder 0.62, a log 0.18, bones 0.1); the shadow-only hull
    /// for the tall ones. Returns the proxy's half width.</summary>
    // (den r16 D, R15f item 4: the corridors flat in value, floor .34 against banks .28-.31, bank L90 .50 against den_room's .33-.39)
    // every bank card's lit tops x SetBankTop (albedo, den_set.gdshaderinc top_k) and its take of the pools' and shafts' light
    // x SetBankPt (pt_take): the lane pools then lift the corridor floor without the banks. 1, 1: the old banks
    static readonly float SetBankTop = SurvivorUnchained.Args.Num("den-bank-top", 0.6f), SetBankPt = SurvivorUnchained.Args.Num("den-bank-pt", 0.5f);   // (d2: s11 corr bank L90 .50 -> .35, rooms .46-.53 -> .37-.40)
    // (den r16 D, R15f item 5) the round boulders' lit planes as one or two facets on the light's side (den_rocks.py facets: O1rf.png); 0: O1r
    static readonly float SetBankCorr = SurvivorUnchained.Args.Num("den-bank-corr", 0.7f);   // (den r16 D) corridor banks' albedo x this (DenRagged.Corridor's weight; 1 off)
    static ImageTexture? corrTex; static ZoneData? corrZone;
    static ImageTexture? CorrTex(Ctx c)
    {
        if (corrZone == c.Z) return corrTex;
        int n = c.Z.Res; var px = new byte[n * n];
        for (int j = 0; j < n; j++) for (int i = 0; i < n; i++)
            px[j * n + i] = (byte)Mathf.Clamp(Mathf.Round(255f * DenRagged.Corridor(-c.Z.Half + i * c.Z.Step, -c.Z.Half + j * c.Z.Step, c.Z.Rooms)), 0f, 255f);
        corrZone = c.Z; corrTex = ImageTexture.CreateFromImage(Image.CreateFromData(n, n, false, Image.Format.R8, px));
        return corrTex;
    }
    static readonly float SetRockFacets = SurvivorUnchained.Args.Num("den-rock-facets", 1f);
    // (den r16 D, R15f item 8: the logs' lit tops C .061-.077 against den_room's .102, lavender driftwood) the logs' (O2) saturation x this
    static readonly float SetLogSat = SurvivorUnchained.Args.Num("den-log-sat", 1.8f);
    static readonly float SetLogCap = SurvivorUnchained.Args.Num("den-log-cap", 3f), SetLogR = SurvivorUnchained.Args.Num("den-log-r", 10f);   // (den r17 lead, R16 item 7) 0: r16's repeats
    static readonly Vector3 SetLogTint = V3("den-log-tint", new Vector3(1f, 1f, 1f));   // (den r16 D) the logs' tint over the set's
    static readonly float SetNoRepeat = SurvivorUnchained.Args.Num("den-set-norepeat", 1f);   // (den r15 R) 0: bank runs may lay one card twice in a row
    static readonly float SetRockVary = SurvivorUnchained.Args.Num("den-rock-vary", 1f);   // (den r15 R) 0: stones near each other may repeat one piece
    static readonly float SetRootK = SurvivorUnchained.Args.Num("den-root-k", 0.8f);   // (den r15 R, judge item 9) the 3D root tendrils (B6) read salmon: albedo L and C x this (linear scale this^3)
    static readonly int BigBoneCap = (int)SurvivorUnchained.Args.Num("den-bigbone-cap", 1f), SkullCap = (int)SurvivorUnchained.Args.Num("den-skull-cap", 1f);   // (den r15 Q) per camera footprint
    static readonly float BigBoneR = SurvivorUnchained.Args.Num("den-bigbone-r", 22f);   // (den r16 E, R15f item 7) was 11: the camera shows more than 11 m, two large pieces slipped through; 11 = as r15
    // (den r16 E2, R15f item 7) an antlered skull takes the large-piece budget too (0 = as r15: skulls only by the skull cap), and the skull cap counts within --den-skull-r m (r15: 15 for the set, 9 for decals)
    static readonly bool BigSkull = SurvivorUnchained.Args.Num("den-bigbone-skull", 1f) > 0f;
    static readonly float SkullR = SurvivorUnchained.Args.Num("den-skull-r", 22f);
    static float PlaceSetObj(Ctx c, string sheet, SetPiece pc, float x, float zz, float k, float ryk, bool hull, float contact = -1f, string? key = null, bool level = false)
    {
        // (den r14 objects, item 4) the bone piles and logs vary: at most 2 deer skulls and 3 rib cages in a camera footprint
        // (DenCaps, ~9 m, the decals' kinds), never two of one log within 8 m; each mirrored, the piles turned about the card's middle
        bool mirror = false; float rot = 0f;
        // (den r15 helper D) a bone drift (O4) is a whole skeleton, skull and ribs: it takes from the same rib cage budget
        if (SetVary > 0f && sheet == "O4" && !(DenCaps.Take("bigbone", new Vector2(x, zz), BigBoneCap, BigBoneR) && DenCaps.Take("ribcage", new Vector2(x, zz), 3, 15f))) return 0f;   // (den r15 Q) one budget across kinds: BigBoneCap large bone pieces (rib cage, heap, drift) within BigBoneR
        if (SetVary > 0f && sheet is "O3" or "O2" && setSheets!.TryGetValue(sheet, out var vall))
        {
            var pp = new Vector2(x, zz);
            int ix = vall.IndexOf(pc);
            if (sheet == "O3")
            {
                // (den r15 helper D) every pile card is a skeleton: skull (ix 3) 2, rib cages (0, 2) 3, heaps (1, 4) 3 within a camera
                // footprint (DenCaps, shared with the decals' kinds); the rest is not laid here (flat litter takes its place)
                string? kind = ix == 3 ? "deer_skull" : ix is 0 or 2 ? "ribcage" : "pile";
                if ((kind != "deer_skull" || BigSkull) && !DenCaps.Take("bigbone", pp, BigBoneCap, BigBoneR)) return 0f;   // (den r15 Q) the large pieces share one budget (den r16 E2: the antlered skull too)
                if (!DenCaps.Take(kind == "deer_skull" ? "skull" : kind, pp, kind == "deer_skull" ? SkullCap : kind == "pile" ? 2 : 3, kind == "pile" ? 8f : kind == "deer_skull" ? SkullR : 15f)) return 0f;
                float rr = Hash((int)(x * 17f), (int)(zz * 17f), 2202);
                rot = ix == 3 ? (rr - 0.5f) * 1.4f : ix == 0 ? (rr - 0.5f) * 3.4f : rr * Mathf.Tau;
            }
            else
            {
                // (den r17 lead, R16 item 7: seven of one splintered log in the s23 room) at most --den-log-cap logs within --den-log-r m
                // (a view), and no log where every variant already lies within 8 m (the loop used to fall through and lay a repeat)
                if (SetLogCap > 0f && !DenCaps.Take("log", pp, (int)SetLogCap, SetLogR)) return 0f;
                bool free = false;
                for (int t = 0; t < vall.Count; t++) { if (DenCaps.Take("log" + ix, pp, 1, 8f)) { free = true; break; } ix = (ix + 1) % vall.Count; pc = vall[ix]; }
                if (!free && SetLogCap > 0f) return 0f;
            }
            mirror = Hash((int)(x * 19f), (int)(zz * 19f), 2203) < 0.5f;
            k *= 0.88f + 0.3f * Hash((int)(x * 23f), (int)(zz * 23f), 2204);
        }
        // (den r15 R, R15 judge item 7: one stone twice, s11 corr) stones near each other (12 m) take different pieces of their size
        // class (big 0 and 3, small 1 and 2); a third is the same piece mirrored and 0.8 the size
        if (SetRockVary > 0f && sheet == "O1" && setSheets!.TryGetValue("O1", out var oall) && oall.Count == 4)
        {
            var pp = new Vector2(x, zz);
            int ix = oall.IndexOf(pc);
            if (ix >= 0)
            {
                int alt = ix switch { 0 => 3, 3 => 0, 1 => 2, _ => 1 };
                if (DenCaps.Take("rock" + ix, pp, 1, 12f)) { }
                else if (DenCaps.Take("rock" + alt, pp, 1, 12f)) { pc = oall[alt]; k *= oall[ix].Metres.X / pc.Metres.X; }
                else k *= 0.8f;
                mirror = Hash((int)(x * 19f), (int)(zz * 19f), 2213) < 0.5f;
            }
        }
        // (den r15 A, R14 judge item 6 "the pale cube rock") O1's flat-topped block (piece 2), cast on its proxy at the banks'
        // feet, drew a pale cube (s11 room 1790-1920,620-800): the plain O1 stones (lanes, alcoves) take the round mossed piece 1
        if (SetRockNoCube > 0f && sheet == "O1" && key == null && setSheets!["O1"].Count > 2 && setSheets["O1"].IndexOf(pc) == 2) pc = setSheets["O1"][1];
        // (den r19 K, R18b item 8: the s11 room's cut-cube stones) --den-rock-round 1: O1's flat-topped block (piece 2) is never laid (any key, wall groups too): the round mossed piece 1, mirrored by the hash; 0 = as r18
        if (SurvivorUnchained.Args.Num("den-rock-round", 1f) > 0f && sheet == "O1" && setSheets!["O1"].Count > 2 && setSheets["O1"].IndexOf(pc) == 2) { k *= pc.Metres.X / setSheets["O1"][1].Metres.X; pc = setSheets["O1"][1]; }
        // (den r18 lead, D4 R17 item 2) the painted bone litter and carcasses turned a little (about +-35 deg, inside the painted light; mirrors are in the sheets)
        if (SetVary > 0f && sheet is "O7" or "O9") rot = (Hash((int)(x * 17f), (int)(zz * 17f), 2205) - 0.5f) * 1.2f;
        // (den r18 D5, R18 item 4: one long bone, always pointing right) --den-flat-rot 1: the flat bones and carcasses turn the full circle, the fur tufts mirror and turn a little
        if (FlatRot > 0f && sheet is "O7" or "O9") rot = (Hash((int)(x * 17f), (int)(zz * 17f), 2205) - 0.5f) * Mathf.Tau;
        if (FlatRot > 0f && sheet == "O6") { mirror = Hash((int)(x * 19f), (int)(zz * 19f), 2206) < 0.5f; rot = (Hash((int)(x * 17f), (int)(zz * 17f), 2207) - 0.5f) * 0.9f; }
        // (den r19 B, R18b item 5) the femur at most --den-femur-cap of the bone picks (a long knobbed bone: piece 0, 4, 8 of O7 and their mirrors); a flat bone never within --den-bone-axis degrees of
        // standing on end on the screen (an edge-on bone reads as a post); litter and root crowns recorded so the litter is taken off the crowns' footprints (LitterOffCrowns)
        if (sheet == "O7" && setSheets!.TryGetValue("O7", out var o7all))
        {
            int oi = o7all.IndexOf(pc);
            if (oi >= 0 && FemurCap < 1f)
            {
                o7Picks++;
                if (oi % 10 is 0 or 4 or 8)
                {
                    if (femurPicks + 1 > FemurCap * o7Picks) { int[] alt = { 1, 5, 6, 9 }; oi = alt[(int)(Hash((int)(x * 13f), (int)(zz * 13f), 2301) * alt.Length) % alt.Length] + (oi >= 10 ? 10 : 0); pc = o7all[oi]; }
                    else femurPicks++;
                }
            }
            if (BoneAxis > 0f && rot != 0f)
            {
                float lim = Mathf.DegToRad(90f - BoneAxis), a = Mathf.PosMod(rot + Mathf.Pi / 2f, Mathf.Pi) - Mathf.Pi / 2f;   // a bone has no head: a in [-90, 90)
                rot += (Mathf.Abs(a) > lim ? Mathf.Sign(a) * lim : a) - a;
            }
        }
        if (LitterCrown >= 0f && !noLitterRec)
        {
            if (objBufs.Count == 0) { crownRec.Clear(); litterRec.Clear(); o7Picks = femurPicks = 0; }   // (a new zone: its buffers were just cleared)
            if (sheet == "B6") crownRec.Add((x, zz, 0.38f * pc.Metres.X * k, 0.45f * pc.Metres.Y * k));
            else if (sheet is "O3" or "O6" or "O7" or "O9") litterRec.Add((key ?? sheet, objBufs.TryGetValue(key ?? sheet, out var lb0) ? lb0.V.Count : 0, x, zz));
        }
        float W = pc.Metres.X * k, Hr = pc.Metres.Y * k;
        // (den r18 lead, L3 R17 item 5) the light's lair shafts keep off the stones, the root crowns and the arc (DungeonLight LairFrameFoot)
        if (sheet is "B6" or "O1" or "O8") Placed.Add((x, zz, 0.5f * W));
        if (sheet == "O8") Tusks.Add((x, zz, 0.5f * W));   // (den r19 lead) the tusk groups apart, for the lair beams
        float rx = 0.46f * W, ry = ryk * rx;
        float aa = CamUp.Y * ry, hm = 0.94f * Hr;
        float bb = Mathf.Max((hm * hm - aa * aa) / (2f * hm), 0.25f * rx);
        float rz = bb / -CamUp.Z;
        float y0 = H(c, x, zz);
        float yFront = new Vector3(x, y0, zz + rz).Dot(CamUp);
        bool domeOnly = SetRockDome > 0f && sheet == "O1";
        System.Func<float, float, float> surf = (px, pz) =>
        {
            float ex = (px - x) / rx, ez = (pz - zz) / rz;
            float e = 1f - ex * ex - ez * ez;
            float s = e > 0f && ry > 0f ? y0 + ry * Mathf.Sqrt(e) : -99f;
            // (r11) never more than 1.5 m under its own foot: over a pit's mouth the cast missed the floor and ran 120 m
            // down the view (seed 23's lair: a fan of streaks to the vanishing point)
            if (level) return Mathf.Max(SurfBank(c, px, pz), FloorY(c, px, pz) + 0.04f);   // (den r17 P3) a root over a pit's lip lies level over the mouth (the pit card's floor), not down the hole under it
            if (domeOnly) return Mathf.Max(Mathf.Max(s, H(c, px, pz)), y0 - 1.5f);   // (den r15 G) plain O1 stones: their own dome over the floor, never the rising bank (the pale cube)
            return Mathf.Max(Mathf.Max(s, SurfBank(c, px, pz)), y0 - 1.5f);
        };
        key ??= sheet;
        if (!objBufs.TryGetValue(key, out var buf)) objBufs[key] = buf = new SetBuf();
        int ob = buf.V.Count;
        const int nu = 16, nv = 14;
        float crot = Mathf.Cos(rot), srot = Mathf.Sin(rot), cyc = yFront + (pc.FootV - 0.5f) * Hr;
        float top = y0 + ry + 10f;
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                float u = (float)i / (nu - 1), v = (float)j / (nv - 1);
                float X = x + (u - 0.5f) * W, Y = yFront + (pc.FootV - v) * Hr;
                if (rot != 0f) { float ox = X - x, oy = Y - cyc; X = x + ox * crot - oy * srot; Y = cyc + ox * srot + oy * crot; }
                var q = SetCast(new Vector3(X, 0f, 0f) + CamUp * Y, surf, top);
                buf.V.Add(q - CamView * (ry > 0f ? 0.04f : 0.03f));
                buf.N.Add(Vector3.Up);
                float uu = mirror ? 1f - u : u;
                buf.U.Add(new Vector2(pc.Uv.Position.X + uu * pc.Uv.Size.X, pc.Uv.Position.Y + v * pc.Uv.Size.Y));
                buf.C.Add(new Color(1f, 1f, key == "O1r" && SetRockPaint <= 0f ? v : 0f, 1f));   // (den r14 objects) the lit boulders' shader wants the card's v
            }
        for (int j = 0; j < nv - 1; j++)
            for (int i = 0; i < nu - 1; i++)
            {
                int k0 = j * nu + i, k1 = k0 + 1, k2 = k0 + nu, k3 = k2 + 1;
                buf.I.Add(ob + k0); buf.I.Add(ob + k2); buf.I.Add(ob + k1); buf.I.Add(ob + k1); buf.I.Add(ob + k2); buf.I.Add(ob + k3);
            }
        if (hull) hulls.Add(new Transform3D(Basis.FromScale(new Vector3(rx, ry, rz)), new Vector3(x, y0, zz)));
        float ca = contact >= 0f ? contact : hull ? 0.6f : 0.35f;
        if (ca <= 0f) return rx;
        blob ??= new GradientTexture2D
        {
            Width = 128, Height = 128, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f),
            Gradient = new Gradient { Offsets = new[] { 0f, 0.55f, 1f }, Colors = new[] { new Color(0, 0, 0, 1), new Color(0, 0, 0, 0.7f), new Color(0, 0, 0, 0) } },
        };
        c.Root.AddChild(new Godot.Decal
        {
            Name = "SetContact", TextureAlbedo = blob, Modulate = new Color(1, 1, 1, ca), AlbedoMix = 1f,
            Size = new Vector3(2.5f * rx, 1.2f, 2.5f * rz), Position = new Vector3(x, y0, zz),
        });
        return rx;
    }

    /// <summary>(r10d) A hole painting (H2 a pit, H1 a hollow) over a hole of the floor: laid in the camera's plane, each
    /// painted point's offset from the painted lip's centre (the piece's mouth) taken to the floor and scaled by the hole's
    /// radius over the painted lip's at its bearing (as the old pit decals were fitted to the outline), then laid on the
    /// level floor; blended at its fading surround. False when there is no such painting.</summary>
    static bool PlaceSetHole(Ctx c, string sheet, Vector2 ctr, float[] co, int pick)
    {
        // (den r18 P5, R17 items 1, 5) --den-pit-paint 1: a lair pit (H2's place) laid as H3's painting (den_boss.png's sunken bowls,
        // the far wall lit, roots over the lips), its big piece on a pit of radius --den-pit-paint-r m or more, the small on the rest;
        // the hole and its ledge kill unchanged (DungeonGen). 0: the procedural pit (pit_cells, pit_v2)
        if (sheet == "H2" && co.Length > 0 && SurvivorUnchained.Args.Num("den-pit-paint", 1f) > 0f)
            foreach (var lr in c.Z.Rooms)
                if (lr.Kind == "Boss" && new Vector2(lr.X, lr.Z).DistanceTo(ctr) < lr.R + 4f) { sheet = "H3"; pick = co[0] >= SurvivorUnchained.Args.Num("den-pit-paint-r", 2.2f) ? 0 : 1; break; }
        if (SetHoles <= 0f || !LoadSet() || !setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) return false;
        var pc = all[pick % all.Count];
        if (pc.Mouth.Z <= 0f) return false;
        // (den r18 lead, R18 judge item 5: both seeds the same two pit paintings, the vein shape and fungus in the same place) an H3
        // painting mirrored east-west on a hash of its spot (--den-pit-mirror 1; 0 as judged)
        bool hm = sheet == "H3" && SurvivorUnchained.Args.Num("den-pit-mirror", 1f) > 0f && Hash((int)(ctr.X * 7f), (int)(ctr.Y * 7f), 2207) < 0.5f;
        float mx = hm ? 1f - pc.Mouth.X : pc.Mouth.X;
        // (den r14 objects, item 11) the cracked-mud hollows were stamps: clear of each other by two diameters, each its own size,
        // turned, its rim a noise outline (Fourier lobes 2-5)
        float hrot = 0f;
        if (sheet == "H1" && co.Length == 1 && SetHollowVary > 0f)
        {
            int hx = (int)(ctr.X * 11f), hz = (int)(ctr.Y * 11f);
            float hr0 = co[0] * (0.75f + 0.4f * Hash(hx, hz, 2401));
            foreach (var (q, qr) in laidHollows) if (q.DistanceTo(ctr) < 2f * (hr0 + qr) * SetHollowGap) return true;   // too near its neighbour: left out
            laidHollows.Add((ctr, hr0));
            var nc = new float[9]; nc[0] = hr0;
            for (int h = 2; h <= 5; h++) { float am = hr0 * (0.2f / h) * (0.5f + Hash(hx, hz, 2410 + h)); float ph = Hash(hx, hz, 2420 + h) * Mathf.Tau; nc[2 * h - 3] = am * Mathf.Cos(ph); nc[2 * h - 2] = am * Mathf.Sin(ph); }
            co = nc;
            hrot = Hash(hx, hz, 2402) * Mathf.Tau;
        }
        // (den r19 V2, R18b item 6: the same two paintings in both seeds) an H3 painting turned a quarter by a hash of its spot (--den-pit-rot 1; 0 off)
        float prot = sheet == "H3" && SurvivorUnchained.Args.Num("den-pit-rot", 0f) > 0f ? Mathf.Pi * 0.5f * Mathf.Floor(4f * Hash((int)(ctr.X * 7f), (int)(ctr.Y * 7f), 2208)) : 0f;
        float sn = -CamUp.Z;   // a floor metre north draws this many metres up the camera's plane
        float W = pc.Metres.X, Hr = pc.Metres.Y, ma = pc.Mouth.Z * W, mb = pc.Mouth.W * Hr / sn;
        if (!objBufs.TryGetValue(sheet, out var buf)) objBufs[sheet] = buf = new SetBuf();
        int ob = buf.V.Count;
        // (r12) a hole in the boss lair glows green (den_boss.png): COLOR.a 0.5 marks it, and a green light low in it
        bool lairHole = false;
        foreach (var rr in c.Z.Rooms) if (rr.Kind == "Boss" && new Vector2(rr.X, rr.Z).DistanceTo(ctr) < rr.R + 4f) lairHole = true;
        // (den r17 P, R16 item 1) the lair's walkable hollows (H1) are not dressed as glowing pits: the judged lair "pits" were
        // these (the real holes lay off the frame); the holes (H2) now sit in view (DungeonGen.LairPitPlan). 0: as r16
        if (sheet == "H1" && SurvivorUnchained.Args.Num("den-hollow-plain", SurvivorUnchained.Maps.DungeonGen.LairPits > 0 ? 1f : 0f) > 0f) lairHole = false;   // (den r17 P2) plain whenever the lair's pits are in view (DungeonGen.LairPits); 0: dressed as pits
        if (lairHole) GD.Print($"[den-pit] {sheet} at ({ctr.X:0.0}, {ctr.Y:0.0}) r {co[0]:0.00}");   // (den r17 P2) for framing a pit (--at)
        // (den r13 rooms) one or two pits of the lair dark and empty (no glow, no light): the first, and the third on a seed-salted coin
        bool pitEmpty = false;
        if (lairHole && SurvivorUnchained.Args.Num("den-pit-empty", 0f) > 0f)
        {
            int pn = lairPits++;
            pitEmpty = pn == 0 || (pn == 2 && Hash((int)(ctr.X * 7f), (int)(ctr.Y * 7f), 1313) < 0.5f);
            GD.Print($"[den-lair] pit {pn} at {ctr.X:0.0},{ctr.Y:0.0} empty={pitEmpty}");
        }
        if (lairHole && !pitEmpty && SurvivorUnchained.Args.Num("den-pit-glow", 0.8f) > 0f)
            c.Root.AddChild(new OmniLight3D { Name = "PitGlow", Position = new Vector3(ctr.X, FloorY(c, ctr.X, ctr.Y) + SurvivorUnchained.Args.Num("den-pit-light-y", -1.6f), ctr.Y),   // (den r17 P, R16 item 1) was +0.6: it lit the card's middle 14x its rim (the dome's hot centre)
                LightColor = new Color(0.62f, 0.95f, 0.5f), LightEnergy = SurvivorUnchained.Args.Num("den-pit-light", 0.7f), OmniRange = 4.5f, OmniAttenuation = 1.6f, ShadowEnabled = false });
        int nu = Mathf.Clamp(Mathf.CeilToInt(W / 0.3f) + 1, 8, 48), nv = Mathf.Clamp(Mathf.CeilToInt(Hr / 0.3f) + 1, 8, 48);
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                float u = (float)i / (nu - 1), v = (float)j / (nv - 1);
                float dx = (u - mx) * W, dz = (v - pc.Mouth.Y) * Hr / sn;   // floor metres from the lip's centre (x east, z south)
                float th = Mathf.Atan2(dz, dx), cs = Mathf.Cos(th), si = Mathf.Sin(th);
                float rp = ma * mb / Mathf.Sqrt(mb * mb * cs * cs + ma * ma * si * si);
                float g = Mathf.Clamp(FourierAt(co, th) / Mathf.Max(rp, 0.05f), 0.15f, 4f);
                var off = new Vector2(dx, dz) * g;
                if (prot != 0f) off = new Vector2(off.X * Mathf.Cos(prot) - off.Y * Mathf.Sin(prot), off.X * Mathf.Sin(prot) + off.Y * Mathf.Cos(prot));   // (den r19 V2)
                if (hrot != 0f) off = new Vector2(off.X * Mathf.Cos(hrot) - off.Y * Mathf.Sin(hrot), off.X * Mathf.Sin(hrot) + off.Y * Mathf.Cos(hrot));
                var w = ctr + off;
                if (lairHole && SetPitCells > 0f) { while (buf.U2.Count < buf.V.Count) buf.U2.Add(Vector2.Zero); buf.U2.Add(off); }   // (den r16 A) the pit-local offset
                buf.V.Add(new Vector3(w.X, FloorY(c, w.X, w.Y) + 0.05f, w.Y));
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(pc.Uv.Position.X + (hm ? 1f - u : u) * pc.Uv.Size.X, pc.Uv.Position.Y + v * pc.Uv.Size.Y));
                // (r11) COLOR.b: half the painted point's distance from the lip's centre in lip radii (1 at the lip), so
                // den_set_soft fades the painting's own earth surround out past the rim (it read as a pink stamped ring)
                float ell = Mathf.Sqrt(dx * dx / Mathf.Max(ma * ma, 1e-4f) + dz * dz / Mathf.Max(mb * mb, 1e-4f));
                // (den r16 A2, R15f item 1) a cell pit's COLOR.g: its lip's radius on this bearing / 8 (metres; the sunken pit's wall)
                float cg = lairHole && !pitEmpty && SetPitCells > 0f && sheet != "H3" && SurvivorUnchained.Args.Num("den-pit-glow", 0.8f) > 0f ? Mathf.Clamp(rp * g / 8f, 0f, 1f) : 1f;   // (den r18 P5) H3 a painting: COLOR.g 1 (den_set's alpha cut at .5)
                buf.C.Add(new Color(1f, cg, Mathf.Clamp(0.5f * ell, 0f, 1f), lairHole && !pitEmpty ? 0.5f : 1f));
            }
        for (int j = 0; j < nv - 1; j++)
            for (int i = 0; i < nu - 1; i++)
            {
                int k0 = j * nu + i, k1 = k0 + 1, k2 = k0 + nu, k3 = k2 + 1;
                buf.I.Add(ob + k0); buf.I.Add(ob + k2); buf.I.Add(ob + k1); buf.I.Add(ob + k1); buf.I.Add(ob + k2); buf.I.Add(ob + k3);
            }
        c.Tick("set " + sheet);
        return true;
    }

    /// <summary>(r10d) The rooms' open floor dressed, as den_room.png has things IN the room: bone piles (O3) through it, a
    /// small stone (O1) or a short log (O2) a few metres off the banks; seed-salted (Hash), clear of the room's middle (her
    /// start and the fight), the walls' feet, the pits and hollows, the boulders and each other (the decals' Ok() rule).
    /// (r11) The boss lair too, as den_boss.png: one hero boulder (about 3 m) first, then kills' bone piles and blood
    /// through its open floor, a stone or log now and then; all cards, she and the pack walk through them.</summary>
    static void SetOpen(Ctx c, List<(float X, float Z, float R, string Kind)> rooms)
    {
        var hollows = DenHollows(c);
        var taken = new List<Vector2>();
        foreach (var (bp, _) in c.Boulders) taken.Add(bp);
        int ri = 0, n = 0;
        foreach (var r in rooms)
        {
            ri++;
            bool lair = r.Kind == "Boss";
            int want = Mathf.RoundToInt(SetOpenK * (lair ? SetLairWant : 3f + r.R / 2.5f)), got = 0;   // (r12 judge: den_boss.png ~80 pieces; 35 -> --den-lair-want)   // (r11 judge: the lair ~a third of den_boss.png's dressing)   // (r11 1.5 + R/4 -> 3 + R/3: den_room.png has a handful IN the room)
            float a0 = Hash(ri, 21, 990) * Mathf.Tau;
            int rw = 0, rl = 0, rn = 0, crowns = 0;   // (den r13 rooms) the lair's root-crowns (B6 spills) so far
            var crownAt = new List<(Vector2 P, float Hx, float Hz)>();   // (den r18 D5) the lair's root-crowns' footprints: no litter, fire or low-half group on them
            for (int k = 0; k < (lair ? 900 : 96) && got < want; k++)
            {
                float rad = lair ? (got == 0 ? 4f + 5f * Hash(ri, k, 991) : 3f + SetLairRing * Mathf.Sqrt(Hash(ri, k, 991))) : 2.8f + Mathf.Max(0.8f * r.R - 2.8f, 0.5f) * Mathf.Sqrt(Hash(ri, k, 991)), ang = a0 + k * 2.39996f;
                // (the hero stone on the lair's far side, up the frame from the fight: below, it stands behind the HUD)
                if (lair && got == 0) ang = Mathf.Pi * (1.15f + 0.7f * Hash(ri, k, 989));   // (r11: from 2.8 m off her start to 0.8 R: the room's R overreaches its floor)
                var p = new Vector2(r.X + Mathf.Cos(ang) * rad, r.Z + Mathf.Sin(ang) * rad);
                float w = Wall(c, p.X, p.Y);
                if (w < 1.8f || Hole(c, p.X, p.Y) < 2.2f || p.DistanceTo(new Vector2(r.X, r.Z)) < 2.6f) { rw++; continue; }
                // (r11) never in an exit's lane: a ray from the room's middle past this point (and 15 degrees either side)
                // that meets no wall within R + 8 m runs out through a door
                bool lane = false;
                for (int e = -1; e <= 1 && !lane; e++)
                {
                    float ea = ang + e * 0.26f;
                    var d = new Vector2(Mathf.Cos(ea), Mathf.Sin(ea));
                    float t = 0.5f;
                    while (t < r.R + 8f && Wall(c, r.X + d.X * t, r.Z + d.Y * t) >= 0f) t += 0.5f;
                    if (t >= r.R + 8f) lane = true;
                }
                if (lane) { rl++; continue; }
                bool near = false;
                foreach (var (hp, hr, _) in hollows) if (hp.DistanceTo(p) < hr + 1.2f) near = true;
                foreach (var t in taken) if (t.DistanceTo(p) < (lair ? 1.8f : 2.6f)) near = true;
                if (near) { rn++; continue; }
                float u = Hash(ri, k, 992), q = Hash(ri, k, 993);
                bool litRock = SetRockLit > 0f;
                string sheet = lair ? (got == 0 ? "O1" : u < (litRock ? 0.035f : 0.09f) ? "O1" : u < 0.16f ? "O2" : u < 0.42f ? "B6" : u < 0.56f ? "O4" : "O3") : u < (litRock ? 0.13f : 0.35f) ? "O1" : u < 0.5f ? "O2" : "O3";   // (r11: boulders and logs anywhere in the open, as den_room.png)
                if (lair && sheet == "B6" && SetLairCrowns > 0 && ++crowns > SetLairCrowns) { sheet = "O3"; crowns--; }   // (den r13 rooms) at most this many root-crowns in a lair, the rest small scatter
                if (!setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) continue;
                var sorted = new List<SetPiece>(all);
                sorted.Sort((a, b) => a.Metres.X.CompareTo(b.Metres.X));
                // (stones and logs from the sheet's smaller half, a stone at most 1.6 m across: she walks through them)
                int half = Mathf.Max(1, sorted.Count / 2);
                var pc = sheet is "O3" or "B6" or "O4" ? sorted[(int)(q * sorted.Count) % sorted.Count] : sorted[(int)(q * half) % half];
                if (NoRibHeap > 0f && sheet == "O3" && all.IndexOf(pc) == 1) pc = all[Hash(ri, k, 987) < 0.5f ? 2 : 4];   // (den r18 D5, R18 item 4) the curved rib with straight sticks read as a bow
                // (r11: a stone up to 2.4 m across, a log 3-4 m: they are cards, she walks through them; the room's
                // fight was tuned without them, so none has a body)
                if (lair && got == 0) pc = sorted[sorted.Count - 1];   // (the lair's hero stone: the sheet's biggest)
                if (!lair && FireNear(p, 0.5f * pc.Metres.X, 0.5f * pc.Metres.X)) { rn++; continue; }   // (den r18 lead, r9a/r9b: the s11 start room's stone stood on its campfire)
                if (lair && (FireClear > 0f || FlatRot > 0f))
                {
                    // (den r18 D5, R18 items 2, 4) crowns, stones and logs keep --den-fire-clear m from a fire; a crown (and the hero stone's) keeps off the litter groups already laid
                    float kk = sheet == "B6" ? 0.7f : 1f, hx = (sheet == "B6" ? 0.42f : 0.5f) * pc.Metres.X * kk, hz = sheet == "B6" ? 0.42f * pc.Metres.Y * kk * 1.4f : hx;
                    if (got == 0) { hx = Mathf.Max(hx, 2.4f); hz = Mathf.Max(hz, 1.8f); }
                    bool bad = FireNear(p, hx, hz);
                    if (!bad && sheet == "B6" && got > 0) foreach (var cl in openClumps) { float dx = (cl.X - p.X) / (hx + 0.2f), dz = (cl.Y - p.Y) / (hz + 0.2f); if (dx * dx + dz * dz < 1f) { bad = true; break; } }
                    if (bad) { if (sheet == "B6") crowns--; rn++; continue; }
                    if (sheet == "B6") crownAt.Add((p, hx, hz));
                }
                float k2 = sheet == "O4" ? 0.55f + 0.25f * Hash(ri, k, 994) : sheet == "B6" ? 0.6f + 0.25f * Hash(ri, k, 994) : lair && got == 0 ? Mathf.Min(litRock ? 1.6f : 1.2f, (2.8f + 0.6f * Hash(ri, k, 994)) / pc.Metres.X) : sheet == "O1" ? Mathf.Min(litRock ? 1.6f : 1f, (1.6f + 0.8f * Hash(ri, k, 994)) * (litRock ? 1.5f : 1f) / pc.Metres.X) : sheet == "O2" ? 0.8f + 0.2f * Hash(ri, k, 994) : 0.9f + 0.3f * Hash(ri, k, 994);
                // (r11) the lair's roots over its floor, as den_boss.png's: a spill under the hero stone, more through the open
                if (lair && got == 0 && SetPick("B6", Hash(ri, k, 988)) is SetPiece hs && ++crowns > 0)
                    PlaceSetObj(c, "B6", hs, p.X, p.Y + 0.4f, 0.85f, 0f, false, 0f);
                if (sheet is "B6" or "O4") PlaceSetObj(c, sheet, pc, p.X, p.Y, k2, sheet == "O4" ? 0.1f : 0f, false, sheet == "O4" ? 0.3f : 0f);
                else PlaceSetObj(c, sheet, pc, p.X, p.Y, k2, sheet == "O1" ? 0.62f : sheet == "O2" ? 0.18f : 0.1f, sheet == "O1", -1f, sheet == "O1" && litRock ? "O1r" : null);
                taken.Add(p); got++; n++;
                // (r11) blood (O5) by a kill's bones, and now and then on its own nearby (den_room.png's splashes and drags)
                if (lair ? Hash(ri, k, 995) < SetLairBlood : Hash(ri, k, 995) < SetRoomBlood)   // (den r15 S: the room's O3 pile always dragged a flat puddle; now by chance)
                {
                    float ba = Hash(ri, k, 996) * Mathf.Tau, bd = 0.9f + 0.8f * Hash(ri, k, 997);
                    var bp = p + new Vector2(Mathf.Cos(ba), Mathf.Sin(ba)) * bd;
                    if (Wall(c, bp.X, bp.Y) > 1.0f && Hole(c, bp.X, bp.Y) > 1.5f && SetPickBlood(Hash(ri, k, 998)) is SetPiece bpc)
                    { PlaceSetObj(c, "O5", bpc, bp.X, bp.Y, SetBloodK * (1.1f + 0.5f * Hash(ri, k, 999)), 0f, false, 0f); c.Tick("set blood"); }
                }
            }
            if (lair && LairLow > 0f) LairLowHalf(c, r, ri, taken, crownAt);   // (den r18 D5, R18 item 7)
            if (lair && (SetLairFungus > 0f || SetPitRoots > 0f)) SetLairDress(c, r, ri, taken);   // (den r17 P3, R16 item 1) the roots run without the fungus (--den-pit-roots 0: as before)
            GD.Print($"SetOpen {r.Kind} room ({r.X:0.0}, {r.Z:0.0}) R {r.R:0.0}: {got}/{want}{(lair ? $", root-crowns {crowns}" : "")}, off the floor {rw}, in a lane {rl}, crowded {rn}");
        }
        c.Count["set open"] = n;
    }

    /// <summary>(den r18 D5, R18 item 7) The lair's near (+z, camera-low) half had no carcass or blood in view: one carcass (O9) on blood (O5) and
    /// two litter groups (a long bone and a tuft; a heap and a fur), each off the pits, crowns, fires, boulders and her standing spot.</summary>
    static void LairLowHalf(Ctx c, (float X, float Z, float R, string Kind) r, int ri, List<Vector2> taken, List<(Vector2 P, float Hx, float Hz)> crownAt)
    {
        if (!setSheets!.TryGetValue("O9", out var o9) || o9.Count < 10 || !setSheets.TryGetValue("O7", out var o7) || o7.Count < 20) return;
        setSheets.TryGetValue("O6", out var o6); setSheets.TryGetValue("O3", out var o3);
        var rc = new Vector2(r.X, r.Z);
        var mine = new List<Vector2>();
        bool Spot(float a0, float r0, out Vector2 at)
        {
            float best = 1e9f; at = default; bool found = false;
            for (int ia = -14; ia <= 14; ia++)
                for (int ir = 0; ir <= 24; ir++)
                {
                    float a = a0 + ia * 0.05f, rad = 3.8f + ir * 0.5f;
                    var p = rc + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * rad;
                    if (p.Y < rc.Y + 1.5f || p.Y > rc.Y + 6.5f || Mathf.Abs(p.X - rc.X) > 13f || Wall(c, p.X, p.Y) < 2.2f || Hole(c, p.X, p.Y) < 2.6f || p.DistanceTo(rc) < 3.4f || FireNear(p, 1.5f, 1.2f)) continue;
                    float sc = Mathf.Abs(ia) * 0.4f + Mathf.Abs(rad - r0);
                    if (sc >= best) continue;
                    bool bad = false;
                    foreach (var tk in taken) if (tk.DistanceTo(p) < 2.4f) { bad = true; break; }
                    foreach (var m in mine) if (!bad && m.DistanceTo(p) < 3.5f) bad = true;
                    foreach (var cl in openClumps) if (!bad && cl.DistanceTo(p) < 1.8f) bad = true;
                    foreach (var h in laidHollows) if (!bad && h.P.DistanceTo(p) < h.R + 1.5f) bad = true;
                    foreach (var cw in crownAt) { float dx = (cw.P.X - p.X) / (cw.Hx + 1f), dz = (cw.P.Y - p.Y) / (cw.Hz + 1f); if (!bad && dx * dx + dz * dz < 1f) bad = true; }
                    if (bad) continue;
                    best = sc; at = p; found = true;
                }
            return found;
        }

        int nlay = 0;
        // (den r19 B, R18b item 2) the guaranteed near-half carcass: a big O9 (red flesh, pale fur, >= 100 px across at play zoom) on an O5 puddle 1.5x its size, up the frame from the subtitle band (screen y < 760:
        // <= ~2.8 m below the lair's middle, where the camera stands), off pits, crowns, fires and her spot; and a root runner across the bare floor to the left. --den-lair-carc 0: the r18 carcass 10 m out.
        float carcK = SurvivorUnchained.Args.Num("den-lair-carc", 1f);
        bool carcDone = false;
        if (carcK > 0f)
        {
            float ck = SurvivorUnchained.Args.Num("den-lair-carc-k", 0.9f);
            float side = Hash(ri, 41, 4510) < 0.5f ? -1f : 1f;
            int ci = new[] { 3, 0, 2 }[(int)(Hash(ri, 41, 4511) * 3f) % 3] + (Hash(ri, 41, 4505) < 0.5f ? 5 : 0);
            float cw = o9[ci].Metres.X * ck, ch = o9[ci].Metres.Y * ck;
            bool Free(Vector2 p, float hx, float hz, float gap)
            {
                if (Wall(c, p.X, p.Y) < 2.2f || Hole(c, p.X, p.Y) < 2.6f || Wall(c, p.X - hx, p.Y) < 1.0f || Wall(c, p.X + hx, p.Y) < 1.0f || Hole(c, p.X - hx, p.Y) < 1.2f || Hole(c, p.X + hx, p.Y) < 1.2f) return false;
                if (p.DistanceTo(rc) < 3.0f || FireNear(p, hx, hz)) return false;
                foreach (var tk in taken) if (tk.DistanceTo(p) < gap) return false;
                foreach (var m in mine) if (m.DistanceTo(p) < gap) return false;
                foreach (var cl in openClumps) if (cl.DistanceTo(p) < gap - 0.6f) return false;
                foreach (var h in laidHollows) if (h.P.DistanceTo(p) < h.R + 1.5f) return false;
                foreach (var cw2 in crownAt) { float dx = (cw2.P.X - p.X) / (cw2.Hx + 1f + hx), dz = (cw2.P.Y - p.Y) / (cw2.Hz + 1f + hz); if (dx * dx + dz * dz < 1f) return false; }
                foreach (var cr in crownRec) if (Mathf.Abs(p.X - cr.X) < cr.Hx + hx + 0.3f && Mathf.Abs(p.Y - cr.Z) < cr.Hz + hz + 0.3f) return false;
                return true;
            }
            Vector2 best = default; float bs = 1e9f; bool got = false;
            for (int pass = 0; pass < 2 && !got; pass++)
                for (float dz = 1.2f; dz <= (pass == 0 ? 2.8f : 3.2f); dz += 0.2f)
                    for (float dx = 2.5f; dx <= 10.5f; dx += 0.5f)
                        foreach (float sg in new[] { side, -side })
                        {
                            var p = rc + new Vector2(sg * dx, dz);
                            float sc = Mathf.Abs(dx - 5f) * 0.5f + Mathf.Abs(dz - 2.2f) + (sg == side ? 0f : 1.5f);
                            if (sc >= bs || !Free(p, 0.5f * cw, 0.5f * ch, pass == 0 ? 2.8f : 2.2f)) continue;
                            bs = sc; best = p; got = true;
                        }
            if (got)
            {
                mine.Add(best);
                var o5 = setSheets.TryGetValue("O5", out var o5l) && o5l.Count > 0 ? o5l[0] : SetPickBlood(Hash(ri, 41, 4502));
                if (o5 is SetPiece bpp) PlaceSetObj(c, "O5", bpp, best.X, best.Y + 0.15f, 1.5f * cw / bpp.Metres.X, 0f, false, 0f);
                noLitterRec = true;
                PlaceSetObj(c, "O9", o9[ci], best.X, best.Y, ck, 0.1f, false, 0.4f);
                noLitterRec = false;
                GD.Print($"[den-lair-carc] carcass {ci} {cw:0.0} m at ({best.X - rc.X:0.0}, {best.Y - rc.Y:0.0}) from the lair middle");
                nlay++; carcDone = true;
            }
            // a root runner (B6 piece 1 or 2, long and low) across the floor on the side away from the carcass
            if (setSheets.TryGetValue("B6", out var b6r) && b6r.Count >= 3)
            {
                var rp = b6r[Hash(ri, 41, 4512) < 0.65f ? 1 : 2]; float rk = 0.6f, hw = 0.42f * rp.Metres.X * rk;
                Vector2 rbest = default; float rs = 1e9f; bool rgot = false;
                for (float dz = 2.0f; dz <= 5.0f; dz += 0.5f)
                    for (float dx = 4.5f; dx <= 9.5f; dx += 0.5f)
                        foreach (float rsg in new[] { -1f, 1f })   // the left of the frame first (the lair's bare lower-left), the right when it is blocked
                    {
                        var p = rc + new Vector2(rsg * dx, dz);
                        float sc = Mathf.Abs(dz - 3.5f) + Mathf.Abs(dx - 6.5f) * 0.3f + (rsg > 0f ? 2f : 0f);
                        if (sc >= rs) continue;
                        bool ok = true;
                        for (int s = -2; s <= 2 && ok; s++) { var q = p + new Vector2(s * hw * 0.5f, 0f); if (Wall(c, q.X, q.Y) < 2.0f || Hole(c, q.X, q.Y) < 2.4f || FireNear(q, 0.5f, 0.5f)) ok = false; }
                        if (ok) foreach (var tk in taken) if (tk.DistanceTo(p) < 2.0f) { ok = false; break; }
                        if (ok) foreach (var m in mine) if (m.DistanceTo(p) < 2.5f) { ok = false; break; }
                        if (ok) foreach (var cl in openClumps) if (cl.DistanceTo(p) < 1.6f) { ok = false; break; }
                        if (!ok) continue;
                        rs = sc; rbest = p; rgot = true;
                    }
                if (rgot) { mine.Add(rbest); PlaceSetObj(c, "B6", rp, rbest.X, rbest.Y, rk, 0f, false, 0f); GD.Print($"[den-lair-carc] root runner at ({rbest.X - rc.X:0.0}, {rbest.Y - rc.Y:0.0})"); }
            }
        }
        if (!carcDone && Spot(Mathf.Pi * (0.82f + 0.06f * Hash(ri, 41, 4501)), 10f, out var pa))   // a carcass on blood
        {
            mine.Add(pa);
            if (SetPickBlood(Hash(ri, 41, 4502)) is SetPiece bp) PlaceSetObj(c, "O5", bp, pa.X, pa.Y, SurvivorUnchained.Args.Num("den-lair-low-k", 1.4f) * (0.55f + 0.2f * Hash(ri, 41, 4503)), 0f, false, 0f);
            int bi = (int)(Hash(ri, 41, 4504) * 5f) % 5 + (Hash(ri, 41, 4505) < 0.5f ? 5 : 0);
            PlaceSetObj(c, "O9", o9[bi], pa.X, pa.Y, 0.7f * SurvivorUnchained.Args.Num("den-lair-low-k", 1.4f), 0.1f, false, 0.4f);   // (den r18 lead: at 0.7 the carcass did not read in d9c; --den-lair-low-k)
            GD.Print($"[den-lair-low] carcass at ({pa.X - rc.X:0.0}, {pa.Y - rc.Y:0.0}) from the lair middle");
            nlay++;
        }
        if (Spot(Mathf.Pi * (0.14f + 0.06f * Hash(ri, 42, 4501)), 11.5f, out var pb))   // a long bone and a tuft
        {
            mine.Add(pb);
            PlaceSetObj(c, "O7", o7[(int)(Hash(ri, 42, 4504) * 10f) % 10 + (Hash(ri, 42, 4505) < 0.5f ? 10 : 0)], pb.X, pb.Y, 0.95f, 0.1f, false, 0.3f);
            if (o6 != null && o6.Count > 0) PlaceSetObj(c, "O6", o6[(int)(Hash(ri, 42, 4506) * o6.Count) % o6.Count], pb.X + 0.4f, pb.Y - 0.3f, 0.7f, 0.1f, false, 0f);
            nlay++;
        }
        if (Spot(Mathf.Pi * (0.62f + 0.06f * Hash(ri, 43, 4501)), 6.5f, out var pc2))   // a heap (never the curved-rib one) and a fur
        {
            mine.Add(pc2);
            if (o3 != null && o3.Count > 4) PlaceSetObj(c, "O3", o3[Hash(ri, 43, 4504) < 0.5f ? 2 : 4], pc2.X, pc2.Y, 0.95f, 0.1f, false);
            if (o6 != null && o6.Count > 0) PlaceSetObj(c, "O6", o6[(int)(Hash(ri, 43, 4506) * o6.Count) % o6.Count], pc2.X - 0.5f, pc2.Y + 0.4f, 0.7f, 0.1f, false, 0f);
            nlay++;
        }
        taken.AddRange(mine);
        GD.Print($"LairLowHalf: {nlay}/3 groups laid in the near half");
    }

    static readonly float SetHollowVary = SurvivorUnchained.Args.Num("den-hollow-vary", 1f);   // (den r14 objects, item 11) hollows: noise outline, size, turn
    static readonly float SetHollowGap = SurvivorUnchained.Args.Num("den-hollow-gap", 1f);     // (1 = two diameters between centres)
    static readonly List<(Vector2 P, float R)> laidHollows = new();
    static readonly float FemurCap = SurvivorUnchained.Args.Num("den-femur-cap", 0.3f);   // (den r19 B, R18b item 5) the femur's share of the bone picks (1 = as before)
    static readonly float BoneAxis = SurvivorUnchained.Args.Num("den-bone-axis", 15f);   // (den r19 B, R18b item 5) degrees: a flat bone never stands within this of on end on the screen (0 = as before)
    static readonly float LitterCrown = SurvivorUnchained.Args.Num("den-litter-crown", 0.3f);   // (den r19 B, R18b item 5) litter keeps this many m off a root crown's footprint (-1 = as before)
    static int o7Picks, femurPicks;
    static bool noLitterRec;
    static readonly List<(float X, float Z, float Hx, float Hz)> crownRec = new();
    static readonly List<(string Key, int Start, float X, float Z)> litterRec = new();
    /// <summary>(den r19 B, R18b item 5) Litter (bones, tufts, carcasses, fur) standing within a root crown's footprint grown by --den-litter-crown m is taken out: its card folded to a point, its contact shadow freed.</summary>
    static void LitterOffCrowns(Ctx c)
    {
        if (LitterCrown < 0f || crownRec.Count == 0) return;
        int cut = 0, all = litterRec.Count;
        for (int i = litterRec.Count - 1; i >= 0; i--)
        {
            var (key, st, x, z) = litterRec[i];
            bool on = false;
            foreach (var cr in crownRec) if (Mathf.Abs(x - cr.X) < cr.Hx + LitterCrown && Mathf.Abs(z - cr.Z) < cr.Hz + LitterCrown) { on = true; break; }
            if (!on) continue;
            litterRec.RemoveAt(i);
            if (!objBufs.TryGetValue(key, out var b) || st + 224 > b.V.Count) continue;
            var v0 = b.V[st];
            for (int j = st; j < st + 224; j++) b.V[j] = v0;
            foreach (var ch in c.Root.GetChildren())
                if (ch is Godot.Decal d && Mathf.Abs(d.Position.X - x) < 0.01f && Mathf.Abs(d.Position.Z - z) < 0.01f) { d.QueueFree(); break; }
            cut++;
        }
        if (cut > 0) GD.Print($"[den-litter-crown] {cut} of {all} litter pieces taken off root crowns");
    }
    static readonly float SetRoomBlood = SurvivorUnchained.Args.Num("den-room-blood", 0.3f);   // (den r15 S) a room pick's chance of a blood splash
    static readonly float SetBloodK = SurvivorUnchained.Args.Num("den-blood-k", 0.7f);   // (den r15 S) splash size x: smaller cores, not flat puddles
    static readonly float SetLairBlood = SurvivorUnchained.Args.Num("den-lair-blood", 0.12f);   // (den r15 lead) a lair pick's chance of a blood splash (was: every bone pile plus 0.6 of the rest: red smears all over the s23 lair)
    static readonly float SetLairFungus = SurvivorUnchained.Args.Num("den-lair-fungus", 0f);   // (den r15 Q, judge r15 item 1) off: the 3D clusters read as toppled teal pills; the root crowns carry painted glow caps.    // (den r14 objects, item 13) glow-fungus clusters on the lair's pit rims (0 off)
    static readonly float SetPitRoots = SurvivorUnchained.Args.Num("den-pit-roots", 2f);   // (den r17 P3, R16 item 1) B6 root ends laid over each in-view lair pit's lip (den_boss.png's roots over the rims): this many on the main, one on each smaller; 0 off
    static readonly float SetLairRoots = SurvivorUnchained.Args.Num("den-lair-roots", 0f);     // (den r18 lead, R17 item 4; r17 3) root tendrils (B6) laid between its pits

    /// <summary>(den r14 objects, item 13) The lair's middle had no fungus and its pits stood bare: root tendrils (B6, cards
    /// that block nothing) laid between the pits and glow-fungus clusters on the pit rims (the Fungus() mushrooms and cool light).</summary>
    static void SetLairDress(Ctx c, (float X, float Z, float R, string Kind) r, int ri, List<Vector2> taken)
    {
        var rc = new Vector2(r.X, r.Z);
        var pits = new List<(Vector2 P, float R)>();
        foreach (var (p, rad, _) in DenPits(c)) if (p.DistanceTo(rc) < r.R + 4f) pits.Add((p, rad));
        int roots = 0, fung = 0;
        for (int i = 0; i < pits.Count && roots < (int)SetLairRoots; i++)
            for (int j = i + 1; j < pits.Count && roots < (int)SetLairRoots; j++)
            {
                float d = pits[i].P.DistanceTo(pits[j].P);
                if (d > 30f) continue;
                var m = pits[i].P.Lerp(pits[j].P, 0.4f + 0.2f * Hash(ri, i, 2315)) + new Vector2(Hash(ri, i * 9 + j, 2301) - 0.5f, Hash(ri, i * 9 + j, 2302) - 0.5f) * 1.5f;
                if (Wall(c, m.X, m.Y) < 1.8f || Hole(c, m.X, m.Y) < 1.0f || SetPick("B6", Hash(ri, i * 9 + j, 2303)) is not SetPiece bp) continue;
                PlaceSetObj(c, "B6", bp, m.X, m.Y, 0.5f + 0.2f * Hash(ri, i, 2304), 0f, false, 0f);
                roots++;
            }
        // (den r17 P3) root ends over the lips: a B6 crown beside the pit (across the frame, or above it), its far tendrils
        // crossing the lip by --den-pit-root-in m; the card cast level over the mouth (PlaceSetObj level), not down the hole
        int lipRoots = 0;
        if (SetPitRoots > 0f)
        {
            float big = 0f;
            var rc0 = new Vector2(r.X, r.Z);
            foreach (var (pp0, pr) in pits) if (pp0.DistanceTo(rc0) < 11f) big = Mathf.Max(big, pr);
            float rin = SurvivorUnchained.Args.Num("den-pit-root-in", 0.6f);
            for (int i = 0; i < pits.Count; i++)
            {
                var (pp, pr) = pits[i];
                if (pp.DistanceTo(rc0) >= 11f) continue;   // the plan's far holes (14 m out, off the frame)
                int nr = pr >= big ? (int)SetPitRoots : 1;
                for (int q = 0; q < nr; q++)
                {
                    if (SetPick("B6", Hash(ri, i * 7 + q, 2331)) is not SetPiece bp) continue;
                    float k2 = 0.55f + 0.15f * Hash(ri, i * 7 + q, 2332);
                    // q 0: across the frame (the side nearer the lair's middle), q 1: above it (its tendrils hang down over the far lip)
                    var dir = q % 2 == 0 ? new Vector2(pp.X > r.X ? -1f : 1f, 0f) : new Vector2(0f, -1f);
                    float t = 0.2f;
                    while (t < 12f && Hole(c, pp.X + dir.X * t, pp.Y + dir.Y * t) < 0f) t += 0.1f;
                    float half = dir.Y == 0f ? 0.5f * bp.Metres.X * k2 : 0.35f * bp.Metres.Y * k2 / -CamUp.Z;
                    var m = pp + dir * (t + half - rin) + new Vector2(0f, (Hash(ri, i * 7 + q, 2333) - 0.5f) * pr * (dir.Y == 0f ? 0.6f : 0f));
                    if (Wall(c, m.X, m.Y) < 1.0f) continue;
                    if (FireNear(m, 0.4f * bp.Metres.X * k2, 0.4f * bp.Metres.Y * k2)) continue;   // (den r18 lead, v9s23_j: a lip crown grew over the lair fire)
                    PlaceSetObj(c, "B6", bp, m.X, m.Y, k2, 0f, false, 0f, null, true);
                    lipRoots++;
                }
            }
        }
        int want = Mathf.RoundToInt(SetLairFungus);
        for (int k = 0; k < 40 && fung < want && pits.Count > 0; k++)
        {
            var (pp, pr) = pits[k % pits.Count];
            float a = Hash(ri, k, 2305) * Mathf.Tau, dd = pr * (1.2f + 0.3f * Hash(ri, k, 2306)) + 0.6f;
            var cp = pp + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * dd;
            if (Wall(c, cp.X, cp.Y) < 1.5f || Hole(c, cp.X, cp.Y) < 0.3f) continue;
            bool near = false;
            foreach (var t in taken) if (t.DistanceTo(cp) < 1.5f) near = true;
            if (near) continue;
            int mn = 7 + (int)(Hash(ri, k, 2307) * 5);
            for (int q = 0; q < mn; q++)
            {
                float ma = Hash(ri, k * 13 + q, 2308) * Mathf.Tau, md = Mathf.Sqrt(Hash(ri, k * 13 + q, 2309)) * 0.55f;
                float x = cp.X + Mathf.Cos(ma) * md, zz = cp.Y + Mathf.Sin(ma) * md;
                if (Wall(c, x, zz) < 0.05f || Hole(c, x, zz) < 0.2f) continue;
                float sh = 0.12f + 0.24f * Hash(ri, k * 13 + q, 2310), sr = 0.025f + 0.025f * Hash(ri, k * 13 + q, 2311), cr = (0.07f + 0.11f * Hash(ri, k * 13 + q, 2312)) * FungCapK;   // (den r15 Q) the room fungus's small upright caps (was tall stems, big caps: toppled teal pills)
                var basis = Basis.Identity;   // (den r15 Q) upright
                var t = new Transform3D(basis, new Vector3(x, H(c, x, zz), zz));
                c.Shrooms.AppendFrom(new CylinderMesh { TopRadius = sr, BottomRadius = sr, Height = sh, RadialSegments = 6, Rings = 1 }, 0, t * new Transform3D(Basis.Identity, new Vector3(0, sh / 2, 0)));
                c.Shrooms.AppendFrom(new SphereMesh { Radius = cr, Height = cr * (0.8f + 0.5f * Hash(ri, k * 13 + q, 2315)), IsHemisphere = true, RadialSegments = 16, Rings = 6 }, 0, t * new Transform3D(Basis.Identity, new Vector3(0, sh, 0)));
            }
            c.Root.AddChild(new OmniLight3D { Name = "FungusLight", LightColor = FungLightCol, LightEnergy = FungLightE, OmniRange = 2.6f, ShadowEnabled = false, Position = new Vector3(cp.X, H(c, cp.X, cp.Y) + 0.5f, cp.Y) });
            c.Clusters++; fung++; taken.Add(cp);
        }
        GD.Print($"SetLairDress: {pits.Count} pits (dist {(pits.Count > 1 ? pits[0].P.DistanceTo(pits[1].P) : 0f):0.0}), {roots} root tendrils, {lipRoots} over the lips, {fung} fungus clusters");
    }

    // (den r15 lead, R15 judge item 5: the s23 room's flat opaque puddles) O5's blood by a kill is its splatters only (pieces
    // 1 and 4: a core and droplets); the puddle (0) and the two drags (2, 3) read as paint. --den-blood-pieces 0,1,2,3,4: all
    static readonly string BloodPieces = SurvivorUnchained.Args.Get("den-blood-pieces") ?? "1,4";
    static SetPiece? SetPickBlood(float u)
    {
        if (!LoadSet() || !setSheets!.TryGetValue("O5", out var all) || all.Count == 0) return null;
        var ok = new List<SetPiece>();
        foreach (var w in BloodPieces.Split(',')) if (int.TryParse(w, out int i) && i >= 0 && i < all.Count) ok.Add(all[i]);
        return ok.Count == 0 ? null : ok[(int)(u * ok.Count) % ok.Count];
    }
    /// <summary>(round 10b) One piece of a set sheet by a hash, or null.</summary>
    static SetPiece? SetPick(string sheet, float u)
    {
        if (!LoadSet() || !setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) return null;
        return all[(int)(u * all.Count) % all.Count];
    }

    /// <summary>(round 10b) The kills' leavings where the set dresses: a painted bone pile (O3) at a pile's seed in place
    /// of the old decal bones, rib cages, skulls, fur and blood; by a bank's foot now and then a painted log (O2).</summary>
    static void SetLitter(Ctx c, Vector2 p, int si, float wall)
    {
        if (wall < 2.2f && Hash(si, 7, 971) < 0.22f && SetPick("O2", Hash(si, 7, 972)) is SetPiece lg)
        {
            PlaceSetObj(c, "O2", lg, p.X, p.Y, 0.7f + 0.2f * Hash(si, 7, 973), 0.18f, false);
            c.Tick("set logs");
            return;
        }
        if (Hash(si, 7, 974) < 0.7f && SetPick("O3", Hash(si, 7, 975)) is SetPiece bn)
        {
            if (NoRibHeap > 0f && setSheets!["O3"].IndexOf(bn) == 1) bn = setSheets["O3"][Hash(si, 7, 977) < 0.5f ? 2 : 4];   // (den r18 D5) not the curved-rib heap
            PlaceSetObj(c, "O3", bn, p.X, p.Y, 0.85f + 0.3f * Hash(si, 7, 976), 0.1f, false);
            c.Tick("set bones");
        }
    }

    /// <summary>(round 10b) Decal kinds the set's paintings replace where it dresses (off-style beside them).</summary>
    static bool SetDrops(string kind) => kind is "bone" or "ribcage" or "wolf_skull" or "deer_skull" or "blood" or "hide" or "drag" or "fur";

    static ArrayMesh SetMesh(SetBuf b)
    {
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        arr[(int)Mesh.ArrayType.Vertex] = b.V.ToArray();
        arr[(int)Mesh.ArrayType.Normal] = b.N.ToArray();
        arr[(int)Mesh.ArrayType.TexUV] = b.U.ToArray();
        if (b.U2.Count > 0) { while (b.U2.Count < b.V.Count) b.U2.Add(Vector2.Zero); arr[(int)Mesh.ArrayType.TexUV2] = b.U2.ToArray(); }   // (den r16 A)
        arr[(int)Mesh.ArrayType.Color] = b.C.ToArray();
        arr[(int)Mesh.ArrayType.Index] = b.I.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        return mesh;
    }

    /// <summary>(r10c) An inner corner (B4 back-left, B4R_2 back-right) laid in the camera's plane with its inner point (the
    /// image's foot_u, foot_v: where its far arm's foot meets its wall arm's) on the plane point (X, Y), cast onto the bank
    /// and floor under the two runs' front rows: it shows where they end, in the corner between them.</summary>
    static void SetCorner(Ctx c, SetBuf buf, SetBank b, float X, float Y, float top)
    {
        float W = b.Metres.X * SetScale, Hm = b.Metres.Y * SetScale;
        const float cell = 0.35f;
        int nu = Mathf.CeilToInt(W / cell) + 1, nv = Mathf.CeilToInt(Hm / cell) + 1;
        int base0 = buf.V.Count;
        var keepv = new bool[nu * nv];
        bool left = b.Kind == "corner_l";
        System.Func<float, float, float> surf = (x, zz) => SurfBank(c, x, zz);
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                float u = (float)i / (nu - 1), v = (float)j / (nv - 1);
                float PX = X + (u - b.FootU) * W, PY = Y + (b.FootV - v) * Hm;
                var q = SetCast(new Vector3(PX, 0f, 0f) + CamUp * PY, surf, top);
                // along the arms from the inner point (the far arm runs away from the wall, the wall arm down the frame)
                // under the runs' front rows (they carry on over its arms), over the rows behind; toward its image's edges only its
                // bright roots, as a module over its neighbour
                float fa = Mathf.Min(Mathf.Min(u * W, (1f - u) * W), Mathf.Min(v * Hm, (1f - v) * Hm)) / 2f;
                bool bankSide = (left ? u < b.FootU - 0.02f : u > b.FootU + 0.02f) || v < b.FootV - 0.02f;
                bool keep = !(bankSide && Wall(c, q.X, q.Z) > 0.3f);
                keepv[j * nu + i] = keep;
                buf.V.Add(q - CamView * 0.02f);
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(u, v));
                buf.C.Add(new Color(fa, keep ? 1f : 0f, 0f, 1f));
            }
        for (int j = 0; j < nv - 1; j++)
            for (int i = 0; i < nu - 1; i++)
            {
                int k0 = j * nu + i, k1 = k0 + 1, k2 = k0 + nu, k3 = k2 + 1;
                if (!keepv[k0] && !keepv[k1] && !keepv[k2] && !keepv[k3]) continue;
                buf.I.Add(base0 + k0); buf.I.Add(base0 + k2); buf.I.Add(base0 + k1);
                buf.I.Add(base0 + k1); buf.I.Add(base0 + k2); buf.I.Add(base0 + k3);
            }
    }
}
