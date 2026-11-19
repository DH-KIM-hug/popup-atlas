#!/usr/bin/env python3
"""Write tools/cast/cast_jobs.json: the cast sheets (pop-up paper characters) for tools/run_jobs.py.
  python3 tools/cast/make_jobs.py && python3 tools/run_jobs.py tools/cast/cast_jobs.json [ids]
Same printed folk-art cut-paper style block as tools/atlas (no refs), magenta #FF00FF background for keying."""
import json, os

BG = ("on a perfectly flat, uniform, solid pure MAGENTA background (#FF00FF, RGB 255,0,255) with no texture, no gradient, "
      "no vignette, no shadows on the background. Every piece is fully separate and isolated, with a clear empty magenta gap "
      "of at least 40 pixels on every side; pieces never touch or overlap each other and never touch the image border. "
      "No grid lines, no labels, no text, no numbers. ")
STYLE = ("STYLE (same for every piece): flat front-on orthographic view, like a printed die-cut pop-up book piece, no perspective, "
         "no cast shadows, no drop shadows, no glow, no outline stroke in magenta or white sticker border. Each piece has ONE main base "
         "colour per part plus finely PRINTED folk-art detail on top: stamped dots, little dashes, stitched lines, scalloped edges, tiny "
         "repeated flower and leaf motifs, subtle matte cardstock grain, slightly gouache/screen-printed look, warm friendly cut-paper "
         "children's storybook style. Matte, no gloss, no photo texture, no 3D render. PALETTE (muted warm storybook): brick red / "
         "terracotta, ochre/mustard yellow, sage green, olive, warm browns, cream, soft sky blue, warm orange. Absolutely no magenta, "
         "purple or hot pink anywhere in any piece (rosy cheeks are a soft coral-orange, not pink). ")
# Sky characters (sun, wind) must not carry the botanical motifs of STYLE (2026-11-18: user asked why the sun and wind
# had leaf prints). Same cut-paper look, printed detail only from sun/light or cloud/air vocabulary.
SKY_STYLE = ("STYLE (same for every piece): flat front-on orthographic view, like a printed die-cut pop-up book piece, no perspective, "
             "no cast shadows, no drop shadows, no glow, no halo, no outline stroke in magenta or white sticker border. Each piece has ONE "
             "main base colour per part plus finely PRINTED detail on top, subtle matte cardstock grain, slightly gouache/screen-printed "
             "look, warm friendly cut-paper children's storybook style. Matte, no gloss, no photo texture, no 3D render. PALETTE (muted "
             "warm storybook): ochre/mustard yellow, golden yellow, warm orange, brick red / terracotta, warm browns, cream, soft sky blue. "
             "No green anywhere. Absolutely no magenta, purple or hot pink anywhere in any piece (rosy cheeks are a soft coral-orange, "
             "not pink). NO flowers, NO leaves, NO petals, NO plants, NO vines, NO sprigs, NO botanical motifs of any kind anywhere. ")
NO_BOTANY = (" IMPORTANT: no flowers, no leaves, no petals, no plants, no vines, no botanical motifs anywhere on any piece.")

FACE = ("Faces are simple and sweet: two small dark dot or curved-line eyes, a tiny smile, round soft coral cheek dots. ")

TRAV = ("THE CHARACTER: one friendly young traveller (a cheerful boy-like young man, storybook proportions about 4.5 heads tall), round "
        "cream-peach face, short dark brown hair, " + FACE + "He wears a THICK, heavy, knee-length winter wool COAT in brick red / "
        "terracotta with a wide folded collar, big ochre toggle buttons, stitched seams and small printed folk-art flower motifs and dash "
        "patterns on it; under it a sage green shirt; plain dark chocolate-brown trousers; dark charcoal-brown boots. His HAT is a "
        "round-crowned brimmed felt travel hat in warm medium brown with an ochre band and a tiny leaf stamp. ")
POSE = ("EVERY figure: full body, standing upright and facing the viewer straight on (front view, not turned, not walking), body "
        "symmetric, both feet flat on the same horizontal baseline, feet a little apart with the toes pointing slightly outward. The two "
        "legs are clearly separate: a clean open magenta gap between the legs from the crotch (or the coat hem) all the way down to the "
        "feet; the legs never touch each other. Arms hang down beside the body with the hands at hip height, a little away from the body, "
        "and the hands NEVER overlap or touch the legs. Exactly two arms, two legs, two feet, two hands with simple mitten-like fingers. "
        "All figures the SAME size and the SAME character design, standing in one row on a common baseline, each with its feet near the "
        "bottom third of the image so the figures are as tall as possible (each figure about 80 percent of the image height). ")

JOBS = [
    {"id": "cast_traveller", "kind": "bg", "aspect": "landscape 3:2 at the largest available size (1536x1024)",
     "out": "art_src/cast/raw/cast_traveller.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: FIVE separate full-body die-cut cardstock stand-up figures of the "
     "same character in one horizontal row, " + BG + STYLE + TRAV + POSE +
     "THE FIVE FIGURES, left to right: (1) in the thick red coat buttoned closed AND the hat on; (2) in the thick red coat buttoned "
     "closed, NO hat (hair visible); (3) in the coat and hat, clutching the coat collar shut with both hands at his chest, shoulders "
     "hunched, eyes squeezed (cold wind) - his legs still apart with a gap; (4) NO coat: sage green shirt with rolled sleeves and brown "
     "trousers held by ochre suspenders, hat on, happy; (5) NO coat and NO hat: sage green shirt, suspenders, brown trousers, warm and "
     "smiling with flushed coral cheeks."},
    {"id": "cast_traveller_props", "kind": "bg", "aspect": "landscape 3:2 at the largest available size (1536x1024)",
     "out": "art_src/cast/raw/cast_traveller_props.png",
     "prompt": "A SPRITE SHEET for a children's pop-up storybook: FIVE separate die-cut cardstock pieces, the traveller's clothing, " + BG
     + STYLE + "THE CLOTHES: a THICK heavy knee-length winter wool COAT in brick red / terracotta with a wide folded collar, big ochre "
     "toggle buttons, stitched seams, small printed folk-art flower motifs and dash patterns; and a round-crowned brimmed felt travel HAT "
     "in warm medium brown with an ochre band and a tiny leaf stamp. No person, no body, no hands, no hanger, no hook. THE FIVE PIECES: "
     "(1) the coat seen flat from the front, empty, open a little at the front showing a darker red lining, sleeves hanging straight "
     "down, as if hung up - large; (2) the same coat folded over once and draped, as if carried folded over an arm, a soft folded bundle "
     "with a sleeve hanging down, flat bottom edge; (3) the same coat dropped on the ground: a low wide crumpled heap seen from the front, "
     "collar and one sleeve visible, flat bottom edge; (4) the hat seen straight from the front, brim level, crown up, flat bottom edge "
     "of the brim; (5) the same hat lying tipped on its side on the ground, flat bottom edge."},
    {"id": "cast_sun_v2", "kind": "bg", "aspect": "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)",
     "out": "art_src/cast/raw/cast_sun_v2.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: THREE separate die-cut cardstock SUN character cards in one row, "
     "same size, " + BG + SKY_STYLE + "THE SUN: a big round warm golden-ochre face disc with a slightly lighter inner disc, surrounded by a "
     "ring of layered cut-paper rays (alternating long pointed orange rays and short rounded mustard rays), all rays attached to the disc "
     "so the whole sun is one connected silhouette. PRINTED DETAIL only from sun and light shapes: stamped dots, dash lines, a dashed "
     "concentric ring around the face, small radiating ticks along each ray, scalloped edges; the inner face disc is otherwise plain. "
     "Simple sweet face: dark curved-line or dot eyes, small smile, round soft coral-orange cheek circles, no nose or a tiny dot nose. "
     "THE THREE EXPRESSIONS, left to right: (1) SMILE: gentle closed-eye happy smile, calm; (2) PROUD: chin up, one eye winking, a "
     "confident pleased grin, rays a little longer; (3) BEAMING HOT: a huge open-mouthed delighted grin, eyes shut tight in joy, deeper "
     "orange-red flush on the cheeks, rays extra long and wavy like heat, a few small cut-paper heat squiggles attached to the rays "
     "(connected, not floating)." + NO_BOTANY},
    {"id": "cast_wind_v2", "kind": "bg", "aspect": "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)",
     "out": "art_src/cast/raw/cast_wind_v2.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: THREE separate die-cut cardstock WIND character cards in one row, "
     "same size, " + BG + SKY_STYLE + "THE WIND: a puffy cream-white cloud face (scalloped bumpy cloud outline, a second soft sky-blue "
     "cloud layer peeking behind its bottom edge) with chubby PUFFED-OUT cheeks; on its LEFT side, attached to the cloud and part of the "
     "same silhouette, a few soft sky-blue curly wind swirl ribbons streaming outward to the left. The wind always blows toward the LEFT "
     "(the swirls are only on the left side, the cloud's right side has no swirls). PRINTED DETAIL only from cloud and air shapes: "
     "stitched dashed swirl lines, wavy air streaks, small dots, scalloped edges. Simple face: dark dot or curved-line eyes, round soft "
     "coral cheek circles. THE THREE EXPRESSIONS, left to right: (1) BOAST: smug confident smirk, eyebrows raised, cheeks a little "
     "puffed, small swirls on the left; (2) BLOWING HARD: cheeks hugely puffed, eyes squeezed shut with effort, lips pursed in a small "
     "round 'O' blowing to the left, long strong blue wind streams and swirls attached on the left, cloud slightly stretched; (3) TIRED: "
     "deflated flatter droopy cloud, half-closed sleepy eyes, small open sighing mouth, one sweat drop attached to the cloud, only one "
     "small limp wisp on the left." + NO_BOTANY},
]

