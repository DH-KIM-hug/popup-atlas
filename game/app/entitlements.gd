class_name Entitlements
extends RefCounted
## Which tales open and what the name pass allows (BM of 톡톡 동화극장, docs/APP_UI_PLAN.md "BM"):
##  - 모든 동화 열기 (non-consumable $4.99, family sharing on): every tale, future ones too, plus ONE free first name
##    setup in each creative tale.
##  - 아이 이름 변경권 (consumable $1.99, anyone may buy it, with or without 모든 동화 열기): one pass = one 48-hour
##    window in which the parent sets or redoes the child's name in every creative tale at once (not one per tale).
##  - Free tales: tales.json `free`. Everything else waits for 모든 동화 열기.
##
## DEV_UNLOCK_ALL (user 2026-11-23 "모든 동화 열기로 세팅"): the dev / test build starts as if 모든 동화 열기 were
## owned, so every tale is playable now. Set it to false for a store build (and for screenshots of the locked shelf
## pass `--app-locked`). The purchase flow itself goes through StoreBridge (a StoreKit stub until the iOS plugin).

const DEV_UNLOCK_ALL := true
const PRODUCTS_PATH := "res://app/iap/products.json"

static var _products: Dictionary = {}


static func products() -> Dictionary:
	if _products.is_empty():
		var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(PRODUCTS_PATH))
		_products = v if v is Dictionary else {}
	return _products


static func product(key: String) -> Dictionary:
	return products().get(key, {})


static func dev_unlocked() -> bool:
	return DEV_UNLOCK_ALL and not OS.get_cmdline_user_args().has("--app-locked")


## 모든 동화 열기 bought (or restored), or the dev build's unlock-all flag.
static func owns_all() -> bool:
	return bool(AppState.get_v("owned", false)) or dev_unlocked()


static func purchased_all() -> bool:
	return bool(AppState.get_v("owned", false))


static func can_play(tale: Dictionary) -> bool:
	return owns_all() or bool(tale.get("free", false))


# ------------------------------------------------------------------ name pass

static func run_active() -> bool:
	return int(AppState.get_v("run_until", 0)) > int(Time.get_unix_time_from_system())


static func run_left_hours() -> float:
	return maxf(0.0, (int(AppState.get_v("run_until", 0)) - Time.get_unix_time_from_system()) / 3600.0)


static func first_setup_left(tale_id: String) -> bool:
	return purchased_all() and not (AppState.get_v("first_used", []) as Array).has(tale_id)


## How the parent may set a name in this creative tale now: "run" (a pass window is open), "first" (the free first
## setup that comes with 모든 동화 열기), or "" (needs a pass: show "이름 정하기 (변경권 $1.99)").
static func name_right(tale_id: String) -> String:
	if run_active():
		return "run"
	if first_setup_left(tale_id):
		return "first"
	return ""


static func use_name_right(tale_id: String) -> bool:
	var r := name_right(tale_id)
	if r == "first":
		var u: Array = AppState.get_v("first_used", []).duplicate()
		u.append(tale_id)
		AppState.set_v("first_used", u)
	return r != ""


## A pass bought: it starts its 48-hour window at once (톡톡: purchase -> the run starts right away).
static func grant_pass() -> void:
	var hours := float(product("rename").get("run_hours", 48))
	AppState.set_v("run_until", int(Time.get_unix_time_from_system() + hours * 3600.0))


static func grant_all() -> void:
	AppState.set_v("owned", true)
