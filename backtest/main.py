import pandas as pd
import sys
import csv
import strategies.EMA_CROSS_9_25_bot as strat
import matplotlib.pyplot as plt


# --- Configuration ---
starting_balance = 850
risk_percent = 0.01       # 1% risk per trade
candle_counter = 2016     # Number of candles to backtest
debug = False

if len(sys.argv) == 2:
    candle_counter = int(sys.argv[1])

# --- Globals ---
trades = []
completed_trades = []
account_balance = starting_balance
trades_made = 0
trades_closed = 0
trades_unfinished = 0

stategy_assesment_metrics = [] # {(open price, close price, highest price, lowest price, if BE reached)}

# --- Functions ---
def calculate_units(account_balance, risk_percent, entry_price, stop_loss, instrument):
    """Calculate position size based on risk percent and SL distance."""
    risk_usd = account_balance * risk_percent
    if instrument[-3:] == "JPY":
        pip_size = 0.01
        pip_multiplier = 100
    else:
        pip_size = 0.0001
        pip_multiplier = 10000

    sl_distance = abs(entry_price - stop_loss) * pip_multiplier
    if sl_distance == 0:
        return 0

    units = risk_usd / (sl_distance * pip_size)
    return units

# --- Check instrument availability ---
def check_instrument_availability(instrument='EUR_USD'):
    """Return True if no open position exists on this instrument."""
    return not any(tr['instrument'] == instrument and tr['close_price'] is None for tr in trades)


# --- Execute trade ---
def execute_trade(signal, entry_price, date, time):
    """Open a new trade using strategy signal and risk-based units."""
    global trades, trades_made
    units = calculate_units(account_balance, risk_percent, entry_price, signal['stop_loss'], signal['instrument'])
    trade = {
        "instrument": signal['instrument'],
        "action": signal['action'],
        "entry_price": entry_price,
        "stop_loss": signal['stop_loss'],
        "take_profit": signal['take_profit'],
        "units": units,
        "open_price": entry_price,
        "highest_price": entry_price,
        "lowest_price": entry_price,
        "close_price": None,
        "be_reached": False,
        "win": None,
        "profit": None,
        "profit_pips": None,
        "profit_usd": None
    }
    trades.append(trade)
    trades_made += 1
    if debug:
        print(f"Opened trade: {trade['action']} at {entry_price}, Units: {units}")
    stategy_assesment_metrics.append({
        "entry_price": entry_price,
        "stop_loss": signal['stop_loss'],
        "take_profit": signal['take_profit'],
        "units": units,
    })
    return trade


# --- Update positions --- when new canadle arrives
def update_positions(candle):
    """Update all open positions based on current candle high/low."""
    global trades_closed, account_balance

    for tr in trades:
        if tr['close_price'] is not None:
            continue  # already closed

        action = tr['action']

        # Update excursions
        tr['highest_price'] = max(tr.get('highest_price', tr['entry_price']), candle['high'])
        tr['lowest_price'] = min(tr.get('lowest_price', tr['entry_price']), candle['low'])

        # Check if break-even was reached (1R move in favor)
        if not tr.get('be_reached', False):
            risk_distance = abs(tr['entry_price'] - tr['stop_loss'])
            if action == 'buy' and (candle['high'] - tr['entry_price'] >= risk_distance):
                tr['be_reached'] = True
            elif action == 'sell' and (tr['entry_price'] - candle['low'] >= risk_distance):
                tr['be_reached'] = True

        # --- NEW: Check if trade needs modification (trailing stop, etc.) ---
        new_stop = strat.check_modify(
            price=candle['close'],                  # current price to evaluate trailing
            entry_price=tr['entry_price'],          # break-even / entry level
            take_profit=tr['take_profit'],          # original TP
            breakeven_reached=tr.get('be_reached', False),  # whether BE has been reached
            trail_start=0.7,                        # optional, default threshold
            trail_distance=0.25                      # optional, default trail distance
        )

        if new_stop:
            print(new_stop)

        # Trade exit logic
        hit_tp = hit_sl = False
        if action == 'buy':
            hit_tp = candle['high'] >= tr['take_profit']
            hit_sl = candle['low'] <= tr['stop_loss']
        else:  # sell
            hit_tp = candle['low'] <= tr['take_profit']
            hit_sl = candle['high'] >= tr['stop_loss']

        # Both hit: conservative (assume worst case)
        if hit_tp and hit_sl:
            price = tr['stop_loss']
            win = False
        elif hit_tp:
            price = tr['take_profit']
            win = True
        elif hit_sl:
            price = tr['stop_loss']
            win = False
        else:
            continue  # neither hit this candle

        # Close trade
        tr['close_price'] = price
        tr['win'] = win

        # Profit calculations
        if action == 'buy':
            tr['profit'] = round(price - tr['entry_price'], 6)
        else:
            tr['profit'] = round(tr['entry_price'] - price, 6)

        tr['profit_pips'] = round(tr['profit'] * 10000, 1)
        tr['profit_usd'] = round(tr['profit'] * tr['units'], 2)
        account_balance += tr['profit_usd']

        completed_trades.append(tr)
        trades_closed += 1



def remove_unfinished(trades):
    """Return list of trades that were closed."""
    global trades_unfinished
    cleaned = []
    for tr in trades:
        if tr['close_price'] == 0:
            trades_unfinished += 1
        else:
            cleaned.append(tr)
    return cleaned

def calc_total_profit(trade_list):
    total_usd = sum(t['profit_usd'] for t in trade_list)
    total_pips = sum(t['profit_pips'] for t in trade_list)
    return round(total_usd, 2), round(total_pips, 2)

