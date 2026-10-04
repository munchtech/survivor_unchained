"""Before and after, side by side, for every screen (docs/ui_review/<screen>.jpg).

Three columns: the game as it was before the interface work began, after the
first pass (which kept the old shapes), and after the second pass (each
screen recomposed from first principles). Screenshots come from
godot/.shots (made with the game's --shot hook); a missing one leaves its
column blank and says so.

    python tools/comfy/ui_review.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "godot" / ".shots"
OUT = ROOT / "docs" / "ui_review"
# The game's face, as the concept tool converted it (tools/comfy/out is not kept in git).
FONT = ROOT / "tools" / "comfy" / "out" / "ui_concepts" / "alegreya-sans-700.ttf"

# screen: (title, original, first pass, second pass)
SCREENS = {
    "hud_night": ("The HUD at night (an arena)", "before_arena", "after_arena", "v2_arena"),
    "hud_day": ("The HUD by day (the Verge)", "before_hud_verge_day", "after_hud_verge_day", "v2_hud_verge"),
    "hud_town": ("The HUD at peace (the Waystation)", "before_town_day", "after_town_day", "v2_hud_town"),
    "pack": ("Pack", "before_inventory_00", "after_pack", "v2_pack"),
    "self": ("Self", "before_character_00", "after_self", "v2_self"),
    "arts": ("Arts: the art in hand", "before_arts_00", "after_arts_pad", "v2_arts"),
    "skills": ("Arts: skills by day", "before_arts_00", "after_arts_pad", "v2_skills"),
    "journal": ("Journal: quests", "before_journal_00", "after_journal", "v2_journal"),
    "people": ("Journal: people", "before_journal_00", "after_people", "v2_journal_people"),
    "map": ("Map", "before_map_00", "after_map_town", "v2_map"),
    "draft": ("The draft", "before_draft_00", "after_draft", "v2_draft"),
    "talk": ("Conversation", "before_talk", "after_talk", "v2_talk"),
    "shop": ("Shop", "before_shop", "after_shop", "v2_shop"),
    "stash": ("Storeroom", "before_stash", "after_stash", "v2_stash"),
    "title": ("Title", "before_title", "after_title", "v2_title"),
    "create": ("Making a survivor", "before_create", "after_create", "v2_create"),
    "create_name": ("Making a survivor: name and look", "before_create", "after_create", "v2_create_name"),
    "pause": ("Pause", "before_pause_00", "after_pause_pad", "v2_pause"),
    "settings": ("Pause: settings", "before_pause_00", "after_pause_pad", "v2_pause_settings"),
    "result": ("The arena's end", "before_result", "after_result", "v2_result"),
    "table": ("The Wayfinder's table", "before_table", "after_table", "v2_table"),
    "rest": ("The Last Lamp", "before_rest", "after_rest", "v2_rest"),
    "chapter": ("The chapter's end", "before_chapter_00", "after_chapter", "v2_chapter"),
}
LABELS = ("Before the interface work", "First pass (the old shapes)", "Second pass (recomposed)")
W, H, BAND = 960, 540, 56


def find(name: str) -> Path | None:
    for cand in (SHOTS / f"{name}.png", SHOTS / f"{name}_00.png"):
        if cand.exists():
            return cand
    return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(FONT), 26) if FONT.exists() else ImageFont.load_default()
    head = ImageFont.truetype(str(FONT), 30) if FONT.exists() else ImageFont.load_default()
    for key, (title, *names) in SCREENS.items():
        sheet = Image.new("RGB", (W * 3 + 16, H + BAND * 2), (14, 12, 18))
        d = ImageDraw.Draw(sheet)
        d.text((16, 12), title, font=head, fill=(243, 217, 160))
        for i, (name, label) in enumerate(zip(names, LABELS)):
            x = i * (W + 8)
            d.text((x + 12, BAND + H + 12), label, font=font, fill=(255, 208, 122) if i == 2 else (200, 190, 170))
            path = find(name)
            if path is None:
                d.text((x + 40, BAND + H // 2), f"no picture ({name})", font=font, fill=(120, 110, 100))
                continue
            im = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
            sheet.paste(im, (x, BAND))
        sheet.save(OUT / f"{key}.jpg", quality=86)
        print(key)


if __name__ == "__main__":
    main()
