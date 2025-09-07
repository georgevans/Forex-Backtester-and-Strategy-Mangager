import pandas as pd
import time
import os
import csv
import strategies.EMA_CROSS_9_25_bot as strat
import matplotlib.pyplot as plt

def run_backtest(
    instrument="EUR_USD",
    risk_percent=0.01,
    starting_balance=850,
    candle_counter=2016,
    trail_on=False,
    trail_start=0.7,
    trail_distance=0.25,
    debug=False,
    csv_filename="trades_made_1",
    folder_name="results_set_1",
    metric_filename="metric_set_1"
):
    # --- Globals / State ---
    trades = []
    completed_trades = []
    account_balance = starting_balance
    trades_made = 0
    trades_closed = 0
    trades_unfinished = 0
    stategy_assesment_metrics = []

    # --- Helper functions ---
    def calculate_units(account_balance, risk_percent, entry_price, stop_loss, instrument):
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
        return risk_usd / (sl_distance * pip_size)

    def check_instrument_availability():
        return not any(tr['instrument'] == instrument and tr['close_price'] is None for tr in trades)

    def execute_trade(signal, entry_price, date=None, time=None):
        nonlocal trades_made, account_balance
        units = calculate_units(account_balance, risk_percent, entry_price, signal['stop_loss'], signal['instrument'])
        trade = {
            "trade_id": trades_made,
            "instrument": signal['instrument'],
            "action": signal['action'],
            "entry_price": entry_price,
            "stop_loss": signal['stop_loss'],
            "original_stop_loss": signal['stop_loss'],
            "take_profit": signal['take_profit'],
            "original_take_profit": signal['take_profit'],
            "units": units,
            "open_price": entry_price,
            "highest_price": entry_price,
            "lowest_price": entry_price,
            "close_price": None,
            "be_reached": False,
            "win": None,
            "profit": None,
            "profit_pips": None,
            "profit_usd": None,
            "%_TP_reached": False,
        }
        trades.append(trade)
        trades_made += 1
        stategy_assesment_metrics.append({
            "entry_price": entry_price,
            "stop_loss": signal['stop_loss'],
            "take_profit": signal['take_profit'],
            "units": units,
        })
        if debug:
            print(f"Opened trade: {trade['action']} at {entry_price}, Units: {units}")
        return trade

    def update_positions(candle):
        nonlocal trades_closed, account_balance
        for tr in trades:
            if tr['close_price'] is not None:
                continue

            action = tr['action']
            entry_price = tr['entry_price']

            tr['highest_price'] = max(tr['highest_price'], candle['high'])
            tr['lowest_price'] = min(tr['lowest_price'], candle['low'])

            # Trailing stop logic if enabled
            if trail_on:
                if not tr['%_TP_reached']:
                    tp_distance = abs(tr["take_profit"] - entry_price)
                    trigger_price = entry_price + trail_start * tp_distance if action == 'buy' else entry_price - trail_start * tp_distance
                    if (action == 'buy' and candle['high'] >= trigger_price) or (action == 'sell' and candle['low'] <= trigger_price):
                        tr['%_TP_reached'] = True

                if not tr['be_reached']:
                    risk_distance = abs(entry_price - tr['stop_loss'])
                    if (action == 'buy' and candle['high'] - entry_price >= risk_distance) or \
                       (action == 'sell' and entry_price - candle['low'] >= risk_distance):
                        tr['be_reached'] = True

                if tr['be_reached']:
                    trail_dist = strat.get_trailing_stop_distance_if_triggered(candle, tr, trail_start, trail_distance)
                    if trail_dist is not None:
                        tr["take_profit"] = None
                        if action == 'buy':
                            new_stop = tr['highest_price'] - trail_dist
                            if new_stop > tr['stop_loss']:
                                tr['stop_loss'] = round(new_stop, 6)
                        elif action == 'sell':
                            new_stop = tr['lowest_price'] + trail_dist
                            if new_stop < tr['stop_loss']:
                                tr['stop_loss'] = round(new_stop, 6)

            # Check exit conditions
            hit_tp = hit_sl = False
            if action == 'buy':
                if tr["take_profit"]:
                    hit_tp = candle['high'] >= tr['take_profit']
                hit_sl = candle['low'] <= tr['stop_loss']
            else:
                if tr["take_profit"]:
                    hit_tp = candle['low'] <= tr['take_profit']
                hit_sl = candle['high'] >= tr['stop_loss']

            if not hit_tp and not hit_sl:
                continue

            # Resolve exit
            if hit_tp and hit_sl:
                price, win = tr['stop_loss'], False
            elif hit_tp:
                price, win = tr['take_profit'], True
            elif hit_sl:
                price, win = tr['stop_loss'], False

            tr['close_price'] = price
            tr['win'] = win
            tr['profit'] = round(price - entry_price, 6) if action == 'buy' else round(entry_price - price, 6)
            tr['profit_pips'] = round(tr['profit'] * 10000, 1)
            tr['profit_usd'] = round(tr['profit'] * tr['units'], 2)
            account_balance += tr['profit_usd']
            completed_trades.append(tr)
            trades_closed += 1

    # --- Load historical data ---
    historical_candles = pd.read_csv('backtest\EURUSD5.csv')
    historical_candles = historical_candles.tail(candle_counter).reset_index(drop=True)

    # --- Backtest loop ---
    start_time = time.perf_counter()  # start timer once before the loop

    for idx, row in historical_candles.iterrows():
        if idx % 200 == 0 and idx != 0:  # skip 0
            end_time = time.perf_counter()
            print(f'Candle count: {idx}, {candle_counter-idx} left')
            print(f'Time elapsed for last 200 candles: {end_time - start_time:.4f} seconds')
            start_time = time.perf_counter()  # reset timer for next batch
        candle = {
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close'])
        }
        update_positions(candle)

        if idx < 200:
            continue

        signal = strat.run(historical_candles.iloc[:idx+1].to_dict('records'), instrument=instrument)
        if signal['action'] != 'hold' and check_instrument_availability():
            entry_price = float(historical_candles.iloc[idx + 1]['open']) if idx + 1 < len(historical_candles) else candle['close']
            execute_trade(signal, entry_price, row.get('date'), row.get('time'))

    # Force close any remaining trades
    for tr in trades:
        if tr['close_price'] is None:
            tr['close_price'] = historical_candles.iloc[-1]['close']
            tr['profit'] = tr['close_price'] - tr['entry_price'] if tr['action'] == 'buy' else tr['entry_price'] - tr['close_price']
            tr['profit_pips'] = round(tr['profit'] * 10000, 1)
            tr['profit_usd'] = round(tr['profit'] * tr['units'], 2)
            tr['win'] = tr['profit'] > 0
            account_balance += tr['profit_usd']
            completed_trades.append(tr)

    trades.clear()

    # --- Metrics Calculation ---
    def calculate_metrics(trade_list):
        if not trade_list:
            return {}
        total = len(trade_list)
        wins = [t for t in trade_list if t['profit_usd'] > 0]
        losses = [t for t in trade_list if t['profit_usd'] < 0]
        breakeven = [t for t in trade_list if round(t['profit_usd'], 2) == 0]

        rr_list = []
        for t in trade_list:
            if t['close_price'] is not None and t.get('original_stop_loss') is not None:
                risk = abs(t['entry_price'] - t['original_stop_loss'])
                reward = abs(t['close_price'] - t['entry_price'])
                if risk > 0:
                    rr_list.append(reward / risk)
        avg_rrr = round(sum(rr_list) / len(rr_list), 2) if rr_list else 0.0

        total_usd = sum(t['profit_usd'] for t in trade_list)
        win_rate = len(wins) / total * 100 if total else 0
        avg_win = sum(t['profit_usd'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['profit_usd'] for t in losses) / len(losses) if losses else 0
        profit_factor = (sum(t['profit_usd'] for t in wins) / abs(sum(t['profit_usd'] for t in losses))) if losses else float('inf')

        be_reached = [t for t in trade_list if t.get('be_reached')]
        trail_start_reached = [t for t in trade_list if t.get('%_TP_reached')]
        trail_failures = [t for t in trail_start_reached if t['profit_usd'] <= 0]
        trail_successes = [t for t in trail_start_reached if t['profit_usd'] > 0]

        pct_tp_captured = []
        for t in trail_start_reached:
            tp_distance = abs(t['original_take_profit'] - t['entry_price'])
            if tp_distance > 0:
                profit_distance = abs(t['close_price'] - t['entry_price'])
                pct_tp_captured.append((profit_distance / tp_distance) * 100)
        avg_pct_tp_captured = sum(pct_tp_captured) / len(pct_tp_captured) if pct_tp_captured else 0

        trades_hit_tp = [t for t in trade_list if t['win']]
        win_rate_tp = round(len(trades_hit_tp) / total * 100, 2) if total else 0

        return {
            'total_trades': total,
            'wins': len(wins),
            'losses': len(losses),
            'breakeven': len(breakeven),
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'be_reached_count': len(be_reached),
            'be_reached_pct': round(len(be_reached) / total * 100, 2) if total else 0,
            'trail_start_reached_count': len(trail_start_reached),
            'trail_start_reached_pct': round(len(trail_start_reached) / total * 100, 2) if total else 0,
            'trail_failures': len(trail_failures),
            'trail_successes': len(trail_successes),
            'avg_pct_tp_captured': round(avg_pct_tp_captured, 2),
            'avg_rrr': avg_rrr,
            'win_rate_tp': win_rate_tp
        }

    metrics = calculate_metrics(completed_trades)

    # --- Save trades ---
    if completed_trades:
        os.makedirs(folder_name, exist_ok=True)  # ensure folder exists
        trades_csv_path = os.path.join(folder_name, csv_filename)

        with open(trades_csv_path, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=completed_trades[0].keys())
            writer.writeheader()
            for tr in completed_trades:
                writer.writerow(tr)

        if metrics:
            metrics_csv_path = os.path.join(folder_name, metric_filename)
        with open(metrics_csv_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Metric", "Value"])
            for k, v in metrics.items():
                writer.writerow([k, v])


    # --- Equity curve, drawdowns, cumulative pips ---
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

    # --- Plots ---
    def save_backtest_charts(equity_curve, drawdowns, profits_usd, cum_pips, instrument, folder_name):
        os.makedirs(folder_name, exist_ok=True)

        # Equity Curve
        plt.figure(figsize=(8, 5))
        plt.plot(equity_curve, label="Equity Curve")
        plt.title(f"{instrument} Equity Curve")
        plt.xlabel("Trades")
        plt.ylabel("Account Balance ($)")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(folder_name, f"{instrument}_equity_curve.png"), dpi=300)
        plt.close()

        # Drawdown
        plt.figure(figsize=(8, 5))
        plt.plot(drawdowns, color='red')
        plt.title("Drawdown over Time")
        plt.xlabel("Trades")
        plt.ylabel("Drawdown ($)")
        plt.grid(True)
        plt.savefig(os.path.join(folder_name, f"{instrument}_drawdown.png"), dpi=300)
        plt.close()

        # Profit Distribution
        plt.figure(figsize=(8, 5))
        plt.hist(profits_usd, bins=30, edgecolor='black')
        plt.title("Distribution of Trade Profits")
        plt.xlabel("Profit (USD)")
        plt.ylabel("Frequency")
        plt.savefig(os.path.join(folder_name, f"{instrument}_profit_distribution.png"), dpi=300)
        plt.close()

        # Cumulative Pips
        plt.figure(figsize=(8, 5))
        plt.plot(cum_pips)
        plt.title("Cumulative Pips Over Time")
        plt.xlabel("Trades")
        plt.ylabel("Pips")
        plt.savefig(os.path.join(folder_name, f"{instrument}_cumulative_pips.png"), dpi=300)
        plt.close()

    save_backtest_charts(equity_curve, drawdowns, profits_usd, cum_pips, instrument, folder_name)

    # --- Print summary ---
    total_usd = sum(t['profit_usd'] for t in completed_trades)
    total_pips = sum(t['profit_pips'] for t in completed_trades)
    percentage_PL = (total_usd / starting_balance) * 100

    print("\n" + "="*40)
    print("BACKTEST RESULTS")
    print("="*40)
    print(f"Instrument: {instrument}")
    print(f"Initial balance: ${starting_balance}")
    print(f"Final balance: ${round(account_balance,2)}")
    print(f"Total P/L: ${total_usd} ({total_pips} pips)")
    print(f"Percentage return: {percentage_PL:.2f}%")
    print(f"Risk per trade: {risk_percent*100}%")
    print("\n=== Metrics ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    return completed_trades, account_balance, metrics

test_risk_percent_values = [0.01, 0.03, 0.05, 0.1]
test_trail_start_values = [0.3, 0.5, 0.7, 0.9]
test_trail_on = [True, False]
test_trail_distance_valuse = [0.1, 0.25, 0.5, 0.75, 0.9]

permutations = len(test_trail_on) * len(test_risk_percent_values) * len(test_trail_start_values) * len(test_trail_distance_valuse) # 160
counter = 0
for trail_on in test_trail_on:
    for risk_percent in test_risk_percent_values:
        for start_values in test_trail_start_values:
            for trail_distance in test_trail_distance_valuse:
                counter += 1
                print(f'Permutation: {counter} of {permutations}, {permutations-counter} remaining')
                results_filename = f'results_permutation_{counter}.csv'
                folder_name = f'results_set_{counter}'
                metric_filename = f'metrics_{counter}.csv'
                run_backtest('EUR_USD', risk_percent, 850, 5760, trail_on, start_values, trail_distance, False, results_filename, folder_name, metric_filename)
