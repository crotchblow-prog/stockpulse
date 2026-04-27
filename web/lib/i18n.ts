/**
 * Minimal custom i18n. Two locales (en + zh) is below the next-intl complexity
 * floor. URL slug is the source of truth: /v2/en/* vs /v2/zh/*. localStorage
 * persists the last choice across visits — handled in `RememberLocale`.
 */

export type Locale = "en" | "zh";

export const LOCALES: Locale[] = ["en", "zh"];

type Dict = Record<string, string>;

const en: Dict = {
  // hero
  cash_target: "Cash target",
  buy_size: "Buy size",
  vix_today: "VIX today",
  // sections
  watch_list: "🚩 Watch List",
  holdings: "💼 Holdings",
  market_snapshot: "🌐 Market Snapshot",
  vix_history: "📈 VIX (last 30 days)",
  todays_take: "📝 Today's Take",
  market_read: "Market read.",
  devils_advocate: "Devil's advocate.",
  position_calls: "Position calls",
  synthesis_unavailable: "Today's synthesis is unavailable — see the data sections below.",
  tier_action: "🎯 Tier Action",
  buy_list: "Buy list",
  sell_list: "Sell list",
  no_buys_at_tier: "(no buys at this tier)",
  universe_scanner: "📡 Universe Scanner",
  scanner_legend:
    "β normal: regime-conditional beta vs SPX in calm weeks. Crush recovery: 5-day return after VIX falls ≥30%. Spike decay: 5-day return after VIX rises ≥20%.",
  add_candidates: "🟢 Add candidates",
  watch_transition: "🟡 Watch (transition)",
  avoid_candidates: "🔴 Avoid candidates",
  scanner_th_beta_normal: "β normal",
  scanner_th_crush: "Crush recovery",
  scanner_th_decay: "Spike decay",
  scanner_th_sample: "Sample",
  scanner_th_note: "Note",
  scanner_universe_missing: "_universe data not loaded_",
  also_in_avoid: "⚠️ double-edged — smaller size, trim first on Tier ↑",
  also_in_add: "double-edged (see Add)",
  scanner_dual_legend:
    "Tickers tagged in both 🟢 Add and 🔴 Avoid are double-edged: they amplify on the way up at this Tier but historically break first when VIX rises into stress. Buy at smaller size and trim first if Tier transitions up.",
  // empty states
  no_watchworthy: "Nothing watchworthy today.",
  no_holdings: "No holdings.",
  no_report: "No report yet. The daily cron runs at 22:00 Asia/Taipei.",
  no_report_for_date: "No report for {date}.",
  no_history: "Not enough history yet — need 30 prior daily reports.",
  // table headers
  th_ticker: "Ticker",
  th_last: "Last",
  th_vs_cost: "vs cost",
  th_rsi: "RSI",
  th_vs_50dma: "vs 50DMA",
  th_vs_200dma: "vs 200DMA",
  th_vs_52w_high: "vs 52w high",
  // labels
  generated: "Generated",
  your_local: "your local",
  not_advice: "not investment advice",
  preview: "preview",
  m1_foundation: "M1 foundation",
  // sparkline
  spark_30d_high: "30d high",
  spark_30d_low: "30d low",
  spark_today: "today",
  // tier action labels (mirror holdings.json tier_strategy.<tier>.action,
  // localized so EN readers don't see Chinese in the headers).
  tier_action_0: "Rest",
  tier_action_1: "Cautious positioning",
  tier_action_2: "Watch",
  tier_action_3: "Scale in",
  tier_action_4: "Catch the panic",
  tier_action_5: "Extreme opportunity",
  // footer nav
  "footer.about": "About",
  "footer.privacy": "Privacy",
  "footer.terms": "Terms",
  "footer.contact": "Contact",
  "footer.copyright_brand": "VIX Pulse",
};

const zh: Dict = {
  cash_target: "現金目標",
  buy_size: "進場規模",
  vix_today: "今日 VIX",
  watch_list: "🚩 關注名單",
  holdings: "💼 持倉",
  market_snapshot: "🌐 市場快照",
  vix_history: "📈 VIX（最近 30 天）",
  todays_take: "📝 今日觀點",
  market_read: "市場解讀。",
  devils_advocate: "反方觀點。",
  position_calls: "持倉判斷",
  synthesis_unavailable: "今日的綜合分析尚未產出 — 請參考下方各資料區塊。",
  tier_action: "🎯 Tier 行動",
  buy_list: "買進清單",
  sell_list: "賣出清單",
  no_buys_at_tier: "（此 Tier 不買進）",
  universe_scanner: "📡 標的掃描",
  scanner_legend:
    "β normal：在平靜週期相對 SPX 的 beta。Crush recovery：VIX 下跌 ≥30% 後的五日累積報酬。Spike decay：VIX 上升 ≥20% 後的五日累積報酬。",
  add_candidates: "🟢 加碼候選",
  watch_transition: "🟡 觀察（轉換）",
  avoid_candidates: "🔴 避開候選",
  scanner_th_beta_normal: "β normal",
  scanner_th_crush: "Crush recovery",
  scanner_th_decay: "Spike decay",
  scanner_th_sample: "樣本",
  scanner_th_note: "備註",
  scanner_universe_missing: "_標的池資料未載入_",
  also_in_avoid: "⚠️ 雙面刃 — 規模放小，Tier 上升時優先減碼",
  also_in_add: "雙面刃（見 Add 列）",
  scanner_dual_legend:
    "同時出現在 🟢 加碼候選與 🔴 避開候選的標的屬「雙面刃」：在當前 Tier 隨大盤上漲放大報酬，但歷史上 VIX 進入壓力區時也最先重挫。建議規模放小；若 Tier 向上轉換，優先減碼此類標的。",
  no_watchworthy: "今天沒有需要關注的部位。",
  no_holdings: "目前無持倉。",
  no_report: "尚無報告。每日 cron 將於 22:00 Asia/Taipei 產出。",
  no_report_for_date: "找不到 {date} 的報告。",
  no_history: "歷史資料不足 — 需要 30 個交易日的報告。",
  th_ticker: "標的",
  th_last: "現價",
  th_vs_cost: "vs 成本",
  th_rsi: "RSI",
  th_vs_50dma: "vs 50DMA",
  th_vs_200dma: "vs 200DMA",
  th_vs_52w_high: "vs 52週高",
  generated: "報告日期",
  your_local: "你的時區",
  not_advice: "非投資建議",
  preview: "預覽版",
  m1_foundation: "M1 基礎",
  spark_30d_high: "30 天高",
  spark_30d_low: "30 天低",
  spark_today: "今日",
  tier_action_0: "休兵",
  tier_action_1: "警戒佈局",
  tier_action_2: "觀察",
  tier_action_3: "分批進場",
  tier_action_4: "恐慌承接",
  tier_action_5: "極端機會",
  "footer.about": "關於我們",
  "footer.privacy": "隱私權政策",
  "footer.terms": "服務條款",
  "footer.contact": "聯絡我們",
  "footer.copyright_brand": "VIX Pulse",
};

const dicts: Record<Locale, Dict> = { en, zh };

export function t(locale: Locale, key: string, vars?: Record<string, string | number>): string {
  let s = dicts[locale]?.[key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      s = s.replace(`{${k}}`, String(v));
    }
  }
  return s;
}

export function isLocale(s: string): s is Locale {
  return s === "en" || s === "zh";
}
