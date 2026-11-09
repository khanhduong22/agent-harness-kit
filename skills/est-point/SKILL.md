---
name: est-point
description: "Thực hiện ước lượng Story Point chuẩn hóa cho User Story, Task, Subtask và Bug theo Khung Quy Chuẩn Vận Hành TechPulse 2026 (1 Point = 1 Ngày Công Việc Standard, quy đổi Level Junior 1.0x / Senior 0.5x, Learning Curve Lần 1 1.0x / Lần 2 0.7x / Lần 3+ 0.4x, Bảng Mẫu Định Giá Task 0.2 - 3.0 Points, tích hợp trực tiếp với github-task-breakdown để đồng bộ trường Point Est / Point Act trên GitHub Projects V2)."
license: MIT
metadata:
  version: 2.0.0
  author: TechPulse Engineering & Architecture Team
  category: agile-engineering
  domain: task-estimation
  tags: [story-point, agile, scrum, estimation, techpulse, sprint-planning, standard-day]
---

# EST POINT — Khung Quy Chuẩn Vận Hành TechPulse 2026 (`1 Point = 1 Ngày Công Việc Standard`)

Hệ thống kỹ năng thẩm định và ước lượng **Story Point** chuẩn hóa theo **[Khung Quy Chuẩn Vận Hành TechPulse 2026](https://docs.google.com/presentation/d/15YZOTSmp-PWgte3DsmVwN01hmZzXV0w32INu84Lt0ug/edit?slide=id.p2#slide=id.p2)** (*Hướng dẫn Đo lường Năng suất & Hiệu quả Làm việc*).

---

## 1. Triết Lý & Mốc Neo Khởi Tạo Nguyên Bản (Slide 2)

1. **Bản chất của Point:** Point phản ánh **độ phức tạp của bài toán**, quy mô kỹ thuật và rủi ro, không phải đơn vị chấm công hành chính (Man-hour) thuần túy.
2. **Mốc Khởi Tạo Nguyên Bản (`TechPulse Baseline`):**
   $$\text{1.0 Point} = \text{1 Ngày Công Việc Standard (1 Standard Working Day)}$$
   - Mốc **`1.0 Point`** đại diện cho khối lượng và độ phức tạp tiêu chuẩn mà một nhân sự giải quyết trọn vẹn trong **1 ngày làm việc bình thường**.
   - Tuyệt đối **KHÔNG** dùng thang Fibonacci nguyên tối thiểu 1 (`1, 2, 3, 5, 8...`) cho các task nhỏ (vì gán `1.0 - 2.0 Point` cho một bugfix 1–2 giờ sẽ làm sai lệch hoàn toàn định mức 1 ngày công việc).
3. **Thang Điểm Chuẩn Hóa (`TechPulse Standard Point Scale`):**
   - Sử dụng các mốc thập phân chuẩn theo Bảng Mẫu Định Giá TechPulse:
     `[0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0, 2.5, 3.0]`
4. **Vai Trò 01 — Kiểm Soát Point (Thẩm Định & Duyệt ETA Point - Slide 5):**
   - **Kiểm tra lịch sử task:** Rà soát xem nhân sự đã từng thực hiện task tương tự chưa để hạ Point hợp lý theo **Learning Curve**.
   - **Duyệt Point theo Level:** Phân bổ đúng điểm ứng với trình độ **Junior (`1.0x`)** / **Senior (`0.5x`)**.
5. **Vai Trò 02 — Epic as a Feature & Chống Cộng Trùng (Slide 5):**
   - **Chống phân rã vụn vặt:** Không xé nhỏ task thành các sub-task quá vụn để lấy số lượng. Mỗi task được đánh Point phải tạo ra giá trị tính năng thực sự (*Feature value*).
   - **Ghi nhận điểm đơn cấp (`No Double Counting`):** Điểm chỉ được ghi nhận ở **Sub-issue thực thi** (hoặc ở Issue độc lập nếu không có sub-issue). Nếu một Epic/Story cha đã được tách thành các Sub-issue có Point, thì Story cha để `Point Est = null / 0` (hoặc tổng hợp báo cáo nhưng không cộng trùng vào tổng Point cá nhân).

---

## 2. Hệ Số Quy Đổi Theo Level & Learning Curve (Slide 2 & Slide 3)

### A. Quy Đổi Theo Level (Slide 2)
| Cấp bậc | Hệ số Level | Ví dụ Task A (Tính năng Đăng nhập / CRUD cơ bản) | Mô tả |
| :--- | :---: | :---: | :--- |
| **Level Junior** | `1.0x` | **`1.0 Point`** | Chưa có kinh nghiệm sẵn, cần thời gian làm quen |
| **Level Senior** | `0.5x` | **`0.5 Point`** | Đã có sẵn kiến thức nền tảng, kiến trúc & template |

### B. Tối Ưu Năng Suất Qua Tích Lũy Kinh Nghiệm — Learning Curve (Slide 3)
| Tần suất thực hiện | Hệ số Learning Curve | Ví dụ Module API CRUD (Mốc 1.0 Point) | Mô tả |
| :--- | :---: | :---: | :--- |
| **Lần 1 (Task Mới)** | `1.0x` | **`1.0 Point`** | Xây dựng Module API CRUD lần đầu tiên |
| **Lần 2 (Task Tương Tự)** | `0.7x` | **`0.7 Point`** | Làm Module CRUD cho đối tượng khác tương đương |
| **Lần 3+ (Đã Chuẩn Hóa)** | `0.4x` | **`0.4 Point`** | Sử dụng lại Template, Component & Script tự động |

> **Công thức tính điểm chuẩn TechPulse:**
> $$\text{Point} = \text{Junior Base Point} \times \text{Level Factor} \times \text{Learning Curve Factor}$$
> *(Hoặc tra trực tiếp từ **Bảng Mẫu Định Giá Task Tham Chiếu** ở Mục 3 bên dưới).*

---

## 3. Bảng Mẫu Định Giá Task Tham Chiếu Chuẩn (Slide 6 — PM & Tech Lead)

Đây là **bảng chuẩn bắt buộc** từ Slide 6 của Khung Quy Chuẩn Vận Hành TechPulse 2026:

| Loại Công Việc (Task Category) | Độ Phức Tạp (Complexity) | Junior Point (Lần 1) | Senior Point (Lần 1) | Lần 2+ (Lặp lại / Đã có Template) |
| :--- | :---: | :---: | :---: | :---: |
| **1. Fix Bug thường / Refactoring nhỏ / Chỉnh UI-CSS-Layout nhỏ** | Thấp | **`0.5 Point`** | **`0.25 Point`** | **`0.2 Point`** |
| **2. CRUD API cơ bản / Form đơn giản / 1 Section hoặc Component UI** | Thấp | **`1.0 Point`** | **`0.5 Point`** | **`0.3 - 0.4 Point`** |
| **3. Tích hợp Cổng thanh toán / Third-party / Trang hoàn chỉnh + API / Multi-flow** | Trung bình | **`2.0 Points`** | **`1.0 Point`** | **`0.7 Point`** |
| **4. Tối ưu Kiến trúc / Core Service System / Engine phức tạp** | Rất cao | *Không phân công* | **`2.0 - 3.0 Points`** | **`1.5 Points`** |

---

## 4. Danh Mục Tham Chiếu Chi Tiết Theo Vai Trò (`1 Point = 1 Ngày Công Việc Standard`)

### A. Frontend Development (`FE`)
| Mã | Case công việc | Junior (1st) | Senior (1st) | Lần 2+ (Repeat) | Điều kiện / Phạm vi chuẩn |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `FE-01` | Thay đổi text, label, link, màu, spacing, ẩn scrollbar | `0.5` | **`0.25`** | **`0.2`** | UI tweak / CSS / không đổi kiến trúc |
| `FE-02` | Thêm Button / Input / Pill Tab / Header đồng bộ Figma | `0.5` | **`0.25`** | **`0.2`** | Có sẵn Design System |
| `FE-03` | Xây dựng Modal / Popup / Bottom Sheet đơn giản | `1.0` | **`0.5`** | **`0.3 - 0.4`** | Có thiết kế và component nền |
| `FE-04` | Dark Mode cho 1 Section / Component (Home / Profile section) | `1.0` | **`0.5`** | **`0.3 - 0.4`** | Lần 1: `0.5 pt` (Senior); các section lặp lại tiếp theo: `0.3 pt` |
| `FE-05` | Form nhập liệu / CRUD UI (Create/Edit Alert, Watchlist) | `1.0` | **`0.5`** | **`0.3 - 0.4`** | Validation, submit, loading, error state |
| `FE-06` | Trang Listing / Trang Detail / Bảng dữ liệu kết nối API | `1.0` | **`0.5`** | **`0.4`** | Có API, phân trang, empty/loading state |
| `FE-07` | Chuẩn hóa luồng phức tạp / Multi-condition Filter / Matrix (VD: 13 luồng Notification, Trang Cổ phiếu nổi bật Full) | `2.0` | **`1.0`** | **`0.7`** | Nhiều trạng thái, kết hợp filter/sort/routing hoặc tích hợp API mới |
| `FE-08` | Kiến trúc Realtime UI / WebSocket / Core State Engine | — | **`2.0`** | **`1.5`** | WebSocket, reconnect, đồng bộ đa luồng |

### B. Backend & Database Development (`BE` / `DB`)
| Mã | Case công việc | Junior (1st) | Senior (1st) | Lần 2+ (Repeat) | Điều kiện / Phạm vi chuẩn |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `BE-01` | Thêm field DB / sửa query / fix API mapping hoặc sort/filter nhỏ | `0.5` | **`0.25`** | **`0.2`** | Migration đơn giản, 1 endpoint |
| `BE-02` | CRUD API cơ bản / Event Listener (VD: `@mention` notification, Watchlist CRUD) | `1.0` | **`0.5`** | **`0.3 - 0.4`** | Validation, unit test, xử lý lỗi đầy đủ |
| `BE-03` | Tích hợp Third-Party / Multi-channel Notification (In-App + Email + Telegram) / All-in-one Aggregation API | `2.0` | **`1.0`** | **`0.7`** | Kết nối đa dịch vụ, webhook, hoặc nhiều bảng |
| `BE-04` | Core Service System / Worker Engine / Tối ưu Kiến trúc & Dockerfile / Multi-Portfolio NAV Engine | — | **`2.0 - 3.0`** | **`1.5`** | Kiến trúc lõi, cron/worker matching, hiệu năng cao |

### C. Bug Fixing & Refactoring (`BUG`)
| Mã | Case công việc | Junior (1st) | Senior (1st) | Lần 2+ (Repeat) | Điều kiện / Phạm vi chuẩn |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `BUG-01` | Fix Bug UI / CSS / Layout / Link / Auto-close modal / Scrollbar | `0.5` | **`0.25`** | **`0.2`** | Phạm vi 1–2 component trên FE |
| `BUG-02` | Fix Bug logic vừa / API mapping / Zustand cache tab / Fallback data Mozyfin | `0.5 - 1.0` | **`0.25 - 0.5`** | **`0.2 - 0.3`** | Xử lý state hoặc chuẩn hóa dữ liệu giữa FE & API |
| `BUG-03` | Fix Bug Fullstack (FE + BE) / Đồng bộ nhiều module (VD: 3 tab Cộng đồng FE+BE, đồng bộ chỉ số Market Index) | `1.0 - 2.0` | **`0.5 - 1.0`** | **`0.4 - 0.7`** | Chạm cả FE lẫn BE hoặc nhiều luồng dữ liệu |
| `BUG-04` | Fix Bug Race Condition / Mất dữ liệu / Kiến trúc Core | — | **`1.5 - 2.0`** | **`1.0`** | Cần điều tra sâu và bảo toàn dữ liệu |

---

## 5. Mô Hình Đánh Giá Năng Suất Theo Timeframe (Slide 4)

Năng suất trong Sprint / Tháng được đo lường dựa trên tương quan giữa **Tổng số Point** và **Số lượng Task hoàn thành** (với định mức chuẩn 1 tuần làm việc 5 ngày $\approx 5.0\text{ Points}$ baseline):
- **Kịch bản 1 — Năng Suất Thấp:** Số Point tích lũy quá ít so với định mức kỳ vọng trong Timeframe $\rightarrow$ *Cần hỗ trợ & Đào tạo*.
- **Kịch bản 2 — Năng Suất Tăng:** Tổng Point ngang bằng chu kỳ trước, nhưng giải quyết **số lượng Task nhiều hơn** (nhờ Learning Curve giảm Point trên mỗi task lặp lại) $\rightarrow$ *Hiệu suất cải thiện rõ rệt*.
- **Kịch bản 3 — Tăng Vượt Trội:** Cả **tổng số Point** và **số lượng Task hoàn thành** đều tăng mạnh so với trước $\rightarrow$ *Tuyên dương & Bonus*.

---

## 6. Công Cụ CLI Hỗ Trợ (`scripts/estimate.js`)

```bash
# 1. Tra cứu case trong Casebook theo từ khóa
node ~/.gemini/config/skills/est-point/scripts/estimate.js search "crud"

# 2. Liệt kê toàn bộ case theo nhóm (frontend, backend, bug)
node ~/.gemini/config/skills/est-point/scripts/estimate.js list

# 3. Tính điểm theo chuẩn TechPulse 2026 (JuniorBasePoint, Level [senior|junior], Repeat [1|2|3])
node ~/.gemini/config/skills/est-point/scripts/estimate.js calc 1.0 senior 1
# Output: {"juniorBasePoint": 1, "level": "senior", "repeatCount": 1, "rawPoint": 0.5, "standardPoint": 0.5}

node ~/.gemini/config/skills/est-point/scripts/estimate.js calc 0.5 senior 2
# Output: {"juniorBasePoint": 0.5, "level": "senior", "repeatCount": 2, "rawPoint": 0.18, "standardPoint": 0.2}
```

---

## 7. Liên Kết Với `github-task-breakdown` & GitHub Projects V2

Khi tạo mới hoặc cập nhật Task / Sub-issue / Bug trên GitHub Projects V2 (`Index` — `PVT_kwDODcsuC84BDOQk`):
1. **Áp dụng đúng chuẩn `1 Point = 1 Ngày Công Việc Standard`**:
   - Với **Senior Developer (`khanhduong22`)**:
     - Bug UI / CSS / Layout nhỏ (`BUG-01`, `FE-01`): **`0.2 - 0.25 Point`**
     - Bug logic / API mapping / Dark Mode 1 section lặp lại (`BUG-02`, `FE-04 repeat`): **`0.3 - 0.4 Point`**
     - Task CRUD API / Form / Feature chuẩn / Bug Fullstack (`BE-02`, `FE-05`, `BUG-03`): **`0.5 Point`**
     - Feature trung bình-lớn / 13 luồng Notification / Trang mới hoàn chỉnh kết nối API (`FE-07`, `BE-03`): **`0.7 - 1.0 Point`**
     - Core Engine / Kiến trúc lớn (`BE-04`): **`1.5 - 2.0 Points`**
2. **Không cộng trùng Story Cha (`No Double Counting`)**:
   - Nếu Issue cha (VD: `#3881`, `#3924`, `#3929`, `#3996`, `#3999`, `#4016`) đã có các Sub-issue con được gán Point, thì chỉ ghi nhận Point ở các **Sub-issue thực thi** (đặt `Point Est` / `Point Act` của Issue cha về `null` hoặc chỉ dùng để nhìn tổng quan, tránh cộng gấp đôi).
3. **Đồng bộ lên GitHub Projects V2**:
   - **`Point Est`** (`PVTF_lADODcsuC84BDOQkzhoOFI0`, kiểu `NUMBER`): Điền số thập phân chuẩn (`0.2`, `0.25`, `0.3`, `0.5`, `0.7`, `1.0`, `1.5`, `2.0`).
   - **`Point Act`** (`PVTF_lADODcsuC84BDOQkzhoOFJM`, kiểu `NUMBER`): Điền khi task chuyển sang `Ready for QA` / `Done`.
