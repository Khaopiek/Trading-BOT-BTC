
import websocket
import json
import logging
import telegram
from binance.client import Client

# Importing from credentials.py
from credentials import TELEGRAM_API_KEY, BINANCE_API_KEY, BINANCE_API_SECRET, SEND_TELEGRAM_MESSAGE, TELEGRAM_USER_ID_LIST

# Initialize Binance and Telegram clients
binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
telegram_bot = telegram.Bot(token=TELEGRAM_API_KEY)

# Constants
ORDER_PERCENTAGE = 10  # Placeholder value, set to desired percentage

# Define functions to fetch balance and calculate order amount
def get_balance(asset):
    balance = binance_client.get_asset_balance(asset=asset)
    return float(balance['free'])

def calculate_order_amount(balance, percentage):
    return balance * (percentage / 100)

def place_order(symbol, order_type, amount):
    if order_type == "buy":
        order = binance_client.order_market_buy(symbol=symbol, quantity=amount)
    elif order_type == "sell":
        order = binance_client.order_market_sell(symbol=symbol, quantity=amount)
    else:
        print("Invalid order type!")
        return
    return order

# Remaining original code ...

from telegram_message_sender import send_message

# Your original global variables
# Define the moving averages
MA1 = [1]
MA2 = [20]
MA3 = [100]

# Define the indicators
I1 = 0
I2 = 0
I3 = 0
# Store the last buy transaction details
last_buy_price = 0
last_buy_amount = 0


def on_message(ws, message):
    global MA1, MA2, MA3, I1, I2, I3

    data = json.loads(message)
    close_price = float(data['k']['c'])

    # Update moving averages
    MA1.append(close_price)
    MA2.append(close_price)
    MA3.append(close_price)

    if len(MA1) > 1:
        MA1.pop(0)
    if len(MA2) > 50:
        MA2.pop(0)
    if len(MA3) > 100:
        MA3.pop(0)

    # Calculate indicators
    I1 = 1 if sum(MA1)/len(MA1) > sum(MA2)/len(MA2) else 0
    I2 = 1 if sum(MA2)/len(MA2) > sum(MA3)/len(MA3) else 0
    I3 = 5 if sum(MA1)/len(MA1) < sum(MA3)/len(MA3) else 0

    
    # Buy logic
    if I1 + I2 + I3 == 2:
        # Fetch the available balance (assuming using USDT for simplicity)
        balance = get_balance("TUSD")
        order_amount = calculate_order_amount(balance, ORDER_PERCENTAGE)  # Using the predefined ORDER_PERCENTAGE
        # Place buy order (using a placeholder for symbol and order type for simplicity)
        order = place_order("BTCTUSD", "buy", order_amount)
        
        # Update the last buy transaction details
        last_buy_price = order['fills'][0]['price']
        last_buy_amount = order['fills'][0]['qty']
        
        send_message(f"Buy Signal!\nBought at price: {last_buy_price}\nAmount: {last_buy_amount}")
    
    # Sell logic
    elif I1 + I2 + I3 >= 5:
        # Calculate net profit
        net_profit = (close_price - last_buy_price) * last_buy_amount
        
        send_message(f"Sell Signal!\nBought at price: {last_buy_price}\nSold at price: {close_price}\nAmount: {last_buy_amount}\nNet Profit: {net_profit}")
        
        # Reset the last buy transaction details
        last_buy_price = 0
        last_buy_amount = 0


def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    # Subscribe to BTC TUSD 1s interval candlestick data
    ws.send(json.dumps({
        "method": "SUBSCRIBE",
        "params": ["btcusdt@kline_1s"],
        "id": 1
    }))

ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@kline_1s",
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
ws.on_open = on_open
ws.run_forever()

