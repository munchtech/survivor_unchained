# l13 bend: solver state (WIP, stopped at context budget; no bend code written yet)

Done: round 4's build.json restored (git show 3d4fedc9f:...); native_build plain + warden rebuilt; plain glb, piece.json,
sockets are byte-identical to round 4's. gear_fit build both -> out/body_p1 (7.9 s). Baseline rigid reach table running
to godot/.shots/gear_p2/l13_bend_reach_rigid (not checked).

Facts found (for the next solver):
- Runtime: 8 influences per vertex (gear_fit.top_k k=8, JOINTS_0/1 + WEIGHTS_0/1 in write_unit); carried shapes are glTF
  morph targets per mesh (e["shapes"]). part_blends only touches the close tier.
- Clips: 32 clips, 2298 frames (Jog_Fwd skipped); 12 idles (idle_{arcanist,reaver,stalker,warden}{,_look,_town}).
- native_travel.skin works on gear_fit.Body (V, N, J, W, joint_names). Plain LBS (no tuck): conservative vs reach_table.
- reach_table.plates() DROPS any component whose blend varies (np.abs(Dc-Dc[0]).max() > 2e-3): a bent plate would vanish
  from the table. It must learn bent plates (match the mode row to a piece.json role that has "bend"; ride per vertex).
- write_unit copies every non-JOINTS/WEIGHTS attribute of the src glb: a custom _BEND attribute would leak to the game.

Design planned (cheapest path, no format plumbing): solve alpha at gear_fit build time inside gear_native.part_blends
for rules with "bend" (piece.json part rule, from build.json lames.bend dict or per-part list, set where "carry" is set
in native_spaulder.spaulder ~768). Per bent part group (plate + rims + rivets = sel): Dr = its ride (dense), Ds = her
skin weights at each vertex's bound point (g.dense_weights on tri/bw[inv]); K = row-normalised biweight kernel radius
"smooth" over the group's points (cKDTree.query_pairs); Dt = K@Ds projected on B = ride bones + top others to 8
(fixed set per part: no top-k switching, exact rigid at alpha 0). LBS is linear in weights, so P(a) = (1-a)Pr + aPt
exactly: per frame heights (nearest skin vertex along its normal) of Pr, Pt, P(a); need = a + (L - h_a)/(h_t - h_r);
alpha = clip(K @ maxfilter_r(need), 0, max) (>= need by construction); 2-3 passes to verify. ~30 s/pass.
Weights: D = (1-a)Dr + aDt -> top_k; shapes (CARRY_SHAPES): (1-a)*rigid-fit delta + a*(K @ skin delta).
Proof tool to write: per-vertex posing of a built part; flex = Kabsch residual per frame (idle / all); lap opening =
(lower edge of plate k - top edge of plate k+1) . posed arm axis per theta bin.
