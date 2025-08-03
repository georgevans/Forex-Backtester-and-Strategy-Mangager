from oandapyV20 import API
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing

# Replace these with your actual credentials
API_KEY = "463540f20dc813f79b82efa519f4b8a2-3f2f9497f043b6e7b20417495be1b7ca"
ACCOUNT_ID = "101-004-35977326-001"

client = API(access_token=API_KEY)

# Check account balance
def get_balance():
    r = accounts.AccountSummary(accountID=ACCOUNT_ID)
    client.request(r)
    print("Balance:", r.response['account']['balance'])

def place_trade(units=100, instrument="EUR_USD"):
    order_data = {
        "order": {
            "instrument": instrument,
            "units": str(units),  # positive = buy, negative = sell
            "type": "MARKET",
            "positionFill": "DEFAULT"
        }
    }
    r = orders.OrderCreate(accountID=ACCOUNT_ID, data=order_data)
    client.request(r)
    print("Order placed:", r.response)

def get_price(instrument="EUR_USD"):
    params = {"instruments": instrument}
    r = pricing.PricingInfo(accountID=ACCOUNT_ID, params=params)
    client.request(r)
    for price in r.response['prices']:
        print(f"{instrument} Bid: {price['bids'][0]['price']}, Ask: {price['asks'][0]['price']}")

def trading_bot():
    while True:
        # Example logic: place a trade if price < X
        get_price()
        # add your strategy here...
        # place_trade() if condition met

get_balance()
