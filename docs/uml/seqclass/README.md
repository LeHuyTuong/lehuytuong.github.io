# Sequence Diagram — LMSERP OneWorld

Ba feature đã vẽ xong, cùng cấp `subsystem`, cùng bộ kiểm:

| Feature | Sequence | Activity đi kèm |
|---|---|---|
| UC22 Run Monthly Charge Cycle | `charge-cycle.sequence.drawio` — OK 0 lỗi, 5 cảnh báo | `../activity/charge-cycle.drawio` — OK 0/0 |
| UC21 Collect Payment | `collect-payment.sequence.drawio` — OK 0/0 | `../activity/collect-payment.drawio` — OK 0 lỗi, 2 cảnh báo `[path]` |
| UC19 Take Attendance | `take-attendance.sequence.drawio` — OK 0/0 | `../activity/take-attendance.drawio` — OK 0/0 |

5 cảnh báo của charge-cycle là cùng một loại, đã chờ Tường chốt: `alt` lồng trong
fragment tới bậc 6 (ví dụ số `16.1.2.2.2.1.1`), xem mục riêng bên dưới.

---

# Run Monthly Charge Cycle

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| Sinh lại | `node $S gen charge-cycle.model.json --out . --activity ../activity/charge-cycle.drawio` | OK |
| Cú pháp + đối chiếu activity | `node $S check charge-cycle.sequence.drawio --level subsystem --activity ../activity/charge-cycle.drawio` | OK 0 lỗi, 5 cảnh báo |

Đo độc lập: **10** lifeline, **29** message, **6** fragment (alt lồng nhau 6 tầng).

Model không viết tay mà sinh bằng `build_charge_cycle.py` — cây alt 6 tầng viết tay
dễ sai vị trí operand hơn là viết JSON thẳng.

## Quyết định level: `subsystem`, KHÔNG vẽ class diagram

Cùng lý do với hai feature trên: cấp `software` của skill bắt buộc có ít nhất một
class tên kết thúc `Controller`, mà repo không có (`app/Http/Controllers/` không phục
vụ nghiệp vụ tính phí), và mọi method của một service nằm cùng container nên không có
lời gọi nội bộ để vẽ.

## Bất đối xứng then chốt: duyệt thì máy gọi, bỏ thì người gọi

Đây là điều dễ vẽ sai nhất của feature này, và nó quyết định cả hình dạng sơ đồ:

| Việc | Ai gọi | Bằng chứng |
|---|---|---|
| **Duyệt** đề xuất | Runner (cron) hoặc kế toán bấm nút | `ChargeCycleRunner.php:273` (`$this->proposals->approve($proposal, actor: null, auto: true)`) và `ChargeProposalResource.php:290` (`->approve($record, auth()->user())`) |
| **Bỏ** đề xuất | chỉ kế toán bấm nút | `ChargeProposalResource.php:345` gọi thẳng `dismiss(proposal:, actor:, reason:, pauseEnrollment:)`; `grep -n "dismiss" ChargeCycleRunner.php` = **0** lần |

Hệ quả vẽ: nhánh `[No]` của quyết định `Accountant approves?` phải đi từ
`:Web App`, không phải từ `:Charge Cycle Runner`. Vẽ từ Runner sẽ bịa ra một lời gọi
không tồn tại trong code.

## Cổng hỏng KHÔNG tự bỏ đề xuất

Ba quyết định lồng nhau (`Absences over limit` và điều kiện cấu hình) chỉ **chặn
đường tự duyệt**; khi hỏng, đề xuất vẫn nằm hàng chờ cho kế toán. Bằng chứng:
`ChargeCycleRunner.php:190` rút ngắn bằng

```php
if ($recounted && $this->autoApproval->shouldApprove($proposal) && $this->autoApprove(...)) {
    return;
}
```

Không nhánh nào trong sơ đồ tự gọi `dismiss`. Sơ đồ bản đầu của tôi đã vẽ `dismiss`
ở cả hai nhánh của cổng — sai, và đã bỏ.

