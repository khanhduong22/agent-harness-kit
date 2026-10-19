# PROCESS solution sheet — "Vibe-code với AI"

Schema: `references/genres/process.md` → *The PROCESS solution sheet*.
Every string rendered in `vibe-code-voi-ai.html` traces to a line here.

**Storyboard v3.1, revision 3 — PRODUCT-FIRST (2026-08-27).** The workflow, the seven beats and the
UI → DB → BE claim are unchanged from revision 2. What changed is WHAT THE STATIONS ARE: the brief is
a real one-page document (`station-brd-doc`), the app is a browser window running a real dashboard
(`station-webapp` + `webapp-skin--dashboard`, `--win-w` 640), the deploy beat is the responsive pair
(`station-deploy-responsive`, option C2), and the whole canvas runs the two-tier LOD. Revisions 1–2
still hold: two green derivation legs, `my-app.pages.dev`, no access-control claim, every string ON
an element in ENGLISH while captions / narration / heading stay Vietnamese
(`references/genres/process.md` → *Language*).

**Revision 3.1 (2026-08-27) — layout only.** The right column was re-stacked so the three derivation
pull-lines read as short, mostly-horizontal pulls instead of climbs across the dashboard. Nothing in
AUDIENCE / CORE WORKFLOW / CAST / STEPS / DECISIONS / NUMBERS / LOOP changed; see **REVISION 3.1**
below for the measured before/after and every knock-on.

**Revision 4 (2026-08-27) — the b5 snap block, RE-BAKED to V2 "cartridge modules"; user-approved
("V2 ổn. Em làm lại cái html để apply").** The golden was frozen, and this is a sanctioned
regeneration taken on the record: it invalidates the previous SHA-256, which is re-recorded in
`examples/README.md` in the same change. Nothing in AUDIENCE / CORE WORKFLOW / CAST / STEPS /
DECISIONS / NUMBERS / LOOP changed, no window and no keyframe stop changed, and not one on-screen
STRING changed except the block's own new texture-class interiors. What changed is the SHAPE of one
station and the bottom-left layout it pushed. See **REVISION 4** below.

---

## AUDIENCE

Người không rành kỹ thuật muốn tự dựng app bằng AI (founder / người làm sản phẩm).
**Niềm tin cần sửa:** "vibe-code là AI làm hết, khỏi cần back-end" → không: front-end đi
trước để CHỐT Ý, back-end vẫn phải có, chỉ là AI suy ra nó SAU.

## CORE WORKFLOW

Con đường ngắn nhất vẫn dạy được (viết TRƯỚC storyboard, không lấy cấu trúc bài viết):

```
[Brief · 1 page] → (AI builds the UI) → [clickable screen + mock data]
        → <Looks right?> --not yet--> quay lại AI với 1 câu sửa
                        --OK-------> (AI suy ngược) UI --xanh--> [items] --xanh--> [Back-end]
                                   → [UI+BE+DB khớp] → [link + app thật]
```

**Chuỗi suy luận là UI → DB → BE, và đó là bài học của cut** (sửa của người dùng,
storyboard v3.1): màn hình có trước; từ màn hình AI suy ra bảng dữ liệu; từ bảng vừa suy ra
đó AI mới dựng khối back-end. Cả hai chặng đều là cạnh XANH (`derivation`), nên hình vẽ tự
nó kể đúng thứ tự mà không cần chú thích thêm.

Bảy nhịp: 1 toàn cảnh · 5 bước · 1 toàn cảnh chốt. Happy path duy nhất; nhánh không đi
vẫn được vẽ, mờ, nhãn còn đọc được.

## CAST

**actors**

| vai | là ai với khán giả này | bước nào sở hữu |
|---|---|---|
| AI · builds the UI | công cụ, không phải người; không thuộc nhóm bạn (`external`) | bước 2 |
| AI · infers DB + BE | cùng công cụ, việc khác — nên là trạm khác, cùng ký hiệu | bước 4 |

Không có hình người ở bất kỳ đâu (object-vignette doctrine). Người viết brief KHÔNG được
vẽ thành chip: brief chính là hiện vật của họ, và vignette đã nói đủ.
`NO ROW — người viết brief vẽ bằng chính hiện vật (brief sheet)`.

**artifacts**

| tên + phiên bản | ai SỞ HỮU | bước tạo → bước dùng |
|---|---|---|
| BRD · 1 page (tài liệu một trang) | bạn | vào từ CAST → bước 2 |
| web app chạy được (dashboard trong khung trình duyệt) | AI · builds the UI | bước 3 → bước 3, 4 |
| mock data · json | AI · builds the UI | bước 3 → bước 3 (nuôi UI) |
| Câu sửa (1 câu) | bạn | bước 3 → bước 2 (vòng sau) |
| `items` (bảng) | AI · infers DB + BE | bước 4 → bước 5 |
| Back-end (receive · validate · save) | AI · infers DB + BE | bước 5 (dựng TỪ bảng) → bước 6 |
| UI + BE + DB đã khớp | AI | bước 5 → bước 6 |
| my-app.pages.dev | bước Deploy | bước 6 → người dùng |

## STEPS (đây là BEAT, không phải node)

| n | bước (có ĐỘNG TỪ) | actor | vào → ra | ENTRY | EXIT |
|---|---|---|---|---|---|
| 1 | Nhìn toàn cảnh dây chuyền | — | — | mở cut | khán giả thấy hình dạng + biết bắt đầu từ brief |
| 2 | Viết brief 1 trang rồi đưa cho AI | bạn | — → BRD · 1 page | có ý tưởng | tài liệu một trang đọc được: mục tiêu, người dùng, luồng chính 3 bước, màn hình chính, dòng gạch phạm vi |
| 3 | AI dựng ra web app, bạn xem rồi trả lời "Looks right?" | AI · builds the UI → bạn (người quyết) | BRD → web app + mock data → Câu sửa **hoặc** OK | có brief 1 trang | app mở được trong trình duyệt và bạn nói được "not yet, sửa X" hoặc "OK" |
| 4 | AI đọc chính giao diện, suy ngược ra bảng dữ liệu | AI · infers DB + BE | web app (đã chốt) → `items` | nhánh OK được chọn | mỗi phần tử đang hiện dữ liệu có đúng một cột, không thừa cột nào |
| 5 | AI dựng Back-end THEO bảng vừa suy ra | AI · infers DB + BE | `items` (+ UI) → Back-end → bản đã khớp | đã có bảng | BE biết nhận-kiểm-lưu; ba mảnh khớp vì cùng bám một bảng |
| 6 | Deploy ra link; cùng app đó trên màn hẹp | bước Deploy | bản đã khớp → link + cặp trình duyệt/điện thoại | bản đã khớp | cùng một địa chỉ, cùng nội dung, chỉ xếp lại |
| 7 | Nhìn lại toàn cảnh + chốt | — | — | mọi bước đã chạy | khán giả nhớ: FE trước ≠ bỏ back-end |

**Persona audit — mỗi beat khán giả LÀM gì tiếp?**

| beat | thấy gì | hỏi gì | cái gì trả lời ngay trên khung |
|---|---|---|---|
| 1 | dây chuyền mờ, brief sáng | bắt đầu từ đâu? | brief là thứ duy nhất sáng |
| 2 | tài liệu BRD mở ra ở tầng LOD gần | "brief một trang thì viết cái gì?" | năm ô của chính tài liệu: Goal · Users · Core flow (1-2-3) · Main screen · Not now |
| 3 | app thật + hình thoi + hai nhánh | "làm gì có data mà chạy?" / "sửa thì phải làm lại từ đầu à?" | hũ `mock data · json` cắm vào app; mũi tên cam quay về AI + giấy nhớ `fix the main button` |
| 4 | ba phần tử UI → ba cột | "DB ở đâu ra?" | ba đường xanh rời từ chính con số `128`, tên dòng `Item one`, ô ngày `Added yesterday` |
| 5 | bảng → Back-end, rồi ba mảnh khít nhau | "thế BE ở đâu ra?" | cạnh xanh bảng → Back-end + nhãn `built from the items table`; caption nói rõ UI trước, rồi DB, rồi BE |
| 6 | link + cặp trình duyệt/điện thoại | "gửi cho người khác xem thử được không?" | nhãn `share the link · opens on any phone` + cặp C2 với cùng một địa chỉ và nhãn `Same app / narrower screen` |
| 7 | toàn cảnh + băng chốt | "vậy có cần back-end không?" | băng `FE-FIRST ≠ SKIP BACKEND` |

Không có thuật ngữ ngoài vốn từ khán giả: `deploy` được giải nghĩa ngay trong caption beat 6
(*đẩy ra một cái link, gửi cho người dùng thử*), và khối Back-end nói ba việc của nó bằng câu
thường (`receive what you send` / `check it is valid` / `save it to the table`), không dùng `API`
làm nhãn.

**Không có câu nào nói về quyền truy cập.** Bản đầu ghi *link công khai · ai có link đều mở được*;
người duyệt đọc ra một tuyên bố bảo mật mà cut không có cơ sở để đưa ra. Nhãn bây giờ nói MỤC ĐÍCH
(`share the link · opens on any phone`), còn cấu hình quyền là việc của người deploy.

## DECISIONS

| câu hỏi (trên hình thoi) | nhánh | đi đâu |
|---|---|---|
| **Looks right?** | `not yet` | quay về **AI · builds the UI** (trạm phải LÀM lại), mang theo 1 câu sửa |
| | `OK` | sang **AI · infers DB + BE** |

Cut này vẽ **cả hai**: `not yet` chạy sống ở beat 3 (2 nhịp), `OK` chạy sống ở beat 4; nhánh
không chạy vẫn nằm đó, mờ hơn, nhãn còn đọc. Điều kiện nằm trên CẠNH (`.pill`), câu hỏi
nằm trong hình thoi. AI không bao giờ là người quyết — người quyết là bạn, và đó là lý do
hình thoi mang màu `service`, không mang ký hiệu tia AI.

## NUMBERS

