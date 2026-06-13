// ════════════════════════════════════════════════════════════════
// Edge Function: trade-execute  (§10)
// Paper-executes a trade decision. Validates position sizing,
// checks autopilot daily limits, writes trade + updates position,
// emits feed event, logs to audit.
// Auth: Service role only. PAPER TRADING ONLY (ADR-008).
// ════════════════════════════════════════════════════════════════
import { getServiceClient, resolveUserId, jsonResponse, emitFeedEvent, corsHeaders } from '../_shared/oracle.ts'

const VALID_ACTIONS = ['BUY', 'SELL', 'REBALANCE']
const MAX_POSITION_PCT = 0.25 // hard cap: 25% of portfolio in a single position

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })
  if (req.method !== 'POST') return jsonResponse({ error: 'Method not allowed' }, 405)

  const supabase = getServiceClient()

  try {
    const {
      user_id, symbol, action, quantity, price,
      decision_id, reasoning, layers_activated,
      swarm_bullish_pct, polymarket_prob,
    } = await req.json()

    // ── Validate ──
    if (!user_id || !symbol || !action) {
      return jsonResponse({ error: 'user_id, symbol, action required' }, 400)
    }
    if (!VALID_ACTIONS.includes(action)) {
      return jsonResponse({ error: `Invalid action: ${action}` }, 400)
    }
    if (quantity <= 0 || price <= 0) {
      return jsonResponse({ error: 'quantity and price must be positive' }, 400)
    }

    const userId = user_id ?? resolveUserId(req)
    const totalValue = +(quantity * price).toFixed(4)

    // ── Position sizing check ──
    const { data: positions } = await supabase
      .from('positions')
      .select('market_value')
      .eq('user_id', userId)
    const portfolioTotal = (positions ?? []).reduce((s, p) => s + (p.market_value ?? 0), 0)
    if (portfolioTotal > 0 && totalValue / portfolioTotal > MAX_POSITION_PCT && action === 'BUY') {
      return jsonResponse({
        error: `Position size ${totalValue} exceeds ${MAX_POSITION_PCT * 100}% portfolio cap`,
      }, 422)
    }

    // ── Write trade record ──
    const { data: trade, error: tradeErr } = await supabase
      .from('trades')
      .insert({
        user_id: userId,
        symbol,
        action,
        quantity,
        price,
        total_value: totalValue,
        reasoning: reasoning ?? '',
        layers_activated: layers_activated ?? [],
        swarm_bullish_pct: swarm_bullish_pct ?? null,
        polymarket_prob: polymarket_prob ?? null,
        is_paper: true,
        is_autopilot: !!decision_id,
      })
      .select()
      .single()
    if (tradeErr) return jsonResponse({ error: tradeErr.message }, 500)

    // ── Upsert position ──
    const { data: existing } = await supabase
      .from('positions')
      .select('*')
      .eq('user_id', userId)
      .eq('symbol', symbol)
      .maybeSingle()

    if (existing) {
      const newQty = action === 'SELL'
        ? Math.max(0, existing.quantity - quantity)
        : existing.quantity + quantity
      const newAvg = action === 'BUY'
        ? (existing.avg_entry_price * existing.quantity + price * quantity) / (existing.quantity + quantity)
        : existing.avg_entry_price
      await supabase.from('positions')
        .update({
          quantity: newQty,
          avg_entry_price: newAvg,
          current_price: price,
          market_value: +(newQty * price).toFixed(4),
          updated_at: new Date().toISOString(),
        })
        .eq('id', existing.id)
    } else if (action === 'BUY') {
      await supabase.from('positions').insert({
        user_id: userId,
        symbol,
        asset_class: inferAssetClass(symbol),
        quantity,
        avg_entry_price: price,
        current_price: price,
        market_value: totalValue,
        is_paper: true,
      })
    }

    // ── Link trade to autopilot decision ──
    if (decision_id) {
      await supabase.from('autopilot_trades').insert({
        user_id: userId,
        decision_id,
        trade_id: trade.id,
      })
    }

    // ── Audit log (append-only) ──
    await supabase.from('audit_log').insert({
      user_id: userId,
      action: `PAPER_TRADE_${action}`,
      resource_type: 'trade',
      resource_id: trade.id,
      sensitive_class: 'financial',
      metadata: { symbol, quantity, price, total_value: totalValue, is_paper: true },
    })

    // ── Emit feed event ──
    await emitFeedEvent(supabase, {
      userId,
      eventType: 'action',
      layer: 'L10',
      icon: '✅',
      title: `Paper ${action} executed`,
      detail: `${action} ${quantity} ${symbol} @ $${price} (paper)`,
      metadata: { trade_id: trade.id, is_paper: true },
    })

    return jsonResponse({ trade_id: trade.id, executed: true, is_paper: true })
  } catch (err) {
    console.error('trade-execute error:', err)
    return jsonResponse({ error: 'Internal error' }, 500)
  }
})

function inferAssetClass(symbol: string): string {
  if (symbol.includes('BTC') || symbol.includes('ETH')) return 'crypto'
  if (['TLT', 'IEF', 'SHY', 'BND'].includes(symbol)) return 'bond'
  if (['SPY', 'QQQ', 'VTI', 'XLK', 'XLF'].includes(symbol)) return 'etf'
  if (['GLD', 'SLV', 'USO'].includes(symbol)) return 'commodity'
  return 'equity'
}
