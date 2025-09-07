import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

trail_distance = 0.25 # trail by 25% of tp pips (so if tp is 50 pip, then trail will be 12.5 pips)

def calculate_atr(df, period=14):
    """Calculate Average True Range using DataFrame"""
    try:
        df = df.copy()
        df["high_low"] = df["high"] - df["low"]
        df["high_close_prev"] = abs(df["high"] - df["close"].shift(1))
        df["low_close_prev"] = abs(df["low"] - df["close"].shift(1))
        df["tr"] = df[["high_low", "high_close_prev", "low_close_prev"]].max(axis=1)
        atr_series = df["tr"].rolling(window=period).mean()
        
        latest_atr = atr_series.iloc[-1]
        return Decimal(str(latest_atr))
    except Exception as e:
        print(f"Error calculating ATR: {e}")
        return Decimal('0')

def calculate_rsi(df, period=14):
    df = df.copy()
    delta = df['close'].diff().apply(lambda x: Decimal(str(x)))

    gain = delta.where(delta > 0, Decimal('0'))
    loss = -delta.where(delta < 0, Decimal('0'))

    avg_gain = [Decimal('0')] * len(df)
    avg_loss = [Decimal('0')] * len(df)

    # Initialize first average
    avg_gain[period-1] = sum(gain.iloc[:period]) / Decimal(str(period))
    avg_loss[period-1] = sum(loss.iloc[:period]) / Decimal(str(period))

    # Wilder's smoothing
    for i in range(period, len(df)):
        avg_gain[i] = (avg_gain[i-1] * (Decimal(str(period-1))) + gain.iloc[i]) / Decimal(str(period))
        avg_loss[i] = (avg_loss[i-1] * (Decimal(str(period-1))) + loss.iloc[i]) / Decimal(str(period))

    rs = [avg_gain[i]/avg_loss[i] if avg_loss[i] != 0 else Decimal('0') for i in range(len(df))]
    rsi = [Decimal('100') - (Decimal('100') / (Decimal('1') + rs[i])) if avg_loss[i] != 0 else Decimal('100') for i in range(len(df))]

    return rsi[-1]

def format_price(price, decimal_places=5):
    """Format price to specified decimal places for Oanda compatibility"""
    if decimal_places > 5:
        decimal_places = 5  # Oanda limit
    
    format_str = '0.' + '0' * decimal_places
    return Decimal(str(price)).quantize(Decimal(format_str), rounding=ROUND_HALF_UP)

def get_trailing_stop_distance_if_triggered(candle, trade, trail_start, trail_distance):
    """
    Check if price has reached 50% of TP and return 25% TP as trailing stop distance.

    Parameters:
        candle (dict): OHLC candle data with keys: open, high, low, close
        entry_price (float): Entry price of the trade
        take_profit (float): Take profit level
        action (str): 'buy' or 'sell'

    Returns:
        float: trailing stop distance (25% of TP), if trigger condition met
        None: if trigger condition not met
    """
    entry_price = trade['entry_price']
    take_profit = trade["original_take_profit"]
    action = trade["action"]
    tp_distance = abs(take_profit - entry_price)
    trail_distance = round(tp_distance * trail_distance, 5)  # Use 5 decimals for FX precision

    # 50% TP trigger level
    if action == 'buy':
        trigger_price = entry_price + trail_start * tp_distance
        if candle['high'] >= trigger_price:
            return trail_distance

    elif action == 'sell':
        trigger_price = entry_price - trail_start * tp_distance
        if candle['low'] <= trigger_price:
            return trail_distance

    return None


