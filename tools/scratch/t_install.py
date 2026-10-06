import sys, os
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import rounds, plates, cards
UI = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\art\ui"
RAW = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge"
os.makedirs(UI + r"\hud", exist_ok=True)
rounds.fit_round(RAW + r"\medal\medal_31.png", 140, rim_at=0.98, calm_below=0.5, ember_rim=0.6).save(UI + r"\hud\medal_level.png")
rounds.fit_round(RAW + r"\many1\medal_heart_321_0.png", 128, rim_at=0.98).save(UI + r"\hud\medal_heart.png")
rounds.fit_round(RAW + r"\many1\ring_art_322_0.png", 220, rim_at=0.99, open_below=0.78).save(UI + r"\hud\ring_art.png")
plates.fit(RAW + r"\plate_v2\plate_v2_511_0.png", UI + r"\frames\plate.png")
