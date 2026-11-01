# Humanizer — 26 Anti-AI-Writing Tells & Editorial Rewrite Standard (`blader/humanizer`)

Distilled from [`blader/humanizer`](https://github.com/blader/humanizer) (`★ 63k+`) and Wikipedia's *Signs of AI writing* guide. Apply this pass to every Vietnamese (`VI`) and English (`EN`) article on `blog.khanhdp.com` (and technical stories on `truyen.khanhdp.com`) so prose reads like a Principal Systems Engineer writing from real production telemetry — never like an LLM template.

---

## Core Principle: Cut the Costume, Keep the Substance

Removing AI words (`delve`, `tapestry`, `pivotal`) is only half the job. A piece full of clean words can still announce itself as AI in every paragraph if it keeps **the staging, the cadence, and the defensive throat-clearing** that language models default to.

### Before Every Paragraph, Ask:
1. **Can I state the fact or metric in sentence 1 without a theatrical warm-up?**
2. **Do three consecutive sentences have different lengths and rhythms?**
3. **Did I name the exact syscall, SQL operator, lock key, or latency percentile instead of saying "plays a crucial role in modern distributed systems"?**

---

## Category A: Staging Instead of Stating (Cut Immediately)

### 1. "Not X, but Y" Contrast Addiction (`Không chỉ là X, mà còn là Y`)
LLMs compulsively negate a strawman before stating their point — often 2–3 times per section.
- ❌ **AI Tell (EN)**: *"Singleflight is not about caching forever — it's about coalescing concurrent misses. It isn't a silver bullet; rather, it is a concurrency primitive."*
- ❌ **AI Tell (VI)**: *"Singleflight không chỉ đơn thuần là một lớp cache — đó là nghệ thuật điều phối bất đồng bộ."*
- ✅ **Engineer Prose (EN)**: *"Singleflight coalesces concurrent cache misses onto one in-flight Promise."*
- ✅ **Engineer Prose (VI)**: *"Singleflight gom toàn bộ các truy vấn trùng khóa đang bay vào chung một Promise duy nhất."*

### 2. One-Line Mic-Drop Closers
A short sentence on its own line at the end of a section (`And that changes everything.` / `Period.` / `Và đó mới là kiến trúc thực thụ.`).
- **Fix**: Delete the mic-drop line or fold the concrete metric into the paragraph above.

### 3. Aphorisms & Sayings That Sound Deep (`Chân lý rỗng`)
Contrived proverbs (`Speed is a feature, until it breaks consistency.` / `In distributed systems, silence is the loudest alarm.`).
- **Fix**: State the engineering invariant directly (`When Redis Sentinel takes 4.5s to fail over, an unbounded retry loop turns a brief blip into a connection-pool outage`).

### 4. Staged Run-Ups (`Màn dạo đầu rườm rà`)
`Here's the thing:` / `Let's unpack this.` / `What this really means is:` / `Hãy cùng bóc tách vấn đề này:`.
- **Fix**: Delete the run-up and start with the technical claim.

### 5. Arguing With Nobody (`Strawman Skeptic`)
`You might assume a B-Tree index solves this, right? Wrong.` / `Critics often overlook...`
- **Fix**: Show the `EXPLAIN (ANALYZE, BUFFERS)` plan where the B-Tree index still reads 42,000 heap pages and explain why.

---

## Category B: Rhythm by Rule (Break Mechanical Cadence)

### 6. The Rule-of-Three Compulsion (`Bộ ba cưỡng bức`)
Every list has 3 items; every noun gets 3 adjectives (`fast, reliable, and scalable` / `nhanh chóng, an toàn và hiệu quả`).
- **Fix**: Use 1 exact adjective with a number (`0.21ms p95`), or list 2 or 4 real items.

### 7. Parallel Sentence Openings
Starting 3–4 sentences in a row with `This ensures... This prevents... This enables...` or `If X... If Y... If Z...`.
- **Fix**: Vary sentence structure and merge redundant consequences.

### 8. Em-Dash (`—`) Addiction
Using `—` two or three times per paragraph to bolt an explanation onto the end of a clause (`The query scanned 1.2M rows — a classic sign of chunk exclusion failure — before timing out`).
- **Fix**: Maximum **1 em-dash per section**. Prefer periods, colons, parentheses, or commas.

### 9. Stacked Hedge Qualifiers
`It is worth noting that this approach can potentially help mitigate some of the latency issues...`
- **Fix**: `This cuts p99 latency from 480ms to 27ms.`

---

## Category C: Inflation & Borrowed Authority

### 10. The 24 Banned AI Watchwords
Never use these words in English or their clichés in Vietnamese unless inside a literal code identifier:

| Banned EN Word | Banned VI Equivalent | Replace With |
|---|---|---|
| `delve` / `unpack` | `đào sâu` / `bóc tách` | `inspect`, `profile`, `trace` / `đo đạc`, `truy vết` |
| `tapestry` / `landscape` | `bức tranh toàn cảnh` | Name the stack (`PostgreSQL 16 + Valkey`) |
| `testament` / `beacon` | `minh chứng sống động` | Show the benchmark table |
| `pivotal` / `crucial` / `vital` | `đóng vai trò then chốt` | State what breaks if removed |
| `underscores` / `highlights` | `làm nổi bật` / `nhấn mạnh` | `shows`, `proves` / `chứng minh` |
| `seamless` / `effortless` | `mượt mà không tì vết` | State the exact SLA (`0ms TBT`, `<1ms TTFB`) |
| `robust` / `holistic` | `toàn diện` / `vững chắc` | State the fault-tolerance invariant |
| `leverage` / `utilize` | `tận dụng tối đa` | `use` / `dùng` |
| `foster` / `cultivate` / `elevate` | `nâng tầm` | Cut entirely |
| `game-changer` / `paradigm shift` | `bước ngoặt cách mạng` | Cut entirely |

### 11. Shallow `-ing` Tail Riders
Ending sentences with `, ensuring seamless scalability and enhancing developer productivity` or `, từ đó tối ưu hóa trải nghiệm người dùng`.
- **Fix**: Cut the `-ing` tail at the comma. If the consequence matters, give it a real metric in its own clause.

### 12. Fancy Synonyms for `is / are / has`
Replacing `is` with `serves as`, `stands as`, `boasts`, `features`, or `represents`.
- **Fix**: Write `is` or `has`.

---

## Category D: Formatting by Rule

### 13. Bold-Label Bullet Overload
Turning every single paragraph into a bulleted list of `**Bold Concept:** One sentence explanation.`
- **Fix**: Use tables for structured comparisons (`Option | Pros | Cons | Recommendation`) and real prose paragraphs for narrative cause-and-effect.

### 14. Title-Case / Emoji Section Headers in Technical Prose
- **Fix**: Keep section headings concise, specific, and free of decorative emojis.

---

## Category E & F: Chatbot Residue & Over-Explaining

### 15. Meta-Announcements & Reader Flattery
`In this article, we will explore...` / `Let's dive right in!` / `As every senior engineer knows...` / `In conclusion, by combining X, Y, and Z...`
- **Fix**: Start directly with the production failure mode or telemetry anomaly. End with the verification result or operational trade-off.

### 16. Re-Explaining Textbook Basics to Senior Readers
Don't spend a paragraph defining what Redis is or how HTTP status codes work before showing a Singleflight lock script. Assume the reader is a staff engineer who wants the exact race condition and the exact fix.