def run(candles, instrument="EUR_USD"):
    """
    Main trading strategy function with integrated risk management
    
    Args:
        candles: List of OHLC candle dicts
        instrument: Trading pair (default: EUR_USD)
    """
    # Input validation
    if not candles or len(candles) < 201:  # Need 200 + 1 for EMA_200
        print(len(candles))
        return {"instrument": instrument, "action": "hold", "reason": "insufficient_data"}

    try:
        df = pd.DataFrame(candles)
        
        # Ensure we have required columns
        required_columns = ['high', 'low', 'close', 'open']
        if not all(col in df.columns for col in required_columns):
            print(f"Missing required columns. Found: {df.columns.tolist()}")
            return {"instrument": instrument, "action": "hold", "reason": "invalid_data"}

        # Convert to Decimal for precision
        for col in required_columns:
            df[col] = df[col].apply(lambda x: Decimal(str(x)))

        # Calculate EMAs using Decimal arithmetic
        df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()
        df["ema_9"] = df["close"].ewm(span=9, adjust=False).mean()
        df["ema_25"] = df["close"].ewm(span=25, adjust=False).mean()

        # Calculate indicators
        atr = calculate_atr(df, period=14)
        rsi = calculate_rsi(df, period=14)

        # **FIXED INDEXING LOGIC**: Use consistent lookback periods
        # We need at least 3 candles for signal confirmation
        if len(df) < 3:
            print("Need at least 3 candles for signal detection")
            return {"instrument": instrument, "action": "hold", "reason": "insufficient_signal_data"}

        # Standardized indexing:
        # -3: Two candles ago (for crossover detection)
        # -2: Previous candle (for confirmation) 
        # -1: Current/latest candle (for entry)
        candle_2_ago = df.iloc[-3]    # N-2
        candle_1_ago = df.iloc[-2]    # N-1 (confirmation candle)
        current_candle = df.iloc[-1]  # N (entry candle)

        # --- BUY condition ---
        buy_crossover = (candle_2_ago["ema_9"] < candle_2_ago["ema_25"] and 
                        candle_1_ago["ema_9"] > candle_1_ago["ema_25"])
        buy_trend_filter = candle_1_ago["close"] > candle_1_ago["ema_200"]
        buy_rsi_filter = rsi <= Decimal('70')

        if buy_crossover and buy_trend_filter and buy_rsi_filter:
            entry_price = current_candle["open"]
            sl = candle_1_ago["close"] - (Decimal('1.5') * atr)
            tp = candle_1_ago["close"] + (Decimal('3') * atr)
            
            # Format for Oanda (max 5 decimal places)
            entry_formatted = format_price(entry_price)
            sl_formatted = format_price(sl)
            tp_formatted = format_price(tp)
            
            return {
                "instrument": instrument,
                "action": "buy",
                "entry_price": float(entry_formatted),
                "stop_loss": float(sl_formatted),
                "take_profit": float(tp_formatted),
                "rsi": float(rsi),
                "atr": float(atr),
                "ema_9": float(candle_1_ago["ema_9"]),
                "ema_25": float(candle_1_ago["ema_25"]),
                "ema_200": float(candle_1_ago["ema_200"]),
                "reason": "ema_crossover_buy"
            }

        # --- SELL condition ---
        sell_crossover = (candle_2_ago["ema_9"] > candle_2_ago["ema_25"] and 
                         candle_1_ago["ema_9"] < candle_1_ago["ema_25"])
        sell_trend_filter = candle_1_ago["close"] < candle_1_ago["ema_200"]
        sell_rsi_filter = rsi >= Decimal('30')

        if sell_crossover and sell_trend_filter and sell_rsi_filter:
            
            entry_price = current_candle["open"]
            sl = candle_1_ago["close"] + (Decimal('1.5') * atr)
            tp = candle_1_ago["close"] - (Decimal('3') * atr)
            
            # Format for Oanda (max 5 decimal places)
            entry_formatted = format_price(entry_price)
            sl_formatted = format_price(sl)
            tp_formatted = format_price(tp)
            
            return {
                "instrument": instrument,
                "action": "sell",
                "entry_price": float(entry_formatted),
                "stop_loss": float(sl_formatted),
                "take_profit": float(tp_formatted),
                "rsi": float(rsi),
                "atr": float(atr),
                "ema_9": float(candle_1_ago["ema_9"]),
                "ema_25": float(candle_1_ago["ema_25"]),
                "ema_200": float(candle_1_ago["ema_200"]),
                "reason": "ema_crossover_sell"
            }
        return {
            "instrument": instrument, 
            "action": "hold",
            "rsi": float(rsi),
            "atr": float(atr),
            "ema_9": float(candle_1_ago["ema_9"]),
            "ema_25": float(candle_1_ago["ema_25"]),
            "ema_200": float(candle_1_ago["ema_200"]),
            "reason": "no_signal"
        }

    except Exception as e:
        print(f"Error in strategy execution: {e}")
        return {"instrument": instrument, "action": "hold", "reason": "error", "error": str(e)}

