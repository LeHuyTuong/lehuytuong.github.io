"""Đo hình học activity diagram — thứ mà `activity.mjs check` KHÔNG đo.

Vì sao cần: engine chỉ chấm layout theo số ERROR/WARN của lint, không tính
cạnh có xuyên qua hình hay nhãn có chồn nhau không. Một file có thể `check`
sạch 0 lỗi mà vẽ ra vẫn có đường cắt ngang ô. Script này giải toạ độ thật
trong .drawio và báo hai loại lỗi đó.

Cách đo (đối chiếu với file do `gen` sinh):
  - node là con của swimlane nên toạ độ mxGeometry là TƯƠNG ĐỐI — phải cộng dồn
    toạ độ lane cha mới ra toạ độ tuyệt đối (absxy)
  - điểm rời/điểm vào của cạnh đọc từ exitX/exitY và entryX/entryY trong style
  - đường đi là: điểm rời -> các waypoint trong <Array><mxPoint/> -> điểm vào
  - vị trí nhãn = trung điểm đường + (mxGeometry.x * |Δx|, mxGeometry.y * |Δy|)
  - hộp nhãn ước lượng 52x18 px, hộp hình nội 4 px

Chạy:  python3 docs/uml/activity/scripts/verify_geometry.py <file.drawio>
"""
import itertools
import sys
import xml.etree.ElementTree as ET

LABEL_W, LABEL_H = 52.0, 18.0
SHRINK = 4.0


def load(path):
    root = ET.parse(path).getroot()
    cells = {c.get('id'): c for c in root.iter('mxCell')}
    parent = {c.get('id'): c.get('parent') for c in cells.values() if c.get('parent')}
    return cells, parent


def geo(cell):
    g = cell.find('mxGeometry')
    if g is None:
        return None
    try:
        return (float(g.get('x') or 0), float(g.get('y') or 0),
                float(g.get('width') or 0), float(g.get('height') or 0))
    except ValueError:
        return None


def absxy(cid, cells, parent):
    x = y = 0.0
    cur, seen = cid, set()
    while cur and cur in cells and cur not in seen:
        seen.add(cur)
        g = geo(cells[cur])
        if g:
            x += g[0]
            y += g[1]
        cur = parent.get(cur)
    return x, y


def style(cell):
    return cell.get('style') or ''


def anchor(cell, which):
    sx = style(cell)
    fx, fy = 0.5, 0.5
    try:
        fx = float(sx.split(which + '_X=')[1].split(';')[0])
    except (IndexError, ValueError):
        pass
    try:
        fy = float(sx.split(which + '_Y=')[1].split(';')[0])
    except (IndexError, ValueError):
        pass
    return fx, fy


def boxes_overlap(a, b):
    return not (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0]
                or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])


def seg_rect(p1, p2, r, shrink=SHRINK):
    x0, y0, x1, y1 = r
    x0 += shrink
    y0 += shrink
    x1 -= shrink
    y1 -= shrink
    if x1 <= x0 or y1 <= y0:
        return False
    d = (p2[0] - p1[0], p2[1] - p1[1])
    l2 = d[0] ** 2 + d[1] ** 2
    if l2 == 0:
        return False
    hits = []
    for corner in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        t = max(0.0, min(1.0, ((corner[0] - p1[0]) * d[0] + (corner[1] - p1[1]) * d[1]) / l2))
        px, py = p1[0] + t * d[0], p1[1] + t * d[1]
        if x0 < px < x1 and y0 < py < y1:
            hits.append(True)
    for t in (0.0, 1.0):
        px, py = p1[0] + t * d[0], p1[1] + t * d[1]
        if x0 < px < x1 and y0 < py < y1:
            hits.append(True)
    return bool(hits)


