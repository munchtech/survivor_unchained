def edit(shots, f):
    s = shots["B1"]
    # From 5 m the near roofs hide the toll tower; from 12 m it stands on the right
    # with the lamp in its window, and the crane comes down into the street as she passes under.
    s["cam"] = {"pos": [0.0, 12.0, 38.0], "at": [10.0, 5.0, -8.0], "lens": 24,
                "move": {"pos": [0.0, 1.8, 36.0], "at": [6.0, 4.0, -8.0], "ease": "slow"}}
    s["note"] = ("Crane down from 12 m to 1.8 m just inside the south gate, looking north up the road: roofs, a dozen "
                 "chimneys smoking straight up, the square, the well; right, on the skyline, the toll tower, and in its "
                 "upper window, very small, a lamp still burning, pale in daylight (the roofs take it as the crane comes "
                 "down). She walks in under the camera and on up the road. N7. Title: CHAPTER ONE / The Waystation.")
