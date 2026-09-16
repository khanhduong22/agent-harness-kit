---
name: playwright-e2e-testing
description: Complete end-to-end (E2E) testing workflow with Playwright, including headless browser test execution, form validation guardrails, full CRUD lifecycle, video recording, automatic Google Drive upload via rclone, and instant Slack notifications.
---

# Skill: Playwright E2E Testing (index-admin-cms)

## Purpose
Automate high-confidence, full-lifecycle browser testing with Playwright, complete with video recording and cloud reporting. Every admin/client feature must be verified against runtime UI/DOM, validation guardrails, **downstream side-effect sinks**, and persistent database state before human review.

> **Nguyên tắc số 1 của skill này**: scaffolding (config, POM, fixtures, helper) **đã tồn tại thật** trong `index-admin-cms/`. Skill này KHÔNG chứa bản copy của chúng — copy sẽ drift và sai. Luôn `Read` file thật trước khi viết spec mới.

---

## 1. Nguồn sự thật: đọc code thật, đừng copy từ doc

| Bạn cần | Đọc file thật | Export chính |
|---|---|---|
| Cấu hình runner, project, video | `index-admin-cms/playwright.config.ts` | `defineConfig` (`setup` → `e2e-authenticated`) |
| Login 1 lần, lưu session | `e2e/setup/auth.setup.ts` | storageState → `e2e/.auth/admin.json` |
| Inject POM vào spec | `e2e/fixtures/index.ts` | `test`, `expect`, 11 POM fixtures |
| Helper chung cho POM | `e2e/pages/base.page.ts` | `goto`, `recordPause`, `waitForToast`, `confirmModal`, `cancelModal`, `takeScreenshot` |
| Nhịp video cho người xem | `e2e/utils/video-helper.ts` | `recordPause(page, ms)` |
| Banner + modal tổng kết trong video | `e2e/utils/video-telemetry.ts` | `showStepBanner`, `removeStepBanner`, `showSummaryModal` |
| Verify CSV export + preview | `e2e/utils/csv-preview.ts` | `validateAndPreviewCsv`, `CsvValidationResult` |
| Locator dùng chung | `e2e/utils/selectors.ts` | `SELECTORS` |

> [!WARNING]
> **Không bao giờ tự viết lại `playwright.config.ts`, `base.page.ts`, hay bất kỳ file nào ở bảng trên.** Chúng đang chạy được. Ghi đè bằng một phiên bản "chuẩn" trong đầu sẽ phá suite hiện tại. Cần thêm hành vi → mở rộng file thật.

### Cấu trúc thư mục

```text
index-admin-cms/
├── playwright.config.ts            # Multi-project: setup → e2e-authenticated
└── e2e/
    ├── .auth/admin.json            # [Gitignored] session cache
    ├── setup/auth.setup.ts         # Login 1 lần, dump storageState
    ├── fixtures/index.ts           # test.extend inject POM đã typed
    ├── pages/                      # POM: base.page.ts + auth/ community/ content/
    ├── specs/                      # Spec theo domain: auth/ community/ content/
    └── utils/                      # video-helper, video-telemetry, csv-preview, selectors
```

POM và spec mới đặt theo domain sẵn có (`community/groups`, `community/users`, `community/topics`, `community/tags`, `community/moderation`, `community/notifications`, `content`). Thêm fixture mới → khai báo trong `e2e/fixtures/index.ts`.

> [!IMPORTANT]
> `playwright.config.ts` route spec bằng `testMatch` regex có allowlist domain. Tạo thư mục spec ở domain mới mà quên thêm vào regex thì **spec sẽ không chạy và suite vẫn báo xanh**. Luôn kiểm tra spec mới thực sự được pick up (`npx playwright test --list`).

---

## 2. Bước 0 BẮT BUỘC: Side-Effect Discovery (trước khi viết spec)

Đây là bước hay bị bỏ nhất, và là lý do "E2E pass" nhưng production vẫn vỡ.

**Vấn đề**: rule "phải verify email/notification downstream" là rule *có điều kiện* — "nếu action gửi mail thì...". Nhưng khi viết spec cho một feature, agent **không biết** action đó có phát sinh side-effect hay không. Không biết thì không verify, rồi tick "N/A" một cách thành thật. Rule không sai; thiếu **bước đi tìm**.

### 2.1. Quy trình truy vết sink (chạy TRƯỚC khi viết dòng spec đầu tiên)

Với mỗi action sắp test (create/update/delete/moderate/ban/publish...), truy ngược chuỗi này trong `index-api`:

