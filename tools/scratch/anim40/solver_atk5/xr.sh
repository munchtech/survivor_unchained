#!/bin/bash
# xr.sh CLIP TAG JSON [frame]: variant build; m5 at the frame standing and worst over the run
cd "$(dirname "$0")"; f=${4:-7}
python x5.py "$1" "$2" "$3" >/dev/null 2>&1 || { echo FAIL; exit 1; }
s=$(python m5.py $1 --folder x/$2 --frames $f-$f | tail -1); r=$(python m5.py $1 --folder x/$2 --frames $f-$f --base run_reaver --bf all | tail -1)
echo "$2 S$s"; echo "$2 R$r"
