"""
Strategy Test Bed - Strategy 9 Only
Gap + Momentum at 9:20 Strategy
"""


def _strategy_9(time_key, state, position, price, prev_close, can_trade):
    """
    Strategy 9: Gap + Momentum at 9:20
    
    Entry Logic:
    - At 9:20 AM, check if price touched previous high (within 0.2%)
    - AND price shows momentum above today's open (0.15% higher)
    - Entry at market
    
    Exit Logic:
    - SL: 0.35% below entry
    - Target: 1.5% above entry
    """
    if not can_trade:
        return None, None, None

    # Capture today's open at 9:15
    if time_key == "09-15-00":
        state["open"] = price
        return None, None, None

    # Entry signal only at 9:20 and when no position
    if time_key != "09-20-00" or position is not None:
        return None, None, None

    today_open = state.get("open")
    if today_open is None:
        return None, None, None

    # Use prev_close as a proxy for prev_high (conservative approach)
    prev_high = prev_close * 1.005  # Assume previous day had a small gap
    
    touches_high = price > prev_high * 0.998
    momentum = price > today_open * 1.0015

    if touches_high and momentum:
        sl = price * 0.9965  # 0.35% below entry
        target = price * 1.015  # 1.5% above entry
        return "BUY", sl, target

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
    strategy_id=9
):
    """
    Strategy Logic Router
    Only Strategy 9 is active
    
    Parameters:
    -----------
    time_key : str
        Time in HH-MM-SS format (e.g., "09-15-00")
    hour : int
        Hour (0-23)
    minute : int
        Minute (0-59)
    second : int
        Second (0-59)
    stock : str
        Stock ticker symbol
    price : float
        Current price
    position : dict or None
        Current position if open
    market_state : dict
        Shared market state for tracking
    can_trade : bool
        Whether trading is allowed
    prev_day : dict or None
        Previous day OHLCV data
    strategy_id : int
        Strategy ID (only 9 is active)
    
    Returns:
    --------
    tuple : (signal, stop_loss, target)
        - signal: "BUY", "SELL", or None
        - stop_loss: Stop loss price or None
        - target: Target price or None
    """
    
    # Safety check
    if prev_day is None:
        return None, None, None
    
    prev_close = prev_day["close"]
    
    # Get or create state for this stock
    state = market_state.setdefault(stock, {})
    
    # Capture today's opening price at 9:15
    if time_key == "09-15-00":
        state["open"] = price
    
    # Capture 9:20 price for reference
    if time_key == "09-20-00":
        state["price_920"] = price
    
    # Only Strategy 9 is active
    if strategy_id == 9:
        return _strategy_9(time_key, state, position, price, prev_close, can_trade)
    
    # Default: no signal
    return None, None, None
