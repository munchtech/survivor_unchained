#!/bin/bash
# Usage: look.sh TAG  -> builds, shoots four scenes into godot/.shots/TAG_*.png
cd /c/Users/munch/Desktop/survivorsunchained/godot || exit 1
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
dotnet build SurvivorUnchained.csproj -v q -nologo 2>&1 | grep -E " error |Error\(s\)" | head -5
T=${1:-look}
shot(){ n=$1; shift; "$G" --path . -- "$@" --shot ${T}_$n > /tmp/look_$n.log 2>&1; grep -i "exception" /tmp/look_$n.log | head -3; }
shot vnight --quick reaver --zone verge --time night --seconds 6 &
shot vday --quick reaver --zone verge --time day --seconds 6 &
wait
shot arena --quick arcanist --zone arena --people dead --auto --seconds 25 &
shot town --quick warden --zone waystation --time day --seconds 6 &
wait
ls .shots | grep "^${T}_"
