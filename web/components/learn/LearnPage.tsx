import Link from "next/link";
import { VixPulseLogo } from "@/components/v2/VixPulseLogo";

export type LearnLang = "en" | "zh";

const TIERS: Array<{
  index: 0 | 1 | 2 | 3 | 4 | 5;
  vix: string;
  cash: string;
  buy: string;
  action: { en: string; zh: string };
  meaning: { en: string; zh: string };
}> = [
  {
    index: 0,
    vix: "<15",
    cash: "70%",
    buy: "0%",
    action: { en: "Rest", zh: "休兵" },
    meaning: {
      en: "Market complacent. Asymmetric downside. Don't add.",
      zh: "市場自滿，下行不對稱風險。不加碼。",
    },
  },
  {
    index: 1,
    vix: "15–18",
    cash: "60%",
    buy: "2-5%",
    action: { en: "Cautious", zh: "警戒佈局" },
    meaning: {
      en: "Below average. Defensives only — KO, JNJ, WMT.",
      zh: "低於均值。僅防禦性持倉 — KO, JNJ, WMT。",
    },
  },
  {
    index: 2,
    vix: "18–24.6",
    cash: "50%",
    buy: "3-5%",
    action: { en: "Watch", zh: "觀察" },
    meaning: {
      en: "Median range. Quality growth, small entries.",
      zh: "中位區間。優質成長股，小額試水溫。",
    },
  },
  {
    index: 3,
    vix: "24.6–29.5",
    cash: "35%",
    buy: "5-10%",
    action: { en: "Scale in", zh: "分批進場" },
    meaning: {
      en: "Top quartile. Real opportunity emerging.",
      zh: "前 25%。真正的機會浮現。",
    },
  },
  {
    index: 4,
    vix: "29.5–35",
    cash: "20%",
    buy: "10-20%",
    action: { en: "Catch panic", zh: "恐慌承接" },
    meaning: {
      en: "Top decile. High-conviction buys.",
      zh: "前 10%。高信念進場。",
    },
  },
  {
    index: 5,
    vix: ">35",
    cash: "20%",
    buy: "Heavy",
    action: { en: "Extreme", zh: "極端機會" },
    meaning: {
      en: "Crisis territory. Best risk/reward in years. Never all-in.",
      zh: "危機區。多年最佳風報比。永不 all-in。",
    },
  },
];

const RULES: Array<{
  n: number;
  title: { en: string; zh: string };
  body: { en: string; zh: string };
}> = [
  {
    n: 1,
    title: { en: "Cash targets are anchors, not commands", zh: "現金目標是錨，不是命令" },
    body: {
      en: "If today says 50% cash and you're at 40%, that's a signal to be cautious about adding — not a panic-sell signal. Your portfolio drifts toward the target over time, not in one day.",
      zh: "若今日目標 50% 現金、你目前 40%，這是「加碼要謹慎」的訊號 — 不是「立刻砍倉」。部位隨時間慢慢漂向目標，不是一天到位。",
    },
  },
  {
    n: 2,
    title: { en: "Add slowly during stress, sell slowly during euphoria", zh: "壓力期慢慢加碼，亢奮期慢慢出脫" },
    body: {
      en: "When VIX moves into Tier 3-5, it's tempting to wait for the absolute bottom. Don't. Add 5-10% per Tier 3 day, 10-20% per Tier 4 day, in chunks. Some buys will be early — that's fine. Disciplined accumulation, not perfect timing.",
      zh: "當 VIX 進入 Tier 3-5，會很想等到絕對最低點。別等。Tier 3 加 5-10%、Tier 4 加 10-20%，分批進場。有些會買得太早 — 沒關係。有紀律地累積，不是完美擇時。",
    },
  },
  {
    n: 3,
    title: { en: "Trust the framework over the headline", zh: "相信框架勝於相信頭條" },
    body: {
      en: "When the news screams \"WORST CRISIS EVER\" and VIX Pulse says Tier 4, the framework is telling you to buy. The discomfort of buying during fear is precisely the edge — most investors freeze and miss it.",
      zh: "當新聞大喊「史上最大危機」而 VIX Pulse 在 Tier 4 時，框架是在告訴你買。在恐懼當下買的不適感正是優勢的來源 — 多數投資人會凍結、錯過機會。",
    },
  },
  {
    n: 4,
    title: { en: "Position sizing matters more than timing", zh: "部位大小比擇時更重要" },
    body: {
      en: "A 3% position in NVDA at the wrong moment is recoverable. A 30% position in NVDA at the wrong moment is not. Always size within the tier's buy-size band. Concentration is the source of pain even when you were directionally correct.",
      zh: "NVDA 3% 部位在錯時點可以恢復。30% 部位在錯時點則不能。永遠把部位控制在 Tier 的進場規模區間。集中度是疼痛的來源，即使方向你猜對了。",
    },
  },
  {
    n: 5,
    title: { en: "Earnings override the framework", zh: "財報優先於框架" },
    body: {
      en: "If a holding has earnings within 7 days, default to trim or hedge — even if the tier says add. Binary catalysts (earnings, FDA decisions, merger votes) introduce single-event risk that the framework's regime logic doesn't price.",
      zh: "若持倉七日內有財報，預設減碼或避險 — 即使該 Tier 說可以加碼。二元事件（財報、FDA 決定、併購投票）帶來單一事件風險，這不是框架的 VIX 環境邏輯能處理的。",
    },
  },
];

