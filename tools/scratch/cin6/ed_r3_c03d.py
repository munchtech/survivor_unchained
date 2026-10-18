# Lead: sunk 0.55 m, his head is below any camera at her eye height and the hat's brim hides his face.
# The cameras come down to his eye line (a low cheat on "down at him"), each 30-40 deg off his facing.
def edit(shots, f):
    shots["9"]["cam"]["pos"] = {"mark": "her", "off": [2.6, 0.9, 1.6]}
    shots["9"]["cam"]["at"] = {"mark": "her", "off": [0.6, 1.0, -0.3]}
    shots["10"]["cam"]["pos"] = {"mark": "her", "off": [1.3, 0.85, 1.4]}
    shots["10"]["cam"]["at"] = {"mark": "her", "off": [1.0, 0.8, -0.5]}
    shots["10"]["cam"]["lens"] = 40
    shots["11"]["cam"]["pos"] = {"mark": "her", "off": [2.0, 0.85, -2.9]}
    shots["11"]["cam"]["at"] = {"mark": "her", "off": [0.7, 0.9, -0.4]}
