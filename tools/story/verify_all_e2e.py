#!/usr/bin/env python3
"""Independent 4-tier E2E verification harness for popup-atlas.

Offline / read-only by default: NEVER launches Godot, NEVER calls ElevenLabs / record_lines.py,
and NEVER mutates artifacts/, gate.md, motion_review.md, game/, or recorded.json unless explicit
opt-in flags (--record, --orbit, --run-gate) are passed.

Usage:
  python3 tools/story/verify_all_e2e.py [--offline] [--tier 1,2,3,4] [--tale all]
  python3 tools/story/verify_all_e2e.py --tier 1,3,4 --tale turnip --json
  python3 tools/story/verify_all_e2e.py --tier 2 --orbit --orbit-dir artifacts/houses/e2e
  python3 tools/story/verify_all_e2e.py --tier 3,4 --tale three_pigs --record --run-gate

Exit codes:
  0 = All selected tiers and tales passed
  1 = Verification failure or missing required artifacts
  2 = CLI / configuration / environment error
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
from PIL import Image, ImageFilter, UnidentifiedImageError

REPO_ROOT = Path(__file__).resolve().parents[2]

# Import motion_review read-only for in-memory parse_moves / flags_for / log_hash.
_TOOLS_STORY = Path(__file__).resolve().parent
if str(_TOOLS_STORY) not in sys.path:
    sys.path.insert(0, str(_TOOLS_STORY))
import motion_review as _mr  # noqa: E402

TALES: tuple[str, ...] = (
    "turnip",
    "sun_wind",
    "three_pigs",
    "witch_candy",
    "wolf_goats",
    "sunmoon",
    "rapunzel",
    "patjuk",
)

ORBIT_VIEWS: tuple[str, ...] = (
    "front",
    "r35",
    "l35",
    "r70",
    "l70",
    "back_r",
    "back_l",
    "high",
    "low",
)

VISUAL_KEYS: tuple[str, ...] = (
    "rim",
    "steam",
    "holes",
    "houses",
    "empty",
    "place",
    "felt",
)

SHARED_ATLAS_SHEETS: tuple[str, ...] = (
    "autumn",
    "bushes_hedges",
    "fairytale_west",
    "farm_animals",
    "forest_broadleaf",
    "forest_conifer",
    "hills_clouds",
    "korean_nature",
    "korean_village",
    "meadow_field",
    "small_decor",
    "spring_blossom",
    "stream_water",
    "village_houses",
    "village_props",
    "winter_snow",
)

# Verified baseline SHA-256 and key counts for game/audio/voice/<tale>/recorded.json.
RECORDED_BASELINES: dict[str, dict[str, Any]] = {
    "turnip": {
        "sha256": "c6cc7f49d15cb83c6d9e7cdef51ecea62e7509fdc336fdfb04dddfcbeda1e6ca",
        "keys": 2,
    },
    "sun_wind": {
        "sha256": "78ece4f28161e2cfe8ecc08d4614eda961048079b486b2466d1c93d5312e34ce",
        "keys": 7,
    },
    "three_pigs": {
        "sha256": "1e17f9d0833285837e6df218eb664186430bfb65fbdcf1aa92ff812628210559",
        "keys": 2,
    },
    "witch_candy": {
        "sha256": "afc1a569ecd69916095666d6bc850d9c153de011600bbe5a53670386d180640b",
        "keys": 4,
    },
    "wolf_goats": {
        "sha256": "c6cc7f49d15cb83c6d9e7cdef51ecea62e7509fdc336fdfb04dddfcbeda1e6ca",
        "keys": 2,
    },
    "sunmoon": {
        "sha256": "4f9433d4728f1e534104380753d0e0a424cd2673a61264743caf38338f18668b",
        "keys": 2,
    },
    "rapunzel": {
        "sha256": "99dd379f7f8b8aa08cfec9474901c086ad2e259d996a8b9bbc70c3449d57bc8d",
        "keys": 7,
    },
    "patjuk": {
        "sha256": "d6b96df79b939447c9881fd252dec5cf25d19c658c30404b1ff9404649a48e8e",
        "keys": 4,
    },
}

# Explicit required cast movement/action cycles per tale & skin (from PROJECT.md + Explorer 2 spec).
REQUIRED_CAST_CYCLES: dict[str, dict[str, tuple[str, ...]]] = {
    "turnip": {
        "farm_grandpa": ("walk_cycle", "walk_front", "walk_back"),
        "farm_grandma": ("walk_cycle", "walk_front", "walk_back"),
        "farm_girl": ("walk_cycle", "walk_front", "walk_back"),
        "puppy": ("walk_cycle", "walk_front", "walk_back"),
        "tabby_cat": ("walk_cycle", "walk_front", "walk_back"),
        "mouse": ("walk_cycle", "walk_front", "walk_back"),
    },
    "sun_wind": {},  # traveller uses rigged CastPuppet SKINS["traveller"] if not flipbook
    "three_pigs": {
        "pig_a": ("walk_cycle", "walk_front", "walk_back"),
        "pig_b": ("walk_cycle", "walk_front", "walk_back"),
        "pig_c": ("walk_cycle", "walk_front", "walk_back"),
        "wolf": ("walk_cycle", "walk_front", "walk_back", "run_cycle", "run_front", "run_back", "climb_cycle"),
    },
    "witch_candy": {
        "dahyun": ("walk_cycle", "walk_front", "walk_back"),
        "candy_witch": ("walk_cycle", "walk_front", "walk_back"),
        "bear_kid": ("walk_cycle", "walk_front", "walk_back"),
        "fox_kid": ("walk_cycle", "walk_front", "walk_back"),
        "rabbit_kid": ("walk_cycle", "walk_front", "walk_back"),
        "hobak_cat": ("walk_cycle", "walk_front", "walk_back", "ghost_cycle", "ghost_front", "ghost_back"),
    },
    "wolf_goats": {
        "goat_mom": ("walk_cycle", "walk_front", "walk_back"),
        "wolf": ("walk_cycle", "walk_front", "walk_back", "run_cycle", "run_front", "run_back"),
        "goat_baby": ("walk_cycle", "walk_front", "walk_back", "run_cycle", "run_back", "run_front"),
        "goat_kid_1": ("walk_cycle", "walk_front", "walk_back", "run_cycle", "run_back", "run_front"),
        "goat_kid_2": ("walk_cycle", "walk_front", "walk_back", "run_cycle", "run_back", "run_front"),
        "goat_kid_3": ("walk_cycle", "walk_front", "walk_back", "run_cycle", "run_back", "run_front"),
        "goat_kid_4": ("walk_cycle", "walk_front", "walk_back", "run_cycle", "run_back", "run_front"),
        "goat_kid_5": ("walk_cycle", "walk_front", "walk_back", "run_cycle", "run_back", "run_front"),
        "goat_kid_6": ("walk_cycle", "walk_front", "walk_back", "run_cycle", "run_back", "run_front"),
    },
    "sunmoon": {
        "hanbok_mom": ("walk_cycle", "walk_front", "walk_back"),
        "hanbok_boy": ("walk_cycle", "walk_front", "walk_back", "climb_cycle"),
        "hanbok_girl": ("walk_cycle", "walk_front", "walk_back", "climb_cycle"),
        "tiger": ("walk_cycle", "walk_front", "walk_back", "run_back", "climb_cycle", "dg_back"),
    },
    "rapunzel": {
        "rapunzel": ("walk_cycle", "walk_front", "walk_back"),
        "peasant_father": ("walk_cycle", "walk_front", "walk_back"),
        "gothel": ("walk_cycle", "walk_front", "walk_back", "climb_cycle"),
        "prince": ("walk_cycle", "walk_front", "walk_back", "climb_cycle"),
    },
    "patjuk": {
        "hanbok_granny": ("walk_cycle", "walk_front", "walk_back"),
        "tiger": ("walk_cycle", "walk_front", "walk_back"),
        "pj_bam": ("walk_cycle", "walk_front", "walk_back"),
        "pj_jara": ("walk_cycle", "walk_front", "walk_back"),
        "pj_ddong": ("walk_cycle", "walk_front", "walk_back"),
        "pj_songgot": ("walk_cycle", "walk_front", "walk_back"),
        "pj_jeolgu": ("walk_cycle", "walk_front", "walk_back"),
        "pj_myeongseok": ("walk_cycle", "walk_front", "walk_back"),
        "pj_jige": ("walk_cycle", "walk_front", "walk_back"),
    },
}

# Strict allowlist for gate.md ## Accepted exceptions.
FORBIDDEN_EXCEPTION_IDS: frozenset[str] = frozenset({
    "SCRIPT_ERROR",
    "FAILED_LOADING",
    "DATA_TREE_NULL",
    "ERROR_LINE",
    "VOICE_DUP",
    "CAM_JUMP",
    "CAM_JERK",
    "SPEAKER_OFF",
    "BLACK_LIPS",
    "missing_audio",
    "missing_sound",
    "CHECK_LINES",
    "STORY_DONE",
    "MOTION_NOLOG",
    "MOTION_VERDICT",
    "MOTION_FIX",
    "VISUAL_CHECKLIST",
    "STALL",
    "VIDEO_INFO",
    "RUN_INCOMPLETE",
})

EXCEPTION_LINE_RE = re.compile(r"^\s*-\s*([A-Za-z0-9_]+(?: [\w.:-]+)?)\s*:\s*(.+?)\s*$")
EXCEPTION_STRICT_ID_RE = re.compile(r"^(?:OVERLAP_COUNT|OCCLUDE_COUNT|SET_CHECK \S+|MOTION_FLAG \d{2,})$")

TALE_ATLAS_PREFIXES: dict[str, tuple[str, ...]] = {
    "turnip": ("story_tn_", "story_veg_"),
    "sun_wind": (),
    "three_pigs": ("story_houses", "story_room", "story_hearth", "story_build_props"),
    "witch_candy": ("story_wc_",),
    "wolf_goats": ("story_wg_",),
    "sunmoon": ("story_sm_",),
    "rapunzel": ("story_rp_",),
    "patjuk": ("story_pj_",),
}

MOVE_DO_VERBS = {"walk", "walk_to", "go_inside", "climb"}
MAX_BEAT_GAP_SEC = 180.0
MIN_TOTAL_SEC = 60.0
MAX_TOTAL_SEC = 600.0
MAX_PREBUILT_SEC = 30.0
MAX_MP4_LOG_DIFF_SEC = 10.0
EXPECTED_WIDTH = 1200
EXPECTED_HEIGHT = 900
ORBIT_MAX_HOLES_PX = 30
WALL_SLOPE_MAX = 0.13  # Catches story_wc_houses_a_02 (-0.18758) & b_06 (-0.14598); allows curved thatch/hanok (<=0.126)


@dataclass
class CheckResult:
    id: str
    status: str  # PASS | FAIL | WARN | MISSING
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TierTaleResult:
    tier: int
    tale: str
    status: str  # PASS | FAIL | MISSING
    checks: list[CheckResult] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)


def _aggregate_status(checks: list[CheckResult], strict: bool = False) -> str:
    has_missing = any(c.status == "MISSING" for c in checks)
    has_fail = any(c.status == "FAIL" for c in checks)
    has_warn = any(c.status == "WARN" for c in checks)
    if has_fail or (strict and has_warn):
        return "FAIL"
    if has_missing:
        return "MISSING"
    return "PASS"


def _sha1_10(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:10]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_game_path(root: Path, raw_path: str) -> Path:
    s = raw_path.strip()
    if s.startswith("res://"):
        s = s[6:]
    return root / "game" / s


def _find_sets_recursive(obj: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        if "set" in obj and isinstance(obj["set"], list):
            for item in obj["set"]:
                if isinstance(item, dict):
                    out.append(item)
        for v in obj.values():
            out.extend(_find_sets_recursive(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_find_sets_recursive(v))
    return out


def _find_steps_recursive(obj: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        if "steps" in obj and isinstance(obj["steps"], list):
            for st in obj["steps"]:
                if isinstance(st, dict):
                    out.append(st)
                    out.extend(_find_steps_recursive(st))
        for k, v in obj.items():
            if k != "steps":
                out.extend(_find_steps_recursive(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_find_steps_recursive(v))
    return out


def compute_chroma_metrics(img_path: Path) -> dict[str, int]:
    """Compute boundary-isolated bright magenta detB and 3px band detA counts.

    detB: 1-px outer opaque silhouette edge with balanced bright magenta
          (min(R,B) - G > 50, R > 160, B > 150, |R - B| < 45).
    detA: 3-px boundary band (A > 10 & ~inner3) with min(R,B) - G > 40, R > 120, B > 120, |R - B| < 55.
    """
    im = Image.open(img_path).convert("RGBA")
    arr = np.asarray(im)
    r = arr[..., 0].astype(np.int32)
    g = arr[..., 1].astype(np.int32)
    b = arr[..., 2].astype(np.int32)
    a = arr[..., 3]

    opaque = a > 128
    pad = np.pad(opaque, 1, constant_values=False)
    all4 = pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    edge1 = opaque & (~all4)

    min_rb = np.minimum(r, b)
    rb_diff = np.abs(r - b)

    det_b = edge1 & ((min_rb - g) > 50) & (r > 160) & (b > 150) & (rb_diff < 45)

    alpha_full = ((a > 250).astype(np.uint8)) * 255
    inner3 = np.asarray(Image.fromarray(alpha_full).filter(ImageFilter.MinFilter(7))) > 0
    det_a = (a > 10) & (~inner3) & ((min_rb - g) > 40) & (r > 120) & (b > 120) & (rb_diff < 55)

    return {
        "detB": int(det_b.sum()),
        "detA": int(det_a.sum()),
        "edge1": int(edge1.sum()),
    }


def _git_available(root: Path) -> bool:
    return (root / ".git").exists()


def _git_ls_files(root: Path, rel_glob: str) -> set[str] | None:
    if not _git_available(root):
        return None
    res = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--", rel_glob],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        return None
    return {line.strip() for line in res.stdout.splitlines() if line.strip()}


def _git_touched_art_files(root: Path) -> list[Path]:
    if not _git_available(root):
        return []
    res = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "--", "game/art/cast", "game/art/atlas"],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        return []
    out: list[Path] = []
    for line in res.stdout.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        if "D" in status:
            continue
        rel = line[3:].strip()
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1].strip()
        p = root / rel
        if p.suffix.lower() == ".webp" and p.exists():
            out.append(p)
    return out


def _load_cast_cycles(root: Path) -> tuple[dict[str, dict[str, list[Path]]], list[str]]:
    """Return (skin -> {cycle_name: [existing_frame_paths]}, missing_catalog_files)."""
    cat_path = root / "game/art/cast/catalog.json"
    if not cat_path.exists():
        return {}, [str(cat_path)]
    raw = json.loads(cat_path.read_text(encoding="utf-8"))
    arr = raw if isinstance(raw, list) else raw.get("cards", [])
    cycles: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    missing_files: list[str] = []
    for entry in arr:
        skin = entry.get("skin", "")
        rel_p = entry.get("path", "")
        fp = _resolve_game_path(root, rel_p) if rel_p else None
        if fp is not None and not fp.exists():
            missing_files.append(rel_p)
        if "cycle" in entry:
            if fp is not None and fp.exists():
                cycles[skin][entry["cycle"]].append(fp)
            else:
                cycles[skin].setdefault(entry["cycle"], [])
    return cycles, missing_files


def _load_atlas_catalog(root: Path) -> dict[str, dict[str, Any]]:
    cat_path = root / "game/art/atlas/catalog.json"
    if not cat_path.exists():
        return {}
    raw = json.loads(cat_path.read_text(encoding="utf-8"))
    arr = raw if isinstance(raw, list) else raw.get("cards", [])
    return {e["id"]: e for e in arr if isinstance(e, dict) and "id" in e}


# ---------------------------------------------------------------------------
# Tier 1: Static Script, Audio, Cast, Chroma, Bodies & Runtime Guards
# ---------------------------------------------------------------------------

def _check_t1_script_schema(tale: str, sc: dict[str, Any] | None, err: str | None) -> CheckResult:
    if sc is None:
        return CheckResult("T1_SCRIPT_SCHEMA", "FAIL", f"Invalid or missing script.json: {err}")
    issues: list[str] = []
    if sc.get("tale_id") != tale:
        issues.append(f"tale_id={sc.get('tale_id')!r} != {tale!r}")
    if sc.get("overlap_check") is not True:
        issues.append(f"overlap_check={sc.get('overlap_check')!r} (must be True)")
    if sc.get("spacing") is not True:
        issues.append(f"spacing={sc.get('spacing')!r} (must be True)")
    gs = sc.get("ground_style")
    if gs not in (None, "", "paper"):
        issues.append(f"ground_style={gs!r} (must be absent or 'paper')")
    cast = sc.get("cast", {})
    walkers = [role for role, cfg in cast.items() if isinstance(cfg, dict) and cfg.get("kind") == "walker"]
    if walkers:
        issues.append(f"legacy walker kind present for {walkers}")
    if issues:
        return CheckResult("T1_SCRIPT_SCHEMA", "FAIL", "; ".join(issues), {"issues": issues})
    return CheckResult("T1_SCRIPT_SCHEMA", "PASS", "script.json schema valid (overlap_check=True, spacing=True, paper, 0 walkers)")


def _check_t1_audio_integrity(root: Path, tale: str, sc: dict[str, Any] | None) -> CheckResult:
    if sc is None:
        return CheckResult("T1_AUDIO_INTEGRITY", "MISSING", "script.json missing")
    bad_status: list[str] = []
    missing_audio: list[str] = []
    checked = 0
    for line in sc.get("lines", []):
        if not line.get("used", True):
            continue
        lid = line.get("id", "?")
        for idx, seg in enumerate(line.get("segs", [])):
            checked += 1
            st = seg.get("status")
            if st not in ("reuse", "changed-recorded"):
                bad_status.append(f"{lid}[{idx}]:{st}")
            aud = seg.get("audio")
            if not aud:
                missing_audio.append(f"{lid}[{idx}]:empty_audio")
            else:
                ap = _resolve_game_path(root, aud)
                if not ap.exists() or ap.stat().st_size <= 0:
                    missing_audio.append(f"{lid}[{idx}]:{aud}")
            for pi, piece in enumerate(seg.get("pieces", [])):
                pa = piece.get("audio")
                if not pa:
                    missing_audio.append(f"{lid}[{idx}].pieces[{pi}]:empty_audio")
                else:
                    pp = _resolve_game_path(root, pa)
                    if not pp.exists() or pp.stat().st_size <= 0:
                        missing_audio.append(f"{lid}[{idx}].pieces[{pi}]:{pa}")
    if bad_status or missing_audio:
        msg_parts = []
        if bad_status:
            msg_parts.append(f"{len(bad_status)} seg(s) not recorded ({bad_status[:5]})")
        if missing_audio:
            msg_parts.append(f"{len(missing_audio)} missing/empty audio file(s) ({missing_audio[:5]})")
        return CheckResult(
            "T1_AUDIO_INTEGRITY",
            "FAIL",
            "; ".join(msg_parts),
            {"bad_status": bad_status, "missing_audio": missing_audio, "checked_segs": checked},
        )
    return CheckResult("T1_AUDIO_INTEGRITY", "PASS", f"{checked} used seg(s) recorded and present on disk", {"checked_segs": checked})


def _check_t1_no_elevenlabs(
    root: Path,
    tale: str,
    sc: dict[str, Any] | None,
    record_lines_clean: bool | None,
    baselines: dict[str, dict[str, Any]] | None = None,
) -> CheckResult:
    if sc is None:
        return CheckResult("T1_NO_ELEVENLABS", "MISSING", "script.json missing")
    base_map = baselines if baselines is not None else RECORDED_BASELINES
    issues: list[str] = []
    voice_dir = root / "game/audio/voice" / tale

    def _validate_trimmed_from(tf_raw: Any, out_audio_raw: str | None, ctx: str) -> bool:
        """Validate trimmed_from references an existing distinct source clip on disk."""
        tf_str = str(tf_raw or "").strip()
        if not tf_str:
            return False
        out_name = Path(out_audio_raw).name if out_audio_raw else ""
        srcs = re.findall(r"(?:res://)?[A-Za-z0-9_./-]+\.(?:mp3|wav|ogg)", tf_str)
        if not srcs:
            py_m = re.search(r"([A-Za-z0-9_./-]+\.py)\b", tf_str)
            if not py_m or not (root / py_m.group(1)).exists():
                issues.append(f"{ctx}: unapproved trimmed_from without source clip ({tf_str!r})")
            return False
        all_ok = True
        for src_raw in srcs:
            src_name = Path(src_raw).name
            if out_name and src_name == out_name:
                issues.append(f"{ctx}: trimmed_from self-references {src_name}")
                all_ok = False
                continue
            cand_game = _resolve_game_path(root, src_raw)
            cand_voice = voice_dir / src_name
            if not cand_game.exists() and not cand_voice.exists():
                issues.append(f"{ctx}: trimmed_from source clip missing ({src_raw})")
                all_ok = False
        return all_ok

    # 1. Dry-run TTS equivalence check (mirrors tools/story/record_lines.py without calling it)
    tts_chars = 0
    tts_segs: list[str] = []
    trimmed_audio: set[str] = set()
    for line in sc.get("lines", []):
        lid = line.get("id", "?")
        for idx, seg in enumerate(line.get("segs", [])):
            aud = seg.get("audio")
            if seg.get("trimmed_from"):
                if _validate_trimmed_from(seg.get("trimmed_from"), aud, f"{lid}[{idx}]") and aud:
                    trimmed_audio.add(Path(aud).name)
            for pi, piece in enumerate(seg.get("pieces", [])):
                pa = piece.get("audio")
                if piece.get("trimmed_from"):
                    if _validate_trimmed_from(piece.get("trimmed_from"), pa, f"{lid}[{idx}].pieces[{pi}]") and pa:
                        trimmed_audio.add(Path(pa).name)
        if not line.get("used", True):
            continue
        for idx, seg in enumerate(line.get("segs", [])):
            if seg.get("status") not in ("reuse", "changed-recorded"):
                tags = seg.get("tags") or ""
                text = seg.get("text") or ""
                sent = f"{tags} {text}" if tags else text
                tts_chars += len(sent)
                tts_segs.append(f"{lid}[{idx}]")
            for pi, piece in enumerate(seg.get("pieces", [])):
                if "status" in piece and piece.get("status") not in ("reuse", "changed-recorded"):
                    tags = piece.get("tags") or ""
                    text = piece.get("text") or piece.get("tpl") or ""
                    sent = f"{tags} {text}" if tags else text
                    tts_chars += len(sent)
                    tts_segs.append(f"{lid}[{idx}].pieces[{pi}]")
    if tts_chars > 0 or tts_segs:
        issues.append(f"TTS dry-run non-zero: {len(tts_segs)} seg(s), {tts_chars} chars ({tts_segs[:5]})")

    # 2. recorded.json baseline SHA-256 & key count
    rec_path = voice_dir / "recorded.json"
    rec_data: dict[str, Any] = {}
    if not rec_path.exists():
        issues.append(f"missing {rec_path}")
    else:
        try:
            rec_data = json.loads(rec_path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"invalid recorded.json: {exc}")
            rec_data = {}
        actual_sha = _sha256(rec_path)
        exp = base_map.get(tale)
        if exp:
            if actual_sha != exp["sha256"]:
                issues.append(f"recorded.json sha256 mismatch ({actual_sha[:12]} != {exp['sha256'][:12]})")
            if len(rec_data) != exp["keys"]:
                issues.append(f"recorded.json key count {len(rec_data)} != {exp['keys']}")

    # 3. No unapproved new or modified .mp3 files in game/audio/voice/<tale>/
    if voice_dir.exists():
        disk_mp3s = {p.name for p in voice_dir.glob("*.mp3")}
        tracked = _git_ls_files(root, f"game/audio/voice/{tale}/*.mp3")
        if tracked is not None:
            tracked_names = {Path(p).name for p in tracked}
            new_mp3s = sorted(disk_mp3s - tracked_names - trimmed_audio)
            if new_mp3s:
                issues.append(f"new untracked .mp3 without trimmed_from: {new_mp3s[:5]}")
            r_diff = subprocess.run(
                ["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", f"game/audio/voice/{tale}/"],
                capture_output=True,
            )
            if r_diff.returncode != 0:
                issues.append(f"tracked voice files modified vs HEAD under game/audio/voice/{tale}/")
        else:
            # Isolated fixture without git: allow only recorded.json values or legitimately trimmed_from clips
            known = trimmed_audio | set(rec_data.values() if isinstance(rec_data, dict) else ())
            unknown_mp3s = sorted(disk_mp3s - known)
            if unknown_mp3s:
                issues.append(f"unapproved .mp3 without recorded.json entry or trimmed_from: {unknown_mp3s[:5]}")

    # 4. record_lines.py clean vs HEAD
    if record_lines_clean is False:
        issues.append("tools/story/record_lines.py has uncommitted modifications vs HEAD")

    if issues:
        return CheckResult("T1_NO_ELEVENLABS", "FAIL", "; ".join(issues), {"tts_chars": tts_chars, "issues": issues})
    return CheckResult("T1_NO_ELEVENLABS", "PASS", "0 TTS chars, recorded.json baseline locked, 0 unapproved mp3s, record_lines.py clean")


def _check_t1_cast_cycles(
    tale: str,
    sc: dict[str, Any] | None,
    cast_cycles: dict[str, dict[str, list[Path]]],
    missing_cast_files: list[str],
) -> CheckResult:
    if sc is None:
        return CheckResult("T1_CAST_CYCLES", "MISSING", "script.json missing")

    req_by_skin: dict[str, set[str]] = defaultdict(set)
    for skin, cycs in REQUIRED_CAST_CYCLES.get(tale, {}).items():
        req_by_skin[skin].update(cycs)

    # Also infer movement roles from script.json steps dynamically.
    cast = sc.get("cast", {})
    for st in _find_steps_recursive(sc):
        do = st.get("do")
        if do in MOVE_DO_VERBS:
            who = st.get("who") or st.get("actor")
            roles = who if isinstance(who, list) else ([who] if isinstance(who, str) else [])
            for role in roles:
                cfg = cast.get(role, {})
                if isinstance(cfg, dict) and cfg.get("kind") == "actor":
                    skin = cfg.get("skin", "")
                    if skin and skin != "traveller":
                        req_by_skin[skin].update(("walk_cycle", "walk_front", "walk_back"))
                        if do == "climb":
                            req_by_skin[skin].add("climb_cycle")

    missing_cycles: list[str] = []
    short_cycles: list[str] = []
    for skin, needed in sorted(req_by_skin.items()):
        skin_cycles = cast_cycles.get(skin, {})
        for cy in sorted(needed):
            if cy not in skin_cycles:
                missing_cycles.append(f"{skin}.{cy}")
            elif len(skin_cycles[cy]) < 2:
                short_cycles.append(f"{skin}.{cy}({len(skin_cycles[cy])}f)")

    if missing_cycles or short_cycles or missing_cast_files:
        parts = []
        if missing_cycles:
            parts.append(f"missing cycles: {', '.join(missing_cycles)}")
        if short_cycles:
            parts.append(f"cycles with <2 existing frames: {', '.join(short_cycles)}")
        if missing_cast_files:
            parts.append(f"{len(missing_cast_files)} missing catalog .webp files")
        return CheckResult(
            "T1_CAST_CYCLES",
            "FAIL",
            "; ".join(parts),
            {"missing_cycles": missing_cycles, "short_cycles": short_cycles},
        )
    return CheckResult("T1_CAST_CYCLES", "PASS", f"All {len(req_by_skin)} moving skin(s) have complete >=2-frame cycles")


def _safe_chroma_metrics(img_path: Path) -> tuple[dict[str, int] | None, str | None]:
    try:
        return compute_chroma_metrics(img_path), None
    except (UnidentifiedImageError, OSError) as exc:
        return None, str(exc)


def _compute_global_chroma_audit(root: Path) -> dict[str, Any]:
    """Compute target sprite, git-touched sprite, and full cast/atlas hygiene metrics."""
    unreadable: list[dict[str, str]] = []
    tiger_slip = root / "game/art/cast/cast_tiger_slip.webp"
    tiger_metrics: dict[str, Any] | None = None
    if tiger_slip.exists():
        tm, terr = _safe_chroma_metrics(tiger_slip)
        if terr:
            tiger_metrics = {"error": terr}
            unreadable.append({"file": "game/art/cast/cast_tiger_slip.webp", "error": terr})
        else:
            tiger_metrics = tm

    touched_failures: list[dict[str, Any]] = []
    for p in _git_touched_art_files(root):
        if "/bodies/" in p.as_posix():
            continue
        rel = str(p.relative_to(root))
        m, err = _safe_chroma_metrics(p)
        if err:
            unreadable.append({"file": rel, "error": err})
        elif m is not None and m["detB"] > 10:
            touched_failures.append({"file": rel, **m})

    cast_hygiene: list[dict[str, Any]] = []
    cast_dir = root / "game/art/cast"
    if cast_dir.exists():
        for p in sorted(cast_dir.glob("cast_*.webp")):
            rel = str(p.relative_to(root))
            m, err = _safe_chroma_metrics(p)
            if err:
                unreadable.append({"file": rel, "error": err})
            elif m is not None and m["detB"] > 20:
                cast_hygiene.append({"file": rel, **m})

    atlas_hygiene: list[dict[str, Any]] = []
    atlas_dir = root / "game/art/atlas"
    if atlas_dir.exists():
        for p in sorted(atlas_dir.rglob("*.webp")):
            if "/bodies/" in p.as_posix():
                continue
            rel = str(p.relative_to(root))
            m, err = _safe_chroma_metrics(p)
            if err:
                unreadable.append({"file": rel, "error": err})
            elif m is not None and m["detB"] > 20:
                atlas_hygiene.append({"file": rel, **m})

    return {
        "tiger_slip": tiger_metrics,
        "touched_failures": touched_failures,
        "cast_hygiene": cast_hygiene,
        "atlas_hygiene": atlas_hygiene,
        "unreadable": unreadable,
    }


def _check_t1_chroma_magenta(
    tale: str,
    sc: dict[str, Any] | None,
    chroma_audit: dict[str, Any],
    strict_chroma: bool,
    atlas_cat: dict[str, dict[str, Any]] | None = None,
) -> CheckResult:
    issues: list[str] = []
    warns: list[str] = []

    if tale == "patjuk":
        tm = chroma_audit.get("tiger_slip")
        if tm is None:
            issues.append("cast_tiger_slip.webp missing")
        elif "error" in tm:
            issues.append(f"cast_tiger_slip.webp unreadable: {tm['error']}")
        elif tm["detB"] > 10 or tm["detA"] > 20:
            issues.append(f"cast_tiger_slip.webp detB={tm['detB']} (>10) detA={tm['detA']} (>20)")

    unreadable = chroma_audit.get("unreadable", [])
    if unreadable:
        issues.append(f"{len(unreadable)} unreadable sprite(s): {unreadable[0]['file']} ({unreadable[0]['error']})")

    # Filter touched failures & hygiene relevant to this tale's cast skins AND atlas sheets/cards
    tale_skins: set[str] = set()
    tale_atlas_sheets: set[str] = set()
    tale_atlas_files: set[str] = set()
    tale_prefixes = TALE_ATLAS_PREFIXES.get(tale, ())
    if sc:
        for cfg in sc.get("cast", {}).values():
            if isinstance(cfg, dict) and cfg.get("skin"):
                tale_skins.add(cfg["skin"])
        for item in _find_sets_recursive(sc):
            cid = item.get("card")
            if not cid:
                continue
            if atlas_cat and cid in atlas_cat:
                card_rel = str(atlas_cat[cid].get("path", "")).lstrip("/")
                if card_rel:
                    tale_atlas_files.add(f"game/{card_rel}" if not card_rel.startswith("game/") else card_rel)
                    tale_atlas_sheets.add(Path(card_rel).parent.name)
            m_pfx = re.match(r"^([a-z0-9_]+?)_\d+$", cid)
            if m_pfx:
                tale_atlas_sheets.add(m_pfx.group(1))

    def _matches_tale(rel_path: str) -> bool:
        norm = rel_path.replace("\\", "/")
        if norm.startswith("game/art/cast/"):
            name = Path(norm).name
            return any(name.startswith(f"cast_{skin}_") or name == f"cast_{skin}.webp" for skin in tale_skins)
        if norm.startswith("game/art/atlas/"):
            parts = Path(norm).parts
            sheet = parts[3] if len(parts) >= 5 else ""
            return (
                norm in tale_atlas_files
                or sheet in tale_atlas_sheets
                or any(sheet.startswith(pfx) for pfx in tale_prefixes)
            )
        return False

    tale_touched = [x for x in chroma_audit["touched_failures"] if _matches_tale(x["file"])]
    other_atlas_touched = [
        x for x in chroma_audit["touched_failures"]
        if x["file"].replace("\\", "/").startswith("game/art/atlas/") and not _matches_tale(x["file"])
    ]
    if tale_touched:
        issues.append(f"{len(tale_touched)} modified tale sprite(s) have detB>10 ({tale_touched[0]['file']} detB={tale_touched[0]['detB']})")
    if other_atlas_touched:
        issues.append(f"{len(other_atlas_touched)} modified shared/other atlas sprite(s) have detB>10 ({other_atlas_touched[0]['file']} detB={other_atlas_touched[0]['detB']})")

    tale_cast_hygiene = [x for x in chroma_audit["cast_hygiene"] if _matches_tale(x["file"])]
    other_cast_hygiene = [x for x in chroma_audit["cast_hygiene"] if not _matches_tale(x["file"])]
    atlas_hygiene = chroma_audit["atlas_hygiene"]
    tale_atlas_hygiene = [x for x in atlas_hygiene if _matches_tale(x["file"])]

    if tale_cast_hygiene:
        msg = f"{len(tale_cast_hygiene)} cast sprite(s) have detB>20 (max {max(x['detB'] for x in tale_cast_hygiene)})"
        (issues if strict_chroma else warns).append(msg)
    elif strict_chroma and other_cast_hygiene:
        issues.append(f"{len(other_cast_hygiene)} global cast sprite(s) have detB>20 (max {max(x['detB'] for x in other_cast_hygiene)})")

    if atlas_hygiene:
        scope_list = tale_atlas_hygiene if (tale_atlas_hygiene and not strict_chroma) else atlas_hygiene
        label = "tale atlas" if (tale_atlas_hygiene and not strict_chroma) else "atlas"
        msg = f"{len(scope_list)} {label} sprite(s) have detB>20 (max {max(x['detB'] for x in scope_list)})"
        (issues if strict_chroma else warns).append(msg)

    if issues:
        return CheckResult(
            "T1_CHROMA_MAGENTA",
            "FAIL",
            "; ".join(issues + warns),
            {
                "tale_hygiene_count": len(tale_cast_hygiene),
                "atlas_hygiene_count": len(atlas_hygiene),
                "tale_touched_count": len(tale_touched),
                "other_atlas_touched_count": len(other_atlas_touched),
            },
        )
    if warns:
        return CheckResult(
            "T1_CHROMA_MAGENTA",
            "WARN",
            "; ".join(warns),
            {
                "tale_hygiene_count": len(tale_cast_hygiene),
                "atlas_hygiene_count": len(atlas_hygiene),
            },
        )
    return CheckResult("T1_CHROMA_MAGENTA", "PASS", "Target/modified cast & atlas sprites detB<=10 and 0 hygiene hits")


def _check_t1_set_and_bodies(
    root: Path,
    tale: str,
    sc: dict[str, Any] | None,
    atlas_cat: dict[str, dict[str, Any]],
    bodies: dict[str, Any],
    kit: dict[str, Any],
    house_bodies_src: str,
) -> CheckResult:
    if sc is None:
        return CheckResult("T1_SET_AND_BODIES", "MISSING", "script.json missing")

    issues: list[str] = []
    kit_mats = set(kit.get("materials", {}).keys())
    kit_presets = kit.get("kit", {})

    # 1 & 2: Verify spread.set[].card and spread.set[].build
    set_items = _find_sets_recursive(sc)
    tale_body_ids: set[str] = set()
    for item in set_items:
        cid = item.get("card")
        if cid:
            if cid not in atlas_cat:
                issues.append(f"unknown atlas card {cid!r}")
            else:
                cp = _resolve_game_path(root, atlas_cat[cid].get("path", ""))
                if not cp.exists():
                    issues.append(f"missing atlas webp {atlas_cat[cid].get('path')}")
            if cid in bodies:
                tale_body_ids.add(cid)
        build = item.get("build")
        if isinstance(build, dict):
            parts = build.get("parts")
            if not isinstance(parts, list) or not parts:
                issues.append(f"build {item.get('name', '?')!r} has empty parts")
            else:
                for pi, part in enumerate(parts):
                    for mk in ("mat", "roof_mat", "wall_mat"):
                        mv = part.get(mk)
                        if mv and kit_mats and mv not in kit_mats:
                            issues.append(f"build {item.get('name', '?')!r}[{pi}] unknown {mk}={mv!r}")
        kit_name = item.get("kit")
        if kit_name and kit_name not in kit_presets:
            issues.append(f"unknown kit preset {kit_name!r}")

    # Include story-specific template houses checked per tale
    if tale == "three_pigs":
        tale_body_ids.add("village_houses_01")
    if tale == "witch_candy":
        tale_body_ids.update(k for k in bodies if k.startswith("story_wc_houses_"))

    # 3: Check bodies.json entries for this tale
    for bid in sorted(tale_body_ids):
        b = bodies.get(bid)
        if not isinstance(b, dict):
            issues.append(f"missing bodies.json entry {bid!r}")
            continue
        if 1 not in b.get("mats", []):
            issues.append(f"{bid}: mat 1 (roof) missing")
        for fk in ("side_file", "back_file"):
            fv = b.get(fk)
            if not fv or not _resolve_game_path(root, fv).exists():
                issues.append(f"{bid}: missing {fk} ({fv!r})")
        rm = b.get("roof_mat")
        rf = b.get("roof_file")
        if rm:
            if kit_mats and rm not in kit_mats:
                issues.append(f"{bid}: unknown roof_mat={rm!r}")
        elif not rf or not _resolve_game_path(root, rf).exists():
            issues.append(f"{bid}: missing roof_file ({rf!r})")

        for wl in b.get("wall_lines", []):
            if isinstance(wl, list) and len(wl) >= 2:
                slope = abs(float(wl[1]))
                if slope > WALL_SLOPE_MAX:
                    issues.append(f"{bid}: steep wall_lines slope {wl[1]} (|slope| > {WALL_SLOPE_MAX})")

    # 4: Feature #5 check for village_houses_01 on three_pigs
    if tale == "three_pigs":
        vh01 = bodies.get("village_houses_01", {})
        has_tile_roof = str(vh01.get("roof_file", "")).startswith("art/buildings/tiles/") or bool(vh01.get("roof_mat"))
        has_override = bool(re.search(r'"village_houses_01"\s*:\s*\{[^}]*"roof_mat"', house_bodies_src))
        if not (has_tile_roof and has_override):
            issues.append("village_houses_01 missing terracotta roof_mat override / rebuilt tile roof in house_bodies.py & bodies.json")

    if issues:
        return CheckResult("T1_SET_AND_BODIES", "FAIL", "; ".join(issues[:6]), {"issues": issues})
    return CheckResult("T1_SET_AND_BODIES", "PASS", f"All {len(set_items)} set items and {len(tale_body_ids)} body entries valid")


def _check_t1_orbit_coverage(root: Path, tale: str) -> CheckResult:
    sh = root / "tools/story/house_orbit_all.sh"
    if not sh.exists():
        return CheckResult("T1_ORBIT_COVERAGE", "MISSING", f"missing {sh}")
    txt = sh.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'TALES="\$\{\*:-([^}]+)\}"', txt)
    default_tales = m.group(1).split() if m else []
    has_default = tale in default_tales
    has_case = bool(re.search(rf"^\s*{re.escape(tale)}\)", txt, re.M))
    if not (has_default and has_case):
        return CheckResult(
            "T1_ORBIT_COVERAGE",
            "FAIL",
            f"{tale} missing from tools/story/house_orbit_all.sh (in_default={has_default}, in_case={has_case})",
        )
    return CheckResult("T1_ORBIT_COVERAGE", "PASS", f"{tale} covered in house_orbit_all.sh")


def _check_t1_runtime_guards(root: Path) -> CheckResult:
    issues: list[str] = []

    sr = root / "game/story/story_runner.gd"
    if not sr.exists():
        issues.append("missing story_runner.gd")
    else:
        sr_txt = sr.read_text(encoding="utf-8", errors="replace")
        alive_m = re.search(r"func _alive\(\).*?(?=\nfunc |\Z)", sr_txt, re.S)
        alive_valid = bool(
            alive_m
            and "is_inside_tree()" in alive_m.group(0)
            and ("get_tree() != null" in alive_m.group(0) or "get_tree() == null" in alive_m.group(0))
        )
        m = re.search(r"func _frame\(\).*?(?=\nfunc |\Z)", sr_txt, re.S)
        if not m:
            issues.append("story_runner.gd missing func _frame()")
        else:
            body = m.group(0)
            guard_cands = [body.find("is_inside_tree()"), body.find("get_tree() == null"), body.find("get_tree() != null")]
            if alive_valid:
                guard_cands.append(body.find("_alive()"))
            pos_list = [p for p in guard_cands if p != -1]
            guard_pos = min(pos_list) if pos_list else -1
            m_await = re.search(r"await\s+(?:get_tree\(\)|tree)\.process_frame", body)
            await_pos = m_await.start() if m_await else -1
            if guard_pos == -1 or (await_pos != -1 and guard_pos > await_pos):
                issues.append("story_runner.gd _frame() lacks is_inside_tree()/get_tree()/_alive() guard before process_frame await")

    ss = root / "game/story/spread_stage.gd"
    if not ss.exists():
        issues.append("missing spread_stage.gd")
    else:
        ss_txt = ss.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"func _sky_texture\b.*?(?=\nfunc |\nstatic func |\Z)", ss_txt, re.S)
        if not m:
            issues.append("spread_stage.gd missing _sky_texture()")
        else:
            body = m.group(0)
            mw = re.search(r"var w\s*:?=\s*(\d+)", body)
            mh = re.search(r"var h\s*:?=\s*(\d+)", body)
            w_val = int(mw.group(1)) if mw else 0
            h_val = int(mh.group(1)) if mh else 0
            if w_val < 1024 or h_val < 320:
                issues.append(f"spread_stage.gd _sky_texture() resolution {w_val}x{h_val} < 1024x320")

    gl = root / "game/core/look/ground_layers.gd"
    if not gl.exists():
        issues.append("missing ground_layers.gd")
    else:
        gl_txt = gl.read_text(encoding="utf-8", errors="replace")
        if not re.search(r'@export\s+var\s+ground_style\s*:?=\s*"paper"', gl_txt):
            issues.append('ground_layers.gd default ground_style != "paper"')

    if issues:
        return CheckResult("T1_RUNTIME_GUARDS", "FAIL", "; ".join(issues), {"issues": issues})
    return CheckResult("T1_RUNTIME_GUARDS", "PASS", "StoryRunner._frame guard, _sky_texture >=1024x320, ground_style=='paper'")


def _check_t1_paper_meta(root: Path) -> CheckResult:
    bad: list[str] = []
    for sheet in SHARED_ATLAS_SHEETS:
        sp = root / "game/art/atlas" / sheet / "_slices.json"
        if not sp.exists():
            bad.append(f"{sheet}:missing")
            continue
        try:
            src = str(json.loads(sp.read_text(encoding="utf-8")).get("source", ""))
        except Exception:
            bad.append(f"{sheet}:invalid_json")
            continue
        if not src.endswith("_paper.png"):
            bad.append(f"{sheet}:{src}")
    if bad:
        return CheckResult("T1_PAPER_META", "FAIL", f"{len(bad)} shared sheet(s) not on _paper.png: {bad[:4]}", {"bad": bad})
    return CheckResult("T1_PAPER_META", "PASS", f"All {len(SHARED_ATLAS_SHEETS)} shared atlas _slices.json use *_paper.png")


def verify_tier1(
    root: Path,
    tales: list[str],
    strict: bool = False,
    strict_chroma: bool = False,
    baselines: dict[str, dict[str, Any]] | None = None,
) -> list[TierTaleResult]:
    cast_cycles, missing_cast_files = _load_cast_cycles(root)
    atlas_cat = _load_atlas_catalog(root)
    bodies_p = root / "game/art/atlas/bodies.json"
    bodies = json.loads(bodies_p.read_text(encoding="utf-8")) if bodies_p.exists() else {}
    kit_p = root / "game/art/buildings/kit.json"
    kit = json.loads(kit_p.read_text(encoding="utf-8")) if kit_p.exists() else {}
    hb_p = root / "tools/atlas/house_bodies.py"
    hb_src = hb_p.read_text(encoding="utf-8", errors="replace") if hb_p.exists() else ""

    chroma_audit = _compute_global_chroma_audit(root)
    runtime_check = _check_t1_runtime_guards(root)
    paper_check = _check_t1_paper_meta(root)

    record_lines_clean: bool | None = None
    if _git_available(root) and (root / "tools/story/record_lines.py").exists():
        r = subprocess.run(
            ["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", "tools/story/record_lines.py"],
            capture_output=True,
        )
        record_lines_clean = r.returncode == 0

    results: list[TierTaleResult] = []
    for tale in tales:
        sp = root / "game/stories" / tale / "script.json"
        sc: dict[str, Any] | None = None
        sc_err: str | None = None
        if not sp.exists():
            sc_err = f"missing {sp}"
        else:
            try:
                sc = json.loads(sp.read_text(encoding="utf-8"))
            except Exception as exc:
                sc_err = str(exc)

        checks = [
            _check_t1_script_schema(tale, sc, sc_err),
            _check_t1_audio_integrity(root, tale, sc),
            _check_t1_no_elevenlabs(root, tale, sc, record_lines_clean, baselines=baselines),
            _check_t1_cast_cycles(tale, sc, cast_cycles, missing_cast_files),
            _check_t1_chroma_magenta(tale, sc, chroma_audit, strict_chroma=strict_chroma, atlas_cat=atlas_cat),
            _check_t1_set_and_bodies(root, tale, sc, atlas_cat, bodies, kit, hb_src),
            _check_t1_orbit_coverage(root, tale),
            runtime_check,
            paper_check,
        ]
        results.append(
            TierTaleResult(
                tier=1,
                tale=tale,
                status=_aggregate_status(checks, strict=strict),
                checks=checks,
                metrics={
                    "global_cast_hygiene_gt20": len(chroma_audit["cast_hygiene"]),
                    "global_atlas_hygiene_gt20": len(chroma_audit["atlas_hygiene"]),
                    "global_touched_detb_gt10": len(chroma_audit["touched_failures"]),
                },
                artifacts={"script": str(sp)},
            )
        )
    return results


# ---------------------------------------------------------------------------
# Tier 2: 3D Building Orbit Integrity
# ---------------------------------------------------------------------------

def _discover_orbit_audit(root: Path, tale: str, orbit_dir: Path | None) -> tuple[Path | None, Path | None]:
    candidates: list[Path] = []
    if orbit_dir is not None:
        base = orbit_dir if orbit_dir.is_absolute() else (root / orbit_dir)
        candidates.append(base / tale / f"{tale}_audit.json")
    else:
        default_dir = root / "artifacts/houses/e2e" / tale / f"{tale}_audit.json"
        if default_dir.exists():
            candidates.append(default_dir)
        else:
            houses_root = root / "artifacts/houses"
            if houses_root.exists():
                found = sorted(
                    houses_root.glob(f"*/{tale}/{tale}_audit.json"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                candidates.extend(found)
    for jp in candidates:
        if jp.exists():
            return jp, jp.with_name(f"{tale}_audit.jpg")
    return None, None


def verify_tier2(
    root: Path,
    tales: list[str],
    orbit_dir: Path | None = None,
    run_orbit: bool = False,
    label: str = "e2e",
    strict: bool = False,
) -> list[TierTaleResult]:
    results: list[TierTaleResult] = []
    target_dir = orbit_dir if orbit_dir is not None else Path("artifacts/houses/e2e")
    abs_orbit_dir = target_dir if target_dir.is_absolute() else (root / target_dir)

    if run_orbit:
        missing_in_script = [t for t in tales if _check_t1_orbit_coverage(root, t).status != "PASS"]
        if missing_in_script:
            for t in tales:
                msg = (
                    f"ORBIT_SCRIPT_MISSING_TALE: {missing_in_script} missing from house_orbit_all.sh"
                    if t in missing_in_script
                    else f"Aborted --orbit due to missing tale(s) {missing_in_script} in house_orbit_all.sh"
                )
                results.append(
                    TierTaleResult(
                        tier=2,
                        tale=t,
                        status="FAIL",
                        checks=[CheckResult("T2_ORBIT_PREFLIGHT", "FAIL", msg)],
                    )
                )
            return results

        # IMPORTANT: Call house_orbit_all.sh DIRECTLY (NOT wrapped in with_godot.sh; house_orbit.sh already wraps).
        cmd = [str(root / "tools/story/house_orbit_all.sh"), str(abs_orbit_dir), label, *tales]
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
        if proc.returncode != 0:
            for t in tales:
                results.append(
                    TierTaleResult(
                        tier=2,
                        tale=t,
                        status="FAIL",
                        checks=[CheckResult("T2_ORBIT_EXEC", "FAIL", f"house_orbit_all.sh exited {proc.returncode}: {proc.stderr[-300:]}")],
                    )
                )
            return results

    for tale in tales:
        jp, jpg = _discover_orbit_audit(root, tale, target_dir if (orbit_dir is not None or run_orbit) else None)
        if jp is None or not jp.exists():
            results.append(
                TierTaleResult(
                    tier=2,
                    tale=tale,
                    status="MISSING",
                    checks=[
                        CheckResult(
                            "T2_ORBIT_ARTIFACTS",
                            "MISSING",
                            f"No <tale>_audit.json found for {tale} (checked {abs_orbit_dir / tale})",
                        )
                    ],
                )
            )
            continue

        checks: list[CheckResult] = []
        if jpg is None or not jpg.exists() or jpg.stat().st_size <= 0:
            checks.append(CheckResult("T2_ORBIT_ARTIFACTS", "FAIL", f"Missing or empty contact sheet {jpg}"))
        else:
            checks.append(CheckResult("T2_ORBIT_ARTIFACTS", "PASS", f"Found {jp.name} and {jpg.name}"))

        try:
            rep = json.loads(jp.read_text(encoding="utf-8"))
        except Exception as exc:
            checks.append(CheckResult("T2_ORBIT_SOLIDITY", "FAIL", f"Invalid audit JSON {jp}: {exc}"))
            results.append(TierTaleResult(tier=2, tale=tale, status="FAIL", checks=checks, artifacts={"audit_json": str(jp)}))
            continue

        schema_errs: list[str] = []
        red_views: list[dict[str, Any]] = []
        seam_warns: list[dict[str, Any]] = []
        max_holes = 0
        total_holes = 0

        if not isinstance(rep, dict) or not rep:
            schema_errs.append("top-level audit JSON is empty or not an object")
        else:
            for house, views in rep.items():
                if not isinstance(views, dict):
                    schema_errs.append(f"{house}: not an object")
                    continue
                missing_v = [v for v in ORBIT_VIEWS if v not in views]
                if missing_v:
                    schema_errs.append(f"{house}: missing views {missing_v}")
                    continue
                for v in ORBIT_VIEWS:
                    vd = views[v]
                    if not isinstance(vd, dict):
                        schema_errs.append(f"{house}.{v}: not an object")
                        continue
                    hp = vd.get("holes_px")
                    area = vd.get("house_px")
                    frac = vd.get("frac")
                    if not isinstance(hp, int) or hp < 0:
                        schema_errs.append(f"{house}.{v}: invalid holes_px={hp!r}")
                        continue
                    if not isinstance(area, int) or area <= 0:
                        schema_errs.append(f"{house}.{v}: invalid house_px={area!r}")
                    if not isinstance(frac, (int, float)):
                        schema_errs.append(f"{house}.{v}: invalid frac={frac!r}")
                    total_holes += hp
                    max_holes = max(max_holes, hp)
                    if hp > ORBIT_MAX_HOLES_PX:
                        red_views.append({"house": house, "view": v, "holes_px": hp})
                    elif hp > 0:
                        seam_warns.append({"house": house, "view": v, "holes_px": hp})

        if schema_errs or red_views:
            parts = []
            if schema_errs:
                parts.append(f"schema errors: {schema_errs[:3]}")
            if red_views:
                parts.append(f"red={len(red_views)} view(s) > {ORBIT_MAX_HOLES_PX}px ({red_views[:4]})")
            checks.append(
                CheckResult(
                    "T2_ORBIT_SOLIDITY",
                    "FAIL",
                    "; ".join(parts),
                    {"red_views": red_views, "max_holes_px": max_holes, "total_holes_px": total_holes},
                )
            )
        elif seam_warns and strict:
            checks.append(
                CheckResult(
                    "T2_ORBIT_SOLIDITY",
                    "FAIL",
                    f"--strict: {len(seam_warns)} view(s) have 1..{ORBIT_MAX_HOLES_PX}px seams (max={max_holes})",
                    {"seam_warns": seam_warns, "max_holes_px": max_holes, "total_holes_px": total_holes},
                )
            )
        else:
            checks.append(
                CheckResult(
                    "T2_ORBIT_SOLIDITY",
                    "PASS",
                    f"red=0 across {len(rep)} house(s) (max_holes_px={max_holes}, total_holes_px={total_holes})",
                    {"red_views": [], "max_holes_px": max_holes, "total_holes_px": total_holes},
                )
            )

        results.append(
            TierTaleResult(
                tier=2,
                tale=tale,
                status=_aggregate_status(checks, strict=strict),
                checks=checks,
                metrics={"houses": len(rep) if isinstance(rep, dict) else 0, "red_count": len(red_views), "max_holes_px": max_holes, "total_holes_px": total_holes},
                artifacts={"audit_json": str(jp), "audit_jpg": str(jpg)},
            )
        )
    return results


# ---------------------------------------------------------------------------
# Tier 3 & Tier 4 Shared Discovery & Parsers
# ---------------------------------------------------------------------------

def parse_gate_md(gate_path: Path) -> dict[str, Any]:
    text = gate_path.read_text(encoding="utf-8", errors="replace")
    m_run = re.search(r"^run:\s*(\S+)\s+([0-9a-f]{10})\s*$", text, re.M)
    m_vid = re.search(r"^video:\s*(.+?)\s*$", text, re.M)
    m_sheets = re.search(r"^Contact sheets \(every 2\.5 s\):\s*(.+?)\s*$", text, re.M)
    sheets = [s.strip() for s in m_sheets.group(1).split(",") if s.strip()] if m_sheets else []

    # Parse ## Visual checklist only (before next ## heading)
    checklist: dict[str, bool] = {}
    duplicate_keys: list[str] = []
    vc_sec = ""
    if "## Visual checklist" in text:
        after_vc = text.split("## Visual checklist", 1)[1]
        vc_sec = re.split(r"\n##\s+", after_vc, maxsplit=1)[0]
    for ln in vc_sec.splitlines():
        m = re.match(r"^\s*-\s*\[(x|X| )\]\s*(\w+)\s*:", ln)
        if m:
            key = m.group(2)
            ticked = m.group(1).lower() == "x"
            if key in checklist:
                duplicate_keys.append(key)
            checklist[key] = ticked

    # Parse ALL ## Accepted exceptions sections strictly (detect duplicate headings)
    exceptions: dict[str, str] = {}
    bad_exception_lines: list[str] = []
    forbidden_exceptions: list[str] = []
    ex_headers = list(re.finditer(r"^##\s+Accepted exceptions\b[^\n]*$", text, re.M))
    for hm in ex_headers:
        start = hm.end()
        next_h = re.search(r"^##\s+", text[start:], re.M)
        ex_sec = text[start : start + next_h.start()] if next_h else text[start:]
        for ln in ex_sec.splitlines():
            s = ln.strip()
            if not s or s.startswith("<!--"):
                continue
            m = EXCEPTION_LINE_RE.match(ln)
            if not m:
                bad_exception_lines.append(s)
                continue
            eid = m.group(1).strip()
            reason = m.group(2).strip()
            if len(reason) < 10:
                bad_exception_lines.append(s)
                continue
            base_id = eid.split()[0]
            if base_id in FORBIDDEN_EXCEPTION_IDS or eid in FORBIDDEN_EXCEPTION_IDS:
                forbidden_exceptions.append(eid)
            elif not EXCEPTION_STRICT_ID_RE.match(eid):
                forbidden_exceptions.append(eid)
            exceptions[eid] = reason

    return {
        "run_name": m_run.group(1) if m_run else None,
        "run_sha1": m_run.group(2) if m_run else None,
        "video": m_vid.group(1).strip() if m_vid else None,
        "sheets": sheets,
        "checklist": checklist,
        "duplicate_keys": duplicate_keys,
        "exceptions": exceptions,
        "bad_exception_lines": bad_exception_lines,
        "forbidden_exceptions": forbidden_exceptions,
        "duplicate_exception_sections": len(ex_headers) > 1,
        "exception_section_count": len(ex_headers),
    }


def _find_log_by_name(root: Path, tale: str, name: str) -> Path | None:
    for cand in (root / "artifacts" / tale / "rec" / name, root / "artifacts" / tale / name):
        if cand.exists():
            return cand
    found = list((root / "artifacts" / tale).rglob(name)) if (root / "artifacts" / tale).exists() else []
    return found[0] if found else None


def discover_log_and_mp4(
    root: Path,
    tale: str,
    log_override: Path | None = None,
    mp4_override: Path | None = None,
) -> tuple[Path | None, Path | None]:
    if log_override is not None or mp4_override is not None:
        lp = (log_override if log_override.is_absolute() else root / log_override) if log_override else None
        mp = (mp4_override if mp4_override.is_absolute() else root / mp4_override) if mp4_override else None
        if lp is not None and mp is None:
            gp = root / "artifacts" / tale / "gate.md"
            if gp.exists():
                gd = parse_gate_md(gp)
                if gd["video"]:
                    mp = Path(gd["video"])
                    if not mp.is_absolute():
                        mp = root / mp
        return lp, mp

    gp = root / "artifacts" / tale / "gate.md"
    if gp.exists():
        gd = parse_gate_md(gp)
        lp = _find_log_by_name(root, tale, gd["run_name"]) if gd["run_name"] else None
        mp: Path | None = None
        if gd["video"]:
            vp = Path(gd["video"])
            if vp.exists():
                mp = vp
            else:
                # Fallback if gate.md recorded another checkout's absolute path
                alt = root / "artifacts/video" / vp.name
                if alt.exists():
                    mp = alt
                else:
                    mp = vp
        return lp, mp

    # Fallback if gate.md is absent
    rec_dir = root / "artifacts" / tale / "rec"
    lp = None
    if rec_dir.exists():
        logs = sorted(
            [p for p in rec_dir.glob("*.log") if "import" not in p.name],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for cand in logs:
            if "STORY_DONE" in cand.read_text(errors="replace"):
                lp = cand
                break
        if lp is None and logs:
            lp = logs[0]
    mp = None
    vid_dir = root / "artifacts/video"
    if vid_dir.exists():
        vids = sorted(vid_dir.glob(f"{tale}_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if vids:
            mp = vids[0]
    if mp is None and rec_dir.exists():
        vids = sorted(rec_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if vids:
            mp = vids[0]
    return lp, mp


def probe_video(mp4_path: Path) -> tuple[int, int, float]:
    res = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height:format=duration",
            "-of",
            "json",
            str(mp4_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    j = json.loads(res.stdout)
    st = j["streams"][0]
    return int(st["width"]), int(st["height"]), float(j["format"]["duration"])


def _record_tale(root: Path, tale: str, tag: str, run_gate: bool) -> tuple[Path | None, Path | None, str | None]:
    godot_bin = os.environ.get("GODOT_BIN", "/Applications/Godot.app/Contents/MacOS/Godot")
    with_godot = root / "tools/story/with_godot.sh"
    rec_dir = root / "artifacts" / tale / "rec"
    vid_dir = root / "artifacts/video"
    rec_dir.mkdir(parents=True, exist_ok=True)
    vid_dir.mkdir(parents=True, exist_ok=True)

    imp_log = rec_dir / f"{tag}_import.log"
    run_log = rec_dir / f"{tag}.log"
    avi_path = rec_dir / f"{tag}.avi"
    mp4_path = vid_dir / f"{tale}_{tag}.mp4"

    r_imp = subprocess.run(
        [str(with_godot), godot_bin, "--headless", "--path", str(root / "game"), "--import"],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    imp_log.write_text(r_imp.stdout + r_imp.stderr, encoding="utf-8")

    try:
        r_rec = subprocess.run(
            [
                str(with_godot),
                godot_bin,
                "--path",
                str(root / "game"),
                "--resolution",
                f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}",
                "--fixed-fps",
                "30",
                "--write-movie",
                str(avi_path),
                "--",
                f"--tale={tale}",
                "--autoplay",
                "--quit-on-done",
                "--log-sound",
                "--log-track",
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=900,
        )
        run_log.write_text(r_rec.stdout + r_rec.stderr, encoding="utf-8")
    except subprocess.TimeoutExpired as exc:
        run_log.write_text((exc.stdout or "") + (exc.stderr or ""), encoding="utf-8")
        return run_log, None, "Godot recording timed out after 900s"

    if not avi_path.exists():
        return run_log, None, f"Godot did not produce {avi_path}"

    r_ff = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(avi_path),
            "-c:v",
            "libx264",
            "-crf",
            "24",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(mp4_path),
        ],
        capture_output=True,
        text=True,
    )
    if avi_path.exists():
        avi_path.unlink()
    if r_ff.returncode != 0 or not mp4_path.exists():
        return run_log, None, f"ffmpeg transcode failed: {r_ff.stderr}"

    if run_gate:
        subprocess.run(
            [sys.executable, str(root / "tools/story/gate.py"), tale, str(run_log), str(mp4_path)],
            cwd=str(root),
            capture_output=True,
            text=True,
        )

    return run_log, mp4_path, None


def _in_memory_motion_flags(root: Path, tale: str, log_text: str) -> tuple[int, list[dict[str, Any]], int]:
    """Run motion_review flag detection strictly in-memory (0 files written)."""
    segs = _mr.parse_moves(log_text)
    tr = _mr.parse_track(log_text)
    if not segs:
        return 0, [], 0

    cat_path = root / "game/art/cast/catalog.json"
    cat: dict[str, dict[str, str]] = defaultdict(dict)
    if cat_path.exists():
        d = json.loads(cat_path.read_text(encoding="utf-8"))
        arr = d if isinstance(d, list) else d.get("cards", [])
        for e in arr:
            if "cycle" in e:
                cat[e.get("skin", "")][e["cycle"]] = e.get("view", "side")

    caps = _mr.parse_captions(log_text)
    m = re.search(r"^TRACK_VP (\d+)x(\d+)", log_text, re.M)
    vp = (float(m.group(1)), float(m.group(2))) if m else (1366.0, 1024.0)

    flagged: list[dict[str, Any]] = []
    for idx, s in enumerate(segs, 1):
        fl = _mr.flags_for(s, cat, tr, vp, caps)
        if fl:
            flagged.append({"seg": f"{idx:02d}", "role": s["role"], "flags": [k for k, _ in fl]})
    return len(segs), flagged, sum(len(x["flags"]) for x in flagged)


def verify_tier3(
    root: Path,
    tales: list[str],
    record: bool = False,
    tag: str = "e2e_v1",
    log_override: Path | None = None,
    mp4_override: Path | None = None,
    run_gate: bool = False,
    strict: bool = False,
    video_probe_fn: Callable[[Path], tuple[int, int, float]] | None = None,
) -> tuple[list[TierTaleResult], dict[str, tuple[Path | None, Path | None]]]:
    probe_fn = video_probe_fn or probe_video
    results: list[TierTaleResult] = []
    log_mp4_map: dict[str, tuple[Path | None, Path | None]] = {}

    for tale in tales:
        checks: list[CheckResult] = []
        if record:
            lp, mp, rec_err = _record_tale(root, tale, tag, run_gate=run_gate)
            if rec_err:
                log_mp4_map[tale] = (lp, mp)
                checks.append(CheckResult("T3_RECORD", "FAIL", rec_err))
                results.append(TierTaleResult(tier=3, tale=tale, status="FAIL", checks=checks))
                continue
        else:
            lp, mp = discover_log_and_mp4(root, tale, log_override=log_override, mp4_override=mp4_override)
            if run_gate and lp and mp and lp.exists() and mp.exists():
                subprocess.run(
                    [sys.executable, str(root / "tools/story/gate.py"), tale, str(lp), str(mp), "--no-tiles"],
                    cwd=str(root),
                    capture_output=True,
                    text=True,
                )

        log_mp4_map[tale] = (lp, mp)
        if lp is None or not lp.exists():
            checks.append(CheckResult("T3_RUN_COMPLETENESS", "MISSING", f"No run log found for {tale}"))
            results.append(TierTaleResult(tier=3, tale=tale, status="MISSING", checks=checks))
            continue

        text = lp.read_text(encoding="utf-8", errors="replace")

        # Load gate.md accepted exceptions ONLY when gate.md matches this exact log name & sha1[:10]
        gp = root / "artifacts" / tale / "gate.md"
        accepted_ex: dict[str, str] = {}
        if gp.exists():
            ginfo = parse_gate_md(gp)
            if (
                not ginfo.get("duplicate_exception_sections")
                and ginfo.get("run_name") == lp.name
                and ginfo.get("run_sha1") == _sha1_10(lp)
            ):
                accepted_ex = ginfo.get("exceptions", {})

        # 1. T3_RUN_COMPLETENESS
        comp_issues: list[str] = []
        story_m = re.search(
            rf"^STORY {re.escape(tale)}\b.*?autoplay=(\S+)\s+start=(.*)$",
            text,
            re.M,
        )
        if not story_m:
            comp_issues.append(f"missing 'STORY {tale} ... autoplay=... start=' banner")
        else:
            if story_m.group(1).strip() != "true":
                comp_issues.append(f"autoplay={story_m.group(1).strip()} (expected true)")
            if story_m.group(2).strip() != "":
                comp_issues.append(f"start={story_m.group(2).strip()!r} (expected empty full-tale run)")

        done_m = re.search(
            r"^STORY_DONE total=(\d+(?:\.\d+)?) missing_audio=(\[[^\]]*\]) missing_sound=(\[[^\]]*\]) beats=(\{.*\})",
            text,
            re.M,
        )
        if not done_m:
            comp_issues.append("STORY_DONE line missing or malformed")

        move_count = len(re.findall(r"^MOVE ", text, re.M))
        track_count = len(re.findall(r"^TRACK ", text, re.M))
        if move_count < 1:
            comp_issues.append(f"MOVE count={move_count} (< 1)")
        if track_count < 1:
            comp_issues.append(f"TRACK count={track_count} (< 1, missing --log-track?)")

        if comp_issues:
            checks.append(
                CheckResult(
                    "T3_RUN_COMPLETENESS",
                    "FAIL",
                    "; ".join(comp_issues),
                    {"move_count": move_count, "track_count": track_count},
                )
            )
        else:
            checks.append(
                CheckResult(
                    "T3_RUN_COMPLETENESS",
                    "PASS",
                    f"Full autoplay run with STORY_DONE, MOVE={move_count}, TRACK={track_count}",
                    {"move_count": move_count, "track_count": track_count},
                )
            )

        # 2. T3_BEATS_TIMING (catches patjuk_gate_v1b 905s prebuild stall)
        story_total: float | None = None
        timing_issues: list[str] = []
        max_beat_gap = 0.0
        if not done_m:
            timing_issues.append("cannot verify beat timing without STORY_DONE")
        else:
            story_total = float(done_m.group(1))
            if story_total < MIN_TOTAL_SEC or story_total > MAX_TOTAL_SEC:
                timing_issues.append(f"STORY_DONE total={story_total:.1f}s outside [{MIN_TOTAL_SEC:.0f}, {MAX_TOTAL_SEC:.0f}]s")
            try:
                beats_dict = json.loads(done_m.group(4))
                sorted_beats = sorted(((str(k), float(v)) for k, v in beats_dict.items()), key=lambda kv: kv[1])
                for (b0, t0), (b1, t1) in zip(sorted_beats, sorted_beats[1:]):
                    dt = t1 - t0
                    max_beat_gap = max(max_beat_gap, dt)
                    if dt > MAX_BEAT_GAP_SEC:
                        timing_issues.append(f"beat gap {b0}->{b1} = {dt:.1f}s (> {MAX_BEAT_GAP_SEC:.0f}s stall)")
                if sorted_beats:
                    tail_dt = story_total - sorted_beats[-1][1]
                    max_beat_gap = max(max_beat_gap, tail_dt)
                    if tail_dt > MAX_BEAT_GAP_SEC:
                        timing_issues.append(f"final beat {sorted_beats[-1][0]}->end = {tail_dt:.1f}s (> {MAX_BEAT_GAP_SEC:.0f}s)")
            except Exception as exc:
                timing_issues.append(f"invalid beats JSON in STORY_DONE: {exc}")

        # PERF spread_prebuilt guard
        for pm in re.finditer(r"^PERF spread_prebuilt (\S+) frames=(\d+) max_slice_ms=(\d+(?:\.\d+)?) phases=(\{[^}]*\})", text, re.M):
            key = pm.group(1)
            frames_n = int(pm.group(2))
            try:
                phases = json.loads(pm.group(4))
                phases_sec = sum(float(v) for v in phases.values()) / 1000.0
            except Exception:
                phases_sec = 0.0
            wall_est_sec = frames_n / 30.0
            if max(phases_sec, wall_est_sec) > MAX_PREBUILT_SEC:
                timing_issues.append(f"PERF spread_prebuilt {key} exceeded {MAX_PREBUILT_SEC:.0f}s (phases={phases_sec:.1f}s, frames={frames_n})")

        if timing_issues:
            checks.append(
                CheckResult(
                    "T3_BEATS_TIMING",
                    "FAIL",
                    "; ".join(timing_issues),
                    {"total_s": story_total, "max_beat_gap_s": max_beat_gap},
                )
            )
        else:
            checks.append(
                CheckResult(
                    "T3_BEATS_TIMING",
                    "PASS",
                    f"total={story_total:.1f}s, max_beat_gap={max_beat_gap:.1f}s",
                    {"total_s": story_total, "max_beat_gap_s": max_beat_gap},
                )
            )

        # 3. T3_VIDEO_INTEGRITY
        mp4_dur: float | None = None
        if mp is None or not mp.exists():
            checks.append(CheckResult("T3_VIDEO_INTEGRITY", "MISSING", f"MP4 missing ({mp})"))
        else:
            try:
                w, h, mp4_dur = probe_fn(mp)
                v_issues: list[str] = []
                if w != EXPECTED_WIDTH or h != EXPECTED_HEIGHT:
                    v_issues.append(f"resolution {w}x{h} != {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
                if story_total is not None and abs(mp4_dur - story_total) > MAX_MP4_LOG_DIFF_SEC:
                    v_issues.append(f"|mp4_dur({mp4_dur:.1f}s) - log_total({story_total:.1f}s)| > {MAX_MP4_LOG_DIFF_SEC:.0f}s")
                if v_issues:
                    checks.append(CheckResult("T3_VIDEO_INTEGRITY", "FAIL", "; ".join(v_issues), {"width": w, "height": h, "duration": mp4_dur}))
                else:
                    checks.append(CheckResult("T3_VIDEO_INTEGRITY", "PASS", f"{w}x{h}, duration={mp4_dur:.1f}s", {"width": w, "height": h, "duration": mp4_dur}))
            except Exception as exc:
                checks.append(CheckResult("T3_VIDEO_INTEGRITY", "FAIL", f"ffprobe failed: {exc}"))

        # 4. T3_CHECK_LINES
        check_lines_py = root / "tools/story/check_lines.py"
        if not check_lines_py.exists():
            check_lines_py = REPO_ROOT / "tools/story/check_lines.py"
        cl = subprocess.run([sys.executable, str(check_lines_py), tale, str(lp)], capture_output=True, text=True)
        cl_out = (cl.stdout + cl.stderr).strip().splitlines()
        cl_summary = cl_out[-1] if cl_out else "check_lines: no output"
        if cl.returncode != 0:
            checks.append(CheckResult("T3_CHECK_LINES", "FAIL", cl_summary, {"output": cl_out[:10]}))
        else:
            checks.append(CheckResult("T3_CHECK_LINES", "PASS", cl_summary))

        # 5. T3_ENGINE_ERRORS (ZERO tolerance — CANNOT be waived)
        err_issues: list[str] = []
        n_script_err = len(re.findall(r"SCRIPT ERROR", text))
        n_failed_load = len(re.findall(r"Failed loading", text))
        n_null_tree = len(re.findall(r'Parameter "data\.tree" is null', text))
        mid_errors = [
            ln for ln in text.splitlines()
            if ln.startswith("ERROR:") and not re.match(r"^ERROR:\s*\d+\s+resources still in use at exit", ln)
        ]
        if n_script_err:
            err_issues.append(f"SCRIPT ERROR={n_script_err}")
        if n_failed_load:
            err_issues.append(f"Failed loading={n_failed_load}")
        if n_null_tree:
            err_issues.append(f'Parameter "data.tree" is null={n_null_tree}')
        if mid_errors:
            err_issues.append(f"mid-run ERROR lines={len(mid_errors)}")

        for key in ("missing_audio", "missing_sound"):
            ms = re.findall(key + r"=(\[[^\]]*\])", text)
            if not ms:
                err_issues.append(f"{key} not printed")
            elif ms[-1].strip() != "[]":
                err_issues.append(f"{key}={ms[-1]}")

        for cname in ("VOICE_DUP", "CAM_JUMP", "CAM_JERK", "SPEAKER_OFF"):
            ms = re.findall(rf"{cname}=(\d+)", text)
            if not ms:
                err_issues.append(f"{cname} not printed")
            elif int(ms[-1]) != 0:
                err_issues.append(f"{cname}={ms[-1]}")

        if "BLACK_LIPS" in text:
            ms = re.findall(r"BLACK_LIPS frames-with-wrong-variant=(\d+)", text)
            if not ms:
                err_issues.append("BLACK_LIPS counter malformed")
            elif int(ms[-1]) != 0:
                err_issues.append(f"BLACK_LIPS={ms[-1]}")

        if err_issues:
            checks.append(CheckResult("T3_ENGINE_ERRORS", "FAIL", "; ".join(err_issues), {"issues": err_issues}))
        else:
            checks.append(CheckResult("T3_ENGINE_ERRORS", "PASS", "0 engine/audio/camera errors"))

        # 6. T3_STAGE_COUNTERS (OVERLAP_COUNT, OCCLUDE_COUNT, SET_CHECK, in-memory MOTION_FLAGS)
        stage_fails: list[str] = []
        stage_accepted: list[str] = []
        for pat, cname in ((r"OVERLAP_COUNT (\d+)", "OVERLAP_COUNT"), (r"OCCLUDE_COUNT (\d+)", "OCCLUDE_COUNT")):
            ms = re.findall(pat, text)
            if not ms:
                stage_fails.append(f"{cname} not printed (overlap_check off?)")
            else:
                v = int(ms[-1])
                if v != 0:
                    if not strict and cname in accepted_ex:
                        stage_accepted.append(f"{cname}={v} (accepted)")
                    else:
                        stage_fails.append(f"{cname}={v}")

        bad_sets: dict[str, str] = {}
        for m in re.finditer(r"^SET_CHECK (\S+) road=(\d+) water=(\d+)", text, re.M):
            if int(m.group(2)) or int(m.group(3)):
                bad_sets[m.group(1)] = f"road={m.group(2)} water={m.group(3)}"
        for sname, desc in sorted(bad_sets.items()):
            ex_id = f"SET_CHECK {sname}"
            if not strict and ex_id in accepted_ex:
                stage_accepted.append(f"{ex_id} {desc} (accepted)")
            else:
                stage_fails.append(f"{ex_id} {desc}")

        seg_count, flagged_segs, total_mflags = _in_memory_motion_flags(root, tale, text)
        for item in flagged_segs:
            ex_id = f"MOTION_FLAG {item['seg']}"
            desc = f"{ex_id} ({','.join(item['flags'])})"
            if not strict and ex_id in accepted_ex:
                stage_accepted.append(f"{desc} (accepted)")
            else:
                stage_fails.append(desc)

        if stage_fails:
            checks.append(
                CheckResult(
                    "T3_STAGE_COUNTERS",
                    "FAIL",
                    "; ".join(stage_fails[:6]),
                    {"fails": stage_fails, "accepted": stage_accepted, "motion_flags": total_mflags},
                )
            )
        else:
            msg = f"Stage/motion counters clean (segments={seg_count}, motion_flags={total_mflags})"
            if stage_accepted:
                msg += f"; accepted: {', '.join(stage_accepted)}"
            checks.append(
                CheckResult(
                    "T3_STAGE_COUNTERS",
                    "PASS",
                    msg,
                    {"accepted": stage_accepted, "motion_flags": total_mflags},
                )
            )

        results.append(
            TierTaleResult(
                tier=3,
                tale=tale,
                status=_aggregate_status(checks, strict=strict),
                checks=checks,
                metrics={
                    "total_s": story_total,
                    "mp4_dur_s": mp4_dur,
                    "move_count": move_count,
                    "track_count": track_count,
                    "motion_flags": total_mflags,
                },
                artifacts={"log": str(lp), "mp4": str(mp) if mp else None},
            )
        )
    return results, log_mp4_map


# ---------------------------------------------------------------------------
# Tier 4: Visual Contact Sheet & Motion Tile Audit
# ---------------------------------------------------------------------------

def verify_tier4(
    root: Path,
    tales: list[str],
    log_mp4_map: dict[str, tuple[Path | None, Path | None]] | None = None,
    strict: bool = False,
) -> list[TierTaleResult]:
    results: list[TierTaleResult] = []
    for tale in tales:
        checks: list[CheckResult] = []
        art_dir = root / "artifacts" / tale
        gp = art_dir / "gate.md"
        mp_md = art_dir / "motion/motion_review.md"

        lp, mp4_p = (log_mp4_map or {}).get(tale, (None, None))
        if lp is None:
            lp, mp4_p = discover_log_and_mp4(root, tale)

        expected_rid = f"{lp.name} {_sha1_10(lp)}" if (lp is not None and lp.exists()) else None

        # 1. T4_GATE_MD
        if not gp.exists():
            checks.append(CheckResult("T4_GATE_MD", "MISSING", f"missing {gp}"))
            g_exceptions: dict[str, str] = {}
        else:
            gd = parse_gate_md(gp)
            gate_fresh = (
                not gd.get("duplicate_exception_sections")
                and (not expected_rid or f"{gd['run_name']} {gd['run_sha1']}" == expected_rid)
            )
            g_exceptions = gd["exceptions"] if gate_fresh else {}
            g_issues: list[str] = []

            if not gd["run_name"] or not gd["run_sha1"]:
                g_issues.append("missing/malformed 'run:' header")
            elif expected_rid and f"{gd['run_name']} {gd['run_sha1']}" != expected_rid:
                g_issues.append(f"stale gate.md run={gd['run_name']} {gd['run_sha1']} != {expected_rid}")
            else:
                # Verify referenced log exists & sha1 matches
                ref_log = lp if (lp and lp.exists()) else _find_log_by_name(root, tale, gd["run_name"])
                if ref_log is None or not ref_log.exists():
                    g_issues.append(f"referenced log {gd['run_name']} missing")
                elif _sha1_10(ref_log) != gd["run_sha1"]:
                    g_issues.append(f"log sha1 mismatch ({_sha1_10(ref_log)} != {gd['run_sha1']})")

            if not gd["video"]:
                g_issues.append("missing 'video:' header")
            else:
                gv = Path(gd["video"])
                if not gv.is_absolute():
                    gv = root / gv
                if mp4_p is not None and gv.name != mp4_p.name:
                    g_issues.append(f"video mismatch ({gv.name} != {mp4_p.name})")
                if not gv.exists() and not (root / "artifacts/video" / gv.name).exists():
                    g_issues.append(f"referenced video missing ({gv})")

            if not gd["sheets"]:
                g_issues.append("no gate_contact_*.jpg listed")
            else:
                missing_sheets = [
                    s for s in gd["sheets"]
                    if not (art_dir / s).exists() or (art_dir / s).stat().st_size <= 0
                ]
                if missing_sheets:
                    g_issues.append(f"missing/empty contact sheet(s): {missing_sheets[:5]}")

            missing_keys = [k for k in VISUAL_KEYS if k not in gd["checklist"]]
            unticked = [k for k in VISUAL_KEYS if gd["checklist"].get(k) is False]
            if missing_keys:
                g_issues.append(f"missing visual checklist key(s): {missing_keys}")
            if gd["duplicate_keys"]:
                g_issues.append(f"duplicate visual checklist key(s): {gd['duplicate_keys']}")
            if unticked:
                g_issues.append(f"unticked visual checklist item(s): {unticked}")

            if gd.get("duplicate_exception_sections"):
                g_issues.append("duplicate ## Accepted exceptions section in gate.md")
            if gd["bad_exception_lines"]:
                g_issues.append(f"malformed Accepted exceptions line(s): {gd['bad_exception_lines'][:3]}")
            if gd["forbidden_exceptions"]:
                g_issues.append(f"forbidden/non-allowlisted Accepted exceptions ID(s): {gd['forbidden_exceptions']}")
            if strict and g_exceptions:
                g_issues.append(f"--strict forbids Accepted exceptions ({list(g_exceptions.keys())})")

            if g_issues:
                checks.append(CheckResult("T4_GATE_MD", "FAIL", "; ".join(g_issues), {"issues": g_issues}))
            else:
                checks.append(CheckResult("T4_GATE_MD", "PASS", f"7/7 visual checks [x], {len(gd['sheets'])} contact sheet(s), hash match"))

        # 2. T4_MOTION_REVIEW
        if not mp_md.exists():
            checks.append(CheckResult("T4_MOTION_REVIEW", "MISSING", f"missing {mp_md}"))
        else:
            mtxt = mp_md.read_text(encoding="utf-8", errors="replace")
            m_issues: list[str] = []

            mm_run = re.search(r"^run:\s*(\S+)\s+([0-9a-f]{10})\s*$", mtxt, re.M)
            if not mm_run:
                m_issues.append("missing/malformed 'run:' header in motion_review.md")
            elif expected_rid and f"{mm_run.group(1)} {mm_run.group(2)}" != expected_rid:
                m_issues.append(f"stale motion_review.md run={mm_run.group(1)} {mm_run.group(2)} != {expected_rid}")

            rows = []
            for ln in mtxt.splitlines():
                if re.match(r"^\|\s*\d+\s*\|", ln):
                    c = [x.strip() for x in ln.strip().strip("|").split("|")]
                    rows.append(c)

            log_flags_by_seg: dict[str, list[str]] = {}
            if lp is not None and lp.exists():
                log_text = lp.read_text(encoding="utf-8", errors="replace")
                expected_moves, log_flagged_list, _ = _in_memory_motion_flags(root, tale, log_text)
                log_flags_by_seg = {item["seg"]: item["flags"] for item in log_flagged_list}
                if expected_moves == 0:
                    m_issues.append(f"0 MOVE lines in {lp.name} (expected >= 1; TRACK-only motion_review not accepted)")
                elif rows and len(rows) != expected_moves:
                    m_issues.append(f"row count {len(rows)} != parse_moves count {expected_moves}")

            if not rows:
                m_issues.append("0 segment rows in motion_review.md")

            non_ok: list[str] = []
            missing_tiles: list[str] = []
            wiped_flags: list[str] = []
            bad_flagged_notes: list[str] = []
            unaccepted_flags: list[str] = []
            for c in rows:
                seg_num = c[0].zfill(2) if c and c[0].isdigit() else (c[0] if c else "?")
                flags_cell = c[6] if len(c) > 6 else "-"
                tiles_cell = c[7] if len(c) > 7 else ""
                verdict = c[8].lower() if len(c) > 8 else ""
                note = c[9] if len(c) > 9 else ""
                if verdict != "ok":
                    non_ok.append(f"{seg_num}:{verdict or 'empty'}")
                for tf in tiles_cell.split():
                    tp = mp_md.parent / tf
                    if not tp.exists() or tp.stat().st_size <= 0:
                        missing_tiles.append(tf)
                log_flags = log_flags_by_seg.get(seg_num, [])
                if log_flags and flags_cell == "-":
                    wiped_flags.append(f"{seg_num}({','.join(log_flags)})")
                if flags_cell != "-" or log_flags:
                    if len(note) < 4:
                        bad_flagged_notes.append(seg_num)
                    ex_id = f"MOTION_FLAG {seg_num}"
                    if ex_id not in g_exceptions:
                        unaccepted_flags.append(ex_id)
                    elif strict:
                        unaccepted_flags.append(f"{ex_id}(strict)")

            if non_ok:
                m_issues.append(f"{len(non_ok)} non-ok row(s): {non_ok[:6]}")
            if missing_tiles:
                m_issues.append(f"{len(missing_tiles)} missing/empty tile(s): {missing_tiles[:4]}")
            if wiped_flags:
                m_issues.append(f"wiped flags='-' for log-flagged segment(s): {wiped_flags}")
            if bad_flagged_notes:
                m_issues.append(f"flagged row(s) missing >=4-char note: {bad_flagged_notes}")
            if unaccepted_flags:
                m_issues.append(f"flagged row(s) missing Accepted exception in gate.md: {unaccepted_flags}")

            if m_issues:
                checks.append(CheckResult("T4_MOTION_REVIEW", "FAIL", "; ".join(m_issues), {"rows": len(rows), "issues": m_issues}))
            else:
                checks.append(CheckResult("T4_MOTION_REVIEW", "PASS", f"{len(rows)}/{len(rows)} rows ok, tiles present, hash match"))

        results.append(
            TierTaleResult(
                tier=4,
                tale=tale,
                status=_aggregate_status(checks, strict=strict),
                checks=checks,
                artifacts={"gate_md": str(gp), "motion_review_md": str(mp_md)},
            )
        )
    return results


# ---------------------------------------------------------------------------
# Reporting & CLI
# ---------------------------------------------------------------------------

def _build_payload(results: list[TierTaleResult], tiers: list[int], tales: list[str], mode: str) -> dict[str, Any]:
    overall = "PASS"
    for r in results:
        if r.status == "FAIL":
            overall = "FAIL"
            break
        if r.status == "MISSING":
            overall = "MISSING"
    counts = defaultdict(int)
    for r in results:
        counts[r.status] += 1
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": mode,
        "tiers": tiers,
        "tales": tales,
        "overall": overall,
        "counts": dict(counts),
        "results": [
            {
                "tier": r.tier,
                "tale": r.tale,
                "status": r.status,
                "checks": [asdict(c) for c in r.checks],
                "metrics": r.metrics,
                "artifacts": r.artifacts,
            }
            for r in results
        ],
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# popup-atlas E2E Verification Report ({payload['generated_at']})",
        "",
        f"- **Mode**: `{payload['mode']}`",
        f"- **Tiers**: `{payload['tiers']}`",
        f"- **Overall**: **{payload['overall']}** (`{payload['counts']}`)",
        "",
        "| Tier | Tale | Status | Summary |",
        "|---|---|---|---|",
    ]
    for r in payload["results"]:
        bad = [f"{c['id']}({c['status']}): {c['message']}" for c in r["checks"] if c["status"] != "PASS"]
        summary = " | ".join(bad) if bad else "All checks passed"
        lines.append(f"| Tier {r['tier']} | `{r['tale']}` | **{r['status']}** | {summary} |")
    lines.append("")
    return "\n".join(lines)


def _print_console(payload: dict[str, Any]) -> None:
    print(f"=== popup-atlas E2E Verification ({payload['mode']}) :: OVERALL {payload['overall']} ===")
    for r in payload["results"]:
        print(f"[T{r['tier']}] {r['tale']:<12} {r['status']:<7}")
        for c in r["checks"]:
            if c["status"] != "PASS":
                print(f"   - {c['id']} [{c['status']}]: {c['message']}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="4-tier E2E verification harness for popup-atlas")
    ap.add_argument("--tier", default="all", help="Comma-separated tiers (1,2,3,4) or 'all' (default: all)")
    ap.add_argument("--tale", default="all", help="Comma-separated tale IDs or 'all' (default: all)")
    ap.add_argument("--offline", action="store_true", help="Read-only artifact verification (default)")
    ap.add_argument("--skip-record", action="store_true", help="Alias for --offline")
    ap.add_argument("--record", action="store_true", help="Explicitly run Godot 1200x900 recordings via with_godot.sh")
    ap.add_argument("--orbit", action="store_true", help="Explicitly run house_orbit_all.sh directly")
    ap.add_argument("--run-gate", action="store_true", help="Allow running gate.py (off by default)")
    ap.add_argument("--orbit-dir", default=None, help="Directory with <tale>/<tale>_audit.json (default: artifacts/houses/e2e)")
    ap.add_argument("--tag", default="e2e_v1", help="Output tag for --record (default: e2e_v1)")
    ap.add_argument("--log", default=None, help="Explicit log override (requires single --tale)")
    ap.add_argument("--mp4", default=None, help="Explicit mp4 override (requires single --tale)")
    ap.add_argument("--json", nargs="?", const="-", default=None, metavar="PATH", help="Print JSON or write to PATH")
    ap.add_argument("--report", default=None, metavar="PATH", help="Write Markdown report to PATH")
    ap.add_argument("--strict", action="store_true", help="Treat Accepted exceptions and minor warnings as failures")
    ap.add_argument("--strict-chroma", action="store_true", help="Fail T1_CHROMA_MAGENTA on full-catalog detB>20 warnings")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None, root: Path = REPO_ROOT) -> int:
    a = parse_args(argv)

    # Validate --tier
    if a.tier == "all":
        tiers = [1, 2, 3, 4]
    else:
        tiers = []
        for tok in a.tier.split(","):
            tok = tok.strip()
            if tok not in ("1", "2", "3", "4"):
                print(f"ERROR: invalid --tier token {tok!r} (expected 1..4 or all)", file=sys.stderr)
                return 2
            ti = int(tok)
            if ti not in tiers:
                tiers.append(ti)
        if not tiers:
            print("ERROR: empty --tier list", file=sys.stderr)
            return 2

    # Validate --tale
    if a.tale == "all":
        tales = list(TALES)
    else:
        tales = []
        for tok in a.tale.split(","):
            tok = tok.strip()
            if tok not in TALES:
                print(f"ERROR: unknown tale {tok!r} (valid: {', '.join(TALES)})", file=sys.stderr)
                return 2
            if tok not in tales:
                tales.append(tok)
        if not tales:
            print("ERROR: empty --tale list", file=sys.stderr)
            return 2

    # Validate conflicting offline vs live flags
    if (a.offline or a.skip_record) and (a.record or a.orbit or a.run_gate):
        print("ERROR: --offline/--skip-record cannot be combined with --record, --orbit, or --run-gate", file=sys.stderr)
        return 2

    # Validate --log / --mp4 single-tale rule
    if (a.log is not None or a.mp4 is not None) and len(tales) != 1:
        print("ERROR: --log and --mp4 require a single --tale", file=sys.stderr)
        return 2

    # Validate ffprobe when Tier 3 is selected
    if 3 in tiers and shutil.which("ffprobe") is None:
        print("ERROR: ffprobe not found in PATH (required for Tier 3)", file=sys.stderr)
        return 2

    all_results: list[TierTaleResult] = []
    log_mp4_map: dict[str, tuple[Path | None, Path | None]] = {}

    if 1 in tiers:
        all_results.extend(verify_tier1(root, tales, strict=a.strict, strict_chroma=a.strict_chroma))
    if 2 in tiers:
        orbit_dir = Path(a.orbit_dir) if a.orbit_dir else None
        all_results.extend(verify_tier2(root, tales, orbit_dir=orbit_dir, run_orbit=a.orbit, strict=a.strict))
    if 3 in tiers:
        t3_res, log_mp4_map = verify_tier3(
            root,
            tales,
            record=a.record,
            tag=a.tag,
            log_override=Path(a.log) if a.log else None,
            mp4_override=Path(a.mp4) if a.mp4 else None,
            run_gate=a.run_gate,
            strict=a.strict,
        )
        all_results.extend(t3_res)
    if 4 in tiers:
        all_results.extend(verify_tier4(root, tales, log_mp4_map=log_mp4_map, strict=a.strict))

    mode = "live" if (a.record or a.orbit or a.run_gate) else "offline"
    payload = _build_payload(all_results, tiers, tales, mode)

    if a.report:
        rp = Path(a.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(_render_markdown(payload), encoding="utf-8")

    if a.json == "-":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if a.json:
            jp = Path(a.json)
            jp.parent.mkdir(parents=True, exist_ok=True)
            jp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        _print_console(payload)

    return 0 if payload["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
