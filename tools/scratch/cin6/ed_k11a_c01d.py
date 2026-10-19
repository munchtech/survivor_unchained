# k11a pass 4 (C01 s3): lens at her eye level (pass 3 sat 16 cm under the head bone and framed her chin and throat).
def edit(shots, f):
    c = shots["3"]["cam"]
    c["pos"] = {"actor": "her", "bone": "eyes", "off": [-0.42, 0.0, -0.36]}
    c["at"] = {"actor": "her", "bone": "eyes", "off": [0, -0.02, 0]}
    c["lens"] = 65