def poly_rect(pts, r, shrink=SHRINK):
    return any(seg_rect(pts[i], pts[i + 1], r, shrink) for i in range(len(pts) - 1))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'take-attendance.drawio'
    cells, parent = load(path)

    labels, edges = [], []
    for cid, c in cells.items():
        if c.get('edge') != '1':
            continue
        s, t = c.get('source'), c.get('target')
        if not s or not t or s not in cells or t not in cells:
            continue
        gs, gt = geo(cells[s]), geo(cells[t])
        if not gs or not gt:
            continue
        ax, ay = absxy(s, cells, parent)
        bx, by = absxy(t, cells, parent)
        ex, ey = anchor(cells[s], 'exit')
        nx, ny = anchor(cells[t], 'entry')
        start = (ax + gs[2] * ex, ay + gs[3] * ey)
        end = (bx + gt[2] * nx, by + gt[3] * ny)
        wps = [(float(q.get('x')), float(q.get('y')))
               for q in (c.iter('mxPoint') if c.find('mxGeometry') is not None else [])]
        poly = [start] + wps + [end]
        g = geo(c)
        lx = g[0] if g else 0
        ly = g[1] if g else 0
        val = (c.get('value') or '').strip()
        edges.append((cid, s, t, poly, val))
        if val:
            labels.append((cid, val, (start[0] + end[0]) / 2 + lx * abs(end[0] - start[0]),
                            (start[1] + end[1]) / 2 + ly * abs(end[1] - start[1])))

    print(f'labeled edges: {len(labels)}')
    bad = 0
    for (i1, v1, x1, y1), (i2, v2, x2, y2) in itertools.combinations(labels, 2):
        if boxes_overlap((x1 - LABEL_W / 2, y1 - LABEL_H / 2, LABEL_W, LABEL_H),
                         (x2 - LABEL_W / 2, y2 - LABEL_H / 2, LABEL_W, LABEL_H)):
            print(f"  LABEL OVERLAP {v1!r}({i1}) vs {v2!r}({i2}) "
                  f'at ({x1:.0f},{y1:.0f})/({x2:.0f},{y2:.0f})')
            bad += 1
    print(f'label overlaps: {bad}')

    solids = []
    for cid in cells:
        if not cid or cid.startswith('lane_') or cid == '1':
            continue
        if cells[cid].get('edge') == '1':
            continue
        g = geo(cells[cid])
        if not g or g[2] <= 0:
            continue
        ax, ay = absxy(cid, cells, parent)
        solids.append((cid, (cells[cid].get('value') or ''),
                       (ax, ay, ax + g[2], ay + g[3])))
    hits = 0
    for cid, s, t, poly, val in edges:
        par = parent.get(cid)
        if par and cells.get(par) is not None and cells[par].get('edge') == '1':
            continue
        for sid, sv, r in solids:
            if sid in (s, t):
                continue
            if poly_rect(poly, r):
                print(f"  EDGE {cid} ({val}) {s}->{t} crosses shape {sid} {sv!r} {r}")
                hits += 1
    print(f'edge-through-shape: {hits}')

    # Cạnh x cạnh: lint [path] có báo, nhưng chỉ với 8 cạnh ngắn nhất — một
    # sơ đồ nhiều cạnh dài sẽ còn cắt mà lint im lặng. Vì vậy tự đo lại.
    print(f'edge-edge-crossings: {cross_pairs(edges)}')
    return 0


def segments_cross(p1, p2, p3, p4):
    d1 = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = (p4[0] - p3[0], p4[1] - p3[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if den == 0:
        return None
    t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
    u = ((p3[0] - p1[0]) * d1[1] - (p3[1] - p1[1]) * d1[0]) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (p1[0] + t * d1[0], p1[1] + t * d1[1])
    return None


def cross_pairs(edges):
    n = 0
    for (a, sa, ta, pa, va), (b, sb, tb, pb, vb) in itertools.combinations(edges, 2):
        # Hai cạnh chung một đầu thì gặp nhau ở chỗ, không phải cắt chồng
        if {sa, ta} & {sb, tb}:
            continue
        for i in range(len(pa) - 1):
            for j in range(len(pb) - 1):
                p = segments_cross(pa[i], pa[i + 1], pb[j], pb[j + 1])
                if p:
                    print(f"  CROSS {a}{va!r} x {b}{vb!r} at ({p[0]:.0f},{p[1]:.0f})")
                    n += 1
    return n


if __name__ == '__main__':
    sys.exit(main())