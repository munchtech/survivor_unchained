# Make a lead's worktree the safe way (CLAUDE.md "Disk and worktrees", README junction DANGER):
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/wt_new.ps1 <name> [<start-ref>]
# 1. git worktree add .claude/worktrees/<name> -b <name> <start-ref>   (default: the integration branch HEAD)
# 2. godot/assets is a tracked symlink (120000) that Windows checks out as a text file: replace it with a
#    JUNCTION to the worktree's OWN public/assets (never the main checkout's), and assume-unchanged it.
# 3. Seed godot/.godot/imported from the main checkout (3.3 GB, seconds): a fresh worktree without it
#    throws NREs in shots and a full --import can take an hour. The lead still runs `--import` once (~2 min).
# Refuses at the cap (8 worktrees on disk).
param(
  [Parameter(Mandatory=$true)][string]$Name,
  [string]$StartRef = "claude/vigilant-galileo-l6jqyx",
  # A code-only lane (dotnet test, no Godot shots) does not need the 3.3 GB imported cache:
  # skip it and the worktree costs about 5 GB instead of 9. Never pass it for a lane that
  # shoots pictures or renders; a fresh --import there would take an hour.
  [switch]$NoImport
)
$ErrorActionPreference = "Stop"
$Main = "C:\Users\munch\Desktop\survivorsunchained"
Set-Location $Main
$count = (git worktree list | Measure-Object -Line).Lines
if ($count -ge 8) { Write-Error "worktree cap: $count on disk (CLAUDE.md rule 3); remove merged ones first (wt_audit.py)"; exit 1 }
$wt = Join-Path $Main ".claude\worktrees\$Name"
if (Test-Path $wt) { Write-Error "$wt exists"; exit 1 }
git worktree add $wt -b $Name $StartRef
if ($LASTEXITCODE -ne 0) { exit 1 }
$assets = Join-Path $wt "godot\assets"
if (Test-Path $assets) { Remove-Item -Force $assets }   # the checked-out symlink text file, never a folder
$own = Join-Path $wt "public\assets"
if (-not (Test-Path $own)) { Write-Error "no $own in the worktree"; exit 1 }
cmd /c mklink /J "$assets" "$own" | Out-Null
git -C $wt update-index --assume-unchanged godot/assets
$src = Join-Path $Main "godot\.godot\imported"
$dst = Join-Path $wt "godot\.godot\imported"
if ($NoImport) { Write-Output "imported cache NOT seeded (-NoImport): code lane, dotnet test only" }
elseif (Test-Path $src) { robocopy $src $dst /E /MT:8 /NFL /NDL /NJH /NJS /NP | Out-Null }
$head = git -C $wt rev-parse --short HEAD
Write-Output "worktree $wt on branch $Name @ $head; junction godot\assets -> own public\assets; imported cache seeded"