## `generateCycle()` nằm TRONG `approve()`, nên là message lồng

`ChargeProposalService::approve()` gọi `generateCycle()` ngay trong nó
(`ChargeProposalService.php:107`), và `ChargeCycleRunner.php:23` ghi rõ lịch sử:
trước đó lớp này gọi thẳng `generateCycle()`. Vì vậy `generateCycle` vẽ nằm trong
activation của `approve`, không phải một message ngang hàng. Nhánh `Charge created?`
bên trong là kết quả của lỗi tranh chấp: `ChargeProposalStale` ném ra ở
`ChargeProposalResource.php:291` (bình thường, không để nổ 500).

## Cảnh báo `alt` lồng — chờ Tường chốt, chưa phải lỗi

Cả 5 cảnh báo cùng loại: `alt lồng trong fragment (đường 1.2.2.2.1) — số bậc 6
(ví dụ 16.1.2.2.2.1.1) chưa được Tường chốt, tạm coi hợp lệ`. Đây là cây quyết định
thật của nghiệp vụ tính phí, không phải lỗi vẽ: activity có 6 decision, `alt` lồng 6
tầng là hệ quả trung thực. Tôi **giữ nguyên** và chờ chốt, không tự rút còn 1–2 tầng
bằng cách gộp quyết định (đã thử, gộp xong là sai nghĩa nghiệp vụ).

## Chạy lại

```bash
S=~/.dsh/skills/sequence-class-diagram/scripts/seqclass.mjs
python3 build_charge_cycle.py
node $S gen    charge-cycle.model.json --out . --activity ../activity/charge-cycle.drawio
node $S check  charge-cycle.sequence.drawio --level subsystem --activity ../activity/charge-cycle.drawio
node $S render charge-cycle.sequence.drawio
```

## Bug của bộ kiểm đã vá (05/10/2026)

Trong lúc đo feature này, `check` báo 4 lỗi `[numbering]` mà model đúng: `dismiss`
đánh số `13.1.2.2.2.2` nhưng vị trí yêu cầu `13.1.2.2.2.3`. Nguyên nhân **không
nằm ở model** mà ở `seqclass.mjs`:

`operandOf` đếm operand bằng cách đếm mọi divider mà `d.box.y <= y` và nằm trong
hộp fragment. Nhưng divider luôn nằm trong hộp **mọi frame cha bao quanh**, nên với
`alt` lồng sâu, nó đếm nhầm divider của frame **con** vào frame **cha**: khối
`Accountant approves?` chỉ có 2 operand nhưng `dismiss` bị gán `op=2`.

Đo được bằng số, không phải suy đoán: divider `c18@y1742 x=363 w=1278` thuộc khối
con, nhưng nằm trọn trong hộp `fr2` (`x=135 w=1906`), nên điều kiện `inside` trượt.

Đã vá 3 chỗ trong `~/.dsh/skills/sequence-class-diagram/scripts/seqclass.mjs`:
thêm `dividersOf(f)` lọc theo `x`/`w` trùng khung (divider do `gen` xuôi đúng bề
rộng khung), rồi dùng ở `operandOf` và cả hai chỗ tính `opCount`. Bản gốc lưu ở
`seqclass.mjs.bak-20261005-operandof`.

Sau khi vá: charge-cycle **OK 0 lỗi**; `collect-payment` và `take-attendance` chạy lại
vẫn **OK 0/0** — không hồi quy.


---

# Collect Payment

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| Cú pháp sequence + đối chiếu activity | `node $S check collect-payment.sequence.drawio` | OK 0 lỗi 0 cảnh báo |
| Đối chiếu activity UC21 | `node $S gen collect-payment.model.json --out . --activity ../activity/collect-payment.drawio` | OK |

Đo độc lập (không tin exit code của lint): **5** lifeline, **21** message, **3** fragment
(alt 2 khối), **0** cạnh có waypoint, **0** đường cong.

## Quyết định level: `subsystem`, KHÔNG vẽ class diagram

