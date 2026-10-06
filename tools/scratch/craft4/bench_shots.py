"""The two-panel bench, every hand: python bench_shots.py [NAME...] (all when none named)."""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
Q = ["--quick", "warden", "--zone", "waystation"]
SHOTS = {
    "b_brannoc": Q + ["--near", "brannoc", "--met", "brannoc", "--items", "chain_shirt:2:of_the_wolf@1,bone_amulet:2:hale@1+of_the_first_spark@0,wolf_pelt*5,boar_hide*3,old_iron*12,ember_shard*6",
                      "--gold", "400", "--open", "forge:brannoc", "--anvil", "chain_shirt", "--seconds", "5"],
    "b_make": Q + ["--near", "brannoc", "--met", "brannoc", "--items", "wolf_pelt*5,boar_hide*3,old_iron*12", "--gold", "400", "--open", "forge:brannoc", "--make", "--pattern", "iron_helm", "--seconds", "5"],
    "b_vonnra": Q + ["--near", "vonnra", "--met", "vonnra", "--facts", "toll.paid=true", "--items", "mark_hunt_bone:2,chain_shirt:2:of_the_wolf@1,copper_ring:2:searing@2,ember_shard*10",
                     "--gold", "500", "--open", "forge:vonnra", "--anvil", "chain_shirt", "--seconds", "5"],
    "b_snib": Q + ["--near", "snib", "--met", "snib", "--items", "chain_shirt:2:of_the_wolf@1+hale@1,slurry_jar*1", "--gold", "300", "--open", "forge:snib", "--anvil", "chain_shirt", "--seconds", "5"],
    "b_wenna": Q + ["--near", "wenna", "--met", "wenna", "--facts", "stream.clear=true", "--items", "chain_shirt:2:of_the_wolf@1,bitterroot*4,moonpetal*2", "--gold", "300",
                    "--open", "forge:wenna", "--anvil", "chain_shirt", "--seconds", "5"],
    "b_table": Q + ["--charts", "4", "--items", "wolf_pelt*4,ember_shard*6,old_iron*6", "--gold", "300", "--open", "forge:wayfinder", "--seconds", "5"],
}
names = sys.argv[1:] or list(SHOTS)
for n in names:
    r = subprocess.run([sys.executable, os.path.join(HERE, "play.py"), n, "--timeout", "150", "--"] + SHOTS[n], capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[0] if r.stdout.strip() else f"{n}: no output", flush=True)