# 2026-11-18 traveller expression sheets (user: "계속 웃고만 있는 건 아닌지"). Same design, size and standing pose basis as
# cast_traveller (the existing sheet is passed as the reference image) so tools/cast/cut_cast_rig.py cuts them the same way.
EXPR_REF = ["art_src/cast/raw/cast_traveller.png"]
EXPR_POSE = ("EVERY figure: full body, facing the viewer straight on (front view, not turned), both feet flat on the same horizontal "
             "baseline, feet a little apart with the toes pointing slightly outward, the SAME leg stance as the reference figures. The "
             "two legs are clearly separate: a clean open magenta gap between the legs from the coat hem (or the crotch) all the way "
             "down to the feet; the legs never touch each other and the hands NEVER overlap or touch the legs. Exactly two arms, two "
             "legs, two feet, two hands with simple mitten-like fingers. All figures the SAME size, the SAME proportions and the SAME "
             "character design as the reference image (same face shape, same hair, same red folk-art coat with ochre toggles, same "
             "brown hat, same boots), standing in one row on a common baseline, each figure about 85 percent of the image height. "
             "The FACE expression must be big and clearly readable from far away (it is a small card in a pop-up book), drawn in the "
             "same simple printed style as the reference faces. ")
EXPR_HEAD = ("A CHARACTER SHEET for a children's pop-up storybook: FIVE separate full-body die-cut cardstock stand-up figures of the "
             "SAME traveller character as in the reference image (match him exactly: this is the same paper puppet with new face "
             "expressions and arm poses), in one horizontal row, ")
JOBS += [
    {"id": "cast_traveller_expr_a", "kind": "bg", "refs": EXPR_REF,
     "aspect": "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)",
     "out": "art_src/cast/raw/cast_traveller_expr_a.png",
     "prompt": EXPR_HEAD + BG + STYLE + TRAV.replace(FACE, "") + EXPR_POSE +
     "THE FIVE FIGURES, left to right, all wearing the thick red coat buttoned closed: (1) SURPRISED, hat on: eyes wide open as big "
     "round white eyes with dark pupils, eyebrows raised high, mouth a big open round 'O', both hands thrown up beside his head with "
     "palms open (startled); (2) SURPRISED, NO hat (messy dark brown hair visible, a few hairs sticking up): same wide-eyed open-mouth "
     "'O' shock, both hands reaching up to the top of his bare head as if his hat just blew away; (3) FREEZING COLD, NO hat: shoulders "
     "hunched up high, both arms wrapped tightly across his chest hugging himself, knees a little together but feet still apart with "
     "a gap, eyes squeezed shut as two wavy lines, teeth clenched and chattering shown as a wide grimace with a row of white teeth, "
     "cheeks and nose tinted pale icy blue instead of coral, a small drip at the nose; (4) CALM WALKING FACE, hat on: arms hanging "
     "relaxed at his sides, a gentle neutral face: soft open dot eyes looking ahead, small calm closed mouth as a short flat line (NOT "
     "a grin, not smiling), soft coral cheeks; (5) CALM WALKING FACE, NO hat: same gentle neutral face as (4), arms at his sides."},
    {"id": "cast_traveller_expr_b", "kind": "bg", "refs": EXPR_REF,
     "aspect": "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)",
     "out": "art_src/cast/raw/cast_traveller_expr_b.png",
     "prompt": EXPR_HEAD + BG + STYLE + TRAV.replace(FACE, "") + EXPR_POSE +
     "THE FIVE FIGURES, left to right: (1) WARM AND HOT, coat on but UNBUTTONED and hanging open showing the sage green shirt, hat on: "
     "flushed deep red-orange cheeks, eyes half closed and droopy, mouth open panting, two or three big cut-paper sweat drops in soft "
     "sky blue attached to the edge of his face and hat (touching the silhouette, not floating), one hand tugging the open coat "
     "collar; (2) VERY HOT FANNING, coat on and unbuttoned open, NO hat on his head: he holds his brown hat in one raised hand beside "
     "his face, fanning himself with it, the other arm at his side; face bright red flushed, eyes squeezed into tired curves, mouth "
     "wide open panting with the tongue sticking out, several big sky blue sweat drops attached to his face and hair (touching the "
     "silhouette); (3) RELIEVED AND COOL, NO coat (sage green shirt with rolled sleeves, ochre suspenders, brown trousers), hat on: "
     "eyes closed as content upward curves, a soft peaceful closed-mouth smile, relaxed shoulders, arms at his sides; (4) RELIEVED AND "
     "COOL, NO coat and NO hat: same content closed-eye peaceful smile as (3), arms at his sides; (5) CALM WALKING FACE, NO coat "
     "(shirt, suspenders, trousers), hat on: arms hanging relaxed at his sides, a gentle neutral face: soft open dot eyes looking "
     "ahead, small calm closed mouth as a short flat line (NOT a grin, not smiling), soft coral cheeks."},
]

