namespace SurvivorUnchained.Play.Story;

/// <summary>A tap on the Corvane court's events (talk, raise, sig, pull, knock, low, down, cue, gone, open) for the court clip:
/// the game sets On under --clip and prints each with its movie frame. Nothing listens otherwise.</summary>
public static class CourtTrace
{
    public static System.Action<string>? On;
    public static void Say(string ev) => On?.Invoke(ev);
}
