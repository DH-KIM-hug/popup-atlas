#!/usr/bin/env python3
"""「커다란 순무」 (turnip) sounds -> game/audio/sound_catalog.json, MERGE-ONLY (2026-11-23).

Re-reads the shared catalog right before writing and only adds / replaces the tn.* sounds and the three music ids
below (other agents write this catalog too). Files were copied from 톡톡 동화극장 (sounds/, credits in that project's
sounds/CREDITS.md and game/audio/music/CREDITS.md): sfx unchanged, music loudness-matched to -22 LUFS.
"""
import json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAT = os.path.join(ROOT, "game", "audio", "sound_catalog.json")


def sfx(f, db, note, pos=False, pitch=0.04):
    return {"files": [f"res://audio/sfx/{f}"], "bus": "SFX", "gain_db": db, "pitch_rand": pitch, "vol_rand_db": 1,
            "no_repeat": False, "positional": pos, "loop": False, "note": "turnip: 톡톡 " + note}


SOUNDS = {
    "tn.pop": sfx("tn_pop.mp3", -6, "sfx/el_turnip_pop.mp3 (ElevenLabs SFX made for 톡톡): the turnip comes out", pitch=0.0),
    "tn.strain": sfx("tn_strain.mp3", -9, "sfx/el_pull_strain.mp3 (ElevenLabs SFX made for 톡톡): a heave"),
    "tn.squeak": sfx("tn_squeak.mp3", -8, "sfx/mouse_squeak_1.mp3 (Pixabay 'Mouse Squeak', TanwerAman)"),
    "tn.bark": sfx("tn_bark.mp3", -9, "animals/dog_3.mp3 (Pixabay 'Friendly Small dog bark (1)', Yodguard)", True),
    "tn.meow": sfx("tn_meow.mp3", -8, "animals/cat_2.mp3 (Pixabay 'Cat Meow', SOUND_GARAGE)", True),
    "tn.water": sfx("tn_water.mp3", -10, "sfx/water_pour_1.mp3 (Pixabay 'Pouring Water', Universfield)"),
    "tn.dig": sfx("tn_dig.mp3", -8, "sfx/dig_soil_1.mp3 (Pixabay 'Digging with shovel', freesound_community)"),
    "tn.rustle": sfx("tn_rustle.mp3", -8, "sfx/rustle_1.mp3 (Pixabay 'Bush Rustle', freesound_community)", True),
    "tn.sun": sfx("tn_sun.mp3", -10, "sfx/el_sun_warm.mp3 (ElevenLabs SFX made for 톡톡)", pitch=0.0),
    "tn.grow": sfx("tn_grow.mp3", -10, "sfx/chime_up.mp3 (Pixabay 'Fairy Dust Shimmer 1', floraphonic)"),
    "tn.slurp": sfx("tn_slurp.mp3", -9, "sfx/slurp_1.mp3 (Pixabay 'Cartoon Slurp', freesound_community)"),
    "tn.cheer": sfx("tn_cheer.mp3", -12, "sfx/cheer.mp3 (Pixabay 'Applause, small audience', freesound_community)"),
}
MUSIC = {
    "intro_cozy2": {"file": "res://audio/music/intro_cozy2_1.mp3", "bus": "Music", "gain_db": 0, "loop": False,
                    "fade_in": 0.2, "fade_out": 2.0, "hold": True,
                    "note": "story-start music from 톡톡 동화극장 (sfx/intro_cozy2.mp3, Pixabay 'Light from the Hallway "
                            "(Mbira Lullaby)', KonstantinPazuzuStudio, Pixabay Content License); turnip's intro in 톡톡; "
                            "plays once when the book opens, beat music waits for it"},
    "turnip": {"file": "res://audio/music/music_turnip_1.mp3", "bus": "Music", "gain_db": 0, "loop": True,
               "fade_in": 2.0, "fade_out": 2.0,
               "note": "톡톡's turnip music (music/el_turnip_bgm.mp3, Eleven Music made for 톡톡: Russian village folk, "
                       "balalaika / button accordion / domra / tambourine, 96 BPM), -22 LUFS"},
    "finale_happy": {"file": "res://audio/music/finale_happy_1.mp3", "bus": "Music", "gain_db": 0, "loop": False,
                     "fade_in": 0.2, "fade_out": 2.0,
                     "note": "톡톡's finale music (sfx/finale_happy.mp3, Pixabay 'Happy Kids', HitsLab), the feast"},
}

if __name__ == "__main__":
    d = json.load(open(CAT, encoding="utf-8"))
    d["sounds"].update(SOUNDS)
    d["music"].update(MUSIC)
    json.dump(d, open(CAT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("merged", len(SOUNDS), "sounds,", len(MUSIC), "music into", CAT)
