"""Apply game/audio/voice/<tale>/name/pieces.json to a script.json dict (tools/app/name_pieces.py, tools/story/seed_script.py)."""


def apply_to_script(script, doc):
    """Set seg.pieces / seg.name_gain_db and the new text (wc_114 word order, wc_042 call form) on the name lines."""
    by = {l['id']: l for l in script['lines']}
    for lid, e in doc['lines'].items():
        l = by.get(lid)
        if not l:
            continue
        s = l['segs'][e['seg']]
        quoted = s['text'].strip().startswith('"')
        s['text'] = ('"%s"' % e['text']) if quoted else e['text']
        s['pieces'] = [{k: p[k] for k in ('k', 'tpl', 'gap', 'audio')} for p in e['pieces']]
        s['name_gain_db'] = e['gain_db']
        s['name_slot'] = doc['slot']
        if len(l['segs']) == 1:
            lq = l['text'].strip().startswith('"')
            l['text'] = ('"%s"' % e['text']) if lq else e['text']
