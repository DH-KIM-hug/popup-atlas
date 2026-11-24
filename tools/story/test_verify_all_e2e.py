#!/usr/bin/env python3
"""Comprehensive unit tests for tools/story/verify_all_e2e.py using isolated temp fixtures."""
from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

_TOOLS_STORY = Path(__file__).resolve().parent
if str(_TOOLS_STORY) not in sys.path:
    sys.path.insert(0, str(_TOOLS_STORY))

import verify_all_e2e as e2e  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _replace_run_header(md_text: str, rid: str) -> str:
    return re.sub(r"^run:\s*.+$", f"run: {rid}", md_text, count=1, flags=re.M)


def _write_rgba_webp(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr.astype(np.uint8), mode="RGBA").save(path, "WEBP", lossless=True)


def _make_clean_sprite(path: Path, size: int = 32, interior_rgb: tuple[int, int, int] = (140, 70, 175)) -> None:
    """Create a sprite with an opaque purple costume interior & non-magenta border (0 detB)."""
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    # Dark charcoal outline border + purple interior
    arr[4 : size - 4, 4 : size - 4] = [40, 35, 45, 255]
    arr[6 : size - 6, 6 : size - 6] = [interior_rgb[0], interior_rgb[1], interior_rgb[2], 255]
    _write_rgba_webp(path, arr)


def _make_magenta_rim_sprite(path: Path, size: int = 32) -> None:
    """Create a sprite with bright magenta chroma-key pixels along its 1px silhouette."""
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[4 : size - 4, 4 : size - 4] = [245, 110, 240, 255]
    arr[6 : size - 6, 6 : size - 6] = [200, 130, 80, 255]
    _write_rgba_webp(path, arr)


