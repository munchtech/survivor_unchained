# Send superseded raw shoots to the Recycle Bin (CLAUDE.md rule 6b). The one bin step agents run
# without a prompt (allow rule in .claude/settings.json, the owner's yes, 16 Nov 2026). Call it by
# its absolute path, alone (not chained with && or ;), so the rule matches:
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:/Users/munch/Desktop/survivorsunchained/tools/scratch/coordinator/to_bin.ps1 <path> [<path> ...] [-DryRun]
# Refuses, per path, anything that:
#   - is missing;
#   - is not inside survivorsunchained_inputs at depth 2 or more (inputs\<lane folder>\<something>),
#     or inside a godot\.shots folder of the main checkout or of a .claude\worktrees\<name> worktree;
#   - is a link, sits under a link, or holds a link (junction or symlink) anywhere inside;
#   - holds a state, handoff or provenance file (*state*.md, HANDOFF*.md, PROVENANCE*).
# Never deletes for good: the bin only (the owner empties it). Prints MB per path and the total.
param(
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$Paths,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName Microsoft.VisualBasic
$inputs = 'C:\Users\munch\Desktop\survivorsunchained_inputs'
$repo = 'C:\Users\munch\Desktop\survivorsunchained'
$shotsRe = '^' + [regex]::Escape($repo) + '(\\\.claude\\worktrees\\[^\\]+)?\\godot\\\.shots(\\.+)?$'
$protect = @('*state*.md', 'HANDOFF*.md', 'PROVENANCE*')
$total = 0.0; $bad = 0

function Test-Link([string]$p) {
    $i = Get-Item -LiteralPath $p -Force
    return [bool]($i.Attributes -band [IO.FileAttributes]::ReparsePoint)
}

foreach ($raw in $Paths) {
    if ($raw -eq '-DryRun') { continue }
    try {
        if (-not (Test-Path -LiteralPath $raw)) { throw 'missing' }
        $p = (Resolve-Path -LiteralPath $raw).Path.TrimEnd('\')
        $base = $null
        if ($p.StartsWith($inputs + '\', [StringComparison]::OrdinalIgnoreCase)) {
            $rel = $p.Substring($inputs.Length + 1)
            if (@($rel.Split('\') | Where-Object { $_ }).Count -lt 2) { throw 'a top-level inputs folder: bin what is inside it, not the folder' }
            $base = $inputs
        } elseif ($p -match $shotsRe) {
            $base = $p.Substring(0, $p.IndexOf('\godot\.shots', [StringComparison]::OrdinalIgnoreCase))
        } else {
            throw 'not under survivorsunchained_inputs or a godot\.shots folder'
        }
        # the target and every folder between it and its base: no links
        $x = $p
        while ($x.Length -gt $base.Length) {
            if (Test-Link $x) { throw "link at $x" }
            $x = [IO.Path]::GetDirectoryName($x)
        }
        $item = Get-Item -LiteralPath $p -Force
        if ($item.PSIsContainer) {
            if (@(Get-ChildItem -LiteralPath $p -Recurse -Force -Attributes ReparsePoint -ErrorAction SilentlyContinue).Count) { throw 'holds a link' }
            $files = @(Get-ChildItem -LiteralPath $p -Recurse -Force -File -ErrorAction SilentlyContinue)
        } else {
            $files = @($item)
        }
        foreach ($pat in $protect) {
            $hit = @($files | Where-Object { $_.Name -like $pat } | Select-Object -First 1)
            if ($hit.Count) { throw "holds a kept file: $($hit[0].FullName)" }
        }
        $mb = [math]::Round((($files | Measure-Object Length -Sum).Sum) / 1MB, 1)
        if ($DryRun) { "would bin $mb MB  $p"; $total += $mb; continue }
        if ($item.PSIsContainer) {
            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($p, 'OnlyErrorDialogs', 'SendToRecycleBin')
        } else {
            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($p, 'OnlyErrorDialogs', 'SendToRecycleBin')
        }
        if (Test-Path -LiteralPath $p) { throw 'still there after the bin call' }
        "binned $mb MB  $p"
        $total += $mb
    } catch {
        "REFUSED  $raw  ($($_.Exception.Message))"
        $bad++
    }
}
"total $([math]::Round($total / 1024, 2)) GB$(if ($DryRun) { ' (dry run)' }); refused $bad"
if ($bad) { exit 1 }