```text
1. Catalog sự kiện       index-api/src/community/constants/event.constants.ts   → COMMUNITY_EVENTS
2. Điểm phát sự kiện     index-api/src/community/emitters/community-event.emitter.ts
3. Listener fan-out      index-api/src/community/listeners/notification.listener.ts
                          ├── NotificationService  → bản ghi notification trong DB
                          └── SmtpService          → email thật
4. Kênh email            index-api/src/shared/modules/smtp/smtp.service.ts        → Mailpit :8025
5. Kênh realtime         index-api/src/app/app.gateway.ts  @OnEvent('SEND_NOTIFICATION_TO_USER')
                                                            → websocket → NotificationBell (index-web)
```

Lệnh truy vết nhanh:

```bash
# Action này có bắn event nào không?
grep -rn "COMMUNITY_EVENTS\." index-api/src/community --include="*.ts" | grep -i "<entity>"

# Event đó có listener nào bắt, và fan-out đi đâu?
grep -rn "@OnEvent" index-api/src --include="*.ts"

# Có gửi mail trực tiếp không (không qua event)?
grep -rln "SmtpService\|sendMail" index-api/src index-admin-cms/src --include="*.ts"
```

Hoặc dùng `codebase-memory-mcp`: `trace_path(function_name="<serviceMethod>", direction="outward")` để thấy toàn bộ fan-out.

### 2.2. Sink Inventory — bảng bắt buộc điền trước khi viết spec

Kết quả bước 2.1 phải được ghi thành bảng, đính kèm trong PR:

| Action | Sink phát hiện được | Verify trong video | Nếu N/A: lý do |
|---|---|---|---|
| `POST /groups` | không có event | — | emitter không có `GROUP.CREATED` |
| `PUT /users/:id/ban` | `USER.BANNED` → mail + noti | Mailpit + NotificationBell | — |
| `PUT /posts/:id/hide` | `POST.MODERATED` → noti + public feed | Bell + `/vi/cong-dong` | — |

> [!IMPORTANT]
> **"N/A" chỉ hợp lệ khi đã chạy bước 2.1 và ghi được lý do cụ thể.** Tick N/A mà không có dòng truy vết tương ứng = chưa làm bước 0, và PR bị chặn.

---

## 3. Testing Philosophy: 4-Layer Pyramid

1. **Layer 1 — Smoke & Navigation**: page load, nav link, SideNav active state.
2. **Layer 2 — Full Lifecycle CRUD** (kịch bản lõi):
   - *Phase 1 — Validation Guardrail*: submit form rỗng, assert inline error, verify **ZERO** request gửi xuống backend.
   - *Phase 2 — Create*: điền hợp lệ, submit, assert modal đóng + toast + item hiện trên UI.
   - *Phase 3 — Update*: mở edit modal đã prefill, sửa, lưu, assert UI cập nhật ngay.
   - *Phase 4 — Delete*: trigger xóa, assert confirm dialog, xác nhận, assert item biến mất.
   - *Phase 5 — Persistence*: reload (`page.reload()`), quay lại, assert DB đã lưu đúng state.
3. **Layer 3 — RBAC Matrix**: chạy lại Layer 2 với `storageState` theo từng role (`admin.json`, `moderator.json`, `viewer.json`); assert nút Add/Edit/Delete bị ẩn hoặc disable với role không đủ quyền.
4. **Layer 4 — Closed-Loop Downstream Verification** — với mọi sink tìm được ở §2:

> [!IMPORTANT]
> **Dừng ở toast nội bộ của CMS là chưa đóng vòng lặp. Mock downstream cũng không tính.** Video phải thực sự điều hướng sang hệ thống nhận, trong cùng một session ghi hình:
> - **Sink A — Email (Mailpit `http://localhost:8025`)**: mở đúng mail vừa đến, assert subject, kiểm tra HTML template có branding, verify link động (vd token reset trỏ về `https://index.vn/dat-lai-mat-khau?code=...`).
> - **Sink B — In-App Notification (`index-web` `http://localhost:3000`)**: đăng nhập đúng user nhận, assert badge `NotificationBell` tăng, mở `NotificationPanel`, click item, assert điều hướng đúng route và unread giảm.
> - **Sink C — Public Feed (`index-web` `/vi/cong-dong`)**: sau khi admin ẩn/xóa/khóa/lưu trữ, vào feed công khai assert nội dung đã bị loại khỏi hiển thị.
>
> `index-web` là **read-only** — chỉ chạy và quan sát, tuyệt đối không sửa/commit code trong đó.

---

## 4. Two-Dimensional Completeness: Full Flow × Full Option Matrix

### 4.1. Bẫy "Flow-Only"
Nhiều engineer và AI agent verify được flow chạy từ đầu đến cuối (Navigate ➔ Modal ➔ Fill ➔ Submit ➔ Table ➔ Delete), không lỗi, rồi tuyên bố "100% E2E verified". Nhưng trong flow đó họ chỉ chọn **một option tùy ý** (tạo với category đầu tiên, đổi role thành `ADMIN` và bỏ qua `COMMUNITY_MODERATOR`).

