"""frame-pacing-4: a stack sampler for a running game, with nothing installed (ctypes + dbghelp.dll, which ships with Windows).

  python samp.py <exe path substring> <out prefix> [seconds=60] [interval ms=10]

Waits (up to 60 s) for a process whose image path contains the substring (newest wins), then every interval:
for each thread that burned CPU since the last tick (QueryThreadCycleTime), suspend it, read its context, walk its
stack (StackWalk64, unwind data only, no symbols needed), resume it. Each sample is weighted by the cycles burned.
Writes <out>.samples (one line a sample: t_ms tid cycles addr,addr,... leaf first), <out>.modules (base size path)
and <out>.io (t_ms read_bytes write_bytes threads_busy). Read it with sym.py.
Managed (JIT) frames have no unwind data here: a stack stops there.
"""
import ctypes as C
import ctypes.wintypes as W
import sys
import time

import os
ALL = bool(os.environ.get("SAMP_ALL"))
k32 = C.WinDLL("kernel32", use_last_error=True)
psapi = C.WinDLL("psapi", use_last_error=True)
dbg = C.WinDLL("dbghelp", use_last_error=True)

TH32CS_SNAPPROCESS, TH32CS_SNAPTHREAD = 2, 4
PROCESS_ALL = 0x1F0FFF
THREAD_ACCESS = 0x0002 | 0x0008 | 0x0040 | 0x0800  # suspend_resume, get_context, query_information, query_limited


class PROCESSENTRY32W(C.Structure):
    _fields_ = [("dwSize", W.DWORD), ("cntUsage", W.DWORD), ("th32ProcessID", W.DWORD), ("th32DefaultHeapID", C.c_void_p),
                ("th32ModuleID", W.DWORD), ("cntThreads", W.DWORD), ("th32ParentProcessID", W.DWORD),
                ("pcPriClassBase", C.c_long), ("dwFlags", W.DWORD), ("szExeFile", C.c_wchar * 260)]


class THREADENTRY32(C.Structure):
    _fields_ = [("dwSize", W.DWORD), ("cntUsage", W.DWORD), ("th32ThreadID", W.DWORD), ("th32OwnerProcessID", W.DWORD),
                ("tpBasePri", C.c_long), ("tpDeltaPri", C.c_long), ("dwFlags", W.DWORD)]


class ADDRESS64(C.Structure):
    _fields_ = [("Offset", C.c_uint64), ("Segment", C.c_uint16), ("Mode", C.c_int)]


class KDHELP64(C.Structure):
    _fields_ = [("Thread", C.c_uint64), ("ThCallbackStack", W.DWORD), ("ThCallbackBStore", W.DWORD), ("NextCallback", W.DWORD),
                ("FramePointer", W.DWORD), ("KiCallUserMode", C.c_uint64), ("KeUserCallbackDispatcher", C.c_uint64),
                ("SystemRangeStart", C.c_uint64), ("KiUserExceptionDispatcher", C.c_uint64), ("StackBase", C.c_uint64),
                ("StackLimit", C.c_uint64), ("BuildVersion", W.DWORD), ("RetpolineStubFunctionTableSize", W.DWORD),
                ("RetpolineStubFunctionTable", C.c_uint64), ("RetpolineStubOffset", W.DWORD), ("RetpolineStubSize", W.DWORD),
                ("Reserved0", C.c_uint64 * 2)]


class STACKFRAME64(C.Structure):
    _fields_ = [("AddrPC", ADDRESS64), ("AddrReturn", ADDRESS64), ("AddrFrame", ADDRESS64), ("AddrStack", ADDRESS64),
                ("AddrBStore", ADDRESS64), ("FuncTableEntry", C.c_void_p), ("Params", C.c_uint64 * 4), ("Far", W.BOOL),
                ("Virtual", W.BOOL), ("Reserved", C.c_uint64 * 3), ("KdHelp", KDHELP64)]


