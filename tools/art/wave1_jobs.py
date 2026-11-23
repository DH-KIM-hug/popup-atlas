#!/usr/bin/env python3
"""Wave 1 (2026-11-24, gate audit v1): the shared cycles every tale was missing. PAPER look only, no white rim.

  python3 tools/art/wave1_jobs.py          # writes refs (art_src/cast/raw/ref_w1_*.png) + tools/art/wave1_jobs.json
  bash -c 'python3 tools/run_jobs.py tools/art/wave1_jobs.json <ids>'
  python3 tools/cast/wave1_cast.py         # slice + catalogue (add_cycles), kid clones, climb aliases

Refs are the shipped paper figures on magenta (single character per sheet, so no lineup leak).
"""
import json, os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
RAW = "art_src/cast/raw/"
WIDE = "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)"
BG = ("on a perfectly flat, uniform, solid pure MAGENTA background (#FF00FF, RGB 255,0,255) with no texture, no gradient, "
      "no vignette, no shadows on the background. Every piece is fully separate and isolated, with a clear empty magenta gap "
      "of at least 60 pixels on every side; pieces never touch or overlap each other and never touch the image border. "
      "No grid lines, no labels, no text, no letters, no numbers. ")
COLOUR = ("COLOUR RULE: NO pink and NO magenta-ish colour anywhere: every 'pink' (cheeks, inner ears, noses) is a warm "
          "CORAL-PEACH or SALMON (orange-leaning); any purple is a deep BLUE-violet plum, never reddish purple. ")
PAPER = ("STYLE (same for every piece): flat orthographic view, a die-cut pop-up book piece made of MATTE CUT PAPER and "
         "thin cardstock: every colour area is a separate cut or torn sheet of coloured paper glued in layers (a lighter "
         "or darker paper layer on top for shading and detail), crisp cut edges, each layer edge with a thin darker cut "
         "line, fine smooth paper grain, matte, no gloss. ABSOLUTELY NO felt, NO wool, NO fuzz, NO fabric or knitted "
         "texture, NO stitches, NO dashed stitch lines, NO sewing seams, NO embroidery. Details are small cut paper shapes "
         "or a printed line, never stitching. No perspective, no cast shadows, no drop shadows, no glow, NO white or cream "
         "sticker border round the figure (the cut edge is the figure's own colour). " + COLOUR)
LEGS = ("EVERY walking / running figure has a clearly VISIBLE open magenta GAP between its legs; legs never touch or overlap; "
        "exactly the right number of arms and legs. ")
ROW = ("All figures in ONE horizontal row with their feet on a common baseline near the bottom of the image, a wide magenta "
       "gap between them, the SAME character design and the SAME scale in every figure. ")
REF_LINE = ("MATCH THE REFERENCE CHARACTER EXACTLY (same face, fur / hair, clothes, colours, proportions and size); this is the "
            "same paper puppet in new poses. THIS SHEET SHOWS ONLY THIS ONE CHARACTER; do NOT draw any other character, "
            "NO props unless asked, NO ladder, NO tree, NO rope. ")
BACK = "BACK figures: seen from directly BEHIND: back of the head, clothes / fur from behind, heels toward us, NO face. "
FRONT = "FRONT figures: facing the viewer straight on (not turned). "
SIDE = "SIDE figures: clean side PROFILE facing to the RIGHT. "
NO_BOT = " IMPORTANT: no flowers, no leaves, no plants, no botanical motifs on any character. No text."

REFS = {  # ref png <- shipped figures (on magenta, side by side)
    "wolf": ["cast_wolf_calm", "cast_wolf_walk_back_0", "cast_wolf_run_cycle_0"],
    "tiger": ["cast_tiger_calm", "cast_tiger_walk_back_0", "cast_tiger_walk_cycle_0"],
    "tiger_dg": ["cast_tiger_dg_back", "cast_tiger_dg_cycle_0", "cast_tiger_dg_calm"],
    "kid": ["cast_goat_kid_4_walk_front_0", "cast_goat_kid_4_run_cycle_0", "cast_goat_kid_4_calm"],
    "mother_pig": ["cast_mother_pig_calm", "cast_mother_pig_wave"],
    "rich_lady": ["cast_rich_lady_calm", "cast_rich_lady_side_walk"],
    "peasant_mother": ["cast_peasant_mother_calm", "cast_peasant_mother_happy"],
}


def make_ref(name, ids):
    ims = [Image.open(f"game/art/cast/{i}.webp").convert("RGBA") for i in ids]
    h = max(i.height for i in ims)
    W = sum(i.width for i in ims) + 60 * (len(ims) + 1)
    out = Image.new("RGB", (W, h + 120), (255, 0, 255))
    x = 60
    for i in ims:
        out.paste(i, (x, 60 + h - i.height), i)
        x += i.width + 60
    p = f"{RAW}ref_w1_{name}.png"
    out.save(p)
    return p


JOBS = []


def cast(jid, n, who, body, ref, extra=""):
    JOBS.append({"id": jid, "kind": "bg", "refs": [ref], "aspect": WIDE, "out": RAW + jid + ".png",
                 "prompt": f"A CHARACTER SHEET for a children's pop-up storybook: {n} separate full-body die-cut stand-up "
                 "figures in one horizontal row, " + BG + PAPER + who + LEGS + extra + ROW + REF_LINE + body + NO_BOT})


