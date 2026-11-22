#!/usr/bin/env python3
"""「해님 달님」 (sunmoon) art jobs for tools/run_jobs.py (phase 1, 2026-11-22).

  python3 tools/art/sunmoon_jobs.py            # writes tools/art/sunmoon_jobs.json
  bash -c 'python3 tools/run_jobs.py tools/art/sunmoon_jobs.json <ids>'

Round 1: the cast lineup (design reference = 톡톡's sunmoon cast, art_src/cast/raw/ref_sm_toktok.png, redrawn in our
die-cut felt look) + every set / prop sheet (no character refs). Round 2 references SINGLE-CHARACTER crops of the new
lineup (art_src/cast/raw/ref_sm_<role>.png; a multi-character ref made the model draw its first character everywhere).

Style blocks per category (skill lesson: a shared block leaks motifs):
- SM_CHAR: people and the tiger. Printed detail ONLY on clothing (hanbok trims, 색동 stripes, stitched seams); skin, fur,
  faces plain. The tiger is a children's-book tiger: chubby, round, big friendly eyes, never fangs or claws out.
- SM_BUILD: the thatched cottage and its yard objects. Material prints only (straw, mud plaster, wood grain, paper lattice,
  stone), no botanical motifs.
- SM_NATURE: mountains, pines, rocks, grass: Korean folk-painting (minhwa) print allowed (pine needle fans, ridge stripes).
- SM_SKY: sun, moon, clouds, ropes, stars: no plants, no green.
Key colour magenta #FF00FF: every pink is a CORAL / PEACH / SALMON (hue away from magenta), every purple blue-violet.
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
COLOUR = ("COLOUR RULE: NO pink and NO magenta-ish colour anywhere: every 'pink' is a warm CORAL-PEACH or SALMON-ROSE (like "
          "#F2A07B or #E8836B, clearly orange-leaning), cheeks a soft coral-peach; any purple is a deep BLUE-violet. ")
FELT = ("flat orthographic view, like a printed die-cut pop-up book piece made of matte felt and cardstock, no perspective, "
        "no cast shadows, no drop shadows, no glow, no outline stroke in magenta, no white sticker border. Each part has ONE "
        "flat base colour with subtle matte felt/cardstock grain and a slightly gouache / screen-printed look, warm friendly "
        "cut-paper children's storybook style for ages 3-7, Korean traditional folk-tale setting (Joseon countryside). ")
SM_CHAR = ("STYLE (same for every piece): " + FELT +
           "PRINTED DETAIL (stitched dashed seams, small stamped dots, saekdong rainbow-stripe sleeve bands, ribbon ties) "
           "ONLY on CLOTHING (hanbok jackets, skirts, trousers, headscarves). Skin, fur, faces, hands and feet are PLAIN "
           "with only a few soft stitched seam lines. NO flowers, NO leaves, NO botanical motifs on anyone. Matte, no "
           "gloss, no 3D render. PALETTE: indigo blue, cream, coral-peach, salmon-rose, charcoal grey, mustard, jade "
           "green, warm browns, tiger orange. " + COLOUR)
FACE = ("Faces are simple and sweet: two dark dot or curved-line eyes, a tiny mouth, round soft coral-peach cheek circles; "
        "the expression is big and readable from far away. ")
BOY = ("THE BROTHER (오빠): a Korean boy about 8 years old, storybook proportions about 2.6 heads tall (a big round head), "
       "a round cream-peach face, glossy black bowl-cut hair with straight bangs, an INDIGO-BLUE hanbok jacket (jeogori) "
       "with a cream collar band and an indigo tie ribbon, cream baggy trousers (baji) tied at the ankles, black round "
       "rubber shoes (gomusin). ")
GIRL = ("THE LITTLE SISTER (동생): a Korean girl about 6 years old, a little shorter than her brother, a round cream-peach "
        "face, dark-brown hair in TWO small high pigtail buns tied with coral ribbons and soft bangs, a CORAL-PEACH hanbok "
        "jacket with saekdong rainbow-stripe sleeve bands and a red tie ribbon, a full SALMON-ROSE skirt (chima) to the "
        "ankles, coral round shoes. ")
MOM = ("THE MOTHER (엄마): a gentle young Korean mother, slim, about 1.45 times as tall as the brother, a kind round face, "
       "dark hair pulled back into a low bun with a wooden hairpin, a soft CORAL-PEACH jeogori with a deep-red tie ribbon "
       "and a long CHARCOAL-GREY chima skirt to the ground, a cream apron tied at the waist, simple grey cloth shoes. ")
TIGER = ("THE TIGER (호랑이): a big CHUBBY children's-picture-book TIGER who walks UPRIGHT on his hind legs like a person, "
         "about 1.75 times as tall as the brother: warm tiger-ORANGE felt fur with dark-brown stripes, a big round cream "
         "belly, cream muzzle, round ears with cream insides, small round dark eyes with a sly-but-silly look, coral-peach "
         "cheek circles, chunky soft paws (NO claws showing, NO sharp fangs, NO blood, never horrifying), a long striped "
         "tail. Menacing in a funny way, like a greedy bully in a kids' book. ")
RICH = ("THE RICH LADY (부잣집 마님): a plump kind Korean lady of a big house, about as tall as the mother, a round smiling "
        "face, hair in a neat low bun with a jade hairpin, a JADE-GREEN jeogori with a gold-stamped dot trim and an "
        "INDIGO-NAVY full skirt, cream socks and boat-shaped shoes. ")
LEGS = ("EVERY standing or walking figure has a clearly VISIBLE open magenta GAP between the two legs (or below the skirt "
        "hem between the feet); legs never touch or overlap; hands never overlap the legs. Exactly two arms and two legs. ")
FRONT = ("FRONT figures: full body facing the viewer straight on (not turned), feet a little apart on one horizontal "
         "baseline, shoes seen from the front. ")
SIDE = "SIDE figures: full body in clean side PROFILE facing to the RIGHT (nose to the right edge), one eye visible. "
BACK = ("BACK figures: seen from directly BEHIND: back of the head / hair bun, jacket and skirt back, heels toward the "
        "viewer, no face. ")
ROW = ("All figures in ONE horizontal row with their feet on a common baseline near the bottom of the image, a wide magenta "
       "gap between them, the SAME character design in every figure. ")
REF_LINE = ("MATCH THE REFERENCE CHARACTER EXACTLY (same face, hair, clothes, colours, proportions and size); this is the "
            "same paper puppet in new poses. THIS SHEET SHOWS ONLY THIS ONE CHARACTER; do NOT draw any other character. ")
NO_BOT = " IMPORTANT: no flowers, no leaves, no plants, no botanical motifs on any character."

REF_TOKTOK = [RAW_C + "ref_sm_toktok.png"]


def REF(role):
    return [RAW_C + f"ref_sm_{role}.png"]


JOBS = []


def cast(jid, n, who, body, refs, extra=""):
    JOBS.append({"id": jid, "kind": "bg", "refs": refs, "aspect": WIDE, "out": RAW_C + jid + ".png",
                 "prompt": f"A CHARACTER SHEET for a children's pop-up storybook: {n} separate full-body die-cut stand-up "
                 "figures in one horizontal row, " + BG + SM_CHAR + who + FACE + LEGS + extra + ROW +
                 (REF_LINE if refs != REF_TOKTOK else "") + body + NO_BOT})


# ---------------------------------------------------------------- round 1: lineup (design ref = 톡톡 cast)
cast("cast_sm_lineup", "FIVE", BOY + GIRL + MOM + TIGER + RICH,
     "The reference image shows the character DESIGNS (faces, hair, colours, hanbok) from an older version: keep those "
     "designs but redraw every figure in THIS printed die-cut style, and make every pink a coral-peach / salmon-rose. "
     "SIZES: the brother about 46 percent of the image height, the sister about 42 percent, the mother about 68 percent, "
     "the rich lady about 66 percent, the tiger standing upright about 82 percent. THE FIVE FIGURES, left to right, all "
     "FRONT figures with a calm gentle face (soft dot eyes, a small calm smile), arms relaxed a little away from the body: "
     "(1) THE BROTHER; (2) THE SISTER; (3) THE MOTHER holding a round woven straw BASKET (empty) in both hands in front of "
     "her apron; (4) THE TIGER standing upright on his hind legs, front paws resting on his round belly, tail curling out "
     "to one side without closing the leg gap, a sly little grin; (5) THE RICH LADY, hands folded in front.",
     REF_TOKTOK, extra=FRONT)

# ---------------------------------------------------------------- round 2: expressions (ref = single-character crops)
cast("cast_sm_boy_expr", "SIX", BOY,
     "SIX figures of THE BROTHER, left to right: (1) FRONT, WAVE GOODBYE: one hand waving high, a big bright open smile; "
     "(2) FRONT, SCARED: shoulders up, both fists at his chest, eyes wide, a small wobbly open mouth, trembling; (3) FRONT, "
     "SHUSH: one finger at his lips whispering 'shh!', eyes looking sideways, leaning forward a little; (4) FRONT, CLEVER: "
     "one hand on his hip, the other index finger raised, a cheeky proud grin with closed happy eyes; (5) FRONT, PRAYING: "
     "both palms pressed together at his chest, face tilted UP to the sky, eyes looking up, hopeful; (6) FRONT, GIGGLE: "
     "both hands over his mouth giggling, eyes closed in happy curves, shoulders up.", REF("boy"), extra=FRONT)
cast("cast_sm_girl_expr", "SIX", GIRL,
     "SIX figures of THE SISTER, left to right: (1) FRONT, WAVE GOODBYE: one hand waving high, a big sweet smile; (2) "
     "FRONT, SCARED: hugging herself, eyes wide and teary-shiny (no real tears falling), a small worried mouth; (3) FRONT, "
     "BLURT LAUGH: laughing out loud with the mouth wide open, eyes closed in happy curves, one hand pointing down, "
     "innocent; (4) FRONT, SHY AND AFRAID: hands clasped under her chin, eyebrows tilted, a small shy mouth (afraid of the "
     "dark); (5) FRONT, GIGGLE: both hands over her mouth giggling, eyes closed in happy curves; (6) FRONT, WOW: both hands "
     "at her cheeks, eyes wide and sparkling, mouth a round happy 'O'.", REF("girl"), extra=FRONT)
cast("cast_sm_kids_views", "SIX", BOY + GIRL,
     "SIX figures, left to right: (1) THE BROTHER, SIDE figure facing RIGHT, standing calmly; (2) THE BROTHER, BACK figure "
     "standing; (3) THE SISTER, SIDE figure facing RIGHT, standing calmly; (4) THE SISTER, BACK figure standing; (5) THE "
     "BROTHER, FRONT, HOLDING ON: standing with one arm stretched up holding something above his head (an invisible rope "
     "or branch), the other hand stretched down to the side (holding his sister's hand), brave face; (6) THE SISTER, FRONT, "
     "HOLDING ON: one arm stretched UP to the side (holding her brother's hand), the other hand at her chest, worried "
     "face. (The figures do not touch; leave the magenta gap.)", REF("boy") + REF("girl"), extra=SIDE + BACK + FRONT)
cast("cast_sm_mom_expr", "SIX", MOM,
     "SIX figures of THE MOTHER, left to right: (1) FRONT, WAVE GOODBYE: one hand waving, the other holding the empty "
     "round straw basket on her arm, a warm smile; (2) FRONT, TALKING KINDLY: one index finger raised as she reminds the "
     "children ('lock the door'), the basket on her arm, a loving face; (3) FRONT, WORKING: sleeves rolled up, holding a "
     "wooden paddle in both hands as if stirring a big pot, a busy cheerful face (no basket); (4) FRONT, HAPPY WITH A "
     "FULL BASKET: hugging the straw basket heaped with round white and soft-green rice cakes (tteok) under a cream cloth "
     "corner, a joyful face; (5) FRONT, FRIGHTENED: clutching the basket of rice cakes to her chest, eyes wide, shoulders "
     "up, trembling, a small worried mouth (not crying); (6) FRONT, GIVING: holding out ONE round white rice cake in one "
     "trembling hand toward the RIGHT, the basket on the other arm, a nervous face.", REF("mom"), extra=FRONT)
cast("cast_sm_mom_views", "FOUR", MOM,
     "FOUR figures of THE MOTHER, left to right: (1) SIDE figure facing RIGHT, standing, the straw basket of rice cakes "
     "hooked on her near arm, a calm face; (2) BACK figure standing with the basket on her arm; (3) FRONT, TIRED BUT GLAD: "
     "the full basket on her arm, one hand on her lower back, a gentle tired smile; (4) SIDE figure facing RIGHT, HURRYING: "
     "leaning forward, holding the empty basket, worried face.", REF("mom"), extra=SIDE + BACK + FRONT)
cast("cast_sm_tiger_expr_a", "SIX", TIGER,
     "SIX FRONT figures of THE TIGER, left to right: (1) ROAR 'EO-HEUNG!': both front paws raised beside his head with "
     "soft round paw pads showing, mouth wide open in a big silly roar, eyes squeezed (funny, not scary, no fangs); (2) "
     "DEMAND: leaning forward, one paw held out palm-up asking for food, a bossy greedy grin, tongue licking the lip; (3) "
     "GULP: eyes closed in bliss, cheeks puffed full, both paws patting his belly, a round white rice cake just "
     "disappearing into his mouth; (4) BELLY BIGGER: the same tiger with a noticeably ROUNDER BIGGER belly, both paws on "
     "it, a satisfied smirk; (5) BELLY HUGE: the belly enormous and round like a ball, buttons of fur stretched, a dizzy "
     "happy face; (6) SLY: one paw at his chin, eyes half closed, a sneaky scheming grin.", REF("tiger"), extra=FRONT)
cast("cast_sm_tiger_expr_b", "SIX", TIGER,
     "SIX figures of THE TIGER, left to right: (1) FRONT, SEARCHING: one paw shading his eyes, looking to the side, "
     "puzzled mouth; (2) FRONT, LOOKING UP SURPRISED: head tilted back looking up, eyes wide, mouth a round 'huh?'; (3) "
     "FRONT, SNEAKY WHISPER: paw beside his mouth, leaning, sly; (4) SIDE figure facing RIGHT, standing upright calmly; (5) "
     "BACK figure standing upright (striped back, tail); (6) FRONT, DAZED: sitting on the ground with a big round BUMP "
     "(a round swollen lump) on top of his head, little stars and a swirl beside his head (touching the head), eyes "
     "spiral-dizzy, mouth wobbly 'ouch', paws rubbing his bottom.", REF("tiger"), extra=FRONT + SIDE + BACK)
cast("cast_sm_tiger_disguise", "SIX", TIGER,
     "SIX figures of THE TIGER DISGUISED AS THE MOTHER: he wears the mother's CORAL-PEACH jeogori (too small, tied with "
     "the deep-red ribbon), her long CHARCOAL-GREY chima skirt (his striped tail and big feet poking out below), and a "
     "cream HEADSCARF tied under his chin over his ears; the tiger face, orange fur and stripes clearly show. Left to "
     "right: (1) FRONT, standing, paws folded, a fake sweet smile; (2) FRONT, KNOCKING: one paw raised in a loose fist as "
     "if knocking on a door to the right, sly grin; (3) FRONT, FAKE SWEET VOICE: one paw at his cheek, eyes half closed, "
     "mouth in a fake sing-song 'ooh'; (4) SIDE figure facing RIGHT, standing; (5) BACK figure standing (skirt, tail out "
     "below, headscarf knot); (6) FRONT, CAUGHT: eyes wide, paws up, the headscarf slipping off one ear.",
     REF("tiger"), extra=FRONT + SIDE + BACK)
cast("cast_sm_tiger_tree", "SIX", TIGER,
     "SIX figures of THE TIGER at the tree, left to right: (1) SIDE facing RIGHT, LOOKING DOWN INTO A WELL: bending "
     "forward at the waist, paws on knees, peering down, curious; (2) SIDE facing RIGHT, PULLING A ROPE: leaning back, both "
     "paws gripping a short piece of rope hanging down in front of him, effort face; (3) SIDE facing RIGHT, SMEARING OIL: "
     "holding a small brown sesame-oil bottle in one paw, the other paw flat forward rubbing, a busy grin; (4) SIDE facing "
     "RIGHT, SLIPPING: hugging nothing with both arms and legs as if sliding down a tree trunk to his right, eyes wide, "
     "mouth open 'whoa'; (5) SIDE facing RIGHT, CLIMBING WITH AN AXE (frame A): one paw raised high holding a small wood "
     "axe above his head, the other paw and one foot reaching forward as if gripping a trunk to his right, the other leg "
     "bent below, determined grin; (6) SIDE facing RIGHT, CLIMBING WITH AN AXE (frame B): the axe swung down at chest "
     "height, the opposite arm and leg reaching up.", REF("tiger"), extra=SIDE)
cast("cast_sm_tiger_rope", "FIVE", TIGER,
     "FIVE figures of THE TIGER with a rope, left to right: (1) FRONT, GRABBING EAGERLY: both paws raised up high gripping "
     "nothing above his head (a rope will be there), a greedy happy grin, feet on the ground; (2) BACK view, CLIMBING A "
     "ROPE (frame A): both paws gripping above his head one over the other, legs hugging below, seen from behind; (3) BACK "
     "view, CLIMBING (frame B): the other paw higher, legs pushing; (4) FRONT, FALLING: upside down, arms and legs "
     "flailing, mouth open in a comic 'aaah!', eyes squeezed, a short broken bit of rope in one paw; (5) SIDE facing "
     "RIGHT, RUNNING AWAY: a big round BUMP on top of his head, leaning forward, legs apart mid-run, comic teary eyes.",
     REF("tiger"))
cast("cast_sm_climb", "EIGHT", BOY + GIRL,
     "EIGHT CLIMBING figures, left to right: (1)-(2) THE BROTHER seen from BEHIND climbing a tree trunk (frame A: right "
     "arm and left leg up, frame B: left arm and right leg up), arms reaching up as if hugging a trunk, legs bent; (3)-(4) "
     "THE SISTER from BEHIND climbing the same way (frames A, B); (5)-(6) THE BROTHER from the FRONT climbing a ROPE (both "
     "hands gripping above his head, frame A legs crossed lower, frame B knees pulled up), looking up hopefully; (7)-(8) "
     "THE SISTER from the FRONT climbing a rope (frames A, B), a brave little smile. No tree and no rope drawn: only the "
     "children, their hands closed round the missing trunk / rope.", REF("boy") + REF("girl"))
cast("cast_sm_treetop", "FOUR", BOY + GIRL,
     "FOUR figures, left to right: (1) THE BROTHER sitting on a branch (no branch drawn), front view, legs dangling, "
     "one arm out sideways as if round his sister, a brave but worried face; (2) THE SISTER sitting the same way, holding "
     "on with both hands, scared; (3) THE BROTHER sitting, front, giggling with a hand over his mouth; (4) THE SISTER "
     "sitting, front, giggling with both hands over her mouth. Their seat line (the bottom of the thighs) is flat and "
     "horizontal.", REF("boy") + REF("girl"))
cast("cast_sm_rich_expr", "FOUR", RICH,
     "FOUR FRONT figures of THE RICH LADY, left to right: (1) KIND SMILE, hands folded; (2) GIVING: holding out a wide "
     "round wooden tray heaped with round white and soft-green rice cakes toward the LEFT, a generous smile; (3) THANKING: "
     "one hand raised, palm open, a warm laugh; (4) SIDE figure facing RIGHT standing.", REF("rich"), extra=FRONT + SIDE)

# ---------------------------------------------------------------- drawn cycles (ref = the character's crop)
WALK8 = ("WALK CYCLE: EIGHT full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one walk "
         "cycle in order: (1) CONTACT, (2) DOWN, (3) PASSING, (4) UP; a calm face in profile, legs clearly separated with "
         "an open magenta gap, arms swinging opposite to the legs; (5)-(6) TWO BACK-VIEW frames walking AWAY (left foot "
         "lifted behind, then the right); (7)-(8) TWO FRONT-VIEW frames walking TOWARD the viewer (left foot forward, then "
         "the right; shoes seen from the front). All eight the SAME scale as the reference, feet on one common baseline. ")
RUN6 = ("RUN CYCLE: SIX full-body figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of one run cycle "
        "(CONTACT, DOWN, PASSING, FLIGHT with both feet off the ground), legs wide apart with an open magenta gap, arms "
        "pumping, leaning forward, a hurried worried face; (5)-(6) TWO BACK-VIEW frames running AWAY (left foot up behind, "
        "then the right). All six the SAME scale, the lowest foot on one baseline. ")
cast("cast_sm_boy_walk", "EIGHT", BOY, WALK8, REF("boy"))
cast("cast_sm_girl_walk", "EIGHT", GIRL, WALK8, REF("girl"))
cast("cast_sm_boy_run", "SIX", BOY, RUN6, REF("boy"))
cast("cast_sm_girl_run", "SIX", GIRL, RUN6, REF("girl"))
cast("cast_sm_mom_walk", "EIGHT", MOM,
     WALK8 + "She carries the round straw basket of rice cakes hooked on her near arm in every frame (the basket swings a "
     "little); the skirt hem sways, her feet show below it.", REF("mom"))
cast("cast_sm_tiger_walk", "EIGHT", TIGER,
     WALK8 + "He walks upright on his hind legs with a heavy, swaggering waddle, tail swinging; a sly face in the side "
     "frames.", REF("tiger"))
cast("cast_sm_tiger_sneak", "SIX", TIGER,
     "SNEAK + DISGUISE WALK: SIX figures, left to right: (1)-(4) FOUR SIDE-PROFILE frames facing RIGHT of THE TIGER "
     "DISGUISED AS THE MOTHER (her coral-peach jeogori, charcoal-grey chima, cream headscarf tied under his chin, tail out "
     "below the skirt) walking upright in a tiptoe sneak, leaning INTO the walk (forward, never back), paws held up in "
     "front, sly grin, feet clearly apart; (5)-(6) TWO FRONT-VIEW frames of the disguised tiger walking toward the viewer "
     "(left foot forward, then the right). All six the SAME scale, feet on one baseline. MATCH THE SECOND REFERENCE "
     "(the disguised tiger) EXACTLY: PLAIN coral-peach jacket sleeves with NO rainbow stripes, a DEEP-RED tie ribbon "
     "(never blue), the charcoal-grey skirt and the cream headscarf.", REF("tiger") + [RAW_C + "ref_sm_tiger_dg.png"])
# v1 of cast_sm_tiger_sneak (2026-11-22) drew rainbow sleeves and a blue ribbon (not the disguise figures' clothes):
# kept as cast_sm_tiger_sneak_v1.png, regenerated with the disguise figure as the second reference

# ---------------------------------------------------------------- the sun and the moon (sky characters)
SM_SKY = ("STYLE: " + FELT + "NO plants, NO leaves, NO flowers, NO green anywhere. Matte, no gloss. " + COLOUR)
JOBS.append({"id": "cast_sm_sunmoon", "kind": "bg", "refs": REF("boy") + REF("girl"), "aspect": WIDE,
             "out": RAW_C + "cast_sm_sunmoon.png",
             "prompt": "A SHEET of FOUR round sky-character cards for a children's pop-up storybook, " + BG + SM_SKY +
             "Left to right: (1) THE SUN with THE BROTHER's face: a big round golden-yellow felt sun disc with a ring of "
             "soft pointed orange-gold rays, in the middle the brother's round face and black bowl-cut hair (as in the "
             "reference) smiling warmly; (2) THE MOON with THE SISTER's face: a big round pale cream-lemon full moon disc "
             "with soft grey-blue crater spots and two tiny gold stars stuck on its rim, in the middle the sister's face "
             "with her two pigtail buns and coral ribbons, a sweet calm smile; (3) THE SUN with THE SISTER's face, "
             "beaming and proud; (4) THE MOON with THE BROTHER's face, a kind gentle smile, eyes soft. All four discs the "
             "same size, faces simple and sweet (dot eyes, coral-peach cheeks), the face filling about half the disc."})

# ---------------------------------------------------------------- sets and props (no character refs)
SM_BUILD = ("STYLE: " + FELT + "MATERIAL PRINTS ONLY (golden straw thatch strands with stitched rope bands, cream-ochre mud "
            "plaster with little straw flecks, brown wood grain, cream mulberry-paper lattice, grey stone), NO flowers, NO "
            "leaves, NO botanical motifs on buildings or objects. Matte, no gloss. " + COLOUR)
SM_NATURE = ("STYLE: " + FELT + "Korean folk-painting (minhwa) print detail is welcome on nature pieces: fan-shaped pine "
             "needle clusters, layered ridge stripes, stitched seams, stamped dots. Matte, no gloss. PALETTE: deep pine "
             "green, jade, blue-green and slate-blue mountains, ochre, rust-red autumn, cream, warm grey stone. " + COLOUR)


def sheet(jid, n, style, body, aspect=WIDE):
    JOBS.append({"id": jid, "kind": "bg", "refs": [], "aspect": aspect, "out": RAW_A + jid + ".png",
                 "prompt": f"A PROP SHEET for a children's pop-up storybook: {n} separate die-cut stand-up cardboard pieces, "
                 "every piece standing on a flat bottom edge (the hinge), " + BG + style + body})


sheet("story_sm_cottage", "EIGHT", SM_BUILD,
      "A small Korean THATCHED COTTAGE (choga-jip) and its parts, all drawn straight on (front elevation, no perspective): "
      "(1) THE COTTAGE FRONT: a wide low house front, a thick rounded golden STRAW THATCH roof with stitched rope bands "
      "across it, cream-ochre mud-plaster walls between brown wooden posts, a low grey stone foundation with ONE flat "
      "stone step in the middle; in the middle a CLOSED wooden lattice DOOR covered with cream mulberry paper (a square "
      "lattice of thin wooden bars, a little round iron ring handle); to the RIGHT of the door one square paper-screen "
      "WINDOW (lattice + cream paper, glowing a little warm); a narrow wooden veranda board (toenmaru) along the bottom "
      "of the wall; (2) THE SAME DOOR alone (the lattice paper door leaf, same size as in the front); (3) THE SAME WINDOW "
      "alone; (4) THE SAME WINDOW with a small round POKED HOLE in the paper; (5) THE COTTAGE SIDE / GABLE END: a narrow "
      "mud-plaster side wall with the thatch roof's rounded end overhanging it; (6) THE COTTAGE BACK: the back wall of "
      "the same house with a small plain wooden BACK DOOR at the left; (7) the inside back wall of the room: a "
      "cream-papered wall with a wooden shelf and a folded quilt; (8) a small brass OIL LAMP (deungjan) on a tall wooden "
      "stand with a tiny warm flame.")
sheet("story_sm_yard", "TEN", SM_BUILD,
      "Yard objects of a Korean thatched cottage: (1) an OPEN STONE WELL: a round wall of grey fieldstones about knee high "
      "with a dark open top (dark water inside, a tiny cream reflection), a wooden frame over it with a crossbar and a "
      "coil of straw rope hanging down to a wooden BUCKET (durebak) resting on the rim; (2) the wooden well BUCKET alone, "
      "with a rope handle; (3) a JAR TERRACE (jangdokdae): a low stone platform with THREE big brown earthenware "
      "fermentation JARS (onggi) with lids, the biggest one as tall as a child (a child could hide behind it); (4) ONE BIG "
      "brown onggi jar with a lid, alone; (5) a small brown SESAME-OIL BOTTLE with a twisted straw stopper; (6) a small "
      "wood AXE with a brown handle; (7) a low brushwood FENCE section (woven twigs, tied); (8) a stack of FIREWOOD "
      "bundles; (9) a straw MAT rolled up; (10) a wooden A-frame carrier (jige) leaning.")
sheet("story_sm_tree", "SIX", SM_NATURE,
      "Pieces of ONE big old Korean zelkova tree (neutinamu) by a well, drawn straight on: (1) THE WHOLE BIG TREE, very "
      "TALL (fill the image height): a thick straight brown TRUNK with bark ridges and a few knots rising from wide roots, "
      "splitting near the top into a broad FORK of two strong branches where two small children could sit, and a wide "
      "rounded crown of dark-green leaf clumps (stitched leaf print) above and to the sides; the trunk is clearly visible "
      "from the roots to the fork (no leaves covering it); (2) the same TRUNK alone (roots to fork, no crown), same width; "
      "(3) the CROWN alone (leaf clumps with the fork branches); (4) a shiny wet STREAK of sesame oil (a glossy golden "
      "drip shape) to lay on a trunk; (5) three small AXE NOTCH marks (pale wood chips) in a vertical row; (6) a single "
      "stout side BRANCH with leaves.", aspect=LAND)
sheet("story_sm_mountain", "TEN", SM_NATURE,
      "Korean mountain-pass scenery for a winding mountain road (gogae), all pieces standing: (1)-(4) FOUR different big "
      "layered MOUNTAIN RIDGE cards (wide, two or three overlapping peaks each, jade green / blue-green / slate blue, "
      "stitched ridge lines, a few fan-shaped pine clusters printed on the slopes; one has a notch-shaped saddle in the "
      "middle where a road would cross); (5) a BIG round grey BOULDER as tall as a grown-up with moss dots (something "
      "could hide behind it); (6) a cluster of three smaller rocks; (7) a SEONANGDANG: a cone-shaped pile of stacked grey "
      "stones at a mountain pass with a small tree beside it hung with cream and indigo cloth strips; (8) a clump of "
      "silver-cream PAMPAS GRASS (eoksae) plumes; (9) a red-orange autumn MAPLE bush; (10) a gnarled small PINE on a rock "
      "ledge.")
sheet("story_sm_village", "EIGHT", SM_BUILD,
      "A rich family's house yard in old Korea and its kitchen things, drawn straight on: (1) a TILE-ROOFED HANOK gate "
      "house front: dark grey curved tile roof, cream walls, a big double wooden GATE in the middle (closed); (2) an "
      "outdoor clay STOVE (agungi) with a big black iron cauldron (gamasot) on it and a fire mouth below; (3) a brown "
      "earthenware rice-cake STEAMER (siru) on a stand with soft white steam curls on top; (4) a big round wooden TRAY "
      "heaped with round white and soft-green rice cakes (tteok); (5) a round woven straw BASKET heaped with rice cakes "
      "under a cream cloth; (6) the same round straw BASKET EMPTY; (7) ONE round white rice cake (a plump flat round "
      "tteok); (8) a wide wooden basin of white rice.")
sheet("story_sm_sky", "TEN", SM_SKY,
      "Sky pieces: (1) THE GOOD ROPE: a long VERTICAL thick golden rope (dongajul) of tightly twisted golden straw, fresh "
      "and shining (a few stitched sparkle dots on it), filling most of the image height; (2) THE OLD ROPE: a long "
      "VERTICAL thin grey-brown rope, frayed, with a worn thin spot and loose fibres sticking out, filling most of the "
      "image height; (3) a SNAPPED rope end (frayed); (4)-(6) THREE wide soft CLOUD bands (cream, pale lemon, pale "
      "blue-grey), scalloped edges with stitched seams; (7) a puffy round cloud; (8) a plain round golden SUN disc with "
      "soft rays (no face); (9) a plain cream FULL MOON disc (no face); (10) a gold five-point STAR.", aspect=LAND)
sheet("story_sm_field", "EIGHT", SM_NATURE,
      "A sorghum field (susu-bat) and night garden: (1)-(3) THREE tall SORGHUM stalk clumps (tall slim green-ochre stalks "
      "with long leaves and heavy drooping RUST-RED grain heads on top), each a bit different; (4) a wide low band of "
      "sorghum field (a row of stalks); (5) a clump of autumn chrysanthemum-like wild grass (cream and ochre, no pink); (6) "
      "a small persimmon sapling; (7) a dark low bush; (8) a clump of reeds.")

# phase 1 round 4 (prototype review): the room is seen from inside (the poked window, the paw at the door), so the
# front wall needs its inside face, and the room a floor (the felt showed through)
JOBS.append({"id": "story_sm_cottage_in", "kind": "bg", "refs": [RAW_A + "story_sm_cottage.png"], "aspect": WIDE,
             "out": RAW_A + "story_sm_cottage_in.png",
             "prompt": "A PROP SHEET for a children's pop-up storybook: THREE separate die-cut cardboard pieces, " + BG +
             SM_BUILD + "They belong to the thatched cottage in the reference image. (1) THE INSIDE FACE OF THE COTTAGE'S "
             "FRONT WALL, seen from inside the room, straight on, MIRRORED left-right compared with the outside (so the "
             "paper-screen WINDOW is on the LEFT and the lattice paper DOOR right of the middle): cream papered plaster "
             "wall between brown wooden posts and a low beam along the top (no roof, the wall ends at the beam), the "
             "lattice door and the square lattice window with cream mulberry paper lit softly from outside by cool "
             "moonlight (pale blue-cream glow in the paper squares), a straight floor line along the bottom; the same "
             "width-to-height proportion as the outside wall (wide, low); (2) a flat FLOOR card: a wide rectangle of "
             "glossy warm yellow-ochre oiled-paper ondol floor (jangpanji) in large square sheets with soft seams, seen "
             "straight on from above; (3) a small low wooden table (soban) with one round lid bowl."})


# ---------------------------------------------------------------- 2026-11-22 PAPER look (user: "펠트 질감 싫은뎅", "다시 그려보자")
# No felt anywhere: ground, set cards and characters are matte cut paper; no wool fuzz, no stitch lines. Test card
# first (one ridge + one rock + one bush; the mother, the tiger and the sister calm), then the full redraw after OK.
PAPER = ("STYLE (same for every piece): flat orthographic view, a die-cut pop-up book piece made of MATTE CUT PAPER and "
         "thin cardstock: every colour area is a separate cut or torn sheet of coloured paper glued in layers (a lighter "
         "or darker paper layer on top for shading and detail), crisp cut edges or softly torn deckled edges, each layer "
         "edge with a thin darker cut line and a faint lighter rim on its upper-left (lit) side, fine paper-fibre grain "
         "like Korean hanji / mulberry paper, matte, no gloss. ABSOLUTELY NO felt, NO wool, NO fuzz, NO fabric or "
         "knitted texture, NO stitches, NO dashed stitch lines, NO sewing seams, NO embroidery. Details are small cut "
         "paper shapes or a printed line, never stitching. Warm Korean folk-tale picture book for ages 3-7. " + COLOUR)
PAPER_CHAR = PAPER + ("Characters keep EXACTLY the reference design (face, hair, clothes, colours, proportions); only the "
                      "material changes from felt to cut paper: hanbok panels as cut paper pieces, trims and ribbons as "
                      "thin paper strips, fur stripes as cut paper shapes, faces simple and sweet. ")
JOBS.append({"id": "story_sm_paper_test", "kind": "bg", "refs": [RAW_A + "story_sm_mountain.png"],
             "aspect": "landscape, any size the tool returns is fine (save it as-is)",
             "out": RAW_A + "story_sm_paper_test.png",
             "prompt": "A PROP SHEET for a children's pop-up storybook: THREE separate die-cut stand-up pieces, every "
             "piece standing on a flat bottom edge (the hinge), " + BG + PAPER + "The reference shows the same pieces in an "
             "older FELT look: keep their shapes and colours but make them PAPER. (1) a big layered MOUNTAIN RIDGE card: "
             "two or three overlapping peaks, each peak a separate layer of jade green / blue-green / slate-blue paper "
             "with torn top edges, a few fan-shaped pine clusters cut from dark green paper on the slopes, thin "
             "lighter-paper ridge lines (no dashes, no stitching); (2) a big round grey BOULDER cut from layered grey "
             "papers with a few moss-green paper flecks and a darker paper crack; (3) a red-orange autumn MAPLE bush cut "
             "from several layers of red, orange and rust paper leaves."})
for _role, _who, _pose in (("mom", MOM, "standing calmly, a calm gentle smile, holding the round straw basket of rice "
                            "cakes in both hands in front of her apron"),
                           ("tiger", TIGER, "standing upright on his hind legs, front paws resting on his round belly, "
                            "tail curling out to one side without closing the leg gap, a sly little grin"),
                           ("girl", GIRL, "standing calmly, arms relaxed a little away from the body, a sweet calm "
                            "smile")):
    JOBS.append({"id": f"cast_sm_paper_{_role}", "kind": "bg", "refs": REF(_role), "aspect": "portrait or square, any size the tool returns is fine (save it as-is)",
                 "out": RAW_C + f"cast_sm_paper_{_role}.png",
                 "prompt": "A CHARACTER CARD for a children's pop-up storybook: ONE full-body die-cut stand-up figure, "
                 "centred, feet on a horizontal baseline near the bottom, " + BG + PAPER_CHAR + _who + FACE + LEGS +
                 REF_LINE + "FRONT figure facing the viewer: " + _pose + "."})

# the scenery redraw in paper (after the test card read as paper): every set sheet redrawn PIECE FOR PIECE from its felt
# sheet (same layout, count, positions, shapes, colours), so the labels and card ids carry over; felt raws kept
for _sh in ["story_sm_mountain", "story_sm_tree", "story_sm_field", "story_sm_sky", "story_sm_yard", "story_sm_village",
            "story_sm_cottage", "story_sm_cottage_in"]:
    JOBS.append({"id": _sh + "_paper", "kind": "bg", "refs": [RAW_A + _sh + ".png"],
                 "aspect": "the SAME size and orientation as the reference image (save it as-is)",
                 "out": RAW_A + _sh + "_paper.png",
                 "prompt": "REDRAW the reference prop sheet for a children's pop-up storybook PIECE FOR PIECE: the SAME "
                 "number of pieces in the SAME positions, the same shapes, silhouettes, proportions and colours, the "
                 "same objects; ONLY the material changes: " + BG + PAPER + "Buildings and objects keep their own "
                 "material read in paper form (thatch as layered cut straw-paper strips, plaster as cream paper, wood "
                 "grain as cut brown paper strips, lattice as thin cut paper bars, stone as grey paper pieces, rope as "
                 "twisted paper cord); clouds as layered cut paper with NO dashed lines; plants as cut paper leaves."})

# the full cast in paper (user OK 2026-11-22: "다 종이로 변경"): every cast sheet redrawn PIECE FOR PIECE from its felt
# sheet (same figures, order, poses, sizes, facing, leg gaps) with the approved paper test figure as the MATERIAL ref
_PAPER_REF = {"boy": "cast_sm_paper_girl", "girl": "cast_sm_paper_girl", "mom": "cast_sm_paper_mom",
              "rich": "cast_sm_paper_mom", "tiger": "cast_sm_paper_tiger"}
_CAST_SHEETS = {"cast_sm_lineup": "mom", "cast_sm_boy_expr": "boy", "cast_sm_girl_expr": "girl",
                "cast_sm_kids_views": "girl", "cast_sm_mom_expr": "mom", "cast_sm_mom_views": "mom",
                "cast_sm_tiger_expr_a": "tiger", "cast_sm_tiger_expr_b": "tiger", "cast_sm_tiger_disguise": "tiger",
                "cast_sm_tiger_tree": "tiger", "cast_sm_tiger_rope": "tiger", "cast_sm_climb": "girl",
                "cast_sm_treetop": "girl", "cast_sm_rich_expr": "rich", "cast_sm_sunmoon": "girl",
                "cast_sm_boy_walk": "boy", "cast_sm_girl_walk": "girl", "cast_sm_boy_run": "boy",
                "cast_sm_girl_run": "girl", "cast_sm_mom_walk": "mom", "cast_sm_tiger_walk": "tiger",
                "cast_sm_tiger_sneak": "tiger"}
for _sh, _who in _CAST_SHEETS.items():
    JOBS.append({"id": _sh + "_paper", "kind": "bg",
                 "refs": [RAW_C + _sh + "_felt.png", RAW_C + _PAPER_REF[_who] + ".png"],
                 "aspect": WIDE,
                 "out": RAW_C + _sh + "_paper.png",
                 "prompt": "REDRAW the FIRST reference image (a character sheet for a children's pop-up storybook) "
                 "PIECE FOR PIECE: the SAME number of separate figures in the SAME order left to right, the same poses, "
                 "expressions, facing, sizes, positions and proportions, the same clothes, colours and faces, the same "
                 "open gap between the legs, every figure still fully separate. ONLY the MATERIAL changes, to match "
                 "the SECOND reference image (the same characters' approved paper look): " + BG + PAPER_CHAR +
                 "Do not add or remove any figure; do not add any background element."})

# v2 (2026-11-22): the paper redraw filled the mother's basket on her before-work figures (calm, wave, talk): she
# leaves for work with an EMPTY basket and gets the rice cakes only at the rich house
JOBS.append({"id": "cast_sm_mom_empty_paper", "kind": "bg",
             "refs": [RAW_C + "cast_sm_paper_mom.png", RAW_C + "cast_sm_mom_expr_felt.png"],
             "aspect": "wide landscape, any size the tool returns is fine (save it as-is)",
             "out": RAW_C + "cast_sm_mom_empty_paper.png",
             "prompt": "A CHARACTER SHEET for a children's pop-up storybook: THREE separate full-body die-cut stand-up "
             "figures in one horizontal row, " + BG + PAPER_CHAR + MOM + FACE + LEGS + REF_LINE + FRONT + ROW +
             "The FIRST reference is her approved paper look (copy it exactly, but her basket must be EMPTY). Left to "
             "right: (1) CALM: holding the round woven straw basket in both hands in front of her apron, the basket "
             "COMPLETELY EMPTY (no rice cakes, no cloth, you can see the empty woven inside), a calm gentle smile; (2) "
             "WAVE GOODBYE: one hand waving high, the EMPTY basket hooked on the other arm, a warm smile; (3) TALKING "
             "KINDLY: one index finger raised as she reminds the children, the EMPTY basket on her arm, a loving face. "
             "NO rice cakes anywhere on this sheet."})
JOBS.append({"id": "story_sm_door_fx", "kind": "bg", "refs": [RAW_C + "cast_sm_paper_tiger.png"],
             "aspect": "landscape, any size the tool returns is fine (save it as-is)",
             "out": RAW_A + "story_sm_door_fx.png",
             "prompt": "A PROP SHEET for a children's pop-up storybook: THREE separate die-cut pieces, " + BG + PAPER +
             "They belong to the cute children's-book tiger in the reference (same orange paper, same brown stripes). "
             "(1) THE TIGER'S PAW reaching in sideways from the RIGHT (a forearm and a big round paw, horizontal), the "
             "paw dusted with patchy WHITE FLOUR (white paper flecks) but still orange underneath, three small curved "
             "cream CLAWS just peeking out (cute, not scary); (2) THE TIGER'S EYE close up as seen through a round hole: "
             "a round patch of orange fur with one big round friendly eye (dark brown iris, a white shine dot), a "
             "brown stripe above it, a soft circular edge; (3) the same eye patch with the eye CLOSED in a blink (a "
             "curved line with lashes)."})

# v5: the tiger runs away with his bump: a drawn run cycle (the run-away fell back to his plain walk, bump gone)
JOBS.append({"id": "cast_sm_tiger_bump_run", "kind": "bg",
             "refs": [RAW_C + "cast_sm_paper_tiger.png", RAW_C + "cast_sm_tiger_rope.png"], "aspect": WIDE,
             "out": RAW_C + "cast_sm_tiger_bump_run.png",
             "prompt": "A CHARACTER SHEET for a children's pop-up storybook: FOUR full-body die-cut figures in one "
             "horizontal row, " + BG + PAPER_CHAR + TIGER + FACE + LEGS + REF_LINE +
             "The FIRST reference is his approved paper look; the SECOND shows the pose (the last figure: running away "
             "with a bump). RUN CYCLE: FOUR SIDE-PROFILE frames facing RIGHT of one run cycle in order (CONTACT, DOWN, "
             "PASSING, FLIGHT with both feet off the ground), the tiger running away upright with a big round orange "
             "BUMP on top of his head, comic teary eyes, mouth open 'ouch', arms pumping, legs wide apart with an open "
             "magenta gap, the same size in every frame, the lowest foot on one baseline."})

# v7 (2026-11-22): the morning walk needs an EMPTY basket (the paper walk cycle carries rice cakes); the golden rope
# of the finale should be a straw rope like the old rope card (the first read as a candy-striped twist)
JOBS.append({"id": "cast_sm_mom_walk_empty", "kind": "bg",
             "refs": [RAW_C + "cast_sm_mom_walk.png", RAW_C + "cast_sm_mom_empty_paper.png"], "aspect": WIDE,
             "out": RAW_C + "cast_sm_mom_walk_empty.png",
             "prompt": "REDRAW the FIRST reference image (the mother's walk cycle for a children's pop-up storybook) "
             "PIECE FOR PIECE: the SAME EIGHT figures in the SAME order (four side frames facing right, two back "
             "frames, two front frames), the same poses, sizes and leg gaps, the same cut-paper look; the ONLY change: "
             "her round straw basket is EMPTY in every frame (no rice cakes, no cloth; the empty woven inside shows), "
             "like the SECOND reference. " + BG + PAPER_CHAR + "Do not add or remove any figure."})
JOBS.append({"id": "story_sm_rope_paper", "kind": "bg", "refs": [RAW_A + "story_sm_sky.png"],
             "aspect": "landscape, any size the tool returns is fine (save it as-is)",
             "out": RAW_A + "story_sm_rope_paper.png",
             "prompt": "A PROP SHEET for a children's pop-up storybook: TWO separate die-cut pieces, " + BG + PAPER +
             "(1) THE GOOD ROPE FROM THE SKY: a long VERTICAL thick NEW straw rope (dongajul) of tightly twisted "
             "golden-straw strands, drawn in the same cut-paper style as the thin old grey-brown rope in the reference "
             "(the second rope from the left) but thick, strong, fresh and warm golden, no stripes, no candy twist, a "
             "few tiny gold paper sparkle flecks, filling most of the image height; (2) a short frayed straw end of the "
             "same golden rope."})


if __name__ == "__main__":
    out = os.path.join(HERE, "sunmoon_jobs.json")
    json.dump(JOBS, open(out, "w"), ensure_ascii=False, indent=1)
    print("wrote", out, len(JOBS), "jobs:", " ".join(j["id"] for j in JOBS))
