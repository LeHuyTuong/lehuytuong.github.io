"""Đo cắt đường của registry ERD theo lựa chọn cạnh (fromSide/toSide).

Bằng chứng: erd.mjs:977 tự ghi "rearrange entities or sides" — ngoài xếp lại ô thì còn
một đòn bẩy nữa là chọn cạnh. Ở đây quét từng tổ hợp side của các quan hệ đang dính cắt.
"""
import json, subprocess, os, re, sys, itertools
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'sweep'
OUT.mkdir(exist_ok=True)
ERD = os.path.expanduser('~/.dsh/skills/conceptual-erd/scripts/erd.mjs')
SIDES = ['north', 'east', 'south', 'west']

target = sys.argv[1] if len(sys.argv) > 1 else 'registry'
base = json.load(open(HERE / f'{target}.model.json', encoding='utf-8'))

# các quan hệ nằm trong thông điệp crossing
r = subprocess.run(['node', ERD, 'check', str(HERE / f'{target}.model.json')],
                   capture_output=True, text=True).stdout
pairs = re.findall(r'"([^"]+)" and "([^"]+)"', ' '.join(l for l in r.splitlines() if 'relationship crossings' in l))
hot = sorted({x for p in pairs for x in p})
print(f'target={target} entities={len(base["entities"])} rels={len(base["relationships"])}')
print(f'cặp đang cắt: {pairs}')
print(f'quan hệ dính cắt: {hot}\n')


def label(rel):
    return f'{rel["from"]} {rel["verb"]} {rel["to"]}'


def measure(model):
    p = OUT / f'{target}.side.json'
    p.write_text(json.dumps(model, ensure_ascii=False, indent=1), encoding='utf-8')
    out = subprocess.run(['node', ERD, 'check', str(p)], capture_output=True, text=True).stdout
    cr = re.findall(r'(\d+) relationship crossings', out)
    tail = [l for l in out.strip().splitlines() if l.startswith(('OK', 'FAIL'))]
    errs = [l for l in out.splitlines() if l.startswith('ERROR') and 'crossing' not in l]
    return (int(cr[0]) if cr else 99, tail[-1] if tail else '', errs)


base_c, base_tail, _ = measure(base)
print(f'nền: crossings={base_c}  {base_tail}\n')

best = (base_c, None)
combos = list(itertools.product([(s, None) for s in SIDES] + [(None, s) for s in SIDES],
                                repeat=len(hot)))
print(f'thử {len(combos)} tổ hợp side cho {len(hot)} quan hệ...')
seen = set()
for combo in combos:
    m = json.loads(json.dumps(base))
    idx = {label(x): i for i, x in enumerate(m['relationships'])}
    for name, (fs, ts) in zip(hot, combo):
        if fs:
            m['relationships'][idx[name]]['fromSide'] = fs
        if ts:
            m['relationships'][idx[name]]['toSide'] = ts
    c, tail, errs = measure(m)
    key = (c, tuple(sorted((k, v.get('fromSide'), v.get('toSide'))
                           for k, v in zip(hot, [m['relationships'][idx[n]] for n in hot]))))
    if errs and 'one-screen' in ' '.join(errs):
        continue
    if c < best[0]:
        best = (c, m)
        print(f'  CẢI THIỆN -> crossings={c}  combo={combo}')
    if c == 0:
        break

print(f'\nbest crossings={best[0]}')
if best[1]:
    (OUT / f'{target}.best.json').write_text(json.dumps(best[1], ensure_ascii=False, indent=2), encoding='utf-8')
    for rel in best[1]['relationships']:
        if 'fromSide' in rel or 'toSide' in rel:
            print(f"  {label(rel):46s} from={rel.get('fromSide')} to={rel.get('toSide')}")
