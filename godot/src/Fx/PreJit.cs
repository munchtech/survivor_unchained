using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using Godot;

namespace SurvivorUnchained.Fx;

/// <summary>
/// (P2 task 5) Compiles the game's own methods ahead of their first call, on a worker thread, while the game loads.
/// Measured in the proof exe (legs h1, h2, 140 s of den play): the .NET JIT compiled 1300-1550 methods on the main thread
/// while she played, 112-130 ms in all, and held single frames for it: the first Flare press 22.5-23.0 ms (247 methods in
/// that one frame), the first pickup 11.2 ms then 6.8 ms. A method compiled here is found compiled at its first call.
/// The list is not kept by hand: every method and constructor of this assembly, by reflection, then every closed generic
/// type its fields, signatures and locals name that the runtime has no shared code for (a value-type argument, or a generic
/// of ours), and the equality comparer of each value-type field (a record's Equals asks for it). A new skill or effect is
/// covered by being in the assembly. Not covered: generic METHODS (their type arguments are only known at the call), and
/// what the engine's own binding assembly compiles at its first call. No static constructor is run by this (the canary
/// says so in the log line). --no-prejit turns it off, to measure against.
/// </summary>
public static class PreJit
{
    static int started;
    /// <summary>The worker's last line (also printed as "load: pre-JIT ..."); empty until it is done.</summary>
    public static string Report { get; private set; } = "";

    const BindingFlags Declared = BindingFlags.DeclaredOnly | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static;

    /// <summary>Starts the worker once (below the main thread's priority: the load keeps its core).</summary>
    public static void Start()
    {
        if (Interlocked.Exchange(ref started, 1) != 0 || Args.Has("no-prejit")) return;
        new Thread(Run) { IsBackground = true, Name = "prejit", Priority = ThreadPriority.BelowNormal }.Start();
    }

    static void Run()
    {
        long t0 = Stopwatch.GetTimestamp();
        int own = 0, generic = 0, refused = 0, open = 0;
        var closed = new HashSet<Type>();
        try
        {
            Type[] types;
            try { types = typeof(PreJit).Assembly.GetTypes(); }
            catch (ReflectionTypeLoadException e) { types = Array.FindAll(e.Types, t => t != null)!; }
            foreach (var t in types)
            {
                if (t.IsInterface && t.GetMethods(Declared).Length == 0) continue;
                foreach (var f in Safe(() => t.GetFields(Declared)))
                {
                    Collect(f.FieldType, closed);
                    if (f.FieldType.IsValueType && !f.FieldType.IsPrimitive) Comparer(f.FieldType, closed);
                }
                if (t.ContainsGenericParameters) continue;   // an open generic of ours: compiled through its closed uses
                foreach (var m in Safe(() => t.GetMethods(Declared))) { Prepare(m, null, ref own, ref refused, ref open); Uses(m, closed); }
                foreach (var c in Safe(() => t.GetConstructors(Declared))) { Prepare(c, null, ref own, ref refused, ref open); Uses(c, closed); }
            }
            foreach (var g in closed)
            {
                RuntimeTypeHandle[] inst;
                try { inst = Array.ConvertAll(g.GetGenericArguments(), a => a.TypeHandle); } catch { refused++; continue; }
                foreach (var m in Safe(() => g.GetMethods(Declared))) Prepare(m, inst, ref generic, ref refused, ref open);
                foreach (var c in Safe(() => g.GetConstructors(Declared))) Prepare(c, inst, ref generic, ref refused, ref open);
            }
        }
        catch (Exception e) { Report = $"stopped: {e.GetType().Name}: {e.Message}; "; }
        double ms = Stopwatch.GetElapsedTime(t0).TotalMilliseconds;
        Report += $"{own} methods of the game and {generic} of {closed.Count} closed generic types compiled ahead on a worker in {ms:0} ms; " +
            $"{refused} refused, {open} generic methods left to their first call; static constructors run by it: {(Flag.Ran ? "YES (the canary's ran: look at this)" : "none (canary)")}";
        GD.Print("load: pre-JIT: " + Report);
    }

    static T[] Safe<T>(Func<T[]> get) { try { return get(); } catch { return Array.Empty<T>(); } }

    static void Prepare(MethodBase m, RuntimeTypeHandle[]? inst, ref int done, ref int refused, ref int open)
    {
        if (m.IsAbstract || (m.Attributes & MethodAttributes.PinvokeImpl) != 0) return;
        if ((m.MethodImplementationFlags & (MethodImplAttributes.InternalCall | MethodImplAttributes.Runtime | MethodImplAttributes.Native | MethodImplAttributes.Unmanaged)) != 0) return;
        if (m.ContainsGenericParameters) { open++; return; }
        try
        {
            if (inst == null) RuntimeHelpers.PrepareMethod(m.MethodHandle); else RuntimeHelpers.PrepareMethod(m.MethodHandle, inst);
            done++;
        }
        catch { refused++; }
    }

    /// <summary>The closed generic types a method names: its signature's and its locals'.</summary>
    static void Uses(MethodBase m, HashSet<Type> closed)
    {
        try
        {
            foreach (var p in m.GetParameters()) Collect(p.ParameterType, closed);
            if (m is MethodInfo mi) Collect(mi.ReturnType, closed);
            if (m.GetMethodBody() is { } body) foreach (var l in body.LocalVariables) Collect(l.LocalType, closed);
        }
        catch { }
    }

    /// <summary>Keeps `t` (and the generics among its arguments) when it is a closed generic type the runtime compiles
    /// for it alone: one with a value-type argument, or a generic type of this assembly.</summary>
    static void Collect(Type? t, HashSet<Type> closed)
    {
        while (t != null && t.HasElementType) t = t.GetElementType();
        if (t == null || !t.IsConstructedGenericType || t.ContainsGenericParameters || t.IsByRefLike || closed.Contains(t)) return;
        bool mine = t.Assembly == typeof(PreJit).Assembly, value = false;
        foreach (var a in t.GetGenericArguments())
        {
            if (a.IsByRefLike || a.IsPointer || a.IsByRef) return;
            value |= a.IsValueType;
        }
        if (mine || value) closed.Add(t);
        foreach (var a in t.GetGenericArguments()) Collect(a, closed);
    }

    /// <summary>A value type's default equality comparer (dictionaries, sets and a record's Equals ask for it at their
    /// first use): the comparer is made here, by the runtime's own code, and its type compiled with the rest.</summary>
    static void Comparer(Type t, HashSet<Type> closed)
    {
        try
        {
            if (t.IsByRefLike || t.IsPointer || t.ContainsGenericParameters) return;
            var eq = typeof(EqualityComparer<>).MakeGenericType(t);
            if (!closed.Add(eq)) return;
            if (eq.GetProperty("Default", BindingFlags.Public | BindingFlags.Static)?.GetValue(null) is { } def && def.GetType().IsConstructedGenericType) closed.Add(def.GetType());
        }
        catch { }
    }

    // The canary: a type with a static initializer and a method that reads it. Both are compiled by the walk above like
    // every other; if compiling ahead ran static constructors, Flag.Ran would be true by the end.
    static class Canary { public static readonly int V = Flag.Set(); public static int Read() => V; }
    static class Flag { public static volatile bool Ran; public static int Set() { Ran = true; return 1; } }
}
