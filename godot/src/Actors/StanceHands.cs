using SurvivorUnchained.Content;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>Her off-hand follows the stance (view only: no clip, and not person.Kind, changes). On the frame the stance changes
/// (set B taken up or given back) the forearm's and the left hand's pieces become what stances.json "held" names for it, or her
/// loadout's own in set A. A swapped piece sheathes and shows like the original (PersonView.HoldPiece); a left-hand piece
/// without a fitted left pocket (the mace) keeps the plain hand_l mount, the dagger its fitted left fist.</summary>
public sealed class StanceHands
{
    string? applied;   // the stance id last put on the view ("" = none)

    /// <summary>Call each frame; true on the frame the pieces changed (her arm axes then read again).</summary>
    public bool Follow(PersonView view, HeldArms arms, StanceDef? stance, bool sheathed)
    {
        var id = stance?.Id ?? "";
        applied ??= "";
        if (id == applied || view.FlareGripOn) return false;
        view.HoldPiece("forearm.l", Stances.Piece(stance, "forearm.l", arms.Forearm), sheathed);
        var gl = stance?.GripL;
        if (Args.Get("grip-l") is { Length: > 0 } ov) { var q = ov.Split(','); gl = new double[3]; for (int i = 0; i < 3 && i < q.Length; i++) double.TryParse(q[i], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out gl[i]); }
        view.HoldPiece("handslot.l", Stances.Piece(stance, "handslot.l", arms.Left), sheathed, gl);
        applied = id;
        return true;
    }
}
