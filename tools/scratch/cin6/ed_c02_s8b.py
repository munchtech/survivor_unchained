def edit(shots, f):
    cam = shots["8"]["cam"]
    # His lamp-iron's shaft stood in front of the lens at frame left as a hard black band:
    # the camera goes round to her left three-quarter, the lamp and its shaft behind her head, so the shaft and lamp fall outside the left edge; wider (her lips in frame, as the note asks).
    cam["pos"]["off"] = [0.40, -0.03, -0.95]
    cam["at"]["off"] = [0, -0.03, 0]
    cam["lens"] = 100
