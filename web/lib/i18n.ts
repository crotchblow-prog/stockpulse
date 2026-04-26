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
};

const zh: Dict = {
  cash_target: "現金目標",
  buy_size: "進場規模",
  vix_today: "今日 VIX",
  watch_list: "🚩 關注名單",
  holdings: "💼 持倉",
  market_snapshot: "🌐 市場快照",
  vix_history: "📈 VIX（最近 30 天）",
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
