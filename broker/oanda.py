from oandapyV20 import API
import time
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.positions as positions
from datetime import datetime


class OandaClient:
    def __init__(self, api_key, account_id):
        self.client = API(access_token=api_key)
        self.account_id = account_id

    def get_balance(self):
        r = accounts.AccountSummary(accountID=self.account_id)
        self.client.request(r)
        return float(r.response['account']['balance'])

    def get_price(self, instrument):
        params = {"instruments": instrument}
        r = pricing.PricingInfo(accountID=self.account_id, params=params)
        self.client.request(r)
        price_data = r.response['prices'][0]
        return {
            "bid": float(price_data['bids'][0]['price']),
            "ask": float(price_data['asks'][0]['price']),
            "time": price_data['time']
        }

    def get_candles(self, instrument, count=200, granularity="M5"):
        params = {"count": count, "granularity": granularity, "price": "M"}
        r = instruments.InstrumentsCandles(instrument=instrument, params=params)
        self.client.request(r)
        candles = r.response["candles"]
        return [{
            "time": c["time"],
            "open": float(c["mid"]["o"]),
            "high": float(c["mid"]["h"]),
            "low": float(c["mid"]["l"]),
            "close": float(c["mid"]["c"]),
            "complete": c["complete"]
        } for c in candles if c["complete"]]

    def calculate_units(self, amount_gbp, instrument="EUR_USD"):
        # Get current GBP/USD and instrument price
        instrument_price = self.get_price(instrument)["ask"]
        gbpusd_price = self.get_price("GBP_USD")["bid"]

        amount_usd = amount_gbp * gbpusd_price
        units = int(amount_usd / instrument_price)
        return units

    def get_open_positions(self):
        r = positions.OpenPositions(accountID=self.account_id)
        self.client.request(r)
        positions_data = r.response.get("positions", [])
        return {p["instrument"]: int(p["long"]["units"]) - int(p["short"]["units"]) for p in positions_data}

    def has_open_position(self, instrument):
        open_positions = self.get_open_positions()
        return instrument in open_positions and open_positions[instrument] != 0

    def execute_trade(self, signal, prevent_duplicates=True):
        side = signal["action"]  # 'buy' or 'sell'
        instrument = signal["instrument"]
        risk_gbp = signal.get("risk_gbp", 300)

        # Avoid duplicate entries unless hedging is enabled
        if prevent_duplicates and self.has_open_position(instrument):
            print(f"[SKIP] Position already open on {instrument}")
            return None

        units = self.calculate_units(risk_gbp, instrument)
        if side == "sell":
            units = -units

        order_data = {
            "order": {
                "instrument": instrument,
                "units": str(units),
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }

        r = orders.OrderCreate(accountID=self.account_id, data=order_data)
        self.client.request(r)
        response = r.response

        fill = response.get("orderFillTransaction", {})

        return {
            "trade_id": fill.get("id"),
            "instrument": instrument,
            "side": side,
            "units": int(fill.get("units", 0)),
            "price": float(fill.get("price", 0)),
            "pl": float(fill.get("pl", 0)),
            "timestamp": fill.get("time")
        }
    


# Features:
# get_balance()	Returns account balance in GBP
# get_price(instrument)	Returns latest bid/ask/time for given pair
# get_candles(...)	Returns historical candles for indicator calculation
# calculate_units(...)	Converts £300 to correct number of units
# get_open_positions()	Returns dictionary of open positions
# has_open_position()	Boolean — is there a live trade on this instrument?
# execute_trade()	Places a market order with GBP-based sizing