WOLF = ("THE WOLF: the grey storybook wolf of the reference who walks upright like a person, a mustard-ochre waistcoat with "
        "two small coloured patches, a bushy grey tail with a dark tip. ")
TIGER = ("THE TIGER: the big chubby orange storybook tiger of the reference who walks upright on his hind legs, dark brown "
         "stripes, a cream belly, round ears, a long striped tail. ")
TIGER_DG = ("THE TIGER DRESSED AS THE MOTHER: the chubby orange tiger of the reference wearing the mother's clothes: a cream "
            "headscarf over his head, a coral-orange hanbok jacket (jeogori), a long dark-brown skirt (chima) to his ankles, "
            "his striped tail poking out under the skirt, tiger paws for feet. ")
KID = ("THE KID GOAT: the small cream-white fluffy kid goat of the reference on four legs, little horns, floppy ears with "
       "coral-peach insides, a GREEN collar with a gold bell (keep the collar plain GREEN in every figure). ")

refs = {k: make_ref(k, v) for k, v in REFS.items()}
cast("cast_w1_wolf_back", "FOUR", WOLF,
     "FOUR figures, left to right, all seen from BEHIND: (1)-(2) TWO BACK-VIEW frames of a RUN AWAY from the viewer "
     "(fleeing in panic: leaning forward, arms pumping, (1) the left foot kicked up high behind with the sole showing, "
     "(2) the right foot kicked up high behind; the tail streaming); (3)-(4) TWO BACK-VIEW frames CLIMBING A LADDER that "
     "is NOT drawn: (3) the LEFT arm reaching high above the head gripping an invisible rung, the right hand at shoulder "
     "height, the RIGHT knee raised high (foot on a higher rung); (4) the mirror: the RIGHT arm reaching high, the LEFT knee "
     "raised high. Hands are closed fists round invisible rungs; nothing between them.", refs["wolf"], extra=BACK)
cast("cast_w1_tiger_back", "FOUR", TIGER,
     "FOUR figures, left to right, all seen from BEHIND: (1)-(2) TWO BACK-VIEW frames of a RUN AWAY from the viewer "
     "(fleeing: leaning forward, arms pumping, (1) the left foot kicked up high behind showing the paw pad, (2) the right "
     "foot kicked up; the tail streaming); (3)-(4) TWO BACK-VIEW frames CLIMBING UP A TREE TRUNK that is NOT drawn, "
     "hugging it: (3) both arms reaching up high, the left paw higher, the RIGHT knee drawn up high to the side; (4) the "
     "right paw higher, the LEFT knee drawn up high. Nothing drawn between the arms.", refs["tiger"], extra=BACK)
cast("cast_w1_tiger_dg_back", "TWO", TIGER_DG,
     "TWO BACK-VIEW figures WALKING AWAY from the viewer, seen from directly behind (the back of the headscarf, the back of "
     "the jacket and the long skirt, the striped tail poking out under the skirt): (1) the left foot lifted behind under "
     "the skirt hem, (2) the right foot lifted behind. A sneaky slightly hunched walk.", refs["tiger_dg"], extra=BACK)
cast("cast_w1_kid_run_front", "TWO", KID,
     "TWO FRONT-VIEW frames of the kid goat RUNNING straight TOWARD the viewer in a scared dash (the face to us, eyes wide, "
     "ears flying, the green collar and bell bouncing): (1) the LEFT front leg lifted high and bent, (2) the RIGHT front "
     "leg lifted high and bent; the hind legs visible behind, every leg separate with magenta gaps.", refs["kid"],
     extra=FRONT)
for skin, who in [
        ("mother_pig", "THE MOTHER PIG: the plump kind mother pig of the reference who walks upright, a red headscarf with "
                       "white dots, a green dress, a cream apron. "),
        ("rich_lady", "THE RICH LADY (부잣집 마님): the plump kind Korean lady of the reference, a green hanbok jacket with "
                      "gold trim, a long deep-blue-violet skirt (chima) to the ground, dark hair in a low bun with a hairpin. "),
        ("peasant_mother", "THE PEASANT MOTHER: the kind young countryside mother of the reference, light-brown wavy hair, "
                           "a cream blouse, a long mustard-yellow pinafore dress, small brown shoes. ")]:
    cast(f"cast_w1_{skin}_walk", "EIGHT", who,
         "WALK CYCLE: EIGHT full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one calm "
         "walk cycle in order: (1) CONTACT (legs wide apart, front heel down), (2) DOWN, (3) PASSING (one leg under the "
         "body, the other lifted and bent), (4) UP; arms swinging opposite to the legs, upright, a calm kind face (for a "
         "long skirt: the feet and the hem show the stride, one foot forward under the hem); (5)-(6) TWO BACK-VIEW frames "
         "walking AWAY (left foot lifted behind, then the right foot); (7)-(8) TWO FRONT-VIEW frames walking TOWARD the "
         "viewer (left foot forward, then the right). All eight the SAME scale as the reference.", refs[skin],
         extra=SIDE + BACK + FRONT)

json.dump(JOBS, open("tools/art/wave1_jobs.json", "w"), ensure_ascii=False, indent=1)
print(len(JOBS), "jobs", [j["id"] for j in JOBS])
