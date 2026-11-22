#!/usr/bin/env python3
"""「늑대와 일곱 아기염소」 (wolf_goats) art jobs for tools/run_jobs.py (phase 1, 2026-11-23).

  python3 tools/art/wolf_goats_jobs.py            # writes tools/art/wolf_goats_jobs.json
  bash -c 'python3 tools/run_jobs.py tools/art/wolf_goats_jobs.json <ids>'

PAPER look only (user 2026-11-22: no felt anywhere, no stitching). Per-category style blocks (skill lesson: a shared
block leaks motifs): WG_CHAR (goats, wolf: printed detail only on clothing), WG_BUILD (the goats' cottage, furniture:
material prints only), WG_FX (chalk, flour, splash, stones: no plants, no faces).

Round 1: the goat lineup (design ref = 톡톡's wolf_goats goats, art_src/cast/raw/ref_wg_toktok.png), the wolf's new
figures (ref = the shared paper wolf of three_pigs, art_src/cast/raw/ref_wg_wolf.png), the cottage and room sheets, the
fx/props sheet. Round 2 references SINGLE-CHARACTER crops of the new goat lineup (ref_wg_mom / ref_wg_kid /
ref_wg_baby): a multi-character ref made the model draw its first character everywhere (witch_candy lesson).

The six older kids are ONE design drawn with a plain GREEN collar; tools/cast/wolf_goats_cast.py recolours the collar
per kid (red, orange, yellow, green, blue, indigo), so one expression / cycle sheet serves all six. The youngest (막내)
is smaller with a coral-red collar and a golden bell, its own sheets.
Key colour magenta #FF00FF: every pink is CORAL / PEACH / SALMON, every purple blue-violet.
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
COLOUR = ("COLOUR RULE: NO pink and NO magenta-ish colour anywhere: every 'pink' (inner ears, cheeks, noses) is a warm "
          "CORAL-PEACH or SALMON (like #F2A07B or #E8836B, clearly orange-leaning); any purple is a deep BLUE-violet. ")
PAPER = ("STYLE (same for every piece): flat orthographic view, a die-cut pop-up book piece made of MATTE CUT PAPER and "
         "thin cardstock: every colour area is a separate cut or torn sheet of coloured paper glued in layers (a lighter "
         "or darker paper layer on top for shading and detail), crisp cut edges or softly torn deckled edges, each layer "
         "edge with a thin darker cut line and a faint lighter rim on its upper-left (lit) side, fine paper-fibre grain, "
         "matte, no gloss. ABSOLUTELY NO felt, NO wool, NO fuzz, NO fabric or knitted texture, NO stitches, NO dashed "
         "stitch lines, NO sewing seams, NO embroidery. Details are small cut paper shapes or a printed line, never "
         "stitching. No perspective, no cast shadows, no drop shadows, no glow, no white sticker border. Warm European "
         "fairy-tale picture book for ages 3-7 (a meadow farm, a cosy cottage). " + COLOUR)
WG_CHAR = PAPER + ("PRINTED DETAIL only on clothing (the apron's pocket and dot print, the vest's patches and buttons). "
                   "Fur and faces are plain cut paper with a few layered tufts. NO flowers, NO leaves, NO botanical motifs "
                   "on anyone. ")
FACE = ("Faces are simple and sweet: dark dot or curved-line eyes, a tiny mouth, soft coral-peach cheek circles; the "
        "expression is big and readable from far away. ")
MOM = ("THE MOTHER GOAT (엄마 염소): a gentle mother goat who stands and walks UPRIGHT on her two hind legs like a person, "
       "a round cream-white face with a small cream beard tuft, two short curved tan horns, long floppy ears with "
       "coral-peach insides, kind dark eyes, coral-peach cheeks, cream-white body, small dark-brown hooves for hands and "
       "feet, a short cream tail; she wears a RED APRON-DRESS (pinafore) with a cream front pocket and a few tiny cream "
       "dots. ")
KID = ("A KID GOAT (아기 염소): a small round baby goat standing on FOUR legs like a real little goat, a big round "
       "cream-white head, two tiny tan horn nubs, long floppy ears with coral-peach insides, big dark dot eyes, coral-peach "
       "cheeks, a fluffy cream-white body, thin legs with small tan-brown hooves, a tiny tuft tail, and a plain GRASS-GREEN "
       "paper COLLAR (one flat green colour, #4CAF50) with a small round golden bell. ")
BABY = ("THE YOUNGEST KID (막내): the smallest baby goat, a little smaller and rounder than the other kids, standing on FOUR "
        "legs, a big round cream-white head with a soft curl of fluff on top, NO horns yet, long floppy ears with "
        "coral-peach insides, big shiny dark eyes, coral-peach cheeks, a fluffy cream-white body, small tan hooves, a "
        "tiny tuft tail, and a CORAL-RED paper COLLAR with a round golden bell. ")
WOLF = ("THE WOLF (늑대): EXACTLY the reference wolf: a lanky grey cartoon wolf who walks UPRIGHT on his hind legs, cream "
        "muzzle and chest ruff, pointed ears with orange insides, yellow sly eyes, a dark navy nose, a bushy grey tail with "
        "a dark tip, a mustard-ochre VEST with two buttons and a red patch and a blue patch. ")
FLOUR = ("From now on his two FRONT PAWS (hands) are dusted WHITE with flour (plain white paper paws with a few white "
         "flour specks), everything else grey as before. ")
LEGS = ("EVERY standing or walking figure has a clearly VISIBLE open magenta GAP between its legs; legs never touch or "
        "overlap; exactly the right number of legs (two for the wolf and the mother, four for a kid). ")
FRONT = ("FRONT figures: full body facing the viewer straight on (not turned), feet on one horizontal baseline. ")
SIDE = "SIDE figures: full body in clean side PROFILE facing to the RIGHT (nose to the right edge), one eye visible. "
BACK = "BACK figures: seen from directly BEHIND: back of the head and ears, tail toward the viewer, no face. "
ROW = ("All figures in ONE horizontal row with their feet on a common baseline near the bottom of the image, a wide magenta "
       "gap between them, the SAME character design in every figure. ")
REF_LINE = ("MATCH THE REFERENCE CHARACTER EXACTLY (same face, horns, ears, clothes, colours, proportions and size); this "
            "is the same paper puppet in new poses. THIS SHEET SHOWS ONLY THIS ONE CHARACTER; do NOT draw any other "
            "character. ")
NO_BOT = " IMPORTANT: no flowers, no leaves, no plants, no botanical motifs on any character. No text."

REF_TOKTOK = [RAW_C + "ref_wg_toktok.png"]
REF_WOLF = [RAW_C + "ref_wg_wolf.png"]


def REF(role):
    return [RAW_C + f"ref_wg_{role}.png"]


JOBS = []


def cast(jid, n, who, body, refs, extra=""):
    JOBS.append({"id": jid, "kind": "bg", "refs": refs, "aspect": WIDE, "out": RAW_C + jid + ".png",
                 "prompt": f"A CHARACTER SHEET for a children's pop-up storybook: {n} separate full-body die-cut stand-up "
                 "figures in one horizontal row, " + BG + WG_CHAR + who + FACE + LEGS + extra + ROW +
                 (REF_LINE if refs != REF_TOKTOK else "") + body + NO_BOT})


# ---------------------------------------------------------------- round 1: goat lineup (design ref = 톡톡)
cast("cast_wg_lineup", "FOUR", MOM + KID + BABY,
     "The reference image shows the character DESIGNS (an older felt version): keep the designs (cream goats, the "
     "mother's red apron-dress, floppy ears, little horns, bell collars) but redraw every figure in THIS matte cut-PAPER "
     "style, and make every pink a coral-peach. SIZES: the mother about 80 percent of the image height, a kid about 42 "
     "percent, the youngest about 34 percent. THE FOUR FIGURES, left to right: (1) THE MOTHER GOAT, FRONT, standing "
     "upright, a calm warm smile, holding an empty round woven basket on one arm; (2) A KID GOAT, FRONT view standing on "
     "four legs facing the viewer, a calm happy face, the GREEN collar and golden bell clearly visible; (3) A KID GOAT, "
     "SIDE profile facing RIGHT standing on four legs (four legs visible with gaps), calm happy face, green collar; "
     "(4) THE YOUNGEST KID, FRONT view on four legs, a sweet shy face, coral-red collar, golden bell.", REF_TOKTOK,
     extra=FRONT)

# ---------------------------------------------------------------- round 1: the wolf's new figures (ref = shared wolf)
cast("cast_wg_wolf_a", "SIX", WOLF,
     "SIX figures of THE WOLF, left to right: (1) SIDE facing RIGHT, KNOCKING: standing upright at an (invisible) door, "
     "one fist raised high ready to knock, a gruff grumpy open mouth; (2) FRONT, MUNCHING CHALK: holding a white chalk "
     "stick in both grey paws at his mouth, cheeks bulging, eyes squeezed shut, white chalk crumbs; (3) FRONT, FAKE SWEET "
     "VOICE: grey paws clasped under his chin, head tilted, eyes half closed, a sugary fake smile; (4) SIDE facing RIGHT, "
     "SHOWING THE WHITE PAW: crouching low, one WHITE flour-dusted front paw stretched far forward near the ground (as if "
     "slipping it under a door), the other white paw at his chest, a sly grin; (5) FRONT, SNEEZING: head thrown back, "
     "eyes squeezed shut, mouth wide in a big 'achoo', both WHITE flour-dusted front paws flung out, a small puff of "
     "white flour round his nose; (6) FRONT, SEARCHING: nose up sniffing the air, eyes narrowed, both WHITE flour-dusted "
     "front paws raised like claws ready to grab, a greedy grin.", REF_WOLF, extra=FRONT + SIDE)
cast("cast_wg_wolf_b", "SIX", WOLF + FLOUR,
     "SIX figures of THE WOLF, left to right: (1) ASLEEP LYING ON HIS BACK on the ground seen from the SIDE (head to the "
     "LEFT, feet to the right), a HUGE round full belly bulging up under the vest, eyes closed, mouth open snoring, white "
     "paws resting on the belly (a long low figure); (2) the SAME lying asleep pose, the huge belly now lumpy and round "
     "with a neat line of cross stitches made of thin dark paper strips down the middle (stones inside), still snoring "
     "(a long low figure); (3) FRONT, SITTING UP GROGGY on the ground, legs out, both white paws holding his huge heavy "
     "round belly, dizzy half-closed eyes; (4) SIDE facing RIGHT, LEANING FAR FORWARD over (an invisible) well rim to "
     "look down, one white paw on the huge round belly, the other reaching forward, mouth open thirsty; (5) TUMBLING "
     "HEAD FIRST downward: upside down, legs and tail kicking up in the air, arms down, shocked face (falling into a "
     "well); (6) FRONT, SOAKING WET: standing upright, fur flattened and dripping with pale-blue paper water drops, a "
     "puddle drip under his feet, shivering, shocked open mouth, tail drooping, belly normal size again.",
     REF_WOLF, extra=FRONT + SIDE)
cast("cast_wg_wolf_flour_walk", "EIGHT", WOLF + FLOUR,
     "WALK CYCLE: EIGHT full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one sneaky "
     "walk cycle in order: (1) CONTACT, (2) DOWN, (3) PASSING, (4) UP; leaning INTO the walk (forward, never back), a sly "
     "grin, white floury paws held up in front, legs clearly separated with an open magenta gap; (5)-(6) TWO BACK-VIEW "
     "frames walking AWAY (left foot lifted behind, then the right); (7)-(8) TWO FRONT-VIEW frames walking TOWARD the "
     "viewer (left foot forward, then the right). All eight the SAME scale as the reference, feet on one common baseline.",
     REF_WOLF + [RAW_C + "ref_wg_wolf_walk.png"])
cast("cast_wg_wolf_heavy_walk", "EIGHT", WOLF + FLOUR,
     "HEAVY WALK CYCLE with a HUGE ROUND FULL BELLY (he has eaten far too much): his belly is a big round ball bulging "
     "out under the short vest, both white paws holding the belly from below, a slow heavy waddle. EIGHT full-body "
     "figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one waddling walk cycle (CONTACT, DOWN, "
     "PASSING, UP), legs apart with an open magenta gap, leaning back a little under the weight, a sleepy satisfied face; "
     "(5)-(6) TWO BACK-VIEW frames waddling AWAY (belly sides showing past his hips); (7)-(8) TWO FRONT-VIEW frames "
     "waddling TOWARD the viewer (left foot forward, then the right). All eight the SAME scale, feet on one baseline.",
     REF_WOLF + [RAW_C + "ref_wg_wolf_walk.png"])
cast("cast_wg_wolf_wet_run", "SIX", WOLF,
     "RUN CYCLE, SOAKING WET (he fell into a well): fur flattened and dripping pale-blue paper water drops, a few drops "
     "flying off behind him, a scared crying face, normal slim belly, grey paws (the water washed the flour off). SIX "
     "full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one run cycle (CONTACT, DOWN, "
     "PASSING, FLIGHT with both feet off the ground), legs wide apart with an open magenta gap, arms pumping, leaning "
     "forward; (5)-(6) TWO BACK-VIEW frames running AWAY (left foot up behind, then the right). All six the SAME scale, "
     "the lowest foot on one baseline. NO burnt or red bottom, NO smoke.",
     REF_WOLF + [RAW_C + "ref_wg_wolf_walk.png"])

# ---------------------------------------------------------------- round 2: goats (ref = single-character crops)
cast("cast_wg_mom_expr", "SIX", MOM,
     "SIX figures of THE MOTHER GOAT, left to right: (1) FRONT, WARNING KINDLY: the empty basket on one arm, the other "
     "hoof's finger raised ('remember!'), a loving serious face; (2) FRONT, WAVING GOODBYE: basket on one arm, the other "
     "hand waving high, a warm smile; (3) FRONT, SHOCKED: both hooves at her cheeks, eyes wide, mouth a round 'oh!', no "
     "basket; (4) FRONT, CALLING: both hooves cupped round her mouth calling out, worried eyebrows, no basket; (5) FRONT, "
     "DETERMINED: holding big silver SCISSORS in one hand and a needle with a long red thread in the other, a brave "
     "determined face, a small round sewing basket hooked on her arm; (6) FRONT, JOYFUL DANCE: one leg lifted, both arms "
     "up, eyes closed in happy curves, a big open smile.", REF("mom"), extra=FRONT)
cast("cast_wg_mom_views", "SIX", MOM,
     "SIX figures of THE MOTHER GOAT, left to right: (1) SIDE facing RIGHT standing, basket on her arm, calm; (2) BACK "
     "figure standing, basket on her arm; (3) SIDE facing RIGHT, SHUSH: tiptoeing, one hoof at her lips 'shh!', the sewing "
     "basket on her arm; (4) SIDE facing RIGHT, KNEELING on both knees, leaning forward, both hands working low in front "
     "of her with big silver scissors (busy careful face); (5) SIDE facing RIGHT, KNEELING on both knees, leaning forward, "
     "sewing low in front of her with a needle and long red thread (careful face); (6) FRONT, OPEN ARMS: kneeling on one "
     "knee with both arms open wide for a hug, a loving teary-happy smile.", REF("mom"), extra=SIDE + BACK + FRONT)
WALK8 = ("WALK CYCLE: EIGHT full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one walk "
         "cycle in order: (1) CONTACT, (2) DOWN, (3) PASSING, (4) UP; a calm face in profile, legs clearly separated with "
         "an open magenta gap; (5)-(6) TWO BACK-VIEW frames walking AWAY; (7)-(8) TWO FRONT-VIEW frames walking TOWARD the "
         "viewer. All eight the SAME scale as the reference, feet on one common baseline. ")
WALK8_Q = ("WALK CYCLE of a FOUR-LEGGED little goat: EIGHT full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE "
           "frames facing RIGHT of one trotting walk cycle (diagonal leg pairs swapping), all four legs visible with open "
           "magenta gaps between them, a happy face in profile; (5)-(6) TWO BACK-VIEW frames trotting AWAY (rump, tail and "
           "back legs toward the viewer, one hind leg lifted, then the other); (7)-(8) TWO FRONT-VIEW frames trotting "
           "TOWARD the viewer (one front leg lifted, then the other). All eight the SAME scale as the reference, hooves on "
           "one common baseline. ")
RUN6_Q = ("RUN CYCLE of a FOUR-LEGGED little goat: SIX full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames "
          "facing RIGHT of one GALLOP (gathered: all four legs tucked under; extended: front legs reaching forward and "
          "hind legs stretched back; landing on the front legs; pushing off the hind legs), legs with open magenta gaps, "
          "ears flying back, a hurried worried face; (5)-(6) TWO BACK-VIEW frames running AWAY (rump and tail toward the "
          "viewer, hind legs kicking). All six the SAME scale, the lowest hoof on one baseline. ")
cast("cast_wg_mom_walk", "EIGHT", MOM,
     WALK8 + "She walks upright on her hind legs with the empty woven basket hooked on her near arm in every frame, her "
     "apron-dress swaying.", REF("mom"))
cast("cast_wg_kid_expr", "SIX", KID,
     "SIX figures of THE KID GOAT (the SAME kid every time, the same GREEN collar), left to right: (1) SIDE facing RIGHT, "
     "HAPPY HOP: leaping in the air with all four legs tucked, ears flying, a big happy open mouth; (2) FRONT on four legs, "
     "SCARED: ears flat back, eyes wide, trembling, a small wobbly mouth; (3) FRONT on four legs, SUSPICIOUS: frowning, "
     "eyes narrowed, head tilted, mouth a small flat line ('that's not mom!'); (4) FRONT on four legs, SHOUTING: mouth wide "
     "open shouting, brave frown, ears up; (5) FRONT on four legs, OVERJOYED: eyes closed in happy curves, a big smile "
     "(fooled, thinking mother is back); (6) FRONT, DANCING on the two hind legs with the front legs up, a big laugh.",
     REF("kid"), extra=FRONT + SIDE)
cast("cast_wg_kid_views", "SIX", KID,
     "SIX figures of THE KID GOAT (same GREEN collar), left to right: (1) BACK view standing on four legs (rump, tail and "
     "the back of the ears toward the viewer); (2) SIDE facing RIGHT standing on four legs, SCARED: ears back, crouched; "
     "(3) SIDE facing RIGHT, PUSHING: head down, pushing forward with the forehead and front hooves (pushing something "
     "round in front of it; draw NOTHING in front, only the goat); (4) FRONT on four legs, LOOKING UP happily with a "
     "sideways glance; (5) FRONT, SITTING on its haunches, ears perked, attentive; (6) SIDE facing RIGHT, POPPING OUT: a "
     "springy jump upward with legs stretched down, eyes wide, mouth open 'mama!'.", REF("kid"), extra=FRONT + SIDE + BACK)
cast("cast_wg_kid_walk", "EIGHT", KID, WALK8_Q, REF("kid"))
cast("cast_wg_kid_run", "SIX", KID, RUN6_Q, REF("kid"))
cast("cast_wg_baby_expr", "SIX", BABY,
     "SIX figures of THE YOUNGEST KID (the SAME little goat, coral-red collar), left to right: (1) FRONT on four legs, "
     "LOOKING AROUND worried, head turned, ears up; (2) FRONT on four legs, CRYING: big eyes with tear drops (pale-blue "
     "paper drops), mouth wobbling; (3) SIDE facing RIGHT, JOY JUMP: springing up with all four legs stretched, mouth "
     "open 'mama!'; (4) FRONT on four legs, WHISPERING: leaning in, ears forward, a tiny 'o' mouth, eyes wide (softly "
     "saying 'careful'); (5) BACK view standing on four legs; (6) SIDE facing RIGHT standing on four legs, calm.",
     REF("baby"), extra=FRONT + SIDE + BACK)
cast("cast_wg_baby_walk", "EIGHT", BABY, WALK8_Q, REF("baby"))
cast("cast_wg_baby_run", "SIX", BABY, RUN6_Q, REF("baby"))

# ---------------------------------------------------------------- sets and props (no characters unless noted)
WG_BUILD = PAPER + ("MATERIAL PRINTS ONLY (straw thatch strands, cream plaster, wood grain, stone, woven wicker, checked "
                    "cloth). NO flowers, NO leaves, NO botanical motifs, NO animals, NO people. ")
WG_FX = PAPER + "NO plants, NO leaves, NO faces, NO characters. "


def sheet(jid, n, style, body, refs=None):
    JOBS.append({"id": jid, "kind": "bg", "refs": refs or [], "aspect": WIDE, "out": RAW_A + jid + ".png",
                 "prompt": f"A PROP SHEET for a children's pop-up storybook: {n} separate die-cut stand-up cardboard "
                 "pieces, every piece standing on a flat bottom edge (the hinge), " + BG + style + body})


sheet("story_wg_cottage", "SIX", WG_BUILD,
      "THE GOAT FAMILY'S COTTAGE and its parts, all drawn straight on (front elevation, no perspective), the SAME house "
      "design in every piece: (1) THE COTTAGE FRONT, the largest piece: a cosy one-storey European farm cottage, cream "
      "plaster walls between dark-brown timber beams, a thick golden STRAW THATCH roof with a rounded ridge, a low grey "
      "fieldstone base, ONE arched dark-green plank FRONT DOOR in the middle standing on a single flat stone step, a "
      "WINDOW on each side of the door (small square panes, dark-blue glass, cream shutters), a small stone chimney on "
      "the roof; the house about twice as wide as it is tall; (2) the FRONT DOOR LEAF alone: the same arched green plank "
      "door with an iron ring handle, exactly the size it has in piece 1; (3) THE COTTAGE BACK: the same house from "
      "behind, cream plaster and timber, one small window, the thatch roof, no door; (4) THE ROOM'S BACK WALL seen from "
      "INSIDE: a wide cream plaster wall with timber beams, a small window with checked curtains in the middle, a wooden "
      "shelf with jugs and plates, a low-ceiling beam along the top, as wide as the cottage front; (5) THE FRONT WALL "
      "SEEN FROM INSIDE: the same width as piece 1, cream plaster and beams, the arched door in the middle (closed, "
      "planks seen from inside with a wooden bar latch) and a window on each side showing a bright day outside; (6) a "
      "FLOOR card: wide warm wooden floorboards seen from straight above, a round braided rug in the middle (a flat "
      "rectangle about as wide as piece 1).")
sheet("story_wg_room", "FOURTEEN", WG_BUILD,
      "COTTAGE FURNITURE, each piece a separate stand-up card, front view: (1) a TALL GRANDFATHER CLOCK (longcase clock), "
      "warm walnut wood, a round cream clock face with dark hands at the top, a tall narrow case below with a glass door "
      "showing a brass pendulum, about three times as tall as it is wide; (2) the SAME clock with its tall case door "
      "swung OPEN to the right: inside the case a dark, empty cosy space, the pendulum pushed to one side; (3) a wooden "
      "BED with a carved head and foot board, a plump white pillow and a coral-and-cream PATCHWORK QUILT smooth on it, "
      "seen from the long side; (4) a big round woven wicker LAUNDRY BASKET with two handles, white sheets folded inside; "
      "(5) a wooden TABLE with a long red-and-cream CHECKED TABLECLOTH hanging down to the floor on all sides; (6) a "
      "wooden CHAIR with a heart cut-out in the back, front view; (7) the same CHAIR toppled over, lying on its side; "
      "(8) the coral-and-cream PATCHWORK QUILT thrown in a crumpled heap on the floor; (9) the wicker LAUNDRY BASKET "
      "tipped over on its side with white sheets spilling out; (10) the TABLE with its checked cloth pulled half off and "
      "hanging crooked, a cup tipped over; (11) a tall wooden DRESSER with plates and cups on its shelves; (12) a small "
      "black iron STOVE with a kettle on top; (13) a small round wicker SEWING BASKET with a pair of silver scissors, a "
      "spool of red thread and a pincushion; (14) a three-legged wooden STOOL.")
sheet("story_wg_hide", "FIVE", WG_BUILD + "This sheet MAY show the little kid goats of the reference, hiding. ",
      "HIDING PLACES with the little KID GOATS of the reference image (cream goats, floppy coral-lined ears, tiny horn "
      "nubs, coloured collars) hiding in them, the same furniture design as described: (1) a wooden BED with a "
      "coral-and-cream PATCHWORK QUILT that has THREE lumpy round humps under it, from one hump a pair of floppy ears "
      "pokes out, from another a little tail, from the third four tiny hooves (three kids hiding under the quilt); (2) a "
      "big round woven wicker LAUNDRY BASKET full of white sheets with ONE kid goat's two floppy ears and horn nubs and "
      "big eyes peeking over the rim; (3) a wooden TABLE with a long red-and-cream CHECKED TABLECLOTH hanging to the "
      "floor, under its hem two pairs of little tan hooves and one tiny tail peeking out (two kids hiding under the "
      "table); (4) a TALL GRANDFATHER CLOCK (walnut wood, round cream face) with its tall case door OPEN, the YOUNGEST "
      "KID (smallest, no horns, coral-red collar, golden bell) squeezed inside the case, peeking out shyly; (5) the same "
      "TALL GRANDFATHER CLOCK with its case door CLOSED and two big shiny little eyes peeking through the small glass "
      "pane of the case door.", REF("kid") + REF("baby") + [RAW_A + "story_wg_room.png"])
sheet("story_wg_meadow", "SIX", PAPER + "NO animals, NO people. ",
      "MEADOW SET PIECES for a European fairy-tale meadow (a farm with a well under a big tree), each a separate stand-up "
      "card, front view: (1) a BIG OLD SHADY OAK TREE, the largest piece: a thick gnarled brown trunk with roots at the "
      "base, a huge round layered canopy of several greens cut as overlapping paper leaf clusters, about as wide as it is "
      "tall; (2) an old round STONE WELL: a waist-high round wall of grey fieldstones, two wooden posts with a little "
      "shingled roof, a wooden winch with a rope and a wooden bucket hanging; the well's mouth shows as a dark opening "
      "above the stones; (3) the FRONT HALF of the same well's stone rim alone (just the curved front stone wall, the same "
      "width and stones as in piece 2, no posts, no roof): a low curved band; (4) a long low leafy HEDGE BUSH of round "
      "green paper clumps, about three times as wide as tall (something to hide behind); (5) a WOODEN SIGNPOST with two "
      "blank arrow boards (no letters); (6) a small WOODEN MARKET STALL with a striped cream-and-red awning and a counter "
      "with a few boxes of white CHALK sticks and jars on it.")
sheet("story_wg_fx", "TWELVE", WG_FX,
      "SMALL STORY PIECES: (1) three short white CHALK sticks in a little pile; (2) a big white FLOUR SACK, tied at the "
      "top, a little flour spilling, burlap tan paper; (3) a soft round PUFF CLOUD of white flour (layered white paper "
      "billows); (4) a big SPLASH of water bursting upward (layered pale-blue and white paper drops and a crown of water); "
      "(5) a round grey STONE; (6) an oval grey-brown STONE; (7) a speckled round STONE, a bit bigger; (8) a small white "
      "CHALK stick bitten in half with crumbs; (9) a few pale-blue WATER DROPS (three teardrops); (10) a round "
      "pale grey-blue SNORE BUBBLE (a plain round bubble, no text); (11) a little pile of grain "
      "and a wooden scoop; (12) a sparkle burst of cream-gold paper stars.")


if __name__ == "__main__":
    out = os.path.join(HERE, "wolf_goats_jobs.json")
    json.dump(JOBS, open(out, "w"), ensure_ascii=False, indent=1)
    print(out, len(JOBS), "jobs:", " ".join(j["id"] for j in JOBS))