class IO_COUNTERS(C.Structure):
    _fields_ = [(n, C.c_uint64) for n in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes", "OtherBytes")]


assert C.sizeof(STACKFRAME64) == 264, C.sizeof(STACKFRAME64)

k32.CreateToolhelp32Snapshot.restype = W.HANDLE
k32.OpenProcess.restype = W.HANDLE
k32.OpenThread.restype = W.HANDLE
k32.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
k32.OpenThread.argtypes = [W.DWORD, W.BOOL, W.DWORD]
k32.SuspendThread.argtypes = [W.HANDLE]
k32.ResumeThread.argtypes = [W.HANDLE]
k32.GetThreadContext.argtypes = [W.HANDLE, C.c_void_p]
k32.QueryThreadCycleTime.argtypes = [W.HANDLE, C.POINTER(C.c_uint64)]
k32.CloseHandle.argtypes = [W.HANDLE]
k32.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, C.c_wchar_p, C.POINTER(W.DWORD)]
k32.GetProcessIoCounters.argtypes = [W.HANDLE, C.POINTER(IO_COUNTERS)]
k32.GetExitCodeProcess.argtypes = [W.HANDLE, C.POINTER(W.DWORD)]
k32.Process32FirstW.argtypes = [W.HANDLE, C.POINTER(PROCESSENTRY32W)]
k32.Process32NextW.argtypes = [W.HANDLE, C.POINTER(PROCESSENTRY32W)]
k32.Thread32First.argtypes = [W.HANDLE, C.POINTER(THREADENTRY32)]
k32.Thread32Next.argtypes = [W.HANDLE, C.POINTER(THREADENTRY32)]
psapi.EnumProcessModulesEx.argtypes = [W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), W.DWORD]
psapi.GetModuleFileNameExW.argtypes = [W.HANDLE, C.c_void_p, C.c_wchar_p, W.DWORD]
psapi.GetModuleInformation.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, W.DWORD]
dbg.SymInitializeW.argtypes = [W.HANDLE, C.c_wchar_p, W.BOOL]
dbg.SymRefreshModuleList.argtypes = [W.HANDLE]
dbg.SymCleanup.argtypes = [W.HANDLE]
dbg.StackWalk64.argtypes = [W.DWORD, W.HANDLE, W.HANDLE, C.POINTER(STACKFRAME64), C.c_void_p, C.c_void_p, C.c_void_p,
                            C.c_void_p, C.c_void_p]
dbg.StackWalk64.restype = W.BOOL
FTA = C.cast(dbg.SymFunctionTableAccess64, C.c_void_p)
GMB = C.cast(dbg.SymGetModuleBase64, C.c_void_p)


def procs():
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    e = PROCESSENTRY32W(); e.dwSize = C.sizeof(e)
    out = []
    ok = k32.Process32FirstW(snap, C.byref(e))
    while ok:
        out.append((e.th32ProcessID, e.szExeFile))
        ok = k32.Process32NextW(snap, C.byref(e))
    k32.CloseHandle(snap)
    return out


def image(pid):
    h = k32.OpenProcess(0x1000, False, pid)
    if not h:
        return ""
    buf = C.create_unicode_buffer(1024); n = W.DWORD(1024)
    ok = k32.QueryFullProcessImageNameW(h, 0, buf, C.byref(n))
    k32.CloseHandle(h)
    return buf.value if ok else ""


def find(sub, wait=60.0):
    sub = sub.lower().replace("/", "\\")
    t0 = time.time()
    while time.time() - t0 < wait:
        hits = [pid for pid, name in procs() if name.lower().endswith(".exe") and sub in image(pid).lower()]
        if hits:
            return max(hits)
        time.sleep(0.05)
    return 0


def threads(pid):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    e = THREADENTRY32(); e.dwSize = C.sizeof(e)
    out = []
    ok = k32.Thread32First(snap, C.byref(e))
    while ok:
        if e.th32OwnerProcessID == pid:
            out.append(e.th32ThreadID)
        ok = k32.Thread32Next(snap, C.byref(e))
    k32.CloseHandle(snap)
    return out