# 2026-11-18 front-facing leg parts (user: "팔자걸음인딩?"). The figures stand with their boots in SIDE view, toes pointing
# outward, so a boy walking toward the reader duck-walks. These legs replace every traveller figure's leg_l/leg_r (shared
# across expressions, see tools/cast/front_legs.py). Reference = the current lower bodies (colour/cuff/boot match).
LEG_REF = ["art_src/cast/raw/ref_traveller_legs.png", "art_src/cast/raw/cast_traveller.png"]
JOBS += [
    {"id": "cast_traveller_legs_front", "kind": "bg", "refs": LEG_REF,
     "aspect": "landscape 3:2 at the largest available size (1536x1024)",
     "out": "art_src/cast/raw/cast_traveller_legs_front.png",
     "prompt": "A SPRITE SHEET for a children's pop-up storybook: FOUR separate die-cut cardstock LEG pieces for the paper puppet "
     "of the traveller boy in the reference images, in one horizontal row, all the same height, " + BG + STYLE.replace(
         "tiny repeated flower and leaf motifs, ", "") +
     "MATCH THE REFERENCE EXACTLY: same felt/cardstock texture, same trouser browns, same dark plum-brown boots with the cream "
     "dashed stitch line along the sole. Each piece is ONE single leg, cut off straight across at the top of the thigh (a flat "
     "horizontal top edge, no hips, no body, no coat, no hands), hanging perfectly straight and vertical, seen EXACTLY FROM THE "
     "FRONT as if the boy walks straight toward the viewer. THE BOOT IS SEEN FROM THE FRONT, NOT FROM THE SIDE: the boot toe points "
     "straight AT the viewer, so the foot reads as a rounded toe cap facing us, symmetric left-right, only a little wider than the "
     "boot shaft, with a thin strip of darker sole and the cream dashed sole stitch running across the front of the toe at the "
     "bottom; the bottom edge is flat. The toe must NOT stick out to the left or to the right (no side-view boot, no profile foot, no "
     "heel showing, no toes pointing outward). THE FOUR PIECES, left to right: (1) and (2) a LEFT and a RIGHT leg in plain dark "
     "chocolate-brown trousers (no stitch line on the trousers), the trouser leg straight and slightly baggy, ending in a slightly "
     "wider turned-up cuff at mid-shin, then the front-view boot shaft and toe cap below; (3) and (4) a LEFT and a RIGHT leg in the "
     "warm medium brown trousers of the reference's right figure, with a dashed ochre-yellow stitched seam running down the OUTER "
     "side of each leg (on piece 3 the seam is along its left edge, on piece 4 along its right edge), the trouser leg straight, "
     "ending in a cuff at mid-shin over the same front-view boot. Each leg about 3 times taller than it is wide (thigh width), "
     "each about 80 percent of the image height, all four with their soles on one common baseline, a wide magenta gap between "
     "the pieces." + NO_BOTANY},
]

# 2026-11-18 walk v4 (user: "잘린 다리가 코트 위를 삐져나와서 이상해 그리고 군인처럼 걷는 거 같아"). The swing leg used to be the
# straight front leg slid up + squashed, which exposed its cut top/cuff under the hem. Now a pre-drawn BENT-KNEE leg is swapped
# in while the foot is up (tools/cast/lift_legs.py), and the calm walking figures get separate swinging arm cards
# (tools/cast/walk_arms.py). Refs: the straight front legs sheet (colour/texture match) and the calm figures.
LIFT_REF = ["art_src/cast/raw/cast_traveller_legs_front.png", "art_src/cast/raw/ref_traveller_legs.png"]
LIFT_COMMON = (
    "MATCH THE FIRST REFERENCE SHEET EXACTLY: the same four legs (same felt/cardstock texture, same trouser browns, same "
    "turned-up cuff, same dark plum-brown boots with the cream dashed stitch line along the sole), in the same order, same width. "
    "Each piece is ONE single leg seen EXACTLY FROM THE FRONT while the boy walks straight toward the viewer, cut off straight "
    "across at the very top (a flat horizontal top edge; no hips, no body, no coat, no hands). The top part of every piece is a "
    "TALL plain straight trouser section (it will be hidden under a coat), the same width as the reference thigh. THE FOUR PIECES, "
    "left to right: (1) LEFT and (2) RIGHT leg in plain dark chocolate-brown trousers (no stitch line); (3) LEFT and (4) RIGHT leg "
    "in the warm medium brown trousers with a dashed ochre-yellow stitched seam down the OUTER side (piece 3: along its left edge, "
    "piece 4: along its right edge). The boot toe always points straight AT the viewer (front view, symmetric toe cap, never a "
    "side-view foot, no toes pointing outward). All four pieces the same height, tops on one common line, a wide magenta gap "
    "between the pieces, each piece about 80 percent of the image height." + NO_BOTANY)
JOBS += [
    {"id": "cast_traveller_legs_lift", "kind": "bg", "refs": LIFT_REF,
     "aspect": "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)",
     "out": "art_src/cast/raw/cast_traveller_legs_lift.png",
     "prompt": "A SPRITE SHEET for a children's pop-up storybook: FOUR separate die-cut cardstock LIFTED-LEG pieces for the paper "
     "puppet of the traveller boy, " + BG + STYLE.replace("tiny repeated flower and leaf motifs, ", "") + LIFT_COMMON +
     " THE POSE OF EVERY LEG: mid-step, the knee BENT and the foot LIFTED, the knee coming forward toward the viewer: below the "
     "tall trouser top the knee shows as a soft rounded bump with a few small fabric crease lines, the shin below the knee is "
     "SHORT (foreshortened, tipped toward us), the trouser cuff sits just above the boot, and the boot is seen from the front a "
     "little LARGER than in the reference (it is closer to us), the toe cap tipped up slightly so a thin sliver of the darker sole "
     "with the cream dashed stitch shows under it. Seen as a whole each lifted leg is noticeably SHORTER than the straight "
     "reference legs (about three quarters of their height) but just as wide, hanging vertically, symmetric, not bent sideways."},
    {"id": "cast_traveller_legs_half", "kind": "bg", "refs": LIFT_REF,
     "aspect": "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)",
     "out": "art_src/cast/raw/cast_traveller_legs_half.png",
     "prompt": "A SPRITE SHEET for a children's pop-up storybook: FOUR separate die-cut cardstock LEG pieces for the paper "
     "puppet of the traveller boy, " + BG + STYLE.replace("tiny repeated flower and leaf motifs, ", "") + LIFT_COMMON +
     " THE POSE OF EVERY LEG: just starting a step, the knee SLIGHTLY bent and coming a little forward toward the viewer, the heel "
     "just lifting: below the tall trouser top a soft knee bump with one or two small crease lines, the shin a little "
     "foreshortened, the boot seen from the front, toe cap toward us. Each leg about nine tenths of the height of the straight "
     "reference legs, just as wide, hanging vertically, symmetric, not bent sideways."},
]
WALK_REF = ["art_src/cast/raw/ref_traveller_calm.png", "art_src/cast/raw/cast_traveller.png"]
JOBS += [
    {"id": "cast_traveller_walk_armless", "kind": "bg", "refs": WALK_REF,
     "aspect": "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)",
     "out": "art_src/cast/raw/cast_traveller_walk_armless.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: THREE separate full-body die-cut cardstock stand-up figures, "
     "EXACTLY the three figures of the FIRST reference image (same face, same calm expression, same hair, same hat, same red folk-art "
     "coat with the same ochre toggles, pockets and flower prints, same green shirt, suspenders and trousers, same boots, same size, "
     "same stance, same order) but WITHOUT ARMS: both arms and sleeves are removed, because they are separate paper puppet pieces. "
     "Where each arm was, the garment's side continues straight down from the rounded shoulder to the hem (coat) or to the waist "
     "(shirt), with a stitched side seam, so the torso is complete and nothing is cut away from it; the torso is the same width as in "
     "the reference. No hands anywhere. " + BG + STYLE + " Feet flat on one common baseline, a clean open magenta gap between the "
     "legs, each figure about 85 percent of the image height."},
    {"id": "cast_traveller_walk_arms", "kind": "bg", "refs": WALK_REF,
     "aspect": "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)",
     "out": "art_src/cast/raw/cast_traveller_walk_arms.png",
     "prompt": "A SPRITE SHEET for a children's pop-up storybook: FOUR separate die-cut cardstock ARM pieces for the paper puppet "
     "of the traveller boy in the FIRST reference image (same size as his arms there), " + BG + STYLE + "Each piece is ONE whole "
     "arm hanging straight down, seen from the front, from a rounded shoulder cap at the top to the hand at the bottom (simple "
     "mitten-like hand, thumb toward the body). THE FOUR PIECES, left to right: (1) his RIGHT arm (on the viewer's left) and (2) his "
     "LEFT arm (on the viewer's right) in the brick red / terracotta coat sleeve exactly as in the reference coat (stitched dashes, "
     "small leaf print, ochre dashed cuff band), cream-peach hand below the cuff; (3) his RIGHT arm and (4) his LEFT arm in the "
     "sage green shirt sleeve rolled up above the elbow exactly as in the reference (small flower print, rolled cuff), bare "
     "cream-peach forearm and hand. Arms the same length and proportions as in the reference figures."},
]