| số | giá trị | dùng ở đâu |
|---|---|---|
| độ dài brief | **1 trang** | nhãn tab brief, caption beat 2 |
| số mỏ neo ngữ nghĩa trên app | **3** | đúng ba `[data-anchor]` (hợp đồng template v2) — và vì thế ba đường xanh, ba cột |
| số cột bảng `items` | **3** | bảng schema (bằng số ô nhập, không hơn) |
| số nhịp vòng lặp hiển thị | **2** | beat 3 chạy 2 gói phản hồi trên cung quay lại |
| số mảnh phải khớp | **3** (UI · BE · DB) | khối snap 3 mảnh |
| `NO NUMBER IN SOURCE` — tổng số vòng trước khi xong | — | cung quay lại chỉ mang GIA SỐ, không mang "×N" |
| `NO NUMBER IN SOURCE` — số người dùng thử | — | không vẽ chip đếm người |
| `NO NUMBER IN SOURCE` — thời gian mỗi bước | — | không có nhãn phút/giờ ở đâu cả |
| `NOT A NUMBER — texture` | `128` · `12` · `↑ 8%` · `Mon…Sat` · `+ 2 more` | **seed data bên trong sản phẩm giả**, không phải số liệu của nguồn: không caption nào đọc chúng lên, và chúng không nằm trong khối NUMBERS như một tuyên bố |

## LOOP

- **Gia số mỗi vòng:** *một câu sửa cụ thể cho MỘT thứ trên màn hình* — `fix the main
  button`, không phải "làm lại". Viết trên giấy nhớ cưỡi trên cung quay lại.
- **Số vòng cut kể:** 2 nhịp (thấy được là nó lặp, không nói nó lặp mấy lần).
- **Cái gì kết thúc vòng:** bạn trả lời `OK` — con người, không phải AI.
- Cung quay lại trỏ về **AI · builds the UI** (trạm phải làm lại), không trỏ về brief.

---

## Audits over this sheet

- **Ownership** — mỗi hiện vật đúng một chủ ✓ (bảng biểu trên).
- **Continuity** — `artifact in` của mỗi bước là `artifact out` của bước trước hoặc là
  entry trong CAST ✓ (brief là entry duy nhất).
- **Entry/exit honesty** — không bước nào có EXIT là "xong"; mỗi EXIT nói ai xác nhận và
  bằng gì ✓.
- **Increment** — viết trước storyboard ✓.
- **No invented numbers** — 4 dòng `NO NUMBER IN SOURCE` ở trên ✓.
- **Five-second test** — beat 1/7 ở gate `overview`: đọc được HÌNH DẠNG (một dây chuyền,
  một vòng cam quay lại, một nhánh xanh suy ngược) + băng chốt. Chi tiết đọc ở 5 beat kia.

## Phase 3 — component mapping table (một query `--domain components` cho mỗi dòng CAST)

| Sheet component | Component ID | Snippet Ref | Role | States used |
|---|---|---|---|---|
| BRD · 1 trang | `document-spec` | `snippets/process-stations.html#station-brd-doc` | `data` | `flow-attention` (beat 1), LOD close (beat 2) |
| AI · builds the UI | `ai-assistant` | `#station-ai-spark` (full) | `external` | — |
| AI · infers DB + BE | `ai-assistant` | `#station-ai-spark` (`--sm`) | `external` | — |
| Web app bấm được (dashboard) | `prototype-screen` | `snippets/process-webapp-templates.html#station-webapp-dashboard` | `client` | LOD close (beat 3, 4) |
| Looks right? | `decision-point` | `#station-decision-diamond` | `service` | — |
| Câu sửa (giấy nhớ) | `feedback-note` | `#station-sticky-note` | `async` (mặc định vàng cam của shell) | — |
| Back-end (API·kiểm tra·lưu) | `test-checklist` | `#station-list-card` | `service` | — |
| my-app.pages.dev | `deploy-url` | `#station-url-pill`, **bên trong** `process-webapp-templates.html#station-deploy-responsive` | `infra` | — |
| **mock data · json** | `NO ROW — custom shape` | `#station-data-jar` | `data` | — |
| **`items` (bảng)** | `NO ROW — custom shape` | `#station-schema-table` | `data` | — |
| **UI+BE+DB đã khớp** | `NO ROW — custom shape` | `#station-snap-cartridge` (rev 4; trước là `#station-snap-seam`) + `#mini-dashboard` / `#mini-api-card` / `#mini-items-table` | `client`/`service`/`data` | — |
| **cùng app đó trên điện thoại** | `NO ROW — custom shape` | `process-webapp-templates.html#station-deploy-responsive` (`.phone--mini`, KHÔNG có ripple) | `client` | — |

**0-results recorded** (all after the `-n 5` retry, per Query Contract rule 9):
`"database table schema columns"` → 0 · `"running app on a phone"` → 0 ·
`"backend service block"` → 0 (best 2.02, floor 2.0) ·
`"the three pieces UI backend database snapped together"` → 0.
Cả bốn đều đã có SHELL đã được duyệt trong `templates/snippets/process-stations.html`; chúng
là hình tự dựng theo *semantic-tracing licence*, không phải hàng lấy từ catalog.

**False friends considered and REJECTED:**
- `REJECTED team-stakeholder` — query VN "màn hình bấm được cho người dùng xem thử" trả về
  chip nhóm người; cast này KHÔNG vẽ người, và thứ cần vẽ là màn hình.
  Query lại bằng tiếng Anh trả `prototype-screen` (6.76) — dùng cái đó.
- `REJECTED document-spec` cho "hũ mock data" và cho "bảng dữ liệu" — cả hai query VN đều
  rơi về brief sheet; brief là ĐẦU VÀO của con người, không phải data máy sinh ra.
- `REJECTED person-actor / team-stakeholder` cho "người viết brief" — object-vignette
  doctrine: brief sheet đã đại diện cho họ, thêm chip là thêm một trạm không tải thông tin.

**Payload rows:** `file` (4.22, `"document transfer"`) = brief chạy trên cạnh xám;
`feedback` (9.36) = câu sửa chạy trên cung cam. Không có glyph cargo nào được VẼ trong cut
này (một chấm trơn), nên `features` KHÔNG khai `payload-glyphs` và `glyphs` để rỗng.

## REVISION 3 — station swaps, anchor map, LOD plan, retire decisions

**CORE WORKFLOW unchanged.** Cùng bảy nhịp, cùng chuỗi UI → DB → BE. Chỉ đổi *cái gì được vẽ*.

### Station swaps

| trạm | revision 2 | revision 3 | lý do |
|---|---|---|---|
| brief | `.brd` `station-brief-sheet` (314×220) | `.doc` **`station-brd-doc`** (360×380, LOD 2 tầng) | product-first: brief là một TÀI LIỆU thật, và chỉ có lưới nhãn/giá trị mới cho tầng xa vẽ xương trong khi tên mục vẫn đọc được như cấu trúc |
| UI | `.scr` `station-screen` (form 3 ô, 330×390) | `.win` **`station-webapp` + `webapp-skin--dashboard`**, `--win-w:640` | user chốt dashboard làm flavor mặc định; UX thật (toolbar · KPI · chart · list), **không có form** |
| deploy | `.url` + `.phone` có ripple | **`station-deploy-responsive`** (C2: `.win--deploy` 470 + `.phone--mini` 216 + pill) | user chốt C2 (*"đầy đủ hơn"*); ripple bị bỏ vì claim của nó là "vừa có người bấm", không phải claim của nhịp này |

### Anchor map (hợp đồng template v2, invariant #2 — đúng BA mỏ neo)

| `data-anchor` | phần tử UI | mép phải ĐO ĐƯỢC | tới hàng |
|---|---|---|---|
| `amount` | con số KPI `128` (`.kpi__v span`) | x 892.8, y 229 | `amount · number` (y **432**) |
| `name` | tiêu đề dòng 1 `Item one` (`.icard__t .lod`) | x 969.2, y 477 | `name · text` (y **478**) |
| `created_at` | ô ngày dòng 2 `Added yesterday` (`.icard__w .lod`) | x 1426, y 552 | `created_at · date` (y **524**) |

(Ba giá trị `y` của hàng là của **revision 3.1**; bản 3 để bảng ở đỉnh cột nên ba hàng nằm ở
y 120/166/211 — xem REVISION 3.1 bên dưới.)

Ba cột đọc từ BA CHỖ KHÁC NHAU — đó chính là bài học: lược đồ được đọc ra từ giao diện, không phải
từ một cái form. **Thứ tự hàng của bảng `items` được xếp theo thứ tự dọc của ba mỏ neo**
(`amount` → `name` → `created_at`) để ba đường xanh không cắt nhau; đây là một quyết định bố cục,
không phải một tuyên bố về lược đồ.

### LOD plan

| trạm | tầng xa (mặc định) | tầng gần bật ở nhịp | phần thưởng của tầng gần |
|---|---|---|---|
| `brief` (`.lodw-brief`) | 4 ô giá trị là thanh xương | **b2** | Core flow nở ra thành **ba bước đánh số**; Goal / Users / Main screen thành câu thật |
| `app` (`.lodw-app`) | tên dòng + ô ngày là thanh xương; delta KPI, nhãn trục, meta thẻ ẩn | **b3 và b4** (tắt ở nhịp toàn cảnh giữa hai nhịp) | `all time` / `new` / `vs last week`, `Mon…Sat`, `In list`, và hai tên dòng + hai ô ngày |

Không mỏ neo nào nằm trong `[data-lod="close"]` (`ANCHOR-GATED` xanh): cả ba dùng khung crossfade
`.lod`, thứ không bao giờ bị cổng. Chiều cao trạm y hệt ở cả hai tầng; chỉ `opacity` chạy, và chạy
SAU khi camera dừng (0.34s = 1.0119% master).

### Retire / keep decisions

- **Hũ `mock data · json`: GIỮ.** Dashboard đầy số thật-trông-như-thật; nếu bỏ hũ thì seed data đọc
  ra như dữ liệu thật, mà "chưa có cơ sở dữ liệu nào cả" đúng là điều nhịp này phải nói. Hũ nằm
  trong khung của b2 lẫn cạnh app, mũi tên vẫn chạy JAR → APP.