def modules(hp):
    arr = (C.c_void_p * 2048)(); need = W.DWORD()
    if not psapi.EnumProcessModulesEx(hp, arr, C.sizeof(arr), C.byref(need), 3):
        return []
    out = []
    for i in range(min(2048, need.value // 8)):
        buf = C.create_unicode_buffer(1024)
        psapi.GetModuleFileNameExW(hp, arr[i], buf, 1024)
        mi = (C.c_uint64 * 3)()
        psapi.GetModuleInformation(hp, arr[i], mi, 24)
        out.append((arr[i] or 0, mi[1] & 0xFFFFFFFF, buf.value))
    return out


def main():
    sub, out = sys.argv[1], sys.argv[2]
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
    step = (float(sys.argv[4]) if len(sys.argv) > 4 else 10.0) / 1000.0
    pid = find(sub)
    if not pid:
        print("no process with", sub); return 2
    hp = k32.OpenProcess(PROCESS_ALL, False, pid)
    if not hp:
        print("OpenProcess failed", C.get_last_error()); return 2
    dbg.SymSetOptions(0x4 | 0x200 | 0x80000)
    time.sleep(0.3)
    dbg.SymInitializeW(hp, None, True)
    raw = C.create_string_buffer(1232 + 16)
    ctx = C.addressof(raw) + (-C.addressof(raw)) % 16
    hts, last = {}, {}
    f = open(out + ".samples", "w")
    fio = open(out + ".io", "w")
    t0 = time.perf_counter(); wall0 = time.time()
    next_list, next_mods, n, walked, mods = 0.0, 0.0, 0, 0, []
    code = W.DWORD()
    io = IO_COUNTERS()
    cyc = C.c_uint64()
    frame = STACKFRAME64()
    while True:
        now = time.perf_counter() - t0
        if now > secs:
            break
        if not k32.GetExitCodeProcess(hp, C.byref(code)) or code.value != 259:
            break
        if now >= next_list:
            next_list = now + 0.5
            for tid in threads(pid):
                if tid not in hts:
                    h = k32.OpenThread(THREAD_ACCESS, False, tid)
                    if h:
                        hts[tid] = h
            dbg.SymRefreshModuleList(hp)
            if now >= next_mods:
                next_mods = now + 2.0
                m = modules(hp)
                if m:
                    mods = m
        busy = 0
        for tid, h in list(hts.items()):
            if not k32.QueryThreadCycleTime(h, C.byref(cyc)):
                k32.CloseHandle(h); del hts[tid]; continue
            d = cyc.value - last.get(tid, cyc.value)
            last[tid] = cyc.value
            if d < 2_000_000 and not ALL:  # under ~0.5 ms of CPU since the last tick: idle (SAMP_ALL=1 samples waiting threads too)
                continue
            if d < 2_000_000 and n % 10:
                continue
            busy += 1
            if k32.SuspendThread(h) == 0xFFFFFFFF:
                continue
            C.memset(ctx, 0, 1232)
            C.c_uint32.from_address(ctx + 0x30).value = 0x100003
            addrs = []
            if k32.GetThreadContext(h, ctx):
                rip = C.c_uint64.from_address(ctx + 0xF8).value
                C.memset(C.byref(frame), 0, C.sizeof(frame))
                frame.AddrPC.Offset = rip; frame.AddrPC.Mode = 3
                frame.AddrFrame.Offset = C.c_uint64.from_address(ctx + 0xA0).value; frame.AddrFrame.Mode = 3
                frame.AddrStack.Offset = C.c_uint64.from_address(ctx + 0x98).value; frame.AddrStack.Mode = 3
                for _ in range(40):
                    if not dbg.StackWalk64(0x8664, hp, h, C.byref(frame), ctx, None, FTA, GMB, None):
                        break
                    if frame.AddrPC.Offset == 0:
                        break
                    addrs.append(frame.AddrPC.Offset)
                if not addrs:
                    addrs = [rip]
            k32.ResumeThread(h)
            walked += 1
            f.write("%d %d %d %s\n" % (now * 1000, tid, d, ",".join("%x" % a for a in addrs)))
        if k32.GetProcessIoCounters(hp, C.byref(io)):
            fio.write("%d %d %d %d\n" % (now * 1000, io.ReadBytes, io.WriteBytes, busy))
        n += 1
        left = step - ((time.perf_counter() - t0) - now)
        if left > 0:
            time.sleep(left)
    mods = modules(hp) or mods
    with open(out + ".modules", "w", encoding="utf-8") as fm:
        fm.write("# pid %d wall0 %.3f ticks %d samples %d secs %.1f\n" % (pid, wall0, n, walked, time.perf_counter() - t0))
        for b, s, p in mods:
            fm.write("%x %x %s\n" % (b, s, p))
    f.close(); fio.close()
    dbg.SymCleanup(hp)
    print("pid %d: %d ticks, %d samples, %d modules, %.1f s" % (pid, n, walked, len(mods), time.perf_counter() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
