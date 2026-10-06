"""A6 camera variants on her left side (mkt.py)."""
ONLY = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
V = {"A6": [
    {"id": "A6b", "cam": {"pos": {"actor": "her", "bone": "eyes", "off": [-1.0, -0.05, -1.45]}, "at": {"actor": "her", "bone": "eyes", "off": [0, -0.1, 0]},
                          "lens": 50, "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 2.8}},
    {"id": "A6c", "cam": {"pos": {"actor": "her", "bone": "eyes", "off": [-0.45, 0.02, -1.3]}, "at": {"actor": "her", "bone": "eyes", "off": [0, -0.08, 0]},
                          "lens": 65, "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 2.8}},
]}
