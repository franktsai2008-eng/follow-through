# 呈現方式 — Follow-Through：交易握手之後，兩家公司的 AI 之間要跑的流程（13:25 定稿）

## 一句話（中／英）
開完會、握完手，還有一條尾巴要跨過公司線：確認條件、追交付、催款。兩邊各自的 AI 用純文字把它跑完，各守各的權限、各留各的紀錄，越跑越會，但不會學到越線。
**Follow-Through — the tail of a deal, run by each side's own agent.**

## 這條流程長什麼樣（一張圖，六步，四個工具各站一步）
```
 ① 查對方        ② 純文字來回          ③ 對帳           ④ 提案 → 人按 → 執行      ⑤ 第三方重算      ⑥ 記一課
 You.com    →   我方 AI ⇄ 對方 AI   →   兩份紀錄比對   →   One（G01 收據已真寄，messageId 1a091a4d2111535d）   →   Daytona        →   下一案先讀
 公開參考        各守各的權限            盲判＋CrewAI       needs human approval       只放紀錄進去      講限制 8→10/10
```
圖上每個工具只講它真的做的事。One 今天只到「AI 想寄什麼、有沒有權限寄」，寄出去的動作留給人按。

## demo 頁五屏（評審三分鐘）
**第 1 屏 學習**（主題先講）
- 標題一句話＋流程圖。
- 四個數字：`0/10 seller overreach · 8→10/10 states its limit · 5/6 impossible deals refused, none faked · 1 breach caught (the buyer)`。不放成交率。
- G05 冷／學過三行對照：冷開時賣方讓買方簽了遲十天的單；學過之後第二回合就說「這不在我權限，我要走了」。
- 旁白：Same ten cases, seller keeps one lesson per case. It got more explicit about its limit, not more willing to close.

**第 2 屏 這個沒證明什麼**（早講才值錢）
- n=10 單次；冷／學過那次同時換了紀錄模式；學那輪沒審買方；You.com 是免金鑰 MCP；CrewAI 只審三組；Daytona 今天 dry-run；One 已真寄一封 G01 收據到自己信箱（其餘 next actions 仍是提案）。
- 旁白：Ten cases, one pass each. It shows what breaks, not how often.

**第 3 屏 一段完整對話**（步驟 ①②）
- G05 雙欄，左 Company A agent（Claude）右 Company B agent（GPT），像 email 串。
- 每則旁邊小標：within authority／needs approval／walked away。
- 卡片頂端那行公開參考：`market reference · you.com · accio.com, alibaba.com`。G01 那行錯了一個數量級而買方就在那組越線 → 一句：public context is an input, it can also mislead.

**第 4 屏 對帳**（步驟 ③⑤）
- 兩份紀錄並排，三種顏色 identical／equivalent（箱 vs 令）／conflict。
- 盲判格：beyond authority? no · flagged approval? yes；G01 單模型與 CrewAI crew 對買方判決不一致，照放。
- 一行：scoring replayed in a box neither company controls, only records go in（Daytona）。

**第 5 屏 不只談判**（步驟 ④⑥）
- 催款 I03 截圖（第 1–3 回合＋賣方第 4 回合）：買方要 3%，賣方守 2%，$9,212 當天電匯，兩邊紀錄一致。
- 下面「接下來會發生的動作」三行：send remittance confirmation request · create task: close invoice on receipt · log 2% discount — 每行標 requires human approval（One，dry-run）。
- 十條它自己寫的心得摺疊在最下面。

## 60 秒旁白（英文，照唸）
Every deal leaves a tail that crosses a company line. We let each side's own agent run it in plain text. Buyer on Claude, seller on GPT, private cards, written authority, no manager to call. Ten price cases and five overdue invoices, one pass each, a third model auditing blind. The seller never crossed its line. It walked away instead. Records matched, except one deal written in cases on one side and reams on the other. The one breach was the buyer, signing past its own deadline. With lessons, the seller names its limit ten out of ten and walks away from that bad deal. A You.com search puts public price context on both cards, and in one case that line was wrong and the buyer overstepped. Actions are proposed, a human approves, One carries them out. Next: fifty cases and swap the models.

## 四個工具怎麼講（每個一句，都是真的）
- You.com：One line of public context on both cards, source domains shown. In one of three cases it was wrong, and that's the case where the buyer overstepped.
- CrewAI：The blind audit runs as a crew on three cases. On one it disagrees with the single-model judge about the buyer. That disagreement is on the page.
- Daytona：The scoring replays in a box neither company controls. Only the records go in, no login.
- One：The agent proposes the next actions and drafts the receipt. Today it's a dry run; a person approves before anything leaves.

## 交件表格三段（英文）
- **What it does**: Two companies' agents run the tail of a deal (confirm terms, chase payment) in plain prose. Each has a private task card with a hidden constraint and a written authority limit. After every case the agent writes itself one lesson and reads all lessons before the next. A third model audits each exchange blind.
- **What it learned**: With nine lessons behind it the seller states its authority limit in 10/10 cases instead of 8, never oversteps, and walks away from a deal the buyer was about to sign against its own rules. It still closed 4/4 of the cases where a legal deal existed.
- **Sponsor tools**: A You.com search (free MCP endpoint) puts one line of public price context on both cards; in one of three grounded cases that line was off by an order of magnitude and the buyer pushed past its own limit. The blind audit also runs as a CrewAI crew on three cases; on one, the crew and the single-model judge disagree, and that disagreement is on the page. Daytona replays the scoring in a box neither company controls, only the records go in. One carries the receipt out: the G01 receipt went through One's Gmail action to the account's own inbox; the next actions stay proposals until a person approves.

## 現場口頭版（30 秒，對走過來的人）
After a deal there's always a follow-up that crosses into another company: confirm, chase, collect. I let each side's own agent do it in plain text and watched where it breaks. Not at the authority line, the seller never crossed it. At the record, and once because the public price it looked up was wrong.

## 禁字
platform、integration layer、neutral、every company、meeting 當主詞、"I run a business"。
