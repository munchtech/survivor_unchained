#!/usr/bin/env bash
# Compares the shipped notice files with their upstream sources (ignoring line endings).
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-aab20546fe06daa89/godot/licences
T=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal/up
mkdir -p "$T"
fetch() { curl -sL "$1" -o "$T/$2"; }
fetch https://raw.githubusercontent.com/godotengine/godot/4.5.1-stable/LICENSE.txt GODOT_LICENSE.txt
fetch https://raw.githubusercontent.com/godotengine/godot/4.5.1-stable/COPYRIGHT.txt GODOT_COPYRIGHT.txt
fetch https://raw.githubusercontent.com/dotnet/runtime/release/8.0/LICENSE.TXT DOTNET_LICENSE.TXT
fetch https://raw.githubusercontent.com/dotnet/runtime/release/8.0/THIRD-PARTY-NOTICES.TXT DOTNET_THIRD-PARTY-NOTICES.TXT
for f in GODOT_LICENSE.txt GODOT_COPYRIGHT.txt DOTNET_LICENSE.TXT DOTNET_THIRD-PARTY-NOTICES.TXT; do
  a=$(tr -d '\r' < "$W/$f" | sha256sum | cut -c1-12)
  b=$(tr -d '\r' < "$T/$f" | sha256sum | cut -c1-12)
  if [ "$a" = "$b" ]; then echo "$f same"; else echo "$f DIFFERS ($(wc -c < "$W/$f") vs $(wc -c < "$T/$f") bytes)"; fi
done
for f in OFL-Alegreya.txt OFL-AlegreyaSans.txt OFL-Cinzel.txt; do
  cmp -s <(tr -d '\r' < "$W/$f") <(tr -d '\r' < "$W/../art/fonts/$f") && echo "$f same as art/fonts" || echo "$f DIFFERS from art/fonts"
done
