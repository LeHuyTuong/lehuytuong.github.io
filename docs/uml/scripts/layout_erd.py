#!/usr/bin/env python3
"""Gan toa do cho 45 entity cua ERD.

Engine tu route (arrangeAuto) that bai 45 entity / 99 quan he: da do 1800 to hop
shape x seed ma khong shape nao route duoc (chi 38 entity moi duoc). Skill cho
phep "che do tay" — dat x/y cho MOI entity thi autoLayout = false, bo hanh router.

Toa do lay tu chinh thuat toan placeEntities cua engine (bang cach giu lai
/tmp/erd_place.json do bo do tai doanh), roi nhan he do do lai thanh khoang px.
x/y la TAM HOP, khong phai goc.
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATH = ROOT / "erd" / "domain.model.json"
GRID_JS = pathlib.Path.home() / ".dsh/skills/conceptual-erd/scripts/erd-grid.mjs"
CACHE = pathlib.Path("/tmp/erd_place.json")

GX, GY = 168, 168          # khoang px giua tam hai hop cung hang / cung cot
OX, OY = 120, 130          # goc bang; hang 0 nam o tren

model = json.loads(PATH.read_text())
names = [e["name"] for e in model["entities"]]
index = {n: i for i, n in enumerate(names)}
edges = [{"u": index[r["from"]], "v": index[r["to"]]} for r in model["relationships"]]

if not CACHE.exists() or "--rebuild" in sys.argv:
    # Do bang: chay thuat toan do cua engine, chon shape co quang duong ngan nhat.
    probe = pathlib.Path("/tmp/erd_place.mjs")
    probe.write_text(
        "import fs from 'node:fs';\n"
        "import { placeEntities } from " + json.dumps(GRID_JS.as_uri()) + ";\n"
        "const [namesPath, edgesPath, outPath] = process.argv.slice(2);\n"
        "const names = JSON.parse(fs.readFileSync(namesPath, 'utf8'));\n"
        "const edges = JSON.parse(fs.readFileSync(edgesPath, 'utf8'));\n"
        "const n = names.length;\n"
        "const col = (k, c) => k % c, row = (k, c) => Math.floor(k / c);\n"
        "let best = null;\n"
        "for (let c = 9; c <= 11; c++) for (let r = 4; r <= 6; r++) {\n"
        "  if (c * r < n || c * r > n + 25) continue;\n"
        "  // Khung ve 1920x1080: uu tien shape rong hon cao (c/r >= 1.6),\n"
        "  // chi dung shape vuot canh ngang lam phu. Trong do, do duong ngan nhat.\n"
        "  const fit = (c * 168 <= 1900 && r * 168 <= 1010) ? 0 : 1;\n"
        "  for (let seed = 1; seed <= 12; seed++) {\n"
        "    const cell = placeEntities({ n, edges, cols: c, rows: r, core: 0, seed });\n"
        "    let tot = 0;\n"
        "    for (const e of edges) tot += Math.abs(col(cell[e.u], c) - col(cell[e.v], c))\n"
        "                             + Math.abs(row(cell[e.u], c) - row(cell[e.v], c));\n"
        "    const avg = tot / edges.length;\n"
        "    const score = [fit, avg];\n"
        "    if (!best || score[0] < best.fit\n"
        "             || (score[0] === best.fit && score[1] < best.avg)) best = { c, r, seed, cell, avg, fit };\n"
        "  }\n"
        "}\n"
        "fs.writeFileSync(outPath, JSON.stringify(best));\n"
    )
    pathlib.Path("/tmp/erd_names.json").write_text(json.dumps(names))
    pathlib.Path("/tmp/erd_edges.json").write_text(json.dumps(edges))
    subprocess.run(["node", str(probe), "/tmp/erd_names.json", "/tmp/erd_edges.json",
                    str(CACHE)], check=True)

best = json.loads(CACHE.read_text())

for e in model["entities"]:
    k = best["cell"][index[e["name"]]]
    e["x"] = OX + (k % best["c"]) * GX
    e["y"] = OY + (k // best["c"]) * GY

model.pop("grid", None)
PATH.write_text(json.dumps(model, ensure_ascii=False, indent=1))
print(f"{len(names)} entity, shape {best['c']}x{best['r']}, seed {best['seed']}, "
      f"avg Manhattan {best['avg']:.2f} -> {PATH}")