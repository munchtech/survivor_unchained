def edit(shots, f):
    # From his right (the lamp is in his left fist), so the cage does not stand in front of his face.
    shots["3"]["cam"]["pos"] = {"mark": "w", "off": [-0.9, 0.8, 2.2]}
