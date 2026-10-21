# cine6 r3c: his head was cut by the frame top in s3/s5; s10's camera sat inside Grimtunnel's hat lamps.
def edit(shots, f):
    shots["3"]["cam"]["at"]["off"] = [0.2, 2.65, 0.2]
    shots["5"]["cam"]["at"]["off"] = [0.3, 1.75, 0.2]
    shots["10"]["cam"]["pos"]["off"] = [0.3, 1.35, -1.65]
