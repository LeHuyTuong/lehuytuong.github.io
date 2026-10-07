# Conceptual ERD — trạng thái và phép đo

## Kết luận ngắn

**Sơ đồ chưa sinh được `.drawio`.** Model đã sạch lỗi nghiệp vụ. Chặn không phải giới hạn của
nội dung — đó là phát hiện ngày 05/10: engine bố trí tự động đặt **cạnh ô theo tên dài nhất**
(88px) trong khi router cần chỗ cho **số cổng** (`Users` bậc 18 → cần 420px). Thiếu đúng 12px
là router chết hoàn toàn. Sửa một dòng là chạy được.

**Đã tách 3 sơ đồ theo bounded context** (Tường duyệt, ngoại lệ nguyên tắc 8): cả ba **OK 0
error**, `academic` và `finance` **0 crossing**, `registry` còn **2 crossing** (ngân sách 3).
Không mất quan hệ nào: 47 vẽ trên sơ đồ + 31 xuyên context + 5 của `Media Assets` (thực thể
có y không vẽ) = 83. Xem mục phép đo bên dưới.

> **Đo crossing bằng `gen`, không phải `check`.** `check <spec.json>` không chạy layout, nên nó
> luôn trả cùng một số crossing bất kể bạn sửa `fromSide`/`toSide` thế nào. Chỉ `gen` mới đo
> được (`conceptual-erd: N entities, M relationships, canvas …, X crossing(s)`).

Không chia nhỏ ERD, vì nguyên tắc số 8 của skill: **MỘT sơ đồ hợp nhất, không tách**.

## Model hiện tại

`domain.model.json` — sinh bởi [../scripts/build_erd_model.py](../scripts/build_erd_model.py)
từ `inventory.json`.

- **33 entity, 83 relationship** (86 → 83 sau khi khử 3 quan hệ trùng, xem bên dưới)
- `core: "Students"` — học sinh là hàng hoá quanh mã ngành tính tiền, mọi liên học/thanh toán
  treo vào họ.
- Mọi quan hệ mang `evidence` dạng `file:dòng` đọc thẳng từ `belongsTo` trong model Laravel.

**3 quan hệ trùng đã khử** (86 → 83). Cùng một quan hệ bị khai hai lần: một lần ở model bên
nhận (`Charge.php:193` khai `Charges--pay-->Payments`), một lần ở model bên gửi
(`PaymentAllocation.php:57` khai `charge()`). Giữ **khai báo ở model** — đó là chỗ định nghĩa,
còn pivot chỉ là nơi sử dụng. Ba quan hệ bị khử: `Charges--pay-->Payments`,
`Charges--invoice-->Tax Invoices` (một lần từ `TaxInvoiceCharge.php:27`, một lần từ
`TaxInvoiceLine.php:47`).

Trạng thái `gen` hiện tại: **1 lỗi, 77 cảnh báo**. Lỗi duy nhất:

```
ERROR [spec] auto layout found no route for some relationship
```

77 cảnh báo là quy tắc 9 (đồ thị có chu trình — đúng thực tế nghiệp vụ) và quy tắc 2 (mức `}o--o{`
là chung, chưa phân biệt 1-n / n-n chưa phân biệt điểm bắt buộc).

## Nguồn gốc của lỗi: đã đo, không phải đoán

Bảng trung gian thuần kỹ thuật (pivot) **không được vẽ** theo nguyên tắc "chỉ entity và
relationship" — nhiều-nhiều vẽ thẳng. Đã loại 12 pivot:

```
ClassRoomNoteMedia  ClassStaff          GuardianContactMethod  GuardianStudent
PaymentAllocation   ReceiptPrintEvent   SessionStaff           StudentContactMethod
StudentPickupContact TaxInvoiceCharge   TaxInvoiceLine         UserBranchAssignment
```

Còn giữ lại 4 bảng có **ý nghĩa nghiệp vụ thật** (không phải bảng nối kỹ thuật):
`Holiday`, `Score`, `Refund`, `Setting`.

Nhờ vậy model đi từ 45 entity / 99 quan hệ xuống 33 / 86.

## Phép đo: 22/66 là SAI, nguyên nhân thật là engine chọn cạnh ô quá nhỏ

