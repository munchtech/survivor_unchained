namespace SurvivorUnchained.Sound; public static class SoundHooks { public static System.Action<string>? Cue; public static void Play(string id) => Cue?.Invoke(id); }
