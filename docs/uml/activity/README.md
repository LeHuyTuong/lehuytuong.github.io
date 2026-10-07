# Activity Diagram — LMSERP OneWorld

Bốn sơ đồ (3 case study LMSERP + 1 của chính dịch vụ), mọi action/decision đều có bằng chứng `file:dòng` trong
[`../flows.md`](../flows.md) (mục 8.5 cho `take-attendance`, 8.1–8.2 + 8.7 cho
`charge-cycle`, 8.6 + 8.7 cho `collect-payment`).

| File | Bố cục | Nghiệp vụ |
| --- | --- | --- |
| `service-delivery` | 3 lane, 8 action, 2 decision | **Chính dịch vụ này:** giao một bộ diagram cho khách (`--level system`) |
| `take-attendance` | 4 lane, 10 action, 5 decision | Giáo viên điểm danh một buổi |
| `charge-cycle` | 4 lane, 14 action, 8 decision, 2 merge | Cron quét kỳ thu và chốt nợ |
| `collect-payment` | 4 lane, 14 action, 7 decision | Kế toán ghi thu tại quầy |

## Chạy lại

```bash
S=~/.dsh/skills/activity-diagram/scripts/activity.mjs

node $S gen take-attendance.model.json --out take-attendance.drawio --level subsystem
python3 scripts/fix_paths.py          # chỉnh tay waypoint (xem mục dưới)

node $S gen charge-cycle.model.json --out charge-cycle.drawio --level subsystem
# charge-cycle không cần vá tay: chọn thứ tự lane trong model.json là xong
# (xem mục "charge-cycle vẽ lại 05/10" bên dưới)

node $S gen collect-payment.model.json --out collect-payment.drawio --level subsystem \
  --containers "Web App,Payment Service,Credit Pool,MySQL"
# collect-payment không cần vá tay: gen ra đã 0 lỗi, 0 cắt, 0 xuyên hình
# (còn 2 cảnh báo [path] — xem mục "5 nhánh hội tụ một merge" bên dưới)

for f in take-attendance charge-cycle collect-payment; do
  node $S check $f.drawio --level subsystem
  python3 scripts/verify_geometry.py $f.drawio
  node $S render $f.drawio
done
```

## Lint KHÔNG đo hình học — phải tự đo

`activity.mjs` chỉ chấm bố cục theo số `ERROR`/`WARN` của lint. Nó **không**
tính cạnh có xuyên qua hình, nhãn có chồn nhau không. Một file có thể
`check` sạch 0 lỗi mà vẽ ra vẫn có đường cắt ngang ô — đã gặp ở biến thể
3 decision: 0 ERROR + 1 WARN nhưng **34 đường xuyên hình**.

`scripts/verify_geometry.py` giải toạ độ thật trong `.drawio` và báo ba loại
lỗi: cạnh xuyên hình, nhãn chồn nhau, và **cạnh cắt cạnh**. Ba lỗi từng phát
hiện khi dùng nó:

- bộ đo tự cộng hai lần toạ độ lane (double-count) nên báo đội lên gấp đôi;
- vòng lặp so chéo dùng polyline của cạnh trước;
- nhãn cạnh phải tính bằng `(trung điểm) + (mxGeometry.x * |Δx|,
  mxGeometry.y * |Δy|)` — số nhân là tương đối, không phải pixel.

Lớt thứ ba chỉ xuất hiện sau khi bộ đo đã đúng: lint `[path]` **chỉ** báo 5 cắt
ngắn nhất, nên một sơ đồ nhiều cạnh dài vẫn còn cắt mà lint im lặng. Kết quả của
ba lớp phải khớp nhau, nếu lệch thì chưa đo xong.

Vì vậy **không tin exit code của lint**: cứ chạy `verify_geometry.py` trước khi
báo xong. Cảnh báo `[uml label-arrow]` thì vô hại — 7/7 sơ đồ bằng chứng có ít
nhất một.

## Vì sao sửa tay waypoint

`gen` xuất ra 8 cắt cạnh. Skill cho ba lối thoát, ở thứ tự: đổi thứ tự khai báo
→ tách nhiều diagram nhỏ → **chỉnh tay toạ độ rồi `check` lại**. Đã thử hai lối
đầu, đều không giữ được nghiệp vụ:

- **Đổi lane** tối ưu được hình học (xuống 3 WARN) nhưng phải dời 3 trong 4
  decision quyền ra khỏi `Permission Service` sang `Teacher` — đúng loại tối ưu
  bằng cách hạ chất lượng mô hình mà skill cấm.
