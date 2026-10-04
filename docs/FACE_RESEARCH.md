# Facial attractiveness: what the science says, and what it means for her face

The research behind the heroine's default face, her face sliders and her pre-made faces (docs/team/face.md). The owner asked for this: "look up beauty science and proportions and fix that stuff".

## 1. What holds up

### Averageness
- **Finding.** Faces averaged from many faces are rated more attractive than almost every face that went into them, and more so the more faces are averaged. ([Langlois & Roggman 1990](https://digitalcommons.usu.edu/fchd_facpub/237))
- **Why it matters.** An average face is free of oddities: no single feature is out of proportion.
- **The limit.** Average is attractive but not the most attractive. The averaged shape of the *most attractive* faces beats the average of all of them, and exaggerating how it differs from the average makes it better still. Observers in Japan and Britain agreed on this. ([Perrett, May & Yoshikawa 1994, *Nature*](https://research-portal.st-andrews.ac.uk/en/publications/facial-shape-and-judgements-of-female-attractiveness/))
- **A later model.** Averageness is attractive along some face dimensions and not others. A model that moves a face in the right direction away from the average predicts attractiveness far better than averageness or sexual dimorphism alone. ([Said & Todorov 2011](https://collaborate.princeton.edu/en/publications/a-statistical-model-of-facial-attractiveness/))
- **For us:**
  - Her own face sits near the attractive average: no feature extreme.
  - Every slider runs *away* from that centre. Its middle is the safe, beautiful face.
  - Presets differ from each other by bone structure, never by oddity.

### Symmetry
- Symmetry, averageness and sexual dimorphism are the three well-supported, cross-cultural cues. ([Rhodes 2006](https://homepages.uc.edu/~martinj/Taste%20Food%20&%20Wine/Aesthetics_of_Food_&_Drink/Rhodes%20-%20Evolutions%20of%20Facial%20Beauty.pdf); [Little, Jones & DeBruine 2011](https://eprints.gla.ac.uk/77707); [Jones 2019](https://cronfa.swan.ac.uk/Record/cronfa48959/Details))
- **For us:** her face is mirror-symmetric, and every slider moves both sides alike. A little asymmetry belongs to the skin paint (freckles, a mole), not the bones.

### Feminine cues
Femininity in a woman's face is preferred above the average, across cultures ([Perrett et al. 1994](https://research-portal.st-andrews.ac.uk/en/publications/facial-shape-and-judgements-of-female-attractiveness/); [Rhodes 2006](https://homepages.uc.edu/~martinj/Taste%20Food%20&%20Wine/Aesthetics_of_Food_&_Drink/Rhodes%20-%20Evolutions%20of%20Facial%20Beauty.pdf)). [Cunningham (1986)](https://genepi.qimr.edu.au/contents/p/staff/1986_Cunningham_FacialBeauty_Pers&SocialPsych925-935.pdf) measured 24 features in 50 women's faces against men's ratings, and found three kinds of feature that raise attractiveness:
- **Neonate features:** large eyes, a small nose and a small chin.
- **Mature features:** prominent cheekbones and narrow cheeks.
- **Expressive features:** high brows, large pupils and a large smile.

Raters from different ethnic groups agree strongly on which women's faces are attractive ([Cunningham et al. 1995](https://itts023d.itts.ttu.edu/ordb/Data/70248)). The cues hold across ethnicity, though the details vary.

What each cue means for her face:

| Cue | Evidence | Her face |
|---|---|---|
| **Eyes** large | Cunningham 1986 | Eyes a touch larger than MakeHuman's woman. *Size* slider: both ways, but more room upward. |
| **Eye spacing** near average | Interocular distance ≈ 46% of face width at the eyes is most attractive, and this is the average ([Pallett, Link & Lee 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2814183)) | *Set* slider centred on that; ends tasteful. |
| **Eyes to mouth** near average | Vertical eye-to-mouth distance ≈ 36% of face length (hairline to chin) is most attractive (Pallett et al. 2010) | Mouth height, nose length and chin length all move this. Her own face sits at about 36%. |
| **Canthal tilt** positive | Faces with a more upward medial-to-lateral eye axis were preferred 93% of the time (Bashour & Geist 2007, via [Eppley](https://www.eppleyplasticsurgery.com/attractive-eyes)) | A slight upward tilt by default. *Tilt* slider. |
| **Nose** small and narrow | Cunningham 1986 | Narrow bridge, refined tip. *Width*, *Length*, *Tip*, *Bridge* sliders. |
| **Lips** full | Lip fullness is a feminine and youthful cue. The most attractive upper:lower ratio was 1:1.6 in one study ([Heidekrueger 2017](https://www.egms.de/static/en/meetings/dgpraec2017/17dgpraec103.shtml)) and about 1:2 in another ([Popenko 2017](https://www.newswise.com/articles/what-are-the-most-attractive-lips-more-attention-doesn-t-mean-most-beautiful)); 2:1 was rated low | Lower lip fuller than the upper by default. Upper and lower lip sliders kept separate, plus mouth width. |
| **Cheekbones** high and prominent, **cheeks** narrow | Cunningham 1986 | *Cheekbone height*, *width* and *prominence*, and *cheek fullness*, each its own slider. |
| **Jaw and chin** narrow, chin small | Cunningham 1986; a narrow lower face reads feminine | A tapered jaw by default. *Jaw width*, *jaw angle*, *chin width* (now able to go much narrower), *chin length* and *chin projection*. |
| **Brows** high | Cunningham 1986 | *Brow height* slider. Brow ridge soft by default (a heavy ridge is a male cue). |
| **Neck** slender | A thick neck is a male cue | Slimmer by default (heroine_head.py BUILD). *Neck width* and *length*. |
| **Midface** compact | Pupil-to-lip distance about equal to the interpupillary distance reads well ([Perfect Corp midface ratio](https://www.perfectcorp.com/business/blog/general/midface-ratio)) | Nose length and mouth height keep it compact. This is a popular rule of thumb rather than primary research, so it is used only as a check. |

## 2. Thirds, fifths and the golden ratio: what is myth

- **Thirds and fifths** are the neoclassical canons:
  - thirds: hairline to brows, brows to nose base, nose base to chin, all equal;
  - fifths: the face five eye-widths across.

  Modern measurement finds that attractive people rarely fit them. The lower third is usually longer than the middle. ([Al-Sebaei 2015](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4369102/), with Farkas's earlier work.) They are a sketching guide, not a beauty law. We use them only to sanity-check that no slider end makes one third grotesque.
- **The golden ratio (1.618) and Marquardt's mask** are not supported:
  - The mask's goodness-of-fit method is faulty.
  - It fits non-European faces poorly.
  - It matches *masculinised* European women's faces, against the public's clear preference for femininity. ([Holland 2008, *Aesthetic Plastic Surgery*](https://link.springer.com/doi/10.1007/s00266-007-9080-z))
  - The "new golden ratios" that do predict attractiveness (36% and 46%) are simply the *average* face's (Pallett et al. 2010).
- **The 1:1.6 lip ratio** is the one place a "golden" number shows up in a study (Heidekrueger 2017). A second study preferred 1:2. Both agree the lower lip should be the fuller one.

## 3. How the best character creators keep every result attractive

| Game | Structure | How it keeps faces attractive |
|---|---|---|
| **Baldur's Gate 3** | No face sliders. Eight curated heads per race, then make-up, tattoos, scars, eyes and hair. | The lead character artist's reason: sliders in most games produce faces that look alike after hours of work. Curated heads are always good ([Steam discussion of the dev interview](https://steamcommunity.com/app/1086940/discussions/0/3808408747680589528)). The cost is sameness. |
| **Cyberpunk 2077** | A numbered list (about 22 options) for each of eyes, nose, mouth, jaw and ears ([fandom](https://cyberpunk.fandom.com/wiki/Cyberpunk_2077_Character_Customization)). | Every part is authored to fit every other part, so no combination breaks. There is no continuous range. |
| **Black Desert** | Direct sculpting: drag points on the face, plus bone and volume controls. Hailed as the best ([KitGuru](https://www.kitguru.net/professional/design-create/jon-martindale/black-desert-mmo-character-creator-released-as-standalone-game/)). | A very high-quality base head, every handle range-limited, and shareable presets. Freedom is high, but the base is so good that most results stay pretty. |
| **Elden Ring** | Templates first (age, masculine-to-feminine, bone-structure emphasis), then about 50 sliders in 11 groups ([wiki](https://eldenring.wiki.gg/wiki/Character_Creator)). | Macro sliders before micro ones. Wide ranges, so ugly faces are possible: a cautionary tale for range. |
| **Dragon's Dogma 2** | Base heads drawn from scans of over a hundred people, then very detailed sliders (twelve for the nose alone) ([VideoGamer](https://www.videogamer.com/?p=475410)). | Start from shape volume, then details. Players note the presets look old and the depth is hard to read. |

What we take from them:
1. **A beautiful base and curated presets come first** (BG3, Black Desert). The default face and every preset must be stunning on their own. Sliders personalise them; they don't rescue them.
2. **Group sliders by region** (Elden Ring), in the order a portrait artist works:
   - Head (forehead, temples, brow ridge);
   - Eyes and brows;
   - Nose;
   - Cheeks;
   - Mouth;
   - Jaw and chin;
   - Ears and neck.
3. **Make every range matter, but stop where she breaks** (unlike Elden Ring):
   - each slider's end is the most extreme version of that feature still within the range of attractive faces;
   - a slider is capped only where the mesh truly breaks.
4. **Presets differ in bone structure and ethnicity** (Dragon's Dogma's scans), each one fitted to a real-looking beautiful reference face. Ours are painted by the local AI and fitted by landmarks (tools/assets/face_refs.py and face_fit.py).
5. **Expressive cues come for free:**
   - her idle face life: blinks, a hint of a smile, pupils;
   - the portrait light in creation.

## 4. How we build presets from the research

1. **Generate a reference (tools/assets/face_refs.py).** Krea 2 (local) paints a beauty-campaign portrait of each preset's woman, front and three-quarter side by side, hair pulled back, at four seeds. The prompt names the woman's ethnicity and her bone structure, and the cues above.
2. **Pick the best seed by eye,** at full resolution.
3. **Read her landmarks (tools/assets/face_fit.py).** MediaPipe's 478 face landmarks are read off each view.
4. **Fit the targets.** A bounded least-squares fit finds MakeHuman's targets (and our sculpts) that move the same points of the heroine's face onto them. Each view is fitted:
   - at its own pose;
   - against anchors read off her rendered at a similar turn.
5. **Check:**
   - the fitted face rendered beside its reference (front and three-quarter);
   - judged at full resolution;
   - adjusted by hand where the landmarks can't see something (ear shape, brow ridge depth, nose projection in profile).
6. **Map to sliders.** The fitted target weights are mapped onto the game's sliders, so each preset is a slider setting and the player can carry on from it.
