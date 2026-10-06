PAIRS = [
("""        if (Args.Get("sex") == "female") draft.Sex = Sex.Female;""", """        if (Args.Get("sex") == "female") draft.Sex = Sex.Female;
        else if (Args.Get("sex") == "male") draft.SetSex(Sex.Male);"""),
]