- **Tách diagram** làm mất đúng cái đáng giá nhất: 5 nhóm điều kiện trong một
  chuỗi quyết định.

Nên dùng lối thứ ba. `scripts/fix_paths.py` sửa 3 cạnh và 1 bộ điểm nối, đưa
**8 cắt xuống 2**. Ràng buộc do chính engine đặt ra (`[edge]` và `[path]`):
đoạn nối phải thẳng (hai waypoint liền nhau cùng x hoặc cùng y), waypoint đầu
phải thẳng hàng với điểm rời, và đoạn đầu/cuối phải chạy ra khỏi hình chứ không
lọt ngược vào trong.

Điều đáng ghi: **đổi điểm vào để sửa hình thì tệ hơn để yên**. Engine gán cùng
một `entryX/Y = 0.5,0.5` cho cả ba cạnh vào `mDeny`, nên chúng dồn về một điểm —
trông như lỗi đáng sửa nhất. Thử 4 bộ điểm vào thì **tất cả đều sinh thêm
ERROR**, vì khi đổi `entryX/Y` thì luật `[edge]` bắt buộc phải đi lại toàn bộ
đường. Cái duy nhất sửa được bằng cách đổi điểm nối là `e4` (đổi `exit` sang mép
phải, `entry` sang đỉnh merge), đó là 3 trong 8 cắt đã hạ.

## 2 cắt còn lại: giới hạn bản chất, không phải lỗi toạ độ

| Cắt | Vì sao không dời được |
|---|---|
| `e12` × `e13` ở (740,1095) | `e12` đi từ merge sang lane `Web App` (x=410) nên **bắt buộc** băng ngang qua x=740, đúng chỗ `e13` đi thẳng xuống cùng vùng. Thử 6 mức ngang y=1060…1130 và 3 hành lang lùi phải cho `e13`: hoặc vẫn cắt, hoặc thêm ERROR. |
| `e14` × `e16` ở (300,1218) | Cả hai cùng đi từ `Web App`/`Teacher` sang cột `Teacher` ở cùng dải y=1230. Tách được bằng cách cho `e16` vòng xuống y=1218 (đã làm), nhưng đoạn cuối vẫn phải cắt ngang đoạn ngang của `e14` để vào mép trên. |

Cả hai đều là hệ quả của việc **hai nhánh kết thúc ở hai ô cùng hàng**. Rút gọn
đi được thì phải bỏ `flowfinal` `ffLocked` hoặc dồn `showLocked`/`showEdit` vào
một ô — tức là mất nghiệp vụ. Theo quy tắc của skill, giữ lỗi và ghi lý do còn
hơn bỏ phần tử có thật.

## Biến thể đã thử và bị loại

| Biến thể | Kết quả | Vì sao loại |
|---|---|---|
| 3 decision nối chuỗi, lane tự do (96 tổ hợp) | 1 WARN / 9 cắt | Cắt hình nhiều |
| 3 decision tách 3 lane | 4 WARN / 13 cắt | Tệ hơn |
| fork/join 3 nhánh song song | 10–13 WARN / 12–14 cắt | Tệ hơn nhiều; còn lỗi `[uml fork]` khi join không dùng |
| Bỏ `mDeny`/`mAllow` | 5 và 20 ERROR | Bỏ merge làm nhánh deny mồ côi, không tới được từ initial node |
| Gộp 6 điều kiện thành 1 decision | 0 WARN / 0 cắt | Sạch nhất nhưng **mất hẳn phát hiện đáng bán**: không còn thấy `canMark()` có 5 điều kiện có thứ tự |
| **4 decision, đủ 5 nhóm điều kiện** | 2 cắt / 0 chồng nhãn / 3 WARN `[path]` | **Chọn** |

Cấu trúc fork/join bị engine giới hạn: `fork` phải đúng 1 cạnh vào, `join` phải
≥2 vào 1 ra, và `m1..m3` 1-vào-1-ra không được tính là merge.

## Quyết định nghiệp vụ đã giữ

- **4 decision, không gộp.** `AttendancePermission::canMark()`
  (`app/Services/Attendance/AttendancePermission.php:71-95`) có 5 nhóm điều kiện
  **có thứ tự**: `CANCELLED` chặn tất cả kể cả admin (:75-77); buổi tương lai chặn
  tất cả (:81-83); `READ_ONLY = ['manager','ketoan']` chặn (:85-87); admin luôn
  được phép (:90-92); còn lại thì `staffsSession() && withinEditWindow()` (:94).
  Gộp còn 3 nhóm trong một decision là tối ưu hình học bằng cách bỏ bằng chứng.