- **Ripple điện thoại: BỎ.** Doctrine của nhịp deploy nói thẳng: ripple = "vừa có người bấm";
  nhịp này nói "cùng app đó, màn hẹp hơn". Narration nhịp 6 đã viết lại theo (bỏ "bấm nút vẫn chạy").
- **Khối snap 3 mảnh: GIỮ** nguyên vai trò minh hoạ ở b5, packet chạy xuyên.
- **`.scr` / `.brd` / `.field` / `.cta` / `.ripple`: gỡ khỏi CSS của cut** — không trạm nào dùng nữa.

### Five-second audit — chạy lại từng nhịp trên contact sheet mới (k toàn cảnh 0.69)

| nhịp | khán giả thấy trong 5 giây | đạt? |
|---|---|---|
| 1 | một dây chuyền: tài liệu → tia AI → cửa sổ trình duyệt → hình thoi → bảng → khối 3 mảnh → cặp trình duyệt/điện thoại. Hình dạng đọc được dù chữ là texture | ✓ hình dạng sản phẩm dễ nhận hơn hộp-có-nhãn ở k cao hơn của bản cũ |
| 2 | tài liệu BRD mở ra, 5 mục có chữ thật, mũi tên sang tia AI | ✓ |
| 3 | app thật trong khung trình duyệt + hình thoi hai nhánh + giấy nhớ cam | ✓ (đường xanh đã hạ xuống .32 nên không "gạch" lên app) |
| 4 | ba đường xanh rời khỏi ba phần tử, đáp xuống ba hàng | ✓ rõ nhất trong cả cut |
| 5 | ba mảnh khít nhau, một chấm chạy xuyên | ✓ |
| 6 | hai màn hình cùng một địa chỉ + pill `Live` | ✓ đọc ra "cùng app, màn hẹp hơn" |
| 7 | toàn cảnh + băng chốt | ✓ |

**Loop seam:** khung 100% == khung 0% (mọi delay đều âm; dim wash tự lên lại trong 0.5s cuối; mọi
`--lodc` về 0 ở cả 0% và 100%).

## REVISION 3.1 — bố cục cột phải, để ba đường suy-ra ĐỌC RA là ba cú kéo ngang

**Không đổi gì về nội dung.** Vẫn bảy nhịp, vẫn UI → DB → BE, vẫn cùng cast, cùng chữ. Đây thuần
tuý là **bố cục**.

### Vì sao phải sửa

User báo hai lần rằng ba đường xanh ở b4 trông như **nối sai cạnh**. Đo lại trong trình duyệt thì
hình học *đúng*: cả ba đều đáp vào **mép trái** của bảng `items`. Nhưng hai trong ba đường phải
**leo** 311px và 341px, cắt ngang gần như toàn bộ giao diện dashboard, để lên tới cái bảng đang đậu
ở đỉnh cột phải:

| đường | bản 3 (Δy / Δx → góc) | bản 3.1 |
|---|---|---|
| `KPI 128 → amount` | −109 / 637 → 9.7° (chấp nhận được) | **+203 / 637 → 17.7°** |
| `row title → name` | −311 / 561 → 29° | **+1 / 561 → ~0° (ngang tuyệt đối)** |
| `date cell → created_at` | −341 / 104 → **73°** (gần như dựng đứng) | **−28 / 104 → 15°** |

Một người đọc nhầm hai lần thì cái nhầm ấy LÀ lỗi — dù mỗi endpoint đều hợp lệ. Sửa để mỗi đường
đọc ra là **một cú kéo ngắn, gần như nằm ngang, từ mỏ neo sang đúng hàng của nó**; góc lớn nhất
giảm từ 73° xuống 17.7°, và đường duy nhất còn dốc là đường có quãng chạy DÀI nhất (637px), tức là
đường chịu được độ dốc đó rẻ nhất.

### Cột phải xếp lại (mọi hộp đều ĐO trong trình duyệt, không suy ra bằng số học)

| trạm | bản 3 (stage-local) | bản 3.1 | vì sao |
|---|---|---|---|
| `items` | 1530..1960 × **50..234** | 1530..1960 × **364..548** (hàng 432/478/524) | hàng đáp đúng dải dọc của ba mỏ neo; hàng giữa ngang bằng mỏ neo của nó |
| `decide` (hình thoi) | 1522.6..1675.4 × 277.6..430.4 | × **191.6..344.4** | dải giữa giờ là của bảng; hình thoi lên đỉnh cột |
| `fix-note` | 1518.5..1721.5 × 541.5..635.3 | 1497.5..1700.5 × **36.5..130.3** | vẫn "cưỡi" cung quay lại — cung đổi hướng thì giấy nhớ đổi theo |
| `not yet` pill | 1610 × 450 | 1620 × **154** | nằm cạnh đoạn leo của cung |
| `OK` pill | 1678 × 298 | 1678 × **215** | giữ nguyên khoảng cách 56px phía trên cạnh của nó |
| `ai-db` | 1730..1960 × 324..385.2 | × **240..301.2** | ăn theo cạnh `OK` ở y 271 |
| `tag` | 1730 × 410 | **1600** × **558** | cạnh đoạn xanh `items → Back-end` mới |
| `backend` | 1730..1960 × 450..582 | × **588..720** | ngay dưới bảng |

### Cạnh viết lại

- `app → Looks right?` / `OK → AI` : y 354 → **y 271**.
- `AI → items` : `M 1845 324 V 234` (đi lên) → **`M 1845 301 V 364`** (đi xuống, đáp mép trên bảng).
- `items → Back-end` : vòng phải `M 1960 190 H 2010 V 516 H 1960` → **`M 1845 548 V 588`**. Bảng
  giờ nằm ngay trên back-end nên đoạn suy-ra thứ hai chỉ còn một nét dọc — ngắn hơn, và đọc ra
  "cái này sinh ra từ cái ngay trên nó".
- `snap three pieces` : `M 1845 582 V 728 …` → **`M 1845 720 V 728 …`** (đoạn ngang y 728 giữ nguyên).
- `not yet → AI rebuilds` : `M 1599 430 V 672 H 500 V 366` → **`M 1599 195 V 28 H 500 V 290`**.
  **Đây là ràng buộc, không phải sở thích:** dải giữa mà cung cũ đi xuyên qua giờ là dải của ba
  đường suy-ra, và một cung quay-lại cắt ngang ba đường xanh đọc tệ hơn hẳn một vòng lặp đi vòng
  qua đỉnh — vốn cũng chính là hình dạng của "quay về từ đầu". Cung mới cắt **0** đường nào.
- Ba đường `edge--pull` viết lại từ mỏ neo ĐO ĐƯỢC; mỗi đường vẫn rời mỏ neo bằng một đoạn thẳng
  ngắn (`V`/`H`) — đó là thứ cho checker đọc được hướng rời đi, và cũng là thứ giữ nét "chân
  leader" ở mỏ neo.

### Ăn theo (knock-on) đã đo lại

- **Spotlight b4**: khung bảng `items` 1518..1972 × **352..560**.
- **Spotlight b3**: giấy nhớ giờ cách hình thoi 52.2px ⇒ hai bộ ngoặc sẽ đứng cách nhau 28.3px,
  **dưới ngưỡng gộp pad+arm = 34** ⇒ **gộp làm một** bộ quanh hợp của hai trạm (đúng luật cut đã
  dùng ở b6). Đọc cũng đúng hơn: nhịp 3 nói về *quyết định VÀ một câu bạn gửi lại*.
- **Camera b4**: bbox = app ∪ items = **y hệt bản 3** (bảng vẫn nằm trong dải dọc của app) ⇒
  k 1.6 / tx −1360 / ty −169 **không đổi**.
- **Camera b3**: bbox bản 3.1 là `[880, 168.5, 880.5, 547.9]` (world), transform k 1.68 /
  tx −1276 / ty −237 chứa trọn nó ⇒ khi đó **giữ nguyên camera**, chỉ cập nhật bbox. Việc "giữ
  nguyên" ấy là chỗ **REV 5** phải sửa lại: bbox đó bỏ sót đúng hai thứ mà nhịp này SỐNG nhờ —
  dải sơn của cung quay lại và chính thẻ `cap-b3`. Xem *Revision 5* ở cuối tệp.
- **Caption**: cả 7 thẻ giữ nguyên vị trí; `caption-boxes` xanh, và cả cap-b3 lẫn cap-b4 vẫn nằm
  trong khung của nhịp mình.
- **Dead-geometry**: 14/14 cạnh có mẫu lộ thiên (gate xanh).
- **Reduced-motion**: không đổi luật nào — packet vẫn đậu ở đích, `pull-park` vẫn `opacity:1`.

### Đường nào còn cắt qua giao diện, và tại sao chấp nhận

`KPI 128 → amount` vẫn đi chéo qua thẻ biểu đồ ở 17.7°. Ba lối thoát đều tệ hơn: (a) rời KPI theo
phương ngang thì gạch xuyên hai ô KPI còn lại; (b) tụt xuống rãnh trống y 276..288 rồi mới đổ thì
phải đổ 150px trong hành lang 70px giữa cửa sổ và bảng — gần như dựng đứng; (c) kéo bảng sang phải
cho hành lang rộng ra thì bbox b4 nở, k rơi xuống dưới 1.6 và **thủng sàn chữ**. Đường hiện tại là
độ dốc nhỏ nhất mà bố cục này cho phép, và nó là đường duy nhất còn lại.

## REVISION 3.2 — nhịp tổng kết dài gấp đôi, caption hết chớp, vòng lặp có mặt

Ba ghi chú cuối của user trước khi promote golden. Không đổi cast, không đổi cạnh, không đổi lời.

### 3.2-a — MASTER 33.6s → 38.4s: nhịp cuối giữ gấp đôi

User: *"cái nhịp xem lại tổng thể diagram... nên được giữ lại lâu hơn gấp đôi để user xem một chút"*.