Skill `sequence-class-diagram` mặc định sinh CẶP sequence + class. Ở feature này ta
chốt **chỉ sequence**. Ba lý do, đều đo được từ code chứ không phải suy đoán:

1. **Nghiệp vụ thu tiền không có controller.** `app/Http/Controllers/` không có file
   nào phục vụ tài chính; `routes/web.php` dài 40 dòng và chỉ có đúng một route
   (`Route::redirect('/', '/app/login')`).
2. **Hai điểm vào đều là action closure ẩn danh.** `ChargeResource.php:522` và
   `ListCharges.php:485` cùng gọi một hàm:
   `app(PaymentService::class)->recordCollection(charge, amount, paidOn, method, receivedBy, note)`.
   Không có lớp nào để đặt lên lifeline kiểu Controller, nên class diagram nếu vẽ sẽ
   phải bịa thêm lớp — thứ mà `uml.md` cấm.
3. **Cấp `subsystem` là quy định của chính skill**: một sequence, không class
   diagram, `classes` phải rỗng (để khác rỗng thì `gen` thoát 2).

## Ghi thẳng đường đi thật thay vì vẽ tầng giả

| Điều vẽ trong sơ đồ | Bằng chứng trong code |
|---|---|
| `POST /livewire/update` là message đầu | `ListCharges extends ListRecords` (`ListCharges.php:62`) → Filament `ListRecords.php:23` chạy trên Livewire |
| `«in-process»` giữa `:Web App` và `:Payment Service` | grep `Http::\|Guzzle\|curl_\|file_get_contents` trong service tài chính = **0** lần |
| Không có lifeline controller | xem lý do 1 |
| Lưu ý khi đọc sequence | **không có** `$this->authorize(...)` ở cả hai điểm vào; chống chặm chân là guard non-authz `abort_unless(...)` (`ListCharges.php:476`) và scope `BelongsToCenter` trên `Charge.php:26` / `Payment.php:26` |

## Chạy lại

```bash
S=~/.dsh/skills/sequence-class-diagram/scripts/seqclass.mjs
node $S gen    collect-payment.model.json --out . --activity ../activity/collect-payment.drawio
node $S check  collect-payment.sequence.drawio
node $S render collect-payment.sequence.drawio
```

`--out` của `seqclass` nhận **THƯ MỤC** (sinh ra `<feature>.sequence.drawio`);
`activity.mjs` nhận **ĐƯỜNG DẪN FILE**.

## Hai điều chỉnh so với bản vẽ đầu

Cả hai đều do `check` bắt được, không phải do tôi đoán:

1. **Bỏ `alt` lồng trong activity.** Bản đầu có `alt "Counter collection?"` bao
   `alt "Balance reaches zero?"`. Quyết định thứ hai hoá ra là một dòng ternary
   `$newRemaining === 0 ? PAID : PARTIAL` (`PaymentService.php:98`), tức KHÔNG phải
   nhánh nghiệp vụ — vẽ ra là bịa. Quyết định thứ nhất do tôi tự nghĩ ra và code
   không có: cả hai điểm vào đều gọi chung `recordCollection(...)`. Xoá cả hai, thay
   bằng `dCover "Amount covers remaining?"` và `dOverflow "Overflow remains?"` — hai
   so sánh có thật ở `recordCollection.php:270` và `:274`.
2. **Ba message DB cuối gán cho `:Payment Service`, không phải `:Credit Pool`.**
   `ActivityLogService::log` được gọi trong `PaymentService::recordDeposit`
   (`PaymentService.php:188`), không phải trong `CreditPoolService`; các ghi
   `PaymentAllocation` cũng nằm trong cùng transaction đó (`PaymentService.php:185` —
   cùng transaction là cố ý, để tiền và phân bổ tiền là nguyên tử).

## Kiểm hình học (activity đi kèm)

