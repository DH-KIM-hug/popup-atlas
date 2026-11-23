#!/usr/bin/env python3
"""「라푼젤」 (rapunzel) sounds -> game/audio/sound_catalog.json, MERGE-ONLY (2026-11-23).

Copies 톡톡 동화극장's rapunzel sounds (READ-ONLY source, credits in its sounds/CREDITS.md, repeated in
game/audio/music/CREDITS.md) into game/audio/sfx|music, music loudness-matched to -22 LUFS, then re-reads the shared
catalog right before writing and only adds / replaces the rp.* sounds and the two music ids below.
"""
import json, os, shutil, subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAT = os.path.join(ROOT, "game", "audio", "sound_catalog.json")
SRC = "/Users/house_of_4k2b/projects/2026/patjuk-game/sounds/"


def sfx(f, db, note, pos=False, pitch=0.04):
    return {"files": [f"res://audio/sfx/{f}"], "bus": "SFX", "gain_db": db, "pitch_rand": pitch, "vol_rand_db": 1,
            "no_repeat": False, "positional": pos, "loop": False, "note": "rapunzel: 톡톡 " + note}


COPY = {"rp_creak.mp3": "sfx/creak.mp3", "rp_pull.mp3": "sfx/pull_pop_2.mp3", "rp_magic.mp3": "sfx/magic_wand.mp3",
        "rp_knock.mp3": "sfx/knock_2.mp3", "rp_rise.mp3": "sfx/chime_up.mp3", "rp_slide.mp3": "sfx/slide_down.mp3",
        "rp_harp.mp3": "sfx/harp_gliss.mp3", "rp_snip.mp3": "sfx/el_scissor_snip.mp3", "rp_whoosh.mp3": "sfx/wind_gust.mp3",
        "rp_petals.mp3": "sfx/sparkle.mp3"}
SOUNDS = {
    "rp.creak": sfx("rp_creak.mp3", -10, "sfx/creak.mp3 (Pixabay 'Old Wooden Door', Universfield): the garden gate", True),
    "rp.pull": sfx("rp_pull.mp3", -8, "sfx/pull_pop_2.mp3 (Pixabay 'Cartoon Yoink 1', floraphonic): the rampion comes up"),
    "rp.magic": sfx("rp_magic.mp3", -9, "sfx/magic_wand.mp3: the witch appears / vanishes"),
    "rp.knock": sfx("rp_knock.mp3", -8, "sfx/knock_2.mp3 (ElevenLabs SFX made for 톡톡): the stick's 톡"),
    "rp.rise": sfx("rp_rise.mp3", -8, "sfx/chime_up.mp3 (Pixabay 'Fairy Dust Shimmer 1', floraphonic): the tower rises", pitch=0.0),
    "rp.slide": sfx("rp_slide.mp3", -10, "sfx/slide_down.mp3 (synthesised slide whistle, CC0): the braid 스르르"),
    "rp.harp": sfx("rp_harp.mp3", -12, "sfx/harp_gliss.mp3 (Pixabay 'Harp Glissando Up C7 1', floraphonic): the song's notes"),
    "rp.snip": sfx("rp_snip.mp3", -9, "sfx/el_scissor_snip.mp3 (ElevenLabs SFX made for 톡톡): 싹둑", pitch=0.0),
    "rp.whoosh": sfx("rp_whoosh.mp3", -10, "sfx/wind_gust.mp3: the soft magic wind"),
    "rp.petals": sfx("rp_petals.mp3", -10, "sfx/sparkle.mp3 (Pixabay 'Magic Twinkle', Universfield): petals at the reunion"),
}
MUSIC = {
    "rapunzel": {"file": "res://audio/music/music_rapunzel_1.mp3", "bus": "Music", "gain_db": 0, "loop": True,
                 "fade_in": 2.0, "fade_out": 2.0,
                 "note": "톡톡's rapunzel music (music/el_rapunzel_bgm.mp3, Eleven Music made for 톡톡: forest tower, lute / "
                         "harp / recorder / strings, 76 BPM), -22 LUFS"},
    "rp_song": {"file": "res://audio/music/rp_song_1.mp3", "bus": "Music", "gain_db": 0, "loop": True,
                "fade_in": 1.5, "fade_out": 2.0,
                "note": "톡톡's 'song over the wood' (sfx/classical_songs_without_words.mp3: Mendelssohn, Songs without "
                        "Words op. 19, piano, abydos_music on Pixabay, Pixabay Content License; first 18 s), -22 LUFS"},
}

if __name__ == "__main__":
    for dst, src in COPY.items():
        shutil.copyfile(SRC + src, os.path.join(ROOT, "game/audio/sfx", dst))
    for dst, src in {"music_rapunzel_1.mp3": "music/el_rapunzel_bgm.mp3",
                     "rp_song_1.mp3": "sfx/classical_songs_without_words.mp3"}.items():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", SRC + src, "-af", "loudnorm=I=-22:TP=-2:LRA=11",
                        "-ar", "44100", "-b:a", "128k", os.path.join(ROOT, "game/audio/music", dst)], check=True)
    d = json.load(open(CAT, encoding="utf-8"))
    d["sounds"].update(SOUNDS)
    d["music"].update(MUSIC)
    json.dump(d, open(CAT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("merged", len(SOUNDS), "sounds,", len(MUSIC), "music into", CAT)
