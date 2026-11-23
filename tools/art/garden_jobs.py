#!/usr/bin/env python3
"""Shared VEGETABLE GARDEN (텃밭) kit for tools/run_jobs.py (2026-11-23, turnip v2: "순무는 텃밭이 없네용?").

  python3 tools/art/garden_jobs.py            # writes tools/art/garden_jobs.json
  bash -c 'python3 tools/run_jobs.py tools/art/garden_jobs.json story_veg_garden story_veg_ground'

Generic (any tale can dress a cottage vegetable garden with it): story_* categories so the meadow template's category
queries never pick them, tags garden / vegetable / soil / farm. Two sheets:
- story_veg_garden: stand-up pieces (soil ridges, vegetable rows, fence, tools);
- story_veg_ground: pieces seen from DIRECTLY ABOVE, laid flat on the page (`flat: true` set entries): the tilled plot,
  a path.
PAPER look only (no felt, no stitching), per-category block (plants are the subject; no faces, no animals, no people).
Style reference: the turnip garden sheet (paper), told NOT to copy its pieces.
After generation: python3 tools/atlas/add_sheet.py <sheet> && python3 tools/atlas/veg_garden_fix.py <sheet>
(labels: tools/atlas/labels/story_veg_*.json; contact sheets art_src/atlas/qa/story_veg_*_contact.png).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_A = "art_src/atlas/raw/"
WIDE = "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)"

BG = ("on a perfectly flat, uniform, solid pure MAGENTA background (#FF00FF, RGB 255,0,255) with no texture, no gradient, "
      "no vignette, no shadows on the background. Every piece is fully separate and isolated, with a clear empty magenta gap "
      "of at least 40 pixels on every side; pieces never touch or overlap each other and never touch the image border. "
      "No grid lines, no labels, no text, no letters, no numbers. ")
COLOUR = ("COLOUR RULE: NO pink and NO magenta-ish colour anywhere: any pink is a warm CORAL-PEACH (#F2A07B); any purple "
          "is a deep BLUE-violet plum (#5B4A8C), never reddish purple. ")
PAPER = ("STYLE (same for every piece): a die-cut pop-up book piece made of MATTE CUT PAPER and thin cardstock: every "
         "colour area is a separate cut or torn sheet of coloured paper glued in layers (a lighter or darker paper layer "
         "on top for shading and detail), crisp cut edges or softly torn deckled edges, each layer edge with a thin darker "
         "cut line and a faint lighter rim on its upper-left (lit) side, fine paper-fibre grain, matte, no gloss. "
         "ABSOLUTELY NO felt, NO wool, NO fuzz, NO fabric or knitted texture, NO stitches, NO dashed stitch lines, NO "
         "sewing seams, NO embroidery. No cast shadows, no drop shadows, no glow, no white sticker border. Warm European "
         "fairy-tale picture book for ages 3-7: a cottage VEGETABLE GARDEN in summer. " + COLOUR)
GARDEN = PAPER + ("Vegetables, soil and garden things are the subject (leaf veins as cut lines are fine). NO faces on "
                  "anything, NO animals, NO people, NO text. SOIL is warm cocoa / clay BROWN cut paper (#6B4A32 furrows, "
                  "#8A5E3C ridges, #B8794F lit tops) with a few tiny darker paper crumbs, never grey, never black. ")
REF = [RAW_A + "story_tn_garden.png"]
REF_LINE = ("The reference image only shows the PAPER STYLE to match (layered matte cut paper, the same soil and leaf "
            "colours); do NOT copy its pieces (no giant turnip, no seed, no watering can, no mouse mound). ")

JOBS = []


def sheet(jid, n, body, flat=False):
    lead = (f"A PROP SHEET for a children's pop-up storybook: {n} separate die-cut cardboard pieces, " +
            ("every piece seen from DIRECTLY ABOVE (a top-down plan view, like a paper piece lying flat on a table, no "
             "perspective, no horizon, no sides showing), " if flat else
             "every piece a stand-up piece seen straight from the front, standing on a flat straight bottom edge (the "
             "hinge), no perspective, "))
    JOBS.append({"id": jid, "kind": "bg", "refs": REF, "aspect": WIDE, "out": RAW_A + jid + ".png",
                 "prompt": lead + BG + GARDEN + REF_LINE + body})


sheet("story_veg_garden", "SIXTEEN",
      "Pieces, all straight on from the front, in rows, left to right: "
      "(1) a LONG LOW SOIL RIDGE: one tilled garden row of mounded brown soil seen from the front, very wide and low "
      "(about 7 times as wide as tall), its top a soft scalloped bumpy line of layered torn brown paper, a few crumbs, "
      "flat bottom edge, nothing growing on it; "
      "(2) a second LONG LOW SOIL RIDGE like piece 1 but with a slightly different scallop rhythm and a darker furrow "
      "layer along its foot; "
      "(3) a row of four round LETTUCE heads (frilly light-green leaves) sitting on a low brown soil ridge, wide and low; "
      "(4) a row of ONION / spring-onion plants: tall thin straight blue-green leaves with small cream bulbs peeping out "
      "of a low brown soil ridge, wide; "
      "(5) a row of four ordinary small TURNIPS: each a round cream bulb with a small blue-violet shoulder half sunk in a "
      "low brown soil ridge, with a small tuft of green leaves on top (normal garden size, all four alike), wide and low; "
      "(6) two TOMATO plants tied to straight wooden stakes with round red tomatoes and green leaves, standing in a "
      "little soil mound (one piece); "
      "(7) a row of PEA plants climbing a low wooden stick-and-string trellis with green pods and small white flowers, "
      "wide; "
      "(8) a sprawling PUMPKIN vine: big round green leaves, curly tendrils, two small orange pumpkins on the ground, wide "
      "and low; "
      "(9) a row of STRAWBERRY plants: low three-part leaves, small red berries and white flowers, on a low soil ridge, "
      "wide and low; "
      "(10) a LONG low wooden PICKET FENCE section: weathered cream-white pointed pickets on two horizontal rails, about "
      "6 times as wide as tall; "
      "(11) a SHORT picket fence section (4 pickets) with a corner post; "
      "(12) a small wooden garden GATE standing OPEN (the gate leaf turned toward us, hinged to one post), cream-white "
      "pickets like piece 10; "
      "(13) an EMPTY wooden WHEELBARROW with one spoked wheel and two handles, side view, unpainted wood; "
      "(14) a wicker BASKET heaped with fresh vegetables (carrots with tops, a cabbage, two radishes, a cucumber); "
      "(15) three small wooden ROW MARKER sticks, each topped with a tiny blank seed-packet picture card (pictures of a "
      "carrot, a cabbage, a pea pod, no words); "
      "(16) a LOW border EDGING strip of rounded field stones set in a line, very wide and low (about 8 times as wide as "
      "tall). Every row piece is wide and low with a flat bottom edge; keep every piece clearly separate.")

sheet("story_veg_ground", "FOUR",
      "Pieces, all seen from directly ABOVE, lying flat: "
      "(1) the BIGGEST piece, about two thirds of the image width: a RECTANGULAR TILLED VEGETABLE PLOT seen from above: "
      "warm brown cut-paper soil with straight parallel RIDGES and FURROWS running LEFT TO RIGHT across it (about 9 "
      "evenly spaced long ridges: each ridge a lighter clay-brown torn paper strip with a soft scalloped edge, the furrows "
      "between them darker cocoa brown), a few tiny paper crumbs and pebbles, its outer edge a slightly irregular torn "
      "paper edge; NO plants on it, NO path, NO fence; "
      "(2) a smaller SQUARE patch of loose freshly dug brown soil seen from above, crumbly layered torn paper, torn "
      "irregular edge; "
      "(3) a long narrow garden PATH of round flat pale-grey and sandy STEPPING STONES set in a strip of beaten light "
      "tan earth, seen from above, running LEFT TO RIGHT, about 6 times as long as wide; "
      "(4) a long narrow strip of beaten light tan EARTH PATH seen from above with a few pebbles, torn edges, running "
      "LEFT TO RIGHT, about 7 times as long as wide.", flat=True)

if __name__ == "__main__":
    p = os.path.join(HERE, "garden_jobs.json")
    json.dump(JOBS, open(p, "w"), ensure_ascii=False, indent=1)
    print(p, len(JOBS))
