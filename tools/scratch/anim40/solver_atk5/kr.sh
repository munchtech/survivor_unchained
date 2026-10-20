#!/bin/bash
# kr.sh CLIP TAG JSON F: build variant; flat/edge (atkm cam45) and m5 at frame F
cd "$(dirname "$0")"; f=${4:-7}
python x5.py "$1" "$2" "$3" >/dev/null 2>&1 || { echo FAIL $2; exit 1; }
a=$(python ../solver_atk/atkm.py $1 --folder x/$2 --play idle_reaver --frames $f-$f | tail -1 | cut -c66-100)
m=$(python m5.py $1 --folder x/$2 --frames $f-$f | tail -1 | cut -c1-120)
echo "$2 |$a| $m"
