bash /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40/tools/scratch/anim40/solver_atk7c/t9.sh "$1" "$2" | head -2
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40/tools/anim
python motion.py run_reaver_axes --outfits 2>&1 | grep -v "body ready" | sed 's/ r: up.*vol/ | vol/'
python ../scratch/anim40/solver_atk7c/wb.py run_reaver_axes | tail -1
