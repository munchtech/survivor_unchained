using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Sim;

/// <summary>
/// Trigger effects as the web game writes them in content ({ do: 'status',
/// target: 'hit', status: {...} }), read into the Effect kinds and written
/// back (skills.json is written from the defs): items, traits, lamps and
/// skills carry their rules as data.
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

    /* The inverse of Read: each kind's fields under Read's names, a field left
     * out where it is the value Read would fill in. */
    public override void Write(Utf8JsonWriter w, Effect v, JsonSerializerOptions o)
    {
        w.WriteStartObject();
        void Do(string k) => w.WriteString("do", k);
        void N(string k, double x, double d = 0) { if (x != d) w.WriteNumber(k, x); }
        void I(string k, int x, int d = 0) { if (x != d) w.WriteNumber(k, x); }
        void S(string k, string x, string d = "") { if (x != d) w.WriteString(k, x); }
        void B(Basis b) { if (b != Basis.Flat) w.WriteString("basis", b switch { Basis.Hit => "hit", Basis.MaxHp => "maxhp", _ => "weapon" }); }
        void Sc(School s) => w.WriteString("school", EnumKey<School>.Of(s));
        void P(StatusPayload? p) { if (p != null) { w.WritePropertyName("status"); JsonSerializer.Serialize(w, p, o); } }
        switch (v)
        {
            case Effect.Explode e: Do("explode"); N("radius", e.Radius); N("damage", e.Damage); B(e.Basis); Sc(e.School); P(e.Status); break;
            case Effect.Apply e: Do("status"); w.WriteString("target", e.OnHit ? "hit" : "near"); N("radius", e.Radius, 8); I("count", e.Count, 1); P(e.Payload); break;
            case Effect.Spread e: Do("spread"); w.WriteString("kind", EnumKey<StatusKind>.Of(e.Kind)); N("radius", e.Radius); I("count", e.Count); I("stacks", e.Stacks, 1); break;
            case Effect.Missiles e:
                Do("missiles"); I("count", e.Count); N("damage", e.Damage); B(e.Basis); Sc(e.School);
                if (e.Seek != Seek.Nearest) w.WriteString("seek", EnumKey<Seek>.Of(e.Seek));
                N("speed", e.Speed); S("art", e.Art); P(e.Status); break;
            case Effect.Chain e: Do("chain"); I("count", e.Count); N("range", e.Range); N("damage", e.Damage); B(e.Basis); Sc(e.School); break;
            case Effect.Heal e: Do("heal"); N("amount", e.Amount); B(e.Basis); break;
            case Effect.Shield e: Do("shield"); N("amount", e.Amount); N("duration", e.Duration); break;
            case Effect.Barrier e: Do("barrier"); N("fraction", e.Fraction); N("cap", e.Cap, 1); N("duration", e.Duration, 1e9); break;
            case Effect.Zone e:
                Do("zone"); N("radius", e.Radius); N("duration", e.Duration); N("dps", e.Dps); B(e.Basis); Sc(e.School); S("art", e.Art); N("slow", e.Slow); P(e.Status); break;
            case Effect.Buff e:
                Do("buff"); S("id", e.Id); S("stat", e.Stat); N("value", e.Value); w.WriteString("kind", EnumKey<ModKind>.Of(e.Kind)); N("duration", e.Duration); I("maxStacks", e.MaxStacks, 1); break;
            case Effect.Cooldown e: Do("cooldown"); N("seconds", e.Seconds); if (e.Scope != Effect.CooldownScope.All) w.WriteString("scope", EnumKey<Effect.CooldownScope>.Of(e.Scope)); break;
            case Effect.Raise e: Do("raise"); w.WriteString("kind", e.Kind == Effect.RaiseKind.Ghoul ? "ghoul" : "spiritWolf"); N("duration", e.Duration); I("max", e.Max); break;
            case Effect.Pull e: Do("pull"); N("radius", e.Radius); N("strength", e.Strength); break;
            case Effect.Execute e: Do("execute"); N("threshold", e.Threshold); break;
            case Effect.Nova e: Do("nova"); N("radius", e.Radius); N("damage", e.Damage); B(e.Basis); Sc(e.School); N("knockback", e.Knockback); break;
            case Effect.Strike e: Do("strike"); I("count", e.Count); N("radius", e.Radius); N("damage", e.Damage); B(e.Basis); Sc(e.School); N("area", e.Area); break;
            case Effect.Ember e: Do("ember"); N("amount", e.Amount); break;
            default: throw new JsonException($"no trigger effect for {v.GetType().Name}");
        }
        w.WriteEndObject();
    }
}
