#!/usr/bin/env bash
# Desktop builds of the Godot game, into release/godot/<platform>/.
#
#   tools/godot/export.sh [windows|linux|macos|all]    (default: all)
#
# Needs Godot's export templates (tools/godot/setup.sh --templates). Each
# build is a release build: the C# compiled optimised, the .pck beside it.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$("$ROOT/tools/godot/setup.sh")}"
# Godot's own SDK packages, for the C# build (see godot/nuget.config).
export GODOT_NUPKGS="$(dirname "$GODOT")/GodotSharp/Tools/nupkgs"
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
  echo "  release/godot/$dir/$file"
}
# The first export imports anything new.
"$GODOT" --headless --path . --import >/dev/null 2>&1 || true
case "$want" in
  windows|all) build "Windows" windows SurvivorUnchained.exe ;;&
  linux|all) build "Linux" linux SurvivorUnchained.x86_64 ;;&
  macos|all) build "macOS" macos SurvivorUnchained.zip ;;
esac
