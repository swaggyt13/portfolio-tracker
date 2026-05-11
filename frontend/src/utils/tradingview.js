// Build TradingView chart URLs from a symbol and an optional exchange.
// US stocks default to NASDAQ when we lack a real exchange. The user can
// override per symbol via the metadata endpoint.

const US_PRIMARY = new Set(['NASDAQ', 'NYSE', 'AMEX', 'ARCA', 'BATS'])

export function tradingViewUrl(symbol, exchange, exchangeOverride) {
  if (!symbol) return null

  const sym = String(symbol).trim().toUpperCase()
  let resolvedExchange = (exchangeOverride || exchange || '').toString().toUpperCase()

  // Map common IBKR exchange names to TradingView equivalents.
  if (resolvedExchange === 'ISLAND' || resolvedExchange === 'NMS' || resolvedExchange === 'PINK') {
    resolvedExchange = 'NASDAQ'
  }
  if (!US_PRIMARY.has(resolvedExchange)) {
    // Fall back to NASDAQ. TradingView resolves most US tickers regardless,
    // and an override can be applied per symbol via the notes panel.
    resolvedExchange = 'NASDAQ'
  }

  return `https://www.tradingview.com/chart/?symbol=${resolvedExchange}:${sym}`
}

export function openTradingView(symbol, exchange, exchangeOverride) {
  const url = tradingViewUrl(symbol, exchange, exchangeOverride)
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
}
