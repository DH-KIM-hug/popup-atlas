class_name StoreBridge
extends Node
## Purchases and restore (docs/APP_UI_PLAN.md "결제"). Two products from res://app/iap/products.json:
## unlockall (non-consumable) and rename (consumable).
##
## This build has NO real payment and NO network: when no StoreKit plugin singleton is present the bridge is a stub
## that plays a test purchase sheet (the caller shows it) and records the result in user://app/store_stub.json, so
## "구매 복원" can be tried too. Next step (documented in the plan): a StoreKit 2 iOS plugin (singleton name in
## PLUGIN) with purchase(product_id) / restore() / transactions signals; receipts verified by the name server
## (`/receipt`, the same rule as 톡톡: each transaction id accepted once) before a pass starts.

signal finished(product_key: String, ok: bool, message: String)
signal restored(ok: bool, owned_all: bool)

const PLUGIN := "StoreKit2"  ## expected singleton of the iOS plugin (not bundled yet)
const STUB_PATH := "user://app/store_stub.json"

var busy := false


func is_stub() -> bool:
	return not Engine.has_singleton(PLUGIN)


## Start buying `key` ("unlockall" | "rename"). The stub resolves after the test sheet's 확인 (confirm_stub).
func purchase(key: String) -> void:
	if busy:
		return
	busy = true
	if not is_stub():
		var s := Engine.get_singleton(PLUGIN)
		s.call("purchase", str(Entitlements.product(key).get("id", "")))
		return  # the plugin's transaction callback calls _done (wired when the plugin lands)


## The stub's test sheet answered (ok = 확인, false = 취소).
func confirm_stub(key: String, ok: bool) -> void:
	if not ok:
		_done(key, false, "cancelled")
		return
	var led := _ledger()
	if key == "unlockall":
		led["unlockall"] = true
	else:
		led["rename_count"] = int(led.get("rename_count", 0)) + 1
	_save_ledger(led)
	_done(key, true, "")


func _done(key: String, ok: bool, msg: String) -> void:
	busy = false
	if ok:
		if key == "unlockall":
			Entitlements.grant_all()
		elif key == "rename":
			Entitlements.grant_pass()
	finished.emit(key, ok, msg)


## 구매 복원: only the non-consumable comes back (a consumable pass cannot be restored; the real app keeps unused
## passes on its server account, as 톡톡 does).
func restore() -> void:
	if not is_stub():
		Engine.get_singleton(PLUGIN).call("restore")
		return
	var own := bool(_ledger().get("unlockall", false))
	if own:
		Entitlements.grant_all()
	restored.emit(true, own)


func _ledger() -> Dictionary:
	if AppState.cli_story_run() or not FileAccess.file_exists(STUB_PATH):
		return {}
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(STUB_PATH))
	return v if v is Dictionary else {}


func _save_ledger(d: Dictionary) -> void:
	if OS.get_cmdline_user_args().has("--app-fresh"):
		return
	DirAccess.make_dir_recursive_absolute(STUB_PATH.get_base_dir())
	var f := FileAccess.open(STUB_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(d, " "))
