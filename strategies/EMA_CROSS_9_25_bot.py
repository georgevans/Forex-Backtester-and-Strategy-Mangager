import pandas as pd

def calculate_atr(candles, period=14):
    df = pd.DataFrame(candles)
    df["high-low"] = df["high"] - df["low"]
    df["high-close_prev"] = abs(df["high"] - df["close"].shift(1))
    df["low-close_prev"] = abs(df["low"] - df["close"].shift(1))
    df["tr"] = df[["high-low", "high-close_prev", "low-close_prev"]].max(axis=1)
    atr = df["tr"].rolling(window=period).mean()
    return atr.iloc[-1] 

def run(candles, instrument="EUR_USD"):
    import pandas as pd

    df = pd.DataFrame(candles)
    if len(df) < 26:
        return {"instrument": instrument, "action": "hold"}

    df["ema_9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["ema_25"] = df["close"].ewm(span=25, adjust=False).mean()

    atr = calculate_atr(candles, period=14)

    prev = df.iloc[-2]
    last = df.iloc[-1]

    if prev["ema_9"] < prev["ema_25"] and last["ema_9"] > last["ema_25"]:
        # Buy signal
        sl = last["close"] - 1.5 * atr
        tp = last["close"] + 3 * atr
        return {
            "instrument": instrument,
            "action": "buy",
            "stop_loss": float(sl),
            "take_profit": float(tp),
            'risk': 300
        }

    elif prev["ema_9"] > prev["ema_25"] and last["ema_9"] < last["ema_25"]:
        # Sell signal
        sl = last["close"] + 1.5 * atr
        tp = last["close"] - 3 * atr
        return {
            "instrument": instrument,
            "action": "sell",
            "stop_loss": float(sl),
            "take_profit": float(tp),
            'risk': 300
        }

    else:
        return {"instrument": instrument, "action": "hold", "risk_gbp": 300}