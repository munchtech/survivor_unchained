#!/usr/bin/env bash
# Desktop builds of the Godot game, into release/godot/<platform>/.
#
#   tools/godot/export.sh [windows|linux|macos|all]    (default: all)
#   tools/godot/export.sh windows-demo   the demo testers download (preset "Windows Demo", feature demo) and its
#                                        proof twin ("Windows Demo (proof)", + perf: the autopilot's switches are read),
#                                        then release/godot/SurvivorUnchained_Demo_<yyyymmdd>_<sha>.zip (the demo alone)
#
# Needs Godot's export templates (tools/godot/setup.sh --templates). Each
# build is a release build: the C# compiled optimised, the .pck beside it.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$("$ROOT/tools/godot/setup.sh")}"
export GODOT_NUPKGS="$(dirname "$GODOT")/GodotSharp/Tools/nupkgs"
# Godot's SDK packages ship with the engine: a package source for this
# machine (the project asks nuget.org alone, so it builds anywhere, the
# Godot editor on another computer included).
dotnet nuget list source 2>/dev/null | grep -qF "$GODOT_NUPKGS" || dotnet nuget add source "$GODOT_NUPKGS" --name godot-sdk >/dev/null
cd "$ROOT/godot"
want="${1:-all}"
build() {
  local preset="$1" dir="$2" file="$3"
  rm -rf "$ROOT/release/godot/$dir"
  mkdir -p "$ROOT/release/godot/$dir"
  echo "exporting $preset..."
  local log="$ROOT/release/godot/$dir.log"
  "$GODOT" --headless --path . --export-release "$preset" "$ROOT/release/godot/$dir/$file" >"$log" 2>&1 || true
  grep -E "ERROR|WARNING" "$log" | grep -v "RID allocations\|resources still in use" || true
  # A failed C# build still leaves an executable behind: that is no build.
  if grep -q "Failed to build project" "$log" || [ ! -e "$ROOT/release/godot/$dir/$file" ]; then
    echo "no $preset build (see release/godot/$dir.log)" >&2; exit 1
  fi
  # The licence texts and credits go beside the game (docs/legal/LEGAL_BRIEF.md, issue 4).
  mkdir -p "$ROOT/release/godot/$dir/licences"
  cp "$ROOT/godot/licences/"* "$ROOT/release/godot/$dir/licences/"
  echo "  release/godot/$dir/$file"
}
# The build's stamp (BugReporter reads res://data/build.json into each report; git-ignored, rewritten each export).
stamp() {
  local sha; sha="$(git -C "$ROOT" rev-parse --short=9 HEAD)"
  git -C "$ROOT" diff --quiet HEAD -- godot || sha="$sha+dirty"
  printf '{ "sha": "%s", "flavor": "%s", "date": "%s" }\n' "$sha" "$1" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >"$ROOT/godot/data/build.json"
}
# The demo's zip: the exe, the .pck, the .NET data folder, the licences, README.txt (tools/godot/demo_README.txt).
demo_zip() {
  local dir="$ROOT/release/godot/windows-demo"
  cp "$ROOT/tools/godot/demo_README.txt" "$dir/README.txt"
  local name="SurvivorUnchained_Demo_$(date +%Y%m%d)_$(git -C "$ROOT" rev-parse --short=9 HEAD).zip"
  rm -f "$ROOT/release/godot/$name"
  python "$ROOT/tools/godot/zip_dir.py" "$dir" "$ROOT/release/godot/$name" SurvivorUnchained_Demo
  echo "  release/godot/$name ($(du -h "$ROOT/release/godot/$name" | cut -f1))"
}
# The first export imports anything new.
"$GODOT" --headless --path . --import >/dev/null 2>&1 || true
case "$want" in
  windows-demo) stamp demo; build "Windows Demo" windows-demo SurvivorUnchained.exe; build "Windows Demo (proof)" windows-demo-proof SurvivorUnchained.exe; demo_zip; exit 0 ;;
esac
stamp full
case "$want" in
  windows|all) build "Windows" windows SurvivorUnchained.exe ;;&
  linux|all) build "Linux" linux SurvivorUnchained.x86_64 ;;&
  macos|all) build "macOS" macos SurvivorUnchained.zip ;;
esac
