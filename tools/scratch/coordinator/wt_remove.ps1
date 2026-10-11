# Remove a finished agent worktree safely (CLAUDE.md, "Disk and worktrees").
#   powershell -NoProfile -File tools/scratch/coordinator/wt_remove.ps1 <worktree path> [-Force]
# Links (junctions, symlinks) inside it are removed first, the link only, so no delete can
# follow one into real assets (some worktrees linked godot/assets into the main checkout).
# -Force only when its uncommitted edits were checked and are discarded on purpose.
# Long paths: git can unregister a worktree and still fail on deep files ("Filename too long");
# the leftover folder is then removed with a long-path-aware delete, never sent to the bin.
param([Parameter(Mandatory=$true)][string]$Path, [switch]$Force)
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\munch\Desktop\survivorsunchained'
$root = Join-Path $repo '.claude\worktrees'
$p = (Resolve-Path -LiteralPath $Path).Path.TrimEnd('\')
if (-not $p.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "not under $root : $p" }
foreach ($l in @(Get-ChildItem -LiteralPath $p -Recurse -Force -Attributes ReparsePoint -ErrorAction SilentlyContinue)) {
    if ($l.PSIsContainer) { [System.IO.Directory]::Delete($l.FullName, $false) } else { [System.IO.File]::Delete($l.FullName) }
    "link removed: $($l.FullName) -> $($l.Target)"
}
if (@(Get-ChildItem -LiteralPath $p -Recurse -Force -Attributes ReparsePoint -ErrorAction SilentlyContinue).Count) { throw "links remain in $p" }
$args2 = @('-C', $repo, '-c', 'core.longpaths=true', 'worktree', 'remove')
if ($Force) { $args2 += '--force' }
& git @args2 $p
$registered = (& git -C $repo worktree list --porcelain) -match [regex]::Escape(($p -replace '\\', '/'))
if ((Test-Path -LiteralPath $p) -and -not $registered) {
    Remove-Item -LiteralPath ('\\?\' + $p) -Recurse -Force
}
if (Test-Path -LiteralPath $p) { "STILL THERE: $p" } else { "removed: $p" }
& git -C $repo worktree prune
