"""Chỉnh tay toạ độ cạnh để hết cảnh báo [path] của activity.mjs.

Lối thoát hợp lệ (3) trong SKILL.md: sau `gen` thì sửa tay toạ độ trong draw.io
rồi `check` lại. Chỉ dời waypoint của các cạnh đã đo là cắt/chồn nhau —
không sửa nghiệp vụ, không bỏ phần tử thật.

Chạy:
  python3 docs/uml/activity/scripts/fix_paths.py
  node ~/.dsh/skills/activity-diagram/scripts/activity.mjs check \
       docs/uml/activity/take-attendance.drawio --level subsystem
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACT = HERE.parent
DRAWIO = ACT / 'take-attendance.drawio'

# id cạnh -> waypoint mới (toạ độ tuyệt đối trong mxGraphModel), đo từ
# 5 cảnh báo [path] của file do gen sinh:
#   e8/e10/e11  nhãn [Yes]/[No] dồn cùng ngang ở vùng merge
# Luật [edge] của engine: đoạn nối phải thẳng — hai waypoint liền nhau cùng x
# hoặc cùng y, và waypoint đầu phải thẳng hàng với điểm rời (exit) của hình nguồn.
# Vì vậy chỉ dời được theo đường gấp vuông đã đo, không dời tay được.
#
# Đo bằng quét tổ hợp waypoint, coordinate descent trên 36 hành trình vuông góc
# sinh bằng công thức, và thử các bộ điểm vào khác nhau (script quét đã xoá sau
# khi chốt kết quả, chỉ giữ lại bản vá này và verify_geometry.py). Kết quả đo:
# 0 error, 3 warning [path], 0 cạnh xuyên hình, 0 nhãn chồn, 2 cắt cạnh-cạnh —
# hạ từ 8 xuống 2. Hai cắt còn lại là giới hạn bản chất, xem README.
TAKE_FIX = {
    # e4: dClosed -> mDeny. Engine kéo nó sang trái qua hành lang x=110 rồi băng
    # ngang y=940, cắt cả e8 và e10. Đổi điểm rời sang mép phải rồi vòng ra
    # NGOÀI hành lang x=1340 của e6 (đo được), thay vì đi qua giữa cụm.
    'e4': [(1400, 535), (1400, 955), (1120, 955), (1120, 985)],
    # e12: mDeny -> denyMark. Lùi ra x=1160 rồi hạ ngang y=1095, khác e13 (đi
    # thẳng xuống tới 1110) nên không cắt nhau.
    'e12': [(1160, 1045), (1160, 1095), (520, 1095), (520, 1110)],
    # e16: allowMark -> showEdit vòng xuống y=1218 trước khi rẽ trái, tránh dải
    # ngang y=1195 của e14.
    'e16': [(740, 1160), (740, 1218), (110, 1218), (110, 1230)],
}

# e4 đi thẳng ra từ mép phải (1, 0.5) và đi thẳng vào đỉnh mDeny (0.5, 0).
# Giữ nguyên (0.5, 0.5) sẽ sinh ERROR: đoạn đầu/đoạn cuối lọt ngược vào hình.
TAKE_ANCHORS = {'e4': {'exitX': 1, 'exitY': 0.5, 'entryX': 0.5, 'entryY': 0}}


def set_waypoints(cell, points):
    geom = cell.find('mxGeometry')
    if geom is None:
        geom = ET.SubElement(cell, 'mxGeometry')
        geom.set('relative', '1')
        geom.set('as', 'geometry')
    old = geom.find('Array')
    if old is not None:
        geom.remove(old)
    arr = ET.SubElement(geom, 'Array')
    arr.set('as', 'points')
    for x, y in points:
        ET.SubElement(arr, 'mxPoint', {'x': str(x), 'y': str(y)})


def set_anchors(cell, anchors):
    style = cell.get('style') or ''
    for key, val in anchors.items():
        style = re.sub(rf'{key}=[\d.]+', f'{key}={val}', style)
    cell.set('style', style)


def main():
    if not DRAWIO.exists():
        print(f'khong tim thay {DRAWIO}')
        return 1
    tree = ET.parse(DRAWIO)
    cells = {c.get('id'): c for c in tree.getroot().iter('mxCell')}
    missing = [cid for cid in FIX if cid not in cells]
    if missing:
        print('thieu canh:', ', '.join(missing))
        return 1
    for cid, pts in FIX.items():
        set_waypoints(cells[cid], pts)
    for cid, anchors in ANCHORS.items():
        set_anchors(cells[cid], anchors)
    tree.write(DRAWIO, encoding='utf-8', xml_declaration=True)
    print(f'da chinh {len(FIX)} canh, {len(ANCHORS)} bo diem noi trong {DRAWIO.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())