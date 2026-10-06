import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot"
E = os.path.join(G, r"logic\Content\Enemies.cs")
FILES = {
E: [
# Pack
('Id = "wolf_howler", Name = "Old Howler"', 'Id = "wolf_howler", Name = "Howler"'),
('Note = "The pack\'s caller. It hangs back and gives tongue', 'Note = "The Pack\'s caller. It hangs back and gives tongue'),
('Id = "mb_blight_mother", Name = "The Blight-Mother"', 'Id = "mb_blight_mother", Name = "Greenbelly"'),
('Note = "Swollen with the slurry and the litter it put in her. Everything about her is green, and everything she leaves is worse." },',
 'Note = "Heavy with a litter, and with the slurry that got into the litter. Everything about her is green, and everything she leaves behind is worse." },'),
('Id = "mb_caller", Name = "The Caller"', 'Id = "mb_caller", Name = "Old Blue"'),
# Risen
('Note = "The ford\'s dead were buried together, and they get up together. Break it and it comes apart into three that walk on." },',
 'Note = "The Legion buried its dead by the file, in one barrow, and they get up the same way. Break it and it comes apart into three that walk on." },'),
('Id = "risen_bell", Name = "Bell-Ringer"', 'Id = "risen_bell", Name = "Horn-Blower"'),
('Aura = new(9, 9, 4, Haste: 1.25, Word: "Bell"),\n            Note = "The Watch rang the ford bell at dusk. One of them still does, and the dead hurry to it." },',
 'Aura = new(9, 9, 4, Haste: 1.25, Word: "Horn"),\n            Note = "The Legion marched to the horn. One of them still blows his, and the dead come quicker to it. Silence it first." },'),
('Id = "mb_old_quarrel", Name = "Old Quarrel"', 'Id = "mb_old_quarrel", Name = "The Scorpion"'),
('Note = "The ford\'s crossbowman. Dead, it shoots five where it once shot one, and it has not forgotten how to keep its distance." },',
 'Note = "The Legion called its bolt-engine a scorpion. This one has carried his for two thousand years and no longer needs it: he looses five where it loosed one, and he has not forgotten how to keep his distance." },'),
('SpawnStyle.Rise, 3, Word: "Shields!"),', 'SpawnStyle.Rise, 3, Word: "Scuta!"),'),
('Note = "A file-leader of the old Legion, still dressing his line. Where he stands, shields come up out of the ground beside him." },',
 'Note = "A decurion of the Seventh, still dressing his line. Where he stands, shields come up out of the ground beside him." },'),
('Id = "mb_drowned_reeve", Name = "The Drowned Reeve"', 'Id = "mb_drowned_reeve", Name = "The Weed-Wife"'),
('Lesson = "The ford\'s cold walks with it. Keep off its wet ground.",\n            Note = "The reeve who kept the ford\'s tolls, drowned in the ford. It still walks the crossing, and the crossing walks with it." },',
 'Lesson = "The river\'s cold walks with her. Keep off her wet ground.",\n            Note = "The river has had her longer than the ford\'s new dead, and the weed has grown through her. She brings the cold up out of the water with her, and it stays where she walks." },'),
('Id = "mb_ford_bell", Name = "The Ford Bell"', 'Id = "mb_ford_bell", Name = "The Signifer"'),
('Aura = new(7, 11, 4.5, Haste: 1.3, Ward: 0.25, Word: "Bell")', 'Aura = new(7, 11, 4.5, Haste: 1.3, Ward: 0.25, Word: "Signa!")'),
('Lesson = "While the bell rings, the dead are quicker and harder to hurt. Silence it.",\n            Note = "The ringer of the ford bell, and the bell. It rings, and the dead come quicker, and the fallen get up to come too." },',
 'Lesson = "While the standard stands, the dead are quicker and harder to hurt. Bring it down.",\n            Note = "The Legion\'s signifer, who carried its standard: VII on a rag that was red once. The dead quicken and harden where it goes, and the fallen get up to follow it." },'),
# Lamplings
('Id = "mb_bombardier", Name = "The Bombardier"', 'Id = "mb_bombardier", Name = "The Chucker"'),
('Id = "mb_fuse_boss", Name = "The Fuse-Boss"', 'Id = "mb_fuse_boss", Name = "The Perfect of Fuses"'),
('Note = "It carries the biggest crate in the Dig, and it has never once put it down. Its lanes burn behind it." },',
 'Note = "It carries the biggest crate in the Dig, and it has never once put it down. Its title is older than the Dig. Its lanes burn behind it." },'),
('Note = "Carries a lit crate of the Boss\'s blasting ember at a run', 'Note = "Carries a lit crate of the Dig\'s blasting ember at a run'),
('Id = "boss_lamplings", Name = "The Ganger"', 'Id = "boss_lamplings", Name = "Gutterwick"'),
# Kerchiefs
('Note = "Ashford\'s levy kept its crossbows when it lost everything else. Three bolts in a fan, and gaps between them wide enough to stand in." },',
 'Note = "The levy kept its crossbows when it lost everything else. Three bolts in a fan, and gaps between them wide enough to stand in." },'),
('Note = "The levy charged with pikes once, at Ashford, and lost. It has been practising since." },',
 'Note = "The levy still drills with its pikes in the ruts below the Roost, every morning, as if it had a town to march for." },'),
('Note = "Led the levy\'s charge at Ashford and came back from it. Nobody else did, and it has not let them forget it." },',
 'Note = "Led the levy\'s pikes the one time it mattered, against something pikes are no use against, and came back. Not many did. It has not let the rest stop drilling since." },'),
('Note = "Carries an actual barn door, and has done since the wagon it came off. It brings it down on whatever stands still." },',
 'Note = "Carries a barn door. The barn it came off is gone, with the farm and the rest of the street, and he will not put down what is left." },'),
('Note = "The levy\'s drum-major, red to the elbows. Where the drum goes the Kerchiefs go, quicker than you would think." },',
 'Note = "The levy\'s drum-major, in red to the elbows, the old colour. Where the drum goes the Kerchiefs go, quicker than you would think." },'),
],
os.path.join(G, r"logic\Maps\MapOffers.cs"): [
('"boss_pack", "The Pack-Mother", "Alpha of the Deep Wood"', '"boss_pack", "The Pack-Mother", "Who Keeps the Den"'),
('"boss_lamplings", "The Ganger", "Foreman of the Deep Dig"', '"boss_lamplings", "Gutterwick", "Second-Best in the Dig"'),
('"boss_kerchiefs", "The Red Hand", "Warlord of the Ravine"', '"boss_kerchiefs", "The Red Hand", "Who Takes What Is Owed"'),
],
os.path.join(G, r"logic\Play\Zones\ArenaRun.cs"): [
('"dead" => ("A drum, twice. The dead set their feet.", "tell_drum"),', '"dead" => ("A horn, twice. The dead set their feet.", "tell_horn"),'),
("""    /// <summary>What the night calls the boss's coming and its middle: a table's by its half hour,
    /// a story's in the story lead's words.</summary>
    string Nears => Spec.Story ? "It is nearly here" : "The half hour nears";
    string Comes => Spec.Story ? "The night's end" : "The half hour";
    string Past => Spec.Story ? "past its coming" : "past the half hour";
    string Middle => Spec.Story ? "Halfway through the dark" : "The fifteenth minute";""",
"""    /// <summary>What every night calls the boss's coming and its middle, in the story lead's one
    /// voice (the valley's idioms are plain truth; this one is).</summary>
    const string Nears = "The dead of night nears", Comes = "The dead of night", Past = "past the dead of night", Middle = "Halfway through the dark";"""),
('$"It will come again in a quarter hour, stronger"', '"It will come again, stronger."'),
],
os.path.join(G, r"tests\ArenaTests.cs"): [
('Assert.Contains(s.Host.Announced, a => a.Title == "The fifteenth minute");', 'Assert.Contains(s.Host.Announced, a => a.Title == "Halfway through the dark");'),
('Assert.Contains(s.Host.Announced, a => a.Kicker == "The night\'s end");', 'Assert.Contains(s.Host.Announced, a => a.Kicker == "The dead of night");'),
],
}