# ================================================================ 2026-11-18 「아기 돼지 삼형제」 (three_pigs) — SHARED cast
# Three piglets, a mother pig and a wolf: generic storybook animals for the shared cast library (game/art/cast/), reusable
# by later tales. Own style block (skill lesson: a shared style block leaked leaf prints onto faces): printed detail ONLY on
# clothing; skin, fur, faces, ears plain felt/cardstock. Pigs are a warm PEACH pink, far from the magenta key colour.
# Round 1 (no refs): cast_pigs (front lineup) + cast_wolf (front / side / back). Round 2 refs round 1 (same framing).
ANIMAL_STYLE = (
    "STYLE (same for every piece): flat orthographic view, like a printed die-cut pop-up book piece made of matte felt and "
    "cardstock, no perspective, no cast shadows, no drop shadows, no glow, no outline stroke in magenta, no white sticker border. "
    "Each part has ONE flat base colour with subtle matte felt/cardstock grain and a slightly gouache/screen-printed look, warm "
    "friendly cut-paper children's storybook style for ages 3-7, cute and gentle, never scary. PRINTED DETAIL (stitched dashed "
    "seams, small stamped dots, gingham checks, tiny stamped flowers) ONLY on CLOTHING (scarf, hat, overalls, apron, headscarf, "
    "waistcoat). Skin, fur, faces, ears, snouts, hands and feet are PLAIN with only a few soft stitched seam lines: NO flowers, NO "
    "leaves, NO botanical motifs on any face, skin or fur. Matte, no gloss, no photo texture, no 3D render. PALETTE (muted warm "
    "storybook): warm peach-pink skin, coral, brick red, ochre/mustard, golden straw, sky blue, cream, warm browns, cool greys, "
    "charcoal. Absolutely no magenta, no purple, no hot pink anywhere (pig skin is a soft warm PEACH-salmon pink like #F2B8A0, "
    "clearly orange-leaning, never magenta or bubble-gum pink). ")
PIG = ("chubby little piglet, storybook proportions about 2.5 heads tall (big round head, round tummy, short stubby legs that are "
       "still clearly visible, about one quarter of the figure height), soft warm peach-pink skin, big soft triangular ears tipped "
       "forward with a deeper coral inner ear, a round flat snout disc in deeper coral with two dark oval nostrils, a small curly "
       "tail, little cloven trotters in dark rosy brown, two small dark dot eyes, soft coral-orange cheek circles")
PIG_A = ("PIGLET A (the eldest brother): " + PIG + "; he wears a woven golden-yellow STRAW HAT with a small round brim and a thin "
         "brown band, and a mustard-ochre knitted SCARF wrapped once round his neck with fringed ends hanging down his front "
         "(stitched stripe print); no other clothes. ")
PIG_B = ("PIGLET B (the middle brother): " + PIG + "; no hat (a tiny tuft of peach hair on top); he wears sky-blue OVERALLS "
         "(bib with a stitched front pocket, two round ochre buttons, shoulder straps, short legs ending just above the knee, "
         "stitched dashed seams). ")
PIG_C = ("PIGLET C (the youngest brother): " + PIG + "; he wears a cream-white cloth CAP with a short peak and a little button "
         "on top, and brick-red OVERALLS (bib with a stitched front pocket, two round ochre buttons, shoulder straps, short legs "
         "ending just above the knee, stitched dashed seams). ")
MOM = ("THE MOTHER PIG: the same pig design but a grown-up mother, about 1.3 times taller than the piglets, rounder and softer; a "
       "brick-red HEADSCARF with small cream polka dots tied with a little knot on top of her head between the ears, a soft sage "
       "green dress, a cream APRON with a scalloped hem and a stitched pocket. ")
WOLF = ("THE WOLF: a lanky comic storybook WOLF who stands and walks UPRIGHT on two hind legs like a person (a paper puppet), about "
        "1.6 times taller than a piglet, cool medium-grey fur with a cream-beige muzzle, chin, chest and belly, a long pointed "
        "snout with a round dark navy nose, tall pointed ears with a pale coral inner ear, narrow sly yellow-ochre eyes with "
        "small dark pupils, a big bushy grey tail with a charcoal tip, long grey arms with four-fingered paw hands, big grey feet "
        "with charcoal toe pads; he wears a shabby mustard-brown WAISTCOAT with two wooden buttons and two stitched square "
        "patches. Comically sly and hungry, a little silly, never scary or bloody, no sharp teeth showing except two small "
        "blunt fangs when the mouth is open. ")
FRONT_POSE = ("FRONT figures: full body, standing upright facing the viewer straight on (not turned), symmetric, feet a little "
              "apart on one horizontal baseline, the FEET / TROTTERS SEEN FROM THE FRONT pointing straight at the viewer (never "
              "turned outward, never side-view feet). The two legs are clearly separate: a clean open magenta gap between the "
              "legs from the crotch (or the overalls hem) all the way down to the feet; the legs never touch. Arms hang down "
              "beside the body a little away from it unless the pose says otherwise, and hands NEVER overlap or touch the legs. "
              "Exactly two arms, two legs, two feet. ")
SIDE_POSE = ("SIDE figures: full body in clean side PROFILE facing to the RIGHT (nose pointing to the right edge), walking "
             "upright mid-stride: the near leg forward, the far leg back, a clear open magenta gap between the two legs from the "
             "crotch down to the feet, feet in side view flat on the baseline; one eye visible; arms swinging opposite to the "
             "legs. ")