**Hệ quả thật đã gặp**: chỉ test 2/3 role (`ADMIN`, `USER`) khiến `COMMUNITY_MODERATOR` lọt lưới. Lên production, chọn option đó là `400 Bad Request` ngay vì Prisma enum ở backend thiếu giá trị.

Ba nhóm lỗi hay lọt theo cách này:
1. **Schema & serialization mismatch** — enum chưa test fail validation giữa Strapi plugin, NestJS gateway và PostgreSQL enum.
2. **UI rendering crash** — badge, màu, icon, nút gated theo role gắn với option chưa verify sẽ throw runtime error hoặc render rỗng.
3. **Silent logic/permission bug** — transition guard đúng với state phổ biến, vỡ ở state trung gian.

### 4.2. Hai chiều trực giao

```
┌────────────────────────────────────┬────────────────────────────────────┐
│   CHIỀU 1: FLOW COVERAGE           │   CHIỀU 2: OPTION COVERAGE         │
│   (hành trình ngang)               │   (không gian state/option dọc)    │
├────────────────────────────────────┼────────────────────────────────────┤
│ • Điều hướng tới trang feature     │ • 100% giá trị Enum (role, status) │
│ • Mở Create / Edit drawer          │ • 100% lựa chọn Select dropdown    │
│ • Điền và submit form              │ • 100% option Radio group          │
│ • Trigger action lifecycle         │ • 100% tab filter trên listing     │
│ • Xử lý confirm dialog             │ • 100% mốc thời hạn moderation     │
│ • Assert toast & notification      │ • 100% trường search / sort        │
│ • Cleanup & xóa                    │ • 100% nhánh quyết định của dialog │
└────────────────────────────────────┴────────────────────────────────────┘
```

> [!IMPORTANT]
> **Suite phủ 100% flow nhưng chỉ 30% option là INCOMPLETE và bị chặn ship.**

### 4.3. Zero-Skipped-Option Rule

> [!IMPORTANT]
> Với **BẤT KỲ** enum, select, radio group, segmented button, hay state machine đa lựa chọn — role & RBAC, entity status, privacy scope, action duration, tab filter, nhánh quyết định của modal:
> 1. **Mọi option ($N$/$N$, 100%) phải được test và assert tường minh.**
> 2. **Test một tập con ($N-1$/$N$) là VI PHẠM.**
> 3. Mỗi option phải assert đủ 5 tầng:
>    - **DOM**: option có mặt, click được, label đúng.
>    - **Network payload**: request gửi lên chứa đúng giá trị enum.
>    - **Server response**: HTTP 200/201 và entity trả về mang đúng giá trị.
>    - **UI reflection**: badge/tag/trạng thái cập nhật ngay.
>    - **DB persistence**: `page.reload()` xong state vẫn đúng.

### 4.4. Ba pattern triển khai

**Pattern A — Vòng lặp chuyển trạng thái tuần tự** (khi một entity đổi option qua toàn bộ vòng đời):

```typescript
export const COMMUNITY_USER_ROLES = [
  { value: 'COMMUNITY_ADMIN', label: 'Quản trị viên' },
  { value: 'COMMUNITY_MODERATOR', label: 'Kiểm duyệt viên' },
  { value: 'COMMUNITY_MEMBER', label: 'Thành viên' },
] as const;

// ❌ CẤM: chỉ test ADMIN → MEMBER rồi bỏ qua COMMUNITY_MODERATOR
// ✅ CHUẨN: lặp hết mọi role, không bỏ option nào
for (const role of COMMUNITY_USER_ROLES) {
  await userListPage.openChangeRoleModal(targetUserEmail);
  await userModalsPage.selectRole(role.value);

  const [response] = await Promise.all([
    page.waitForResponse(r => r.url().includes('/api/community/users') && r.status() === 200),
    userModalsPage.submitRoleChange(),
  ]);
  expect((await response.json()).data.role).toBe(role.value);

  await userListPage.waitForToast(/cập nhật vai trò thành công/i);
  await userListPage.expectUserRoleBadge(targetUserEmail, role.label);

  await page.reload({ waitUntil: 'domcontentloaded' });
  await userListPage.expectUserRoleBadge(targetUserEmail, role.label);
}
```

**Pattern B — Ma trận tạo mới parametrized** (khi entity được tạo với nhiều biến thể enum):