- **`Closed?` tách `Read only?` khỏi nhau.** Hai nhóm này chặn vì lý do khác nhau —
  một cái vì trạng thái buổi, một cái vì vai trò — và tách ra thấy rõ
  `CENTER_WIDE = ['admin','manager','ketoan']` (:32) chỉ mở rộng cho vai quản lý.
- **`staffsSession()` không mở rộng sang `class_staff`** (:100-103, :105-114) —
  giáo viên được gán lớp vẫn không tự động có quyền ghi. Đây là điểm dễ hiểu sai
  nhất nên giữ riêng `Staffs, window?`.
- **Nhánh bị chặn kết thúc bằng ⊗** (`ffLocked`), không hội tụ về luồng chính:
  `AttendancePolicy.php:10-18` chặn `/app/attendances` trả 403 cho
  Teacher/Assistant, nên nhánh đó thật sự dừng chứ không chuyển tiếp.
- **`Admin?` và `Staffs, window?` cùng hội tụ vào `mAllow`.** Admin bỏ qua được
  `staffsSession()` (`:90-92`), nên cho nó là một nhánh độc lập của cùng quyết
  định chứ không phải trường hợp riêng dẫn tới kết quả khác.

## Hai sơ đồ 2026-10-05: charge-cycle và collect-payment

## `collect-payment` — bản vẽ lại 05/10 theo Q1 («extend», không gộp)

Sơ đồ usecase đã tách xong (05/10) theo Q1: `Record Payment` / `Record Deposit` là
`«extend»` có điều kiện. Model `collect-payment.model.json` được viết lại hoàn toàn để
phản ánh luồng chính của UC16 (`recordCollection`, `PaymentService.php:231`) với 2 nhánh
con dưới dạng action gắn nhãn `→Record Payment UC` / `→Record Deposit UC`. UML activity
chưa hỗ trợ `«extend»` node — nên dùng action + nhãn để đánh dấu boundary.

### Kết quả đo (verify_geometry.py + activity.mjs, 05/10)

| Sơ đồ | ERROR | WARN | nhãn chồn | cạnh xuyên hình | cắt cạnh-cạnh |
| --- | --- | --- | --- | --- | --- |
| `take-attendance` | 0 | 0 | 0 | 0 | **0** |
| `charge-cycle` | 0 | 3 (`[path]`) | 0 | 0 | **2** (cặp `e21`×`e31` tại 960,1675) |
| `collect-payment` | **0** | **3** (`[path]` 2 + `[label-arrow]` 1) | 0 | 0 | **0** |

0 lỗi, 0 cắt, 0 xuyên. 3 cảnh báo còn lại là bố cục (nhãn Yes/No chụm, label chạm đầu
mũi tên) — không ảnh hưởng đúng sai luồng.

#### Bốn lần sai khi viết lại (đều do cấu trúc, không phải toạ độ)

1. Để `split` (compute applied/overflow) làm **action** → `[5 edges]`. **Sửa** thành
   **decision** — đây là nơi quyết định gọi recordPayment hay recordDeposit.
2. Nhãn `[No (applied only)]` → `[4 decision]` rule bắt buộc `[Yes]`/`[No]`. **Sửa.**
3. Duplicate merge `m1` (>=3 edges). **Sửa:** `dOverflow` có đúng 2 outgoing.
4. Label camelCase `recordPayment` → `[6 human-language]`. **Sửa** thành "Apply payment
   (→Record Payment UC)" — code reference `PaymentService.php:281`.

#### Luồng mới theo bằng chứng code (:231–:303)

```
Khóa charge → Đã thu đủ? → [Yes: ChargeAlreadySettled ⊗]
           → [No] → Chia applied/overflow
                   → applied > 0 → [→Record Payment UC] → Apply → hội tụ
                   → overflow > 0 → [→Record Deposit UC] → Record → hội tụ
                   → Issue receipt → Set PAID/PARTIAL → Log → ✓
```

**Chú ý:** nhánh `:287` `AmbiguousBranchContext` (học sinh chưa ở cơ sở duy nhất) hiện
**chưa** có trong activity — viết ra nếu có thời gian, vì đây là trường hợp biên.

### `charge-cycle` vẽ lại 05/10: sửa SAI LỆCH NGHIỆP VỤ, không phải sửa hình

Bản trước đạt 9 WARN + 1 cắt cạnh, và tôi định xếp nó vào nhóm "giới hạn bố cục
ELK" như `take-attendance`. **Đó là chẩn đoán sai.** Đọc lại
`ChargeCycleRunner::processOne()` cho thấy hai chỗ sơ đồ vẽ sai nghiệp vụ —
và sửa chúng thì số cảnh báo **tăng** 9 → 10 rồi về **3**. Bố cục xấu đang **che**
một lỗi nội dung.

