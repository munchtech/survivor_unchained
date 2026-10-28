#!/bin/bash
# The Turn measure (docs/design/CLASS_IDENTITY_AND_TALENTS.md 3.3, 6.2; P5a's band x0.90-1.15): each arena twice on the
# same build (the on run replays the off run's cards and chests), no falls, 30 minutes. The skill is carried from the
# first minute at rank 4 (--skillrank); off = its wick without a Turn (the strand's three lead-ins, then Light my way's
# lead-ins), on = the same with the strand's Turn in fourth. Callings that can't carry the skill are dropped.
# turn_measure.sh BALANCE_DLL BOT(deft|plain) SEEDS SEED0 PAR STRAND[@SKILL] OUT.jsonl [more Balance options]
#   e.g. turn_measure.sh bal/Balance.dll deft 24 1 20 wide out/wide_deft.jsonl
#   frost (no skill carries it yet): ... frost@oathblade out/frost_deft.jsonl --strands oathblade=wide/linger/frost
# then: python tools/scratch/classes/turn_ratio.py OUT.jsonl (S = the skill's damage on/off, its crowd and champion
# parts, P = all dealt x taken as the Hand measure reads it, sigma, two disjoint seed halves).
# wicks.json is read at run time from godot/data: a data tune needs no rebuild. ~20 min a Turn x bot at 24 seeds, par 20.
DLL=$1; BOT=$2; N=$3; S0=$4; PAR=$5; TURN=$6; OUT=$7; shift 7
cd "$(dirname "$0")/../../../godot"
time dotnet "$DLL" arena --callings all --tiers 1,2,3,4 --seeds $N --seed0 $S0 --policies greedy --bot $BOT \
  --pair turn:$TURN --nofall 1 --span 30 --par $PAR --out "$OUT" "$@" > "${OUT%.jsonl}.log" 2>&1
python ../tools/scratch/classes/turn_ratio.py "$OUT"
