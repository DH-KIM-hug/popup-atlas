class_name TaleHandler
extends Node3D
## Per-tale effects for a SpreadStage (game/stories/<tale>/fx.gd, named by script.json `handler`). The stage builds
## the generic parts from the script (world template, cast from `cast`, set pieces from `spread.set`, camera shots,
## page pop/fold, sightlines); a tale's handler adds what only that tale does (sun_wind: the wind's gusts, the hat
## and coat, warm light, the stream; three_pigs: straw flying, hammer bangs, the kitchen cutaway...).
## Every hook is optional. One handler node per spread, child of the stage.

var stage: SpreadStage


## After the cast is built, before the sky layout / sightlines (synchronous).
func setup() -> void:
	pass


## After sightlines, may spread work over frames with the stage's slicer (await stage.slicer_tick()).
func build_async() -> void:
	pass


## Tale effect by name; return true when handled.
func fx(_name: String) -> bool:
	return false


## Every frame from the stage's _process, after the camera / cast / walker updates.
func step(_dt: float) -> void:
	pass


## Walker stroll speed factor (weather) and gait knobs; 1 = no change.
func stroll_mod(_dt: float, _pp: PaperPuppet) -> float:
	return 1.0


## Tap reaction for a target; true when handled (else the stage's generic hop / bounce).
func wiggle(_target: String) -> bool:
	return false


## Held press (blow verbs).
func set_blowing(_on: bool, _power: float) -> void:
	pass


## Extra tap targets ("fire", ...): names, their world centre (or null) and screen radius (px, or -1).
func targets() -> Array:
	return []


func target_point(_t: String) -> Variant:
	return null


## SPEAKER_OFF check: where a speaker who is not on the page as their actor shows instead (sunmoon's finale: the
## children are the sun and the moon). null = no stand-in.
func speaker_point(_who: String) -> Variant:
	return null


func target_radius(_t: String) -> float:
	return -1.0


## walk_to place (sun_wind: "stream" → the bank spot). Return true when the handler moves the walker.
func walk_to_place(_place: String) -> bool:
	return false


## Same-page beat change (three_pigs: the chimney beat keeps the brick_wolf page).
func enter_beat(_b: Dictionary) -> void:
	pass