**Sai 1 — `autoPause()` chạy TRƯỚC `propose()`, không phải sau khi kế toán từ chối.**
Bản cũ đặt `dismiss → dPause "Pause enrollment?" → pauseEnr` ở cuối luồng, tức
hàm ý "kế toán bấm từ chối rồi mới hỏi có bảo lưu em không". Code thì ngược lại
(`ChargeCycleRunner.php:148-156`): điều kiện `isLongAbsent() && isCycleDue()`
đứng **trên cùng** với `propose()`, và thoát sớm (`return`) — đề xuất, kể cả
đề xuất PENDING cũ, **không bao giờ được tạo** cho học sinh đó. Hơn nữa đây là
việc **hệ thống tự làm**, không có ai bấm: `autoPause()` gọi
`ActivityLogService::log(actor: null, ...)` (`:324`) và bắn
`AutoPausedEnrollmentAlert` cho toàn bộ người dùng của trung tâm (`:335-337`).
Vẽ thành quyết định của con người là bịa cả người lẫn thời điểm.

Đã dời thành `dNothing → dLongAbsent "Long absence due?" → pauseEnr →
logPause → ffPaused`, đặt trước `findExisting`.

**Sai 2 — `mAuto` hội tụ vào `mApprove` tức là vẽ "tự duyệt" cho cả 3 nhánh
từ chối.** `ChargeAutoApproval::shouldApprove()` trả `false` ở **cả bốn**
trường hợp (`:60-73`); chỉ khi trả `true` thì `processOne()` mới gọi
`autoApprove()` (`:196`). Nên ba nhánh `dEnabled[No]` / `dUnmarked[No]` /
`dAbsence[Yes]` là **không đủ điều kiện tự duyệt → rơi về kế toán**, chứ không
phải đi tới `approve`. Bản cũ vẽ ngược hướng đó.

Đã đổi thành `mManual` nối `dDecision`, và tách hai action vì khác tác nhân:
`approve "Accountant approves proposal"` vs
`autoApprove "Auto approve proposal as system"`, hội tụ tại `mApproved` trước
`generate`. (`[5 edges]` bắt buộc phải qua merge — 1 action không nhận 2 mũi tên.)

**Đo lại:** 0 ERROR, 3 WARN, 0 nhãn chồn, 0 cạnh xuyên hình, 2 bản ghi cắt cạnh
(thực chất là **một** cặp `e21`×`e31` tại 960,1675, verifier ghi 2 lần vì đo
trùng điểm giao).

| Hướng xử lý cắt cạnh | Kết quả đo | Ghi chú |
| --- | --- | --- |
| lanes `[Scheduler, Proposal, Auto, Finance]` (bản cũ) | **3** cắt | 3 cạnh `[No]` vòng từ lane Scheduler sang `mManual` |
| `mManual` đổi sang lane `Auto Approval` | 3 cắt | Không đổi — lane chỉ ảnh hưởng lint, engine xếp theo DAG |
| lanes `[Scheduler, Auto, Finance, Proposal]` | **2** cắt | **Chọn** |
| lanes `[Scheduler, Finance, Auto, Proposal]` | 2 cắt | tương đương |
| lanes `[Proposal, Scheduler, Auto, Finance]` | 3 cắt + 1 nhãn chồn | tệ hơn |

Vết còn lại là hai cạnh vào cùng một đích (`mManual` nhận 3 cạnh, `stop` nhận 2)
mà engine chỉ cho neo vào 4 đỉnh — **cùng loại giới hạn** đã ghi ở
`collect-payment` (`mReject` 5 cạnh). Muốn hết phải bỏ nội dung nghiệp vụ có
thật, skill cấm, nên giữ. Đổi 24 hoán vị thứ tự node không giúp: ELK bám DAG
chứ không bám thứ tự khai báo.

### Quyết định nghiệp vụ đã giữ ở hai sơ đồ mới

- **Không có nhánh "Charge tự sinh".** `Charge` chỉ được tạo trong
  `ChargeProposalService::approve()` (`ChargeProposalService.php:100,107,114-119`).
  Tự duyệt cũng gọi đúng hàm đó với `$auto = true` (:95-98) — nhưng đó là
  **tác nhân khác** (hệ thống vs kế toán) chứ không phải cùng một luồng, nên
  vẽ 2 action + 1 merge thay vì gộp.
