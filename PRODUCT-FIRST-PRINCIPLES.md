# Follow-Through — 第一性原理拆解與產品呈現（2026-09-11 場內版 13:05，已吸收獨立審查）

## 0. 一句話
一筆交易握手之後還有一條尾巴要跨過公司線：確認條件、追交付、催款。我們讓兩邊各自的 AI 用純文字把這條尾巴跑完：各守各的權限、各留各的紀錄、越跑越會，但不會學到越線。

## 1. 做什麼、不做什麼
- 做：交易「之後」跨公司的來回。今天主角是談價十組；催款只放一個跑完的案例當「不只談判」的一張截圖，不做分頁。
- 不做：會議中的紀錄摘要（大平台免費送）、AI 代你開會（證據反對）、要求對方公司裝任何東西。
- 主詞是「交易的尾巴」，不是會議。

## 2. 躲不掉的事實 → 需求 → 功能（頁面只放前四條，其餘是方法註腳）
| # | 事實 | 因此需要 | 功能 | 工具 | 資料怎麼說 |
|---|---|---|---|---|---|
| F1+F2 | 兩家公司＝兩個委託人，利益不同、資訊不共享；代理人只有被授權的範圍，主管不一定在 | 兩個獨立 process、私有卡片；權限寫在卡上，超出要升級不能硬答應 | 私有任務卡＋授權句；盲判越權／自報 | `harness.py`（claude -p／codex exec，codex 工作目錄在 /tmp）、`judge.py` | 賣方 0/10 越權、8/10 主動講要批、六組不可能成的單五組拒絕、零假成交 |
| F4 | 對方沒義務用你的工具 | 傳輸＝純文字，對方零帳號 | 只交換 prose；STATUS 是自家停止訊號 | `harness.py` | 十組全程純文字 |
| F3 | 兩邊對同一筆交易的理解會分歧，而且沒東西對帳 | 各留一份紀錄、可比對、分歧可偵測 | memo→盲抽取→identical／equivalent／conflict | `score.py`、`receipt_one.py` | JSON 紀錄那輪：4/5 一致、1 筆同交易一邊記箱一邊記令；memo 那輪：4/4 一致 |
| F7 | 對外動作不可逆 | 提案與執行分開，人按 | 動作清單標 needs human approval；收據 dry-run | `receipt_one.py`（One） | 場內只到 dry-run |
| F5（假說，今天半證偽） | 引用的外部事實會變，而且引來的可能是錯的 | 來源要看得見、要能被質疑，不是「兩邊看同一行就更準」 | 卡片上一行公開參考＋來源域名 | `grounding.py`（You.com 免金鑰 MCP，不是 Search API） | 三組裡買方唯一一次越線就在參考最爛的 G01（$1.33–4.70/piece 對上 $44/unit）→ 公開參考是輸入，也會誤導 |
| F6（設計目標，不是事實） | 同一個學習訊號可以用「更敢答應」或「更會拒絕」兩種方式滿足 | 學習目標明寫成守線，成交率另外看住 | `--learn` 心得；量講限制、越權、非陷阱組成交 | `compare.py` | 講限制 8→10/10；賣方仍 0 越權；非陷阱組兩輪都 4/4 成交；多走的那次是 G05 買方要簽爛單 |
| F8 | 別人的東西不能碰我的系統 | 第三方能重算卻拿不到憑證 | 只放紀錄進沙盒重放 | `sandbox_daytona.py` | 場內 |
| F9（方法規範） | 做的人不能自評 | 盲判、跨模型 | 單模型判＋CrewAI crew 對照 | `judge.py`、`audit_crew.py` | crew 只跑 3 組，G01 買方判決兩者不一致，這個不一致直接放頁上 |

## 3. 已知的洞（先講比被抓到好）
- 冷 vs 學過那次比較同時換了紀錄模式（json→memo），n=1 無重跑，學習與噪音分不開。下一跑：50 組、重跑三次、模式固定。
- learn 那輪沒跑買方盲判，「仍零越權」只講賣方。
- 走人的案例紀錄欄留白或寫 terms discussed, no deal，不要顯示賣方 memo 抽出來的最後報價。
- You.com 用的是免金鑰 MCP；CrewAI 只審了三組；Daytona 與 One 今天只到 dry-run。

## 4. 產品呈現
### 4.1 名字與一句話（英文照抄）
**Follow-Through** — the tail of a deal, run by each side's own agent.
After the handshake someone still has to confirm the terms, chase the delivery and chase the money across a company line. Here each company's own agent does it in plain text, stays inside its written authority, keeps its own record, and gets more explicit about its limits with every case.

