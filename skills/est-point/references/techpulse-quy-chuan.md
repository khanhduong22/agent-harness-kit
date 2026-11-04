# KHUNG QUY CHUẨN VẬN HÀNH TECHPULSE 2026
## Hướng Dẫn Đo Lường Năng Suất & Hiệu Quả Làm Việc (Point-Based System)

**Đơn vị ban hành:** Ban Công nghệ TechPulse (CONFIDENTIAL - NỘI BỘ)  
**Đối tượng áp dụng:** PM, Tech Lead & Toàn bộ Nhân viên TechPulse  
**Giai đoạn:** Pilot Data Collection (Sprint 1 - 4)

---

### 1. Định nghĩa Khái niệm "Point" & Mốc Neo Khởi Tạo
- **Bản chất Point:** Point phản ánh **độ phức tạp của bài toán**, không phải đơn vị tính thời gian hành chính (Man-day / Man-hour).
- **Mốc khởi tạo nguyên bản:**  
  $$\text{1 Point} = \text{1 Ngày Công Việc Standard}$$  
  Mốc 1 Point đại diện cho khối lượng và độ phức tạp tiêu chuẩn mà một nhân sự giải quyết trọn vẹn trong 1 ngày làm việc bình thường. Mốc chuẩn này giúp mọi nhân sự dễ dung hợp khái niệm ước lượng ban đầu.
- **Quy đổi theo Level (Trình độ nhân sự):**
  - *Ví dụ Task A (Tính năng Đăng nhập):*
    - **Junior (chưa có kinh nghiệm sẵn):** `1.0 Point`
    - **Senior (đã có sẵn kiến thức / template):** `0.5 Point`

---

### 2. Tối Ưu Năng Suất Qua Tích Lũy Kinh Nghiệm (Learning Curve)
Công việc tương tự dựa trên lịch sử đã làm sẽ giảm độ phức tạp, phản ánh năng suất thực tế tăng lên:
- **Lần 1 (Task Mới):** Xây dựng Module API CRUD lần đầu tiên $\rightarrow$ `1.0 Point`
- **Lần 2 (Task Tương Tự):** Làm Module CRUD cho đối tượng khác $\rightarrow$ `0.7 Point`
- **Lần 3 (Đã Chuẩn Hóa):** Sử dụng lại Template & Script tự động $\rightarrow$ `0.4 Point`

> **Ý nghĩa đối với Nhân viên:** Số Point ETA cho task tương tự giảm giúp nhân sự giải quyết được **NHIỀU TASK HƠN** trong cùng một chu kỳ Timeframe.

---

### 3. Mô Hình Đánh Giá Năng Suất Theo Timeframe (Sprint / Tháng)
Năng suất được đo lường dựa trên tương quan giữa **Tổng số Point** và **Số lượng Task hoàn thành**:

| Kịch Bản | Trạng Thái | Mô Tả | Hành Động Quản Trị |
| :--- | :--- | :--- | :--- |
| **Kịch bản 1** | **Năng Suất Thấp** ❌ | Số Point tích lũy quá ít so với định mức kỳ vọng trong Timeframe | Cần hỗ trợ & Đào tạo |
| **Kịch bản 2** | **Năng Suất Tăng** 📈 | Tổng Point ngang bằng chu kỳ trước, nhưng giải quyết số lượng Task nhiều hơn | Hiệu suất cải thiện rõ rệt |
| **Kịch bản 3** | **Tăng Vượt Trội** 🏆 | Cả tổng số Point và số lượng Task hoàn thành đều tăng mạnh so với trước | Tuyên dương & Thưởng (Bonus) |

---

### 4. Hướng Dẫn Vận Hành Dành Cho PM & Tech Lead

#### VAI TRÒ 01: KIỂM SOÁT POINT (Thẩm Định & Duyệt ETA Point)
1. **Kiểm tra lịch sử task:** PM/Tech Lead rà soát xem nhân sự đã từng thực hiện task tương tự chưa để hạ Point hợp lý (theo Learning Curve).
2. **Duyệt Point theo Level:** Đảm bảo phân bổ đúng độ khó ứng với trình độ Senior / Junior.

#### VAI TRÒ 02: EPIC AS A FEATURE (Chống Phân Rã Task Vụn Vặt)
1. **Giữ đúng tầm nhìn Epic:** Không cho phép nhân viên tự ý xé nhỏ task thành các sub-task quá vụn để lấy số lượng / tích điểm ảo.
2. **Đảm bảo đầu ra hoàn chỉnh:** Mỗi task được đánh Point phải tạo ra giá trị tính năng thực sự (*Feature value*).

---

### 5. Bảng Mẫu Định Giá Task Tham Chiếu (PM & Tech Lead)

| Loại Công Việc (Task Category) | Độ Phức Tạp (Complexity) | Junior Point | Senior Point | Lần 2+ (Lặp lại / Template) |
| :--- | :--- | :---: | :---: | :---: |
| **CRUD API cơ bản / Form đơn giản** | Thấp | `1.0 Point` | `0.5 Point` | `0.3 - 0.4 Point` |
| **Tích hợp Cổng thanh toán / Third-party** | Trung bình | `2.0 Points` | `1.0 Point` | `0.7 Point` |
| **Tối ưu Kiến trúc / Core Service System** | Rất cao | *Không phân công* | `2.0 - 3.0 Points` | `1.5 Points` |
| **Fix Bug thường / Refactoring nhỏ** | Thấp | `0.5 Point` | `0.25 Point` | `0.2 Point` |

---

### 6. Hướng Dẫn Thực Hành Dành Cho Nhân Viên
- **Tái Sử Dụng Resource:** Xây dựng thư viện component, code snippet để làm các task sau nhanh hơn.
- **Tự Động Hóa Quy Trình:** Tạo Script / Automation giúp giảm thời gian làm việc thủ công lặp đi lặp lại.
- **Chủ Động Nhận Task Tương Tự:** Nhận các task thuộc thế mạnh giúp tăng số lượng task giải quyết trong Sprint.

---

### 7. Lộ Trình Triển Khai Pilot (2026)
- **Sprint 1 - 2:** Thử nghiệm định giá Point & Thu thập dữ liệu thực tế.
- **Sprint 3 - 4:** Phân tích đường cong học tập & Tinh chỉnh Benchmark chuẩn hóa.
