"""Plain words for the look in every prompt: no product or artist named (the legal lead's ask)."""
import os

T = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools"
EDITS = {
    r"comfy\concepts.py": [("dramatic rim lighting, Diablo and Baldur's Gate art style. ",
                            "dramatic rim lighting, grounded gritty dark fantasy realism with painterly brushwork. ")],
    r"comfy\ui_concepts.py": [("hand-painted, AAA game UI in the style of \"\n         \"Diablo IV and Hades, crisp edges",
                               "hand-painted, AAA game UI with \"\n         \"painterly brushwork and deep shadow, crisp edges")],
    r"comfy\ui_assets.json": [("AAA game UI art in the style of Diablo IV and Hades, crisp edges",
                               "AAA game UI art with painterly brushwork and deep shadow, crisp edges"),
                              ("no frame, no text, in the style of Diablo IV skill icons.",
                               "no frame, no text, painterly brushwork, ember glow."),
                              ("no frame, no text, in the style of Diablo IV item icons.",
                               "no frame, no text, painterly brushwork.")],
    r"uiforge\explore.py": [("hand painted in the style of Diablo IV skill icons, ",
                             "hand-painted with painterly brushwork, ")],
    r"uiforge\items.py": [("hand painted in the style of Diablo IV item icons, the object alone, ",
                           "hand-painted with painterly brushwork, the object alone, ")],
    r"uiforge\icons.py": [("for a dark fantasy game skill icon, in the style of Diablo IV skill icons, hand painted, ",
                           "for a dark fantasy game skill icon, hand-painted with painterly brushwork, ")],
    r"uiforge\emblems.py": [("for a dark fantasy game skill icon, in the style of Diablo IV skill icons, hand painted, ",
                             "for a dark fantasy game skill icon, hand-painted with painterly brushwork, ")],
}
for rel, pairs in EDITS.items():
    p = os.path.join(T, rel)
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:50], s.count(a))
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(s)
    print("ok", rel)
