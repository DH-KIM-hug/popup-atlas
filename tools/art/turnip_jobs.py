#!/usr/bin/env python3
"""「커다란 순무」 (turnip) art jobs for tools/run_jobs.py (2026-11-23).

  python3 tools/art/turnip_jobs.py            # writes tools/art/turnip_jobs.json
  bash -c 'python3 tools/run_jobs.py tools/art/turnip_jobs.json <ids>'

PAPER look only (user 2026-11-22: no felt anywhere, no stitching). Per-category style blocks (a shared block leaks
motifs): TN_CHAR (people + animals: printed detail only on clothing), TN_GARDEN (vegetables, garden tools, soil: plant
prints are the subject here, but NO faces, NO characters), TN_FEAST (table, pot, bowls: material prints only).

Round 1: the cast lineup (design ref = 톡톡's turnip cast, art_src/cast/raw/ref_tn_toktok.png: grandpa, grandma, the
granddaughter, the dog, the cat, the mouse, the turnip) + the garden and feast prop sheets. Round 2 references
SINGLE-CHARACTER crops of the new lineup (art_src/cast/raw/ref_tn_<role>.png; a multi-character ref made the model draw
its first character everywhere, witch_candy lesson).
Every pulling figure is a SIDE profile facing RIGHT (the stage mirrors them to face the turnip).
Key colour magenta #FF00FF: every pink is CORAL / PEACH / SALMON, the turnip's purple top a BLUE-violet plum.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_C = "art_src/cast/raw/"
RAW_A = "art_src/atlas/raw/"
WIDE = "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)"

BG = ("on a perfectly flat, uniform, solid pure MAGENTA background (#FF00FF, RGB 255,0,255) with no texture, no gradient, "
      "no vignette, no shadows on the background. Every piece is fully separate and isolated, with a clear empty magenta gap "
      "of at least 40 pixels on every side; pieces never touch or overlap each other and never touch the image border. "
      "No grid lines, no labels, no text, no letters, no numbers. ")
COLOUR = ("COLOUR RULE: NO pink and NO magenta-ish colour anywhere: every 'pink' (cheeks, inner ears, noses, the mouse's "
          "tail) is a warm CORAL-PEACH or SALMON (like #F2A07B or #E8836B, clearly orange-leaning); any purple is a deep "
          "BLUE-violet plum (like #5B4A8C), never reddish purple. ")
PAPER = ("STYLE (same for every piece): flat orthographic view, a die-cut pop-up book piece made of MATTE CUT PAPER and "
         "thin cardstock: every colour area is a separate cut or torn sheet of coloured paper glued in layers (a lighter "
         "or darker paper layer on top for shading and detail), crisp cut edges or softly torn deckled edges, each layer "
         "edge with a thin darker cut line and a faint lighter rim on its upper-left (lit) side, fine paper-fibre grain, "
         "matte, no gloss. ABSOLUTELY NO felt, NO wool, NO fuzz, NO fabric or knitted texture, NO stitches, NO dashed "
         "stitch lines, NO sewing seams, NO embroidery. Details are small cut paper shapes or a printed line, never "
         "stitching. No perspective, no cast shadows, no drop shadows, no glow, no white sticker border. Warm European "
         "(old Russian countryside) fairy-tale picture book for ages 3-7: a cottage vegetable garden in summer. " + COLOUR)
TN_CHAR = PAPER + ("PRINTED DETAIL only on clothing (the sash, the apron, the headscarf's small dots, the dress hem). "
                   "Skin, fur and faces are plain cut paper with a few layered tufts. NO flowers, NO leaves, NO "
                   "botanical motifs on anyone. ")
FACE = ("Faces are simple and sweet: dark dot or curved-line eyes, a tiny mouth, soft coral-peach cheek circles; the "
        "expression is big and readable from far away. ")
GRANDPA = ("GRANDPA (할아버지): a kind sturdy old countryside grandfather, storybook proportions about 3 heads tall, a round "
           "rosy cream-peach face, a big fluffy WHITE beard and moustache, a small round nose, a BROWN flat cap, a long "
           "DARK-GREEN belted tunic shirt to mid-thigh with a MUSTARD-OCHRE sash belt, BROWN trousers, DARK-BROWN boots. ")
GRANDMA = ("GRANDMA (할머니): a kind round old grandmother, a little shorter than grandpa, a round cream-peach face with "
           "rosy cheeks, soft grey-white hair under a RED headscarf tied at the back of the neck, a CREAM long-sleeved "
           "blouse, a long ORANGE pinafore dress to the ankles, a CREAM apron tied at the waist, small brown shoes. ")
GIRL = ("THE GRANDDAUGHTER (손녀): a little girl about 6 years old, about 0.7 times grandpa's height, a round cream-peach "
        "face, brown hair in ONE round top bun tied with a red ribbon and soft bangs, a short-sleeved RED dress to the "
        "knees with a small cream collar, white socks, red shoes. ")
DOG = ("THE DOG (강아지): a small fluffy WHITE puppy standing on FOUR legs like a real puppy, tan-orange patches on its "
       "floppy ears and back, big shiny dark eyes, a black button nose, coral-peach cheeks, a little coral tongue, a BLUE "
       "harness on its chest, a fluffy curled white tail. About as tall as grandpa's knee. ")
CAT = ("THE CAT (고양이): a slim ORANGE-YELLOW tabby cat on FOUR legs like a real cat, darker orange stripes, a cream "
       "muzzle and chest, pointed ears with coral-peach insides, green-gold eyes, white whisker lines, a long curling "
       "striped tail. A little smaller than the dog. ")
MOUSE = ("THE MOUSE (생쥐): a TINY round GREY mouse on four little feet, very big round ears with coral-peach insides, a "
         "cream belly, shiny black bead eyes, a small coral nose, thin whiskers, a long thin coral-peach tail. Much smaller "
         "than the cat. ")
LEGS = ("EVERY standing or walking figure has a clearly VISIBLE open magenta GAP between its legs; legs never touch or "
        "overlap; exactly the right number of legs (two for a person, four for an animal); hands never overlap the legs. ")
FRONT = "FRONT figures: full body facing the viewer straight on (not turned), feet on one horizontal baseline. "
SIDE = "SIDE figures: full body in clean side PROFILE facing to the RIGHT (nose to the right edge), one eye visible. "
BACK = "BACK figures: seen from directly BEHIND: back of the head, clothes / fur from behind, heels toward us, no face. "
ROW = ("All figures in ONE horizontal row with their feet on a common baseline near the bottom of the image, a wide magenta "
       "gap between them, the SAME character design in every figure. ")
REF_LINE = ("MATCH THE REFERENCE CHARACTER EXACTLY (same face, hair, clothes, colours, proportions and size); this is the "
            "same paper puppet in new poses. THIS SHEET SHOWS ONLY THIS ONE CHARACTER; do NOT draw any other character "
            "and do NOT draw a turnip unless asked. ")
NO_BOT = " IMPORTANT: no flowers, no leaves, no plants, no botanical motifs on any character. No text."
PULL = ("PULLING (a tug of war): seen from the SIDE facing RIGHT, the whole body LEANING BACK hard (about 20 degrees, away "
        "from the right), both arms stretched FORWARD to the right at waist-to-chest height with the hands closed in fists "
        "round something that is NOT drawn, the front foot planted forward, the back leg braced, an effort face (eyes "
        "squeezed shut, cheeks puffed). ")
TUMBLE = ("TUMBLED OVER: fallen backwards onto the bottom (seen from the side, back toward the LEFT), legs kicked up in the "
          "air, arms flung up, a surprised-laughing open mouth. ")

REF_TOKTOK = [RAW_C + "ref_tn_toktok.png"]


def REF(role):
    return [RAW_C + f"ref_tn_{role}.png"]


JOBS = []


def cast(jid, n, who, body, refs, extra=""):
    JOBS.append({"id": jid, "kind": "bg", "refs": refs, "aspect": WIDE, "out": RAW_C + jid + ".png",
                 "prompt": f"A CHARACTER SHEET for a children's pop-up storybook: {n} separate full-body die-cut stand-up "
                 "figures in one horizontal row, " + BG + TN_CHAR + who + FACE + LEGS + extra + ROW +
                 (REF_LINE if refs != REF_TOKTOK else "") + body + NO_BOT})


# ---------------------------------------------------------------- round 1: lineup (design ref = 톡톡)
cast("cast_tn_lineup", "SIX", GRANDPA + GRANDMA + GIRL + DOG + CAT + MOUSE,
     "The reference image shows the character DESIGNS from an older felt version (and a turnip, which you must NOT "
     "draw): keep the designs but redraw every figure in THIS matte cut-PAPER style, every pink a coral-peach. SIZES: "
     "grandpa about 80 percent of the image height, grandma about 74 percent, the girl about 56 percent, the dog about 34 "
     "percent, the cat about 30 percent, the mouse about 14 percent. THE SIX FIGURES, left to right, all with a calm "
     "happy face: (1) GRANDPA, FRONT, standing, arms relaxed; (2) GRANDMA, FRONT, standing, hands folded on her apron; "
     "(3) THE GIRL, FRONT, standing, arms relaxed a little away from the body; (4) THE DOG, SIDE profile facing RIGHT "
     "standing on four legs, tail up; (5) THE CAT, SIDE profile facing RIGHT standing on four legs, tail curling up; "
     "(6) THE MOUSE, SIDE profile facing RIGHT standing on four little feet, tail curling.", REF_TOKTOK, extra=FRONT)

# ---------------------------------------------------------------- round 2: people (ref = single-character crops)
for role, who, extra_b in [
        ("grandpa", GRANDPA,
         "(4) SIDE facing RIGHT, KNEELING ON ONE KNEE planting: one hand down near the ground (dropping a tiny seed), the "
         "other on his knee, a gentle hopeful face; (5) SIDE facing RIGHT, WATERING: holding a green tin watering can "
         "forward and tilted down with both hands, a kind smile; (6) FRONT, CLAPPING HIS PALMS together in front of his "
         "chest, ready to work, a cheerful determined grin."),
        ("grandma", GRANDMA,
         "(4) FRONT, ENCOURAGING: both fists up at her shoulders, a big cheerful open smile ('let's do it together!'); "
         "(5) FRONT, LADLING SOUP: holding a big wooden ladle in one hand and a soup bowl in the other, a warm smile; "
         "(6) FRONT, CLAPPING with joy, eyes closed in happy curves."),
        ("girl", GIRL,
         "(4) FRONT, EAGER WAVE: one hand waving high, a big bright smile; (5) SIDE facing RIGHT, SKIPPING: one knee up, "
         "arms swinging, a happy face, both feet off the ground (still a visible gap between the legs); (6) FRONT, "
         "CLAPPING with joy, eyes closed in happy curves.")]:
    cast(f"cast_tn_{role}_expr", "SIX", who,
         f"SIX figures, left to right: (1) {PULL}(2) {TUMBLE}(3) FRONT, SURPRISED: eyes wide, mouth a round 'oh!', hands "
         "up at the shoulders; (4) FRONT, HAPPY CHEER: both arms raised high, a big open laughing smile; (5) FRONT, "
         "SITTING TIRED on the ground, legs stretched out in front, hands resting on the ground behind, a tired sighing "
         "face 'phew'; (6) FRONT, EATING: holding a small wooden soup bowl in one hand and a spoon in the other at the "
         "mouth, a delighted happy face.", REF(role), extra=FRONT + SIDE)
    cast(f"cast_tn_{role}_more", "SIX", who,
         "SIX figures, left to right: (1) SIDE facing RIGHT, standing calmly; (2) BACK figure standing; (3) FRONT, "
         "CALLING OUT: both hands cupped round the mouth, shouting with a big open mouth, leaning forward a little; "
         + extra_b, REF(role), extra=SIDE + BACK + FRONT)
    cast(f"cast_tn_{role}_walk", "EIGHT", who,
         "WALK CYCLE: EIGHT full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one "
         "cheerful walk cycle in order: (1) CONTACT (legs wide apart, front heel down), (2) DOWN, (3) PASSING (one leg "
         "straight under the body, the other lifted and bent), (4) UP; arms swinging opposite to the legs, upright and "
         "steady, a calm happy face, the legs clearly separated with an open magenta gap; (5)-(6) TWO BACK-VIEW frames "
         "walking AWAY (left foot lifted behind, then the right foot); (7)-(8) TWO FRONT-VIEW frames walking TOWARD the "
         "viewer (left foot forward, then the right foot). All eight the SAME scale as the reference, feet on one common "
         "baseline.", REF(role))
for role, who in [("grandma", GRANDMA), ("girl", GIRL)]:
    cast(f"cast_tn_{role}_run", "SIX", who,
         "RUN CYCLE (hurrying happily): SIX full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing "
         "RIGHT of one run cycle in order: (1) CONTACT, (2) DOWN, (3) PASSING, (4) FLIGHT (both feet off the ground); "
         "leaning forward, arms pumping, legs clearly apart with an open magenta gap, a bright eager face; (5)-(6) TWO "
         "FRONT-VIEW frames running TOWARD the viewer (left knee up, then the right).", REF(role))

# ---------------------------------------------------------------- round 2: animals
for role, who, extra in [
        ("dog", DOG, "(8) SIDE facing RIGHT, GROWLING at someone: front legs low and stiff, ears back, a grumpy little "
                     "frown showing a tiny bit of white teeth, tail stiff. "),
        ("cat", CAT, "(8) SIDE facing RIGHT, GLARING: back arched, fur on the tail puffed, ears flat, a cross squint. "),
        ("mouse", MOUSE, "(8) FRONT, BRAVE: standing up on its hind feet, chest out, one tiny fist raised, a determined "
                         "proud little face. ")]:
    hold = {"dog": "gripping a cloth hem in its MOUTH and with both front paws (the cloth is NOT drawn)",
            "cat": "both front paws stretched forward gripping a tail (the tail is NOT drawn)",
            "mouse": "both tiny front paws stretched forward gripping a tail (the tail is NOT drawn)"}[role]
    cast(f"cast_tn_{role}_expr", "EIGHT", who,
         "EIGHT figures, left to right: (1) SIDE facing RIGHT, standing calmly on four legs; (2) SIDE facing RIGHT, "
         f"PULLING: standing up on its HIND legs and LEANING BACK hard, {hold}, the hind feet braced, an effort face; "
         "(3) TUMBLED OVER onto its back, paws in the air, a surprised-laughing open mouth (side view); (4) FRONT, "
         "SURPRISED: sitting up, eyes wide, mouth a round 'oh!'; (5) FRONT, HAPPY: standing up on its hind legs, front "
         "paws raised, a big open laughing smile; (6) FRONT, SITTING TIRED: sitting slumped, tongue or mouth open "
         "panting, eyes half closed; (7) FRONT, EATING: sitting up holding a tiny wooden bowl, delighted; " + extra,
         REF(role), extra=SIDE + FRONT)
    cast(f"cast_tn_{role}_walk", "EIGHT", who,
         ("TROT CYCLE" if role != "mouse" else "SCURRY CYCLE") + ": EIGHT full-body figures on FOUR legs, left to right: "
         "(1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one cheerful trot in order (legs reaching, gathering, "
         "passing, stretching), every leg separate with open magenta gaps between them, tail swinging, a happy eager "
         "face; (5)-(6) TWO BACK-VIEW frames trotting AWAY (seen from behind: tail, back legs alternating); (7)-(8) TWO "
         "FRONT-VIEW frames trotting TOWARD the viewer (front paws alternating). All eight the SAME scale as the "
         "reference, feet on one common baseline.", REF(role))

# ---------------------------------------------------------------- round 3 (v5, user on v4: "애들 달리는거 점검좀"):
# drawn RUN cycles for the animals (they ran on their trot / scurry walk cycles, at run speed); refs = the single crop +
# the animal's own walk sheet (same design, same scale)
for role, who, gait in [("dog", DOG, "GALLOP: a happy puppy dash, ears flying back, tongue out"),
                        ("cat", CAT, "BOUNDING RUN: a light quick cat dash, body stretched long, tail streaming back"),
                        ("mouse", MOUSE, "SCURRY DASH: a tiny quick mouse dash, body low and stretched, tail streaming back")]:
    cast(f"cast_tn_{role}_run", "EIGHT", who,
         f"RUN CYCLE ({gait}): EIGHT full-body figures on FOUR legs, left to right: (1)-(4) FOUR SIDE-PROFILE frames "
         "facing RIGHT of ONE run cycle in order: (1) REACH (front legs stretched far forward, hind legs stretched far "
         "back, body long and low), (2) FRONT FEET LANDING (front paws down under the chest, hind legs coming forward), "
         "(3) GATHER (all four paws bunched together under the body, back rounded, hind paws planted ahead of the front "
         "paws), (4) PUSH-OFF (hind legs pushing back, front legs reaching forward, all four feet off the ground); every "
         "leg separate with open magenta gaps between them, leaning forward, an eager happy face, the SAME head and "
         "body size in all four; (5)-(6) TWO BACK-VIEW frames running AWAY from the viewer (seen from directly behind: "
         "the back of the head and ears, the tail up, the hind legs alternating, one paw kicked up); (7)-(8) TWO "
         "FRONT-VIEW frames running straight TOWARD the viewer (the face to us, ears flying, front paws alternating, one "
         "paw lifted high). All eight the SAME scale as the reference figures, feet (or the lowest paw) on one common "
         "baseline.", REF(role) + [RAW_C + f"cast_tn_{role}_walk.png"])

# ---------------------------------------------------------------- set / prop sheets (round 1, no character refs)
TN_GARDEN = PAPER + ("Vegetable leaves and plants are the subject here (veins as cut lines are fine). NO faces on "
                     "anything, NO animals, NO people. ")
TN_FEAST = PAPER + ("MATERIAL PRINTS ONLY (wood grain, checked cloth, glazed clay, tin). NO flowers, NO leaves, NO faces, "
                    "NO animals, NO people. ")


def sheet(jid, n, style, body, refs=None):
    JOBS.append({"id": jid, "kind": "bg", "refs": refs or [], "aspect": WIDE, "out": RAW_A + jid + ".png",
                 "prompt": f"A PROP SHEET for a children's pop-up storybook: {n} separate die-cut stand-up cardboard "
                 "pieces, every piece standing on a flat bottom edge (the hinge), " + BG + style + body})


TURNIP = ("THE GIANT TURNIP: a huge round turnip bulb, CREAM-WHITE on the lower two thirds and a deep BLUE-VIOLET plum "
          "(#5B4A8C, never pink or reddish) on the top shoulder, soft paper-layer shading, a thin root tail at the bottom, "
          "and a big bushy crown of broad dark-green and leaf-green turnip leaves with pale veins rising from the top ")
sheet("story_tn_garden", "FOURTEEN", TN_GARDEN,
      "Pieces, all straight on, left to right in two rows: (1) " + TURNIP + "(the whole turnip, the largest piece, the "
      "leaves about as tall as the bulb); (2) the SAME TURNIP LEAF CROWN alone with just the top violet shoulder of the "
      "bulb (as if the bulb is still under the ground), the same size and shape of leaves as piece 1; (3) a tiny turnip "
      "SPROUT: two small round seed leaves on a short pale stem; (4) a YOUNG turnip plant: a small rosette of five broad "
      "green leaves; (5) ONE round brown seed (small); (6) a small heap of tilled brown soil with a round dark planting "
      "hole in front; (7) a green tin WATERING CAN with a long spout and a rose; (8) a spray of pale-blue paper water drops "
      "falling in a fan (a loose bunch of 7 drops joined by thin pale strands); (9) two brown soil clods flying (one "
      "piece, joined); (10) a short row of three round green CABBAGES; (11) a row of feathery CARROT tops with orange "
      "shoulders peeping out of the soil; (12) three wooden bean poles tied at the top with green bean vines and pods; (13) "
      "a low rounded earth MOUND with grass tufts and a dark round MOUSE HOLE at its foot (the hole a solid dark brown "
      "oval, no animal); (14) a long low TILLED GARDEN BED seen from the front: brown soil ridges in rows, a low "
      "wattle edging. The turnip pieces are the biggest; keep every piece clearly separate.")
sheet("story_tn_feast", "TEN", TN_FEAST,
      "Pieces, all straight on, left to right: (1) a long wooden farmhouse TABLE seen from the front with a red-and-cream "
      "CHECKED tablecloth hanging over its front, sturdy legs with open magenta gaps between them (the largest piece); "
      "(2) a big round BLACK-IRON SOUP POT with two handles and a lid tilted open, golden turnip soup inside showing at "
      "the rim; (3) a small wooden SOUP BOWL full of golden turnip soup with cream turnip cubes, seen from the front; (4) "
      "a wooden chopping board with cream-and-violet turnip slices and a small knife; (5) a long wooden BENCH seen from "
      "the front (legs with gaps); (6) a curl of cream paper STEAM (three wavy strands); (7) a round loaf of brown bread "
      "in a wicker basket; (8) a clay jug of milk; (9) a string of small round warm-yellow paper LANTERNS hanging between "
      "two thin wooden poles; (10) a wooden ladle.")


# ---------------------------------------------------------------- the book: cover, title, back cover, title-page spot
# (helpers and blocks from tools/art/cover_jobs.py; the jobs live here so that shared file stays untouched)
import sys as _sys
_sys.path.insert(0, HERE)
import cover_jobs as _cj  # noqa: E402

JOBS += [
    _cj.art("cover_tn_art", [RAW_C + "ref_tn_grandpa.png", RAW_C + "ref_tn_grandma.png", RAW_C + "ref_tn_girl.png",
                             RAW_C + "ref_tn_dog.png", RAW_A + "story_tn_garden.png"], extra_refs_mat=False, subject=
            "All references are already PAPER: copy their material. SUBJECT: 커다란 순무 (The Giant Turnip). A sunny "
            "summer vegetable garden: in the middle a HUGE turnip (reference 5, piece 2: a big crown of green leaves, the "
            "blue-violet plum shoulder of the bulb showing above the brown soil, never pink). Pulling it in one tidy "
            "line from the right side, each holding the one ahead: GRANDPA (reference 1: white beard, brown flat cap, "
            "dark-green belted tunic) gripping the leaves, GRANDMA (reference 2: red dotted headscarf, orange pinafore, "
            "cream apron) holding his waist, the GIRL (reference 3: red dress, top bun) holding grandma, the white PUPPY "
            "(reference 4: tan ear patches, blue harness) tugging the girl's skirt, an orange tabby CAT holding the "
            "puppy's tail and a tiny grey MOUSE at the very end, all leaning back with effort, funny and cheerful. "
            "Behind them a long thatched farmhouse and a small red barn. SKY (top 40 percent): soft blue paper with thin "
            "cloud strips at the edges only. LIGHT: warm summer afternoon. PALETTE: leaf greens, soil browns, turnip "
            "cream and blue-violet, grandpa green, grandma orange, girl red."),
    _cj.title("cover_tn_title", "The Korean title on one line, centred: '커다란 순무' ('커다란' a little smaller than '순무').",
              "Letter colours: '커다란' leaf green #5e8c3a, '순무' warm cream #f2e3c6 letters on a blue-violet plum "
              "#5b4a8c inner layer, a thin dark-brown cut line around each letter, two small green turnip leaves as "
              "decoration above '무' (not touching or replacing any stroke). NEVER replace or decorate any stroke of a "
              "letter; every jamo plainly visible: 커 다 란 순 무."),
    _cj.back("back_tn_art", "cover_tn_art.png", "Evening after the story: a long table with a red-and-cream checked "
             "cloth in front of the lit farmhouse under a string of warm paper lanterns; grandpa, grandma, the girl, "
             "the puppy, the cat and the tiny mouse all eating turnip soup from wooden bowls, a big black pot steaming "
             "on the table; the empty garden plot beside them with a big hole where the turnip was. Warm sunset light, "
             "a few first stars."),
    _cj.spot("spot_tn", "a small green tin WATERING CAN beside a single little turnip SPROUT (two round seed leaves) "
             "growing out of a small heap of brown garden soil.", refs=[RAW_A + "story_tn_garden.png"]),
]


if __name__ == "__main__":
    out = os.path.join(HERE, "turnip_jobs.json")
    json.dump(JOBS, open(out, "w"), ensure_ascii=False, indent=1)
    print(len(JOBS), "jobs ->", out)
    for j in JOBS:
        print(" ", j["id"], len(j["prompt"]))
