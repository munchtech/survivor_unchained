using System;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace SurvivorUnchained.World;

/// <summary>
/// A value the world remembers: nothing, a yes or no, a number or a word
/// ('beasts.outcome' = 'cured', 'caravan.days' = 3). Compared the way the
/// web game's JavaScript compares them: equal only when the same kind and
/// the same value; as a number, a yes is 1 and nothing is 0.
/// </summary>
[JsonConverter(typeof(FactConverter))]
public readonly struct Fact : IEquatable<Fact>
{
    public enum Kind : byte { Null, Bool, Num, Str }

    public readonly Kind Type;
    readonly double num;
    readonly string? str;

    Fact(Kind type, double num, string? str) { Type = type; this.num = num; this.str = str; }

    public static readonly Fact Null = default;
    public static Fact Of(bool b) => new(Kind.Bool, b ? 1 : 0, null);
    public static Fact Of(double n) => new(Kind.Num, n, null);
    public static Fact Of(string s) => new(Kind.Str, 0, s);

    public static implicit operator Fact(bool b) => Of(b);
    public static implicit operator Fact(double n) => Of(n);
    public static implicit operator Fact(int n) => Of(n);
    public static implicit operator Fact(string? s) => s == null ? Null : Of(s);

    public bool IsNull => Type == Kind.Null;
    /// <summary>JavaScript truthiness: not null, not false, not 0, not ''.</summary>
    public bool Truthy => Type switch
    {
        Kind.Bool => num != 0,
        Kind.Num => num != 0 && !double.IsNaN(num),
        Kind.Str => str!.Length > 0,
        _ => false,
    };

    /// <summary>As a number (JavaScript's Number()): nothing is 0, true is 1,
    /// a word that is not a number is NaN.</summary>
    public double Number => Type switch
    {
        Kind.Num or Kind.Bool => num,
        Kind.Str => double.TryParse(str, NumberStyles.Float, CultureInfo.InvariantCulture, out var v) ? v : str!.Trim().Length == 0 ? 0 : double.NaN,
        _ => 0,
    };

    public string? Str => Type == Kind.Str ? str : null;
    public bool Bool => Type == Kind.Bool && num != 0;

    public bool Equals(Fact o) => Type == o.Type && Type switch
    {
        Kind.Null => true,
        Kind.Str => str == o.str,
        _ => num == o.num,
    };
    public override bool Equals(object? obj) => obj is Fact f && Equals(f);
    public override int GetHashCode() => HashCode.Combine(Type, num, str);
    public static bool operator ==(Fact a, Fact b) => a.Equals(b);
    public static bool operator !=(Fact a, Fact b) => !a.Equals(b);

    /// <summary>As text, the way a template shows it ('' for nothing).</summary>
    public override string ToString() => Type switch
    {
        Kind.Null => "",
        Kind.Bool => num != 0 ? "true" : "false",
        Kind.Num => num.ToString(CultureInfo.InvariantCulture),
        _ => str!,
    };
}

public sealed class FactConverter : JsonConverter<Fact>
{
    public override bool HandleNull => true;

    public override Fact Read(ref Utf8JsonReader r, Type t, JsonSerializerOptions o) => r.TokenType switch
    {
        JsonTokenType.Null => Fact.Null,
        JsonTokenType.True => Fact.Of(true),
        JsonTokenType.False => Fact.Of(false),
        JsonTokenType.Number => Fact.Of(r.GetDouble()),
        JsonTokenType.String => Fact.Of(r.GetString()!),
        _ => throw new JsonException($"a fact is null, a boolean, a number or a string, not {r.TokenType}"),
    };

    public override void Write(Utf8JsonWriter w, Fact v, JsonSerializerOptions o)
    {
        switch (v.Type)
        {
            case Fact.Kind.Null: w.WriteNullValue(); break;
            case Fact.Kind.Bool: w.WriteBooleanValue(v.Bool); break;
            case Fact.Kind.Num: w.WriteNumberValue(v.Number); break;
            default: w.WriteStringValue(v.Str); break;
        }
    }
}
