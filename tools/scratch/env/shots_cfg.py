"""The E1 shot sets (shared by shots.py and sweep.py)."""
HER = ["--quick", "warden", "--sex", "female", "--preset", "own", "--skin", "fair", "--eyes", "moss", "--hair", "braid", "--seed", "7", "--nohud"]
ROAD = "3,64;9,40;0,-38;-2,-72"
# the town: the square, the east road to the toll, the north street (round 3; rounds 0-2: "0,23;3,3;8,-18", the last under a roof's shade)
TOWN = "3,3;24,0;0,-24"
SETS = {
    # camp, road A (by the cart), road B (by the post), the ford, the wood road; then the close view at the fire
    "night": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "-7.5,87.5;" + ROAD + ";-8.6,88.6,1,0"], 6),
    # road B twice, 6 s apart (round 2's frame caught her lightning)
    "roadb": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "0,-38;0,-38;0,-38"], 3),
    # scouting: the wood road at dawn round round 2's spot, and the town's streets
    "woodscout": (["--zone", "lowford", "--facts", "prologue.done=true", "--auto", "idle", "--spots", "-2,-72;-5,-66;1,-78;3,-68;-6,-77"], 5),
    "townscout_dawn": (["--zone", "waystation", "--time", "dawn", "--auto", "idle", "--spots", "0,23;8,-18;24,0;-6,-4;0,-24;10,24"], 6),
    "townscout_day": (["--zone", "waystation", "--time", "day", "--auto", "idle", "--spots", "0,23;8,-18;24,0;-6,-4;0,-24;10,24"], 6),
    # the camp and road B by night only (round 3c checks)
    "camp": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "-7.5,87.5;9,40"], 2),
    "camp3": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "-7.5,87.5;-7.5,87.5;-7.5,87.5"], 3),
    "nightc": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "-7.5,87.5;9,40;0,-38;-8.6,88.6,1,0"], 4),
    # the close view at the fire, four times 6 s apart (her idle breaks change her pose between them)
    "close4": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "-8.6,88.6,1,0;-8.6,88.6,1,0;-8.6,88.6,1,0;-8.6,88.6,1,0"], 4),
    # E2 lamps: the ford's three lamp-irons at the play camera (by the pylons at 0,-33.5, -9.7,-49.6, 9.7,-49.6)
    "ford": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "0,-37;-7,-46;7,-46"], 3),
    # E2 lamps: the camp's post lamp (light 1) mid-frame, for its pool (1 m vs 4 m)
    "pool": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "-3,91;-3,91"], 2),
    "dawn": (["--zone", "lowford", "--facts", "prologue.done=true", "--auto", "idle", "--spots", "-7.5,87.5;" + ROAD], 5),
    "town_dawn": (["--zone", "waystation", "--time", "dawn", "--auto", "idle", "--spots", TOWN], 3),
    "town_day": (["--zone", "waystation", "--time", "day", "--auto", "idle", "--spots", TOWN], 3),
    # E2: the black roof slabs (teaching F10, F11): the Post and the Barrow's crypt by night
    "roofs": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "16,31;-17,4;-22,2"], 3),
}