- Beat 1–6 vẫn 4800ms; **beat 7 (recap overview) = 9600ms**. Master 38400ms.
- Beat 1 (overview mở màn) **vẫn 1×** — nó là teaser, người xem chưa được kể gì thì chưa có gì
  để ngắm. Chỉ nhịp ĐÓNG mới đáng giữ lâu. Đã encode vào `references/camera-beat.md` (bảng
  "Per-beat shape") như một luật của ENGINE, áp cho mọi genre kể cả progressive tier story;
  ba golden đông cứng KHÔNG bị cắt lại vì luật này.
- Mọi mốc `%` được emit lại từ `tests/fixtures/vibe-code-voi-ai.timeline.tsv`, và bảng đó giờ ghi endpoint bằng
  **ms** chứ không phải `%`: master đổi, câu chuyện không đổi. `emit_timeline.py --master 38400ms
  --beat 4800ms` làm toàn bộ số học.
- `cap-b7` GIỮ NGUYÊN cửa sổ 3360ms (29400→32760ms). Không kéo caption dài ra theo nhịp — kéo ra
  thì pace tụt xuống 2.2 wps và người xem phải nhìn chữ thay vì nhìn hình. 3.9s cuối của cut
  **không có caption**, đó chính là chỗ để ngắm diagram.
- Divisor gate: `stickyPulse` phải đổi **2800 → 2560ms** (38400/2800 không nguyên; 2560×15=38400).
  `.pk` 2400/4800/1600 vẫn chia hết. `master-divisors` PASS.
- `br-back` / `br-ok` / `pull-park` là keyframes viết tay (không qua emitter) và cũng đã được
  chuyển sang thang mới — bắt được bằng cách so ảnh t=0 với t=master.

### 3.2-b — caption hết "chớp": bỏ HẲN opacity, caption chạy 100% bằng clip

User (lần 1): *"animation chạy text diễn giải... bị chớp 1 cái ở lúc bắt đầu xuất hiện"*.
User (lần 2, đây mới là manh mối quyết định): *"ở lượt đầu nó không bị, sau khi toàn bộ các
phase hoàn tất rồi loop về nó mới bị"* — **vòng 1 sạch, vòng 2 trở đi mới chớp.**

**Đo bằng playback THẬT** (CDP `Page.startScreencast`, không pause, không seek), qua 5 cấu hình:
headless-new và headful GPU, 1×/2×, có và KHÔNG có JS chạy trong trang, trên CẢ bản trước 3.2 lẫn
bản sau. Kết quả: **không cấu hình nào tái hiện được cú chớp ở vòng 2** — mọi chuỗi wipe đều đơn
điệu. Ghi nhận thẳng: máy này không quan sát được lỗi đó. Xem "câu hỏi mở" mục 4.

Nhưng manh mối "vòng 1 sạch / vòng 2 bẩn" chỉ ra ĐÚNG MỘT khác biệt cấu trúc giữa hai vòng:

- Caption ẩn bằng `opacity:0` suốt ~30s, và trong lúc ẩn, clip của nó bị **để nguyên ở OPEN**.
- `opacity` là thuộc tính của COMPOSITOR; `clip-path` là thuộc tính PAINT.
- Compositor thật (có sức ép bộ nhớ, nhiều tab) thả raster của layer ẩn lâu. Frame mà opacity rời
  khỏi 0, nó có thể trình lại **tile CŨ** — tile được raster khi clip đang OPEN, tức NGUYÊN CÁI
  THẺ — trong đúng một frame, trước khi raster mới (clip đóng) kịp về.
- **Vòng 1 không có tile cũ** (raster duy nhất từng tồn tại là raster clip-đóng). Nên vòng 1 sạch,
  vòng 2 trở đi thì không. Trình duyệt tự động chỉ có một tab, không có sức ép bộ nhớ, nên không
  bao giờ thả tile — đó là lý do hợp lý cho việc không tái hiện được.

**Cách sửa: bỏ cuộc đua đi chứ không đua với nó.** Keyframes caption giờ animate **ĐÚNG MỘT thuộc
tính**, và đó là thuộc tính KHÔNG compositable:

```
@keyframes cap-bN{
  0%,S%   {clip-path:inset(-6% 100% -6% -1%); animation-timing-function:ease-in-out}
  W%,E%   {clip-path:inset(-6% -1% -6% -1%);  animation-timing-function:ease-in-out}
  T%,100% {clip-path:inset(-6% -1% -6% 101%)}
}
```

- `opacity` là **hằng 1** suốt đời phần tử (đặt ở rule gốc, không xuất hiện trong keyframes). Không
  còn sự kiện "hiện lại" nào để compositor phục vụ một tile cũ vào đó.
- Thẻ được giấu bằng HÌNH HỌC (clip diện tích 0), không bao giờ bằng độ trong suốt.
- Trạng thái đóng ở hai đầu đều nằm NGOÀI thân thẻ (`100%` bên trái, `101%` bên phải) nên clip
  diện tích 0 không thể để lại một vệt khử răng cưa. **Đã kiểm:** ảnh tại t=0 / 24000 / 33600 /
  38399ms so với bản trước chỉ lệch ≤1/255 trên vài pixel rải rác (nhiễu raster), không có gì của
  caption được vẽ.
- FAIL-SAFE giữ nguyên chiều: clip gốc là clip đóng, nên nếu keyframes không áp được thì mọi
  caption đều ẩn — y như trước.

Hai thay đổi khác đi kèm (mục 3.2-b bản đầu, vẫn giữ):
`CLOSED` là `100%` chứ không phải `101%` của engine (frame có mực đầu tiên: **864 px mực / rộng
18px → 39 px mực / rộng 1px**), và đoạn wipe có `ease-in-out`.

**Đánh đổi, ghi lại:** lối RA giờ là **wipe-out cùng chiều** (left inset quét sang phải) chứ không
phải fade. Câu chữ bị quét đi theo đúng chiều nó đã đến. Đã soi frame giữa lối ra: thẻ bị ăn từ
trái, góc bo bên phải còn nguyên.

**Không dùng thêm `visibility`** (phương án b của lead): với opacity hằng 1 thì đã không còn cổng
hiển thị nào phía compositor; thêm `visibility` là thêm lại đúng loại sự kiện "bật/tắt rời rạc" mà
cách sửa này sinh ra để loại bỏ. Giữ làm đòn bẩy kế tiếp nếu user vẫn thấy chớp.

**Engine đã đổi (2026-08-27).** `scripts/timeline_css_idiom.py::caption_window` nay phát ra đúng
khối clip-only này, nên `cap-b*` của cut này không còn là ngoại lệ:
`tests/run_golden_regression.py` diff từng stop như mọi hàng khác, `PROCESS_OWN_IDIOM` chỉ còn
`lod-`. Ba golden system-design vẫn giữ idiom cũ, được miễn theo tên `SD_LEGACY_CAPTION` (user
hoãn re-bake). *Trước đây: engine phát idiom cũ, cut này vá tay SAU khi emit.*

### 3.2-c — vòng lặp quay lại: HIGHLIGHT + CAMERA FOLLOW

User: *"chỗ cái loop vòng lại để sửa UI... có cách nào focus tốt hơn không, VD như camera follow
cái dot chạy từ cái hình thoi về update UI?"* → sau đó chốt: *"cứ thử cho camera follow xem hoặc
kết hợp cả 2 luôn cũng được"*. Làm cả hai, **highlight chịu lực chính**, follow là phần tăng cường.

**HIGHLIGHT** (opacity-only, không thêm màu — cam đã là nghĩa của vòng lặp):
- `.arc-halo` — CHÍNH đường đó vẽ thêm một lần **ở dưới**, stroke 11px, cam `--edge-service`,
  `stroke-opacity:.22`. Chỉ `opacity` chạy (0 ngoài b3, 1 trong b3). Không mang `data-edge` và
  class không chứa `edge`: checker duyệt `path[class*="edge"]`, một cung phải được đếm một lần.
- `.recede-b3` trên `.ai--sm` (AI infers DB+BE), `.tbl` (`items`), `.lst` (Back-end) → opacity
  1 → **.34** trong đúng cửa sổ b3, đúng ngữ pháp `.pull-park` sẵn có. Chúng vẫn được VẼ, chỉ
  lùi lại; b4 kéo chúng về đủ mạnh trước khi chúng thành chủ thể.
- Không dùng wash che một phần sân khấu: `.stage-dim-b1` phủ TOÀN stage nên không thấy mép;
  một wash cục bộ sẽ để lại đường viền xám giữa nền. Ghi lại như một lựa chọn, không phải bỏ sót.

**FOLLOW** — b3 là nhịp DUY NHẤT có cú máy giữa nhịp:

| mốc | % của 38.4s | ms | việc |
|---|---|---|---|
| vào | 25 → 26.5625 | 9600→10200 | overview → b3 (600ms) |
| **hold b3** | 26.5625 → 30.4688 | 10200→11700 | 1500ms; caption bung xong ở 11217ms |
| **travel** | 30.4688 → 33.5938 | 11700→12900 | 1200ms, ease-in-out, chỉ `transform` |
| **hold b3b** | 33.5938 → 37.5 | 12900→14400 | **1500ms**, đậu trên AI · builds the UI |
| ra | 37.5 → 39.0625 | 14400→15000 | b3b → **b4 thẳng**, 600ms, KHÔNG qua overview |

