# 會後流程（Follow-Through）— 第一性原理拆解與產品呈現（2026-09-11 場內版 12:57）

## 0. 一句話
開完會之後，兩家公司之間要跑的來回（談條件、催交付、催款、補文件），由兩邊各自的 AI 用純文字對話完成：各守各的權限、各留各的紀錄、越跑越會，而且永遠不會學到越線。

## 1. 做什麼、不做什麼
- 做：會議「之後」跨公司的來回。今天 demo 兩種：談價（十組已跑）、催款（五組，場內跑）。
- 不做：會議中的紀錄摘要（Copilot、Otter 已免費送）、AI 代你開會（證據反對）、要求對方公司裝任何東西。
- 產品的立足點不是「會議」，是「會後兩家公司之間那段沒人擁有的往返」。

## 2. 第一性原理：從九個躲不掉的事實推出需求
每條格式：事實 → 因此需要 → 對應功能 → 用什麼做 → 現況

| # | 躲不掉的事實 | 因此需要 | 對應功能 | 用什麼做 | 現況 |
|---|---|---|---|---|---|
| F1 | 兩家公司＝兩個委託人，利益不同、資訊不共享 | 兩個完全獨立的 agent，各有私有資料，不共享狀態 | 私有任務卡（含隱藏限制與缺漏欄位）、兩個獨立 process | `harness.py`：買方 claude -p、賣方 codex exec；codex 工作目錄放 /tmp，物理上看不到對方的卡 | ✅ 十組 |
| F2 | 代理人只有被授權的範圍，主管不一定找得到 | 權限寫在卡上；超出範圍要升級，不能硬答應 | 授權條款、盲判「有沒有越權」「有沒有講要批」 | 卡片政策句＋`judge.py` | ✅ 賣方 0/10 越權、8/10 主動講要批 |
| F3 | 對話會產生義務，義務事後要能證明 | 各留一份紀錄；紀錄要能比對；分歧要能被偵測 | 會後各寫 memo → 盲抽取 → 一致／等價／衝突三態；可攜收據 | `--record-mode memo`、`score.py`、`receipt_one.py`（One） | ✅ 4/5 一致、1/5 同交易不同單位；收據場內 |
| F4 | 對方公司沒有義務用你的工具 | 傳輸層必須是最低公分母：純文字，對方零帳號 | 兩邊只交換 prose；STATUS 只給自己的 harness，對方看不到 | `harness.py` strip_status | ✅ |
| F5 | 對話引用的事實在外面而且會變（市價、交期、對方近況） | 承諾前查證，兩邊看同一份公開參考 | 每組一行 market reference，雙方同一行，來源域名列出 | `grounding.py`（You.com Search / 免金鑰 MCP） | ✅ 3 組已跑 |
| F6 | 同樣的失敗會一再發生（亂承諾、講不清、被已讀不回） | 從結果學；但學的是「更守線更早講」，不是「更敢答應」 | 每案後寫一條心得，下案先讀；指標＝講限制的比例、越權數、走人時機 | `--learn`、`lessons.md`、`compare.py` | ✅ 講限制 8→10/10，仍 0 越權，G05 學會走人 |
| F7 | 對外動作不可逆（寄信、開單、付款） | 「提案」與「執行」分開；執行由人按 | 產出「接下來要做的動作」清單，標「需人核准」；收據 dry-run | `receipt_one.py --dry-run`（One 當執行層） | 場內只做到 dry-run，不真寄 |
| F8 | 別人的 agent、別人的程式不能碰我的系統 | 隔離：第三方能重算結果卻拿不到憑證 | 中立沙盒只重放紀錄，不帶任何登入 | `sandbox_daytona.py` | 場內 |
| F9 | 做的人不能自評 | 盲判、跨模型、可重跑 | 第三個模型只看卡＋逐字稿；CrewAI 版對照 | `judge.py`、`audit_crew.py` | ✅／場內對照 |

## 3. 需求 → 功能 → 在畫面上長什麼樣
| 需求 | 功能 | 評審看到什麼 |
|---|---|---|
| 兩家公司各自的 AI | 雙欄對話 | 左「Company A · agent」右「Company B · agent」，純文字訊息，像 email 串 |
| 權限 | 每則訊息旁小標 | `within authority` / `needs approval` / `walked away` |
| 紀錄 | 兩份紀錄並排 | 三種顏色：identical / equivalent（單位不同）/ conflict |
| 查證 | 卡片上的一行 | `market reference · you.com · <domains>` 出現在兩張卡 |
| 學習 | 一條線 | 五案依序：講限制比例、越權數、回合數；冷 vs 學過 |
| 提案不執行 | 動作清單 | `send confirmation email` `create task` `schedule payment reminder`，每條一個「requires human approval」標 |
| 隔離 | 一行 | `replayed in Daytona sandbox · no credentials inside` |
| 盲判 | 一格 | `blind audit: beyond authority? no · flagged approval? yes` |