BACK_POSE = ("BACK figures: full body seen from directly BEHIND (walking away from the viewer): back of the head and ears, the "
             "back of the clothes, the tail, the HEELS of the feet toward the viewer, legs apart with a clear open magenta gap, "
             "arms hanging at the sides; no face visible. ")
SHEET_COMMON = ("All figures standing in one row with their feet on a common baseline near the bottom of the image, each figure "
                "about 80 percent of the image height (a smaller character only as much smaller as stated), the SAME character "
                "design in every figure. ")
TP_REF_PIGS = ["art_src/cast/raw/cast_pigs.png"]
TP_REF_WOLF = ["art_src/cast/raw/cast_wolf.png"]
WIDE = "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)"
JOBS += [
    {"id": "cast_pigs", "kind": "bg", "aspect": WIDE, "out": "art_src/cast/raw/cast_pigs.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: FOUR separate full-body die-cut stand-up figures in one "
     "horizontal row, " + BG + ANIMAL_STYLE + PIG_A + PIG_B + PIG_C + MOM + FRONT_POSE +
     "All four standing in one row with their feet on a common baseline near the bottom of the image; the three piglets are the "
     "SAME size (each about 62 percent of the image height), the mother about 80 percent. THE FOUR FIGURES, left to right, all "
     "FRONT figures with a calm gentle walking face (soft open dot eyes looking ahead, a small calm closed mouth, NOT a big "
     "grin): (1) PIGLET A; (2) PIGLET B; (3) PIGLET C; (4) THE MOTHER PIG, a warm gentle smile, hands folded in front of her "
     "apron."},
    {"id": "cast_wolf", "kind": "bg", "aspect": WIDE, "out": "art_src/cast/raw/cast_wolf.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: THREE separate full-body die-cut stand-up figures of the "
     "SAME wolf in one horizontal row, " + BG + ANIMAL_STYLE + WOLF + FRONT_POSE + SIDE_POSE + BACK_POSE + SHEET_COMMON +
     "THE THREE FIGURES, left to right: (1) FRONT figure, calm sly walking face (half-lidded eyes, a small sly closed smile), "
     "arms hanging at his sides, tail curling out beside one leg; (2) SIDE figure facing RIGHT, prowling walk mid-stride, calm "
     "sly face, tail out behind him; (3) BACK figure, walking away, tail hanging down between the legs' gap without closing it "
     "(the tail ends above the gap or curls to one side)."},
]


def _pig_sheet(sid, who, figures):
    return {"id": sid, "kind": "bg", "refs": TP_REF_PIGS, "aspect": WIDE, "out": f"art_src/cast/raw/{sid}.png",
            "prompt": "A CHARACTER SHEET for a children's pop-up storybook: FIVE separate full-body die-cut stand-up figures of "
            "the SAME piglet as in the reference image (match him EXACTLY: same face, ears, snout, skin colour, clothes, size "
            "and proportions; this is the same paper puppet in new poses and expressions), in one horizontal row, " + BG
            + ANIMAL_STYLE + who + FRONT_POSE + SIDE_POSE + BACK_POSE + SHEET_COMMON +
            "The FACE expression must be big and clearly readable from far away. THE FIVE FIGURES, left to right: " + figures}


JOBS += [
    _pig_sheet("cast_pig_a_views", PIG_A,
               "(1) SIDE figure facing RIGHT, calm walk mid-stride, gentle face; (2) BACK figure walking away, hat and scarf ends "
               "seen from behind; (3) FRONT figure HAPPY: big open smile, eyes curved happy, one arm raised high waving hello; "
               "(4) FRONT figure SCARED: eyes wide round white with small pupils, mouth a wobbly open 'O', ears pinned back, "
               "both hands up at his cheeks; (5) SIDE figure facing RIGHT RUNNING away scared: leaning forward, long stride, "
               "arms flung back, eyes wide, hat about to fly but still on his head, a big open magenta gap between his legs."),
    _pig_sheet("cast_pig_a_expr", PIG_A,
               "(1) FRONT figure DEFIANT: hands on hips (elbows out, hands not touching the legs), chin up, eyebrows down, "
               "mouth a firm little frown, saying no; (2) FRONT figure PLAYING A FLUTE: a small wooden flute held to his mouth "
               "with both hands, eyes closed happily, a little tune; (3) FRONT figure PANTING AND TIRED: shoulders slumped, "
               "eyes squeezed, mouth open panting with tongue out, two soft blue sweat drops attached to his head; (4) SIDE "
               "figure facing RIGHT CARRYING a big golden tied bundle of STRAW in both arms in front of his tummy, walking "
               "mid-stride, cheerful; (5) FRONT figure TEASING AND LAUGHING: eyes squeezed shut laughing, mouth wide open, one "
               "hand on his tummy, the other pointing to the side."),
    _pig_sheet("cast_pig_b_views", PIG_B,
               "(1) SIDE figure facing RIGHT, calm walk mid-stride, gentle face; (2) BACK figure walking away, the overall "
               "straps crossing on his back; (3) FRONT figure HAPPY: big open smile, eyes curved happy, one arm raised high "
               "waving hello; (4) FRONT figure SCARED: eyes wide round white with small pupils, mouth a wobbly open 'O', ears "
               "pinned back, both hands up at his cheeks; (5) SIDE figure facing RIGHT RUNNING away scared: leaning forward, long "
               "stride, arms flung back, eyes wide, a big open magenta gap between his legs."),
    _pig_sheet("cast_pig_b_expr", PIG_B,
               "(1) FRONT figure DEFIANT: hands on hips (elbows out, hands not touching the legs), chin up, eyebrows down, "
               "mouth a firm little frown, saying no; (2) FRONT figure PLAYING A small VIOLIN: violin under his chin, bow in the "
               "other hand, eyes closed happily; (3) FRONT figure PANTING AND TIRED: shoulders slumped, eyes squeezed, mouth "
               "open panting with tongue out, two soft blue sweat drops attached to his head; (4) SIDE figure facing RIGHT "
               "CARRYING a short stack of three wooden PLANKS on his shoulder, walking mid-stride, cheerful; (5) FRONT figure "
               "HAMMERING: holding a small wooden hammer raised high in one hand, the other hand on his hip, a busy happy face "
               "with the tongue poking out in concentration."),
    _pig_sheet("cast_pig_c_views", PIG_C,
               "(1) SIDE figure facing RIGHT, calm walk mid-stride, gentle determined face; (2) BACK figure walking away, cap "
               "and overall straps seen from behind; (3) FRONT figure HAPPY: big open smile, eyes curved happy, one arm raised "
               "high waving hello; (4) FRONT figure BRAVE: one fist raised up at shoulder height, chest out, a confident brave "
               "smile, eyebrows determined; (5) FRONT figure STARTLED: eyes wide, mouth open 'O', both hands up beside his face, "
               "ears up."),
    _pig_sheet("cast_pig_c_expr", PIG_C,
               "(1) FRONT figure DEFIANT: hands on hips (elbows out, hands not touching the legs), chin up, eyebrows down, "
               "mouth a firm little frown, saying no; (2) FRONT figure LAYING A BRICK: holding one red brick in one hand and a "
               "small trowel in the other at chest height, calm patient focused face, tongue poking out a little; (3) FRONT "
               "figure PROUD: both hands on his overall straps, chest out, eyes closed in a proud content smile; (4) SIDE figure "
               "facing RIGHT CARRYING two red BRICKS stacked in both arms, walking mid-stride, slow and steady, a determined "
               "face; (5) FRONT figure CHEERING: both arms raised high in joy, eyes curved happy, mouth wide open laughing."),
    {"id": "cast_mom_expr", "kind": "bg", "refs": TP_REF_PIGS, "aspect": "landscape 3:2 at the largest available size (1536x1024)",
     "out": "art_src/cast/raw/cast_mom_expr.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: TWO separate full-body die-cut stand-up figures of the SAME "
     "mother pig as the rightmost figure of the reference image (match her EXACTLY: same face, headscarf, dress, apron, size), "
     "in one horizontal row, " + BG + ANIMAL_STYLE + MOM + FRONT_POSE + SHEET_COMMON +
     "THE TWO FIGURES, left to right: (1) FRONT figure WAVING GOODBYE: one arm raised high waving, the other hand on her heart, "
     "a warm loving smile with a little proud tear-free sparkle in her eyes; (2) FRONT figure TALKING WARMLY: both hands open "
     "in front of her at waist height, palms up, a kind encouraging open-mouth smile."},
]


