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

if __name__ == "__main__":
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cast_jobs.json")
    json.dump(JOBS, open(p, "w"), ensure_ascii=False, indent=1)
    print(p, len(JOBS))
