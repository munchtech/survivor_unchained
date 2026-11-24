namespace SurvivorUnchained.Core;

/// <summary>
/// The den test build (export preset "Windows (den test)", feature `den_test`, or a dev run given `--den-loop`; the tester lane,
/// 23 Nov 2026): the den and nothing else, for an outside tester. The exe starts in the den with no switches (Args.DenTest); a
/// den's end (cleared or fallen) goes into a fresh den (a new seed), not to the town; lamp-post travel offers no other zone. The
/// build leaves out the art of every place but the den (the preset's exclude list), so no way out of it may be offered.
/// </summary>
public static class DenTest
{
    /// <summary>Whether this run is the den test (set by the engine at start).</summary>
    public static bool On;
}
