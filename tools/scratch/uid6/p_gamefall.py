PAIRS = [
("""            hud.Prompt(new PromptView(controls.UsingPad ? "A" : KeyLabel("interact"), "Get up", "",
                $"{KeyLabel("cancel")}: Let the night go", null, Act.Confirm));""",
"""            // The two choices as type on the darkened world, a click or a key choosing (no prompt box).
            hud.Fall(risesLeft, () => FallKey(Act.Confirm), () => FallKey(Act.Cancel));"""),
("""        fallRise = fallLetGo = null;
        hudMode = null;
        if (scene != null) scene.SimPaused = false;
        hud.Prompt(promptShown = null);""",
"""        fallRise = fallLetGo = null;
        hudMode = null;
        if (scene != null) scene.SimPaused = false;
        hud.Prompt(promptShown = null);
        hud.Fall(null);"""),
]