Bảng dưới đây là phép đo **sai** đã ghi ở lượt trước. Giữ lại để thấy sai ở đâu:

| Cách đo | Kết quả |
|---|---|
| Truyền `grid` tường minh, thử mọi hình 5×3 … 12×10 | 33/86: **không hình nào route được** |
| Bỏ trống `grid` để engine tự sinh (6 hình × 5 seed) | 33/86: **không route được** |
| Cắt dần theo độ | 23 entity / 69 quan hệ OK; 24–33 đều fail |

Đã kết luận nhầm **"trần 22 entity / 66 quan hệ"**. Không có trần nào cả.

### Nguyên nhân thật: `sharedSide` lấy từ TÊN DÀI NHẤT, không lấy từ SỐ CỔNG

`analyze()` tính cạnh ô bằng `sharedSide = max(baseS)` — `baseS` đến từ `wrapName(tên)`,
tức **chiều rộng chữ của tên dài nhất** ([erd.mjs:619](~/.dsh/skills/conceptual-erd/scripts/erd.mjs#L619)).
Nhưng router cần chỗ cho **cổng**: mỗi entity bậc *d* cần `(d−1)×PORT.gapMin + 2×PORT.corner`
= `(d−1)×22 + 20` px, cộng 2 chân stub 30px.

Đo trên model 33 entity (probe trực tiếp `placeEntities` + `routeGrid`, không qua `analyze`):

```
sharedSide (từ tên dài nhất "Attendance Records") = 88 px
max degree = 18   (Users)
  Users         deg=18  need=420px  thiếu 332px
  Branches      deg=12  need=300px  thiếu 212px
  Centers       deg=12  need=300px  thiếu 212px
  Charges       deg=11  need=280px  thiếu 192px
  Class Sessions deg=11 need=280px  thiếu 192px
  ...
  -> 30/33 entity thiếu chỗ
```

Quét trục `S` trên 4 hình lưới (6×6, 7×5, 7×6, 6×7) × 5 seed:

| S | shape route được |
|---|---|
| **88** (giá trị thật hiện tại) | **0/4** |
| 100 | 4/4 |
| 120 → 240 | 4/4 |

**Chỉ cần `S ≥ 100` là route thành công toàn bộ.** Chênh lệch 88 → 100 là 12px.

### Vì sao engine không tự làm

Khối mã nới cạnh ô theo số cổng chỉ chạy trong nhánh `if (!autoLayout)`
([erd.mjs:722](~/.dsh/skills/conceptual-erd/scripts/erd.mjs#L722)).
Bố trí lưới tự động — cũng là nhánh ta cần — **bỏ qua hoàn toàn**, nên `S` đứng ở 88 và
router không còn chỗ đặt cổng. Đây là lỗi engine, không phải giới hạn của nghiệp vụ.

Hai điều trước đây từng được gọi là "giới hạn" đều là hệ quả của cùng một nguyên nhân này:
con số 38, rồi 22, đều đo trên một engine đang đặt cạnh ô sai.

### Bằng chứng đã vá thử

Đã vá `sharedSide = max(baseS, cần theo bậc cao nhất)` và chạy `analyze` trên chính model
33/86, `grid 6×6`, **không đụng tên entity**:

```
elapsed 147.5s
side 400 | canvas 3256x3164 | crossings 75
  ERROR [crossing]    x1: 75 relationship crossings — more than the budget of 3
  ERROR [3 one-screen] x1: content bounding box 3256x3162 px exceeds the screen 1920x1080
  warns 77  { "3 one-screen":1, "6 english-present-simple":24, "spec":3, "9 no-cycle":49 }
```

`ERROR [spec] auto layout found no route` **đã biến mất**. Đó là bằng chứng nguyên nhân đúng.

Hai dòng vá nằm ở [erd.mjs:611-624](~/.dsh/skills/conceptual-erd/scripts/erd.mjs#L611-L624).

### Đo tiếp (05/10, sau khi Tường chọn "đo trước khi quyết")

Đường cong đầu tiên trông rất đẹp — bỏ 3 entity thì crossing rơi từ 69 xuống 3. **Đường cong
đó sai.** Lý do: bỏ 3 entity bậc thấp nhất là bỏ `Users`, `Centers`, `Branches` — và ba
cái đó là **cầu nối**. Số quan hệ mất đi tăng vọt:

| Giữ | Quan hệ còn lại | Mất | Bị bỏ |
|---|---|---|---|
| 33 | 86 | 0 | — |
| 32 | 68 | **18** | `Users` |
| 31 | 57 | **29** | `Centers`, `Users` |
| 30 | 48 | **38** | `Branches`, `Centers`, `Users` |
| 29 | 38 | **48** | thêm `Class Sessions` |

`Users` có bậc **18**. Cắt nó để sơ đồ đẹp là xoá 18 quan hệ thật trong code — đúng loại
lỗi đã mắc với `ChargeStatus::VOIDED` (xem [../state/README.md](../state/README.md)).
Nên đường cong 69 → 3 **loại**.

Câu hỏi đúng phải là: giữ **hết** 86 quan hệ, bố trí thế nào cho hết crossing? Đo bằng
`analyze` thật trên 4 hình lưới:

| Hình | Canvas | Crossing | Lỗi |
|---|---|---|---|
| 6×6 | 3256×3164 | **75** | crossing + one-screen |
| 7×6 | 3744×3212 | **91** | crossing + no-overlap + one-screen |
| 8×6 | 4090×3340 | **78** | crossing + no-overlap + one-screen |
| 6×7 | 3296×3688 | **86** | crossing + no-overlap + one-screen |

**Không hình nào về gần ngân sách 3.** Khoảng cách xa nhất cũng 24 lần. Đây không phải chọn
hình sai — đây là giới hạn thật của sơ đồ hợp nhất 33 entity, và nó **không sửa được bằng
bố cục**.

Tóm lại sau khi vá engine: còn tồn tại đúng **một** quyết định, và nó thuộc về chính sách
chứ không thuộc về tool.

## Quyết định của Tường: chia bounded context, và kết quả đo

Tường chọn **tách 3 sơ đồ** thay vì chấp nhận 75 crossing. Đây là ngoại lệ nguyên tắc 8, được
duyệt có ý thức. Về mặt kỹ thuật engine không cấm: luật chỉ chặn khi **một file** khai
`service`/`module`/`diagrams`/`subsystem` ([erd.mjs:553](~/.dsh/skills/conceptual-erd/scripts/erd.mjs#L553));
ba file riêng là ba sơ đồ.

Sinh ra bằng [../scripts/build_erd_contexts.py](../scripts/build_erd_contexts.py). Chia theo
trách nhiệm nghiệp vụ, và **mọi entity đều do một context sở hữu** — không entity nào mất:

| Context | Entity vẽ | Quan hệ vẽ | Entity có y không vẽ | Quan hệ của nó |
|---|---|---|---|---|
| `academic` | 14 | 18 | — | — |
| `finance` | 8 | 8 | — | — |
| `registry` | 10 | 21 | `Media Assets` | 5 (ghi ở `cross-context.md`) |
| **Tổng** | **32** | **47** | **1** | **5** |

31 quan hệ xuyên context ghi đủ kèm `evidence` ở [cross-context.md](cross-context.md).

**47 + 31 + 5 = 83**, không mất quan hệ nào. Script assert điều này mỗi lần chạy, và
`SystemExit` nếu có quan hệ rơi mất — kể cả trước khi ghi file, nên `cross-context.md` không
bao giờ bị bỏ sót.

### Hai hướng đã thử và bị loại (đừng thử lại)

1. **Chỉ vẽ quan hệ nội bộ** → 5 entity bị báo lẻ (`5 core-first`), vì toàn bộ quan hệ của
   chúng đi sang context khác. Thêm "bằng chứng" để lách luật sẽ là bịa.
2. **Mượn quan hệ xuyên context** (vẽ cả ở hai nơi) → engine từ chối: `unknown entity`
   26–30 lần mỗi sơ đồ. **Giới hạn thật của công cụ.** Đã ghi chú trong script để không ai
   thử lại.

### Còn lại

| Sơ đồ | Entity | Quan hệ | Crossing | Kết quả `gen` |
|---|---|---|---|---|
| `academic` | 14 | 18 | **0** | OK 0 error, 15 warn |
| `finance` | 8 | 8 | **0** | OK 0 error, 1 warn |
| `registry` | 10 | 21 | **2** | OK 0 error, 16 warn |

Cả ba đã **0 error**. Hai lý do đã xử lý:

- `finance` từng báo lỗi vì `Journal Entries` nằm sai context. Nó thuộc `academic` (đi cùng
  `Session Journals`), không thuộc `finance` — không tới được `Charges`.
- `registry` từng 4 crossing ở **mọi** hình lưới 3×4…6×5, vì 11 entity với 26 quan hệ.
  Root cause là `Media Assets` là hub bậc 5, mà **toàn bộ 5 quan hệ đều nội bộ registry** hoặc
  chỉ trỏ vào registry — không cái nào chạm `academic`. Tách nó ra sơ đồ riêng sẽ ra **một ô
  vuông không quan hệ nào**, vô nghĩa về mặt nghiệp vụ.

Nên `Media Assets` trở thành **entity có y không vẽ**: quan hệ của nó nằm ở mục riêng
"Thực thể thuộc context nhưng có y không vẽ" trong [cross-context.md](cross-context.md), kèm
lý do. Không xoá khỏi mô hình — chỉ không vẽ lên sơ đồ nào. Đổi lại `registry` còn 10 entity
sạch, 2 crossing, dưới ngân sách 3.

## Vấn đề còn lại sau khi vá: 75 crossing và tràn màn hình

| Lỗi | Nội dung |
|---|---|
| `crossing` | **75** relationship crossing — ngân sách là 3 |
| `3 one-screen` | content bounding box 3256×3162 px > màn hình 1920×1080 |
| `9 no-cycle` | 49 cảnh báo — đồ thị có chu trình, **đúng thực tế nghiệp vụ** |

Cả hai lỗi đều là hệ quả của **33 entity trên một sơ đồ**. Đây mới là câu hỏi cần Tường chốt,
và câu trả lời không còn là "cắt cho vừa 22" nữa.

## Vì sao không cắt bớt entity cho vừa một con số

Cắt để vừa engine là **vẽ sai thứ khách cần**. Repo này có 45 model; cắt còn 22 nghĩa là
vẽ thiếu hơn một nửa nghiệp vụ. Ba lý do không làm:

1. Nguyên tắc 8 của skill cấm tách ERD thành nhiều sơ đồ.
2. Bỏ entity cũng bỏ mất quan hệ thật trong code — cùng loại lỗi đã mắc với
   `ChargeStatus::VOIDED` (xem [../state/README.md](../state/README.md)).
3. Ngưỡng 22 vốn là giới hạn của **bộ vẽ**, không phải của nghiệp vụ — và nay đã chứng minh
   là giới hạn của một **lỗi engine**, không phải của nội dung. Trộn hai thứ lại sẽ tạo ra
   một sơ đồ đẹp nhưng sai.

## Hướng đi nếu cần chốt

- **Ưu tiên hơn hẳn: sửa engine.** Đã xác định đúng một dòng (`sharedSide` lấy từ tên dài
  nhất thay vì từ số cổng). Vá xong router chạy; phần còn lại là câu hỏi thật của nghiệp vụ.
- Dùng công cụ vẽ tay (draw.io) đặt layout rồi bỏ qua `gen`: được sơ đồ đầy đủ 33 entity, nhưng
  mất kiểm tra tự động — mất đúng cái giá trị dịch vụ bán ra.
- **Chấp nhận crossing vượt ngân sách, ghi rõ lý do.** Engine đã tối ưu tới mức 75; đó là
  trần thật của hình hợp nhất. Nếu Tường chấp nhận, sơ đồ xanh và trung thực.
- Đổi chính sách: cho phép tách ERD theo bounded context (Academic / Finance / Scheduling) thành
  3 sơ đồ. **Cần Tường chốt**, vì đụng nguyên tắc 8. Không cắt entity để vừa — đã chứng minh
  cắt là mất quan hệ thật.

## Lệnh tái lập phép đo

```bash
cd docs/uml
python3 scripts/build_erd_model.py          # 33 entity, 86 relationship
node ~/.dsh/skills/conceptual-erd/scripts/erd.mjs gen erd/domain.model.json --out erd/domain.drawio
```