const SECTIONS: Array<{
  emoji: string;
  title: { en: string; zh: string };
  question: { en: string; zh: string };
  body: { en: string; zh: string };
}> = [
  {
    emoji: "📊",
    title: { en: "Tier banner", zh: "Tier 標題列" },
    question: { en: "Where are we today?", zh: "今天我們在哪裡？" },
    body: {
      en: "Current VIX, today's tier, suggested cash target, and buy-size band. Macro context for everything else.",
      zh: "當下 VIX、今日 Tier、建議現金比例、進場規模區間。其他資訊的總體脈絡。",
    },
  },
  {
    emoji: "📝",
    title: { en: "Today's Take", zh: "今日觀點" },
    question: { en: "What should I do?", zh: "我今天該做什麼？" },
    body: {
      en: "AI-generated synthesis: market read + contrarian view + per-position action calls (hold / add / trim / exit / watch) with confidence and rationale.",
      zh: "AI 綜合分析：市場解讀 + 反方觀點 + 每檔持倉的動作（hold / add / trim / exit / watch），含信心度與理由。",
    },
  },
  {
    emoji: "🚩",
    title: { en: "Watch List", zh: "關注名單" },
    question: { en: "What to worry about?", zh: "有什麼要擔心的？" },
    body: {
      en: "Holdings flagged by closed-vocab labels — oversold RSI, earnings within 7 days, deep drawdown, near 52-week high. Per-position alarm system.",
      zh: "觸發預定義事件標籤的持倉 — RSI 超賣、七日內財報、深度回檔、接近 52 週高。每檔部位的警報系統。",
    },
  },
  {
    emoji: "📡",
    title: { en: "Universe Scanner", zh: "標的掃描" },
    question: { en: "What to add or avoid?", zh: "可以加碼什麼？該避開什麼？" },
    body: {
      en: "59-ticker universe filtered by today's tier and historical VIX-regime behavior. Three sub-regions: 🟢 Add candidates, 🟡 Watch (transition), 🔴 Avoid candidates.",
      zh: "59 檔標的池依今日 Tier 與歷史 VIX 行為過濾。三區：🟢 加碼候選、🟡 觀察（轉換）、🔴 避開候選。",
    },
  },
  {
    emoji: "💼",
    title: { en: "Holdings", zh: "持倉" },
    question: { en: "Position stats", zh: "部位數據" },
    body: {
      en: "Each holding's price, return vs cost, RSI, distance from 50/200-day moving averages, distance from 52-week high.",
      zh: "每檔持倉的：股價、相對成本損益、RSI、相對 50 日／200 日均線距離、相對 52 週高點距離。",
    },
  },
  {
    emoji: "🌐",
    title: { en: "Market Snapshot", zh: "市場快照" },
    question: { en: "Broad context", zh: "整體市場脈絡" },
    body: {
      en: "VIX, VIX3M (forward expectation), S&P 500, Nasdaq, Dow, USD/JPY, BTC, gold, WTI oil. Cross-asset context for today.",
      zh: "VIX、VIX3M（前向預期）、S&P 500、Nasdaq、Dow、USD/JPY、BTC、黃金、WTI 原油。今日跨資產脈絡。",
    },
  },
];

const QUICK_STEPS: Array<{ n: number; en: string; zh: string }> = [
  { n: 1, en: "Read today's tier and cash target.", zh: "看今日 Tier 與現金目標。" },
  { n: 2, en: "Compare to your portfolio. Above or below the target?", zh: "對比目前部位。高於或低於目標？" },
  { n: 3, en: "Set a small drift goal — \"5% closer this week,\" not full restructure.", zh: "設定小的漂移目標 — 「本週靠近 5%」，不是大重整。" },
  { n: 4, en: "Watch the Watch List for binary catalysts (earnings, special-case flags).", zh: "盯關注名單的二元催化事件（財報、特殊規則旗標）。" },
  { n: 5, en: "Use the Universe Scanner when deploying cash.", zh: "佈局現金時看標的掃描。" },
];

