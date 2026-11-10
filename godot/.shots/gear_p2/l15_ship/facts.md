# l15 ship: plate tops (UNJUDGED)
piece_ship --min 0.45 (flags --min/--max-move/--max-strain; sockets moved by body_follow_post.follow_sockets = same field move).
Follow, all three: twins 49.0%, max move 10.47 mm, strain 3.67 mm; sockets max move 3.94 mm. Nothing refused.
Diagnostic (rebuilt vs old installed, points > 25 mm off x=0, mm): new->old med/p95/max
 plain 2.09/14.17/17.28; etched 1.42/12.47/17.28; gilded 1.77/13.99/17.31. old->new: 1.79/6.16/12.77, 1.30/4.63/12.77, 1.57/4.82/12.77.
 (max well over 3 mm outside the gore: the piece moved, not only the gore; the lead's look decides.)
Chain: cover.py, gear_fit bind, build --body body_p1 (gear/out is git-ignored), gear_wear --tests skin (wear/). pose_tuck NOT run (needs wearcheck --dump).
tuck_count 910 -> 860 on all three (old rows carried pose_tuck raises; re-keyed base tuck lost them): pose_tuck is owed.
Wear after (new table format: close ex | play ex | close frame | play frame): plain 632/0, 101/550, 632/0, 101/551; gilded 104/0, 104/672, 104/0, 104/634; etched 367/0, 0/0, 367/0, 0/0. Before (l12) was 5 columns, not directly comparable.
pytest tools/armor: 134 run; 2 failed after ship, 1 fixed (etched row got "finish" from piece.json; removed), 1 open:
 test_worn_rest::test_joins_keep_the_piece_joined: gear_fit finds 0 gore bridges on plate_top_plain (expects 1): the rebuilt gore is not a bridge component.
