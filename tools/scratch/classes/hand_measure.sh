#!/bin/bash
# The Hand measure (docs/design/CLASS_IDENTITY_AND_TALENTS.md 2.2 item 1, 6.2): every calling, tiers 1-4, each arena
# played with the Hand off, then on replaying the off run's cards and chests at their minutes, no falls, 30 minutes.
# hand_measure.sh BALANCE_DLL BOT(deft|plain) SEEDS SEED0 OUT.jsonl [more Balance options]
# then: python tools/scratch/classes/hand_ratio.py OUT.jsonl  (per calling x tier: on/off damage, sigma)
# hands.json is read at run time from godot/data: a data tune needs no rebuild.
DLL=$1; BOT=$2; N=$3; S0=$4; OUT=$5; shift 5
cd "$(dirname "$0")/../../../godot"
time dotnet "$DLL" arena --callings all --tiers 1,2,3,4 --seeds $N --seed0 $S0 --policies greedy --bot $BOT \
  --pair 1 --nofall 1 --span 30 --par 20 --out "$OUT" "$@" > "${OUT%.jsonl}.log" 2>&1
python ../tools/scratch/classes/hand_ratio.py "$OUT"