Activity đi kèm là `../activity/collect-payment.drawio`, đo bằng
`../activity/scripts/verify_geometry.py`: **0** nhãn chồng, **0** cạnh xuyên hình,
**0** cạnh cắt cạnh. Nó còn **2 cảnh báo `[path]`** trên `activity.mjs check`: 5 nhánh
từ chối hội tụ vào một merge `mReject` mà engine chỉ cho neo vào 4 đỉnh (0.5,0 ·
1,0.5 · 0.5,1 · 0,0.5), nên 2 nhãn phải chung điểm. Đã thử tách thành 2 merge
(`mReject` cho lỗi nhập liệu + một merge cho lỗi nghiệp vụ) — tệ hơn, vì `showError`
khi đó nhận 3 cạnh và sinh **1 lỗi**. Giữ 1 merge và chấp nhận 2 cảnh báo.

---

# Sequence Diagram — Take Attendance (LMSERP OneWorld)

| Kiểm | Kết quả |
|---|---|
| `node $S check take-attendance.sequence.drawio --level subsystem` | OK 0 lỗi 0 cảnh báo |
| `node $A check ../activity/take-attendance.drawio --level subsystem` | OK 0 lỗi 0 cảnh báo |
| `verify_geometry.py take-attendance.drawio` | 0 nhãn chồng · 0 cạnh xuyên hình · 0 cạnh cắt cạnh |
| `node $D check take-attendance.sequence.drawio` | OK 0 lỗi; 62 cảnh báo `[overlap]` — toàn bộ là activation bar / nhãn nằm trên lifeline, đúng loại false-positive đã ghi ở Collect Payment |

Cấu hình: 5 lifeline · 34 message · 3 fragment (`alt` 5 nhánh · `alt` 2 nhánh · `opt`).

## Level `subsystem`, vẫn KHÔNG vẽ class diagram

Ba lý do (giống Collect Payment):
1. `AttendanceBoardService::__construct(protected AttendancePermission $permission)`
   (`AttendanceBoardService.php:35`) **có** DI thật — nhưng không có `interface` nào
   khai báo dưới `app/Services/` hay `app/Features/`, nên không có tầng `«interface»`.
2. `SessionAttendance` là Filament `Page` trên Livewire (`SessionAttendance.php`),
   **không có route** trong `routes/` và không có controller.
3. Level `software` của engine bắt buộc ≥1 class tên kết thúc bằng `Controller`
   (`seqclass.mjs:36`) — repo không có class nào thoả.

`level: subsystem` bắt buộc `classes: []`; service nằm trong `external[]`.

## Ba chỗ activity cũ vẽ SAI so với code — đã sửa, đây là phần đáng đọc nhất

Đối chiếu `AttendancePermission::canMark()` (`AttendancePermission.php`) với activity
cũ ra 3 sai lệch. Cả 3 đều do vẽ theo cảm tính thay vì đọc code:

| Activity cũ vẽ | Code thật | Bằng chứng |
|---|---|---|
| `Closed?` | enum `SessionStatus` **không có** `CLOSED` — chỉ `SCHEDULED` / `COMPLETED` / `CANCELLED` | `app/Enums/SessionStatus.php:12-14` |
| 4 quyết định: cancelled / read-only / admin / staff+window | `canMark()` có **5** điều kiện, đúng thứ tự: cancelled → **buổi tương lai** → read-only → admin → staff+window | `AttendancePermission.php` |
| `Session cancelled?` → `Raise charge proposal for each absent student` | `saveBatch()` **không** gọi đề xuất phí. `ChargeCycleRunner` đọc `cycle_absences` ở job cron, ngoài màn hình điểm danh | grep `CycleAttendance` trong `app/` = 0 lời gọi; nó là struct nhập liệu của `CycleAttendanceCounter.php:62` |

Hệ quả: activity cũ **thiếu** luật "buổi tương lai" — đúng luật mà code ghi rõ là
*"có mặt ở một buổi tương lai không phải dữ liệu, nó là điều đoán"* — và **thừa** một
nhánh nghiệp vụ không tồn tại.