def _wolf_sheet(sid, figures, n="FIVE"):
    return {"id": sid, "kind": "bg", "refs": TP_REF_WOLF, "aspect": WIDE, "out": f"art_src/cast/raw/{sid}.png",
            "prompt": "A CHARACTER SHEET for a children's pop-up storybook: " + n + " separate full-body die-cut stand-up "
            "figures of the SAME wolf as in the reference image (match him EXACTLY: same face, fur colours, ears, tail, "
            "waistcoat, size and proportions; the same paper puppet in new poses and expressions), in one horizontal row, "
            + BG + ANIMAL_STYLE + WOLF + FRONT_POSE + SIDE_POSE + SHEET_COMMON +
            "The FACE expression must be big and clearly readable from far away. THE FIGURES, left to right: " + figures}


JOBS += [
    _wolf_sheet("cast_wolf_side",
                "(1) SIDE figure facing RIGHT SNIFFING: walking mid-stride, nose tipped up high in the air, eyes closed "
                "dreamily, a hungry happy smile, one paw on his tummy; (2) SIDE figure facing RIGHT HUFFING AND PUFFING: standing "
                "with feet planted wide apart (gap between the legs), leaning back, chest swelled, cheeks hugely puffed out "
                "round, eyes squeezed shut with effort, lips pursed in a small 'O' blowing to the RIGHT (no wind drawn, just "
                "the face); (3) SIDE figure facing RIGHT EXHAUSTED: SITTING slumped on the ground (legs stretched out in front, "
                "flat bottom on the baseline), arms hanging limp, tongue lolling out, eyes dizzy spirals, ears drooping; (4) "
                "SIDE figure facing RIGHT SNEAKING on TIPTOE: crouched low, knees bent, walking on his toes mid-stride, both "
                "paws raised in front like a sneaky cartoon, a sly grin, eyes looking sideways; (5) SIDE figure facing RIGHT "
                "RUNNING AWAY in panic: leaning far forward, huge stride, arms flailing, eyes wide teary, mouth wide open "
                "yelping, his tail bushed out with a scorched charcoal-black tip and three small grey smoke puffs attached to "
                "it."),
    _wolf_sheet("cast_wolf_front",
                "(1) FRONT figure SHOUTING with a mock-fierce face: mouth wide open (two small blunt fangs), eyebrows down, one "
                "fist raised (knocking pose), the other hand on his hip; (2) FRONT figure HUNGRY AND SLY: licking his lips with "
                "the tongue out to one side, eyes narrow and greedy, both paws rubbing together in front of his chest; (3) FRONT "
                "figure 'OUCH, HOT!': jumping with both arms flung up, eyes bulging wide, mouth wide open yelping, fur standing "
                "on end in spikes, ears straight up, his tail bushed out behind him with a scorched charcoal tip and small grey "
                "smoke puffs, coral-red flush on the cheeks; (4) FRONT figure FALLING: upside-down tumble is NOT wanted - he is "
                "upright with both arms stretched straight up above his head and both legs together pointing down (as if "
                "dropping down a chimney feet first), eyes wide, mouth a surprised 'O' (in this one figure the legs may touch).",
                n="FOUR"),
]

# Walk parts (front rig). Same 3-sheet scheme as the traveller (front / half / lift legs; armless calm torsos).
TP_PARTS_REF = ["art_src/cast/raw/cast_pigs.png", "art_src/cast/raw/cast_wolf.png"]
LEG_COMMON = (
    "Each piece is ONE single leg seen EXACTLY FROM THE FRONT as if the character walks straight toward the viewer, cut off "
    "straight across at the very top (a flat horizontal top edge; no hips, no body, no hands). The top part of every piece is "
    "a TALL plain section (skin, fur or the overalls fabric; it will be hidden behind the body). The foot always points "
    "straight AT the viewer (front view, symmetric, never a side-view foot). MATCH THE REFERENCE CHARACTERS EXACTLY (colours, "
    "felt texture, trotters / paws). THE EIGHT PIECES, left to right, as four LEFT/RIGHT pairs: (1)(2) PIGLET A: plain warm "
    "peach-pink piglet leg with a dark rosy-brown cloven trotter seen from the front; (3)(4) PIGLET B: the sky-blue overalls "
    "short leg (stitched hem just above the knee), then the peach-pink lower leg and trotter; (5)(6) PIGLET C: the brick-red "
    "overalls short leg with the same hem, then the peach-pink lower leg and trotter; (7)(8) THE WOLF: a long grey furry leg "
    "with a cream inner stripe and a big grey foot seen from the front, charcoal toe pads at the bottom. The three piglet "
    "pairs are short and chubby (each about 2.2 times taller than wide), the wolf pair long (about 5 times taller than "
    "wide); tops on one common line, a wide magenta gap between the pieces." + NO_BOTANY)
