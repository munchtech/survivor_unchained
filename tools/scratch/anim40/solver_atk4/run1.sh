#!/bin/bash
# run1.sh CLIP TAG JSON : build, then summarise contact max (f3-16) and stm at the finish frames
cd "$(dirname "$0")"
python exp.py "$1" "$2" "$3" >/dev/null || exit 1
pfo=$(python pf.py "$1" --folder "x/$2" --outfits reaver 2>&1 | awk 'NR>1{for(i=2;i<=5;i++) if($i>m[i]) m[i]=$i; if($7>m[7]) m[7]=$7} END{printf "up%d fa%d hd%d br%d rea%d", m[2],m[3],m[4],m[5],m[7]}')
st=$(python ../solver_atk3/stm.py "$1" --folder "x/$2" --frames 7-7 2>&1 | tail -1 | cut -c20-)
echo "$2 | $pfo | $st | $3"
