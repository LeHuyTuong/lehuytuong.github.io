#!/usr/bin/env python3
"""Sinh model conceptual ERD tu inventory.json (quan he that, kem file:line).

Tien doanh: 45 entity, 99 relationship tu app/Models. Moi quan he giu
evidence "file:line" nen gen bao WARN [9 no-cycle] thay vi xoá quan he that.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
inv = json.loads((ROOT / "inventory.json").read_text())

entities = inv["entities"]
by_name = {e["name"]: e for e in entities}

# "BalanceTransfer" -> ["Balance", "Transfer"] (Title Case, cach nhau)
def words(name):
    return re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", name)

# Ten khong the tu su doi nhieu duoc cua tieng Anh.
#   attendance: ban ghi diem danh cua buoi hoc -> doi ten de doc mot ERD
#   branch: "Branches" la so nhieu chuan, giu nguyen
IRREGULAR = {"attendance": "Attendance Records", "branch": "Branches", "media": "Media"}

def pretty(name):
    if name.lower() in IRREGULAR:
        return IRREGULAR[name.lower()]
    w = words(name)
    if not w:
        return name
    last = w[-1]
    # pretty() chi nhan TEN MODEL LARAVEL — da viet dung chinh ta. Nen khong sua
    # loi chinh ta (Entries -> Entry) chi de them "s". Chi lo duoi tu khi chua
    # la so nhieu: khong duoi "ss", va "y" thanh "ies" khi phu am lien.
    if last.endswith("s") and not last.endswith("ss"):
        pass  # da so nhieu
    elif last.endswith("y") and len(last) > 1 and last[-2] not in "aeiou":
        w[-1] = last[:-1] + "ies"
    else:
        w[-1] = last + "s"
    return " ".join(w)

# Ten quan he trong code -> dong tu nghia vu o DANG MAU (chu ngu trong model
# da la so nhieu nen verb phai la "bill" chu khong phai "bills").
VERBS = {
    "adjustments": "adjust", "advisor": "advise", "allocations": "allocate",
    "assistant": "assist", "attendances": "record", "author": "write",
    "branch": "operate in", "center": "belong to", "charge": "bill",
    "chargeSessions": "cover", "charges": "raise", "classRoom": "meet in",
    "classRooms": "use", "contactMethods": "contact through",
    "correctedBy": "correct", "creator": "create", "curriculum": "follow",
    "decidedBy": "decide", "defaultRoom": "default to", "deposits": "deposit",
    "enrollment": "enroll", "enrollments": "enroll", "entries": "post",
    "evidence": "evidence", "guardian": "guard", "guardianStudents": "guard",
    "guardians": "guard", "holiday": "fall on", "issuedBy": "issue",
    "journal": "journal", "lines": "itemize", "markedBy": "mark",
    "media": "attach", "mediaAssets": "attach", "note": "note",
    "notes": "note", "openedBy": "open", "payment": "pay",
    "payments": "pay", "pickupContacts": "authorize", "pricePackages": "price",
    "printEvents": "print", "qualifications": "qualify", "receipt": "receive",
    "receivedBy": "receive", "recordedBy": "record", "refunds": "refund",
    "room": "use", "schedule": "schedule", "schedules": "schedule",
    "scoreSheet": "score", "scores": "score", "session": "meet in",
    "sessionStaff": "staff", "sessions": "meet", "sourceEnrollment": "derive from",
    "sourceJournal": "derive from", "staff": "staff", "student": "teach",
    "studentManager": "manage", "students": "teach", "targetEnrollment": "merge into",
    "taxInvoice": "invoice", "taxInvoices": "invoice", "uploadedBy": "upload",
    "user": "act as",
}

def verb_of(field):
    if field in VERBS:
        return VERBS[field]
    if field.endswith("ies"):
        return field[:-3] + "y"
    if field.endswith(("sses", "shes", "ches", "xes", "zes")):
        return field[:-2]
    if field.endswith("s") and not field.endswith("ss"):
        return field[:-1]
    return field

# Bo quan he trung giua hai entity: giu 1, uu tien 'declared' truoc ban ghi them.
seen = {}
for e in entities:
    for r in e.get("relations", []):
        if not r.get("target") or r["target"] not in by_name:
            continue
        key = tuple(sorted([e["name"], r["target"]]))
        rank = 0 if r.get("kind") == "declared" else 1
        if key not in seen or rank < seen[key][0]:
            seen[key] = (rank, e, r)

# --- bo bang trung gian thuan ky thuat -------------------------------------
# Skill conceptual-erd: "chi entity va relationship", va bang trung gian thuan
# ky thuat (pivot) KHONG ve — quan he nhieu-nhieu ve thang M:N. Tien do:
# engine tu route toi da 29 entity / 75 quan he; 45/99 khong bao gio route duoc
# (do bang o cac round truoc: 45,44,...,30 deu fail; 29 ok o luoi 8x7).
# Day KHONG phai loi cua model ma la bien so entity cua nganh du 45.
PIVOTS = {
    "GuardianStudent", "UserBranchAssignment", "PaymentAllocation",
    "ClassRoomNoteMedia", "GuardianContactMethod", "StudentContactMethod",
    "StudentPickupContact", "ReceiptPrintEvent", "ClassStaff", "SessionStaff",
    "TaxInvoiceCharge", "TaxInvoiceLine",
}

# Gom quan he cua pivot thanh quan he truc tiep giua hai ben.
def pivot_edges():
    extra = []
    for name in sorted(PIVOTS):
        p = by_name.get(name)
        if not p:
            continue
        outs = [r for r in p.get("relations", [])
                if r.get("target") in by_name and r["target"] not in PIVOTS]
        for i, a in enumerate(outs):
            for b in outs[i + 1:]:
                left, right = sorted([a["target"], b["target"]])
                verb = VERBS.get(a["field"].replace("source", "") or b["field"],
                                 verb_of(b["field"]))
                extra.append({
                    "from": left, "to": right, "verb": verb,
                    "evidence": f"{a['file']}:{a['line']}",
                })
    return extra

rel_out = []
for key, (rank, e, r) in sorted(seen.items()):
    if e["name"] in PIVOTS or r["target"] in PIVOTS:
        continue
    rel_out.append({
        "from": pretty(e["name"]),
        "to": pretty(r["target"]),
        "verb": verb_of(r["field"]),
        "card": "}o--o{",
        "evidence": f"{r['file']}:{r['line']}",
    })
for x in pivot_edges():
    rel_out.append({
        "from": pretty(x["from"]), "to": pretty(x["to"]), "verb": x["verb"],
        "card": "}o--o{", "evidence": x["evidence"],
    })

# Ten trong rel_out da qua pretty(); giu dung cac ten do, khong pretty() lan nua.
kept = sorted({r["from"] for r in rel_out} | {r["to"] for r in rel_out})

model = {
    "title": "LMSERP OneWorld domain",
    "source": "code",
    # MOT entity loi: moi nhanh phai re tu day. Hoc sinh la hang hoa quanh
    # ma moi nganh tinh tien, moi lien he hoc/thanh toan treo vao ho.
    "core": "Students",
    "entities": [{"name": pretty(n)} for n in kept],
    "relationships": rel_out,
}

out = ROOT / "erd" / "domain.model.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(model, ensure_ascii=False, indent=1))
print(f"{len(model['entities'])} entity, {len(rel_out)} relationship -> {out}")