### 4.2 demo 頁順序（三分鐘評審）
1. 第一屏＝學習：G05 冷／學過兩段逐字稿三行對照＋四個數字：`0/10 seller overreach · 8→10/10 states its limit · 5/6 impossible deals refused, none faked · 1 breach caught (the buyer)`。不放成交率。
2. 第二屏＝這個東西沒證明什麼（第 3 節四條）。早講才值錢。
3. 一段完整對話雙欄（G05），訊息旁 within authority／needs approval／walked away；卡片上那行公開參考連來源域名。
4. 兩份紀錄並排＋盲判格；G01 單模型與 crew 不一致那格照放。
5. 十列逐案表；最後一列放一個催款案例當截圖。
6. 一行：proposed next actions, human approves before anything leaves（One）；一行：scoring replayed in a box neither company controls, only records go in（Daytona）。
7. 四個工具各一句。

### 4.3 60 秒旁白
Every deal leaves a tail that crosses a company line. We let each side's own agent run it in plain text. Buyer on Claude, seller on GPT, private cards, written authority, no manager to call. Ten cases, one pass each, a third model auditing blind. The seller never crossed its line. It walked away instead. Records matched, except one deal written in cases on one side and reams on the other. The one breach was the buyer, signing past its own deadline. With lessons, the seller names its limit ten out of ten and walks away from that bad deal. A You.com search puts one line of public price context on both cards, and in one case that line was wrong and the buyer overstepped. Next: fifty cases and swap the models.

### 4.4 交件表格（英文）
- **What it does**: Two companies' agents run the tail of a deal (confirm terms, chase payment) in plain prose. Each has a private task card with a hidden constraint and a written authority limit. After every case the agent writes itself one lesson and reads all lessons before the next. A third model audits each exchange blind.
- **What it learned**: With nine lessons behind it the seller states its authority limit in 10/10 cases instead of 8, never oversteps, and walks away from a deal the buyer was about to sign against its own rules. It still closed 4/4 of the cases where a legal deal existed.
- **Sponsor tools**: A You.com search (free MCP endpoint) puts one line of public price context on both cards; in one of three grounded cases that line was off by an order of magnitude and the buyer pushed past its own limit, so public context is an input that can also mislead. The blind audit also runs as a CrewAI crew on three cases; on one, the crew and the single-model judge disagree about the buyer, and that disagreement is on the page. Daytona replays the scoring in a box neither company controls, only the records go in, no login. One carries the receipt out; today that is a dry run.

### 4.5 評審會問的六題
- Your compliance number went up but your deal rate went down. How do you know you didn't just teach it to refuse? — In both runs it closed 4 out of 4 cases where a legal deal existed. The only extra walk-away is the trap case where the buyer was about to sign past its own deadline. If the lesson were "refuse more", the non-trap cases would drop first. They didn't.
- Isn't the real fix a shared schema or an API between the two companies? — That is exactly the question. The other company never agreed to our schema. So I test how far plain prose gets, and where it breaks: so far, not at the authority line, but at the record.
- Why plain text and not an API? — The other company never agreed to use our tool. Prose is the only channel both sides already have.
- Isn't learning just prompt stuffing? — The lessons are written by the agent from its own outcomes. I score the thing that must not move: it stayed inside its authority ten out of ten while getting more explicit about it.
- Only ten cases? — Ten, one pass each. The rates are in the file with explicit denominators. I'm not extrapolating them. Fifty cases, three reruns, one record mode, that's the next run.
- Who is the customer? — The side that wants the loop closed. I'm not selling anything today. This is an experiment.

### 4.6 現場一句話
- 對評審：The tail of a deal, run by each side's own agent, in plain text, inside its authority.
- 對 builder：It's the follow-up after a deal, but the other side is a different company's agent.
- 對贊助商：Your tool sits on one side of the company line. I'm testing what happens at the line.

## 5. 現在到 16:15
1. 13:30 交最小版：repo 連結＋demo 頁截圖＋4.4 三段。
2. demo 頁按 4.2 重排（學習放第一屏、四個數字換掉、洞放第二屏、走人列留白）。
3. 催款挑一個跑完的案例做成一張截圖放第五屏。
4. 16:15 交最終版。落後先砍 Daytona 截圖、再砍 CrewAI 對照；學習第一屏與第二屏的洞不砍。

## 6. 反方先打自己（照這個講）
- 「真正的解法不是共用 schema 或 API 嗎」→ 4.5 第二題。
- 「這就是談判 benchmark」→ I'm not scoring who won. I score whether each side stayed inside a written authority, and whether the two records of the same deal match.
- 「學習是 prompt stuffing」→ 4.5 第四題。
- 「n=10」→ 4.5 第五題。
- 「這就是催帳軟體」→ 催帳軟體是單邊模板；這裡對面也是一個有權限的 agent。
- 禁字：platform、integration layer、neutral、every company、meeting 當主詞。