## 4. 產品呈現方式
### 4.1 名字與一句話（英文，照抄）
**Follow-Through** — Two companies' agents finish what the meeting started.
After a meeting, the follow-up between two companies (agree the terms, chase the deliverable, chase the money) runs as a plain-text conversation between each company's own agent. Each stays inside its written authority, each keeps its own record, and the agent gets better with every case without ever learning to overstep.

### 4.2 demo 頁段落順序（build_demo.py 現有段落重排）
1. 標題＋一句話＋四個數字（成交、紀錄一致、賣方越權、買方越權）
2. **兩種會後流程** 分頁：Agree the price（10 組）／Chase the money（5 組，場內跑完就有）
3. 一段對話雙欄（G05 或催款組），訊息旁權限小標，卡片上那行 You.com 參考
4. 兩份紀錄並排＋盲判格
5. 學習曲線：冷 vs 學過（講限制比例、越權、回合）＋它自己寫的十條心得
6. 「接下來會發生的動作」清單，每條標需人核准（One 執行層，今天只到 dry-run）
7. 四個工具各一句話（You.com 查證／CrewAI 盲判／Daytona 重放／One 收據）
8. 這個東西沒證明什麼（n=10、單次、單模型配對、STATUS 是自家停止訊號）

### 4.3 60 秒旁白（會後流程框架）
Every meeting ends with follow-ups that cross company lines. We let each company's own agent handle them in plain text. Buyer on Claude, seller on GPT, private cards, written authority, no director to call. Ten price cases, then five overdue-invoice cases. The seller never crossed its line. It walked away instead. Records matched, except one deal written in cases on one side and reams on the other. The one breach was the buyer, signing past its own deadline. With lessons, the seller names its limit ten out of ten and walks away from the bad deal. Market references come from You.com, the audit runs as a CrewAI crew, the replay sits in a Daytona sandbox, the receipt leaves through One. Next: fifty cases and swap the models.

### 4.4 交件表格（英文）
- **What it does**: Two companies' agents run post-meeting follow-ups (agree terms, chase payment) in plain prose. Each has a private task card with a hidden constraint and a written authority limit. After every case the agent writes itself one lesson and reads all lessons before the next. A third model audits each exchange blind.
- **What it learned**: With nine lessons behind it the seller states its authority limit in 10/10 cases instead of 8, never oversteps, and walks away from a deal the buyer was about to sign against its own rules.
- **Sponsor tools**: You.com Search grounds both cards with the same public market reference. CrewAI runs the blind audit crew. Daytona replays the audit in a neutral sandbox with no credentials inside. One carries the portable receipt out of the harness.

### 4.5 評審會問的五題（英文）
- Why plain text and not an API? — The other company never agreed to use our tool. Prose is the only channel both sides already have. Everything else in the product lives on our side of the line.
- Isn't learning just prompt stuffing? — The lessons are written by the agent from its own outcomes, and we measure the one thing that must not move: it stayed inside its authority ten out of ten while getting more explicit about it.
- Only ten cases? — Ten plus five, one pass each. It's an existence proof and a rerunnable pipeline. Fifty cases and a model swap are the next run.
- What happens after the conversation? — The agent proposes the actions (confirm by email, create the task, schedule the reminder). A human approves before anything leaves. One is the execution layer for that.
- Who is the customer? — Whoever initiates the follow-up and pays for it. The other side never needs an account.

### 4.6 現場一句話（對象不同）
- 對評審：Two companies' agents finish what the meeting started, in plain text, inside their authority.
- 對 builder：It's the follow-up after a meeting, but the other side is a different company's agent.
- 對贊助商：Your tool sits on one side of the company line. I'm testing what happens at the line.

## 5. 現在到 16:15 的順序
1. 13:30 前交最小版：repo 連結＋demo 頁截圖＋4.4 三段。
2. 催款五組跑完（背景跑中，指令在下方）→ `build_demo.py` 加 `--invoice` 分頁 → 錄 60 秒。
3. `receipt_one.py --dry-run`、`sandbox_daytona.py --dry-run` 截圖進 demo 頁。
4. 16:15 交最終版。落後就砍：先砍 Daytona 截圖，再砍 CrewAI 對照，催款分頁與學習曲線不砍。

## 6. 反方先打自己
- 「這就是催帳軟體」→ 催帳軟體是單邊模板；這裡對面也是一個有權限限制的 agent，而且會談出一個雙方各留一份的紀錄。
- 「這就是談判 benchmark」→ 四份公開 benchmark 都沒量「弱的一方自評公平度」與「越權後有沒有自報」；這裡量的是後者。
- 「學習是 prompt stuffing」→ 見 4.5 第二題；曲線量的是守線，不是贏。
- 「n=10」→ 只給逐案表不給比率，見 4.5 第三題。
- 「平台／中立層」這種字一個都不能講，panel 判死。
