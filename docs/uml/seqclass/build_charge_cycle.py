import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def op(guard, steps):
    return {"guard": guard, "steps": list(steps)}


RUNNER = "Charge Cycle Runner"
PROPOSAL = "Charge Proposal Service"
AUTO = "Charge Auto Approval"
CHARGE = "Charge Service"
COUNTER = "Cycle Attendance Counter"
ABSENCE = "Absence Tracker"
LOG = "Activity Log Service"
ALERT = "Alert Recipients"


def call(op_, frm, to, step=None, kind="in-process"):
    d = {"call": f"«{kind}» {op_}", "from": frm, "to": to}
    if step:
        d["step"] = step
    return d


def reply(text, frm, to, step=None):
    d = {"reply": text, "from": frm, "to": to}
    if step:
        d["step"] = step
    return d


# --- Scheduler lane: scan, then hand over to the runner -------------------
scan = [
    call("run(dryRun, enrollmentId, actor)", "Scheduler", RUNNER, "Scan due enrollments", "REST"),
    call("SELECT enrollments WHERE status = ACTIVE AND is_billable = true", RUNNER, "MySQL",
         "Scan due enrollments", "SQL"),
    reply("chunk of billable enrollments", "MySQL", RUNNER),
]

# --- Proposal Service lane: preview, then the billable? gate -------------
preview = [
    call("previewCycle(enrollment)", RUNNER, CHARGE, "Preview cycle"),
]

# --- Proposal Service lane: long absence short-circuit -------------------
absence_gate = [
    call("isLongAbsent(enrollment) AND isCycleDue(enrollment)", RUNNER, ABSENCE),
    reply("long absence reached the center threshold and a new cycle is due", ABSENCE, RUNNER),
]

pause = [
    call("autoPause(enrollment)", RUNNER, RUNNER, "Auto pause enrollment as PAUSED"),
    call("UPDATE enrollments SET status = PAUSED", RUNNER, "MySQL",
         "Auto pause enrollment as PAUSED", "SQL"),
    call("log(actor: null, finance.enrollment.auto_paused)", RUNNER, LOG, "Log auto pause and notify center"),
    call("notify(AutoPausedEnrollmentAlert)", RUNNER, ALERT, "Log auto pause and notify center"),
]

# --- Proposal Service lane: existing proposal, then counters -------------
find_existing = [
    call("propose(enrollment)", RUNNER, PROPOSAL, "Find proposal of cycle"),
    reply("proposal of the cycle, or null when nothing to bill", PROPOSAL, RUNNER, "Find proposal of cycle"),
]

count_and_create = [
    call("count(enrollment, sessions)", RUNNER, COUNTER, "Count cycle attendance"),
    reply("absences and unmarked counts", COUNTER, RUNNER, "Count cycle attendance"),
    call("saveProposal(proposal, status: PENDING)", RUNNER, PROPOSAL, "Create proposal as PENDING"),
]

read_cfg = [call("shouldApprove(proposal)", RUNNER, AUTO, "Read auto approval settings")]

# --- Finance Service lane: generate, then the stale race ---------------
generated = [
    call("generateCycle(enrollment)", RUNNER, CHARGE, "Generate charge"),
    {"alt": [
        op("Charge created?", [
            reply("charge written", CHARGE, RUNNER, "Generate charge"),
            call("log(approval, charge)", RUNNER, LOG, "Log approval and charge"),
        ]),
        op("not Charge created?", [
            reply("ChargeProposalStale — conditions changed, the cycle stays in the queue",
                  CHARGE, RUNNER, "Generate charge"),
        ]),
    ]},
]

# --- Proposal Service lane: the accountant's call ------------------------
# ChargeProposalService.php:107 — `approve()` gọi `generateCycle()` ngay trong
# nó, nên `generate` là TIN NHẮN LỒNG trong activation của `approve`.
# Activity: cả hai nhánh (kế toán duyệt / máy tự duyệt) đều hội về merge
# `mApproved` rồi mới tới `generate` — nên `generate` chỉ vẽ MỘT lần sau
# `decision`, đúng một bản cho cả hai đường.
manual = [
    call("approve(proposal, actor, auto: false)", RUNNER, PROPOSAL, "Accountant approves proposal"),
    reply("proposal approved by the accountant", PROPOSAL, RUNNER, "Accountant approves proposal"),
]