JOBS += [
    {"id": "cast_tp_legs_front", "kind": "bg", "refs": TP_PARTS_REF, "aspect": WIDE, "out": "art_src/cast/raw/cast_tp_legs_front.png",
     "prompt": "A SPRITE SHEET for a children's pop-up storybook: EIGHT separate die-cut LEG pieces for the paper puppets of the "
     "three piglets and the wolf in the reference images, " + BG + ANIMAL_STYLE + LEG_COMMON +
     " THE POSE OF EVERY LEG: straight, hanging vertically, standing."},
    {"id": "cast_tp_legs_half", "kind": "bg", "refs": TP_PARTS_REF, "aspect": WIDE, "out": "art_src/cast/raw/cast_tp_legs_half.png",
     "prompt": "A SPRITE SHEET for a children's pop-up storybook: EIGHT separate die-cut LEG pieces for the paper puppets of the "
     "three piglets and the wolf in the reference images, " + BG + ANIMAL_STYLE + LEG_COMMON +
     " THE POSE OF EVERY LEG: just starting a step, the knee SLIGHTLY bent and coming a little toward the viewer, a soft knee "
     "bump, the lower leg a little foreshortened, the foot seen from the front; each leg about nine tenths of a straight "
     "leg's height, just as wide, hanging vertically, symmetric."},
    {"id": "cast_tp_legs_lift", "kind": "bg", "refs": TP_PARTS_REF, "aspect": WIDE, "out": "art_src/cast/raw/cast_tp_legs_lift.png",
     "prompt": "A SPRITE SHEET for a children's pop-up storybook: EIGHT separate die-cut LIFTED-LEG pieces for the paper puppets "
     "of the three piglets and the wolf in the reference images, " + BG + ANIMAL_STYLE + LEG_COMMON +
     " THE POSE OF EVERY LEG: mid-step, the knee BENT and the foot LIFTED toward the viewer: a rounded knee bump, a SHORT "
     "foreshortened lower leg, the foot seen from the front a little LARGER (closer to us), tipped up so a sliver of the sole "
     "shows; each lifted leg about three quarters of a straight leg's height, just as wide, hanging vertically, symmetric."},
    {"id": "cast_tp_walk_armless", "kind": "bg", "refs": TP_PARTS_REF, "aspect": WIDE,
     "out": "art_src/cast/raw/cast_tp_walk_armless.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: FOUR separate full-body die-cut stand-up figures, EXACTLY "
     "the three piglets (left three figures of the first reference) and the wolf (leftmost figure of the second reference), in "
     "that order (piglet A, piglet B, piglet C, wolf), same faces, same calm expression, same clothes, same size relation (the "
     "wolf about 1.6 times taller), same stance, but WITHOUT ARMS: both arms are removed because they are separate paper "
     "puppet pieces. Where each arm was, the body's side continues smoothly down from the rounded shoulder (the scarf, overall "
     "bib and straps, waistcoat stay complete), so the torso is complete and nothing is cut away from it; the torso is the "
     "same width as in the reference. No hands anywhere. " + BG + ANIMAL_STYLE + PIG_A + PIG_B + PIG_C + WOLF +
     " Feet flat on one common baseline, feet pointing at the viewer, a clean open magenta gap between the legs."},
]

# Side-view walk (user 2026-11-18: walkers may go left/right in side profile). Legs cut from the side stride figures show
# their repainted tops when swung, so side figures get drawn side legs too (tools/cast/side_legs.py fits them).
TP_SIDE_REF = ["art_src/cast/raw/cast_pig_a_views.png", "art_src/cast/raw/cast_wolf.png"]
JOBS += [
    {"id": "cast_tp_legs_side", "kind": "bg", "refs": TP_SIDE_REF, "aspect": WIDE, "out": "art_src/cast/raw/cast_tp_legs_side.png",
     "prompt": "A SPRITE SHEET for a children's pop-up storybook: EIGHT separate die-cut LEG pieces for the SIDE-VIEW paper "
     "puppets of three piglets and a wolf (the side-profile figures of the reference images, facing RIGHT), " + BG + ANIMAL_STYLE +
     "Each piece is ONE single leg seen exactly FROM THE SIDE, hanging straight and vertical, the FOOT POINTING TO THE RIGHT "
     "(side-view trotter or paw, toe to the right, heel to the left), cut off straight across at the very top (a flat "
     "horizontal top edge; no hips, no body). The top part of every piece is a TALL plain section (skin, fur or the overalls "
     "fabric; it will be hidden behind the body), the leg is the same width from the top down to the ankle. MATCH THE "
     "REFERENCE CHARACTERS EXACTLY. THE EIGHT PIECES, left to right, as four NEAR/FAR pairs (the FAR leg is the same leg "
     "printed one shade darker): (1)(2) PIGLET A: plain warm peach-pink piglet leg, dark rosy-brown cloven trotter in side "
     "view; (3)(4) PIGLET B: the sky-blue overalls short leg with a stitched hem just above the knee, then the peach-pink "
     "lower leg and trotter; (5)(6) PIGLET C: the same with brick-red overalls; (7)(8) THE WOLF: a long grey furry leg with a "
     "cream inner stripe and a big grey paw in side view, charcoal claws at the toe. Piglet pairs short and chubby (about "
     "2.2 times taller than wide), the wolf pair long (about 5 times taller than wide); tops on one common line, a wide "
     "magenta gap between the pieces." + NO_BOTANY},
]

# 2026-11-19 (user: "바깥보여줄때 창문에 돼지들이 이상해"): window PEEK figures — head + little hands on a windowsill, so a pig
# at home reads framed by a window (a whole standing figure scaled into a window looked wrong). One sheet, six pieces.
PEEK = ("PEEK figures: each piece is ONLY the HEAD and the two little HANDS (trotters) of a piglet peeking over a windowsill, "
        "front view facing the viewer straight on: the round head with both ears, the snout and the eyes, and below the chin the "
        "two little hands resting side by side on an invisible horizontal line, the bottom edge of the piece is a clean STRAIGHT "
        "horizontal cut just below the hands (the sill hides the rest); no body, no clothes except what is on the head (a hat or "
        "a cap) and the top of a scarf or overall straps just under the chin. Each piece about as wide as tall. ")
JOBS += [
    {"id": "cast_tp_peek", "kind": "bg", "refs": TP_REF_PIGS, "aspect": WIDE, "out": "art_src/cast/raw/cast_tp_peek.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: SIX separate die-cut pieces of the SAME three piglets in the "
     "reference image, in one horizontal row, " + BG + ANIMAL_STYLE + PIG_A + PIG_B + PIG_C + PEEK +
     "MATCH THE REFERENCE CHARACTERS EXACTLY (same faces, ears, hat, cap, colours). All six pieces the SAME size, bottoms on "
     "one common baseline. THE SIX PIECES, left to right: (1) PIGLET A peeking, SCARED (eyes wide and round, eyebrows up, "
     "small open worried mouth); (2) PIGLET A peeking, DEFIANT (eyebrows down, frowning, mouth open shouting 'no!'); "
     "(3) PIGLET B peeking, SCARED; (4) PIGLET B peeking, DEFIANT; (5) PIGLET C peeking, BRAVE calm (steady eyes, a small "
     "determined smile); (6) PIGLET C peeking, DEFIANT. A wide magenta gap between the pieces." + NO_BOTANY},
]

# 2026-11-19 (user: "돼지 옆으로 달려가는 모습 이상해유"): drawn RUN CYCLES (a rigid card hopping read as a dragged sticker).
RUN = ("RUN CYCLE: SIX full-body figures of the SAME piglet running, left to right: FOUR SIDE-PROFILE frames facing RIGHT "
       "(nose to the right edge), one run cycle in order: (1) CONTACT: front leg reaching forward heel down, back leg pushing "
       "off behind, arms swinging opposite; (2) DOWN: body lowest, front leg bent under the body taking the weight, back leg "
       "lifting behind; (3) PASSING: standing leg straight under the body, the other leg bent and swinging forward past it; "
       "(4) FLIGHT: both feet off the ground, legs spread forward and back, body highest, arms pumping. In every side frame the "
       "two legs are clearly separated with an open magenta gap between them, the arms clearly pump opposite to the legs, "
       "one eye visible, a SCARED face in profile (eye big and round, eyebrow up, mouth open in an 'eek'), ears flying back. "
       "Then TWO BACK-VIEW frames running AWAY from the viewer: (5) left leg up behind, right foot down; (6) right leg up "
       "behind, left foot down; back of the head and ears, the back of the clothes, the tail, arms pumping. All six the "
       "SAME scale as the reference character, feet on one common baseline (the flight frame's feet a little above it). ")
