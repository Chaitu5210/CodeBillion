# strategies.py
def _strategy_63(time_key, state, position, price, prev_close, prev_day):
    """IMPROVED 24: Prev High Bounce + Better Target"""
    if prev_day is None:
        return None, None, None
    
    prev_high = prev_day.get("high", prev_close)
    prev_close_val = prev_day.get("close", prev_close)
    
    if time_key == "09-20-00" and position is None and "open" in state:
        today_open = state["open"]
        price_920 = price
        
        # Price near prev high with strong momentum
        touches_prev_high = abs(price_920 - prev_high) / prev_high < 0.004  # Slightly wider
        momentum = price_920 > today_open * 1.0015
        
        if touches_prev_high and momentum:
            sl = prev_high * 0.9965  # 0.35% stop
            target = price_920 * 1.025  # 2.5% target
            return "BUY", sl, target
    
    if position:
        sl = position.get("sl")
        target = position.get("target")
        if sl and price <= sl:
            return "SELL", None, None
        if target and price >= target:
            return "SELL", None, None
    
    return None, None, None


def strategy_logic(
    time_key,
    hour,
    minute,
    second,
    stock,
    price,
    position,
    market_state,
    can_trade,
    prev_day=None,
    strategy_id=1
):
    """
    Multiple strategies to test
    strategy_id: 1-10 for different strategy variations
    """

    # ================= SAFETY =================
    if prev_day is None:
        return None, None, None

    prev_close = prev_day["close"]

    # ================= STORE OPEN & 9:20 =================
    state = market_state.setdefault(stock, {})

    # capture today open
    if time_key == "09-15-00":
        state["open"] = price

    # capture 9:20 price
    if time_key == "09-20-00":
        state["price_920"] = price

    # ================= STRATEGY SELECTION =================
    
    # Strategy 1: Original - Conservative Gap + Momentum
    elif strategy_id == 63:
        return _strategy_63(time_key, state, position, price, prev_close, prev_day)
    