auto = [
    call("approve(proposal, actor: null, auto: true)", RUNNER, PROPOSAL, "Auto approve proposal as system"),
    reply("proposal approved as the system", PROPOSAL, RUNNER, "Auto approve proposal as system"),
]

# --- Proposal Service lane: the one human decision ----------------------
# Kế toán DUYỆT thì Runner gọi (`autoApprove` cũng qua Runner,
# ChargeCycleRunner.php:273), nhưng KẾ TOÁN BỎ thì gọi từ màn hình Filament:
# ChargeProposalResource.php:345 gọi thẳng `ChargeProposalService::dismiss()`.
# Runner không hề có lời gọi dismiss — nên nhánh [No] đi từ Web App, không từ
# Runner; đó cũng là lý do không cần giữ activation của PROPOSAL mở qua ranh
# giới đó.
decision = {"alt": [
    op("Accountant approves?", manual + generated),
    op("not Accountant approves?", [
        call("dismiss(proposal, reason, pauseEnrollment)", "Web App", PROPOSAL, "Dismiss proposal"),
        call("log(dismissal)", PROPOSAL, LOG, "Log dismissal"),
        reply("proposal dismissed", PROPOSAL, "Web App"),
    ]),
]}

# --- Auto Approval lane: three nested gates, one auto path --------------
# Activity: dEnabled --Yes--> dUnmarked --Yes--> dAbsence --No--> autoApprove.
# Ba quyết định LỒNG nhau, mỗi quyết định hỏi "có đủ điều kiện tự duyệt không".
# Nhánh [Yes] của cổng nào cũng hội về mManual — merge KHÔNG mang action — rồi
# mới tới dDecision. Cổng hỏng KHÔNG tự bỏ đề xuất (ChargeCycleRunner không có
# lời gọi dismiss nào); đề xuất vẫn nằm hàng chờ, chỉ là không tự ghi nợ.
# ChargeCycleRunner.php:190 — `shouldApprove() && autoApprove()`.
not_eligible = [
    reply("false — a setting blocks auto approval, the proposal waits for the accountant",
          AUTO, RUNNER, "Read auto approval settings"),
]

auto_gate = [
    {"alt": [
        op("not Absences over limit", auto),
        op("Absences over limit", [decision]),
    ]},
]

steps = scan + preview + [{"alt": [
    op("Cycle to bill?", absence_gate + [{"alt": [
        op("Long absence due?", pause),
        op("not Long absence due?", find_existing + [{"alt": [
            op("Already decided?", [
                reply("proposal null or a cycle the accountant already decided", RUNNER, RUNNER,
                      "Find proposal of cycle"),
            ]),
            op("not Already decided?", count_and_create + read_cfg + auto_gate),
        ]}]),
    ]}]),
    op("not Cycle to bill?", [
        reply("preview null — the cycle cannot be billed yet", CHARGE, RUNNER, "Preview cycle"),
    ]),
]}]

model = {
    "feature": "Charge Cycle",
    "activity": str(HERE.parent / "activity" / "charge-cycle.drawio"),
    "level": "subsystem",
    "style": "REST",
    "actor": "Scheduler",
    "boundary": "Web App",
    "external": [RUNNER, PROPOSAL, AUTO, CHARGE, COUNTER, ABSENCE, LOG, ALERT],
    "database": "MySQL",
    "classes": [],
    "steps": steps,
}

out = HERE / "charge-cycle.model.json"
text = json.dumps(model, ensure_ascii=False, indent=2) + "\n"
json.loads(text)
out.write_text(text)


def depth(seq, d=0):
    best = d
    for s in seq:
        if "alt" in s:
            best = max(best, depth(s["alt"], d + 1))
    return best


def bad(seq):
    n = 0
    for s in seq:
        if isinstance(s, list):
            n += 1
        elif "alt" in s:
            for o in s["alt"]:
                n += bad(o["steps"])
    return n


print("JSON hop le | do sau alt toi da:", depth(steps), "| list long:", bad(steps))