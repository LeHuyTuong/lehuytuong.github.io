# Context Diagram (DFD mức 0) — LMSERP OneWorld

Hệ thống là **một hình tròn**, mỗi thực thể tối đa 2 mũi tên (vào/ra), mọi nhãn là
**danh từ dữ liệu** chứ không phải hành động.

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| Cú pháp DFD mức 0 | `node $S check system.drawio` | OK 0 lỗi 0 cảnh báo |
| Đối chiếu actor + resource từ `flows.json` | thêm `--flows ../flows.json` | OK |
| Đối chiếu hệ ngoài từ code | thêm `--repo <repo> --model system.model.json` | OK |

Đo độc lập (không tin exit code của lint): **1** ellipse process, **7** entity,
**14** mũi tên, **0** mũi tên không nhãn, **0** đường cong, canvas 1169×827.

## Chạy lại

```bash
S=~/.dsh/skills/context-diagram/scripts/context.mjs
node $S gen    system.model.json --out system.drawio
node $S check  system.drawio \
  --flows ../flows.json \
  --repo /Volumes/SSD/Dev/active/LMSERP-OneWorld \
  --model system.model.json
node $S render system.drawio [--svg]
```

## Vì sao model viết tay chứ không dùng `derive`

Skill có `derive` dựng model từ code, nhưng nó **chỉ đọc Spring và FastAPI**
(tài liệu skill ghi rõ). Chạy thật trên Laravel:

```
$ node $S derive --flows ../flows.json --repo <repo> --out ctx.model.json
actor: Administrator, Manager, Teacher, Assistant, Accountant
  | Administrator: 0 dòng vào, 0 dòng ra
  | Manager: 0 dòng vào, 0 dòng ra
  ... (cả 5 vai đều 0)
98 câu hỏi/ghi chú cho Tường
```

`flows.json` có `routes: []` nên không suy được nhãn nào. Hình này viết tay từ
`flows.json` (`actors`, `resources` — 14 tài nguyên kèm policy là bằng chứng), và
hệ ngoài lấy từ **đọc tay code** chứ không đoán.

## 7 thực thể, và 7 thứ bị loại — có lý do

Vẽ hệ ngoài kiểu "quét host rồi vẽ hết" là sai ở đây: repo có
`fonts.bunny.net`, `maxcdn`, `js.pusher.com`, `docx`… — toàn bundle frontend và
CDN, không phải luồng dữ liệu. Chỉ 2 hệ ngoài thật:

| Entity | Bằng chứng |
|---|---|
| Google Drive API | `GoogleDriveService.php:13,17` (endpoint), `:80,130` (upload/trash), `:177-196` (bearer token) |
| GitHub API | `PullDeployCommand.php:107,129,152` (`Http::withToken` → tạo PR) |

Bảy thứ bị loại, ghi lý do trong `excludedExternals` của model:

- **Font/CDN/vendor JS** — trình duyệt tải, không phải luồng của hệ thống.
- **SMTP / Mailgun / SendGrid / Mandrill / IFTTT / Telegram** — `MAIL_MAILER=log`
  (`.env.example:54`), mail ghi ra log, không có server nào được gọi. Handler của
  Mailgun/SendGrid nằm trong `vendor/`, app không chọn cái nào.
- **Redis + SQLite** — hạ tầng của chính hệ thống, nằm trong ranh giới process.
- **`oneworld-dev.carbonx.io.vn`, `*.localhost`** — chỉ trong script QA `tmp/`.
- **`Google Sign-In`** — detector khớp nhầm `oauth2.googleapis.com/token`
  (`GoogleDriveService.php:17,203`); đó là **token endpoint của Drive** đã vẽ rồi,
  không phải đăng nhập bằng Google. Đây là false positive đáng ghi lại.

## Ba lần sửa, đều do luật chứ không phải do bố cục

1. **`entity → entity` bị ERROR `[dfd entity-entity]`.** Tôi vẽ luồng
   "Administrator → Google Drive credentials → Drive". Luật DFD mức 0 không có
   entity nối entity — credential phải đi qua hệ thống. Sửa: đổi thành
   `Administrator → system` mang nhãn `Google Drive credentials`.
2. **`[dfd technical]` với nhãn `Access token`.** DFD ghi dữ liệu nghiệp vụ, không
   ghi giao thức. Sửa: `Granted file access`.
3. **`[label]` — note thừa kế đè nhãn `Charge list and cycles`.** Sửa: bỏ note khỏi
   `notes` (nội dung thừa kế đã thể hiện bằng cách liệt kê đủ nhãn dưới vai cha).

## Quyết định nghiệp vụ đã giữ

- **Administrator liệt kê nhãn riêng, không dùng note "vẽ mọi nhãn của vai khác".**
  Vai cha giao dịch với tài nguyên mà vai con không có (`User`, `Role`, `Activity
  Log` — `flows.json` chỉ gán Administrator), nên phải vẽ riêng.
- **`Google Drive credentials` là luồng vào của Administrator** dù nó không phải
  dữ liệu nghiệp vụ: không có nó thì không upload được media, và nó là thứ khách
  phải cấu hình khi triển khai. Vẽ thiếu thì triển khai mới phát hiện ra.
- **Không vẽ `Login/Logout` thành luồng riêng.** Chúng đi qua cả 5 vai và mọi vai
  đều có chung, nên gộp vào nhãn đầu tiên của từng vai thay vì thêm mũi tên.

## Còn lại

Chưa có README cho thư mục này trước đó — đây là sơ đồ thứ 4 trong bộ sơ bộ đã
chốt (`plan.md` dòng 13). Đã đủ điều kiện sang bước `sequence + class`.
