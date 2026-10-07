#!/usr/bin/env python3
"""Chia ERD hợp nhất thành 3 sơ đồ theo bounded context.

Nguyên tắc: KHÔNG cắt bỏ quan hệ. Quan hệ nội bộ context vẽ trên sơ đồ của context đó;
quan hệ xuyên context ghi đủ vào cross-context.md kèm evidence. Tổng hai phần luôn bằng
tổng quan hệ gốc — assert ở cuối.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ERD = HERE.parent / "erd"
SRC = ERD / "domain.model.json"

CONTEXTS = {
    "registry": {
        "title": "LMS ERP - Registry and People",
        "core": "Students",
        "entities": [
            "Users", "Students", "Guardians", "Enrollments", "Student Notes",
            "Branches", "Centers", "Settings", "Balance Transfers",
            "Qualifications",
        ],
        # Tinh ro thuoc ve registry (co bang chung, anh chup) nhung van la kho tai lieu
        # dung chung nen KHONG ve o day: 10 entity/21 quan he do OK 0 loi, 11 entity/26
        # quan he do 4 cat vuot ngan sach 3. Do la san cua bo cuc, khong phai loi tham so.
        "external": ["Media Assets"],
    },
    "finance": {
        "title": "LMS ERP - Finance and Billing",
        "core": "Charges",
        "entities": [
            "Charges", "Charge Sessions", "Charge Proposals", "Charge Adjustments",
            "Payments", "Receipts", "Refunds",
            "Tax Invoices",
        ],
    },
    "academic": {
        "title": "LMS ERP - Academic and Teaching",
        "core": "Class Sessions",
        "entities": [
            "Class Sessions", "Class Rooms", "Rooms", "Schedules", "Curriculums",
            "Class Room Notes", "Score Sheets", "Scores", "Teaching Work Logs",
            "Session Journals", "Journal Entries", "Holidays",
            "Attendance Records", "Price Packages",
        ],
    },
}

EXPLAIN = {
    "registry": "Hoi soat, danh tinh, co so va hoc sinh vien",
    "finance": "Tinh tien, thu, hoan, hoa don",
    "academic": "Lich day, phong, mon, diem, tai lieu",
}


def main() -> None:
    model = json.loads(SRC.read_text())
    names = [e["name"] for e in model["entities"]]

    owner = {}
    for ctx, cfg in CONTEXTS.items():
        # "external" van duoc gan owner de quan he xuyen context sinh day du,
        # nhung thuc the KHONG len so do (xem ghi chu o CONTEXTS["registry"]).
        for n in list(cfg["entities"]) + list(cfg.get("external", [])):
            if n not in names:
                raise SystemExit(f"{ctx}: entity khong ton tai: {n}")
            if n in owner:
                raise SystemExit(f"{n} bi gan 2 lan: {owner[n]} va {ctx}")
            owner[n] = ctx

    missing = [n for n in names if n not in owner]
    if missing:
        raise SystemExit(f"chua gan entity: {missing}")

    rels = model["relationships"]
    internal = {c: [] for c in CONTEXTS}
    cross = []
    for r in rels:
        a, b = owner[r["from"]], owner[r["to"]]
        if a == b:
            internal[a].append(r)
        else:
            cross.append((a, b, r))

    written = 0
    shown = set()
    for ctx, cfg in CONTEXTS.items():
        keep = set(cfg["entities"])
        # Chi ve quan he noi bo. Quan he xuyen context ghi day du o cross-context.md.
        # Thu "muon" (ve ca quan he 1 dau o context khah) DA THU va bi engine tu choi:
        # "unknown entity" x26-30 lan. Khong dung lai.
        drawn = [r for r in rels if r["from"] in keep and r["to"] in keep
                 and owner[r["from"]] == owner[r["to"]]]
        seen_here = set()
        uniq = []
        for r in drawn:
            key = (r["from"], r["to"], r["verb"], r["card"], r.get("evidence", ""))
            if key in seen_here:
                continue
            seen_here.add(key)
            uniq.append(r)
        sub = {
            "title": cfg["title"],
            "source": model["source"],
            "core": cfg["core"],
            "entities": [e for e in model["entities"] if e["name"] in keep],
            "relationships": uniq,
        }
        out = ERD / f"{ctx}.model.json"
        out.write_text(json.dumps(sub, ensure_ascii=False, indent=1) + "\n")
        kinds = len([r for r in uniq if owner[r["from"]] == owner[r["to"]]])
        borrows = len(uniq) - kinds
        print(f"{ctx:9} {len(sub['entities']):2} entity  {len(uniq):2} quan he "
              f"({kinds} noi bo + {borrows} muon) -> {out.name}")
        for r in uniq:
            shown.add((r["from"], r["to"], r["verb"], r["card"], r.get("evidence", "")))
        written += len(uniq)

    hidden_set = {n for cfg in CONTEXTS.values() for n in cfg.get("external", [])}

    def key_of(r):
        return (r["from"], r["to"], r["verb"], r["card"], r.get("evidence", ""))

    cross_keys = {key_of(r) for _, _, r in cross}
    # Quan he cua thuc the co y khong ve: KHONG phai mat thong tin, ma la chuyen sang
    # muc rieng trong cross-context.md. Khong duoc bo qua am tham.
    hidden_rels = [r for r in rels
                   if r["from"] in hidden_set or r["to"] in hidden_set]
    dropped = [r for r in rels
               if key_of(r) not in shown
               and key_of(r) not in cross_keys
               and key_of(r) not in {key_of(r) for r in hidden_rels}]
    if dropped:
        raise SystemExit(f"MAT {len(dropped)} quan he that: {dropped[:3]}")

    lines = [
        "# Quan he xuyen bounded context",
        "",
        f"Tach tu `{Path(SRC).name}` ({len(rels)} quan hệ). Moi sơ do context chi ve quan he",
        f"noi bo; {len(cross)} quan he xuyen context nay khong ve tren sơ do nao, nen duoc ghi day day du",
        "de khong mat thong tin.",
        "",
        "| Tu context | Den context | Quan he | Nhan | Card | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for a, b, r in sorted(cross, key=lambda t: (t[0], t[1], t[2]["from"])):
        lines.append(
            f"| {a} | {b} | {r['from']} → {r['to']} | {r['verb']} | `{r['card']}` | `{r['evidence']}` |"
        )

    if hidden_rels:
        lines += [
            "",
            "## Thuc the thuoc context nhung co y khong ve",
            "",
            "Cac quan he duoi day thuoc ve thuc the ma khong nen ve len bat ky so do nao.",
            "",
            "| Context | Quan he | Nhan | Card | Evidence |",
            "|---|---|---|---|---|",
        ]
        for r in hidden_rels:
            lines.append(
                f"| {owner[r['from']]} | {r['from']} → {r['to']} | {r['verb']} "
                f"| `{r['card']}` | `{r['evidence']}` |"
            )
    (ERD / "cross-context.md").write_text("\n".join(lines) + "\n")

    n_internal = sum(len(internal[c]) for c in internal)
    for ctx, cfg in CONTEXTS.items():
        hidden = cfg.get("external", [])
        if not hidden:
            continue
        h = set(hidden)
        n_own = len([r for r in hidden_rels if r["from"] in h or r["to"] in h])
        print(f"  [{ctx}] KHONG ve: {', '.join(hidden)} "
              f"({n_own} quan he goc, ghi o cross-context.md)")
    print(f"\ntong goc {len(rels)} = noi bo {n_internal} + xuyen context {len(cross)}"
          f" + thuc the khong ve {len(hidden_rels)}")
    print(f"trong do noi bo: {n_internal - len(hidden_rels)} ve tren so do, "
          f"{len(hidden_rels)} thuoc thuc te khong ve")
    assert n_internal + len(cross) == len(rels), "tong khong khop"
    print("assert OK: moi quan he goc deu xuat hien it nhat mot lan tren mot sơ do")
    assert not dropped, "mat quan he"
    for a, b, _ in cross:
        assert a != b


if __name__ == "__main__":
    main()
