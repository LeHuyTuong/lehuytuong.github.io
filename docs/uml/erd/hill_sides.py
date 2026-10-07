"""Leo đồi tham lam để giảm cắt đường của ERD bằng lựa chọn cạnh (fromSide/toSide).

Bằng chứng: erd.mjs:977 tự ghi "rearrange entities or sides". Quét thô tổ hợp side là
8^k — vượt khả thi ngay từ k=4. Ở đây mỗi vòng thử từng quan hệ một lần, giữ cải thiện,
dừng khi không còn cải thiện. Mỗi vòng = len(rels) lần check, không nhân với kích thước.
"""
import json, subprocess, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'sweep'
OUT.mkdir(exist_ok=True)
ERD = os.path.expanduser('~/.dsh/skills/conceptual-erd/scripts/erd.mjs')
SIDES = [None, 'north', 'east', 'south', 'west']

target = sys.argv[1] if len(sys.argv) > 1 else 'registry'
max_rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 6
base = json.load(open(HERE / f'{target}.model.json', encoding='utf-8'))


def label(rel):
    return f'{rel["from"]} {rel["verb"]} {rel["to"]}'


def measure(model):
    p = OUT / f'{target}.hill.json'
    p.write_text(json.dumps(model, ensure_ascii=False, indent=1), encoding='utf-8')
    out = subprocess.run(['node', ERD, 'check', str(p)], capture_output=True, text=True).stdout
    cr = re.findall(r'(\d+) relationship crossings', out)
    tail = [l for l in out.strip().splitlines() if l.startswith(('OK', 'FAIL'))]
    errs = ' '.join(l for l in out.splitlines() if l.startswith('ERROR') and 'crossing' not in l)
    penalty = 1 if 'one-screen' in errs else 0
    return (int(cr[0]) if cr else 99) + penalty * 100, (tail[-1] if tail else ''), errs


cur = json.loads(json.dumps(base))
cur_c, cur_tail, _ = measure(cur)
print(f'nền: score={cur_c}  {cur_tail}', flush=True)
best = (cur_c, json.loads(json.dumps(cur)))

for rnd in range(1, max_rounds + 1):
    improved = False
    for i, rel in enumerate(cur['relationships']):
        for key in ('fromSide', 'toSide'):
            orig = rel.get(key)
            for s in SIDES:
                if s == orig:
                    continue
                trial = json.loads(json.dumps(cur))
                t = trial['relationships'][i]
                if s is None:
                    t.pop(key, None)
                else:
                    t[key] = s
                c, tail, _ = measure(trial)
                if c < best[0]:
                    best = (c, trial)
                    improved = True
                    print(f'  v{rnd} {label(rel):44s} {key}={orig} -> {s}  score={c}', flush=True)
            if best[1] is not cur:
                cur = json.loads(json.dumps(best[1]))
    if not improved:
        print(f'v{rnd}: không còn cải thiện, dừng')
        break

c, model = best
path = OUT / f'{target}.hill-best.json'
path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding='utf-8')
final, tail, errs = measure(model)
print(f'\nKẾT: score={final}  {tail}')
print(f'ghi {path.name}')
for rel in model['relationships']:
    if 'fromSide' in rel or 'toSide' in rel:
        print(f"  {label(rel):46s} from={rel.get('fromSide')} to={rel.get('toSide')}")