for _pid, _who in [("a", PIG_A), ("b", PIG_B), ("c", PIG_C)]:
    JOBS.append({"id": f"cast_pig_{_pid}_run_cycle", "kind": "bg", "refs": TP_REF_PIGS, "aspect": WIDE,
                 "out": f"art_src/cast/raw/cast_pig_{_pid}_run_cycle.png",
                 "prompt": "A CHARACTER SHEET for a children's pop-up storybook: SIX separate full-body die-cut figures of the "
                 "SAME piglet in one horizontal row, " + BG + ANIMAL_STYLE + _who + RUN + "MATCH THE REFERENCE CHARACTER "
                 "EXACTLY (same face, ears, hat or cap, clothes, colours). A wide magenta gap between the figures." + NO_BOTANY})

# 2026-11-19 (user: "늑대도 이상한디요?"): drawn WOLF cycles (the rigged side walk leaned back and slid like a cut-out).
_WCOMMON = ("All figures the SAME scale as the reference wolf, feet on one common baseline, a wide magenta gap between them. "
            "MATCH THE REFERENCE WOLF EXACTLY (same face, grey fur, cream muzzle, mustard waistcoat with patches, tail). ")
JOBS += [
    {"id": "cast_wolf_walk_cycle", "kind": "bg", "refs": TP_REF_WOLF, "aspect": WIDE, "out": "art_src/cast/raw/cast_wolf_walk_cycle.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: SIX separate full-body die-cut figures of the SAME wolf in one "
     "horizontal row, " + BG + ANIMAL_STYLE + WOLF + "SNEAKY PROWL WALK: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT (nose to "
     "the right edge) of one sneaking walk cycle in order: (1) CONTACT: front foot reaching forward heel down, back leg behind; "
     "(2) DOWN: knees bent lowest, weight on the front foot; (3) PASSING: one leg straight under the body, the other bent and "
     "swinging forward past it; (4) UP: rising on the standing toes, the other leg reaching forward. In every side frame he "
     "LEANS FORWARD (the head and shoulders ahead of the hips, never leaning back), knees bent, sly half-lidded eyes looking "
     "ahead, a sly closed grin, the two hands held up in front of the chest like a sneaky cartoon tiptoe (paws dangling), "
     "the big tail curving out behind and swinging with the step, the two legs clearly separated with an open magenta gap. "
     "(5)-(6) TWO BACK-VIEW frames walking AWAY from the viewer: (5) left foot lifted behind, (6) right foot lifted behind; back "
     "of the head and ears, the back of the waistcoat, the tail, arms swinging. " + _WCOMMON + NO_BOTANY},
    {"id": "cast_wolf_run_cycle", "kind": "bg", "refs": TP_REF_WOLF, "aspect": WIDE, "out": "art_src/cast/raw/cast_wolf_run_cycle.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: FOUR separate full-body die-cut figures of the SAME wolf in "
     "one horizontal row, " + BG + ANIMAL_STYLE + WOLF + "RUNNING AWAY (comic, scalded): FOUR SIDE-PROFILE frames facing RIGHT "
     "(nose to the right edge) of one run cycle in order: (1) CONTACT, (2) DOWN, (3) PASSING, (4) FLIGHT (both feet off the "
     "ground, legs spread). Leaning forward hard, a red scalded bottom with a little wisp of steam, eyes squeezed shut in a "
     "comic 'ouch' face, mouth open wailing, arms flailing forward, tail streaming behind, the two legs clearly separated with "
     "an open magenta gap. " + _WCOMMON + NO_BOTANY},
]

# 2026-11-19 (user: "이전 걸음 이상해요"): every walk in three_pigs is a drawn cycle (no leg-swapping rig).
PWALK = ("WALK CYCLE: EIGHT full-body figures of the SAME piglet walking happily, left to right: (1)-(4) FOUR SIDE-PROFILE "
         "frames facing RIGHT of one walk cycle in order: (1) CONTACT, (2) DOWN, (3) PASSING, (4) UP; a calm happy face in "
         "profile (eye soft, small smile), legs clearly separated with an open magenta gap, arms swinging opposite to the "
         "legs, a little bounce; (5)-(6) TWO BACK-VIEW frames walking AWAY from the viewer (left foot lifted behind, then the "
         "right), back of the head, ears, clothes and tail, arms swinging; (7)-(8) TWO FRONT-VIEW frames walking TOWARD the "
         "viewer (left foot stepping forward, then the right; trotters seen from the front pointing at the viewer), a calm "
         "happy face. All eight the SAME scale as the reference, feet on one common baseline. ")
for _pid, _who in [("a", PIG_A), ("b", PIG_B), ("c", PIG_C)]:
    JOBS.append({"id": f"cast_pig_{_pid}_walk_cycle", "kind": "bg", "refs": TP_REF_PIGS, "aspect": WIDE,
                 "out": f"art_src/cast/raw/cast_pig_{_pid}_walk_cycle.png",
                 "prompt": "A CHARACTER SHEET for a children's pop-up storybook: EIGHT separate full-body die-cut figures of "
                 "the SAME piglet in one horizontal row, " + BG + ANIMAL_STYLE + _who + PWALK + "MATCH THE REFERENCE "
                 "CHARACTER EXACTLY. A wide magenta gap between the figures." + NO_BOTANY})
JOBS += [
    {"id": "cast_pig_a_carry_cycle", "kind": "bg", "refs": TP_REF_PIGS, "aspect": WIDE, "out": "art_src/cast/raw/cast_pig_a_carry_cycle.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: FOUR separate full-body die-cut figures of the SAME piglet "
     "in one horizontal row, " + BG + ANIMAL_STYLE + PIG_A + "CARRY WALK: FOUR SIDE-PROFILE frames facing RIGHT of one walk "
     "cycle (CONTACT, DOWN, PASSING, UP) while he carries a big tied golden STRAW BUNDLE in both arms in front of his chest, "
     "a cheerful busy face in profile, legs clearly separated with an open magenta gap. MATCH THE REFERENCE CHARACTER "
     "EXACTLY. All four the same scale, feet on one baseline, a wide magenta gap between them." + NO_BOTANY},
    {"id": "cast_wolf_front_cycle", "kind": "bg", "refs": TP_REF_WOLF, "aspect": WIDE, "out": "art_src/cast/raw/cast_wolf_front_cycle.png",
     "prompt": "A CHARACTER SHEET for a children's pop-up storybook: FOUR separate full-body die-cut figures of the SAME wolf in "
     "one horizontal row, " + BG + ANIMAL_STYLE + WOLF + "FRONT VIEW (walking TOWARD the viewer, feet seen from the front "
     "pointing at the viewer): (1)-(2) a sneaky WALK, sly half-lidded eyes and sly grin, hands held up in front of the chest, "
     "left foot stepping forward, then the right; (3)-(4) RUNNING toward the viewer, comic scalded 'ouch' face (eyes "
     "squeezed shut, mouth wailing), arms flailing, left leg up, then the right. Legs clearly separated with an open magenta "
     "gap. " + _WCOMMON + NO_BOTANY},
]

if __name__ == "__main__":
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cast_jobs.json")
    json.dump(JOBS, open(p, "w"), ensure_ascii=False, indent=1)
    print(p, len(JOBS))
