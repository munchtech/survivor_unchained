import sys
b = open(sys.argv[1], "rb").read().split(b"\n")
a, z = int(sys.argv[2]), int(sys.argv[3])
cr = [i + 1 for i in range(a - 1, z) if b[i].endswith(b"\r")]
print("CRLF lines in range:", len(cr), "of", z - a + 1, cr[:5], cr[-5:])
