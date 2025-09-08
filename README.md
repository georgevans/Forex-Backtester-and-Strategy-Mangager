# Forex Strategy Backtester & Live Trader

A Python-based Forex trading framework for backtesting and live trading major currency pairs. 

This project features one strategy that implements an EMA crossover strategy with ATR-based risk management and RSI confirmation. This strategy is carried out by a live trading bot using the OANDA broker API.
The main purpose of the project however is to create a backtester that can be used with any strategy that returns investment signals based on candle data. The end goal is to create a bank of strategies and use machine learnign to optimize each strategies parameters to improve returns and reduce drawdowns.

## Features

- **EMA Crossover Strategy (9/25)** with trend confirmation using EMA200  
- **Risk management:** Position sizing based on ATR and user-defined risk percent  
- **RSI filter:** Avoid trades in overbought/oversold conditions  
- **Backtesting engine:** Analyze historical performance with trade metrics, equity curves, drawdowns, and profit distribution  
- **Live trading bot:** Automated execution of trades on OANDA accounts  
- **Multi-instrument support:** Trade major Forex pairs like EUR/USD, GBP/USD, USD/JPY  

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/forex-strategy-backtester.git
cd forex-strategy-backtester
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables for live trading (OANDA API):

```env
OANDA_API_KEY=your_api_key
OANDA_ACCOUNT_ID=your_account_id
```

## Usage

### Backtesting

1. Prepare historical candle data in CSV format (OHLC):

```text
date, time, open, high, low, close
```

2. Run backtester:

```bash
python backtester.py
```

3. Backtester outputs:

- Trade statistics: win rate, average win/loss, profit factor  
- Equity curve and drawdown plots  
- Trade CSV export (`trades_made.csv`)  

### Live Trading

1. Configure instruments and strategies in `main.py`:

```python
instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY']
strategies = ['EMA_CROSS_9_25']
```

2. Run live trading bot:

```bash
python main.py
```

3. The bot fetches live candles, evaluates signals, and executes trades on your OANDA account.

## Strategy Details

- **EMA Cross 9/25:** Generates buy/sell signals when EMA9 crosses EMA25  
- **Trend Filter:** Only trade in the direction of EMA200 trend  
- **ATR-Based Stop Loss/Take Profit:** Stop loss and take profit are calculated relative to ATR  
- **RSI Filter:** Prevents buying if RSI > 70 or selling if RSI < 30  
- **Trailing Stop:** Optional trailing stop to protect profits  

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for improvements or new features.

This project is licensed under the MIT License.

