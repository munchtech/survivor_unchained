// Her outfits' pieces (tools/assets/heroine_outfits.py), drawn as what they
// are made of rather than as a texture laid on a shape. Each piece carries,
// at each point, how far it is from the piece's edge and how convex it is
// there (its second UV), and how much of the sky it sees and a number of
// its own (its vertex colour); its first UV is in its material's repeats
// (`repeats` a metre), so all detail is at true size.
//  - leather: its grain, fine and coarse; a dyed, burnished edge; a row of
//    stitches in from the edge; lighter and smoother where it is worn (on
//    what stands out), darker in its creases.
//  - metal: forged, not chrome: a faint hammered unevenness and the grain of
//    its polishing; polished bright at its edges and on what stands out,
//    dulled and darkened where pieces meet and dirt keeps.
//  - cloth: its weave, a soft sheen at its edges as seen across it.
//  - gloss: latex and satin, clean and smooth.
// The body is heroine_outfit.gdshaderinc (shared with heroine_outfit_metal.gdshader, which adds metal's own light).
shader_type spatial;

#include "res://shaders/heroine_outfit.gdshaderinc"