def calculate_metrics(trade_list):
    """Calculate standard trade metrics."""
    if not trade_list:
        return {}
    wins = [t for t in trade_list if t['win']]
    losses = [t for t in trade_list if not t['win']]
    win_rate = len(wins) / len(trade_list) * 100
    avg_win = sum(t['profit_usd'] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t['profit_usd'] for t in losses) / len(losses) if losses else 0
    profit_factor = (sum(t['profit_usd'] for t in wins) / abs(sum(t['profit_usd'] for t in losses))
                     if losses and sum(t['profit_usd'] for t in losses) != 0 else float('inf'))
    return {
        'total_trades': len(trade_list),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(win_rate, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(profit_factor, 2)
    }

def export_trades_to_csv(filename="trades_output.csv", include_open=False):
    """Export all trades to a CSV file for analysis."""
    fieldnames = [
        "instrument", "action", "open_price", "entry_price",
        "stop_loss", "take_profit", "highest_price", "lowest_price",
        "be_reached", "close_price", "profit", "profit_pips",
        "profit_usd", "win", "units"
    ]

    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        # Completed trades first
        for tr in completed_trades:
            writer.writerow(tr)

        # Optionally include open trades still running
        if include_open:
            for tr in trades:
                if tr['close_price'] is None:
                    writer.writerow(tr)

    print(f"Trades exported to {filename}")

# --- Load data ---
historical_candles = pd.read_csv('EURUSD5.csv')
historical_candles = historical_candles.tail(candle_counter).reset_index(drop=True)
print(f"Loaded {len(historical_candles)} most recent candles for backtest.")

# --- Backtest loop ---
for idx, row in historical_candles.iterrows():
    candle = {
        "open": float(row['open']),
        "high": float(row['high']),
        "low": float(row['low']),
        "close": float(row['close'])
    }

    # Update open positions first
    update_positions(candle)

    # Need enough candles for strategy
    if idx < 200:
        continue

    # Strategy signal
    signal = strat.run(historical_candles.iloc[:idx+1].to_dict('records'), instrument="EUR_USD")

    # Execute trade if allowed
    if signal['action'] != 'hold' and check_instrument_availability():
        if idx + 1 < len(historical_candles):
            entry_price = float(historical_candles.iloc[idx + 1]['open'])
        else:
            entry_price = candle['close']
        execute_trade(signal, entry_price, row['date'], row['time'])

# Force close remaining trades at last candle close
for tr in trades:
    if tr['close_price'] == 0:
        tr['close_price'] = historical_candles.iloc[-1]['close']
        if tr['action'] == 'buy':
            tr['profit'] = tr['close_price'] - tr['entry_price']
        else:
            tr['profit'] = tr['entry_price'] - tr['close_price']
        tr['profit_pips'] = round(tr['profit'] * 10000, 1)
        tr['profit_usd'] = round(tr['profit'] * tr['units'], 2)
        tr['win'] = tr['profit'] > 0
        account_balance += tr['profit_usd']
        completed_trades.append(tr)

trades.clear()

# --- Results ---
clean_trades = remove_unfinished(completed_trades)
total_usd, total_pips = calc_total_profit(clean_trades)
metrics = calculate_metrics(clean_trades)
percentage_PL = (total_usd / starting_balance) * 100


print("\n" + "="*40)
print("BACKTEST RESULTS")
print("="*40)
print(f"Initial balance: ${starting_balance}")
print(f"Final balance: ${round(account_balance,2)}")
print(f"Total P/L: ${total_usd} ({total_pips} pips)")
print(f"Percentage return: {percentage_PL:.2f}%")
print(f"Risk per trade: {risk_percent*100}%")

if metrics:
    print("\nTrade Statistics:")
    print(f"Total trades: {metrics['total_trades']}")
    print(f"Wins: {metrics['wins']} | Losses: {metrics['losses']}")
    print(f"Win rate: {metrics['win_rate']}%")
    print(f"Average win: ${metrics['avg_win']} | Average loss: ${metrics['avg_loss']}")
    print(f"Profit factor: {metrics['profit_factor']}")
print("="*40)

equity_curve = [starting_balance]
balance = starting_balance
for t in completed_trades:
    balance += t['profit_usd']
    equity_curve.append(balance)

drawdowns = []
peak = starting_balance
balance = starting_balance
for t in completed_trades:
    balance += t['profit_usd']
    peak = max(peak, balance)
    drawdowns.append(peak - balance)

profits_usd = [t['profit_usd'] for t in completed_trades]

cum_pips = [0]
total = 0
for t in completed_trades:
    total += t['profit_pips']
    cum_pips.append(total)

export_trades_to_csv("trades_made.csv")

plt.figure(figsize=(12,6))
plt.plot(equity_curve, label="Equity Curve")
plt.xlabel("Trades")
plt.ylabel("Account Balance ($)")
plt.title("Backtest Equity Curve")
plt.legend()
plt.grid(True)
plt.show()

plt.figure(figsize=(12,4))
plt.plot(drawdowns, color='red')
plt.title("Drawdown over Time")
plt.xlabel("Trades")
plt.ylabel("Drawdown ($)")
plt.grid(True)
plt.show()

plt.hist(profits_usd, bins=30, edgecolor='black')
plt.title("Distribution of Trade Profits")
plt.xlabel("Profit (USD)")
plt.ylabel("Frequency")
plt.show()

plt.plot(cum_pips)
plt.title("Cumulative Pips Over Time")
plt.show()