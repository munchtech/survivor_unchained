import os
from ed import ROOT
P = os.path.join(ROOT, "src/Ui/Forge.cs")
s = open(P, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("\r\n", "\n")
a = s.index("    /// <summary>A craft's press: it does the craft when it can, and while under the pointer or")
b = s.index("    /// <summary>\n    /// A craft as type, two to a row")
s = s[:a] + s[b:]
open(P, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
print("ok")
