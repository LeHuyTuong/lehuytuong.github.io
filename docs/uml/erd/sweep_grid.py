import json, subprocess, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'sweep'
OUT.mkdir(exist_ok=True)
ERD = os.path.expanduser('~/.dsh/skills/conceptual-erd/scripts/erd.mjs')

target = sys.argv[1] if len(sys.argv) > 1 else 'registry'
base = json.load(open(HERE / f'{target}.model.json', encoding='utf-8'))
n = len(base['entities'])

for cols in range(2, 8):
    rows = -(-n // cols)
    m = dict(base)
    m['grid'] = {'cols': cols, 'rows': rows}
    p = OUT / f'{target}.g{cols}x{rows}.json'
    p.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')
    out = subprocess.run(['node', ERD, 'check', str(p)], capture_output=True, text=True).stdout
    cr = re.findall(r'(\d+) relationship crossings', out)
    tail = [l for l in out.strip().splitlines() if l.startswith(('OK', 'FAIL'))]
    extra = [l for l in out.splitlines() if l.startswith('ERROR') and 'crossing' not in l]
    print(f"cols={cols} rows={rows} cells={cols*rows:3d}  crossings={cr[0] if cr else '?':>3}  "
          f"{tail[-1][:60] if tail else ''}  {' | '.join(e[:50] for e in extra)}")
