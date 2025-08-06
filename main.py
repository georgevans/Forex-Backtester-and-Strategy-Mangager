import os
import time
import requests
from broker import oanda
from strategies import EMA_CROSS_9_25_bot 

# get signal
# signal = {
#   "instrument": "GBP_USD",
#   "action": "buy",
#   "risk_gbp": 300
# }
# 
risk_percent = 1
API_KEY = os.getenv("OANDA_API_KEY")
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")

# result = oanda.execute_trade(signal)
#if result:
#    print(f"Trade executed on {result['instrument']} at {result['price']} with P/L: {result['pl']}")

client = oanda.OandaClient(API_KEY, ACCOUNT_ID)

def trading_bot(instruments, strategies, risk_percent):
    print('Running bot...')

    while True:
        for instrument in instruments:
            print(f'Current instrument: {instrument}')
            for attempt in range(3):
                print('Attempting to collect candles...')
                try:
                    candle_data = client.get_candles(instrument)
                    break
                except requests.exceptions.RequestException as e:
                    print(f"Attempt {attempt+1} failed while fetching candles for {instrument}: {e}")
                    time.sleep(5)
            else:
                print(f"Skipping {instrument} after 3 failed attempts to fetch candles.")
                continue

            
            for strategy in strategies:
                if strategy == 'EMA_CROSS_9_25':
                    signal = EMA_CROSS_9_25_bot.run(candle_data, instrument)
                    print(signal)
                    if signal['action'] != 'hold':
                        current_price = client.get_price(instrument)
                        if signal['action'] == 'buy':
                            current_price_actual = signal['ask']
                        else:
                            current_price_actual = signal['big']
                        sl_distance = abs(signal['stop_loss'] - current_price_actual)
                        sl_pips = sl_distance / 0.0001
                        units = int(signal['risk'] / (sl_pips * 0.0001))
                        balance = client.get_balance()
                        if (balance - 300 >= 0):
                            risk_gbp = balance * (risk_percent / 100)
                            signal['risk'] = risk_gbp
                            signal['units'] = units
                            trade = client.execute_trade(signal)
                        print(trade)
                    else:
                        print('Hold')

        for i in range(60):
            if i % 10 == 0:
                print(f'Waiting for new candles\nTime passed: {i} Seconds')
            time.sleep(1)

instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY']
strategies = ['EMA_CROSS_9_25']

trading_bot(instruments, strategies, risk_percent)