(Số của **REV 6**. Bản 3.2–5 là hold 2100 / travel 900 / hold b3b **600** / ra overview 600 —
tức 32.0312 · 34.375 · 35.9375. Xem *Revision 6* ở cuối tệp: user báo cú follow "nhanh quá,
cần chờ lại một chút".)

- `b3b` được **KHAI BÁO trong manifest** như một hold thật: k 1.6, tx −680, ty −192, center
  (1025, 457.5), bbox (530,142.5,990,629.5), gate `read` (số của REV 5; bản 3.2 là ty −212 /
  bbox (530,170,990,546.4)). Nhờ vậy nó đi qua `check_holds` (containment
  + sàn chữ), qua `verify-hold-geometry`, và **có một khung riêng trên contact sheet** — đúng chỗ
  user cần để phán bằng ảnh tĩnh. Stage D giờ có 8 hold camera thay vì 7, nên tổng gate là
  19 PASS / 4 N-A chứ không phải 18/4 (từ REV 5 là **20 PASS / 4 N-A** — thêm một gate, xem cuối
  tệp); con số tăng vì có thêm hold và thêm gate, không phải vì đổi luật.
- Gói khung `k=1.6` ôm cả AI · builds the UI (world 530–830) lẫn cửa sổ app (880–1520): sàn chữ
  1.6 × 15 = 24 frame px, đúng bằng sàn landscape, y hệt b4.
- **MỘT chuyến, không đuổi theo từng vòng.** Cung có hai packet lệch nửa vòng trên lap 4800ms;
  camera đi đúng một chuyến rồi ĐẬU, packet thứ hai tự về đích với máy đứng yên. Camera lặp theo
  vòng lặp thì người xem say — đây là lựa chọn có chủ ý, không phải giới hạn kỹ thuật.
- **`cap-b3` không phải né gì cả.** Nó neo theo world (1150, 736) và nằm trọn trong CẢ HAI khung.
  Không phải cho nó "cưỡi" camera, không phải giấu đi. Từ REV 5 nó nằm **trong bbox** của cả hai
  hold (thẻ đo được: world 868.3..1431.7 × 736..772) nên khoảng hở đáy là do solver quyết, không
  phải do may: 36.8 frame px ở b3, 36.8 ở b3b.
- `focus-b3b` — bracket của AI · builds the UI (đúng hộp bracket b2 đã đo). Cửa sổ **12900→14400ms**
  với lead 600ms (REV 6; trước là 12300→13800ms), nên nó lên hết ĐÚNG lúc máy đậu xuống: đích được
  gọi tên NGAY TRONG nửa sau của cú lia, chứ không phải được đặt tên sau khi tới. (Đo trên trang
  thật: opacity 0.00 ở 12300ms, 0.50 ở 12600ms, 1.00 ở 12900ms.)
- **Reduced motion: KHÔNG follow, KHÔNG highlight.** Máy đậu ở overview như cũ; ở overview một
  quầng cam trên một cung và một bảng schema bị lùi lại là nhấn mạnh không có gì giải thích.
  `.arc-halo` → 0, `.recede-b3` → 1.

**Contact sheet đọc được gì:** `b3` (t=**10950**ms từ REV 6) cho thấy quầng cam + cụm DB/BE đã lùi
+ caption đang bung nốt; `b3b` (t=**13650**ms) cho thấy packet cam đang đổ xuống AI · builds the UI
trong bracket, cùng khung với app nó dựng lại. Khung giữa-chuyến KHÔNG lên sheet — sheet chỉ chụp
ĐIỂM GIỮA của mỗi hold đã khai báo và ghim transform của hold đó, nên cú lia 1200ms chỉ xem được
khi phát thật (hoặc trên MP4).

**Loop seam:** t=0 và t=38400ms **byte-identical** (sha256 trùng, sau khi để repaint lắng 120ms;
không property nào của bất kỳ animation nào khác nhau giữa hai mốc).

## REVISION 4 — khối snap b5 thành CARTRIDGE MODULES (V2)

User duyệt V2 trên board `plans/reports/designer-260827-1230-snap-block-enrichment-board.md`
("V2 ổn. Em làm lại cái html để apply"). Golden ĐÃ đông cứng, nên đây là một lần **tái sinh có
phép**: SHA-256 cũ hết hiệu lực và được ghi lại ngay trong cùng thay đổi
(`examples/README.md`). Không đổi cast, không đổi lời, không đổi cửa sổ, không đổi mốc keyframe.

### 4-a — vì sao phải làm lại

Khối cũ là ba hình chữ nhật phẳng dính nhau cộng hai viên thoi teal — từ vựng sampler-v2, vẽ
TRƯỚC doctrine *product-first*. Bây giờ nó đứng cạnh một tài liệu BRD thật và một cửa sổ trình
duyệt thật, và nó đọc ra như chỗ chưa vẽ xong. Nó cũng phạm chính luật của genre — *close tier
phải TRẢ GIÁ*: ở `k=2` nó chiếm 1620×260 px sơn mà không dạy thêm gì so với `k=0.69`.

### 4-b — cái gì thay vào

Ba **mảnh mô-đun**, mỗi mảnh mang đúng sản phẩm mà nó là:

| mảnh | ruột (miniature) | vì sao là miniature đó |
|---|---|---|
| UI | `#mini-dashboard` | ĐÚNG cái dashboard nhịp 3/4 vừa xem: tab, địa chỉ, ba ô số, hai dòng item |
| BE | `#mini-api-card` | `POST /items` · `GET /items` · `GET /items/:id` — một back-end trông như thế |
| DB | `#mini-items-table` | ĐÚNG bảng `items` nhịp 4 vừa suy ra |

Mối nối là **mộng / ổ**: mảnh bên trái mang cái **mộng** đã cắm sẵn vào **ổ** của mảnh bên phải, và
mộng mặc màu role của mảnh BÊN TRÁI (bản ghi RỜI mảnh đó, mảnh sau NHẬN). Đáy mỗi mảnh là một
**dải cổng** full-bleed, ba dải nối thành một rãnh chạy suốt khối. Mộng nằm **đúng giữa** dải cổng
— nên mối khớp và cái cổ họng bản ghi chui qua LÀ MỘT VẬT. Thêm hai vạch "đã cắm khít" trên mỗi
mối, gờ cầm ở header, và `out` / `in` cỡ texture ở hai đầu dải.

Từ vựng này đã được ghi vào doctrine trước khi dùng: `references/genres/process.md` →
*Vocabulary — mộng / ổ / port band*. Board tự cảnh báo rằng một ẩn dụ dùng một lần là bị cấm; entry
đó là thứ hợp thức hoá nó.

### 4-c — hình học, ĐO trong trình duyệt chứ không suy bằng số học

| thứ | trước | sau |
|---|---|---|
| khối b5 | 810×130 @ (60,760) stage | **810×282 @ (60,760)** — mép TRÊN không đổi |
| đường packet b5 | `M 90 825 H 840` | `M 90 1019 H 840` — 1019 = đáy khối (1042) − 23 = tâm dải cổng = tâm mộng |
| cạnh b6 (khối → deploy) | `M 870 825 H 1000` | `M 870 1019 H 1000` — rời khối ngay tại cổng `out` |
| cạnh "snap three pieces" | `M 1845 720 V 728 H 470 V 760` | `M 1845 720 V 728 H 780 V 760` |
| bracket b5 | `…882 880 … 902 …` | `M 70 748 H 48 V 770 M 860 748 H 882 V 770 M 882 1032 V 1054 H 860 M 70 1054 H 48 V 1032` |
| hold b5 | `k 2, tx −90, ty −1350`, bbox `120,880,810,130` | `k 2, tx −90, **ty −1502**`, bbox `120,880,810,**282**` |
| `cap-b5` | world `top:1050` (DƯỚI khối) | world `top:800` (**TRÊN** khối) |
| `.banner` | stage `top:990` | stage `top:1058` (world 1178) |
| `cap-b1` / `cap-b7` | world `top:1245` | world `top:1295` |

`k` giữ nguyên 2.0: `solve_camera.py --bbox 120,880,810,282 --gate read --k 2` cho `tx −90 /
ty −1502`, containment PASS, chữ nhỏ nhất 30 frame px so với sàn 24.

### 4-d — vì sao caption b5 nhảy lên TRÊN khối

Khối cao thêm 152 px thì cột dưới-trái không còn đủ chỗ cho *caption + banner + caption tổng kết*:
cộng lại cần 338 px trong khi từ đáy khối (world 1162) tới đáy world chỉ còn 278. `camera-beat.md`
cho phép đặt thẻ **"trong khoảng trống ngay TRÊN hoặc dưới chủ thể"** khi ô cố định không nằm lọt
khung — đây đúng là trường hợp đó. Khoảng trống trên khối (world 751–880 trong khung b5) trống
sạch: `seed` kết thúc ở 731, `cap-b2` ở 748.
Hệ quả đã đo và đã sửa: cạnh "snap three pieces" **rơi xuống ở x 470**, tức chui thẳng dưới thẻ
caption (caption `z-index:9`, overlay cạnh `z-index:1`) — trên ảnh nó đọc ra thành *caption nhả ra
mũi tên*. Điểm rơi dời sang x 780 (mép trên mảnh DB): cả đường chạy nằm trọn bên phải thẻ, cách 75
px, và đó cũng là lối ngắn hơn cho một nguồn nằm tít bên phải. Bracket vẫn ôm cả ba mảnh nên mệnh
đề không đổi.

### 4-e — caption b5: ĐỌC LẠI, KHÔNG SỬA

*"Từ bảng `items` vừa suy ra, AI dựng back-end: UI có trước, rồi DB, rồi BE."*
Giữ nguyên, có chủ ý. Hình bây giờ nói RẤT to phần "khớp vào nhau" và "một bản ghi chạy xuyên" —
mộng đã cắm, vạch khít, packet chạy trong rãnh. Caption gánh **nửa còn lại** mà hình không vẽ được:
THỨ TỰ suy ra. Hai vế không mâu thuẫn, chúng bù nhau, và cả hai đều nằm trong lời dẫn nhịp 5.
Thêm chữ "khớp" vào caption sẽ đẩy nó lên ~19 từ trong cửa sổ đọc ~2.9 s, tức vượt trần ~5 từ/giây
của `camera-beat.md`. Một caption không đọc kịp thì tệ hơn một caption thiếu một tính từ.

### 4-f — thu hoạch vào thư viện (harvest)

| file | được thêm |
|---|---|
| `templates/snippets/process-stations.css` | `css-station-snap-cartridge` **thay** `css-station-snap-seam`; `css-station-mini-base`; `css-station-mini-api-card`; `css-station-mini-items-table` |
| `templates/snippets/process-stations.html` | `station-snap-cartridge` **thay** `station-snap-seam`; `mini-api-card`; `mini-items-table` |
| `templates/snippets/process-webapp-templates.css` / `.html` | `css-webapp-miniature` / `mini-dashboard` — ở cạnh anh em cỡ thật của nó |
| `references/genres/process.md` | mục *Vocabulary — mộng / ổ / port band*; điều khoản "ẩn dụ vỏ dùng một lần là cấm"; ghi chú rule-of-two cho ba miniature |
| `data/components.csv` | **KHÔNG đổi.** Ba mảnh vẫn phân giải qua các dòng sẵn có; đây là đổi VỎ, không đổi CAST. `code-artifact` vẫn trỏ `#station-code-card` (nó là thẻ diff, không phải cartridge). |

`.mbe` (thẻ API) là **lần xuất hiện ĐẦU TIÊN** — vào thư viện bằng lập luận phổ quát mà rule-of-two
cho phép, và lập luận đó chỉ có hiệu lực khi user đã duyệt board; user đã duyệt (2026-08-27).

### 4-g — cổng đã chạy lại sau khi re-bake

`verify_all --serve` **19 PASS / 4 N-A** (y hệt trước re-bake) · `run_golden_regression` **PASS**
(0 lệch; b5 hold khớp `ty −1502`) · `run_smoke` **All checks passed** · `validate_csv` /
`validate_anchors` 0 lỗi · quét riêng khối: 0 chữ dưới 15 px ngoài diện texture, 0 tràn hộp, 0
self-opacity trong station, khối sơn đúng 810×282.

## DEVIATIONS (recorded, per SKILL.md)

1. **`--blueprint` ABSTAINED** on the free-text scenario (both VN and EN wording); re-run
   with `--type process-loop --style flat-minimal` and everything else taken as returned.
   Style is not a free pick: `process` is locked flat-minimal by its genre guide.
2. **Layout `timeline-sequence`, with the two departures the genre guide already
   licenses**: no disc-on-axis marker (the axis position is occupied by a run and its cargo
   label) and no alternating sides. Measured: axis-band gap between adjacent stations
   76–114 px (floor: half the shorter side, never < 40).
   Third departure, recorded here: the axis **wraps once**, band 1 → band 2, because seven
   stations plus a three-piece snap block do not fit one 1800 px line at k_read 1.6. The
   wrap run is drawn as a plain gray forward edge at a y that no station occupies.
3. **Captions use the adjacency placement, not a fixed slot.** `references/camera-beat.md`
   permits it "only when a fixed slot would put the card outside its hold's frame" — with a
   camera roaming a 1920×1208 world at k 0.83–1.7, no single world band is inside every
   frame. Each card sits in the gap under its own beat's subject.
4. **Emitter deviation.** `scripts/emit_timeline.py` emits the caption/state/traffic
   keyframes and the manifest fragments from the event table below — used as prescribed.
   `scripts/solve_camera.py` computed every `k/tx/ty`. What was hand-authored is the
   STATION MARKUP: there is no HTML-mode station emitter in the repo (the snippets are
   copy-sources, and `search.py --blueprint` composes an SVG-shaped spec), so the stations
   were copied block-by-block from `templates/snippets/process-stations.html`.
5. **Pull-lines leave three SEMANTIC ANCHORS inside the app window (revision 3).** Not form fields
   any more: the KPI number, a row title and a date cell. Two of the three sit deep inside the
   window, so see deviation 16 for the z-index consequence and deviation 17 for the departure-jog
   that keeps the anchoring gate honest.
6. **`.edge--soft` annotation tie — NOW USED, and it passes (revision 3 update).** Revision 2 recorded
   it as unusable because "it carries no marker and terminates on nothing, which the anchoring gate
   reads as FLOATING". The gate never objected to the CLASS: it objected to a tie that ended in empty
   space. In `station-deploy-responsive` both ends sit on real station borders
   (`M 1470 1010 H 1620`: the deploy window's right border → the phone's left border), so
   `verify-html-edge-anchors.mjs` passes it like any other edge, marker or no marker. **No class
   exemption is needed and none was asked for.** The open question in phase-05 is answered: the rule
   is *anchor both ends*, not *avoid the class*.
   Revision 2's text, kept for the diff: It carries no marker and terminates on
   nothing, which the anchoring gate reads as FLOATING. The relationship it would have
   drawn is drawn instead with two REAL edges, and revision 1 changed which two: one gray
   forward edge `AI·infers → items` (the AI produces the table) and one GREEN
   derivation edge `items → Back-end` (the back-end is read out of that table).
   The old second gray edge `AI·suy → Back-end` is gone — it drew the back-end as a
   sibling the AI happened to also emit, which is exactly the claim the user corrected.
   Flagged as an open question for the genre.

7. **Upstream rule at beat 5, read explicitly.** `references/camera-beat.md` requires the
   upstream station in frame. At `k_read` 1.6 the snap block (810 px) plus the Back-end card
   (world x 1490–1750) span 1420 px, which needs k ≤ 1.30 — an empty interval at a `read` gate.
   The frame is NOT zoomed out (that is the one resolution the file forbids). The upstream is in
   frame BY IDENTITY instead: the bảng and the Back-end are literally re-drawn as the middle and
   right pieces of the snap block, and the assemble edge runs in from the frame's right edge with
   its arrowhead landing on the UI piece. Recorded here rather than waived silently.
8. **Branch parking is an opacity window, not a second edge layer.** The genre's branch convention
   wants the untaken path "parked at reduced opacity with its condition label still legible". Both
   branch edges and both `.pill` labels carry a master-timeline opacity animation (`br-back`,
   `br-ok`): 0.5 when not taken, 1.0 for the beat that takes them. Opacity only, same discipline as
   every other beat layer; nothing is duplicated and nothing is erased.
9. **The verdict banner lives INSIDE the stage** and rides the chrome fade, so it is on screen only
   at the two overview beats and is dimmed by beat 1's wash like everything else. First attempt put
   it in the chrome layer OUTSIDE the stage, where the stage (a later sibling) painted over it and
   it never appeared at all — caught on the contact sheet, not by any gate.
10. **No web font.** `camera-beat.md` suggests Inter or Be Vietnam Pro for Vietnamese captions; this
   cut ships the snippet's own `system-ui` stack instead, which covers Vietnamese natively and keeps
   the file at zero external hosts. Recorded because it is a departure from a named suggestion.

11. **Fit-to-viewport layer (revision 1).** The frame keeps its authored 1920×1080 layout box and
   is scaled into the viewport by `--fit:calc(min(100vw,177.7778vh) / 1920px)`, centred with
   `position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) scale(var(--fit))`. Not a
   deviation any more — it is contract clause 7 in
   `templates/snippets/process-stage-and-edges.css` and a rule in `references/genres/process.md`
   as of this revision. Recorded here because the factor is exactly `1` at a 1920×1080 viewport,
   which is why every headless gate still measures the numbers written in this file.
12. **Caption pace, revision 1.** The captions were rewritten as full explanatory sentences
   (user: "text diễn giải đang bị ngắn và cụt quá"). Measured against
   `references/camera-beat.md`'s calibrated ceiling ("a 3.0s window carries about 15 words"):
   b1 17 tokens / 3.76s = 4.5 · b2 15 / 2.92 = 5.1 · b3 15 / 2.92 = 5.1 · b4 15 / 2.92 = 5.1 ·
   b5 15 / 2.92 = 5.1 · b6 15 / 2.92 = 5.1 · b7 15 / 3.36 = 4.5. Vietnamese tokens are
   SYLLABLES, so these sit at the stated envelope rather than past it. b2/b4/b5/b6 wrap to two
   lines via `.beat-caption--2` (an explicit width + `text-wrap:balance`); b1/b3/b7 stay one
   line because their beat's frame has no vertical room for a second.

13. **Two languages on one canvas (revision 2).** Every string ON an element is ENGLISH; the
   explanatory voice — 7 captions, the narration, the page heading and the banner's sub-line — is
   Vietnamese. This is not a deviation either: it is the *Language* rule in
   `references/genres/process.md`, written from this cut's own review
   (*"text trên các element đừng dùng tiếng Việt không dấu, kì lắm, cứ dùng English"*).
   Recorded here because it changes what "every string traces to a sheet line" MEANS: a sheet line
   in Vietnamese may be rendered on the canvas in English, and the mapping is this file's tables.
   The renames: `bang_du_lieu`→`items`, `ten`/`gia_tri`/`thoi_gian`→`name`/`amount`/`created_at`,
   *Tên/Giá trị/Thời gian*→*Name/Amount/Date*, *Đúng ý chưa?*→*Looks right?*, *chưa*→*not yet*,
   *sửa lại nút chính*→*fix the main button*, *FE-FIRST ≠ BỎ BACK-END*→*FE-FIRST ≠ SKIP BACKEND*.
   Caption b5 quotes the element by its English name in mono (`bảng items`) rather than
   translating it — the rule's own escape hatch.
14. **The legend stays Vietnamese, and it is a judgment call.** The *Language* rule lists the
   registers but not the legend, which is neither an element label nor narration: it is the KEY
   that teaches the audience how to read the three edge colours. It is filed as explanatory and
   left in the audience's language. If review disagrees, it is six strings.
15. **URL shortened, and its box re-measured (revision 2).** `app-cua-ban.example.dev` wrapped to
   two lines inside the pill; `my-app.pages.dev` is one line, which drops the `link` station from
   70px to 50px tall — so the b6 spotlight bracket was re-cut from the MEASURED box
   (1180,839)-(1480,889). The English brief copy went the other way and grew one wrapped line
   (brief now 30,140→344,359.6), so the b1 bracket was re-cut too. Neither was guessed: both come
   from a headless `getBoundingClientRect` pass after the copy edit, which is the only honest
   source for an HTML station's height.

## Event table → `scripts/emit_timeline.py`

Source of every window in the cut; see `tests/fixtures/vibe-code-voi-ai.timeline.tsv`.

16. **The app window sits at `z-index:0`, under the edge overlay — ONE deliberate departure from
   stage-contract clause 4 (revision 3).** Clause 4 puts `.edges` under every station. Two of the
   three derivation anchors are 570 px inside the window, so with the overlay underneath, `amount`
   and `name` would be invisible for their whole run and b4's claim — *the AI reads THESE three
   things* — would be unreadable. Parking that ONE station under the overlay makes the lines visible
   from their own anchors. Nothing else changes: every other station keeps `z-index:2` with the
   overlay under it, and no other edge crosses this station's footprint (checked path by path).
   DEAD-GEOMETRY still measures by BOX, so the checker still requires each pull-line to surface
   outside the window — all three do, in the 70 px gap before the table.
17. **Each pull-line departs PARALLEL to the window side it sits nearest (revision 3).**
   `verify-html-edge-anchors.mjs` ports `facing_side()`: an endpoint inside a box is judged against
   the NEAREST side, and a departure heading INTO the box fails as WRONG-SIDE. `amount` is nearest
   the left border, so its path starts `V` (vertical, depth 0); `name` is nearest the bottom border
   and starts `H`; `created_at` is nearest the right border and starts `H` outward. This is
   geometry, not a workaround — a line that leaves an anchor sideways is also what reads as "taken
   FROM here".
18. **The three pull-lines are PARKED at opacity .32 outside beat 4**, using the same master-timeline
   window the branch edges already use (`.br-ok` / `.br-back`). They run straight across the app
   window by design; left at full strength they slice the dashboard at every other beat and b3's
   "AI built you a screen" reads as "something is crossed out". Parked, the derivation is still
   drawn and still legible as a relationship; b4 brings it to full. Nothing is erased.
19. **The LOD tier switch is driven by an animated custom property, not by the `data-lod-tier`
   attribute (revision 3).** The copy-source flips the attribute on an ancestor; a single-canvas
   BEATS cut has no per-beat wrapper to flip and no JavaScript. `@property --lodc` is animated on
   each LOD station by the master timeline — the identical mechanism every other beat layer here
   uses — and the attribute selectors are kept, so a static copy of a station still behaves as the
   snippet documents. All four LOD rules still hold, and the `LOD-LEAK` gate stays LIVE rather than
   vacuous: it freezes the page at t=0, where every `--lodc` keyframe is 0 (the far tier), and reads
   computed opacity back. It swept 14 elements on this cut.
20. **Reduced motion parks the CLOSE tier, against the copy-source's own default.** `css-process-lod`
   keeps the far tier under reduced motion because there the tier still SWITCHES and a skeleton is a
   passing state. In this cut's reduced-motion still nothing will ever flip, so a permanent skeleton
   would claim the app has no content. Geometry is identical either way (that is the LOD contract),
   so the only difference is words instead of bars. Reviewed on the re-shot PNG; recorded here rather
   than chosen silently. This answers the encode tranche's open question 4.
21. **The overview k fell 0.80 → 0.69, and the world grew 1920×1280 → 2160×1460.** The product-first
   stations are simply bigger: a 640 px browser window, a 360 px document, a 470+216 responsive pair.
   The genre guide already says the overview shows text as TEXTURE, and the five-second test is about
   SHAPE — a document, a browser window and a phone are more legible shapes at k 0.69 than labelled
   boxes were at k 0.80. Re-audited beat by beat above.
22. **`data-station` ids are now English** (`brief`, `ai-ui`, `seed`, `app`, `decide`, `fix-note`,
   `ai-db`, `items`, `backend`, `snap-*`, `app-live`, `app-phone`, `link`). They are not user-visible
   — only the edge checker prints them — but the unaccented-Vietnamese ids (`bang`, `quyet`,
   `cau-sua`, `app-that`) were an open question from revision 2 and the rebuild was the cheap moment
   to close it.
23. **Beat 2 and beat 3 swapped subjects, which is a forced caption touch-up, not a storyboard
   change.** The BRD document is 360×380 and the app window 640×551: at the `read` gate's hard floor
   (k ≥ 1.6, i.e. 1150×625 world px of frame) no frame holds brief + AI + app at once. So b2 is now
   the BRIEF beat (its LOD close tier is the reward) and b3 carries "AI dựng xong màn hình" together
   with the loop. The seven beats, the cast, the edges and the UI → DB → BE claim are untouched; the
   b2/b3/b4/b6 caption wording moved with the subjects and the narration follows.

24. **Caption chạy 100% bằng `clip-path`; `opacity` KHÔNG BAO GIỜ động (revision 3.2).** Khác
   engine idiom ở ba điểm: `CLOSED` là `inset(-6% 100% ...)` chứ không phải 101%; đoạn wipe có
   `ease-in-out`; và **opacity bị bỏ hẳn khỏi keyframes** — lối vào lẫn lối ra đều là clip, nên
   lối ra là một **wipe-out cùng chiều** thay cho fade. Lý do, số đo và giới hạn bằng chứng ở mục
   3.2-b: manh mối "vòng 1 sạch, vòng 2 mới chớp" chỉ đúng một khác biệt cấu trúc, là việc tách
   `opacity` (compositor) khỏi `clip-path` (paint) trong khi thẻ ẩn ~30s với clip để nguyên OPEN.
   Cách sửa loại bỏ chỗ tách đó chứ không đua với nó.
   **HẾT DEVIATION (2026-08-27):** `scripts/timeline_css_idiom.py::caption_window` đã đổi sang
   đúng khối này, nên `cap-b*` của cut không còn là ngoại lệ — golden regression diff từng stop,
   `PROCESS_OWN_IDIOM` chỉ còn `lod-`. Ba golden system-design vẫn ở idiom cũ dưới
   `SD_LEGACY_CAPTION`. *Trước đây: engine không bị đụng vào, cut này vá tay sau khi emit.*
   **CHƯA TÁI HIỆN ĐƯỢC** cú chớp vòng 2 trên máy này (5 cấu hình, xem 3.2-b), nên đây là một cách
   sửa theo CẤU TRÚC, không phải một cách sửa đã được chứng minh bằng before/after của chính lỗi
   đó. Cái đã chứng minh được: trạng thái nhìn thấy ở mọi hold không đổi, seam vẫn byte-identical,
   vòng 1/2/3 vẫn sạch, mọi gate xanh.
25. **Một cú máy GIỮA NHỊP ở b3 (revision 3.2).** `camera-beat.md` mô tả mỗi nhịp là vào–giữ–ra
   với phần giữ "dead still". b3 giữ hai lần với một chuyến 900ms ở giữa, và chuyến đó được khai
   báo hợp lệ bằng cách cho đích đến (`b3b`) một hold riêng trong manifest — nên mọi gate vẫn soi
   được nó, không có đoạn nào của cut nằm ngoài tầm kiểm tra.
26. **`.arc-halo` là cạnh thứ hai vẽ chồng lên cạnh thật.** Nó không phải một quan hệ mới, nên nó
   không mang `data-edge`, không mang class `edge`, và không xuất hiện trong bất kỳ đếm cạnh nào.
   Nếu về sau checker đổi selector, đây là chỗ phải kiểm lại.
27. **Beat 7 dài gấp đôi, beat 1 thì không.** Đối xứng bị phá có chủ ý; lý do ở mục 3.2-a và luật
   đã được ghi vào `references/camera-beat.md`.
28. **b3 KHÔNG có nhịp thở overview trước khi sang b4 (revision 6).** `camera-beat.md` viết "mọi
   nhịp làm việc đều kết thúc bằng cách ném người xem về toàn cảnh". Cut này giữ luật đó ở 5/6
   ranh giới nhịp; riêng `b3b → b4` là một cú LIA NGANG thẳng, 680px, 600ms, cùng k 1.6. Lý do:
   b3b và b4 cùng thang, cùng họ ty, và CHUNG chủ thể (cửa sổ app nằm trong cả hai khung) — nhịp
   thở sẽ đi tái lập một bức tranh chưa hề rời đi — trong khi 600ms đó là thứ duy nhất còn lại để
   mua thời gian đậu cho cú follow. Một cú lia ngang thuần 600ms cũng NHẸ hơn năm nhịp thở cut này
   vẫn giữ, vì mỗi nhịp thở đó zoom 1.6–2× trong đúng 600ms. Kèm theo: `lod-app` phải GỘP hai cửa
   sổ close-tier (10200→18600ms) — không còn khoảnh khắc overview nào ở giữa để về far tier, và
   một cú lật skeleton giữa cú lia ở k 1.6 là lỗi nhìn thấy được.

---

## Revision 5 (2026-08-27) — biên khung của cung quay lại, và một gate mới

**User report:** *"biên quá sát nên đường nét dẫn về dễ bị che và không thấy rõ"* — ở nhịp
highlight vòng lặp (b3/b3b), cung cam quay về AI chạy sát mép trên của khung.

**Đo được, không phải cảm giác.** Đoạn ngang của cung nằm ở stage y=28 ⇒ world y=148; quầng
`.arc-halo` rộng 11 world px nên dải sơn của nó bắt đầu ở **world y 142.5**.

| hold | k / ty (trước) | tâm nét tới mép trên | **dải sơn** tới mép trên |
|---|---|---|---|
| b3 | 1.68 / −237 | 11.6 frame px | **2.4** |
| b3b | 1.6 / −212 | 24.8 frame px | **16.0** |

**Nguyên nhân gốc: bbox của b3 nói dối bằng cách im lặng.** Chú thích của nó ghi "+ the return
arc" nhưng con số dừng ở `y0 = 168.5` — tức mép trên của cửa sổ app, thấp hơn dải sơn của cung
26 world px — và bbox của b3b cũng bỏ luôn cả cung lẫn thẻ `cap-b3`. Không gate nào thấy: mọi
gate camera đều đo **bbox mà hold TỰ KHAI**, nên một cạnh chỉ nằm trong đó nếu tác giả bỏ nó vào.
Bản 3.1 đã ghi rõ là "giữ nguyên camera vì hạ khung xuống sẽ đẩy cap-b3 ra ngoài" — đó là né,
không phải giải.

**Cách giải: đưa CẢ HAI thứ bị bỏ sót vào must-show rồi giải lại.**

| | trước | sau |
|---|---|---|
| bbox b3 | `880, 168.5, 880.5, 547.9` | **`868.3, 142.5, 892.2, 629.5`** |
| bbox b3b | `530, 170, 990, 546.4` | **`530, 142.5, 990, 629.5`** |
| b3 | k 1.68 / tx −1276 / ty −237 | **k 1.6 / tx −1143 / ty −192** |
| b3b | k 1.6 / tx −680 / ty −212 | **k 1.6 / tx −680 / ty −192** |
| `cap-b3` | `font-size:15.5px` (26.0 frame px ở k 1.68) | **16px** (25.6 ở k 1.6, y hệt `cap-b4`) |
| dải sơn của cung tới mép trên | 2.4 / 16.0 frame px | **36.0 / 36.0** |
| `cap-b3` tới mép dưới | 20.0 / 56.8 | **36.8 / 36.8** |

- **Thẻ `cap-b3` đo được** (world `868.3..1431.7 × 736..772`) giờ là một phần của must-show ở
  cả hai hold, nên khoảng hở đáy do solver quyết chứ không phải trùng hợp. Thẻ **không phải di
  chuyển**: một lần giải lại đúng là đủ, và mọi cách dời thẻ đều mua thêm rủi ro để đổi lấy ít
  hơn 10 world px.
- **Cung KHÔNG bị hạ xuống.** Hành lang duy nhất phía dưới là 22 world px giữa nó và mép trên
  cửa sổ app (và 19 px tới giấy nhớ) — hạ tối đa được ~8 px, tức 13 frame px, không đủ; và ở
  k 1.68 mép khung chỉ cách cung 7 world px nên hạ bao nhiêu cũng không cứu được b3. Giải lại
  camera là cách duy nhất, đúng thứ tự ưu tiên của lệnh.
- **Cú follow giờ là một cú LIA NGANG THUẦN TÚY** — cùng k, cùng ty, chỉ tx đổi −1143 → −680.
  Đó cũng là cú máy đúng hơn cho một packet đang chạy trên một đoạn nằm ngang.
- **k rơi 1.68 → 1.6** = đúng sàn đọc (`k_read = 24/15`), y hệt b3b và b4. Sàn chữ 24.0 frame px,
  PASS. `pad` trong fixture đổi 40 → **22** cho hai hold này: must-show cao 629.5 world px, một
  pad 40 world px sẽ đẩy `k_fit` xuống 1.589, dưới sàn đọc. 22 world px là thứ khung thật sự mua
  được ở k 1.6 — và nó là **36 FRAME px**, gấp rưỡi con số 24 mà luật biên đòi.

**Luật đã encode** (`references/camera-beat.md` → *Keep the teaching line off the frame edge*;
`references/genres/process.md` → Build traps; `references/pre-delivery-checklist.md` item 7):
tại một hold, một cạnh chỉ được lại gần một cạnh khung ở chỗ nó **thật sự đi xuyên qua** cạnh đó;
mọi cạnh khung nó không xuyên qua đều nợ nó **24 frame px**, đo trên **dải sơn** (quầng tính là
sơn của cạnh), còn "có xuyên qua hay không" thì đọc trên **tâm nét** để một nét dày không tự mua
được miễn trừ. Cạnh có một trạm không hề xuất hiện trong khung thì là phông nền của nhịp đó,
không đo.

**Gate:** `scripts/browser-checks/verify-frame-edge-margin.mjs`, chạy trong stage E của
`verify_all.py` cho genre `process`. **Mutation test:** FAIL trên golden trước khi sửa (đúng 2 vi
phạm: b3 2.4px, b3b 16.0px, không có false positive nào ở 6 hold còn lại) → PASS sau khi sửa
(42 lượt cạnh, 8 hold). Ba golden system-design **không đổi một dòng output nào**.

**Gates:** `verify_all --serve` **20 PASS / 4 N-A** · `run_golden_regression` PASS ·
`run_smoke` All checks passed · `validate_csv` / `validate_anchors` / `validate_checks` /
`validate_colors` sạch · loop seam byte-identical · video 1152 frame dựng lại toàn bộ.


---

## Revision 6 (2026-08-27) — nhịp của cú follow: chậm cú lia, và ĐẬU LẠI cho packet về tới nơi

**User report:** *"chỗ camera follow đường loop về đang nhanh quá, cần chờ lại một chút."*

**Chỉ đổi NHỊP.** Không đổi cast, cạnh, chữ, `k/tx/ty`, bbox, palette. Master vẫn 38400ms, `b4`
vẫn mở ở 39.0625%. Toàn bộ việc chia lại nằm TRONG bao của b3.

| đoạn | trước (REV 3.2–5) | **sau (REV 6)** |
|---|---|---|
| hold `b3` | 10200→12300 (2100ms) | **10200→11700 (1500ms)** — 26.5625→30.4688% |
| travel | 12300→13200 (**900ms**) | **11700→12900 (1200ms)** — ease-in-out, chỉ `transform` |
| hold `b3b` | 13200→13800 (**600ms**) | **12900→14400 (1500ms)** — 33.5938→37.5% |
| ra | 13800→14400 overview, rồi 14400→15000 vào b4 | **14400→15000 thẳng sang b4 (600ms)** |

**Lỗi thật nằm ở chỗ ĐẬU, không phải ở tốc độ cú lia.** 600ms ở `b3b` ngắn hơn chính cú wipe của
caption: người xem vừa đi theo packet về nhà thì máy đã rời đi, và packet **chưa bao giờ kịp đáp
xuống trong khung** — nó bị cắt ở 87.5% quãng đường trong lúc lớp traffic đang mờ dần. Bây giờ:
1500ms đậu, và cửa sổ `traffic-b3` + `arc-halo` kéo tới 37.5% nên toàn bộ đoạn đổ xuống AI diễn ra
với **máy đứng chết** và packet ở opacity 1.

**Đo trên chính MP4 đã đóng gói** (1152 frame, 30fps, crf 18, yuv420p; mép trái thanh chrome của
cửa sổ app dùng làm mốc — nó tĩnh trong world nên vị trí trên màn hình ĐỌC RA tx của máy):

| frame | t | mốc x | đọc ra |
|---|---|---|---|
| 351 | 11.700s | 264 | máy đứng ở `b3` (tx −1143) — cú lia bắt đầu |
| 369 | 12.300s | **498** | **đang lia** (tx ≈ −910, đúng giữa chuyến) |
| 387 | 12.900s | 730 | tới `b3b` (tx −680) |
| 410 | 13.667s | **730** | **đậu** |
| 432 | 14.400s | **730** | **vẫn đậu** — 1500ms không nhúc nhích |
| 441 | 14.700s | 390 | đang sang b4 (tx ≈ −1018 = đúng điểm giữa) |
| 450 | 15.000s | 49 | tới `b4` (tx −1360) |

Kiểm chứng "đứng chết" bằng nguồn KHÔNG NÉN: một vùng world tĩnh (thẻ `mock data · json`) là
**pixel-identical** ở cả 46 frame từ 12.900s đến 14.400s.

**Packet có về ĐÚNG LÚC máy đậu không** — cũng đo trên MP4, dò dải cam rộng ≥8px trong cột đổ
xuống (x 204–229):

| t | y của packet | |
|---|---|---|
| 12.900s | — | máy vừa đậu, packet còn trên đoạn ngang |
| 13.667s | 80–99 | vừa quẹo góc, bắt đầu đổ xuống |
| 13.900s | 200–219 | giữa đoạn đổ |
| 14.167s | 336–355 | |
| 14.300s | 402–423 | |
| **14.367s** | **438–458** | **nhập vào mũi tên — về tới AI** |

Tức là **toàn bộ 0.8s đổ xuống + cú đáp nằm trọn trong 1500ms đậu**. Trước REV 6 người xem không
hề thấy đoạn này. Hai packet vẫn lệch nửa vòng trên lap 4800ms, `animation-delay` **không đổi** —
lịch của chúng được kiểm lại chứ không bị chỉnh, và nó đã khớp.

**Ăn theo, đều được suy lại chứ không giả định:**

- `traffic-b3`, `arc-halo`: cửa sổ 10200→**14400ms** (26.5625→37.5%).
- `focus-b3b`: 12900→**14400ms** — lên hết đúng lúc máy đậu (0.00 ở 12300ms, 0.50 ở 12600, 1.00 ở 12900).
- `recede-b3`, `br-back` (keyframes viết tay, không qua emitter): giữ tư thế b3 tới 37.5%, trả về
  ở 39.0625% cùng lúc với `br-ok`.
- `lod-app`: **GỘP** hai cửa sổ close-tier thành 10200→18600ms. Xem deviation 28.
- `pull-park`, `stage-dim-b1`, mọi caption, mọi nhịp khác: **không đổi một stop nào**.
- Nhịp thở overview ở 37.5% bị **xoá** — deviation 28.

**Gates:** `verify_all --serve` **20 PASS / 4 N-A** · `run_golden_regression` **PASS** (emitter
tự dựng lại `w-traffic-b3`, `halo-b3`, `focus-b3b` khớp 0.0000 pp với keyframes viết tay) ·
`run_smoke` All checks passed · `validate_csv` / `validate_manifest` sạch · **loop seam
byte-identical** · **reduced-motion sha256 y hệt REV 5** · contact sheet + video 1152 frame dựng
lại toàn bộ.

**Một cái bẫy đã sập trong lúc làm, ghi lại vì nó có ích:** đoạn chú thích REV 6 mới thêm vào lúc
đầu đóng `*/` sớm, làm đoạn REV 5 phía sau rơi ra ngoài comment và **giết luôn `@keyframes beats`**
— trang mất sạch chuyển động camera. `verify_all` vẫn **20 PASS**: stage D đọc manifest, stage E
GHIM transform lên `.camera`, còn `run_golden_regression` đọc HTML bằng regex. Thứ duy nhất kêu là
trường `was` của `pinCamera` (in ra `was none` thay vì `was matrix(...)`) — đúng như hold-frames.mjs
hứa, nhưng nó chỉ là một dòng chữ, không phải một cổng. Xem "câu hỏi mở" ở báo cáo builder.