```typescript
export const GROUP_PRIVACY_VARIANTS = [
  { value: 'PUBLIC', label: 'Công khai' },
  { value: 'PRIVATE', label: 'Riêng tư' },
  { value: 'RESTRICTED', label: 'Hạn chế' },
] as const;

for (const variant of GROUP_PRIVACY_VARIANTS) {
  test(`tạo nhóm với privacy: ${variant.value}`, async ({ groupListPage, groupModalPage, page }) => {
    const groupName = `E2E ${variant.value} Group ${Date.now()}`;
    await groupListPage.navigate();
    await groupListPage.clickCreateGroup();
    await groupModalPage.fillForm({ name: groupName, privacy: variant.value });

    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('/api/community/groups') && r.status() === 201),
      groupModalPage.submit(),
    ]);
    expect((await response.json()).data.privacy).toBe(variant.value);

    await groupListPage.waitForToast(/tạo nhóm thành công/i);
    await groupListPage.expectGroupPrivacyBadge(groupName, variant.label);
  });
}
```

**Pattern C — Assert DOM có đủ option** (chạy trước khi tương tác với dropdown/radio enum):

```typescript
async expectExhaustiveEnumOptions(
  trigger: Locator,
  expected: Array<{ value: string; label: string }>,
): Promise<void> {
  await trigger.click();
  const options = this.page.getByRole('option');
  await expect(options).toHaveCount(expected.length);           // đủ số lượng
  for (const opt of expected) {
    await expect(options.filter({ hasText: opt.label })).toBeVisible();
  }
}
```

---

## 5. Best Practices & Modal Scoping

1. **Accessible role selector**: ưu tiên `page.getByRole('button', { name: ... })` hơn text lỏng hay CSS selector.
2. **Modal scoping guardrail**: scope nút trong modal bằng `page.getByRole('dialog')` / `getByRole('alertdialog')` để tránh `strict mode violation` khi nhiều nút trùng label ("Hủy", "Lưu").
3. **Explicit timeout**: spec lifecycle nhiều bước phải đặt `test.setTimeout(60000)`.
4. **Zero raw selector trong spec**: mọi locator nằm trong POM. Spec phải đọc như một câu chuyện nghiệp vụ bằng tiếng Việt/Anh.
5. **Nhịp video**: chèn `recordPause(1500)` giữa các chuyển trạng thái quan trọng — headless chạy 10-50ms/action, không pause thì video vô dụng với người xem.
6. **Telemetry trong video**: dùng `showStepBanner` trước mỗi bước và `showSummaryModal` trước khi đóng browser (xem `e2e/utils/video-telemetry.ts`).
7. **Credentials**: lấy từ env (`CMS_ADMIN_EMAIL`, `CMS_ADMIN_PASSWORD`). Không hardcode password trong spec, POM, hay tài liệu.

---

## 6. Cloud Reporting Workflow

`notify-slack.sh` reads `SLACK_WEBHOOK_URL` from the environment or from
`~/.config/agent-harness/secrets.env` (override with `AGENT_HARNESS_SECRETS`).
A webhook is a credential — never write it into a tracked file. With the
variable unset the script prints where it looked and exits 0, so a run without
Slack configured still succeeds.

```bash
# 1. Upload video lên Google Drive (rclone → gdrive:Index-E2E-Reports/YYYY-MM-DD/)
./scripts/upload-e2e-video.sh <path-to-video.webm> "<Task-Name>"

# 2. Bắn Slack handover
./scripts/notify-slack.sh \
  "<Task Name>" "<GitHub PR URL>" "<Status Details>" \
  "<Google Drive Video URL>" "<Issue Info>" "<Flow Steps>"
```

---

## 7. Verification Checklist Before Handover

- [ ] **Sink Inventory (§2.2) đã điền xong** — mọi action đều đã truy vết `COMMUNITY_EVENTS` / `@OnEvent` / `SmtpService`; mỗi dòng có verification step hoặc lý do N/A cụ thể. *(Không điều kiện — luôn phải có bảng này.)*
- [ ] Mọi sink trong bảng đã được verify thật trong video (Mailpit / NotificationBell / public feed), không mock, không dừng ở toast CMS.
- [ ] Playwright suite pass 100% (`npx playwright test`).
- [ ] Spec mới thực sự được `testMatch` pick up (`npx playwright test --list`).
- [ ] `setup` sinh `.auth/admin.json`, `e2e-authenticated` tái sử dụng được.
- [ ] Spec dùng POM qua `fixtures/index.ts`, không có raw CSS selector.
- [ ] Two-Dimensional Completeness: 100% flow **và** 100% option của mọi enum/select/radio/tab (Zero-Skipped-Option Rule).
- [ ] Export file/dữ liệu: verify UTF-8 BOM và render preview modal ≥ 4s.
- [ ] `recordPause(1500)` đặt giữa các chuyển trạng thái quan trọng.
- [ ] `showStepBanner` mỗi bước + `showSummaryModal` cuối run.
- [ ] Video 1800x1200, đã upload Google Drive và link share công khai còn sống.
- [ ] Slack đã nhận: issue info, PR link, video URL, breakdown các bước.