Đã bỏ node `dCancelled2`, `raiseProposal`, `ffBlocked`; thêm `dFuture`, `dRoleRO`;
đổi `Closed?` → `Session cancelled?`. Kết quả: 10 action · 5 decision · 1 merge ·
4 flow final, **0 lỗi 0 cảnh báo**.

## Vì sao 4 nhánh từ chối mỗi nhánh một ⊗ riêng

Ban đầu cả 4 nhánh deny hội tụ vào `ffLocked`. Đo thật, mỗi cách sửa đều tệ hơn:

| Cách sửa | Kết quả đo được |
|---|---|
| Giữ 1 merge, tách `mDeny` thành `mDenySession` + `mDenyRole` | 20 lỗi, 12 cạnh cắt |
| Tách merge rồi dồn vào action `denyMark` | 3 lỗi, 2 cạnh cắt |
| Cho mỗi nhánh deny một `flowfinal` riêng (⊗ × 4) | **0 lỗi, 0 cạnh cắt** |

Đây đúng lời khuyên trong SKILL.md dòng 68: *một nhánh cụt kết thúc bằng `flowfinal`
thay vì đi qua `merge` rồi tới `stop` chung*. Engine chỉ cho neo vào 4 đỉnh, nên 4 nhánh
hội tụ một đích thì luôn chụm nhãn. Tách ⊗ là cách vừa đúng nghiệp vụ (4 lý do khóa
mỗi cái một kiện), vừa hết giới hạn kỹ thuật.

## Vì sao sequence không có `loop`

Bản đầu tôi vẽ `loop` "For each changed cell" — nhưng activity **không có vòng lặp**
(`verify` của engine: `[xc AF branch] loop không khớp vòng lặp nào của activity`).
Đúng với code: `saveBatch()` gọi `canMark()` qua memo `$markable[$session->id] ??=`,
20 ô cùng buổi chỉ hỏi quyền **1 lần** — không phải 20 vòng lặp tuần tự vẽ ra sơ đồ.

## Đường đi thật, không vẽ tầng giả

| Điều vẽ | Bằng chứng |
|---|---|
| `POST /livewire/update` là message đầu | `SessionAttendance` là Filament `Page` trên Livewire |
| `authorizeOpen` **không** bị nuốt | `SessionAttendance.php:571` gọi thẳng, lỗi trả 403 chứ không im lặng — tránh lộ IDOR |
| Ghi đè `session_id` mọi dòng về buổi đang mở | `SessionAttendance.php` (`$changes` từ client không được phép đổi buổi) |
| `$this->rosterCache = null` → đọc lại DB | không tin trạng thái client |
| Sửa là soft-delete **trước** rồi insert | `AttendanceBoardService::persist()` (`:182`) — unique `att_session_enrollment_unique` chỉ tính dòng chưa xoá; điểm danh là bằng chứng, phải giữ vết |

## Hai điều chỉnh so với bản vẽ đầu

1. **Bỏ self-call.** Bản đầu vẽ `«in-process» persist(...)` và các helper của
   `AttendancePermission` như lời gọi nội bộ trên chính lifeline đó. Ở level `subsystem`
   mọi method của một service nằm trong cùng một container — không có lời gọi nào để vẽ.
   Đổi thành: 1 lời gọi thật (`saveBatch`) + 5 lệnh `«SQL»`.
2. **Bỏ `break` + self-reply.** Bản đầu lấp `break` bằng self-reply trên
   `:AttendancePermission` để có nội dung; self-reply không phải cách hợp lệ để điền một
   fragment `break`. Đổi thành `alt` 5 nhánh đúng theo `canMark()`.

## Sai lầm của chính công cụ khi sửa nhanh

`activity.model.json` dùng key **`text`**, không phải `value`. Tôi ghi `value` → script
báo nhầm 3 lỗi "thiếu câu hỏi kết thúc bằng ?" và "dòng 15 có 3 nhánh ra", trong khi
`dClosed` còn giữ `text` cũ. Đọc lại file model trước khi vá tránh được vòng lặt này.
