using System.Threading;
using System.Threading.Tasks;
using SurvivorUnchained.Core;
using Xunit;

/// <summary>MainWait: a worker that needs the main thread's queue served (as a person made on a worker needs the
/// rendering server flushed) finishes while the main thread waits on it, by a task or by a lock.</summary>
public class MainWaitTests
{
    [Fact]
    public void TaskNeedingThePumpFinishes()
    {
        var served = new ManualResetEventSlim();
        var t = Task.Run(() => { served.Wait(); return 7; });
        Assert.True(MainWait.For(t, true, () => served.Set(), 5000));
        Assert.Equal(7, t.Result);
    }

    [Fact]
    public void LockHeldByAWorkerNeedingThePumpIsTaken()
    {
        var gate = new object();
        var served = new ManualResetEventSlim();
        var holding = new ManualResetEventSlim();
        var w = Task.Run(() => { lock (gate) { holding.Set(); served.Wait(); } });
        holding.Wait();
        MainWait.Enter(gate, true, () => served.Set());
        Monitor.Exit(gate);
        Assert.True(w.Wait(5000));
    }

    [Fact]
    public void TimesOutAndOffMainIsPlain()
    {
        var never = new TaskCompletionSource<int>().Task;
        int pumped = 0;
        Assert.False(MainWait.For(never, true, () => pumped++, 30));
        Assert.True(pumped > 0);
        Assert.False(MainWait.For(never, false, () => pumped = -100, 10));
        Assert.True(pumped > 0);
    }
}