const NOTS: Array<{ en: string; zh: string }> = [
  { en: "Not financial advice", zh: "非投資建議" },
  { en: "Not auto-trading", zh: "非自動交易" },
  { en: "Not day-trading", zh: "非當沖" },
  { en: "Not get-rich-quick", zh: "非快速致富" },
];

const T = (lang: LearnLang) => ({
  hero_title: lang === "en" ? "Daily decision support for the disciplined investor" : "給有紀律投資人的每日決策輔助",
  hero_sub:
    lang === "en"
      ? "VIX Pulse turns the VIX from a number into a framework: where the regime is today, what your positions look like through that lens, and what specific actions are warranted."
      : "VIX Pulse 把 VIX 從一個數字轉成框架：今天的環境在哪、用這個視角看你的部位、以及該採取什麼具體動作。",
  cta_today: lang === "en" ? "→ See today's report" : "→ 看今日報告",
  quick_start: lang === "en" ? "Quick start" : "快速開始",
  what_is_vix: lang === "en" ? "What is VIX?" : "VIX 是什麼？",
  vix_intro:
    lang === "en"
      ? "Wall Street's fear gauge. A number from S&P 500 options prices that measures how nervous the market is right now, looking ahead 30 days. Big VIX moves correlate with falling markets — but VIX itself is direction-agnostic. It measures expected size of move, not which way."
      : "華爾街的恐懼指標。由 S&P 500 選擇權價格計算，衡量市場目前的緊張程度，預期接下來 30 天的波動。VIX 大漲常伴隨股市下跌 — 但 VIX 本身與方向無關，它衡量預期波動幅度。",
  framework: lang === "en" ? "The 6-tier framework" : "六個 Tier 框架",
  framework_caption:
    lang === "en"
      ? "Each tier has a target cash percentage to keep on the sidelines and a target buy size per new position. Most investors do the opposite — buy heavy when markets feel safe, sell when scared. The framework forces the reverse."
      : "每個 Tier 都有建議的現金比例與單筆進場規模。多數人做的剛好相反 — 市場安全時重押、市場可怕時殺出。這套框架強制反向操作。",
  rules: lang === "en" ? "Five rules to invest better" : "投資得更好的五條原則",
  how_to_read: lang === "en" ? "How to read each section" : "如何讀懂每個區塊",
  what_not: lang === "en" ? "What VIX Pulse is NOT" : "VIX Pulse 不是什麼",
  open_source: lang === "en" ? "Open source" : "原始碼開放",
  open_source_body:
    lang === "en" ? (
      <>
        VIX Pulse is open-source on{" "}
        <a className="underline" href="https://github.com/crotchblow-prog/stockpulse">
          GitHub
        </a>
        . Framework lives in <code>config/holdings.json</code>, the 59-ticker universe in{" "}
        <code>scripts/analyzers/regime_sensitivity.py</code>. Daily reports committed to{" "}
        <code>web/public/reports/</code>.
      </>
    ) : (
      <>
        VIX Pulse 開源於{" "}
        <a className="underline" href="https://github.com/crotchblow-prog/stockpulse">
          GitHub
        </a>
        。框架本體在 <code>config/holdings.json</code>，59 檔標的池在{" "}
        <code>scripts/analyzers/regime_sensitivity.py</code>。每日報告 commit 到{" "}
        <code>web/public/reports/</code>。
      </>
    ),
});

const TIER_COLORS = ["#3b82f6", "#06b6d4", "#a3a3a3", "#f59e0b", "#f97316", "#ef4444"];

