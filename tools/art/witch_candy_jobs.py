#!/usr/bin/env python3
"""「사탕 마녀의 핼러윈」 (witch_candy) art jobs for tools/run_jobs.py (phase 1, 2026-11-19).

  python3 tools/art/witch_candy_jobs.py            # writes tools/art/witch_candy_jobs.json
  python3 tools/run_jobs.py tools/art/witch_candy_jobs.json <ids>

Round 1 (no new refs): the cast lineup (design reference = 톡톡's witch_candy cast, redrawn in our die-cut look) and
every prop / set sheet. Round 2 references the new lineup so faces and clothes stay identical across sheets.

Style blocks are per category (skill lesson: a shared block printed leaves on the sun):
- WC_CHAR: characters. Printed detail ONLY on clothing; skin, fur, faces plain.
- WC_PROP: Halloween props and candies. No flower / leaf / vine motifs (a pumpkin stem curl and a strawberry leaf cap
  are the only plant shapes, because the objects are those things).
- WC_BUILD: the candy shop and its room. Material prints only (plaster, planks, tiles, stone), no botanical motifs.
Key colour: magenta #FF00FF. The slicer keys hue 278-337°, so every purple must be BLUE-violet (hue < 270°):
indigo plum like #4B3A7A, never reddish purple or pink. Pinks are avoided (coral / peach instead).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_C = "art_src/cast/raw/"
RAW_A = "art_src/atlas/raw/"
WIDE = "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)"
LAND = "landscape 3:2 at the largest available size (1536x1024)"

BG = ("on a perfectly flat, uniform, solid pure MAGENTA background (#FF00FF, RGB 255,0,255) with no texture, no gradient, "
      "no vignette, no shadows on the background. Every piece is fully separate and isolated, with a clear empty magenta gap "
      "of at least 40 pixels on every side; pieces never touch or overlap each other and never touch the image border. "
      "No grid lines, no labels, no text, no letters, no numbers. ")
PURPLE = ("COLOUR RULE: every purple is a deep BLUE-VIOLET indigo plum (like #4B3A7A or #3E3470), clearly bluish, never a "
          "reddish purple, never pink, never magenta. No hot pink or bubble-gum pink anywhere (cheeks and inner ears are a "
          "soft coral-peach). ")
WC_CHAR = (
    "STYLE (same for every piece): flat orthographic view, like a printed die-cut pop-up book piece made of matte felt and "
    "cardstock, no perspective, no cast shadows, no drop shadows, no glow, no outline stroke in magenta, no white sticker "
    "border. Each part has ONE flat base colour with subtle matte felt/cardstock grain and a slightly gouache/screen-printed "
    "look, warm friendly cut-paper children's storybook style for ages 3-7, cute and gentle, cosy Halloween, never scary. "
    "PRINTED DETAIL (stitched dashed seams, small stamped dots, tiny stars, stripes) ONLY on CLOTHING (hats, capes, dresses, "
    "stockings, costumes). Skin, fur, faces, ears, hands and feet are PLAIN with only a few soft stitched seam lines. NO "
    "flowers, NO leaves, NO vines, NO botanical motifs anywhere. Matte, no gloss, no photo texture, no 3D render. PALETTE: "
    "pumpkin orange, ochre/mustard, golden yellow, cream, warm browns, mint green, deep blue-violet indigo plum, sky blue, "
    "brick red, charcoal. " + PURPLE)
FACE = ("Faces are simple and sweet: two dark dot or curved-line eyes, a tiny mouth, round soft coral-peach cheek circles; "
        "the expression is big and readable from far away. ")
DAHYUN = ("DAHYUN: a little girl about 6 years old, storybook proportions about 2.5 heads tall (a big round head), a round "
          "cream-peach face, shoulder-length straight dark-brown BOB hair with straight bangs; dressed as a LITTLE WIZARD: a "
          "deep blue-violet indigo pointed wizard HAT with a soft drooping tip and one golden-yellow star on it, a short "
          "blue-violet indigo CAPE tied with an orange bow at the neck, a cream-beige dress under the cape, orange-and-cream "
          "STRIPED STOCKINGS, red round-toed shoes. ")
WITCH = ("THE CANDY WITCH: a kind, quirky, ROUND grown-up lady about 1.6 times as tall as Dahyun, a round soft body, a round "
         "friendly face with coral-peach cheeks and a small ROUND button nose (NOT pointy, NO warts, NO long nails, NO green "
         "skin, never scary), a big cloud of MINT-GREEN CURLY hair made of round spiral curls, a deep blue-violet indigo plum "
         "pointed witch HAT with a soft bent tip and a little golden star dangling from the tip, worn a little crooked, a deep "
         "blue-violet plum dress with a puffy skirt, a cream scalloped collar, an ORANGE belt with small yellow stars, "
         "orange-and-cream striped stockings, round brown shoes. ")
CAT = ("HOBAKI THE CAT: a chubby ORANGE tabby cat (pumpkin-orange fur, darker orange stripes, a cream-white chest, muzzle and "
       "paws, round friendly dark dot eyes, coral-peach cheek circles, a striped tail); a real cat on four legs (NOT a black "
       "cat), about half as tall as Dahyun when sitting. ")
RABBIT = ("THE RABBIT FRIEND: a small white rabbit child who stands upright like a person, the same height as Dahyun "
          "(ears included), long ears with coral-peach inner ears, a short golden-yellow CAPE with little stars tied with a "
          "ribbon, red shoes. ")
BEAR = ("THE BEAR FRIEND: a small warm-brown bear cub child who stands upright like a person, the same height as Dahyun, "
        "dressed in a round orange ribbed PUMPKIN COSTUME body suit, a tiny pumpkin-stem cap on the head, brown shoes. ")
FOX = ("THE FOX FRIEND: a small orange fox child who stands upright like a person, the same height as Dahyun, cream muzzle and "
       "chest, a bushy tail with a white tip, a cream CRESCENT-MOON hat, a short blue-violet indigo cape, brown boots. ")
LEGS = ("EVERY standing or walking figure has a clearly VISIBLE open magenta GAP between the two legs from the hem (or the "
        "crotch) all the way down to the feet; legs never touch or overlap; hands never overlap the legs. Exactly two arms "
        "and two legs (four legs for the cat). ")
FRONT = ("FRONT figures: full body facing the viewer straight on (not turned), symmetric, feet a little apart on one "
         "horizontal baseline, the feet / shoes SEEN FROM THE FRONT pointing at the viewer (never turned outward). ")
SIDE = ("SIDE figures: full body in clean side PROFILE facing to the RIGHT (nose to the right edge), one eye visible. ")
BACK = ("BACK figures: seen from directly BEHIND walking away: back of the head / hat / cape, heels toward the viewer, legs "
        "apart with a gap, no face. ")
ROW = ("All figures in ONE horizontal row with their feet on a common baseline near the bottom of the image, a wide magenta "
       "gap between them, the SAME character design in every figure. ")
REF_LINE = ("MATCH THE REFERENCE CHARACTER EXACTLY (same face, hair, clothes, colours, proportions and size); this is the same "
            "paper puppet in new poses. ")
NO_BOT = " IMPORTANT: no flowers, no leaves, no plants, no vines, no botanical motifs anywhere on any piece."

REF_TOKTOK = [RAW_C + "ref_wc_lineup.png"]
REF = [RAW_C + "cast_wc_lineup.png"]

JOBS = []


def cast(jid, n, who, body, refs=REF, extra=""):
    JOBS.append({"id": jid, "kind": "bg", "refs": refs, "aspect": WIDE, "out": RAW_C + jid + ".png",
                 "prompt": f"A CHARACTER SHEET for a children's pop-up storybook: {n} separate full-body die-cut stand-up "
                 "figures in one horizontal row, " + BG + WC_CHAR + who + FACE + LEGS + extra + ROW +
                 (REF_LINE if refs is REF else "") + body + NO_BOT})


# ---------------------------------------------------------------- round 1: lineup (design reference = 톡톡 cast)
cast("cast_wc_lineup", "SIX", DAHYUN + WITCH + CAT + RABBIT + BEAR + FOX,
     "The reference image shows the character DESIGNS (face, hair, colours, costumes) from an older version: keep those "
     "designs but redraw every figure in THIS printed die-cut style. SIZES: Dahyun, the rabbit, the bear and the fox about "
     "the same height (about 55 percent of the image height, the rabbit's ears included), the witch about 1.6 times as tall "
     "(about 88 percent of the image height), the cat sitting about half Dahyun's height. THE SIX FIGURES, left to right, "
     "all FRONT figures with a calm gentle face (soft open dot eyes, a small calm smile, NOT a big grin), arms hanging "
     "relaxed a little away from the body: (1) DAHYUN; (2) THE CANDY WITCH, hands folded in front of her belt; (3) HOBAKI "
     "THE CAT sitting upright facing the viewer, front paws together, tail curled round beside the paws; (4) THE RABBIT; "
     "(5) THE BEAR; (6) THE FOX, tail curling out beside one leg without closing the leg gap.",
     refs=REF_TOKTOK, extra=FRONT)

# ---------------------------------------------------------------- round 2: expressions (ref = the new lineup)
cast("cast_dahyun_expr_a", "FIVE", DAHYUN,
     "FIVE FRONT figures of DAHYUN, left to right: (1) EXCITED: holding a small orange pumpkin-shaped invitation card up in "
     "both hands at her chest, eyes wide and sparkly, mouth open in a happy 'oh!'; (2) YUCK: grossed-out comic face, eyes "
     "squeezed, tongue out, one hand raised flat in front of her chest, leaning back a little; (3) EAGER: one arm raised "
     "high (hand up, volunteering), big determined smile; (4) EATING: holding a round candy at her mouth with one hand, "
     "eyes closed in delight, cheeks bulging happily; (5) REACHING: one arm stretched out to the side pointing at something "
     "at shoulder height, curious open-mouthed smile.", extra=FRONT)
cast("cast_dahyun_expr_b", "FIVE", DAHYUN,
     "FIVE figures of DAHYUN, left to right: (1) FRONT, GHOST-PLAY: both arms raised up high with the hands drooping like a "
     "silly ghost, her LIPS coloured solid BLACK (a round black 'O' mouth saying 'oooh'), eyes giggling, not scary; (2) "
     "FRONT, HAPPY WAVE: one hand waving high, big open smile; (3) FRONT, WOW: both hands at her cheeks, eyes wide, mouth a "
     "big round 'O' of amazement; (4) SIDE figure facing RIGHT, standing calmly (both feet on the baseline, a small gap "
     "between them), gentle face; (5) BACK figure standing, seen from behind (hat, cape with the bow ends, stockings).",
     extra=FRONT + SIDE + BACK)
cast("cast_witch_expr_a", "FIVE", WITCH,
     "FIVE FRONT figures of THE CANDY WITCH, left to right: (1) WELCOME: one arm raised high waving hello, the other "
     "open, a big warm open smile; (2) MAGIC STIR: both arms stretched out together toward the LEFT side of the image at "
     "waist height, fingers spread, little golden star sparkles attached to her fingertips (touching the hands, not "
     "floating), a delighted concentrating smile; (3) GIGGLE: one hand at her mouth giggling 'hee hee', eyes closed in "
     "happy curves, shoulders up; (4) SURPRISED: both hands raised beside her face, eyes wide, mouth open shouting 'wait!'; "
     "(5) OFFERING: holding out one open palm in front of her with a small round orange candy on it, a kind smile.",
     extra=FRONT)
cast("cast_witch_expr_b", "FIVE", WITCH,
     "FIVE figures of THE CANDY WITCH, left to right: (1) FRONT, GHOST-PLAY: both arms up with drooping hands like a silly "
     "ghost, LIPS coloured solid BLACK in a round 'O', giggling eyes; (2) FRONT, PUMPKIN MAGIC: her round tummy has become "
     "a big round orange PUMPKIN with ribs and a tiny stem curl at the belt, glowing warm (a lighter golden centre printed on "
     "it, no real glow outside the silhouette), her cheeks orange too, delighted face, arms out; (3) FRONT, TWO CANDIES: "
     "holding one round candy up in each raised hand, a cheeky proud grin; (4) SIDE figure facing RIGHT, standing calmly, "
     "kind face; (5) BACK figure standing, seen from behind (hat, mint curls, dress, stockings).",
     extra=FRONT + SIDE + BACK)
cast("cast_cat_expr", "SIX", CAT,
     "SIX figures of HOBAKI THE CAT, left to right: (1) SITTING front, calm; (2) SITTING front, MEOWING with the mouth "
     "open, eyes closed happily; (3) SITTING front, holding a paw over the nose (pinching the nose at a bad smell), eyes "
     "squeezed, three small wavy smell lines attached to the paw; (4) STARTLED: standing on four legs side view facing "
     "RIGHT, back arched, fur puffed, tail straight up, eyes wide, all four feet on the baseline with gaps between the legs; "
     "(5) GHOST-PLAY: sitting up on the hind legs, both front paws raised like a silly ghost, LIPS / mouth solid BLACK round "
     "'O'; (6) FISH MAGIC: the cat with a big blue FISH TAIL instead of the hind legs and tail, floating, side view facing "
     "RIGHT, little round bubble dots attached, happy face.")
cast("cast_friends_expr_a", "SIX", RABBIT + BEAR + FOX,
     "SIX FRONT figures, left to right: (1) THE RABBIT cheering, both arms up; (2) THE BEAR cheering, both arms up; (3) THE "
     "FOX cheering, both arms up; (4) THE RABBIT with FROG MAGIC: green frog legs with webbed feet instead of her legs, "
     "crouched ready to hop, a big happy face; (5) THE BEAR with DUCK MAGIC: big orange webbed duck feet, a little tuft of "
     "yellow duck tail feathers at the back, a tiny orange beak-shaped cap, leaning to one side waddling; (6) THE FOX with "
     "BAT MAGIC: small blue-violet bat wings spread from her back, pointed little ears on her cap, hovering with both feet "
     "slightly off the baseline.", extra=FRONT)
cast("cast_friends_expr_b", "SIX", RABBIT + BEAR + FOX,
     "SIX figures, left to right: (1) THE RABBIT, FRONT, GHOST-PLAY: both arms up with drooping hands, LIPS solid BLACK "
     "round 'O', giggling; (2) THE BEAR, the same ghost-play; (3) THE FOX, the same ghost-play; (4) THE RABBIT, SIDE figure "
     "facing RIGHT, standing calmly; (5) THE BEAR, SIDE figure facing RIGHT, standing; (6) THE FOX, SIDE figure facing "
     "RIGHT, standing.", extra=FRONT + SIDE)

# ---------------------------------------------------------------- transformations of Dahyun (6 results)
cast("cast_dahyun_tf_a", "FIVE", DAHYUN,
     "FIVE MAGIC TRANSFORMATION figures of DAHYUN (same head, same face, same hair and hat; the head the SAME size as in "
     "the reference), left to right: (1) STRAWBERRY, FRONT: her dress has become a round red STRAWBERRY suit with small "
     "yellow seed dots, a green leaf cap on top of her hat, red cheeks, arms out happily, legs apart; (2) STRAWBERRY BALL: "
     "she is curled up into a round red strawberry BALL (seed dots, green leaf cap), only her face, hands and feet showing, "
     "a comic dizzy 'help!' face, as if rolling; (3) DUCK, FRONT: big orange webbed DUCK FEET instead of shoes, a tuft of "
     "yellow duck tail feathers behind, a tiny orange beak-shaped cap on the hat, surprised looking down at her feet, legs "
     "apart; (4) FISH, SIDE view facing RIGHT: a big blue FISH TAIL with fins instead of her legs, floating horizontally as "
     "if swimming in the air, arms forward, a blissful smile, three round bubble dots attached to her mouth; (5) FROG JUMP, "
     "SIDE view facing RIGHT: green FROG LEGS with webbed feet, mid-leap with the legs stretched back, arms forward, a big "
     "happy open mouth.")
cast("cast_dahyun_tf_b", "FIVE", DAHYUN,
     "FIVE MAGIC TRANSFORMATION figures of DAHYUN (same head, face, hair and hat, the head the SAME size as in the "
     "reference), left to right: (1) FROG SIT, FRONT: green frog legs folded in a frog crouch, one hand waving high, big "
     "smile, round frog-eye bumps on her hat; (2) PUMPKIN, FRONT: her round tummy and cheeks have become a big orange "
     "PUMPKIN with ribs, a lighter golden glowing centre printed on the belly (no glow outside the silhouette), amazed happy "
     "face, arms out, legs apart; (3) BAT, SIDE view facing RIGHT: small blue-violet BAT WINGS spread UP from her back, "
     "flying with the feet off the baseline, joyful face; (4) BAT, SIDE view facing RIGHT: the same but the wings swept "
     "DOWN; (5) GHOST PARADE, FRONT: both arms up, hands drooping, BLACK LIPS round 'O', stepping toward the viewer with the "
     "left foot forward, legs apart.")

# ---------------------------------------------------------------- drawn cycles
WALK8 = ("WALK CYCLE: EIGHT full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one walk "
         "cycle in order: (1) CONTACT, (2) DOWN, (3) PASSING, (4) UP; a calm happy face in profile, legs clearly separated "
         "with an open magenta gap, arms swinging opposite to the legs; (5)-(6) TWO BACK-VIEW frames walking AWAY (left foot "
         "lifted behind, then the right), arms swinging; (7)-(8) TWO FRONT-VIEW frames walking TOWARD the viewer (left foot "
         "stepping forward, then the right; shoes seen from the front), calm happy face. All eight the SAME scale as the "
         "reference, feet on one common baseline. ")
GHOST6 = ("GHOST-PLAY PARADE MARCH: SIX full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one "
          "marching walk cycle in order (CONTACT, DOWN, PASSING, UP), both arms raised forward and up with drooping hands "
          "like a silly ghost, the LIPS painted thick solid JET-BLACK like black lipstick (a big black ring of lips around a round 'oooh' mouth, clearly black from far away; normal clothes, NO sheet costume), giggling eyes, legs clearly separated with an "
          "open magenta gap, a bouncy step; (5)-(6) TWO FRONT-VIEW frames marching TOWARD the viewer (left foot forward, then "
          "the right), the same arms-up black-lips 'oooh'. All six the SAME scale as the reference, feet on one baseline. ")
cast("cast_dahyun_walk_cycle", "EIGHT", DAHYUN, WALK8)
cast("cast_dahyun_ghost_cycle", "SIX", DAHYUN, GHOST6)
cast("cast_dahyun_duck_cycle", "FOUR", DAHYUN,
     "DUCK WADDLE: FOUR SIDE-PROFILE frames facing RIGHT of one comic waddling walk cycle (CONTACT, DOWN, PASSING, UP): "
     "Dahyun with big orange webbed DUCK FEET instead of shoes, yellow duck tail feathers behind, a tiny orange beak-shaped "
     "cap on her hat, body tilting from side to side, elbows out flapping like little wings, a surprised giggling face, the "
     "legs clearly separated with an open magenta gap. All four the SAME scale, feet on one baseline.")
cast("cast_witch_walk_cycle", "EIGHT", WITCH, WALK8)
cast("cast_witch_ghost_cycle", "SIX", WITCH, GHOST6)
cast("cast_cat_walk_cycle", "EIGHT", CAT,
     "CAT WALK CYCLE on four legs: EIGHT figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one cat "
     "walk cycle in order (CONTACT, DOWN, PASSING, UP), tail up and curving, calm happy face, the four legs clearly "
     "separated with open magenta gaps; (5)-(6) TWO BACK-VIEW frames walking AWAY (tail up, left then right paw lifted); "
     "(7)-(8) TWO FRONT-VIEW frames walking TOWARD the viewer (left then right front paw forward). All eight the SAME "
     "scale, paws on one baseline.")
cast("cast_cat_ghost_cycle", "SIX", CAT,
     "GHOST-PLAY PARADE MARCH ON THE HIND LEGS: SIX figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of "
     "the cat walking upright on its hind legs (CONTACT, DOWN, PASSING, UP), both front paws raised forward like a silly "
     "ghost, mouth solid BLACK round 'O', tail up, the two hind legs clearly separated with an open magenta gap; (5)-(6) TWO "
     "FRONT-VIEW frames marching upright TOWARD the viewer (left then right hind paw forward), paws up, black 'O' mouth. All "
     "six the SAME scale, feet on one baseline.")
for _k, _who in (("rabbit", RABBIT), ("bear", BEAR), ("fox", FOX)):
    cast(f"cast_{_k}_walk_cycle", "EIGHT", _who, WALK8)
    cast(f"cast_{_k}_ghost_cycle", "SIX", _who, GHOST6)

# ---------------------------------------------------------------- props and sets (atlas, story_* categories)
SHEET = ("A SPRITE ATLAS sheet for a children's pop-up storybook: separate die-cut cardstock pieces arranged in loose "
         "horizontal rows " + BG)
WC_PROP = (
    "STYLE (same for every piece): flat front-on orthographic view like a printed die-cut pop-up book piece, no perspective, "
    "no cast shadows, no drop shadows, no glow outside the silhouette, no outline stroke in magenta, no white sticker "
    "border. Each part has ONE main base colour plus finely PRINTED detail: stitched dashes, stamped dots, tiny stars, "
    "stripes, ribs and grooves, subtle matte cardstock grain, slightly gouache/screen-printed look, warm friendly cut-paper "
    "style for ages 3-7, cosy Halloween, cute and never scary or gross. Matte, no gloss, no photo texture, no 3D render. "
    "PALETTE: pumpkin orange, ochre/mustard, golden yellow, cream, warm browns, chocolate, mint green, sky blue, cobalt "
    "blue, brick red, cherry red, deep blue-violet indigo plum, charcoal. " + PURPLE +
    "NO flower, leaf or vine motifs on any piece (the only plant shapes allowed are a pumpkin's own stem curl and a "
    "strawberry's own leaf cap). No faces on objects except where stated (living creatures get two small dot eyes; carved "
    "pumpkin lanterns have cut-out eye and mouth holes). Each standing piece ends in a clean flat horizontal bottom edge, "
    "all parts of one piece connected into a single silhouette. ")
WC_BUILD = (
    "STYLE (same for every piece): flat front-on orthographic view like a printed die-cut pop-up book piece, no perspective, "
    "no cast shadows, no drop shadows, no outline stroke in magenta, no white sticker border. Each part has ONE main base "
    "colour plus finely PRINTED material detail: plaster texture, wood grain and nail dots, roof tiles or shingles, stone "
    "courses, stitched dashes, stamped dots and little stars, subtle matte cardstock grain, slightly gouache/screen-printed "
    "look, warm friendly cut-paper style, cosy Halloween night (warm, never scary). NO flower, leaf or vine motifs on "
    "buildings, walls, floors or furniture. No faces on objects. Matte, no gloss, no photo texture, no 3D render. "
    "PALETTE: warm cream plaster, honey and chocolate wood browns, mint green trim, pumpkin orange, ochre, deep teal-blue "
    "roof, deep blue-violet indigo plum, cream, charcoal, warm golden window light. " + PURPLE +
    "Each standing piece ends in a clean flat horizontal bottom edge. ")


def atlas(sid, body, style=WC_PROP):
    JOBS.append({"id": "atlas_" + sid, "kind": "bg", "aspect": LAND, "out": RAW_A + sid + ".png",
                 "prompt": SHEET + style + body})


atlas("story_wc_ingredients", "THIS SHEET: funny Halloween candy INGREDIENTS on a magic shop shelf, 12 pieces in three rows, "
      "each ingredient about the same size (toy size), standing on a flat bottom. ROW 1 (RED): (1) a small round glass JAR "
      "with a cork holding three big cherry-red cut-paper DROPS (baby dragon snot, cute not gross), a cream label with a tiny "
      "smiling red baby dragon picture; (2) a red toy FIRE TRUCK, square and chunky, a white ladder on top, a little water "
      "cannon, navy wheels, no face; (3) a big red LADYBUG with black spots and two small dot eyes, sitting on a flat base. "
      "ROW 2 (YELLOW): (4) a small carved HALLOWEEN PUMPKIN LANTERN in golden-orange with cut-out triangle eyes and a smiling "
      "mouth hole, a warm golden light printed inside the holes, a green stem curl; (5) a small glass JAR holding a puffy "
      "golden-yellow paper CLOUD (a baby chick's fart, funny), a cream label with a tiny yellow chick picture; (6) a yellow "
      "RUBBER DUCK toy with an orange beak and dot eyes. ROW 3 (BLUE): (7) a soft blue swirl like a soft-serve ice-cream "
      "swirl on a little cream plate (a monster's poo, cute, two little wavy smell lines attached on top), no face; (8) a "
      "cobalt-blue FISH standing on its tail fin on a flat base, dot eyes, a happy little smile; (9) a little curling blue "
      "WAVE of three layered paper wave strips with cream foam tips, on a flat base. Plus (10) a wooden LADLE standing on "
      "its handle end; (11) a pumpkin-shaped orange INVITATION CARD with a tiny picture of a black pot and a wrapped candy "
      "printed on it and a small cream ribbon (no text); (12) the same invitation card seen tilted as if fluttering in the "
      "wind.")
atlas("story_wc_pot", "THIS SHEET: the magic candy POT and its fire, 18 pieces. (1) a big round black iron CAULDRON seen "
      "from the front, a thick rim, two little ear handles, three short legs, printed rivets and tiny stars on its belly; "
      "(2) the same cauldron's REAR RIM: only the back half of the rim as a thin black curved band (to stand behind the "
      "liquid); (3)-(10) EIGHT flat OVAL liquid DISCS seen almost from above (wide flat ellipses, about four times as wide "
      "as tall, with a few printed bubble rings and dots), each ONE colour: (3) clear sky-blue water, (4) cherry red, (5) "
      "golden yellow, (6) cobalt blue, (7) pumpkin orange, (8) leaf-free fresh green, (9) blue-violet indigo plum, (10) "
      "deep charcoal black with a few cream sparkle dots; (11) a flat SPIRAL SWIRL band (one wide curling ribbon spiral, "
      "cream-white, like a whirlpool seen from above); (12) a small pile of firewood LOGS with a stone ring; (13)-(15) "
      "THREE FLAMES of increasing size (small, medium, large), layered cut-paper flames in brick red, orange, golden yellow "
      "and cream, each on a flat bottom; (16) a big puffy cream and warm-grey SMOKE PUFF cloud (the 'POOF!'), flat bottom; "
      "(17) a cluster of three round BUBBLES in pale sky blue and cream; (18) a golden comic STAR BURST sparkle shape (no "
      "text).")
atlas("story_wc_candies", "THIS SHEET: magic Halloween CANDIES, 10 pieces, each candy large and clear, standing on a flat "
      "bottom or on its stick. (1) a STRAWBERRY-SHAPED wrapped candy: cherry-red strawberry body with yellow seed dots and a "
      "green leaf cap, cream twisted wrapper ends on both sides; (2) a DUCK-SHAPED lollipop: a golden-yellow duck "
      "silhouette in side view with an orange beak, on a kraft-brown stick with a coral ribbon; (3) a FISH-SHAPED flat "
      "cobalt-blue jelly candy with darker fins and pale blue scale arcs, a cream paper band round its middle; (4) a "
      "FROG-SHAPED lollipop: a green frog face silhouette with two round eye bumps (no eyeballs), a lighter green belly, on "
      "a stick with a yellow ribbon; (5) a round PUMPKIN candy: orange with ribbed grooves and a little green stem, cream "
      "twisted wrapper ends; (6) a BAT-SHAPED lollipop: a blue-violet bat with spread wings on a stick with a lilac-blue "
      "ribbon; (7) a round BLACK GHOST CANDY: a glossless deep charcoal-black ball with one big cream highlight dot, white "
      "twisted wrapper ends; (8) a tall glass CANDY JAR full of mixed colourful candies with a cork lid; (9) a wide low "
      "HEAP of many mixed candies (all the candies above, spilling), flat bottom; (10) a small woven BASKET of candies.")
atlas("story_wc_halloween", "THIS SHEET: cosy Halloween street decorations, 18 pieces. (1)-(3) carved PUMPKIN LANTERNS in "
      "three sizes (small, medium, big), pumpkin orange with ribs and a green stem curl, cut-out triangle eyes and a "
      "friendly grin as holes showing a warm golden candle glow printed inside (friendly, not scary); (4) a stack of two "
      "pumpkin lanterns; (5) a long string of BUNTING: little triangle paper flags in orange, cream, deep blue-violet and "
      "mustard hanging from a cord that ends in two short posts (one wide piece, flat bottom on both posts); (6) a corner "
      "PAPER COBWEB (cream paper cut lacework, NO spider); (7) a round hanging PAPER COBWEB with a short cord on top (no "
      "spider); (8)-(10) three small flat BAT SILHOUETTES in deep blue-violet indigo with spread wings (different poses), "
      "cute, no eyes; (11) a big FULL MOON disc in warm cream with soft printed crater dots; (12) a small golden STAR and "
      "(13) a second smaller star; (14) an iron STREET LANTERN POST with a warm golden lit lantern on top; (15) a short "
      "wooden picket FENCE section with a little pumpkin on one post; (16) a witch's BROOM standing upright (straw head "
      "down); (17) a small friendly round GHOST (a cream-white sheet ghost, two dot eyes, a small smile, floating shape "
      "with a flat bottom edge); (18) a hay BALE with a pumpkin on top.")
atlas("story_wc_shop", "THIS SHEET: the CANDY WITCH'S SHOP, a big storybook building as flat front-on pop-up pieces, 7 "
      "pieces. (1) the SHOP FACADE (large, about as wide as tall): cream-plaster front wall with chocolate-brown timber "
      "framing, a big deep teal-blue scalloped-shingle ROOF with a tall pointed gable and a little crooked chimney, an "
      "orange-and-cream striped AWNING over a big shop WINDOW on the left showing shelves of colourful candy jars and a "
      "warm golden lit interior, a tall round-topped OPEN DOORWAY in the middle (the doorway is a dark warm-brown arched "
      "opening, the door itself NOT in it), a small round window up in the gable glowing golden, a hanging wooden sign "
      "shaped like a big swirl lollipop (no text), a pumpkin lantern on each side of the door step, symmetric-ish and "
      "clearly one connected silhouette; (2) the shop's round-topped wooden DOOR alone (mint-green planks, a round brass "
      "knob, a little star window), the size of the doorway; (3) the matching SIDE WALL panel: a plain rectangle of the same "
      "cream plaster and timber framing with one small lit window, no roof, same wall height as the facade's wall; (4) the "
      "matching ROOF SIDE panel: a rectangle of the same deep teal scalloped shingles; (5) the facade's BACK seen from "
      "inside: the same outline as piece 1 but showing the inside face: plain cream plaster wall with brown timber, the "
      "arched doorway opening and the window from inside (dark night blue outside); (6) a tall narrow neighbour TOWNHOUSE "
      "facade (ochre plaster, a deep blue-violet roof, two lit golden windows); (7) a small neighbour COTTAGE facade "
      "(cream plaster, chocolate roof, one lit window, a pumpkin by the door).", style=WC_BUILD)
atlas("story_wc_room", "THIS SHEET: the INSIDE of the candy witch's shop as big flat pop-up room pieces, 9 pieces, seen "
      "straight on. (1) the BACK WALL seen from inside: one very WIDE landscape rectangle (about 1.8 times as wide as tall), "
      "warm cream plaster on the upper part with a thin wooden rail, honey-wood wainscot panels along the bottom third, a "
      "skirting board at the very bottom, TWO arched WINDOWS in the upper wall that show the night street outside printed "
      "in them (deep navy sky, a cream full moon in one, little rooftops and orange lit windows and a tiny pumpkin "
      "lantern), flat bottom, straight top; (2) a SIDE WALL seen from inside: an upright rectangle (about 0.7 times as wide "
      "as tall) with the same cream plaster and wainscot, a wooden corner post along its LEFT edge, a small paper cobweb "
      "printed in the top corner; (3) the same SIDE WALL with the corner post along its RIGHT edge; (4) a FLOOR seen from "
      "straight above: a wide rectangle of warm honey wooden floorboards running left to right with nail dots, about 2.4 "
      "times as wide as tall; (5) the INGREDIENT SHELF: a wide low wooden shelf unit (about 2.2 times as wide as tall) with "
      "TWO shelf boards and THREE sections side by side, the back of each section painted a different soft colour (cherry "
      "red section, golden yellow section, sky blue section), little star-shaped brackets, EMPTY (nothing on it), flat "
      "bottom; (6) a tall CANDY SHELF of honey wood full of colourful candy jars (a back-wall cabinet), flat bottom; (7) a "
      "wooden shop COUNTER with a striped orange-and-cream front panel and a glass candy bowl on top; (8) a round stone "
      "HEARTH RING (a low circle of grey stones seen from the front, about four times as wide as tall) for the pot to stand "
      "in; (9) a long dark wooden CEILING BEAM with a hanging paper bat mobile (three little blue-violet bats on strings) and "
      "a small cream paper cobweb in one corner.", style=WC_BUILD)

# 2026-11-19 review: the first ghost-play figures had small dark "O" mouths that read as ordinary mouths, not the
# black lips of the ghost candy; Dahyun's tf_b (5) came out in a ghost-sheet costume. Dedicated sheet, stronger words.
BLACK_LIPS = ("THE GHOST-CANDY LOOK: the LIPS are painted thick solid JET-BLACK, clearly black like black lipstick, a big "
              "round black ring of lips around the open 'oooh' mouth, the black lips as wide as both eyes together, "
              "obviously black from far away; the rest of the face is the normal sweet face; NO sheet costume, NO ghost "
              "costume, NO white cloth, their normal clothes. ")
cast("cast_wc_ghost_lips", "SIX", DAHYUN + WITCH + CAT + RABBIT + BEAR + FOX,
     BLACK_LIPS + "SIX FRONT figures playing ghost, both arms (front paws) raised up with drooping hands like a silly "
     "giggling ghost, never scary, left to right: (1) DAHYUN; (2) THE CANDY WITCH; (3) HOBAKI THE CAT sitting up on its "
     "hind legs; (4) THE RABBIT; (5) THE BEAR; (6) THE FOX. Sizes as in the reference (the witch tallest, the cat "
     "smallest).", extra=FRONT)

# 2026-11-19 review: with the six-figure lineup as the only reference, the rabbit / bear / fox walk and ghost cycles
# came out as DAHYUN (the model drew the lineup's first figure). Single-character reference crops of the lineup
# (art_src/cast/raw/ref_wc_<who>.png) and an explicit "only this character" line; the old raws are kept as _v1.
ONLY = ("THIS SHEET SHOWS ONLY ONE CHARACTER: {name}, exactly the character in the reference image, in every figure. Do "
        "NOT draw Dahyun (the girl in the wizard hat) or any other character. ")
for _k, _who, _name in (("rabbit", RABBIT, "THE WHITE RABBIT FRIEND"), ("bear", BEAR, "THE BROWN BEAR FRIEND in the "
                        "pumpkin costume"), ("fox", FOX, "THE ORANGE FOX FRIEND")):
    for _j in JOBS:
        if _j["id"] in (f"cast_{_k}_walk_cycle", f"cast_{_k}_ghost_cycle"):
            _j["refs"] = [RAW_C + f"ref_wc_{_k}.png"]
            _j["prompt"] = _j["prompt"].replace("in one horizontal row, ", "in one horizontal row, " + ONLY.format(name=_name), 1)
for _j in JOBS:
    if _j["id"] in ("cast_witch_ghost_cycle", "cast_witch_walk_cycle"):
        _j["refs"] = [RAW_C + "ref_wc_witch.png"]
        _j["prompt"] = _j["prompt"].replace("in one horizontal row, ", "in one horizontal row, " + ONLY.format(name="THE CANDY WITCH"), 1)
    if _j["id"] == "cast_cat_ghost_cycle":
        _j["refs"] = [RAW_C + "ref_wc_cat.png"]

if __name__ == "__main__":
    p = os.path.join(HERE, "witch_candy_jobs.json")
    json.dump(JOBS, open(p, "w"), ensure_ascii=False, indent=1)
    print(p, len(JOBS), [j["id"] for j in JOBS])
