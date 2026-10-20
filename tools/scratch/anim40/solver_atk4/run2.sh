#!/bin/bash
# run2.sh CLIP TAG JSON: build; motion (skin) line + stm f7
cd "$(dirname "$0")"
python exp.py "$1" "$2" "$3" >/dev/null || exit 1
mo=$(python ../../../anim/motion.py "$1" --folder "x/$2" 2>&1 | tail -1 | awk -F'|' '{print $4}')
st=$(python ../solver_atk3/stm.py "$1" --folder "x/$2" --frames 7-7 2>&1 | tail -1 | cut -c60-)
echo "$2 |$mo| $st | $3"
