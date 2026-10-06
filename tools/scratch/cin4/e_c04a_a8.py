def edit(shots, f):
    s = shots["A8"]
    # The last 3 s crane straight up over her as she walks on, tilting down into the game's view.
    s["cam"]["move"] = {"start": "end-3.0", "ease": "inout", "follow": True}
    s["note"] = ("Low behind her on the road, looking north up the hill: she walks away from camera into the light; "
                 "at the top of the hill the gate stands open. Her own body from the cut (play). Over the last 3 s the "
                 "camera cranes up over her, tilting down into the game's view; she walks on into play. Bars out over the last 0.8 s; then the Douse announcement and the day tip.")
