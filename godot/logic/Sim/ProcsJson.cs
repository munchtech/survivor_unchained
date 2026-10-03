using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Sim;

/// <summary>
/// Trigger effects as the web game writes them in content ({ do: 'status',
/// target: 'hit', status: {...} }), read into the Effect kinds: items and
/// traits carry their rules as data.
/// </summary>
public sealed class EffectConverter : JsonConverter<Effect>
{
    public override Effect Read(ref Utf8JsonReader r, Type t, JsonSerializerOptions o)
    {
        using var doc = JsonDocument.ParseValue(ref r);
        var e = doc.RootElement;
        string kind = e.GetProperty("do").GetString()!;
        double N(string k, double d = 0) => e.TryGetProperty(k, out var v) ? v.GetDouble() : d;
        int I(string k, int d = 0) => e.TryGetProperty(k, out var v) ? v.GetInt32() : d;
        string S(string k, string d = "") => e.TryGetProperty(k, out var v) ? v.GetString() ?? d : d;
        School Sc() => EnumKey<School>.Parse(S("school", "physical"));
        Basis B() => S("basis", "flat") switch { "hit" => Basis.Hit, "maxhp" => Basis.MaxHp, "weapon" => Basis.Weapon, _ => Basis.Flat };
        StatusPayload? P(string k = "status") => e.TryGetProperty(k, out var v) ? v.Deserialize<StatusPayload>(o) : null;
        return kind switch
        {
            "explode" => new Effect.Explode(N("radius"), N("damage"), B(), Sc(), P()),
            "status" => new Effect.Apply(P()!, S("target") == "hit", N("radius", 8), I("count", 1)),
            "spread" => new Effect.Spread(EnumKey<StatusKind>.Parse(S("kind")), N("radius"), I("count"), I("stacks", 1)),
            "missiles" => new Effect.Missiles(I("count"), N("damage"), B(), Sc(), EnumKey<Seek>.Parse(S("seek", "nearest")), N("speed"), S("art"), P()),
            "chain" => new Effect.Chain(I("count"), N("range"), N("damage"), B(), Sc()),
            "heal" => new Effect.Heal(N("amount"), B()),
            "shield" => new Effect.Shield(N("amount"), N("duration")),
            "barrier" => new Effect.Barrier(N("fraction"), N("cap", 1), N("duration", 1e9)),
            "zone" => new Effect.Zone(N("radius"), N("duration"), N("dps"), B(), Sc(), S("art"), N("slow"), P()),
            "buff" => new Effect.Buff(S("id"), S("stat"), N("value"), EnumKey<ModKind>.Parse(S("kind")), N("duration"), I("maxStacks", 1)),
            "cooldown" => new Effect.Cooldown(N("seconds"), EnumKey<Effect.CooldownScope>.Parse(S("scope", "all"))),
            "raise" => new Effect.Raise(S("kind") == "ghoul" ? Effect.RaiseKind.Ghoul : Effect.RaiseKind.SpiritWolf, N("duration"), I("max")),
            "pull" => new Effect.Pull(N("radius"), N("strength")),
            "execute" => new Effect.Execute(N("threshold")),
            "nova" => new Effect.Nova(N("radius"), N("damage"), B(), Sc(), N("knockback")),
            "strike" => new Effect.Strike(I("count"), N("radius"), N("damage"), B(), Sc(), N("area")),
            "ember" => new Effect.Ember(N("amount")),
            _ => throw new JsonException($"no trigger effect '{kind}'"),
        };
    }

    public override void Write(Utf8JsonWriter w, Effect v, JsonSerializerOptions o) =>
        throw new NotSupportedException("trigger effects are content: read, never written");
}
