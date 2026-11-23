#!/usr/bin/env python3
"""「라푼젤」 (rapunzel) art jobs for tools/run_jobs.py (2026-11-23).

  python3 tools/art/rapunzel_jobs.py            # writes tools/art/rapunzel_jobs.json
  bash -c 'python3 tools/run_jobs.py tools/art/rapunzel_jobs.json <ids>'

PAPER look only (user 2026-11-22: no felt anywhere, no stitching). Per-category style blocks: RP_CHAR (people: printed
detail only on clothing), RP_GARDEN (the witch's garden plants, the cradle, the braid pieces, sparkles: no faces, no
characters), RP_ROOM (the tower room from inside: stone, wood, cloth prints only).

Round 1: one expression sheet per character, the design reference = that character's single 톡톡 figure
(art_src/cast/raw/ref_rp_toktok_<role>.png, white background; 톡톡's art is felt-like: redraw in paper).
Round 2 references SINGLE-CHARACTER crops of round 1 (art_src/cast/raw/ref_rp_<role>.png), never a lineup
(witch_candy lesson: a multi-character ref draws its first character everywhere).
Key colour magenta #FF00FF: every pink is CORAL / PEACH / SALMON; the prince's cape is a tomato RED, never crimson-pink.
Rapunzel's braid: one long thick GOLDEN braid with small RED bows (톡톡's design), drawn on her BACK / over her shoulder
in standing figures; the braid that hangs from the tower is a separate tiled prop (story_rp_garden), so figures at the
window only hold its top.
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
COLOUR = ("COLOUR RULE: NO pink and NO magenta-ish colour anywhere: every 'pink' (cheeks, lips, petals) is a warm "
          "CORAL-PEACH or SALMON (like #F2A07B or #E8836B, clearly orange-leaning); every red is a warm TOMATO red "
          "(#C8322B), never crimson-pink; any purple or violet is a deep BLUE-violet (like #5B4A8C), never reddish purple. ")
PAPER = ("STYLE (same for every piece): flat orthographic view, a die-cut pop-up book piece made of MATTE CUT PAPER and "
         "thin cardstock: every colour area is a separate cut or torn sheet of coloured paper glued in layers (a lighter "
         "or darker paper layer on top for shading and detail), crisp cut edges or softly torn deckled edges, each layer "
         "edge with a thin darker cut line and a faint lighter rim on its upper-left (lit) side, fine paper-fibre grain, "
         "matte, no gloss. ABSOLUTELY NO felt, NO wool, NO fuzz, NO fabric or knitted texture, NO stitches, NO dashed "
         "stitch lines, NO sewing seams, NO embroidery. Details are small cut paper shapes or a printed line, never "
         "stitching. No perspective, no cast shadows, no drop shadows, no glow, no white sticker border. Warm European "
         "fairy-tale picture book for ages 3-7 (Grimm's Rapunzel, a forest tower). " + COLOUR)
RP_CHAR = PAPER + ("PRINTED DETAIL only on clothing (a collar, a belt, a hem band). Skin and hair are plain cut paper "
                   "with a few layered strands. NO flowers, NO leaves, NO botanical motifs on anyone. ")
FACE = ("Faces are simple and sweet: dark dot or curved-line eyes, a tiny mouth, soft coral-peach cheek circles; the "
        "expression is big and readable from far away. ")
RAP = ("RAPUNZEL: a sweet girl about 12 years old, storybook proportions about 3.5 heads tall, a round cream-peach face, "
       "soft GOLDEN-YELLOW hair with a side-swept fringe, the rest of her hair in ONE very long thick GOLDEN BRAID tied "
       "with small tomato-RED bows every hand's width; a sleeveless LEAF-GREEN (soft olive-lime) A-line dress to below the "
       "knee with a small round CREAM collar, brown flat shoes. ")
RAP_SHORT = ("RAPUNZEL WITH SHORT HAIR (after the witch cut her braid): the SAME girl and the same green dress, but her golden "
             "hair is now a short chin-length bob with the same side-swept fringe, NO braid at all, one small tomato-red "
             "bow clip above one ear. ")
GOTHEL = ("GOTHEL THE WITCH: a stern but not scary old woman, storybook proportions about 3.5 heads tall, a round "
          "cream-peach face with a small frown and thick grey eyebrows, SILVER-GREY hair in a bun with a few loose wisps, "
          "a long FOREST-GREEN hooded cloak (hood down on her shoulders, a round bronze clasp) over a long BROWN dress to "
          "the ground, a crooked wooden walking stick / wand in one hand. NO pointed hat. ")
PRINCE = ("THE PRINCE: a kind young prince, storybook proportions about 3.5 heads tall, a round cream-peach face, tousled "
          "CHESTNUT-BROWN hair, a small GOLDEN crown, a CREAM tunic with a brown belt and a gold buckle, a tomato-RED cape "
          "over the shoulders, NAVY-BLUE trousers, tall BROWN boots. ")
FATHER = ("THE FATHER: a kind gentle peasant man, storybook proportions about 3.5 heads tall, a round cream-peach face, "
          "a short brown beard, a BROWN flat cap, a BROWN long-sleeved work tunic with a cream collar and a rope belt, "
          "NAVY-BLUE trousers, brown shoes. ")
MOTHER = ("THE MOTHER: a gentle young woman expecting a baby (a softly rounded tummy), storybook proportions about 3.5 heads "
          "tall, a round cream-peach face, LIGHT-BROWN hair in a low bun, a CREAM blouse, a long MUSTARD-YELLOW dress with a "
          "cream apron bow at the back, brown shoes. ")
LEGS = ("EVERY standing or walking figure has a clearly VISIBLE open magenta GAP between its legs (or under the hem); legs "
        "never touch or overlap; hands never overlap the legs. ")
FRONT = "FRONT figures: full body facing the viewer straight on (not turned), feet on one horizontal baseline. "
ROW = ("All figures in ONE horizontal row with their feet on a common baseline near the bottom of the image, a wide magenta "
       "gap between them, the SAME character design in every figure. ")
REF_TOK = ("The reference image shows this character's DESIGN from an older felt version on a white background: keep the "
           "design (face, hair, clothes, colours, proportions) but redraw it in THIS matte cut-PAPER style, every pink a "
           "coral-peach. THIS SHEET SHOWS ONLY THIS ONE CHARACTER; do NOT draw any other character. ")
REF_LINE = ("MATCH THE REFERENCE CHARACTER EXACTLY (same face, hair, clothes, colours, proportions and size); this is the "
            "same paper puppet in new poses. THIS SHEET SHOWS ONLY THIS ONE CHARACTER; do NOT draw any other character. ")
NO_BOT = " IMPORTANT: no flowers, no leaves, no plants, no botanical motifs on any character. No text."
CLIMB = ("CLIMBING seen from directly BEHIND (back of the head, no face): hanging on a rope that is NOT drawn, both arms "
         "stretched straight UP above the head with the hands closed one above the other (gripping the rope's line), the "
         "body hanging straight below them, ")


def TOK(role):
    return [RAW_C + f"ref_rp_toktok_{role}.png"]


def REF(role):
    return [RAW_C + f"ref_rp_{role}.png"]


JOBS = []


def cast(jid, n, who, body, refs, extra="", tok=False):
    JOBS.append({"id": jid, "kind": "bg", "refs": refs, "aspect": WIDE, "out": RAW_C + jid + ".png",
                 "prompt": f"A CHARACTER SHEET for a children's pop-up storybook: {n} separate full-body die-cut stand-up "
                 "figures in one horizontal row, " + BG + RP_CHAR + who + FACE + LEGS + extra + ROW +
                 (REF_TOK if tok else REF_LINE) + body + NO_BOT})


# ---------------------------------------------------------------- round 1: expression sheets (ref = 톡톡 single figure)
cast("cast_rp_rap_expr", "SEVEN", RAP,
     "SEVEN figures, left to right, all FRONT view, the long golden braid hanging over ONE shoulder down her front to "
     "her ankles: (1) CALM, standing, arms relaxed, a gentle smile; (2) SINGING: hands clasped at her chest, eyes "
     "closed in happy curves, mouth open in a small round 'la'; (3) SURPRISED: eyes wide, a round 'oh!' mouth, both "
     "hands up at her cheeks; (4) JOYFUL: both arms open wide, a big bright smile; (5) CHATTY: one finger at her chin, "
     "head tilted, an innocent curious little smile; (6) SAD: hands holding the end of her braid, eyebrows tilted, a "
     "small worried mouth; (7) WAVING: one hand waving high, a warm smile.", TOK("rap_stand"), extra=FRONT, tok=True)
cast("cast_rp_gothel_expr", "EIGHT", GOTHEL,
     "EIGHT figures, left to right: (1) FRONT, CALM: standing, both hands on the top of her stick, a stern closed mouth; "
     "(2) FRONT, POINTING: one arm stretched out pointing forward, a cross frown, mouth open scolding; (3) FRONT, WAND "
     "UP: the stick raised high above her head in one hand with a small gold star sparkle at its tip, a firm face; (4) "
     "FRONT, CRADLING A BABY: holding a small swaddled baby in a cream blanket in both arms, a softer face (the stick "
     "leaning on her arm); (5) FRONT, HOLDING BIG SCISSORS: a pair of big silver scissors raised in one hand, an angry "
     "frown (not scary); (6) FRONT, STARTLED-CROSS: both hands up, eyebrows high, mouth open 'what?!'; (7) SIDE PROFILE "
     "facing RIGHT standing calmly with her stick; (8) BACK view standing (the cloak and bun from behind, no face).",
     TOK("gothel_stand"), tok=True)
cast("cast_rp_prince_expr", "EIGHT", PRINCE,
     "EIGHT figures, left to right: (1) FRONT, CALM: standing, a friendly smile; (2) FRONT, CALLING UP: both hands "
     "cupped round his mouth, head tilted back a little, mouth open; (3) FRONT, LISTENING: one hand cupped behind his "
     "ear, a curious wondering face; (4) FRONT, DELIGHTED DISCOVERY: one fist up, eyes bright, a whispering open smile; "
     "(5) SIDE PROFILE facing RIGHT, HIDING: crouched low on bent knees, peeking forward, a finger at his lips; (6) FRONT, "
     "SAD: shoulders down, hands hanging, eyebrows tilted, a small sad mouth; (7) FRONT, HAPPY: both arms open wide, a "
     "big warm smile; (8) SIDE PROFILE facing RIGHT, HOLDING OUT A HAND: one arm reaching forward at chest height, palm "
     "open, a loving smile.", TOK("prince_stand"), tok=True)
cast("cast_rp_father_expr", "SIX", FATHER,
     "SIX figures, left to right: (1) FRONT, CALM: standing, a kind smile; (2) FRONT, PROMISING: one fist at his chest, a "
     "brave little nod; (3) SIDE PROFILE facing RIGHT, PULLING a plant out of the ground: bent forward, both hands down "
     "low gripping (the plant is NOT drawn), knees bent; (4) FRONT, SHOCKED: eyes wide, mouth a round 'oh!', both hands "
     "up; (5) FRONT, SORRY: hands together at his chest, eyebrows tilted, an apologetic face; (6) SIDE PROFILE facing "
     "RIGHT, TIPTOEING: sneaking, back a little hunched, one foot lifted on its toes, a hushed careful face.",
     TOK("father_stand"), tok=True)
cast("cast_rp_mother_expr", "FOUR", MOTHER,
     "FOUR figures, left to right, all FRONT view: (1) CALM, standing, hands resting on her rounded tummy, a gentle "
     "smile; (2) LONGING: hands clasped under her chin, looking up and aside, a wishful little sigh; (3) HAPPY: both hands "
     "at her cheeks, a bright smile; (4) SAD: one hand at her cheek, eyebrows tilted.", TOK("mother_window"), tok=True)

# ---------------------------------------------------------------- round 2: more poses + cycles (ref = round-1 crop)
WALK = ("WALK CYCLE: EIGHT full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one walk "
        "cycle in order: (1) CONTACT (legs wide apart, front heel down), (2) DOWN, (3) PASSING (one leg straight under the "
        "body, the other lifted and bent), (4) UP; arms swinging opposite to the legs, upright and steady, {face}, the "
        "legs clearly separated with an open magenta gap; (5)-(6) TWO BACK-VIEW frames walking AWAY (left foot lifted "
        "behind, then the right foot); (7)-(8) TWO FRONT-VIEW frames walking TOWARD the viewer (left foot forward, then "
        "the right foot). All eight the SAME scale as the reference, feet on one common baseline.")
RUN = ("RUN CYCLE (hurrying joyfully): SIX full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT "
       "of one run cycle in order: (1) CONTACT, (2) DOWN, (3) PASSING, (4) FLIGHT (both feet off the ground); leaning "
       "forward, arms pumping, legs clearly apart with an open magenta gap, a bright eager face; (5)-(6) TWO FRONT-VIEW "
       "frames running TOWARD the viewer (left knee up, then the right).")
cast("cast_rp_rap_short", "EIGHT", RAP_SHORT,
     "EIGHT figures, left to right: (1) FRONT, SAD: one hand touching her short hair, teary eyebrows, a small trembling "
     "mouth (no tears drawn); (2) FRONT, SINGING: hands clasped at her chest, eyes closed in happy curves, mouth a small "
     "round 'la'; (3) FRONT, SURPRISED-JOYFUL: both hands at her cheeks, eyes wide and shining, a big open smile; (4) "
     "SIDE PROFILE facing RIGHT, HOLDING OUT A HAND: one arm reaching forward at chest height, a loving smile; (5) FRONT, "
     "HAPPY: arms open wide, a big smile; (6) SIDE PROFILE facing RIGHT standing calmly; (7) BACK view standing (short "
     "hair from behind, no face); (8) FRONT, CALM: standing, a gentle smile.", REF("rap"))
cast("cast_rp_rap_short_walk", "EIGHT", RAP_SHORT, WALK.format(face="a gentle hopeful face"), REF("rap_short"))
cast("cast_rp_gothel_walk", "EIGHT", GOTHEL, WALK.format(face="a stern grumbling face, the stick in one hand"),
     REF("gothel"))
cast("cast_rp_gothel_more", "FOUR", GOTHEL,
     "FOUR figures, left to right: (1) " + CLIMB + "the cloak hanging down, the stick tucked in her belt, the RIGHT knee "
     "lifted; (2) the SAME climbing pose with the LEFT knee lifted and the hands shifted (the other hand on top); (3) FRONT, "
     "STERN TALK: one palm up, a firm closed-eyed grumbling face; (4) FRONT, SATISFIED: arms folded, a small proud smirk "
     "(not scary).", REF("gothel"))
cast("cast_rp_prince_more", "SIX", PRINCE,
     "SIX figures, left to right: (1) " + CLIMB + "the red cape hanging down, the RIGHT knee lifted; (2) the SAME climbing "
     "pose with the LEFT knee lifted and the hands shifted; (3) SIDE PROFILE facing RIGHT standing calmly; (4) BACK view "
     "standing (cape and hair from behind, crown, no face); (5) FRONT, FLOATING gently in the air: arms spread wide like "
     "wings, legs together and dangling, the cape fluttering up, a surprised-calm face; (6) FRONT, LOOKING UP: head tilted "
     "back, one hand shading his eyes, a puzzled wondering face.", REF("prince"))
cast("cast_rp_prince_walk", "EIGHT", PRINCE, WALK.format(face="a calm friendly face"), REF("prince"))
cast("cast_rp_prince_run", "SIX", PRINCE, RUN, REF("prince"))
cast("cast_rp_father_walk", "EIGHT", FATHER, WALK.format(face="a hushed careful face (tiptoeing a little)"),
     REF("father"))

# the window figures: the girl leaning on a window sill (only her upper body shows; the sill is NOT drawn)
WIN = ("WINDOW FIGURES: each shows ONLY the UPPER BODY from the waist up (cut off flat at the waist along a straight "
       "horizontal bottom edge, as if leaning out of a window whose sill is NOT drawn), FRONT view, arms resting forward "
       "on the (undrawn) sill line at the bottom edge. ")
cast("cast_rp_rap_window", "FIVE", RAP,
     WIN + "FIVE figures, left to right: (1) SMILING: hands resting on the bottom edge, a sweet smile, her braid over one "
           "shoulder; (2) SINGING: eyes closed in happy curves, mouth a small round 'la', hands clasped; (3) LETTING DOWN "
           "HER HAIR: both hands forward holding the TOP of her golden braid out over the bottom edge (the braid is cut "
           "off at the bottom edge: the rest is a separate piece), a kind smile; (4) SURPRISED: eyes wide, hands up at "
           "her cheeks; (5) WAVING: one hand waving, a bright smile.", REF("rap"))
cast("cast_rp_gothel_window", "TWO", GOTHEL,
     WIN + "TWO figures, left to right: (1) STERN: both hands on the bottom edge, a cross frown, mouth open scolding; (2) "
           "WAND UP: one hand raising her stick with a small gold star sparkle at its tip, a firm face.", REF("gothel"))

# ---------------------------------------------------------------- set / prop sheets (round 1, no character refs)
RP_GARDEN = PAPER + ("Plants are the subject here (veins as cut lines are fine). NO faces on anything (except the baby in "
                     "the cradle, piece 4), NO animals, NO people. ")
RP_ROOM = PAPER + ("MATERIAL PRINTS ONLY (stone blocks, wood grain, plaster, checked or plain cloth). NO faces, NO animals, "
                   "NO people. ")


def sheet(jid, n, style, body, refs=None):
    JOBS.append({"id": jid, "kind": "bg", "refs": refs or [], "aspect": WIDE, "out": RAW_A + jid + ".png",
                 "prompt": f"A PROP SHEET for a children's pop-up storybook: {n} separate die-cut stand-up cardboard "
                 "pieces, every piece standing on a flat bottom edge (the hinge), " + BG + style + body})


BRAID = ("a thick GOLDEN-YELLOW three-strand braid of hair (honey gold with lighter and darker gold paper strands) with "
         "small tomato-RED bows")
sheet("story_rp_garden", "FOURTEEN", RP_GARDEN,
      "Pieces, all straight on, in two rows: (1) a lush RAMPION plant (라푼젤 상추): a rosette of long smooth bright-green "
      "spoon-shaped leaves with a few slim stems of tiny BLUE-VIOLET bell flowers (blue-violet, never pink); (2) a SECOND "
      "rampion plant, a little different (more flower stems); (3) a long low RAMPION GARDEN BED seen from the front: a "
      "row of five rampion rosettes in dark tilled soil with a low stone edging (the widest piece); (4) a wooden CRADLE on "
      "rockers seen from the side, a sleeping baby's round face peeping out of a cream blanket (the only face); (5) a "
      "PULLED rampion plant: the leaf rosette with its long thick cream-white root dangling, a few soil crumbs; (6) a "
      "STRAIGHT VERTICAL segment of " + BRAID + " (two bows), its top and bottom ends cut perfectly flat and horizontal, "
      "very tall and narrow (about 8 times taller than wide); (7) the BOTTOM END of the same braid: the braid narrowing "
      "into a loose golden tassel tied with a red bow, the top end cut flat; (8) the CUT-OFF braid hanging from a small "
      "black iron HOOK: the hook at the top, the braid hanging straight down from it, its bottom a loose tassel; (9) a "
      "burst of gold and pale-green paper MAGIC SPARKLES (stars and dots in a round puff); (10) two golden paper MUSIC "
      "NOTES joined by a curl; (11) a small cluster of coral-peach and cream paper PETALS (five petals joined by thin "
      "curls); (12) a swirl of pale-blue paper WIND curls (three long curling strands, one piece); (13) a low ROSE-CANE "
      "hedge clump with soft green leaves and a few coral roses (a cosy bush to land in, no sharp thorns); (14) a pair of "
      "big silver SCISSORS lying open (small piece).")
sheet("story_rp_room", "TEN", RP_ROOM,
      "THE ROUND ROOM AT THE TOP OF A STONE TOWER, seen from INSIDE. Pieces, all straight on: (1) an INSIDE WALL panel of "
      "the round tower room: warm cream-grey stone blocks with plaster patches, a slim wooden beam along the top, plain "
      "(tall portrait panel, about 1.4 times taller than wide); (2) the SAME wall panel with a tall ARCHED WINDOW in the "
      "middle: the window opening shows the sky at dusk (peach and soft blue paper) over dark-green forest treetops, "
      "two cream curtains tied back, a deep stone sill; (3) the SAME wall panel with a small wooden SHELF holding a jug, "
      "two books and a candle; (4) the SAME wall panel with a hanging round MIRROR and a hook with a little cream "
      "cloak; (5) a small wooden BED with a patchwork quilt (side view); (6) a three-legged wooden STOOL; (7) a small "
      "round wooden TABLE with a clay jug of wildflowers; (8) a round braided RUG (seen from the front, flat); (9) a "
      "SPINNING WHEEL (small, wooden); (10) THE TOWER WINDOW SEEN FROM OUTSIDE: a small deep ARCHED stone window frame "
      "with two open wooden SHUTTERS swung outward, a protruding stone SILL at the bottom, the opening a solid DARK "
      "warm-brown shadow (no figure inside).")

# ---------------------------------------------------------------- the book: cover, title, back cover, title-page spot
import sys as _sys
_sys.path.insert(0, HERE)
import cover_jobs as _cj  # noqa: E402

JOBS += [
    _cj.art("cover_rp_art", [RAW_C + "ref_rp_rap.png", RAW_C + "ref_rp_prince.png", RAW_C + "ref_rp_gothel.png"],
            extra_refs_mat=False, subject=
            "All references are already PAPER: copy their material. SUBJECT: 라푼젤 (Rapunzel). A tall round grey-stone "
            "TOWER with a cone roof of slate-blue tiles stands in a green forest clearing; from its single high arched "
            "window RAPUNZEL (reference 1: golden hair, leaf-green dress) leans out smiling and lets her very long golden "
            "braid with small red bows hang all the way down the tower wall to the grass; at the bottom the PRINCE "
            "(reference 2: crown, red cape) looks up at her with a hand at his mouth calling. Behind a far tree the "
            "witch GOTHEL (reference 3: green cloak, grey bun) peeks out, small. SKY (top 35 percent): soft peach-to-blue "
            "dusk paper with thin cloud strips at the edges only. PALETTE: tower stone grey, forest greens, braid gold, "
            "prince red, Rapunzel green."),
    _cj.title("cover_rp_title", "The Korean title on one line, centred: '라푼젤'.",
              "Letter colours: warm golden yellow #e8b830 letters with a thin tomato-red #c8322b inner layer and a thin "
              "dark-brown cut line around each letter, a small golden braid with a red bow curling under the word as "
              "decoration (not touching or replacing any stroke). NEVER replace or decorate any stroke of a letter; "
              "every jamo plainly visible: 라 푼 젤."),
    _cj.back("back_rp_art", "cover_rp_art.png", "Evening after the story: a small thatched cottage in a flowery "
             "meadow, RAPUNZEL with short golden hair and the PRINCE walking away hand in hand along a path toward a far "
             "castle on a hill, coral petals in the air; far behind them the lone stone tower in the forest, empty. Warm "
             "sunset light, a few first stars."),
    _cj.spot("spot_rp", "a single long golden BRAID with small red bows hanging down from a small arched stone window "
             "with open wooden shutters.", refs=[RAW_A + "story_rp_room.png"]),
]

ROUND1 = ["cast_rp_rap_expr", "cast_rp_gothel_expr", "cast_rp_prince_expr", "cast_rp_father_expr", "cast_rp_mother_expr",
          "story_rp_garden", "story_rp_room"]

if __name__ == "__main__":
    out = os.path.join(HERE, "rapunzel_jobs.json")
    json.dump(JOBS, open(out, "w"), ensure_ascii=False, indent=1)
    print(len(JOBS), "jobs ->", out)
    for j in JOBS:
        print(" ", j["id"], len(j["prompt"]))
