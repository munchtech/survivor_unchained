#!/bin/bash
# kp.sh CLIP TAG JSON: variant; per frame 4-14: dir.y flat edge.v
cd "$(dirname "$0")"
python x5.py "$1" "$2" "$3" >/dev/null 2>&1 || { echo FAIL $2; exit 1; }
echo "$2 $(python ../solver_atk/atkm.py $1 --folder x/$2 --play idle_reaver --frames 4-14 | tail -11 | awk '{gsub(/\[|\]/," "); print}' | awk '{printf "%s:%s/%s/%s ", $1, $(NF-11), $(NF-9), $(NF-7)}')"