export function LearnPage({ lang }: { lang: LearnLang }) {
  const t = T(lang);
  return (
    <article className="space-y-12 pb-12">
      {/* ── Hero ─────────────────────────────────────────────────── */}
      <header className="space-y-4 pt-2">
        <div className="flex items-center gap-3">
          <VixPulseLogo size={32} />
          <span className="font-mono text-base tracking-wider">VIX PULSE</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight leading-tight">
          {t.hero_title}
        </h1>
        <p className="text-base leading-relaxed text-[color:var(--color-muted)]">{t.hero_sub}</p>
        <div>
          <Link
            href={lang === "en" ? "/" : "/zh"}
            className="inline-block border rounded-md px-4 py-2 text-sm font-mono tracking-wide hover:bg-white/5 transition-colors"
            style={{ borderColor: "var(--color-border)" }}
          >
            {t.cta_today}
          </Link>
        </div>
      </header>

      {/* ── Quick start ──────────────────────────────────────────── */}
      <section className="space-y-4">
        <h2 className="text-lg font-medium">{t.quick_start}</h2>
        <ol className="space-y-3">
          {QUICK_STEPS.map((s) => (
            <li
              key={s.n}
              className="flex items-start gap-4 border rounded-md p-4"
              style={{
                background: "var(--color-bg-surface)",
                borderColor: "var(--color-border)",
              }}
            >
              <span
                className="font-mono text-xs h-7 w-7 inline-flex items-center justify-center rounded-md flex-none"
                style={{ background: "var(--color-bg-elevated)" }}
              >
                {s.n}
              </span>
              <span className="text-sm leading-relaxed">{lang === "en" ? s.en : s.zh}</span>
            </li>
          ))}
        </ol>
      </section>

      {/* ── What is VIX? ─────────────────────────────────────────── */}
      <section className="space-y-4">
        <h2 className="text-lg font-medium">{t.what_is_vix}</h2>
        <p className="text-sm leading-relaxed text-[color:var(--color-muted)]">{t.vix_intro}</p>
      </section>

      {/* ── Tier ramp (visual) ───────────────────────────────────── */}
      <section className="space-y-4">
        <h2 className="text-lg font-medium">{t.framework}</h2>
        <p className="text-sm leading-relaxed text-[color:var(--color-muted)]">
          {t.framework_caption}
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {TIERS.map((tier) => (
            <div
              key={tier.index}
              data-tier={tier.index}
              className="border rounded-md p-4 space-y-2"
              style={{
                background: "var(--color-bg-surface)",
                borderColor: TIER_COLORS[tier.index],
                borderLeftWidth: "3px",
              }}
            >
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-xs tracking-wider" style={{ color: TIER_COLORS[tier.index] }}>
                  TIER {tier.index}
                </span>
                <span className="font-mono text-xs text-[color:var(--color-muted)]">
                  VIX {tier.vix}
                </span>
              </div>
              <div className="text-base font-medium">
                {lang === "en" ? `${tier.action.en} · ${tier.action.zh}` : `${tier.action.zh} · ${tier.action.en}`}
              </div>
              <div className="flex gap-4 text-xs font-mono text-[color:var(--color-muted)]">
                <span>cash {tier.cash}</span>
                <span>buy {tier.buy}</span>
              </div>
              <p className="text-sm leading-snug">{lang === "en" ? tier.meaning.en : tier.meaning.zh}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Rules ─────────────────────────────────────────────────── */}
      <section className="space-y-4">
        <h2 className="text-lg font-medium">{t.rules}</h2>
        <div className="space-y-3">
          {RULES.map((r) => (
            <div
              key={r.n}
              className="border rounded-md p-5"
              style={{
                background: "var(--color-bg-surface)",
                borderColor: "var(--color-border)",
              }}
            >
              <div className="flex items-baseline gap-3 mb-2">
                <span className="font-mono text-xs text-[color:var(--color-muted)]">RULE {r.n}</span>
                <h3 className="text-base font-medium">{lang === "en" ? r.title.en : r.title.zh}</h3>
              </div>
              <p className="text-sm leading-relaxed text-[color:var(--color-muted)]">
                {lang === "en" ? r.body.en : r.body.zh}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How to read each section ─────────────────────────────── */}
      <section className="space-y-4">
        <h2 className="text-lg font-medium">{t.how_to_read}</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {SECTIONS.map((s) => (
            <div
              key={s.emoji}
              className="border rounded-md p-4 space-y-2"
              style={{
                background: "var(--color-bg-surface)",
                borderColor: "var(--color-border)",
              }}
            >
              <div className="flex items-center gap-2">
                <span className="text-xl">{s.emoji}</span>
                <span className="font-medium text-sm">{lang === "en" ? s.title.en : s.title.zh}</span>
              </div>
              <div className="text-xs italic text-[color:var(--color-muted)]">
                {lang === "en" ? `"${s.question.en}"` : `「${s.question.zh}」`}
              </div>
              <p className="text-sm leading-snug">{lang === "en" ? s.body.en : s.body.zh}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── What it's NOT (negative space at the bottom) ─────────── */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium">{t.what_not}</h2>
        <div className="flex flex-wrap gap-2">
          {NOTS.map((n) => (
            <span
              key={n.en}
              className="text-xs font-mono px-3 py-1.5 rounded-md border"
              style={{
                background: "var(--color-bg-surface)",
                borderColor: "var(--color-border)",
                color: "var(--color-muted)",
              }}
            >
              ❌ {lang === "en" ? n.en : n.zh}
            </span>
          ))}
        </div>
      </section>

      {/* ── Footer (open source) ─────────────────────────────────── */}
      <section className="space-y-2 pt-4 text-xs text-[color:var(--color-muted)] border-t" style={{ borderColor: "var(--color-border)" }}>
        <h2 className="text-sm font-medium pt-4">{t.open_source}</h2>
        <p className="leading-relaxed">{t.open_source_body}</p>
      </section>
    </article>
  );
}
