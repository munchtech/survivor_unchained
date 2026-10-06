#!/bin/bash
# usage: combat2_exp.sh NAME [ENV=VAL ...]  -> a tier-3 sweep, 8 seeds, table oaths, deft
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/balance
name=$1; shift
env "$@" dotnet bin/probe/Balance.dll arena --callings all --policies greedy,random --seeds ${SEEDS:-8} --tiers ${TIERS:-3} --level tier --oaths table --cap 34 --bot deft --par 22 --out out/$name.jsonl > out/$name.txt 2>&1
python /c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/combat2_t3.py out/$name.jsonl