def _build_minimal_repo(tmp: Path, tale: str = "turnip") -> dict[str, Any]:
    """Build a minimal isolated repo layout under `tmp` that passes Tiers 1-4 for `tale`."""
    # 1. Shared runtime GDScript guards
    (tmp / "game/story").mkdir(parents=True, exist_ok=True)
    (tmp / "game/core/look").mkdir(parents=True, exist_ok=True)
    (tmp / "game/story/story_runner.gd").write_text(
        "func _frame() -> float:\n\tif not is_inside_tree():\n\t\treturn 0.0\n\tawait get_tree().process_frame\n\treturn 0.0\n",
        encoding="utf-8",
    )
    (tmp / "game/story/spread_stage.gd").write_text(
        "static func _sky_texture(top: Color, hor: Color) -> Texture2D:\n\tvar w := 1024\n\tvar h := 320\n\treturn null\n",
        encoding="utf-8",
    )
    (tmp / "game/core/look/ground_layers.gd").write_text(
        '@export var ground_style := "paper"\n',
        encoding="utf-8",
    )

    # 2. Shared atlas _slices.json + catalog.json + bodies.json + kit.json + house_bodies.py
    for sheet in e2e.SHARED_ATLAS_SHEETS:
        sdir = tmp / "game/art/atlas" / sheet
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "_slices.json").write_text(json.dumps({"source": f"{sheet}_paper.png"}), encoding="utf-8")

    house_card = "village_houses_04"
    _make_clean_sprite(tmp / "game/art/atlas/village_houses/village_houses_04.webp")
    _make_clean_sprite(tmp / "game/art/atlas/village_houses/bodies/village_houses_04_side.webp")
    _make_clean_sprite(tmp / "game/art/atlas/village_houses/bodies/village_houses_04_back.webp")
    _make_clean_sprite(tmp / "game/art/atlas/village_houses/bodies/village_houses_04_roof.webp")
    _make_clean_sprite(tmp / "game/art/buildings/tiles/terracotta.webp")

    (tmp / "game/art/atlas/catalog.json").write_text(
        json.dumps([{"id": house_card, "path": "art/atlas/village_houses/village_houses_04.webp"}]),
        encoding="utf-8",
    )
    (tmp / "game/art/atlas/bodies.json").write_text(
        json.dumps(
            {
                house_card: {
                    "mats": [1, 2, 1],
                    "wall_lines": [[15.0, 0.0], [220.0, 0.0]],
                    "side_file": "art/atlas/village_houses/bodies/village_houses_04_side.webp",
                    "back_file": "art/atlas/village_houses/bodies/village_houses_04_back.webp",
                    "roof_file": "art/atlas/village_houses/bodies/village_houses_04_roof.webp",
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp / "game/art/buildings/kit.json").write_text(
        json.dumps({"materials": {"terracotta": {}}, "kit": {"rapunzel_tower": {"parts": [{"mat": "terracotta"}]}}}),
        encoding="utf-8",
    )
    (tmp / "tools/atlas").mkdir(parents=True, exist_ok=True)
    (tmp / "tools/atlas/house_bodies.py").write_text(
        'OVERRIDE = {\n    "village_houses_01": {"roof_mat": "terracotta"},\n}\n',
        encoding="utf-8",
    )

    # 3. house_orbit_all.sh covering all 8 tales
    (tmp / "tools/story").mkdir(parents=True, exist_ok=True)
    cases = "\n".join(f"  {t}) echo {t} ;;" for t in e2e.TALES)
    orbit_sh = tmp / "tools/story/house_orbit_all.sh"
    orbit_sh.write_text(
        f'#!/bin/sh\nTALES="${{*:-{" ".join(e2e.TALES)}}}"\nfor T in $TALES; do\ncase $T in\n{cases}\nesac\ndone\n',
        encoding="utf-8",
    )
    orbit_sh.chmod(0o755)

    # Copy real check_lines.py so Tier 3 runs actual check_lines.py against the temp fixture
    (tmp / "tools/story/check_lines.py").write_text(
        (REPO_ROOT / "tools/story/check_lines.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    # 4. Cast catalog for `tale`
    cast_entries = []
    skins = list(e2e.REQUIRED_CAST_CYCLES.get(tale, {"farm_grandpa": ("walk_cycle", "walk_front", "walk_back")}).keys())
    for skin in skins:
        for cy in e2e.REQUIRED_CAST_CYCLES[tale][skin]:
            for fi in (0, 1):
                rel = f"art/cast/cast_{skin}_{cy}_{fi}.webp"
                _make_clean_sprite(tmp / "game" / rel)
                cast_entries.append({"skin": skin, "cycle": cy, "frame": fi, "path": rel})
    _make_clean_sprite(tmp / "game/art/cast/cast_tiger_slip.webp")
    (tmp / "game/art/cast/catalog.json").write_text(json.dumps(cast_entries), encoding="utf-8")

    # 5. Tale script.json + audio + recorded.json
    voice_dir = tmp / "game/audio/voice" / tale
    voice_dir.mkdir(parents=True, exist_ok=True)
    mp3_rel = f"audio/voice/{tale}/nar_001.mp3"
    (tmp / "game" / mp3_rel).write_bytes(b"ID3fake_mp3_data")
    rec_json = voice_dir / "recorded.json"
    rec_json.write_text(json.dumps({"nar||hello": "nar_001.mp3"}), encoding="utf-8")
    rec_sha = hashlib.sha256(rec_json.read_bytes()).hexdigest()

    cast_map = {}
    if tale == "turnip":
        cast_map = {
            "grandpa": {"kind": "actor", "skin": "farm_grandpa"},
            "grandma": {"kind": "actor", "skin": "farm_grandma"},
            "girl": {"kind": "actor", "skin": "farm_girl"},
            "dog": {"kind": "actor", "skin": "puppy"},
            "cat": {"kind": "actor", "skin": "tabby_cat"},
            "mouse": {"kind": "actor", "skin": "mouse"},
        }
    else:
        for idx, skin in enumerate(skins):
            cast_map[f"role_{idx}"] = {"kind": "actor", "skin": skin}

    script = {
        "tale_id": tale,
        "overlap_check": True,
        "spacing": True,
        "ground_style": "paper",
        "cast": cast_map,
        "beats": [
            {
                "id": "cover",
                "set": [{"card": house_card, "at": "home"}],
                "steps": [{"do": "say", "line": "l_001"}],
            },
            {
                "id": "end",
                "steps": [{"do": "say", "line": "l_002"}],
            },
        ],
        "lines": [
            {
                "id": "l_001",
                "text": "hello",
                "used": True,
                "segs": [{"speaker": "nar", "text": "hello", "status": "reuse", "audio": f"res://{mp3_rel}"}],
            },
            {
                "id": "l_002",
                "text": "bye",
                "used": True,
                "segs": [{"speaker": "nar", "text": "bye", "status": "changed-recorded", "audio": f"res://{mp3_rel}"}],
            },
        ],
    }
    story_dir = tmp / "game/stories" / tale
    story_dir.mkdir(parents=True, exist_ok=True)
    (story_dir / "script.json").write_text(json.dumps(script), encoding="utf-8")

    # 6. Tier 2 orbit audit fixture
    orbit_tale_dir = tmp / "artifacts/houses/e2e" / tale
    orbit_tale_dir.mkdir(parents=True, exist_ok=True)
    audit_data = {
        "house": {v: {"holes_px": 0, "house_px": 5000, "frac": 0.0} for v in e2e.ORBIT_VIEWS}
    }
    (orbit_tale_dir / f"{tale}_audit.json").write_text(json.dumps(audit_data), encoding="utf-8")
    (orbit_tale_dir / f"{tale}_audit.jpg").write_bytes(b"\xff\xd8\xff\xe0fakejpg")

    # 7. Tier 3 & 4 log, mp4, gate.md, motion_review.md
    art_dir = tmp / "artifacts" / tale
    (art_dir / "rec").mkdir(parents=True, exist_ok=True)
    (art_dir / "motion").mkdir(parents=True, exist_ok=True)
    (tmp / "artifacts/video").mkdir(parents=True, exist_ok=True)

    log_path = art_dir / "rec/e2e_v1.log"
    mp4_path = tmp / "artifacts/video" / f"{tale}_e2e_v1.mp4"
    mp4_path.write_bytes(b"fake_mp4")

    first_role = next(iter(cast_map))
    first_skin = cast_map[first_role]["skin"]
    track_lines = [
        f"TRACK {first_role} t={2.0 + i * 0.125:.2f} x={680.0 + i * 2.0:.1f} y=500.0 h=300.0 fig=walk_cycle view=side moving=1"
        for i in range(25)
    ]
    log_text = "\n".join(
        [
            f"STORY {tale} beats=2 lines=2 missing_audio=[] autoplay=true start=",
            "SEG l_001 0 t=1.0",
            f"MOVE 2.00 5.00 {first_role} walk walk_cycle 1.20 skin={first_skin} hgt=0.30 cyc=4.0 exp=4.4 vmax=0.50 dvmax=0.10 figs=walk_cycle:side:24 views=side:24",
            *track_lines,
            "SEG l_002 0 t=80.0",
            "OVERLAP_COUNT 0 OCCLUDE_COUNT 0 (last page 0 / 0)",
            "VOICE_DUP=0",
            "CAM_JUMP=0 CAM_JERK=0 SPEAKER_OFF=0",
            'STORY_DONE total=120.0 missing_audio=[] missing_sound=[] beats={"cover": 0.0, "zebra_mid": 40.0, "alpha_end": 80.0}',
            "ERROR: 2 resources still in use at exit (benign teardown)",
        ]
    ) + "\n"
    log_path.write_text(log_text, encoding="utf-8")
    rid = f"{log_path.name} {e2e._sha1_10(log_path)}"

    (art_dir / "gate_contact_01.jpg").write_bytes(b"\xff\xd8\xff\xe0sheet1")
    checklist_lines = "\n".join(f"- [x] {k}: verified ok" for k in e2e.VISUAL_KEYS)
    (art_dir / "gate.md").write_text(
        f"# Gate: {tale}\n\nrun: {rid}\nvideo: {mp4_path}\n\n"
        f"Contact sheets (every 2.5 s): gate_contact_01.jpg\n\n"
        f"## Visual checklist\n\n{checklist_lines}\n\n"
        f"## Accepted exceptions\n\n<!-- - <id>: <reason> -->\n",
        encoding="utf-8",
    )

    tile_name = f"01_{first_role}_2.0.jpg"
    (art_dir / "motion" / tile_name).write_bytes(b"\xff\xd8\xff\xe0tile1")
    (art_dir / "motion/motion_review.md").write_text(
        f"# Motion review: {tale}\n\nrun: {rid}\nvideo: {mp4_path} (offset 0.03 s)\n\n"
        "| # | t (story s) | actor | verb | cycle | dist | flags | tiles | verdict | note |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        f"| 01 | 2.00-5.00 | {first_role} | walk | walk_cycle | 1.20 (4.0 H) | - | {tile_name} | ok | clean side walk |\n",
        encoding="utf-8",
    )

    return {
        "baselines": {tale: {"sha256": rec_sha, "keys": 1}},
        "log_path": log_path,
        "mp4_path": mp4_path,
        "script": script,
        "rec_json": rec_json,
    }


class TestTier1(unittest.TestCase):
    def test_tier1_passes_on_valid_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            res = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0].status, "PASS", res[0].checks)

    def test_tier1_no_elevenlabs_rejects_needs_recording_and_unreferenced_mp3(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")

            # 1. Segment with changed-needs-recording must fail
            sc = json.loads((tmp / "game/stories/turnip/script.json").read_text())
            sc["lines"][0]["segs"][0]["status"] = "changed-needs-recording"
            (tmp / "game/stories/turnip/script.json").write_text(json.dumps(sc), encoding="utf-8")

            res = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            checks = {c.id: c for c in res.checks}
            self.assertEqual(checks["T1_AUDIO_INTEGRITY"].status, "FAIL")
            self.assertEqual(checks["T1_NO_ELEVENLABS"].status, "FAIL")

            # 2. Restore status, add unreferenced .mp3 -> fails T1_NO_ELEVENLABS
            sc["lines"][0]["segs"][0]["status"] = "reuse"
            (tmp / "game/stories/turnip/script.json").write_text(json.dumps(sc), encoding="utf-8")
            (tmp / "game/audio/voice/turnip/new_tts_clip.mp3").write_bytes(b"ID3new")
            res2 = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            checks2 = {c.id: c for c in res2.checks}
            self.assertEqual(checks2["T1_NO_ELEVENLABS"].status, "FAIL")

            # 3. Reference that clip via trimmed_from in script.json -> passes
            sc["lines"][1]["segs"][0]["audio"] = "res://audio/voice/turnip/new_tts_clip.mp3"
            sc["lines"][1]["segs"][0]["trimmed_from"] = "res://audio/voice/turnip/nar_001.mp3"
            (tmp / "game/stories/turnip/script.json").write_text(json.dumps(sc), encoding="utf-8")
            res3 = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            self.assertEqual(res3.status, "PASS", res3.checks)

            # 4. Mutate recorded.json -> fails T1_NO_ELEVENLABS
            fx["rec_json"].write_text(json.dumps({"nar||hello": "nar_001.mp3", "extra": "x.mp3"}), encoding="utf-8")
            res4 = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            checks4 = {c.id: c for c in res4.checks}
            self.assertEqual(checks4["T1_NO_ELEVENLABS"].status, "FAIL")

    def test_tier1_chroma_detB_catches_magenta_rim_not_purple_costume(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            purple_path = tmp / "cast_dahyun_calm.webp"
            _make_clean_sprite(purple_path, interior_rgb=(145, 70, 180))
            m_purple = e2e.compute_chroma_metrics(purple_path)
            self.assertEqual(m_purple["detB"], 0)

            magenta_path = tmp / "cast_tiger_slip.webp"
            _make_magenta_rim_sprite(magenta_path)
            m_mag = e2e.compute_chroma_metrics(magenta_path)
            self.assertGreater(m_mag["detB"], 10)

            # Full patjuk fixture check with magenta cast_tiger_slip.webp
            fx = _build_minimal_repo(tmp, "patjuk")
            _make_magenta_rim_sprite(tmp / "game/art/cast/cast_tiger_slip.webp")
            res = e2e.verify_tier1(tmp, ["patjuk"], baselines=fx["baselines"])[0]
            checks = {c.id: c for c in res.checks}
            self.assertEqual(checks["T1_CHROMA_MAGENTA"].status, "FAIL")

    def test_tier1_bodies_steep_slope_and_runtime_guards(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "witch_candy")
            # Inject story_wc_houses_a_02 with -0.18758 slope
            _make_clean_sprite(tmp / "game/art/atlas/village_houses/bodies/wc_side.webp")
            _make_clean_sprite(tmp / "game/art/atlas/village_houses/bodies/wc_back.webp")
            _make_clean_sprite(tmp / "game/art/atlas/village_houses/bodies/wc_roof.webp")
            bodies = json.loads((tmp / "game/art/atlas/bodies.json").read_text())
            bodies["story_wc_houses_a_02"] = {
                "mats": [1, 2],
                "wall_lines": [[93.454, -0.18758], [316.555, 0.06392]],
                "side_file": "art/atlas/village_houses/bodies/wc_side.webp",
                "back_file": "art/atlas/village_houses/bodies/wc_back.webp",
                "roof_file": "art/atlas/village_houses/bodies/wc_roof.webp",
            }
            (tmp / "game/art/atlas/bodies.json").write_text(json.dumps(bodies), encoding="utf-8")

            # Break _sky_texture resolution and remove rapunzel from house_orbit_all.sh
            (tmp / "game/story/spread_stage.gd").write_text(
                "static func _sky_texture(top: Color, hor: Color) -> Texture2D:\n\tvar w := 512\n\tvar h := 160\n\treturn null\n",
                encoding="utf-8",
            )
            (tmp / "tools/story/house_orbit_all.sh").write_text(
                'TALES="${*:-sun_wind three_pigs}"\n',
                encoding="utf-8",
            )

            res = e2e.verify_tier1(tmp, ["witch_candy"], baselines=fx["baselines"])[0]
            checks = {c.id: c for c in res.checks}
            self.assertEqual(checks["T1_SET_AND_BODIES"].status, "FAIL")
            self.assertIn("-0.18758", checks["T1_SET_AND_BODIES"].message)
            self.assertEqual(checks["T1_RUNTIME_GUARDS"].status, "FAIL")
            self.assertEqual(checks["T1_ORBIT_COVERAGE"].status, "FAIL")

    def test_tier1_three_pigs_village_houses_01_missing_roof_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "three_pigs")
            bodies = json.loads((tmp / "game/art/atlas/bodies.json").read_text())
            _make_clean_sprite(tmp / "game/art/atlas/village_houses/bodies/vh01_side.webp")
            _make_clean_sprite(tmp / "game/art/atlas/village_houses/bodies/vh01_back.webp")
            _make_clean_sprite(tmp / "game/art/atlas/village_houses/bodies/vh01_roof.webp")
            bodies["village_houses_01"] = {
                "mats": [1, 2],
                "wall_lines": [[16.0, 0.01], [203.0, -0.01]],
                "side_file": "art/atlas/village_houses/bodies/vh01_side.webp",
                "back_file": "art/atlas/village_houses/bodies/vh01_back.webp",
                "roof_file": "art/atlas/village_houses/bodies/vh01_roof.webp",
            }
            (tmp / "game/art/atlas/bodies.json").write_text(json.dumps(bodies), encoding="utf-8")
            (tmp / "tools/atlas/house_bodies.py").write_text("OVERRIDE = {}\n", encoding="utf-8")

            res = e2e.verify_tier1(tmp, ["three_pigs"], baselines=fx["baselines"])[0]
            checks = {c.id: c for c in res.checks}
            self.assertEqual(checks["T1_SET_AND_BODIES"].status, "FAIL")
            self.assertIn("village_houses_01", checks["T1_SET_AND_BODIES"].message)

    def test_tier1_chroma_atlas_coverage_bodies_safety_and_corrupt_handling(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            subprocess.run(["git", "-C", str(tmp), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(tmp), "config", "user.email", "t@example.com"], check=True)
            subprocess.run(["git", "-C", str(tmp), "config", "user.name", "T"], check=True)
            subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(tmp), "commit", "-q", "-m", "init"], check=True)

            # 1. Corrupt AND magenta /bodies/*.webp must be skipped safely without crashing or failing
            (tmp / "game/art/atlas/village_houses/bodies/village_houses_04_side.webp").write_bytes(b"not_a_webp")
            _make_magenta_rim_sprite(tmp / "game/art/atlas/village_houses/bodies/village_houses_04_back.webp")
            res_bodies = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"], strict_chroma=True)[0]
            self.assertEqual(res_bodies.status, "PASS", res_bodies.checks)

            # 2. Modified tale atlas sprite with detB > 10 fails T1_CHROMA_MAGENTA
            _make_magenta_rim_sprite(tmp / "game/art/atlas/village_houses/village_houses_04.webp")
            res_tale_atlas = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            checks_ta = {c.id: c for c in res_tale_atlas.checks}
            self.assertEqual(checks_ta["T1_CHROMA_MAGENTA"].status, "FAIL")

            # 3. Restore tale atlas, modify non-tale shared atlas sprite -> still fails T1_CHROMA_MAGENTA
            _make_clean_sprite(tmp / "game/art/atlas/village_houses/village_houses_04.webp")
            _make_magenta_rim_sprite(tmp / "game/art/atlas/story_bk_materials/story_bk_materials_00.webp")
            res_shared = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            checks_sh = {c.id: c for c in res_shared.checks}
            self.assertEqual(checks_sh["T1_CHROMA_MAGENTA"].status, "FAIL")

            # 4. Corrupt non-body sprite recorded as unreadable error instead of crashing
            (tmp / "game/art/atlas/story_bk_materials/story_bk_materials_00.webp").write_bytes(b"corrupt")
            res_corrupt = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            checks_co = {c.id: c for c in res_corrupt.checks}
            self.assertEqual(checks_co["T1_CHROMA_MAGENTA"].status, "FAIL")
            self.assertIn("unreadable", checks_co["T1_CHROMA_MAGENTA"].message)

    def test_tier1_chroma_strict_chroma_flags_atlas_hygiene(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            _make_magenta_rim_sprite(tmp / "game/art/atlas/village_houses/village_houses_04.webp")

            res_warn = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"], strict_chroma=False)[0]
            checks_w = {c.id: c for c in res_warn.checks}
            self.assertEqual(checks_w["T1_CHROMA_MAGENTA"].status, "WARN")
            self.assertEqual(res_warn.status, "PASS")

            res_fail = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"], strict_chroma=True)[0]
            checks_f = {c.id: c for c in res_fail.checks}
            self.assertEqual(checks_f["T1_CHROMA_MAGENTA"].status, "FAIL")
            self.assertEqual(res_fail.status, "FAIL")

    def test_tier1_no_elevenlabs_git_overwrite_nongit_trimmed_and_pieces(self) -> None:
        # A. Git mode: overwriting tracked .mp3 fails T1_NO_ELEVENLABS
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            subprocess.run(["git", "-C", str(tmp), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(tmp), "config", "user.email", "t@example.com"], check=True)
            subprocess.run(["git", "-C", str(tmp), "config", "user.name", "T"], check=True)
            subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(tmp), "commit", "-q", "-m", "init"], check=True)

            (tmp / "game/audio/voice/turnip/nar_001.mp3").write_bytes(b"ID3_OVERWRITTEN")
            res_git = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            checks_git = {c.id: c for c in res_git.checks}
            self.assertEqual(checks_git["T1_NO_ELEVENLABS"].status, "FAIL")

        # B. Non-git mode: non-trimmed_from .mp3 in script.json, missing trimmed_from source, and pieces[] status
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            sc_path = tmp / "game/stories/turnip/script.json"
            sc = json.loads(sc_path.read_text())

            # 1. Sneaky new mp3 referenced in script.json WITHOUT trimmed_from
            (tmp / "game/audio/voice/turnip/sneaky_new_tts.mp3").write_bytes(b"ID3sneaky")
            sc["lines"][1]["segs"][0]["audio"] = "res://audio/voice/turnip/sneaky_new_tts.mp3"
            sc_path.write_text(json.dumps(sc), encoding="utf-8")
            res1 = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            self.assertEqual({c.id: c for c in res1.checks}["T1_NO_ELEVENLABS"].status, "FAIL")

            # 2. trimmed_from pointing to nonexistent source clip fails
            sc["lines"][1]["segs"][0]["trimmed_from"] = "res://audio/voice/turnip/missing_src.mp3"
            sc_path.write_text(json.dumps(sc), encoding="utf-8")
            res2 = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            self.assertEqual({c.id: c for c in res2.checks}["T1_NO_ELEVENLABS"].status, "FAIL")

            # 3. Restore seg 1, add pieces[] with changed-needs-recording -> fails T1_NO_ELEVENLABS
            (tmp / "game/audio/voice/turnip/sneaky_new_tts.mp3").unlink()
            sc["lines"][1]["segs"][0] = {
                "speaker": "nar",
                "text": "bye",
                "status": "reuse",
                "audio": "res://audio/voice/turnip/nar_001.mp3",
                "pieces": [{"k": "N", "status": "changed-needs-recording", "audio": "res://audio/voice/turnip/nar_001.mp3"}],
            }
            sc_path.write_text(json.dumps(sc), encoding="utf-8")
            res3 = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            self.assertEqual({c.id: c for c in res3.checks}["T1_NO_ELEVENLABS"].status, "FAIL")

    def test_tier1_runtime_guards_alive_and_tree_process_frame_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            sr = tmp / "game/story/story_runner.gd"

            # Valid _alive() + await tree.process_frame
            sr.write_text(
                "func _alive() -> bool:\n\treturn not _exiting and is_inside_tree() and get_tree() != null\n\n"
                "func _frame() -> float:\n\tif not _alive():\n\t\treturn 0.0\n\tvar tree := get_tree()\n"
                "\tawait tree.process_frame\n\treturn 0.0\n",
                encoding="utf-8",
            )
            res_ok = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            self.assertEqual({c.id: c for c in res_ok.checks}["T1_RUNTIME_GUARDS"].status, "PASS")

            # await tree.process_frame BEFORE _alive() guard -> must FAIL
            sr.write_text(
                "func _alive() -> bool:\n\treturn not _exiting and is_inside_tree() and get_tree() != null\n\n"
                "func _frame() -> float:\n\tvar tree := get_tree()\n\tawait tree.process_frame\n"
                "\tif not _alive():\n\t\treturn 0.0\n\treturn 0.0\n",
                encoding="utf-8",
            )
            res_bad_order = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            self.assertEqual({c.id: c for c in res_bad_order.checks}["T1_RUNTIME_GUARDS"].status, "FAIL")

            # Dummy _alive() lacking is_inside_tree() & get_tree() check -> must FAIL
            sr.write_text(
                "func _alive() -> bool:\n\treturn true\n\n"
                "func _frame() -> float:\n\tif not _alive():\n\t\treturn 0.0\n\tawait tree.process_frame\n\treturn 0.0\n",
                encoding="utf-8",
            )
            res_dummy_alive = e2e.verify_tier1(tmp, ["turnip"], baselines=fx["baselines"])[0]
            self.assertEqual({c.id: c for c in res_dummy_alive.checks}["T1_RUNTIME_GUARDS"].status, "FAIL")


class TestTier2(unittest.TestCase):
    def test_tier2_solidity_red_threshold_and_strict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _build_minimal_repo(tmp, "turnip")
            jp = tmp / "artifacts/houses/e2e/turnip/turnip_audit.json"

            # 12px seam: passes normal, fails --strict
            audit = json.loads(jp.read_text())
            audit["house"]["front"]["holes_px"] = 12
            jp.write_text(json.dumps(audit), encoding="utf-8")
            self.assertEqual(e2e.verify_tier2(tmp, ["turnip"])[0].status, "PASS")
            self.assertEqual(e2e.verify_tier2(tmp, ["turnip"], strict=True)[0].status, "FAIL")

            # 31px hole (red > 30): fails
            audit["house"]["front"]["holes_px"] = 31
            jp.write_text(json.dumps(audit), encoding="utf-8")
            res = e2e.verify_tier2(tmp, ["turnip"])[0]
            self.assertEqual(res.status, "FAIL")
            self.assertEqual(res.metrics["red_count"], 1)

            # Missing view: fails
            del audit["house"]["low"]
            jp.write_text(json.dumps(audit), encoding="utf-8")
            self.assertEqual(e2e.verify_tier2(tmp, ["turnip"])[0].status, "FAIL")

    def test_tier2_orbit_preflight_and_direct_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _build_minimal_repo(tmp, "rapunzel")

            # Remove rapunzel from house_orbit_all.sh -> preflight fails without calling subprocess
            (tmp / "tools/story/house_orbit_all.sh").write_text('TALES="${*:-turnip}"\n', encoding="utf-8")
            with mock.patch("verify_all_e2e.subprocess.run") as m_run:
                res = e2e.verify_tier2(tmp, ["rapunzel"], run_orbit=True)[0]
                self.assertEqual(res.status, "FAIL")
                self.assertIn("ORBIT_SCRIPT_MISSING_TALE", res.checks[0].message)
                m_run.assert_not_called()

            # Restore rapunzel -> calls house_orbit_all.sh directly (NOT with_godot.sh)
            _build_minimal_repo(tmp, "rapunzel")
            with mock.patch("verify_all_e2e.subprocess.run") as m_run:
                m_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                res = e2e.verify_tier2(tmp, ["rapunzel"], run_orbit=True)[0]
                self.assertEqual(res.status, "PASS")
                called_cmd = m_run.call_args[0][0]
                self.assertTrue(called_cmd[0].endswith("tools/story/house_orbit_all.sh"))
                self.assertNotIn("with_godot.sh", " ".join(called_cmd))

    def test_tier2_run_orbit_ignores_stale_directories_when_e2e_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _build_minimal_repo(tmp, "turnip")
            # Move audit from artifacts/houses/e2e/ to stale artifacts/houses/old/
            old_dir = tmp / "artifacts/houses/old/turnip"
            old_dir.mkdir(parents=True, exist_ok=True)
            (tmp / "artifacts/houses/e2e/turnip/turnip_audit.json").rename(old_dir / "turnip_audit.json")
            (tmp / "artifacts/houses/e2e/turnip/turnip_audit.jpg").rename(old_dir / "turnip_audit.jpg")

            # Offline discovery still finds fallback artifacts/houses/old/turnip/
            self.assertEqual(e2e.verify_tier2(tmp, ["turnip"])[0].status, "PASS")

            # run_orbit=True without --orbit-dir MUST NOT fall back to artifacts/houses/old/
            with mock.patch("verify_all_e2e.subprocess.run") as m_run:
                m_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                res = e2e.verify_tier2(tmp, ["turnip"], run_orbit=True)[0]
                self.assertEqual(res.status, "MISSING")


class TestTier3AndTier4(unittest.TestCase):
    def test_tier3_and_tier4_pass_valid_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _build_minimal_repo(tmp, "turnip")
            t3_res, lmap = e2e.verify_tier3(tmp, ["turnip"], video_probe_fn=lambda _: (1200, 900, 120.2))
            self.assertEqual(t3_res[0].status, "PASS", t3_res[0].checks)
            t4_res = e2e.verify_tier4(tmp, ["turnip"], log_mp4_map=lmap)
            self.assertEqual(t4_res[0].status, "PASS", t4_res[0].checks)

    def test_tier3_catches_patjuk_905s_prebuild_stall(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "patjuk")
            lp: Path = fx["log_path"]
            txt = lp.read_text().replace(
                'STORY_DONE total=120.0 missing_audio=[] missing_sound=[] beats={"cover": 0.0, "zebra_mid": 40.0, "alpha_end": 80.0}',
                'STORY_DONE total=1216.6 missing_audio=[] missing_sound=[] beats={"cover": 0.0, "field": 5.5, "winter": 910.5, "end": 1200.0}',
            )
            lp.write_text(txt, encoding="utf-8")
            t3_res, _ = e2e.verify_tier3(tmp, ["patjuk"], video_probe_fn=lambda _: (1200, 900, 1218.67))
            checks = {c.id: c for c in t3_res[0].checks}
            self.assertEqual(checks["T3_BEATS_TIMING"].status, "FAIL")
            self.assertIn("905.0s", checks["T3_BEATS_TIMING"].message)

    def test_tier3_catches_null_tree_mid_error_and_video_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            lp: Path = fx["log_path"]
            txt = lp.read_text() + 'Parameter "data.tree" is null\nERROR: failed to load resource\n'
            lp.write_text(txt, encoding="utf-8")
            t3_res, _ = e2e.verify_tier3(tmp, ["turnip"], video_probe_fn=lambda _: (1024, 768, 90.0))
            checks = {c.id: c for c in t3_res[0].checks}
            self.assertEqual(checks["T3_ENGINE_ERRORS"].status, "FAIL")
            self.assertEqual(checks["T3_VIDEO_INTEGRITY"].status, "FAIL")

    def test_tier3_accepted_exception_and_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            lp: Path = fx["log_path"]
            lp.write_text(
                lp.read_text().replace("OVERLAP_COUNT 0", "OVERLAP_COUNT 1"),
                encoding="utf-8",
            )
            rid = f"{lp.name} {e2e._sha1_10(lp)}"
            gp = tmp / "artifacts/turnip/gate.md"
            gp.write_text(
                _replace_run_header(gp.read_text(), rid) + "- OVERLAP_COUNT: characters hold hands at finale\n",
                encoding="utf-8",
            )
            res_ok, _ = e2e.verify_tier3(tmp, ["turnip"], video_probe_fn=lambda _: (1200, 900, 120.0))
            self.assertEqual(res_ok[0].status, "PASS", res_ok[0].checks)

            res_strict, _ = e2e.verify_tier3(tmp, ["turnip"], strict=True, video_probe_fn=lambda _: (1200, 900, 120.0))
            self.assertEqual(res_strict[0].status, "FAIL")

    def test_tier4_stale_hash_forbidden_waiver_and_flagged_note(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            gp = tmp / "artifacts/turnip/gate.md"

            # 1. Forbidden waiver in Accepted exceptions
            orig_gate = gp.read_text()
            gp.write_text(orig_gate + "- SCRIPT_ERROR: ignore this crash please\n", encoding="utf-8")
            t4_bad = e2e.verify_tier4(tmp, ["turnip"])[0]
            self.assertEqual(t4_bad.status, "FAIL")
            self.assertIn("forbidden", t4_bad.checks[0].message)

            # 2. Malformed short reason
            gp.write_text(orig_gate + "- OVERLAP_COUNT: short\n", encoding="utf-8")
            t4_short = e2e.verify_tier4(tmp, ["turnip"])[0]
            self.assertEqual(t4_short.status, "FAIL")

            # 3. Stale sha1 when log changes by 1 byte
            gp.write_text(orig_gate, encoding="utf-8")
            fx["log_path"].write_text(fx["log_path"].read_text() + "\n", encoding="utf-8")
            t4_stale = e2e.verify_tier4(tmp, ["turnip"])[0]
            checks = {c.id: c for c in t4_stale.checks}
            self.assertEqual(checks["T4_GATE_MD"].status, "FAIL")
            self.assertEqual(checks["T4_MOTION_REVIEW"].status, "FAIL")

    def test_tier3_missing_track_nonzero_start_and_unwaivable_voice_dup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            lp: Path = fx["log_path"]
            txt = lp.read_text()
            txt = txt.replace("start=", "start=field").replace("VOICE_DUP=0", "VOICE_DUP=1")
            txt = "\n".join(ln for ln in txt.splitlines() if not ln.startswith("TRACK ")) + "\n"
            lp.write_text(txt, encoding="utf-8")
            # Even if someone tries to waive VOICE_DUP in gate.md, Tier 3 MUST fail
            gp = tmp / "artifacts/turnip/gate.md"
            gp.write_text(gp.read_text() + "- VOICE_DUP: waive please\n", encoding="utf-8")

            t3_res, _ = e2e.verify_tier3(tmp, ["turnip"], video_probe_fn=lambda _: (1200, 900, 120.0))
            checks = {c.id: c for c in t3_res[0].checks}
            self.assertEqual(checks["T3_RUN_COMPLETENESS"].status, "FAIL")
            self.assertEqual(checks["T3_ENGINE_ERRORS"].status, "FAIL")

    def test_tier4_unticked_checklist_and_flagged_motion_note_rules(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _build_minimal_repo(tmp, "turnip")
            gp = tmp / "artifacts/turnip/gate.md"
            gp.write_text(gp.read_text().replace("- [x] felt:", "- [ ] felt:"), encoding="utf-8")
            md = tmp / "artifacts/turnip/motion/motion_review.md"
            # Flagged row with short note and missing MOTION_FLAG 01 in gate.md
            md.write_text(md.read_text().replace("| - |", "| GLIDE |").replace("| clean side walk |", "| ok |"), encoding="utf-8")

            t4_res = e2e.verify_tier4(tmp, ["turnip"])[0]
            checks = {c.id: c for c in t4_res.checks}
            self.assertEqual(checks["T4_GATE_MD"].status, "FAIL")
            self.assertEqual(checks["T4_MOTION_REVIEW"].status, "FAIL")
            self.assertIn("note", checks["T4_MOTION_REVIEW"].message)
            self.assertIn("MOTION_FLAG 01", checks["T4_MOTION_REVIEW"].message)

    def test_tier3_ignores_stale_gate_md_accepted_exceptions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            lp: Path = fx["log_path"]
            lp.write_text(lp.read_text().replace("OVERLAP_COUNT 0", "OVERLAP_COUNT 1"), encoding="utf-8")
            gp = tmp / "artifacts/turnip/gate.md"
            # gate.md has an older sha1 header and an Accepted exception -> Tier 3 must NOT waive
            gp.write_text(
                gp.read_text() + "- OVERLAP_COUNT: characters hold hands at finale\n",
                encoding="utf-8",
            )
            t3_res, _ = e2e.verify_tier3(tmp, ["turnip"], video_probe_fn=lambda _: (1200, 900, 120.0))
            checks = {c.id: c for c in t3_res[0].checks}
            self.assertEqual(checks["T3_STAGE_COUNTERS"].status, "FAIL")

    def test_tier4_catches_wiped_motion_flags_and_zero_expected_moves(self) -> None:
        # 1. Wiped flags='-' in motion_review.md when log triggers GLIDE
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            lp: Path = fx["log_path"]
            lp.write_text(
                lp.read_text().replace("walk walk_cycle", "fly idle").replace("figs=walk_cycle:side:24", "figs=idle:side:24"),
                encoding="utf-8",
            )
            rid = f"{lp.name} {e2e._sha1_10(lp)}"
            gp = tmp / "artifacts/turnip/gate.md"
            gp.write_text(
                _replace_run_header(gp.read_text(), rid) + "- MOTION_FLAG 01: intentional glide segment test\n",
                encoding="utf-8",
            )
            md = tmp / "artifacts/turnip/motion/motion_review.md"
            md.write_text(_replace_run_header(md.read_text(), rid), encoding="utf-8")

            t4_wiped = e2e.verify_tier4(tmp, ["turnip"])[0]
            checks = {c.id: c for c in t4_wiped.checks}
            self.assertEqual(checks["T4_MOTION_REVIEW"].status, "FAIL")
            self.assertIn("wiped", checks["T4_MOTION_REVIEW"].message)

        # 2. expected_moves == 0 (TRACK-only log) must fail standalone Tier 4
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            lp: Path = fx["log_path"]
            lp.write_text(
                "\n".join(ln for ln in lp.read_text().splitlines() if not ln.startswith("MOVE ")) + "\n",
                encoding="utf-8",
            )
            rid = f"{lp.name} {e2e._sha1_10(lp)}"
            gp = tmp / "artifacts/turnip/gate.md"
            gp.write_text(_replace_run_header(gp.read_text(), rid), encoding="utf-8")
            md = tmp / "artifacts/turnip/motion/motion_review.md"
            md.write_text(_replace_run_header(md.read_text(), rid), encoding="utf-8")

            t4_nomove = e2e.verify_tier4(tmp, ["turnip"])[0]
            checks = {c.id: c for c in t4_nomove.checks}
            self.assertEqual(checks["T4_MOTION_REVIEW"].status, "FAIL")
            self.assertIn("0 MOVE lines", checks["T4_MOTION_REVIEW"].message)

    def test_tier4_duplicate_accepted_exceptions_100plus_and_whitespace_reason(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _build_minimal_repo(tmp, "turnip")
            gp = tmp / "artifacts/turnip/gate.md"
            orig_gate = gp.read_text()

            # 1. Duplicate ## Accepted exceptions section hiding forbidden entry -> FAIL
            gp.write_text(
                orig_gate + "\n## Notes\nchecked\n\n## Accepted exceptions\n- SCRIPT_ERROR: hidden in second section\n",
                encoding="utf-8",
            )
            t4_dup = e2e.verify_tier4(tmp, ["turnip"])[0]
            checks_dup = {c.id: c for c in t4_dup.checks}
            self.assertEqual(checks_dup["T4_GATE_MD"].status, "FAIL")
            self.assertIn("duplicate ## Accepted exceptions", checks_dup["T4_GATE_MD"].message)
            self.assertIn("SCRIPT_ERROR", checks_dup["T4_GATE_MD"].message)

            # 2. Whitespace-padded short reason (<10 chars after .strip()) -> FAIL
            gp.write_text(orig_gate + "- OVERLAP_COUNT:          x\n", encoding="utf-8")
            t4_ws = e2e.verify_tier4(tmp, ["turnip"])[0]
            self.assertEqual({c.id: c for c in t4_ws.checks}["T4_GATE_MD"].status, "FAIL")

            # 3. 3-digit MOTION_FLAG 100 allowed in Accepted exceptions -> PASS
            gp.write_text(orig_gate + "- MOTION_FLAG 100: deliberate jump over river stone\n", encoding="utf-8")
            t4_100 = e2e.verify_tier4(tmp, ["turnip"])[0]
            self.assertEqual({c.id: c for c in t4_100.checks}["T4_GATE_MD"].status, "PASS", t4_100.checks)


class TestCLIExitCodes(unittest.TestCase):
    def test_cli_usage_errors_return_exit_2(self) -> None:
        self.assertEqual(e2e.main(["--log", "foo.log"]), 2)
        self.assertEqual(e2e.main(["--tale", "not_a_tale"]), 2)
        self.assertEqual(e2e.main(["--tier", "9"]), 2)
        self.assertEqual(e2e.main(["--offline", "--record"]), 2)

    def test_cli_json_stdout_and_exit_0_on_clean_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fx = _build_minimal_repo(tmp, "turnip")
            with (
                mock.patch("verify_all_e2e.RECORDED_BASELINES", fx["baselines"]),
                mock.patch("verify_all_e2e.probe_video", return_value=(1200, 900, 120.0)),
                mock.patch("verify_all_e2e.shutil.which", return_value="/usr/bin/ffprobe"),
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = e2e.main(["--offline", "--tale", "turnip", "--json"], root=tmp)
            self.assertEqual(rc, 0, buf.getvalue())
            data = json.loads(buf.getvalue())
            self.assertEqual(data["overall"], "PASS")
            self.assertEqual(len(data["results"]), 4)


if __name__ == "__main__":
    unittest.main()