- **4 điều kiện tự duyệt giữ nguyên 4 decision** (`ChargeAutoApproval.php:58-73`):
  công tắc tắt → đã quyết rồi → cho phép unmarked → ngưỡng vắng mặt.
  Gộp là mất dấu "ngưỡng vắng mặt mặc định 0" — thứ khách hay hỏi nhất.
  **Cả 3 nhánh không đạt đều dẫn về kế toán**, không phải về duyệt tự động.
- **Dismiss không hỏi "Pause enrollment?"** — xem mục "Sai 1" ở trên.
  `dismiss()` chỉ pause qua state graph (`assertCanTransitionTo` rồi `forceFill`,
  :177-182), log kèm cờ `enrollment_paused` (:185-195) — không bao giờ `ENDED`.
- **Overpay bị chặn ở cửa quầy, không phải bỏ luật.** `recordCollection()`
  tự chia: phần đúng `remainingAmount()` đi `recordPayment()`, phần dư đi
  `recordDeposit()` vào quỹ (`PaymentService.php:215-222`). Đó là lý do sơ đồ
  tách `dCover "Amount covers remaining?"` và `dOverflow "Overflow remains?"`
  thành hai quyết định — trước bản vẽ lại đây là `Parent paid extra?`.
- **Nhánh lỗi kết thúc bằng ⊗**, không quay lại form: `gen` chỉ vẽ DAG,
  và nghiệp vụ cũng vậy — bản ghi thu không hợp lệ thì không có ghi chép nào
  được tạo (mọi ném trong `recordPayment` xảy ra trước `DB::transaction`).

## Bản vẽ lại 05/10 — `take-attendance`: sửa 3 chỗ sai so với code

Lần đầu activity điểm danh vẽ `OK: 0 errors, 3 warning(s)` nhưng **3 chi tiết sai với
code**, nên số liệu đẹp mà nội dung sai. Đối chiếu `AttendancePermission::canMark()`:

| Activity cũ | Code thật | Bằng chứng |
| --- | --- | --- |
| `Closed?` | enum **không có** `CLOSED`, chỉ `SCHEDULED`/`COMPLETED`/`CANCELLED` | `app/Enums/SessionStatus.php:12-14` |
| 4 quyết định quyền | `canMark()` có **5**, đúng thứ tự: cancelled → buổi tương lai → read-only → admin → staff+window | `AttendancePermission.php` |
| `Session cancelled?` → `Raise charge proposal for each absent student` | `saveBatch()` không gọi đề xuất phí; `ChargeCycleRunner` đọc `cycle_absences` ở job cron | grep `CycleAttendance` trong `app/` = **0** lời gọi; nó là struct của `CycleAttendanceCounter.php:62` |

Thiếu luật *buổi tương lai* là thiếu mất đúng luật code đã viết rõ bằng lời: *"có mặt ở
một buổi tương lai không phải dữ liệu, nó là điều đoán"*. Thừa nhánh đề xuất phí là bịa
một nghiệp vụ không tồn tại.

Đã bỏ `dCancelled2`, `raiseProposal`, `ffBlocked`; thêm `dFuture`, `dRoleRO`; đổi
`Closed?` → `Session cancelled?`. Kết quả **0 lỗi 0 cảnh báo, hình học 0/0/0**.

### 4 nhánh từ chối → 4 ⊗ riêng, đo từng cách

Giới hạn bản chất: engine chỉ cho neo vào 4 đỉnh (`0.5,0` · `1,0.5` · `0.5,1` · `0,0.5`),
nên 4 nhánh hội tụ một đích luôn chụm nhãn. Đo cả ba cách:

| Cách sửa | Kết quả |
| --- | --- |
| Tách `mDeny` thành `mDenySession` + `mDenyRole` | 20 lỗi, 12 cắt cạnh |
| Tách merge rồi dồn vào action `denyMark` | 3 lỗi, 2 cắt cạnh |
| **Mỗi nhánh deny một `flowfinal` riêng** | **0 lỗi, 0 cắt cạnh** |

Đúng lời khuyên SKILL.md dòng 68. Cách này vừa hết giới hạn kỹ thuật, vừa đúng nghiệp
vụ: 4 lý do khóa mỗi cái một kiện.

### Bẫy khi sửa model: key là `text`, không phải `value`

Sửa nhanh bằng `n['value'] = ...` trong khi schema dùng `n['text']` → script báo nhầm
3 lỗi ("thiếu câu hỏi kết thúc bằng ?", "có 3 nhánh ra") vì `dClosed` vẫn giữ `text` cũ.
Đọc lại file model trước khi vá.
