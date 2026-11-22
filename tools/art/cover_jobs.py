#!/usr/bin/env python3
"""Book-cover art for every tale (2026-11-22, user: "책 표지 디자인 제대로 하자").

  python3 tools/art/cover_jobs.py            # writes tools/art/cover_jobs.json
  bash -c 'python3 tools/run_jobs.py tools/art/cover_jobs.json <ids>'

Each tale gets one full-bleed KEY-ART picture for the front board of a 3D hardcover (game/story/cover_book.gd) and,
optionally, cut-paper title lettering on magenta (keyed into a transparent decal). Material is PAPER (user:
"펠트 질감 싫은뎅"): layered cut / torn paper, no felt, no wool, no stitches. The title band (top ~32 %) stays quiet so
the lettering reads. Characters keep the shipped designs (single-character crops as refs, never a lineup).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = "art_src/cover/raw/"
RC = "art_src/cast/raw/"
RA = "art_src/atlas/raw/"
PORT = "portrait, near-square, the largest size the tool offers (any size it returns is fine); save it as-is"

PAPER = ("MATERIAL: a photographed PAPER-CUT diorama illustration: every shape is a separate sheet of matte coloured "
         "paper or thin cardstock, cut with crisp edges or softly torn deckled edges, glued in overlapping LAYERS at "
         "slightly different depths so each layer casts a small soft shadow on the one behind; fine paper-fibre grain "
         "like Japanese washi / Korean hanji; each layer edge has a thin darker cut line and a faint lighter rim on the "
         "lit side. Matte, no gloss, no 3D-render plastic look. ABSOLUTELY NO felt, NO wool, NO fuzz, NO fabric or "
         "knitted texture, NO stitches, NO dashed stitch lines, NO sewing seams, NO embroidery: where the reference "
         "shows dashed stitching, draw a clean cut-paper edge instead. ")
COVER = ("A FRONT COVER ILLUSTRATION of a children's picture book for ages 3-7, full-bleed to all four edges (no border, "
         "no frame, no book shown, no mockup, just the flat cover artwork). " + PAPER +
         "FORMAT: a near-square portrait picture (slightly taller than wide). COMPOSITION: the TOP 40 PERCENT of the "
         "picture is calm open sky with NOTHING in it except a few tiny stars or soft cloud strips near the edges: no "
         "roof, no moon, no characters, no trees, no detail there; it is reserved for a big title that will be added "
         "later. The buildings and characters sit in the LOWER 60 percent only; the characters stand in front, big and close, faces toward the viewer, clearly readable at a glance. Warm, cosy, magical, never "
         "scary. ABSOLUTELY NO TEXT anywhere: no letters, no title, no words, no numbers, no signature, no logo. ")
REF_CHAR = ("Draw every character EXACTLY as its reference image (same face, hair, hat, clothes, colours, proportions) "
            "but the character references are made of FELT: do NOT copy their fuzzy felt surface. The LAST reference image "
            "is the MATERIAL reference: copy ITS look exactly: smooth matte cardstock, crisp clean scissor-cut edges, "
            "flat even colour per piece, folds and layers shown by small soft shadows, hair as overlapping cut paper "
            "locks. Every surface is SMOOTH PAPER, nothing fuzzy, nothing woolly. Draw each character ONCE. ")
MAT_REF = RC + "cast_sm_paper_girl.png"

LETTER = ("TITLE LETTERING for a children's picture book cover, on a perfectly flat, uniform, solid pure MAGENTA "
          "background (#FF00FF, RGB 255,0,255), no texture, no gradient, no shadow on the background. The lettering is "
          "made of LAYERED CUT PAPER: each Korean syllable cut from thick matte coloured paper, chunky rounded friendly "
          "letterforms for young children, a cream paper backing layer cut around the whole word with a margin (like a "
          "sticker cut-out), a soft drop of the top layer onto the backing, fine paper grain, crisp cut edges. "
          "Spell the Korean text EXACTLY, every jamo correct, nothing added, nothing missing. No other text. ")

JOBS = [
    # 사탕 마녀의 핼러윈 (witch_candy): the witch, 다현이 and 호박이 at the glowing candy shop on Halloween night
    {"id": "cover_wc_art", "kind": "bg", "aspect": PORT, "out": RAW + "cover_wc_art.png",
     "refs": [RC + "ref_wc_witch.png", RC + "ref_wc_dahyun.png", RC + "ref_wc_cat.png", RA + "ref_wc_shopfront.png", MAT_REF],
     "prompt": COVER + REF_CHAR +
     "SUBJECT: Halloween night in a little storybook village. In the middle stands THE CANDY SHOP from the reference "
     "(half-timbered cream walls, teal scalloped roof, an orange-and-cream striped awning, a big window glowing warm "
     "golden with candy jars, an arched door with warm light spilling out, a swirl-lollipop shop sign). In FRONT of the "
     "shop, on a cobbled street: THE CANDY WITCH (reference 1: mint-green curly hair, purple witch hat with a yellow "
     "star, purple puff-sleeve dress with an orange star sash, orange-cream striped socks) smiling and holding up a big "
     "swirl lollipop; beside her the little girl DAHYUN (reference 2: brown bob, purple witch hat with a star, purple "
     "cape with an orange bow, cream dress, striped socks, red shoes) looking up delighted, holding a small orange "
     "pumpkin candy bucket; and the orange tabby cat HOBAK (reference 3) sitting at their feet. Glowing jack-o'-lanterns "
     "on the steps (cut paper, crisp), a few wrapped candies scattered on the cobbles, tiny paper bats far away. SKY (top third): deep "
     "BLUE-violet indigo night paper with a big pale-cream paper moon at one upper corner, a few small cut-paper stars, "
     "soft layered cloud strips, calm and empty in the centre. LIGHT: warm golden lamplight from the shop window and door "
     "on the characters, cool indigo night around. The big pale moon, if any, is SMALL and sits low beside the roof, not in the top 40 percent. PALETTE: indigo night #2b2a5c, blue-violet #4b3a7a, pumpkin orange "
     "#e8862a, candy gold #f2c14e, cream #f4e6c8, teal roof #2f6f73, mint #8fd3c0. Every purple is BLUE-violet, never pink "
     "or magenta."},
    {"id": "cover_wc_title", "kind": "bg", "aspect": "wide landscape (any wide size, e.g. 1536x1024 or 2172x724); save it as-is",
     "out": RAW + "cover_wc_title.png",
     "prompt": LETTER + "The Korean title, on two lines, centred: line 1 '사탕 마녀의' (smaller), line 2 '핼러윈' (big). "
     "Letter colours: candy-striped and Halloween: pumpkin orange #e8862a, candy gold #f2c14e and blue-violet #4b3a7a "
     "letters alternating, a thin dark-plum cut line around each letter, a tiny cut-paper star and a swirl lollipop as "
     "decoration beside the words (not touching the letters). The cream backing layer is one connected shape behind both "
     "lines."},
]


# variants of the same job (pick the best by eye, keep the rest)
for _j in list(JOBS):
    if _j["id"].endswith("_art"):
        for _v in ("b", "c"):
            JOBS.append(dict(_j, id=_j["id"] + "_" + _v, out=_j["out"].replace(".png", "_" + _v + ".png")))

# paper pass: the character refs are felt and their nap leaks into the picture; redraw a chosen picture as smooth cut
# paper, composition kept (the sunmoon scenery redraw did the same piece for piece)
REPAPER = ("REDRAW the FIRST reference illustration EXACTLY: the same composition, the same characters in the same poses "
           "and places, the same buildings, colours, light and framing, the same size and aspect; ONLY the MATERIAL "
           "changes. The SECOND reference is the material to copy: smooth matte CARDSTOCK cut paper with crisp clean "
           "scissor-cut edges, each colour area a flat even sheet, layers separated by small soft drop shadows, folds as "
           "scored creases, hair as overlapping cut-paper locks, cobbles and roof tiles as individually cut paper shapes. "
           "REMOVE every felt / wool / fuzzy / nubby / fibrous surface texture: surfaces are smooth paper with only a very "
           "faint fine grain. No stitches, no dashed seams. Keep the top 40 percent calm empty night sky. No text. ")
for _src in ("cover_wc_art", "cover_wc_art_c"):
    JOBS.append({"id": _src + "_paper", "kind": "bg", "aspect": "the SAME size and aspect as the first reference; save it as-is",
                 "out": RAW + _src + "_paper.png", "refs": [RAW + _src + ".png", MAT_REF], "prompt": REPAPER})


# ---------------------------------------------------------------- rollout (2026-11-22, user chose the book on the table)
RF = "art_src/cover/refs/"
NO_MAT_CHAR = "Do NOT draw the girl shown in the material reference; it only shows the paper material. "
REPAPER2 = REPAPER.replace("Keep the top 40 percent calm empty night sky.", "Keep the calm empty top area as it is.")


def art(id_, refs, subject, extra_refs_mat=True):
    return {"id": id_, "kind": "bg", "aspect": PORT, "out": RAW + id_ + ".png",
            "refs": refs + ([MAT_REF] if extra_refs_mat else []),
            "prompt": COVER + REF_CHAR + (NO_MAT_CHAR if extra_refs_mat else "") + subject}


def title(id_, text, colours):
    return {"id": id_, "kind": "bg", "aspect": "wide landscape (any wide size, e.g. 1536x1024 or 2172x724); save it as-is",
            "out": RAW + id_ + ".png", "prompt": LETTER + text + " " + colours +
            " The cream backing layer is one connected shape behind all the letters."}


SPOT = ("A SMALL SPOT ILLUSTRATION (vignette) for the title page of a children's picture book, on a perfectly flat, "
        "uniform, solid pure MAGENTA background (#FF00FF, RGB 255,0,255), no texture, no gradient, no shadow on the "
        "background, the vignette centred with a wide magenta margin, one connected group of objects sitting on a small "
        "cut-paper ground patch. " + PAPER + "The LAST reference image shows the paper material only (do not draw it). "
        "No characters' faces needed, no text, no letters. Colours warm and soft; no pink or magenta inside the vignette "
        "(every pink is a coral-peach). ")


def spot(id_, subject, refs=()):
    return {"id": id_, "kind": "bg", "aspect": "square if possible, but ANY size the tool returns is fine; save it as-is", "out": RAW + id_ + ".png",
            "refs": list(refs) + [MAT_REF], "prompt": SPOT + "SUBJECT: " + subject}


BACK = ("The BACK COVER ILLUSTRATION of the same children's picture book, full-bleed to all four edges (no border, no "
        "frame, no book shown, just the flat artwork): an EPILOGUE picture of what happened after the story, quiet and "
        "warm, the same world and characters as the FIRST reference image (the front cover), drawn in exactly the same "
        "smooth cut-paper cardstock style, colours and character designs. FORMAT: the same near-square portrait aspect as "
        "the first reference. COMPOSITION: the TOP 25 PERCENT is calm empty sky (a small title word will be added later); "
        "the scene sits in the lower 75 percent, characters smaller than on the front cover, seen a little further away. "
        "ABSOLUTELY NO TEXT anywhere. No felt, no fuzz, no stitches. ")


def back(id_, front, subject, refs=()):
    return {"id": id_, "kind": "bg", "aspect": "the SAME size and aspect as the first reference; save it as-is",
            "out": RAW + id_ + ".png", "refs": [RAW + front] + list(refs), "prompt": BACK + "SUBJECT: " + subject}


ROLL = [
    # ---- round 1
    art("cover_sw_art", [RF + "ref_sw_sun.png", RF + "ref_sw_wind.png", RF + "ref_sw_traveller.png"],
        "SUBJECT: 해와 바람 (The Sun and the Wind). A country road winding over soft green paper hills with a few round trees "
        "and a little stream. On the road, big in the lower middle, THE TRAVELLER (reference 3: a boy in a brown straw "
        "hat and a long rust-red coat with cream flower trims and toggle buttons, brown boots) walking toward us, holding "
        "his coat closed with one hand, a little puzzled smile. In the sky just above the hills (NOT in the top 40 "
        "percent): THE SUN (reference 1: golden-yellow round face with orange paper rays, a sly confident smile) on the "
        "right and THE WIND (reference 2: a cream cloud face with puffed cheeks blowing curly blue paper wind swirls) on "
        "the left, both looking down at the traveller, playful rivals. A few leaves fly in the wind. SKY (top 40 percent): "
        "pale warm blue paper with thin cloud strips at the edges only. LIGHT: warm late-morning sun from the right. "
        "PALETTE: meadow greens, warm road ochre, rust red, golden yellow, sky blue, cream."),
    art("cover_tp_art", [RF + "ref_tp_pig_a.png", RF + "ref_tp_pig_b.png", RF + "ref_tp_pig_c.png", RF + "ref_tp_wolf.png",
                         RA + "story_houses.png"], extra_refs_mat=False, subject="Reference 5 is already PAPER: copy its "
        "material for everything (smooth cut cardstock, no felt). " +
        "SUBJECT: 아기 돼지 삼형제 (The Three Little Pigs). A sunny green meadow with a path; behind, left to right, the "
        "THREE HOUSES from reference 5: a straw house, a wooden house and a red brick house with a chimney, small and "
        "standing apart. In front, big in the lower half, THE THREE PIGS side by side, happy and proud (reference 1: the "
        "eldest in a straw hat and a mustard knitted-look scarf drawn as cut paper; reference 2: the middle one in blue "
        "overalls; reference 3: the youngest in a cream cap and red overalls). THE WOLF (reference 4: grey wolf in a "
        "brown vest) peeks sneakily from behind a round tree at the right edge, only his head and one paw showing, "
        "funny not scary. SKY (top 40 percent): soft blue paper with thin cloud strips at the edges only. LIGHT: warm "
        "morning. PALETTE: grass greens, straw gold, wood brown, brick red, pig coral-peach (never pink), sky blue."),
    art("cover_sm_art", [RF + "ref_sm_boy.png", RF + "ref_sm_girl.png", RF + "ref_sm_tiger.png", RF + "ref_sm_climb_boy.png",
                         RA + "story_sm_cottage_paper.png"], extra_refs_mat=False, subject=
        "All references are already PAPER: copy their material. SUBJECT: 해님 달님 (the Korean folk tale of the sun and the "
        "moon). A deep blue night over a Korean mountain village: a twisted golden straw ROPE hangs down from the sky in a "
        "gentle curve. On the rope, the BROTHER (reference 1, climbing pose like reference 4: indigo jeogori, cream baji) "
        "climbs above his little SISTER (reference 2, climbing the same way: coral jeogori with rainbow sleeve "
        "bands, salmon chima), both looking up hopefully. Below them, at the foot of a big zelkova tree beside the "
        "thatched cottage from reference 5, THE TIGER (reference 3: chubby orange paper tiger, silly not scary) looks "
        "up with his paws on the trunk, grumpy and outwitted. In the sky on either side of the rope (below the top 40 "
        "percent): a warm golden paper SUN low on the left with cut-paper rays and a pale cream paper full MOON on the "
        "right, both plain discs WITHOUT faces. SKY (top 40 percent): calm deep-indigo paper with a few small stars only. "
        "PALETTE: indigo night #26305e, gold #f2c14e, cream moon #f4ead3, coral, jade green, thatch straw, tiger orange."),
    title("cover_sw_title", "The Korean title on ONE line, centred: '해와 바람'.",
          "Letter colours: '해' golden sun-yellow #f2b632 with tiny cut-paper rays, '와' cream-ochre, '바람' sky blue #6fa8d6 "
          "with a small curly cut-paper wind swirl, a thin dark-brown cut line around each letter."),
    title("cover_tp_title", "The Korean title on two lines, centred: line 1 '아기 돼지' (smaller), line 2 '삼형제' (big).",
          "Letter colours: straw gold #e2b54a, wood brown #9a6a3c and brick red #b5523b letters (one material colour per "
          "letter group, like the three houses), a thin dark-brown cut line around each letter, a tiny cut-paper "
          "chimney with a puff of smoke beside the words (not touching the letters)."),
    title("cover_sm_title", "The Korean title on ONE line, centred: '해님 달님'.",
          "Letter colours: '해님' warm sun gold #f2b632 with tiny cut-paper rays, '달님' pale moon cream #f4ead3 on a deep "
          "indigo #26305e inner layer, a thin dark-indigo cut line around each letter, a tiny twisted straw rope and a "
          "small star as decoration beside the words (not touching the letters)."),
    title("back_end_title", "The single Korean word '끝' (The End), big and centred.",
          "Letter colour: warm brick-red #b5523b cut paper on the cream backing, a thin dark-brown cut line, two tiny "
          "cut-paper stars beside it (not touching the letter)."),
    spot("spot_wc", "a small orange jack-o'-lantern candy bucket overflowing with wrapped candies and a swirl lollipop, a "
         "tiny purple witch hat with a yellow star leaning on it, two small candies on the ground."),
    spot("spot_sw", "a brown straw hat and a rust-red coat with cream trims folded on a round grey rock in the grass, a "
         "small golden sun peeking over the rock, a curly blue paper wind swirl beside it."),
    spot("spot_tp", "three tiny houses in a row on a grass patch: a straw house, a wooden house and a red brick house "
         "with a chimney and a little curl of smoke."),
    spot("spot_sm", "a coil of twisted golden straw rope on a grass patch under a small crescent moon and a small sun, "
         "a few stars, one sorghum stalk."),
    # ---- round 2 (needs round 1): felt-nap fix for the two tales whose refs are felt; back covers of the paper tales
    {"id": "cover_sw_art_paper", "kind": "bg", "aspect": "the SAME size and aspect as the first reference; save it as-is",
     "out": RAW + "cover_sw_art_paper.png", "refs": [RAW + "cover_sw_art.png", MAT_REF], "prompt": REPAPER2},
    {"id": "cover_tp_art_paper", "kind": "bg", "aspect": "the SAME size and aspect as the first reference; save it as-is",
     "out": RAW + "cover_tp_art_paper.png", "refs": [RAW + "cover_tp_art.png", MAT_REF], "prompt": REPAPER2},
    back("back_wc_art", "cover_wc_art_paper.png", "Late Halloween night in front of the same candy shop, warm windows glowing: "
         "the candy witch, Dahyun and her three friends in costumes (a white rabbit in a yellow cape, a brown bear in a "
         "pumpkin costume, an orange fox in a purple cape) sit on the shop steps happily eating candies, Hobak the cat "
         "curled up asleep beside them; a small friendly white paper GHOST peeks out from behind the shop corner with a "
         "candy. Moon and stars.", [RC + "ref_wc_lineup.png"]),
    back("back_sm_art", "cover_sm_art.png", "Dawn-quiet: a golden paper SUN on the left and a pale cream paper MOON on the "
         "right shine side by side over the little thatched cottage, now peaceful and empty, smoke-less; below the "
         "cottage a field of tall red-brown SORGHUM stalks (the tiger's fall: one stalk bent, no tiger shown, no blood); "
         "soft blue-indigo sky with a few stars fading."),
    # ---- round 3 (needs the paper covers)
    back("back_sw_art", "cover_sw_art_paper.png", "The traveller sits resting under a round tree beside the road WITHOUT his "
         "coat (the coat and hat lie folded beside him), smiling in the warm sunshine; the SUN smiles gently above, the "
         "WIND as a small friendly cloud rests beside the sun, both content. Calm, warm afternoon light."),
    back("back_tp_art", "cover_tp_art_paper.png", "Evening: inside-view feeling through the round window of the red brick "
         "house, or just outside its open door: the THREE PIGS sit together by a warm fireplace glow, cosy and safe, "
         "one holding a mug; far off on a hill path the small grey WOLF runs away with his tail singed, a tiny puff of "
         "smoke behind him. Warm sunset light."),
]
JOBS += ROLL

# ---- round 4 (coordinator review): the sun and moon WITH the children's faces over the cottage (the kids became
# them; nobody sits in the field), and the sun_wind vignette's coat matching the traveller's real coat
JOBS += [
    back("back_sm_art_v2", "cover_sm_art.png", "Quiet dusk after the story: high in the sky on the left a golden paper "
         "SUN whose face is the little SISTER's face (reference 2: her face and pigtail buns inside the sun's rays) and "
         "on the right a pale cream paper MOON whose face is the BROTHER's face (reference 3: his bowl-cut face inside "
         "the moon), both smiling gently down. Below them the little thatched cottage from the front cover, peaceful, "
         "no smoke, no people; in front of it a field of tall red-brown SORGHUM stalks (one stalk bent). NO children, "
         "NO people, NO tiger anywhere on the ground. Soft blue-indigo dusk sky with a few first stars.",
         [RF + "ref_sm_sun_girl.png", RF + "ref_sm_moon_boy.png"]),
    {"id": "spot_sw_v2", "kind": "bg", "aspect": "square if possible, but ANY size the tool returns is fine; save it as-is",
     "out": RAW + "spot_sw_v2.png", "refs": [RAW + "cover_sw_art_paper.png", MAT_REF],
     "prompt": SPOT + "SUBJECT: the TRAVELLER's own long RUST-RED COAT from the first reference (deep rust-red with "
     "cream flower trims, mustard toggle buttons, a cream hem band) folded over a round grey rock in the grass, his "
     "BROWN STRAW HAT with a mustard band and a little leaf motif lying on top (exactly as in the first reference), a "
     "small golden paper sun peeking over the rock and a curly pale-blue paper wind swirl beside it. The coat is a "
     "European-style long coat, NOT a Korean hanbok jacket, NOT pink. Do not draw the boy."},
]


if __name__ == "__main__":
    out = os.path.join(HERE, "cover_jobs.json")
    json.dump(JOBS, open(out, "w"), ensure_ascii=False, indent=1)
    print("wrote", out, len(JOBS), "jobs:", " ".join(j["id"] for j in JOBS))
